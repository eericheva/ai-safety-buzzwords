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

    python taxonomy_map.py
"""
import math

import common
import lenses

GOLDEN = math.pi * (3 - math.sqrt(5))   # ~2.399963 rad


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
        for i, t in enumerate(sorted(ms)):           # by name, for determinism
            rr = disc * math.sqrt((i + 0.5) / max(1, n))
            th = i * GOLDEN
            pos[t] = [round(cx + rr * math.cos(th), 4), round(cy + rr * math.sin(th), 4)]
    return pos


def main():
    term_lens, lens_meta = lenses.build()

    emb = common.read_json(common.DATA, "grouping_embed.json")
    viz = common.read_json(common.DATA, "viz_data.json")
    stats = {s["term"]: s for s in viz["stats"]}
    sem = {n["term"]: [round(n["x"], 4), round(n["y"], 4)] for n in emb["nodes"]}
    # a term with no embedded papers has no position on the semantic map -> drop it
    # from every layout, so all four layouts hold the same dots
    terms = [t for t in term_lens if t in sem]

    layouts = {"semantic": {t: sem[t] for t in terms}}
    for lens in ("glossary", "mit", "cooccur"):
        layouts[lens] = packed_layout({t: term_lens[t][lens] for t in terms},
                                      lens_meta[lens]["groups"])

    mit = common.read_json(common.DATA, "grouping_mit.json")
    out = {
        # every metric here is reshaped from viz_data, so the snapshot date is its date,
        # not the moment this ran - otherwise the two pages claim different vintages
        "generated": viz["generated"],
        "terms": [{"term": t, "lenses": term_lens[t], "m": common.metric_row(stats[t])}
                  for t in terms],
        "layouts": layouts,
        "lens_meta": lens_meta,
        "weight_metrics": common.WEIGHT_METRICS,
        # MIT coverage gaps (subdomains with no buzzword) - a finding a scatter can't show
        "mit_gaps": [c["subdomain"] for c in mit["coverage"] if c["n_terms"] == 0],
        "cooccur_modularity": common.read_json(common.DATA,
                                               "grouping_cooccur.json")["modularity"],
    }
    common.write_json(out, common.DATA, "taxonomy_map.json")
    print("wrote taxonomy_map.json  terms=%d  layouts=%s" % (len(terms), list(layouts)))
    for lens in layouts:
        xs = [p[0] for p in layouts[lens].values()]
        ys = [p[1] for p in layouts[lens].values()]
        print(f"  {lens:9s}: x[{min(xs):.2f},{max(xs):.2f}] y[{min(ys):.2f},{max(ys):.2f}]")
    print("  mit gaps:", len(out["mit_gaps"]))


if __name__ == "__main__":
    main()
