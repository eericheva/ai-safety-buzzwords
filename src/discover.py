# -*- coding: utf-8 -*-
"""Bottom-up discovery of AI-safety buzzwords NOT yet in the glossary.

Three sources (--source):
  raw2     -- keyphrase-extraction over cached abstracts in data/raw2 (no new fetch)
  openalex -- harvest keywords/topics from OpenAlex works matching a safety query
  mit      -- diff the MIT AI Risk Repository categories against known terms

A phrase is a candidate if it is frequent/relevant AND novel (not already in the
glossary text nor in the buzzwords list). Outputs a ranked CSV per source.
"""
import argparse, csv, glob, json, os, re, urllib.parse, urllib.request
from collections import Counter, defaultdict

import common
from buzzwords import BUZZWORDS, CONTEXT, variants

GLOSSARY = os.path.join(common.HERE, "ai-safety-concepts-glossary.md")

STOP = set("""the a an of to in and for with on is are be by we our this that as from at it its
their can model models language large llm llms using based which such these those has have was were
not or but also more most other into than then when where while use used using new via both each per
set two three may might will would could should paper propose method approach results show demonstrate
however between across many including work task tasks data training test evaluation performance
benchmark benchmarks framework study studies analysis system systems general recent various different
several existing state art high low better best human humans user users response responses input output
prompt prompts text generation generative significant significantly able first second third one another
toward towards within without over under about how what why they them then thus hence given while our
we propose achieve achieves show shows find finds present presents introduce introduces
github https http com www org arxiv available code dataset datasets publicly extensive experiments
experiment future research wide range comprehensive empirical novel propose proposed achieve achieved
significant substantial effective effectiveness demonstrate results result approaches methods paper
studies study widely increasingly remain remains still often typically generally largely
artificial intelligence machine learning deep reinforcement supervised unsupervised""".split())

WORD = re.compile(r"[a-z][a-z-]{2,}")


def known_terms():
    out = set()
    for term, _, _ in BUZZWORDS:
        out.add(term.lower())
        out.update(variants(term))
    return out


def glossary_text():
    return open(GLOSSARY).read().lower()


def novelty_filter():
    gl = glossary_text()
    known = known_terms()
    def novel(phrase):
        return phrase not in gl and phrase not in known
    return novel


def write_csv(rows, header, path):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print("wrote %d rows -> %s" % (len(rows), path))


def ngrams(words, n):
    for i in range(len(words) - n + 1):
        gram = words[i:i + n]
        if gram[0] in STOP or gram[-1] in STOP:
            continue
        yield " ".join(gram)


def discover_raw2(min_count, top, out_path):
    ctx = [c.lower() for c in CONTEXT]
    counts = Counter()
    samples = defaultdict(list)
    for fpath in glob.glob(os.path.join(common.RAW, "*.json")):
        d = common.read_json(fpath)
        for p in (d.get("data") or []):
            axid = (p.get("externalIds") or {}).get("ArXiv")
            text = ((p.get("title") or "") + " " + (p.get("abstract") or "")).lower()
            if not any(c in text for c in ctx):     # keep only safety-context papers
                continue
            words = WORD.findall(text)
            for phrase in set(list(ngrams(words, 2)) + list(ngrams(words, 3))):
                counts[phrase] += 1
                if axid and len(samples[phrase]) < 3:
                    samples[phrase].append(axid)

    novel = novelty_filter()
    rows = [(ph, c, "; ".join(samples[ph]))
            for ph, c in counts.most_common()
            if c >= min_count and novel(ph)]
    write_csv(rows[:top], ["phrase", "count", "sample_arxiv_ids"], out_path)


OPENALEX = "https://api.openalex.org/works"


def openalex_page(query, year_from, per_page, mailto, cursor):
    params = {"search": query, "filter": "from_publication_date:%s-01-01" % year_from,
              "select": "id,keywords,topics", "per-page": per_page, "cursor": cursor}
    if mailto:
        params["mailto"] = mailto
    url = OPENALEX + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r)


def discover_openalex(query, year_from, pages, per_page, mailto, top, out_path):
    counts = Counter()
    cursor = "*"
    for _ in range(pages):
        d = openalex_page(query, year_from, per_page, mailto, cursor)
        for w in d["results"]:
            for k in (w.get("keywords") or []):
                counts[("keyword", k["display_name"].lower())] += 1
            for t in (w.get("topics") or []):
                counts[("topic", t["display_name"].lower())] += 1
        cursor = d["meta"]["next_cursor"]
        if not cursor:
            break

    novel = novelty_filter()
    rows = [(name, kind, c) for (kind, name), c in counts.most_common()
            if novel(name)]
    write_csv(rows[:top], ["keyword", "kind", "count"], out_path)


def discover_mit(out_path):
    gl = glossary_text()
    rows = []
    for domain, subs in common.MIT_SUBS.items():
        for sub in subs:
            words = [w for w in WORD.findall(sub.lower()) if w not in STOP and len(w) > 3]
            matched = [w for w in words if w in gl]
            rows.append((domain, sub, bool(matched), "; ".join(matched)))
    rows.sort(key=lambda r: len(r[3]))     # least-covered subdomains first
    write_csv(rows, ["domain", "subdomain", "covered", "matched_words"], out_path)


# Output files produced by the three discovery sources.
RAW2_CSV = os.path.join(common.DATA, "candidate_terms.csv")
OPENALEX_CSV = os.path.join(common.DATA, "openalex_keywords.csv")
MIT_CSV = os.path.join(common.DATA, "mit_risk_gaps.csv")
MERGED_CSV = os.path.join(common.DATA, "discovery_candidates.csv")


def _norm(term):
    return re.sub(r"\s+", " ", term.lower()).strip()


def read_csv(path):
    """A missing file stops the merge. It used to print `skip (missing)` and return [],
    which ranked the survivors by cross-source agreement across fewer sources than the
    output claimed."""
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def discover_merge(out_path):
    """Fold the raw2 / openalex / mit outputs into one ranked candidate list.

    Terms surfacing in >=2 sources float to the top (cross-source agreement is
    the strongest novelty signal). No fetching -- reads the CSVs each source
    already wrote, so run the three sources first.
    """
    cand = {}  # norm-term -> {"sources": set, "count": int, "sample": str}

    def add(term, source, count, sample):
        term = _norm(term)
        e = cand.setdefault(term, {"sources": set(), "count": 0, "sample": ""})
        e["sources"].add(source)
        e["count"] = max(e["count"], count)
        if sample and not e["sample"]:
            e["sample"] = sample

    for r in read_csv(RAW2_CSV):                       # phrase, count, sample_arxiv_ids
        add(r["phrase"], "raw2", int(r["count"]), r["sample_arxiv_ids"])
    for r in read_csv(OPENALEX_CSV):                   # keyword, kind, count
        add(r["keyword"], "openalex:" + r["kind"], int(r["count"]), "")
    for r in read_csv(MIT_CSV):                        # domain, subdomain, covered, matched_words
        if r["covered"].strip().lower() == "true":
            continue                                   # already in glossary -> not a gap
        matched = set(WORD.findall(r["matched_words"].lower()))
        gap = [w for w in WORD.findall(r["subdomain"].lower())
               if w not in STOP and len(w) > 3 and w not in matched]
        for w in gap:
            add(w, "mit", 0, r["subdomain"])

    # openalex:keyword and openalex:topic both count as source "openalex" for ranking
    def n_src(sources):
        return len({s.split(":")[0] for s in sources})

    rows = sorted(cand.items(),
                  key=lambda kv: (n_src(kv[1]["sources"]), kv[1]["count"]),
                  reverse=True)
    out = [(t, n_src(e["sources"]), "; ".join(sorted(e["sources"])),
            e["count"], e["sample"]) for t, e in rows]
    write_csv(out, ["term", "n_sources", "sources", "count", "sample"], out_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source",
                    choices=["raw2", "openalex", "mit", "merge"], required=True)
    ap.add_argument("--min-count", type=int, default=40)
    ap.add_argument("--top", type=int, default=300)
    ap.add_argument("--query", default="AI safety alignment")
    ap.add_argument("--year-from", type=int, default=2020)
    ap.add_argument("--pages", type=int, default=25)
    ap.add_argument("--per-page", type=int, default=200)
    ap.add_argument("--mailto", default=os.environ.get("OPENALEX_MAILTO"),
                    help="contact email for the OpenAlex polite pool "
                         "(defaults to $OPENALEX_MAILTO)")
    args = ap.parse_args()

    if args.source == "raw2":
        discover_raw2(args.min_count, args.top, RAW2_CSV)
    elif args.source == "openalex":
        discover_openalex(args.query, args.year_from, args.pages, args.per_page,
                          args.mailto, args.top, OPENALEX_CSV)
    elif args.source == "mit":
        discover_mit(MIT_CSV)
    elif args.source == "merge":
        discover_merge(MERGED_CSV)


if __name__ == "__main__":
    main()
