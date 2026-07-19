# -*- coding: utf-8 -*-
"""Triage the neighbouring agent's bottom-up candidate collection.

Input : data/src_raw2/ and data/src_openalex/ (collect_source.py output --
        each candidate term with its own SPECTER2-embedded papers + metrics).
Method: map every candidate onto the 125 existing buzzwords via centered
        SPECTER2 cosine (same trick as variants_suggest.py), then route:

  variant       cos >= 0.80 to nearest buzzword -> a synonym/dup we already
                track; feed it into that buzzword's VARIANTS (recall fix).
  related       0.60 <= cos < 0.80             -> a facet of an existing
                buzzword; review, often a VARIANTS form too.
  new-candidate cos < 0.60 AND coherent        -> a distant BUT tight cluster;
                a genuinely new concept worth adding as a NEW buzzword.
  discard       cos < 0.60 AND incoherent (discourse phrase whose papers don't
                cluster), too few papers, or a broad OpenAlex field.

Coherence = ||mean(unit centered vectors of the candidate's papers)||. Discourse
fillers ("been shown", "real world") scatter across unrelated papers -> ~0.2;
real concepts cluster -> >=0.36 (the lowest any existing buzzword scores). This
is what separates a new concept from noise once proximity has ruled out dups.

This does NOT auto-edit the glossary or VARIANTS -- it produces one ranked,
labelled sheet so a human curates 481 rows in a single pass instead of blind.

Output: data/candidate_triage.csv
"""
import csv, json, os, re
import numpy as np

from buzzwords import BUZZWORDS
from discover import STOP

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "candidate_triage.csv")

VAR_CUT, REL_CUT = 0.80, 0.60      # cosine band edges (proximity to existing)
COH_MIN = 0.36                     # coherence floor = lowest known buzzword
MIN_PAPERS = 5                     # coherence from <5 papers is a fluke

# Discourse / filler tokens that mark a phrase as noise rather than a concept.
DISCOURSE = STOP | set("""prior works work unlike recent various existing propose
proposed results result approach approaches method methods potential concerns
concern great during inference following able toward towards given show shows
present presents introduce find finds achieve significant novel empirical study
studies paper papers task tasks setting settings general specific simple different
""".split())

# Coarse OpenAlex fields that are not safety concepts (too broad to be a buzzword).
BROAD_FIELDS = set("""physics law chemistry biology medicine mathematics economics
psychology sociology philosophy engineering statistics linguistics education
artificial intelligence deep learning machine learning generative model
natural language processing computer vision data science reinforcement learning
programming language knowledge graph neural network architecture optimization
explainable artificial intelligence explainable artificial intelligence (xai)
software engineering information retrieval robotics""".split("\n"))


def slug(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def unit(v):
    v = np.asarray(v, dtype=np.float32)
    n = np.linalg.norm(v)
    return v / n if n > 0 else v


def load_centered(npz_path):
    """id -> (raw vec); plus the global mean for centering."""
    z = np.load(npz_path, allow_pickle=True)
    d = {str(i): np.asarray(v, dtype=np.float32) for i, v in zip(z["ids"], z["vecs"])}
    mean = np.mean(list(d.values()), axis=0)
    return d, mean


def is_noise(term, source):
    toks = term.split()
    if any(t in DISCOURSE for t in (toks[0], toks[-1])):
        return True
    if source == "openalex":
        base = re.sub(r"\s*\(.*?\)", "", term).strip()      # drop "(xai)" etc.
        if base in BROAD_FIELDS or len(toks) == 1:
            return True
    return False


def buzzword_centroids():
    raw, mean = load_centered(os.path.join(HERE, "data", "embeddings.npz"))
    bz = {}
    for t, _, _ in BUZZWORDS:
        f = os.path.join(HERE, "data", "raw2", slug(t) + ".json")
        if not os.path.exists(f):
            continue
        ids = [(p.get("externalIds") or {}).get("ArXiv")
               for p in (json.load(open(f)).get("data") or [])]
        vs = [unit(raw[a] - mean) for a in ids if a in raw]
        if vs:
            bz[t] = unit(np.mean(vs, axis=0))
    return bz


def main():
    bz = buzzword_centroids()
    terms = list(bz)
    mat = np.array([bz[t] for t in terms])
    print("existing buzzword centroids:", len(terms))

    rows = []
    for source in ["raw2", "openalex"]:
        d = os.path.join(HERE, "data", "src_" + source)
        cmap, cmean = load_centered(os.path.join(d, "embeddings.npz"))
        for x in json.load(open(os.path.join(d, "terms.json"))):
            ids = x.get("top", [])[:20]
            vs = [unit(cmap[a] - cmean) for a in ids if a in cmap]
            if not vs:
                continue
            resultant = np.mean(vs, axis=0)
            coh = round(float(np.linalg.norm(resultant)), 3)   # cluster tightness
            c = unit(resultant)
            sims = mat @ c
            j = int(np.argmax(sims))
            cos = round(float(sims[j]), 3)
            near = terms[j]
            npap = x.get("n_papers", 0) or 0

            if cos >= VAR_CUT:
                bucket = "variant"
            elif cos >= REL_CUT:
                bucket = "related"
            elif coh >= COH_MIN and npap >= MIN_PAPERS and not is_noise(x["term"], source):
                bucket = "new-candidate"       # distant but a tight, real cluster
            else:
                bucket = "discard"             # incoherent / too few papers / broad field

            rows.append({
                "candidate": x["term"], "source": source, "bucket": bucket,
                "nearest_buzzword": near, "cosine": cos, "coherence": coh,
                "n_papers": npap, "sum_citations": x.get("sum_citations", ""),
                "sample_top": "; ".join(x.get("top", [])[:3]),
            })

    # within a bucket: proximity buckets rank by cosine, new-candidate by
    # coherence (citations mislead -- "real world" has millions but is noise).
    order = {"variant": 0, "related": 1, "new-candidate": 2, "discard": 3}
    def sortkey(r):
        rank = r["coherence"] if r["bucket"] == "new-candidate" else r["cosine"]
        return (order[r["bucket"]], -rank)
    rows.sort(key=sortkey)
    cols = ["candidate", "source", "bucket", "nearest_buzzword", "cosine",
            "coherence", "n_papers", "sum_citations", "sample_top"]
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    from collections import Counter
    c = Counter(r["bucket"] for r in rows)
    print("wrote %d rows -> %s" % (len(rows), OUT))
    for b in ["variant", "related", "new-candidate", "discard"]:
        print("  %-14s %d" % (b, c[b]))


if __name__ == "__main__":
    main()
