# -*- coding: utf-8 -*-
"""Collect AI-safety buzzword papers from Semantic Scholar bulk search,
then VERIFY each match by exact phrase in title+abstract (no stemming).

Pipeline per buzzword:
  1. S2 bulk call (candidate retriever): year>=2005, CS, sort=citationCount:desc,
     returns up to 1000 candidates with abstracts.
  2. Verify: keep candidates whose (title+abstract) contains a surface variant
     of the buzzword as a whole word (word-boundary, any suffix). This removes
     stemming false positives (scheme != scheming) and off-topic co-matches.
  3. Keep verified arXiv papers; top-N by citations for the table.

Metrics:
  raw_s2_total       -- S2's own (stemmed) total, kept only for reference
  verified_arxiv     -- arXiv papers in the page that pass phrase verification
                        (capped by 1000-candidate retrieval depth) -> cloud weight
  sum_citations      -- citations of verified arXiv papers

Outputs: data/raw/<slug>.json, data/papers.csv, data/buzzword_counts.csv
"""
import csv, json, os, re, time, sys
import urllib.parse, urllib.request

from buzzwords import BUZZWORDS, CONTEXT, SCOPE, variants

API_KEY = "s2k-ZOHSvEHee6VvgAyjrfPDQ88TXPswpt5ts8AOMUuU"
BULK = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"
FIELDS = "title,abstract,year,publicationDate,citationCount,externalIds"
TOP_N = 60
YEAR = "2005-"

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw2")   # new cache (now includes abstracts)
os.makedirs(RAW, exist_ok=True)


def slug(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


# Terms whose stem is a common word: citation-sort buries literal matches, so
# retrieve most-recent-first instead (these buzzwords are recent anyway).
SORT_OVERRIDE = {"scheming": "publicationDate:desc"}


def fetch(query, sort="citationCount:desc"):
    params = {"query": query, "year": YEAR, "fields": FIELDS,
              "fieldsOfStudy": "Computer Science", "sort": sort}
    url = BULK + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"x-api-key": API_KEY})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:
            wait = 3 * (attempt + 1)
            print(f"    retry {attempt+1} after {wait}s ({e})", file=sys.stderr)
            time.sleep(wait)
    return None


def make_matcher(surfaces):
    pats = [re.compile(r"\b" + re.escape(v), re.IGNORECASE) for v in surfaces]
    def hit(text):
        return any(p.search(text) for p in pats)
    return hit


ctx_hit = make_matcher(CONTEXT)


def main():
    counts, papers = [], {}

    for i, (term, cluster, query) in enumerate(BUZZWORDS, 1):
        cache = os.path.join(RAW, slug(term) + ".json")
        if os.path.exists(cache):
            with open(cache) as f:
                d = json.load(f)
        else:
            d = fetch(query, SORT_OVERRIDE.get(term, "citationCount:desc"))
            if d is None:
                print(f"[{i}/{len(BUZZWORDS)}] {term}: FAILED", file=sys.stderr)
                continue
            with open(cache, "w") as f:
                json.dump(d, f)
            time.sleep(1.2)

        raw_total = d.get("total", 0) or 0
        data = d.get("data", []) or []
        hit = make_matcher(variants(term))
        scoped = SCOPE in query

        verified = []
        for pp in data:
            ext = pp.get("externalIds") or {}
            axid = ext.get("ArXiv")
            if not axid:
                continue
            text = (pp.get("title") or "") + " . " + (pp.get("abstract") or "")
            if not hit(text):
                continue
            if scoped and not ctx_hit(text):
                continue
            verified.append((axid, pp))

        kept = verified[:TOP_N]     # already citation-sorted
        sum_cit = sum((pp.get("citationCount") or 0) for _, pp in verified)
        counts.append({
            "term": term, "cluster": cluster,
            "raw_s2_total": raw_total,
            "candidates_arxiv": sum(1 for pp in data if (pp.get('externalIds') or {}).get('ArXiv')),
            "verified_arxiv": len(verified),
            "sum_citations_verified": sum_cit,
        })

        for axid, pp in kept:
            if axid not in papers:
                papers[axid] = {
                    "arxiv_id": axid,
                    "title": (pp.get("title") or "").replace("\n", " ").strip(),
                    "publicationDate": pp.get("publicationDate") or "",
                    "year": pp.get("year") or "",
                    "citationCount": pp.get("citationCount") or 0,
                    "s2_paperId": pp.get("paperId", ""),
                    "matched_terms": set(), "matched_clusters": set(),
                }
            papers[axid]["matched_terms"].add(term)
            papers[axid]["matched_clusters"].add(cluster)

        print(f"[{i}/{len(BUZZWORDS)}] {term:32s} raw={raw_total:6d}  verified_arxiv={len(verified)}")

    counts.sort(key=lambda r: r["verified_arxiv"], reverse=True)
    with open(os.path.join(HERE, "data", "buzzword_counts.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(counts[0].keys()))
        w.writeheader(); w.writerows(counts)

    rows = sorted(papers.values(), key=lambda r: r["citationCount"], reverse=True)
    with open(os.path.join(HERE, "data", "papers.csv"), "w", newline="") as f:
        cols = ["arxiv_id", "title", "publicationDate", "year", "citationCount",
                "n_matched_terms", "matched_terms", "matched_clusters", "arxiv_url", "s2_paperId"]
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for r in rows:
            w.writerow({
                "arxiv_id": r["arxiv_id"], "title": r["title"],
                "publicationDate": r["publicationDate"], "year": r["year"],
                "citationCount": r["citationCount"],
                "n_matched_terms": len(r["matched_terms"]),
                "matched_terms": "; ".join(sorted(r["matched_terms"])),
                "matched_clusters": "; ".join(sorted(r["matched_clusters"])),
                "arxiv_url": f"https://arxiv.org/abs/{r['arxiv_id']}",
                "s2_paperId": r["s2_paperId"],
            })

    print("\n=== DONE ===")
    print(f"buzzwords: {len(counts)}   unique arXiv papers: {len(rows)}")
    print("top by verified_arxiv: " + ", ".join(f"{c['term']}({c['verified_arxiv']})" for c in counts[:10]))


if __name__ == "__main__":
    main()
