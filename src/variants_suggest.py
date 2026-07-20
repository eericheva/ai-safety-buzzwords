# -*- coding: utf-8 -*-
"""Suggest synonym forms to add to VARIANTS -- semantically, from cached data.

The weak spot of the pipeline is that a synonym only counts if it is hand-listed
in buzzwords.VARIANTS; an unlisted synonym is silently dropped (undercount).
This tool proposes candidates for human approval -- it does NOT auto-inject.

Method (no new API calls -- SPECTER2 embeds *papers*, not free text, so we
proxy a phrase's meaning by the papers that use it):

  buzzword centroid = mean SPECTER2 vector of the buzzword's verified papers
  phrase   centroid = mean SPECTER2 vector of papers whose text contains phrase
  score            = cosine(buzzword centroid, phrase centroid)

A novel phrase (not in the glossary, not already any known variant form) that is
used across papers sitting in the buzzword's semantic neighbourhood is a likely
synonym. Everything comes from data/embeddings.npz + data/raw2 -- free re-runs.

Output: data/variants_suggestions.csv  (term, candidate, cosine, df, sample)
        -- top-K per buzzword, above a cosine floor. HUMAN approves before it
        goes into buzzwords.VARIANTS.
"""
import csv, glob, json, os, re
from collections import Counter, defaultdict

import numpy as np

from buzzwords import BUZZWORDS, variants
from discover import ngrams, novelty_filter, WORD

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, "data", "raw2")
NPZ = os.path.join(HERE, "data", "embeddings.npz")
OUT = os.path.join(HERE, "data", "variants_suggestions.csv")

MIN_DF = 8        # a candidate phrase must occur in >= this many embedded papers
TOP_K = 8         # suggestions kept per buzzword
COS_FLOOR = 0.20  # drop suggestions below this centered-cosine (junk cut)
MIN_PAPERS = 3    # skip buzzwords with fewer embedded papers (centroid too noisy)


def slug(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def load_vecs():
    """Return arxiv_id -> unit vector, MEAN-CENTERED first.

    SPECTER2 vectors in a narrow single-domain corpus are strongly anisotropic:
    every paper sits near the global mean, so raw cosines all pile up at ~0.99
    and stop discriminating. Subtracting the corpus mean removes that shared
    component and lets true synonyms separate from generic high-freq words
    (whose phrase-centroid collapses onto the mean -> ~0 after centering).
    """
    z = np.load(NPZ, allow_pickle=True)
    raw = {}
    for i, v in zip(z["ids"], z["vecs"]):
        a = np.asarray(v, dtype=np.float32)
        if np.linalg.norm(a) > 0:
            raw[str(i)] = a
    mean = np.mean(list(raw.values()), axis=0)
    id2vec = {}
    for k, a in raw.items():
        c = a - mean
        n = np.linalg.norm(c)
        if n > 0:
            id2vec[k] = c / n           # unit, mean-centered -> cosine = dot
    return id2vec


def paper_ids(rec):
    return (rec.get("externalIds") or {}).get("ArXiv")


def main():
    id2vec = load_vecs()
    print("embedded papers:", len(id2vec))

    # 1. Global corpus: arxiv_id -> lowercased title+abstract (embedded papers only,
    #    deduped across the per-buzzword files).
    corpus = {}
    for fpath in glob.glob(os.path.join(RAW, "*.json")):
        for p in (json.load(open(fpath)).get("data") or []):
            axid = paper_ids(p)
            if axid and axid in id2vec and axid not in corpus:
                corpus[axid] = ((p.get("title") or "") + " " +
                                (p.get("abstract") or "")).lower()
    print("corpus (embedded, deduped):", len(corpus))

    # 2. Candidate phrases: 1-3 grams, doc-frequency over the corpus. Two passes
    #    to bound memory -- count df first, keep only frequent+novel, then index.
    novel = novelty_filter()
    df = Counter()
    for text in corpus.values():
        words = WORD.findall(text)
        grams = set()
        for n in (1, 2, 3):
            grams.update(ngrams(words, n))
        df.update(grams)
    keep = {ph for ph, c in df.items() if c >= MIN_DF and novel(ph)}
    print("candidate phrases (df>=%d, novel):" % MIN_DF, len(keep))

    phrase_papers = defaultdict(list)
    for axid, text in corpus.items():
        words = WORD.findall(text)
        seen = set()
        for n in (1, 2, 3):
            for g in ngrams(words, n):
                if g in keep and g not in seen:
                    seen.add(g)
                    phrase_papers[g].append(axid)

    # 3. Phrase centroids (mean of normalised vecs, then re-normalise).
    phrases = sorted(phrase_papers)
    pmat = np.zeros((len(phrases), 768), dtype=np.float32)
    for i, ph in enumerate(phrases):
        c = np.mean([id2vec[a] for a in phrase_papers[ph]], axis=0)
        nrm = np.linalg.norm(c)
        if nrm > 0:
            pmat[i] = c / nrm

    # 4. Per buzzword: centroid, cosine to every phrase, keep novel top-K.
    rows = []
    for term, _, _ in BUZZWORDS:
        fpath = os.path.join(RAW, slug(term) + ".json")
        if not os.path.exists(fpath):
            continue
        ids = [paper_ids(p) for p in (json.load(open(fpath)).get("data") or [])]
        vecs = [id2vec[a] for a in ids if a and a in id2vec]
        if len(vecs) < MIN_PAPERS:
            continue
        centroid = np.mean(vecs, axis=0)
        nrm = np.linalg.norm(centroid)
        if nrm == 0:
            continue
        centroid /= nrm

        sims = pmat @ centroid                      # cosine to each phrase
        known = set(variants(term)) | {term.lower()}
        order = np.argsort(-sims)
        picked = 0
        for idx in order:
            if picked >= TOP_K:
                break
            ph = phrases[idx]
            cos = float(sims[idx])
            if cos < COS_FLOOR:
                break                               # sorted -> nothing better ahead
            if ph in known or ph in term.lower() or term.lower() in ph:
                continue                            # already covered / trivial
            sample = "; ".join(phrase_papers[ph][:3])
            rows.append((term, ph, round(cos, 4), len(phrase_papers[ph]), sample))
            picked += 1

    rows.sort(key=lambda r: (r[0], -r[2]))
    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["term", "candidate", "cosine", "df", "sample_arxiv"])
        w.writerows(rows)
    print("wrote %d suggestions (<= %d/buzzword) -> %s" % (len(rows), TOP_K, OUT))


if __name__ == "__main__":
    main()
