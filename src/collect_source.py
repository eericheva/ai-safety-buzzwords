# -*- coding: utf-8 -*-
"""Run the SAME collection pipeline as collect.py, but for a bottom-up candidate
source (raw2 phrases or OpenAlex keywords) instead of the curated glossary.

For the top-N candidate terms by frequency:
  S2 bulk phrase search -> verify exact phrase in title+abstract -> arXiv papers
  -> per-term metrics (papers, citations, cpp, recency, momentum, debut, peak)
     + per-year series (papers n, citations c).

Output per source (data/src_<source>/):
  raw/<slug>.json   cached S2 pages
  terms.json        [{term, n_papers, sum_citations, cpp, recency, momentum,
                      debut, peak, first_year, series:[{y,n,c}], top:[axids]}]
  papers.csv        deduped arXiv papers (top-60/term)

    python collect_source.py raw2 --top 300
    python collect_source.py openalex --top 300
"""
import argparse
import csv
import os
import time
from collections import Counter
from statistics import median

import common
import s2
from buzzwords import variants

FETCH_PAUSE = 2.5         # seconds between phrase searches
TERM_COLUMN = {"raw2": ("candidate_terms.csv", "phrase"),
               "openalex": ("openalex_keywords.csv", "keyword")}


def load_terms(source, topn):
    fname, col = TERM_COLUMN[source]
    rows = list(csv.DictReader(open(os.path.join(common.DATA, fname))))
    seen, out = set(), []
    for r in rows:
        t = r[col].strip()
        if len(t) < 3 or t.lower() in seen:
            continue
        seen.add(t.lower())
        out.append(t)
        if len(out) >= topn:
            break
    return out


def main(source, topn, api_key):
    outdir = os.path.join(common.DATA, "src_" + source)
    raw = os.path.join(outdir, "raw")
    os.makedirs(raw, exist_ok=True)
    terms = load_terms(source, topn)
    print("source=%s  terms=%d" % (source, len(terms)))

    term_rows, papers = [], {}
    for i, term in enumerate(terms, 1):
        cache = os.path.join(raw, common.slug(term) + ".json")
        if os.path.exists(cache):
            d = common.read_json(cache)
        else:
            d = s2.search_bulk('"%s"' % term, s2.SEARCH_SORT, api_key)  # bare quoted phrase
            common.write_json(d, cache)
            time.sleep(FETCH_PAUSE)

        hit = common.matcher(variants(term))
        ver = []
        for pp in (d.get("data") or []):
            ax = (pp.get("externalIds") or {}).get("ArXiv")
            if not ax:
                continue
            txt = (pp.get("title") or "") + " . " + (pp.get("abstract") or "")
            if hit(txt):
                ver.append((ax, pp))

        if not ver:
            print("[%d/%d] %-32s 0" % (i, len(terms), term[:32]))
            continue

        yrs = [pp.get("year") for _, pp in ver if pp.get("year")]
        by = {y: {"n": 0, "c": 0} for y in range(common.Y0, common.Y1 + 1)}
        for _, pp in ver:
            y = pp.get("year")
            if y and common.Y0 <= y <= common.Y1:
                by[y]["n"] += 1
                by[y]["c"] += pp.get("citationCount") or 0
        total_n = len(ver)
        total_c = sum((pp.get("citationCount") or 0) for _, pp in ver)
        recent = sum(1 for y in yrs if y >= 2024)
        yc = Counter(yrs)
        top = sorted(ver, key=lambda x: -(x[1].get("citationCount") or 0))[:common.TOP_N]
        term_rows.append({
            "term": term, "n_papers": total_n, "sum_citations": total_c,
            "cpp": round(total_c / total_n, 1),
            "recency": round(recent / total_n * 100),
            "momentum": recent, "median_year": int(median(yrs)) if yrs else None,
            "first_year": min(yrs) if yrs else None,
            "peak": yc.most_common(1)[0][0] if yc else None,
            "debut": next((y for y in sorted(yc) if yc[y] >= 2), min(yrs) if yrs else None),
            "series": [{"y": y, "n": by[y]["n"], "c": by[y]["c"]}
                       for y in range(common.Y0, common.Y1 + 1)],
            "top": [ax for ax, _ in top],
        })
        for ax, pp in top:                       # dedup papers across terms
            if ax not in papers:
                papers[ax] = {"arxiv_id": ax,
                              "title": (pp.get("title") or "").replace("\n", " ").strip(),
                              "publicationDate": pp.get("publicationDate") or "",
                              "year": pp.get("year") or "",
                              "citationCount": pp.get("citationCount") or 0, "terms": set()}
            papers[ax]["terms"].add(term)
        print("[%d/%d] %-32s n=%d" % (i, len(terms), term[:32], total_n))

    term_rows.sort(key=lambda r: r["n_papers"], reverse=True)
    common.write_json(term_rows, outdir, "terms.json")
    rows = sorted(papers.values(), key=lambda r: r["citationCount"], reverse=True)
    with open(os.path.join(outdir, "papers.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["arxiv_id", "title", "publicationDate", "year", "citationCount", "terms"])
        for r in rows:
            w.writerow([r["arxiv_id"], r["title"], r["publicationDate"], r["year"],
                        r["citationCount"], "; ".join(sorted(r["terms"]))])
    print("DONE %s: terms_kept=%d  papers=%d" % (source, len(term_rows), len(rows)))


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    a.add_argument("source", choices=sorted(TERM_COLUMN))
    a.add_argument("--top", type=int, default=300,
                   help="how many candidate terms to collect; 300 is what the two "
                        "sources committed under data/src_* were built from")
    s2.add_key_arg(a)
    args = a.parse_args()
    main(args.source, args.top, args.api_key)
