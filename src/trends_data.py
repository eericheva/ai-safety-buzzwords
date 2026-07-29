# -*- coding: utf-8 -*-
"""Per-term-per-year time series (paper volume + citation sum) from the FULL
verified sets cached in data/raw2/, plus per-theme distinct-paper streams.

citation-by-year note: S2 gives a paper's *current total* citation count, not a
history. "citations in year Y" here = sum of current citations of papers the term
*published* in Y (impact of that year's cohort), not citations accrued during Y.

Output: data/trends_data.json

    python trends_data.py
"""
import datetime
from collections import defaultdict

import common
import lenses
from buzzwords import BUZZWORDS, variants


def main():
    term_lens, lens_meta = lenses.build()

    terms_out = []
    # lens -> group -> year -> set(axid)  (distinct papers per group per year)
    lens_year = {ln: defaultdict(lambda: defaultdict(set)) for ln in lens_meta}
    axcit = {}   # axid -> citation count (for citation streams)

    for term, cluster, _ in BUZZWORDS:
        d = common.read_json(common.RAW, common.slug(term) + ".json")
        hit = common.matcher(variants(term))
        by_year = defaultdict(lambda: {"n": 0, "c": 0})
        first_year = None
        for pp in (d.get("data") or []):
            axid = (pp.get("externalIds") or {}).get("ArXiv")
            if not axid:
                continue
            text = (pp.get("title") or "") + " . " + (pp.get("abstract") or "")
            if not hit(text):
                continue
            yr = pp.get("year")
            if not yr:
                continue
            cit = pp.get("citationCount") or 0
            if first_year is None or yr < first_year:
                first_year = yr
            if common.Y0 <= yr <= common.Y1:
                by_year[yr]["n"] += 1
                by_year[yr]["c"] += cit
                axcit[axid] = cit
                for ln, g in term_lens[term].items():
                    lens_year[ln][g][yr].add(axid)

        series = [{"y": y, "n": by_year[y]["n"], "c": by_year[y]["c"]}
                  for y in range(common.Y0, common.Y1 + 1)]
        total_n = sum(s["n"] for s in series)
        total_c = sum(s["c"] for s in series)
        if total_n == 0:
            continue
        peak_year = max(series, key=lambda s: s["n"])["y"]
        # first year in-window the term reaches >=2 papers (a "debut")
        debut = next((s["y"] for s in series if s["n"] >= 2), peak_year)
        recent = sum(s["n"] for s in series if s["y"] >= 2024)
        terms_out.append({
            "term": term, "group": common.group_of(cluster), "series": series,
            "total_n": total_n, "total_c": total_c,
            "metrics": {"papers": total_n, "citations": total_c,
                        "cpp": round(total_c / max(1, total_n), 1),
                        "recency": round(recent / total_n * 100),
                        "momentum": recent, "debut": debut, "peak": peak_year},
            "peak_year": peak_year, "debut": debut,
            "first_year": first_year, "lenses": term_lens[term],
        })

    terms_out.sort(key=lambda t: t["total_n"], reverse=True)

    # streamgraph rows PER LENS: paper counts (streams) + citation sums (streams_c)
    streams, streams_c = {}, {}
    for ln, meta in lens_meta.items():
        rows, rows_c = [], []
        for y in range(common.Y0, common.Y1 + 1):
            row, row_c = {"y": y}, {"y": y}
            for g in meta["groups"]:
                axids = lens_year[ln][g].get(y, ())
                row[g] = len(axids)
                row_c[g] = sum(axcit[a] for a in axids)
            rows.append(row); rows_c.append(row_c)
        streams[ln] = rows; streams_c[ln] = rows_c

    out = {
        "generated": datetime.date.today().isoformat(),
        "y0": common.Y0, "y1": common.Y1,
        "groups": common.GROUP_ORDER,
        "group_color": common.GROUP_COLOR,
        "group_color_dark": common.GROUP_COLOR_DARK,
        "lens_meta": lens_meta,
        "weight_metrics": common.WEIGHT_METRICS,
        "streams": streams,
        "streams_c": streams_c,
        "terms": terms_out,
        "stream": streams["glossary"],
    }
    common.write_json(out, common.DATA, "trends_data.json")
    print("wrote trends_data.json  terms=%d  window=%d-%d"
          % (len(terms_out), common.Y0, common.Y1))
    print("top:", ", ".join(f"{t['term']}(peak {t['peak_year']})" for t in terms_out[:6]))
    print("streams per lens:", {ln: len(v) for ln, v in streams.items()})


if __name__ == "__main__":
    main()
