# -*- coding: utf-8 -*-
"""Enrich per-term stats from cached candidate pages, render the word cloud,
and emit viz_data.json for the dashboard.

Re-verifies over data/raw2/*.json (which hold candidate abstracts) so the
per-term counts / median year use the FULL verified set, not just the top-60
kept for the paper table.
"""
import csv, json, os, re
from statistics import median
from collections import defaultdict

from buzzwords import BUZZWORDS, variants

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, "data", "raw2")


def slug(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def matcher(term):
    pats = [re.compile(r"\b" + re.escape(v), re.IGNORECASE) for v in variants(term)]
    return lambda text: any(p.search(text) for p in pats)


# --- 8 macro-themes (cluster number -> group); keeps categorical hues <=8 ---
GROUPS = {
    "Truth & hallucination":        {1, 11},
    "Harm, bias & fairness":        {2, 3},
    "Interaction & affective":      {4, 16},
    "Alignment, goals & control":   {5, 18, 19, 14, 20},
    "Attacks, robustness & training": {6, 17},
    "Privacy, data & memory":       {7},
    "Agents & multi-agent":         {8, 15},
    "Interpretability & self-knowledge": {9, 12, 13},
}
GROUP_ORDER = list(GROUPS.keys())
# readable-on-white hues, categorical order from the validated palette (deepened)
GROUP_COLOR = {
    "Truth & hallucination":              "#1f5fb0",  # blue
    "Harm, bias & fairness":              "#1f7a1f",  # green
    "Interaction & affective":            "#b03a6e",  # magenta
    "Alignment, goals & control":         "#9a6a00",  # amber
    "Attacks, robustness & training":     "#0f7a58",  # teal
    "Privacy, data & memory":             "#c14a1f",  # orange
    "Agents & multi-agent":               "#4a3aa7",  # violet
    "Interpretability & self-knowledge":  "#b3332f",  # red
}


def cluster_num(cluster):
    return int(re.match(r"\s*(\d+)", cluster).group(1))


def group_of(cluster):
    n = cluster_num(cluster)
    for g, nums in GROUPS.items():
        if n in nums:
            return g
    return "Alignment, goals & control"


def main():
    stats = []
    yearly = defaultdict(int)          # year -> distinct-paper count (corpus)
    corpus_years = {}                  # axid -> year (dedupe for timeline)

    for term, cluster, query in BUZZWORDS:
        with open(os.path.join(RAW, slug(term) + ".json")) as f:
            d = json.load(f)
        hit = matcher(term)
        ver = []
        for pp in (d.get("data") or []):
            ext = pp.get("externalIds") or {}
            axid = ext.get("ArXiv")
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
        from collections import Counter as _C
        yc = _C(yrs)
        peak = yc.most_common(1)[0][0] if yc else None
        debut = next((y for y in sorted(yc) if yc[y] >= 2), min(yrs) if yrs else None)
        stats.append({
            "term": term, "cluster": cluster, "group": group_of(cluster),
            "n_papers": len(ver),
            "sum_citations": sum(p["cit"] for p in ver),
            "median_citations": int(median([p["cit"] for p in ver])) if ver else 0,
            "median_year": int(median(yrs)) if yrs else None,
            "first_year": min(yrs) if yrs else None,
            "peak": peak, "debut": debut,
            "recent_share": round(sum(1 for y in yrs if y >= 2024) / len(yrs), 2) if yrs else 0,
        })

    for axid, yr in corpus_years.items():
        yearly[yr] += 1

    stats.sort(key=lambda r: r["n_papers"], reverse=True)

    # --- attach grouping-lens memberships (glossary / mit / semantic / cooccur) ---
    from lenses import build as build_lenses
    term_lens, lens_meta = build_lenses()
    for s in stats:
        s["lenses"] = term_lens.get(s["term"], {})

    # --- write enriched stats CSV ---
    with open(os.path.join(HERE, "data", "buzzword_stats.csv"), "w", newline="") as f:
        cols = ["term", "group", "cluster", "n_papers", "sum_citations",
                "median_citations", "median_year", "first_year", "recent_share"]
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader(); w.writerows(stats)

    dark_color = {  # brighter hues for dark bg (used for lens colours in out dict)
        "Truth & hallucination": "#5598e7", "Harm, bias & fairness": "#38ad38",
        "Interaction & affective": "#e87ba4", "Alignment, goals & control": "#eda100",
        "Attacks, robustness & training": "#1baf7a", "Privacy, data & memory": "#eb6834",
        "Agents & multi-agent": "#9085e9", "Interpretability & self-knowledge": "#e66767",
    }

    # --- derived weight metrics per term (for cloud size / bar length / sorting) ---
    for s in stats:
        s["cpp"] = round(s["sum_citations"] / max(1, s["n_papers"]), 1)   # citations per paper
        s["recency"] = round(s["recent_share"] * 100)                     # % of papers since 2024
        s["momentum"] = round(s["n_papers"] * s["recent_share"])          # recent papers (volume x recency)

    # year metrics size by (year - 2004) so a more recent debut/peak reads bigger
    CLOUD_METRICS = [
        {"key": "papers",    "label": "Papers",            "fn": lambda s: s["n_papers"]},
        {"key": "citations", "label": "Citations",         "fn": lambda s: s["sum_citations"]},
        {"key": "cpp",       "label": "Citations / paper", "fn": lambda s: s["cpp"]},
        {"key": "recency",   "label": "Recency",           "fn": lambda s: s["recency"]},
        {"key": "momentum",  "label": "Momentum",          "fn": lambda s: s["momentum"]},
        {"key": "debut",     "label": "Debut yr",          "fn": lambda s: max((s["debut"] or 2005) - 2004, 1)},
        {"key": "peak",      "label": "Peak yr",           "fn": lambda s: max((s["peak"] or 2005) - 2004, 1)},
    ]

    # --- interactive SVG clouds: one layout per weight metric (recoloured by lens in JS) ---
    from wordcloud import WordCloud
    import html as _html, re as _re

    def make_cloud_svg(value_of):
        # size ~ sqrt(metric): text AREA is proportional to the metric (area-correct),
        # and the compressed range lets all 125 terms place.
        freqs = {s["term"]: max(value_of(s) ** 0.5, 0.05) for s in stats}
        wc = WordCloud(background_color="#faf9f6",
                       width=2100, height=1150, prefer_horizontal=0.94,
                       relative_scaling=0.40, min_font_size=7, max_font_size=115,
                       font_step=1, margin=1, collocations=False, random_state=42,
                       font_path="/System/Library/Fonts/Helvetica.ttc")
        wc.generate_from_frequencies(freqs)
        svg = wc.to_svg(embed_font=False)
        svg = _re.sub(r'<svg xmlns="([^"]*)" width="(\d+)" height="(\d+)"',
                      r'<svg xmlns="\1" viewBox="0 0 \2 \3" width="100%" preserveAspectRatio="xMidYMid meet"',
                      svg, count=1)
        svg = _re.sub(r'<rect\b[^>]*/?>', '', svg, count=1)
        svg = svg.replace("font-family:'Helvetica';", "font-family:'Helvetica',Arial,system-ui,sans-serif;")
        svg = _re.sub(r'(<text\b[^>]*)>([^<]*)</text>',
                      lambda m: '%s data-term="%s">%s</text>' % (m.group(1), _html.escape(m.group(2), quote=True), m.group(2)),
                      svg)
        return svg, len(wc.layout_)

    cloud_svgs = {}
    for m in CLOUD_METRICS:
        cloud_svgs[m["key"]], placed = make_cloud_svg(m["fn"])
        print("cloud[%s] placed %d/125" % (m["key"], placed))
    cloud_svg = cloud_svgs["papers"]   # default

    # --- viz_data.json (stats + yearly + papers subset) ---
    papers = list(csv.DictReader(open(os.path.join(HERE, "data", "papers.csv"))))
    for p in papers:
        p["citationCount"] = int(p["citationCount"])
        p["n_matched_terms"] = int(p["n_matched_terms"])
    yearly_rows = [{"year": y, "n": yearly[y]} for y in sorted(yearly)]

    out = {
        "generated": "2026-07-18",
        "n_papers": len(papers),
        "n_buzzwords": len(stats),
        "total_citations": sum(p["citationCount"] for p in papers),
        "year_min": min(yearly), "year_max": max(yearly),
        "groups": GROUP_ORDER,
        "group_color": GROUP_COLOR,
        "group_color_dark": dark_color,
        "lens_meta": lens_meta,
        "cloud_svg": cloud_svg,
        "cloud_svgs": cloud_svgs,
        "cloud_metrics": [{"key": m["key"], "label": m["label"]} for m in CLOUD_METRICS],
        "stats": stats,
        "yearly": yearly_rows,
        "papers": papers,   # full corpus (top-60/term, deduped)
    }
    with open(os.path.join(HERE, "data", "viz_data.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False)
    print("wrote viz_data.json  papers=%d  buzzwords=%d  citations=%d"
          % (out["n_papers"], out["n_buzzwords"], out["total_citations"]))
    print("top terms:", ", ".join(f"{s['term']}({s['n_papers']})" for s in stats[:8]))


if __name__ == "__main__":
    main()
