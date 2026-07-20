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

Usage: python3 collect_source.py raw2 130
       python3 collect_source.py openalex 130
"""
import csv, json, os, re, sys, time
from collections import Counter
from statistics import median

from collect import fetch, slug   # reuse the S2 fetch + slug

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Y0, Y1 = 2015, 2026
TOP_N = 60


def load_terms(source, topn):
    if source == "raw2":
        rows = list(csv.DictReader(open(os.path.join(HERE, "data", "candidate_terms.csv"))))
        col = "phrase"
    elif source == "openalex":
        rows = list(csv.DictReader(open(os.path.join(HERE, "data", "openalex_keywords.csv"))))
        col = "keyword"
    else:
        raise SystemExit("unknown source " + source)
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


def variants(term):
    t = term.lower()
    return sorted({t, t.replace("-", " "), t.replace(" ", "-")})


def main(source, topn):
    outdir = os.path.join(HERE, "data", "src_" + source)
    raw = os.path.join(outdir, "raw")
    os.makedirs(raw, exist_ok=True)
    terms = load_terms(source, topn)
    print("source=%s  terms=%d" % (source, len(terms)))

    term_rows, papers = [], {}
    for i, term in enumerate(terms, 1):
        cache = os.path.join(raw, slug(term) + ".json")
        if os.path.exists(cache):
            d = json.load(open(cache))
        else:
            d = fetch('"%s"' % term)          # bare quoted phrase
            if d is None:
                print("  FAIL", term, file=sys.stderr); continue
            json.dump(d, open(cache, "w"))
            time.sleep(2.5)

        pats = [re.compile(r"\b" + re.escape(v), re.IGNORECASE) for v in variants(term)]
        ver = []
        for pp in (d.get("data") or []):
            ax = (pp.get("externalIds") or {}).get("ArXiv")
            if not ax:
                continue
            txt = (pp.get("title") or "") + " . " + (pp.get("abstract") or "")
            if not any(p.search(txt) for p in pats):
                continue
            ver.append((ax, pp))

        if not ver:
            print("[%d/%d] %-32s 0" % (i, len(terms), term[:32])); continue

        yrs = [pp.get("year") for _, pp in ver if pp.get("year")]
        by = {y: {"n": 0, "c": 0} for y in range(Y0, Y1 + 1)}
        for _, pp in ver:
            y = pp.get("year")
            if y and Y0 <= y <= Y1:
                by[y]["n"] += 1
                by[y]["c"] += pp.get("citationCount") or 0
        series = [{"y": y, "n": by[y]["n"], "c": by[y]["c"]} for y in range(Y0, Y1 + 1)]
        total_n = len(ver)
        total_c = sum((pp.get("citationCount") or 0) for _, pp in ver)
        recent = sum(1 for y in yrs if y >= 2024)
        yc = Counter(yrs)
        peak = yc.most_common(1)[0][0] if yc else None
        debut = next((y for y in sorted(yc) if yc[y] >= 2), min(yrs) if yrs else None)
        term_rows.append({
            "term": term, "n_papers": total_n, "sum_citations": total_c,
            "cpp": round(total_c / max(1, total_n), 1),
            "recency": round(recent / total_n * 100) if total_n else 0,
            "momentum": recent, "median_year": int(median(yrs)) if yrs else None,
            "first_year": min(yrs) if yrs else None, "peak": peak, "debut": debut,
            "series": series,
            "top": [ax for ax, _ in sorted(ver, key=lambda x: -(x[1].get("citationCount") or 0))[:TOP_N]],
        })
        # dedup papers (top-60 per term)
        for ax, pp in sorted(ver, key=lambda x: -(x[1].get("citationCount") or 0))[:TOP_N]:
            if ax not in papers:
                papers[ax] = {"arxiv_id": ax, "title": (pp.get("title") or "").replace("\n", " ").strip(),
                              "publicationDate": pp.get("publicationDate") or "", "year": pp.get("year") or "",
                              "citationCount": pp.get("citationCount") or 0, "terms": set()}
            papers[ax]["terms"].add(term)
        print("[%d/%d] %-32s n=%d" % (i, len(terms), term[:32], total_n))

    term_rows.sort(key=lambda r: r["n_papers"], reverse=True)
    json.dump(term_rows, open(os.path.join(outdir, "terms.json"), "w"), ensure_ascii=False)
    rows = sorted(papers.values(), key=lambda r: r["citationCount"], reverse=True)
    with open(os.path.join(outdir, "papers.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["arxiv_id", "title", "publicationDate", "year", "citationCount", "terms"])
        for r in rows:
            w.writerow([r["arxiv_id"], r["title"], r["publicationDate"], r["year"], r["citationCount"],
                        "; ".join(sorted(r["terms"]))])
    print("DONE %s: terms_kept=%d  papers=%d" % (source, len(term_rows), len(rows)))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 130)
