# -*- coding: utf-8 -*-
"""Data for the unified grouping MAP (taxonomy.html):

One scatter of 125 dots. Three independent controls:
  Layout  -> dot POSITION clusters by the chosen lens
  Colour  -> dot COLOUR by the chosen lens
  Size    -> dot RADIUS by the chosen weight metric

Positions per layout lens:
  semantic          -> organic SPECTER2 PCA coordinates (real embedding map)
  glossary/mit/cooccur -> grouped sunflower packing: each group gets a disc,
                          group discs arranged on a ring; area-constant packing.

Output: data/taxonomy_map.json
"""
import json, os, math
from lenses import build as build_lenses

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLDEN = math.pi * (3 - math.sqrt(5))   # ~2.399963 rad


def load(name):
    return json.load(open(os.path.join(HERE, "data", name)))


def packed_layout(term_group, groups):
    """Sunflower-pack each group's terms into a disc; discs on a ring."""
    members = {g: [t for t in term_group if term_group[t] == g] for g in groups}
    nmax = max((len(m) for m in members.values()), default=1)
    k = len(groups)
    R = 0.34                       # ring radius for group centres
    pos = {}
    for j, g in enumerate(groups):
        ms = members[g]
        n = len(ms)
        if k == 1:
            cx, cy = 0.5, 0.5
        else:
            ang = 2 * math.pi * j / k - math.pi / 2
            cx, cy = 0.5 + R * math.cos(ang), 0.5 + R * math.sin(ang)
        disc = 0.055 + 0.085 * math.sqrt(n / nmax)   # cluster radius grows with count
        # order members by name for determinism
        for i, t in enumerate(sorted(ms)):
            rr = disc * math.sqrt((i + 0.5) / max(1, n))
            th = i * GOLDEN
            pos[t] = [round(cx + rr * math.cos(th), 4), round(cy + rr * math.sin(th), 4)]
    return pos


def main():
    term_lens, lens_meta = build_lenses()
    terms = list(term_lens.keys())

    emb = load("grouping_embed.json")
    stats = {s["term"]: s for s in load("viz_data.json")["stats"]}

    # --- positions per layout lens ---
    layouts = {}
    # semantic: organic PCA coords from the embedding map
    sem = {n["term"]: [round(n["x"], 4), round(n["y"], 4)] for n in emb["nodes"]}
    # a few terms may be missing from emb (no papers) -> drop them everywhere
    terms = [t for t in terms if t in sem]
    layouts["semantic"] = {t: sem[t] for t in terms}
    for lens in ("glossary", "mit", "cooccur"):
        tg = {t: term_lens[t][lens] for t in terms}
        layouts[lens] = packed_layout(tg, lens_meta[lens]["groups"])

    # --- per-term payload (lenses + weight metrics) ---
    def metrics(t):
        s = stats.get(t, {})
        return {"papers": s.get("n_papers", 0), "citations": s.get("sum_citations", 0),
                "cpp": s.get("cpp", 0), "recency": s.get("recency", 0),
                "momentum": s.get("momentum", 0),
                "debut": s.get("debut") or 0, "peak": s.get("peak") or 0}
    term_rows = [{"term": t, "lenses": term_lens[t], "m": metrics(t)} for t in terms]

    out = {
        "generated": "2026-07-18",
        "terms": term_rows,
        "layouts": layouts,
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
        # MIT coverage gaps (subdomains with no buzzword) — a finding a scatter can't show
        "mit_gaps": [c["subdomain"] for c in load("grouping_mit.json")["coverage"] if c["n_terms"] == 0],
        "cooccur_modularity": load("grouping_cooccur.json")["modularity"],
    }
    json.dump(out, open(os.path.join(HERE, "data", "taxonomy_map.json"), "w"), ensure_ascii=False)
    print("wrote taxonomy_map.json  terms=%d  layouts=%s" % (len(terms), list(layouts)))
    for lens in layouts:
        xs = [p[0] for p in layouts[lens].values()]; ys = [p[1] for p in layouts[lens].values()]
        print(f"  {lens:9s}: x[{min(xs):.2f},{max(xs):.2f}] y[{min(ys):.2f},{max(ys):.2f}]")
    print("  mit gaps:", len(out["mit_gaps"]))


if __name__ == "__main__":
    main()
