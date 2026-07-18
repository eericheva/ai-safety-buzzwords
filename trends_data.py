# -*- coding: utf-8 -*-
"""Per-term-per-year time series (paper volume + citation sum) from the FULL
verified sets cached in data/raw2/, plus per-theme distinct-paper streams.

citation-by-year note: S2 gives a paper's *current total* citation count, not a
history. "citations in year Y" here = sum of current citations of papers the term
*published* in Y (impact of that year's cohort), not citations accrued during Y.

Output: data/trends_data.json
"""
import json, os, re
from collections import defaultdict

from buzzwords import BUZZWORDS, variants
from build_viz import GROUPS, GROUP_ORDER, GROUP_COLOR, group_of, slug

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw2")
Y0, Y1 = 2015, 2026            # chart window (pre-2015 is a handful of papers)


def matcher(term):
    pats = [re.compile(r"\b" + re.escape(v), re.IGNORECASE) for v in variants(term)]
    return lambda text: any(p.search(text) for p in pats)


def main():
    from lenses import build as build_lenses
    term_lens, lens_meta = build_lenses()

    terms_out = []
    # lens -> group -> year -> set(axid)  (distinct papers per group per year)
    lens_year = {ln: defaultdict(lambda: defaultdict(set)) for ln in lens_meta}
    axcit = {}   # axid -> citation count (for citation streams)

    for term, cluster, query in BUZZWORDS:
        with open(os.path.join(RAW, slug(term) + ".json")) as f:
            d = json.load(f)
        hit = matcher(term)
        grp = group_of(cluster)
        by_year = defaultdict(lambda: {"n": 0, "c": 0})
        first_year = None
        for pp in (d.get("data") or []):
            ext = pp.get("externalIds") or {}
            axid = ext.get("ArXiv")
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
            if Y0 <= yr <= Y1:
                by_year[yr]["n"] += 1
                by_year[yr]["c"] += cit
                axcit[axid] = cit
                for ln, g in term_lens[term].items():
                    lens_year[ln][g][yr].add(axid)

        series = [{"y": y, "n": by_year[y]["n"], "c": by_year[y]["c"]}
                  for y in range(Y0, Y1 + 1)]
        total_n = sum(s["n"] for s in series)
        total_c = sum(s["c"] for s in series)
        if total_n == 0:
            continue
        peak_year = max(series, key=lambda s: s["n"])["y"]
        # first year in-window the term reaches >=2 papers (a "debut")
        debut = next((s["y"] for s in series if s["n"] >= 2), peak_year)
        recent = sum(s["n"] for s in series if s["y"] >= 2024)
        metrics = {
            "papers": total_n, "citations": total_c,
            "cpp": round(total_c / max(1, total_n), 1),
            "recency": round(recent / total_n * 100) if total_n else 0,
            "momentum": recent,
            "debut": debut, "peak": peak_year,
        }
        terms_out.append({
            "term": term, "group": grp, "series": series,
            "total_n": total_n, "total_c": total_c, "metrics": metrics,
            "peak_year": peak_year, "debut": debut,
            "first_year": first_year, "lenses": term_lens[term],
        })

    terms_out.sort(key=lambda t: t["total_n"], reverse=True)

    # streamgraph rows PER LENS: paper counts (streams) + citation sums (streams_c)
    streams, streams_c = {}, {}
    for ln, meta in lens_meta.items():
        rows, rows_c = [], []
        for y in range(Y0, Y1 + 1):
            row, row_c = {"y": y}, {"y": y}
            for g in meta["groups"]:
                axids = lens_year[ln][g].get(y, ())
                row[g] = len(axids)
                row_c[g] = sum(axcit.get(a, 0) for a in axids)
            rows.append(row); rows_c.append(row_c)
        streams[ln] = rows; streams_c[ln] = rows_c

    out = {
        "generated": "2026-07-18",
        "y0": Y0, "y1": Y1,
        "groups": GROUP_ORDER,
        "group_color": GROUP_COLOR,
        "group_color_dark": {  # kept for the glossary-coloured atlas default
            "Truth & hallucination": "#5598e7", "Harm, bias & fairness": "#38ad38",
            "Interaction & affective": "#e87ba4", "Alignment, goals & control": "#eda100",
            "Attacks, robustness & training": "#1baf7a", "Privacy, data & memory": "#eb6834",
            "Agents & multi-agent": "#9085e9", "Interpretability & self-knowledge": "#e66767",
        },
        "lens_meta": lens_meta,
        "weight_metrics": [
            {"key": "papers", "label": "Papers"},
            {"key": "citations", "label": "Citations"},
            {"key": "cpp", "label": "Citations / paper"},
            {"key": "recency", "label": "Recency"},
            {"key": "momentum", "label": "Momentum"},
            {"key": "debut", "label": "Debut yr"},
            {"key": "peak", "label": "Peak yr"},
        ],
        "streams": streams,
        "streams_c": streams_c,
        "terms": terms_out,
        "stream": streams["glossary"],
    }
    with open(os.path.join(HERE, "data", "trends_data.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print("wrote trends_data.json  terms=%d  window=%d-%d" % (len(terms_out), Y0, Y1))
    print("top:", ", ".join(f"{t['term']}(peak {t['peak_year']})" for t in terms_out[:6]))
    print("streams per lens:", {ln: len(v) for ln, v in streams.items()})
    # quick sanity: glossary theme totals 2020 vs 2025
    gl = streams["glossary"]
    for th in lens_meta["glossary"]["groups"]:
        r20 = next(r for r in gl if r["y"] == 2020)[th]
        r25 = next(r for r in gl if r["y"] == 2025)[th]
        print(f"  {th:34s} 2020={r20:4d}  2025={r25:4d}")


if __name__ == "__main__":
    main()
