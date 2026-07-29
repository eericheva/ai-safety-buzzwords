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

Outputs: data/raw2/<slug>.json, data/papers.csv, data/buzzword_counts.csv
The per-term cache is what makes this restartable: a rerun re-reads it and only
fetches what is missing, so a failed call costs one term rather than the run.

    python collect.py                  # all 125 buzzwords
    python collect.py --limit 20       # first 20, for a quick end-to-end check
"""
import argparse
import csv
import os
import time

import common
import s2
from buzzwords import BUZZWORDS, CONTEXT, SCOPE, variants

FETCH_PAUSE = 1.2         # seconds between bulk calls

# Terms whose stem is a common word: citation-sort buries literal matches, so
# retrieve most-recent-first instead (these buzzwords are recent anyway).
SORT_OVERRIDE = {"scheming": "publicationDate:desc"}

ctx_hit = common.matcher(CONTEXT)


def main(api_key, limit):
    os.makedirs(common.RAW, exist_ok=True)
    todo = BUZZWORDS[:limit]
    counts, papers = [], {}

    for i, (term, cluster, query) in enumerate(todo, 1):
        cache = os.path.join(common.RAW, common.slug(term) + ".json")
        if os.path.exists(cache):
            d = common.read_json(cache)
        else:
            d = s2.search_bulk(query, SORT_OVERRIDE.get(term, s2.SEARCH_SORT), api_key)
            common.write_json(d, cache)
            time.sleep(FETCH_PAUSE)

        raw_total = d.get("total", 0) or 0
        data = d.get("data", []) or []
        hit = common.matcher(variants(term))
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

        kept = verified[:common.TOP_N]     # already citation-sorted
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

        print(f"[{i}/{len(todo)}] {term:32s} raw={raw_total:6d}  verified_arxiv={len(verified)}")

    counts.sort(key=lambda r: r["verified_arxiv"], reverse=True)
    with open(os.path.join(common.DATA, "buzzword_counts.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(counts[0].keys()))
        w.writeheader(); w.writerows(counts)

    rows = sorted(papers.values(), key=lambda r: r["citationCount"], reverse=True)
    with open(os.path.join(common.DATA, "papers.csv"), "w", newline="") as f:
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
    a = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    s2.add_key_arg(a)
    a.add_argument("--limit", type=int, default=None,
                   help="collect only the first N buzzwords (default: all 125)")
    args = a.parse_args()
    main(args.api_key, args.limit)
