# -*- coding: utf-8 -*-
"""Enrich per-term stats from cached candidate pages, render the word clouds,
and emit viz_data.json for the dashboard.

Re-verifies over data/raw2/*.json (which hold candidate abstracts) so the
per-term counts / median year use the FULL verified set, not just the top-60
kept for the paper table.

    python build_viz.py
"""
import argparse
import csv
import datetime
import os
from collections import Counter, defaultdict
from statistics import median

import cloud
import common
import lenses
from buzzwords import BUZZWORDS, variants


def term_stats():
    """Per-term aggregates plus the corpus year histogram, both from the cache."""
    stats = []
    corpus_years = {}                  # axid -> year (dedupe for the timeline)

    for term, cluster, _ in BUZZWORDS:
        d = common.read_json(common.RAW, common.slug(term) + ".json")
        hit = common.matcher(variants(term))
        ver = []
        for pp in (d.get("data") or []):
            axid = (pp.get("externalIds") or {}).get("ArXiv")
            if not axid:
                continue
            text = (pp.get("title") or "") + " . " + (pp.get("abstract") or "")
            if not hit(text):
                continue
            yr = pp.get("year")
            ver.append({"axid": axid, "year": yr, "cit": pp.get("citationCount") or 0})
            if yr and axid not in corpus_years:
                corpus_years[axid] = yr

        yrs = [p["year"] for p in ver if p["year"]]
        yc = Counter(yrs)
        peak = yc.most_common(1)[0][0] if yc else None
        debut = next((y for y in sorted(yc) if yc[y] >= 2), min(yrs) if yrs else None)
        stats.append({
            "term": term, "cluster": cluster, "group": common.group_of(cluster),
            "n_papers": len(ver),
            "sum_citations": sum(p["cit"] for p in ver),
            "median_citations": int(median([p["cit"] for p in ver])) if ver else 0,
            "median_year": int(median(yrs)) if yrs else None,
            "first_year": min(yrs) if yrs else None,
            "peak": peak, "debut": debut,
            "recent_share": round(sum(1 for y in yrs if y >= 2024) / len(yrs), 2) if yrs else 0,
        })

    yearly = defaultdict(int)
    for yr in corpus_years.values():
        yearly[yr] += 1
    stats.sort(key=lambda r: r["n_papers"], reverse=True)
    return stats, yearly


def main(font):
    stats, yearly = term_stats()

    term_lens, lens_meta = lenses.build()
    for s in stats:
        s["lenses"] = term_lens[s["term"]]

    with open(os.path.join(common.DATA, "buzzword_stats.csv"), "w", newline="") as f:
        cols = ["term", "group", "cluster", "n_papers", "sum_citations",
                "median_citations", "median_year", "first_year", "recent_share"]
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader(); w.writerows(stats)

    # derived weight metrics per term (cloud size / bar length / sorting)
    for s in stats:
        s["cpp"] = round(s["sum_citations"] / max(1, s["n_papers"]), 1)   # citations per paper
        s["recency"] = round(s["recent_share"] * 100)                     # % of papers since 2024
        s["momentum"] = round(s["n_papers"] * s["recent_share"])          # volume x recency

    # one cloud layout per weight metric, recoloured by lens in JS. Size ~ sqrt(metric):
    # text AREA is proportional to the metric, and the compressed range lets every term place.
    cloud_svgs = {}
    for m in common.WEIGHT_METRICS:
        freqs = {s["term"]: max(common.metric_value(s, m["key"]) ** 0.5, 0.05) for s in stats}
        cloud_svgs[m["key"]], placed = cloud.svg(freqs, font)
        print("cloud[%s] placed %d/%d" % (m["key"], placed, len(stats)))

    papers = list(csv.DictReader(open(os.path.join(common.DATA, "papers.csv"))))
    for p in papers:
        p["citationCount"] = int(p["citationCount"])
        p["n_matched_terms"] = int(p["n_matched_terms"])

    out = {
        "generated": datetime.date.today().isoformat(),
        "n_papers": len(papers),
        "n_buzzwords": len(stats),
        "total_citations": sum(p["citationCount"] for p in papers),
        "year_min": min(yearly), "year_max": max(yearly),
        "groups": common.GROUP_ORDER,
        "group_color": common.GROUP_COLOR,
        "group_color_dark": common.GROUP_COLOR_DARK,
        "lens_meta": lens_meta,
        "cloud_svg": cloud_svgs["papers"],   # default
        "cloud_svgs": cloud_svgs,
        "cloud_metrics": common.WEIGHT_METRICS,
        "stats": stats,
        "yearly": [{"year": y, "n": yearly[y]} for y in sorted(yearly)],
        "papers": papers,   # full corpus (top-60/term, deduped)
    }
    common.write_json(out, common.DATA, "viz_data.json")
    print("wrote viz_data.json  papers=%d  buzzwords=%d  citations=%d"
          % (out["n_papers"], out["n_buzzwords"], out["total_citations"]))
    print("top terms:", ", ".join(f"{s['term']}({s['n_papers']})" for s in stats[:8]))


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    a.add_argument("--font", default=cloud.DEFAULT_FONT,
                   help="TTF for the cloud; default is the font wordcloud ships")
    args = a.parse_args()
    main(args.font)
