# -*- coding: utf-8 -*-
"""Turn a collected candidate source (data/src_<source>/terms.json + papers.csv)
into the SAME page data shapes as the curated corpus. Grouping lenses:
  co-occurrence  (local, from paper term co-occurrence)
  semantic       (SPECTER2 embeddings from S2 -> k-means + PCA)
glossary/MIT don't apply to bottom-up candidate terms.

Writes data/src_<source>/{viz_data,trends_data,taxonomy_map}.json

    python build_source_data.py raw2
    python build_source_data.py openalex
"""
import argparse
import csv
import datetime
import os
from collections import defaultdict

import cloud
import common
import cooccur_graph
import embed
import s2
from taxonomy_map import packed_layout

ISO = "Isolated"
MAX_GROUPS = 8            # the categorical palette holds 8 hues
MIN_COMMUNITY = 3         # below this a community is not a group, it is a coincidence
# per-term fields the dashboard reads; `series` and `top` stay out of the page payload
STAT_FIELDS = ("n_papers", "sum_citations", "cpp", "recency", "momentum",
               "median_year", "first_year", "debut", "peak")


def cooccur_lens(tmap, papers):
    """Communities named after their biggest member - the mined branch has no glossary
    theme to name them by."""
    _, comms, deg, mod = cooccur_graph.communities(
        ([x for x in p["terms"].split("; ") if x in tmap] for p in papers), tmap)
    grp, groups = {}, []
    for cs in [c for c in comms if len(c) >= MIN_COMMUNITY]:
        # the name tiebreak is load-bearing: paper counts saturate at the per-term
        # collection cap, so most of a community ties and without it the label would
        # follow set iteration order, i.e. change with PYTHONHASHSEED between runs
        members = sorted(cs, key=lambda t: (-deg[t], t))
        lab = "%s +" % members[0]
        groups.append(lab)
        for m in members:
            grp[m] = lab
    groups.append(ISO)
    for t in tmap:                          # a term in no community of 3+ is isolated
        grp.setdefault(t, ISO)
    if len(groups) > MAX_GROUPS:            # keep the largest, fold the tail into Isolated
        keep = groups[:MAX_GROUPS - 1]
        for t in list(grp):
            if grp[t] not in keep:
                grp[t] = ISO
        groups = keep + [ISO]
    return grp, groups, packed_layout({t: grp[t] for t in tmap}, groups), mod


def semantic_lens(tmap, terms, Xn):
    """k-means over the term centroids, positioned by the PCA of the same vectors."""
    k = min(MAX_GROUPS, max(3, len(terms) // 10))
    labels, xy = embed.kmeans_pca(Xn, k)
    clusters = defaultdict(list)
    for i, t in enumerate(terms):
        clusters[int(labels[i])].append(t)
    grp, groups = {}, []
    for c in sorted(clusters):
        members = sorted(clusters[c], key=lambda t: -tmap[t]["n_papers"])
        lab = "S%d · %s" % (c, ", ".join(members[:2]))
        groups.append(lab)
        for m in members:
            grp[m] = lab
    pos = {terms[i]: [round(float(xy[i, 0]), 4), round(float(xy[i, 1]), 4)]
           for i in range(len(terms))}
    return grp, groups, pos


def main(source, api_key, font):
    d = os.path.join(common.DATA, "src_" + source)
    terms = common.read_json(d, "terms.json")
    papers = list(csv.DictReader(open(os.path.join(d, "papers.csv"))))
    for p in papers:
        p["citationCount"] = int(p["citationCount"] or 0)

    # The semantic lens comes first because it decides the term set: a term whose papers
    # have no SPECTER2 vector has no position on the map, so it is dropped from every
    # lens instead of being parked at the centre. The curated branch does the same.
    ctr_terms, Xn, _ = embed.term_centroids(
        papers, lambda p: p["terms"].split("; "), [t["term"] for t in terms],
        os.path.join(d, "embeddings.npz"), api_key)
    embedded = set(ctr_terms)
    print("  terms with embeddings: %d of %d" % (len(embedded), len(terms)))
    terms = [t for t in terms if t["term"] in embedded]
    tmap = {t["term"]: t for t in terms}

    co_grp, co_groups, co_layout, mod = cooccur_lens(tmap, papers)
    sem_grp, sem_groups, sem_pos = semantic_lens(tmap, ctr_terms, Xn)
    LENS = {"cooccur": (co_grp, co_groups), "semantic": (sem_grp, sem_groups)}
    layouts = {"cooccur": co_layout, "semantic": sem_pos}
    lens_order = list(LENS)
    p0 = "cooccur"            # primary lens for the legacy 'group' field + group_color

    lens_meta = {}
    for ln, (_, groups) in LENS.items():
        light, dark = common.lens_colors(groups)
        lens_meta[ln] = {"label": "Semantic" if ln == "semantic" else "Co-occurrence",
                         "groups": groups, "colors": light, "colors_dark": dark}

    def lenses_of(t):
        return {ln: LENS[ln][0][t] for ln in lens_order}

    cloud_svgs = {}
    for m in common.WEIGHT_METRICS:
        freqs = {t["term"]: max(common.metric_value(t, m["key"]) ** 0.5, 0.05) for t in terms}
        cloud_svgs[m["key"]], _ = cloud.svg(freqs, font)
    print("  clouds done")

    generated = datetime.date.today().isoformat()
    head = {"generated": generated, "source": source,
            "groups": lens_meta[p0]["groups"], "group_color": lens_meta[p0]["colors"],
            "group_color_dark": lens_meta[p0]["colors_dark"], "lens_meta": lens_meta}

    # ---- viz_data ----
    yearly = defaultdict(int)
    for p in papers:
        if p["year"]:
            yearly[int(p["year"])] += 1
    viz = dict(head,
               n_papers=len(papers), n_buzzwords=len(terms),
               total_citations=sum(p["citationCount"] for p in papers),
               year_min=min(yearly), year_max=max(yearly),
               cloud_svg=cloud_svgs["papers"], cloud_svgs=cloud_svgs,
               cloud_metrics=common.WEIGHT_METRICS,
               stats=[dict({"term": t["term"], "group": co_grp[t["term"]],
                            "lenses": lenses_of(t["term"])},
                           **{k: t[k] for k in STAT_FIELDS}) for t in terms],
               yearly=[{"year": y, "n": yearly[y]} for y in sorted(yearly)])
    common.write_json(viz, d, "viz_data.json")

    # ---- trends_data (streams per lens) ----
    axcit = {}
    lens_year = {ln: defaultdict(lambda: defaultdict(set)) for ln in lens_order}
    for p in papers:
        y = int(p["year"]) if p["year"] else None
        if not y or not (common.Y0 <= y <= common.Y1):
            continue
        axcit[p["arxiv_id"]] = p["citationCount"]
        for x in p["terms"].split("; "):
            if x in tmap:
                for ln in lens_order:
                    lens_year[ln][LENS[ln][0][x]][y].add(p["arxiv_id"])
    streams, streams_c = {}, {}
    for ln in lens_order:
        rows, rows_c = [], []
        for y in range(common.Y0, common.Y1 + 1):
            r, rc = {"y": y}, {"y": y}
            for g in lens_meta[ln]["groups"]:
                ax = lens_year[ln][g].get(y, ())
                r[g] = len(ax); rc[g] = sum(axcit[a] for a in ax)
            rows.append(r); rows_c.append(rc)
        streams[ln] = rows; streams_c[ln] = rows_c
    terms_out = sorted(
        [{"term": t["term"], "group": co_grp[t["term"]], "series": t["series"],
          "total_n": t["n_papers"], "total_c": t["sum_citations"],
          "metrics": common.metric_row(t), "peak_year": t["peak"], "debut": t["debut"],
          "first_year": t["first_year"], "lenses": lenses_of(t["term"])} for t in terms],
        key=lambda t: t["total_n"], reverse=True)
    tr = dict(head, y0=common.Y0, y1=common.Y1, weight_metrics=common.WEIGHT_METRICS,
              streams=streams, streams_c=streams_c, terms=terms_out, stream=streams[p0])
    common.write_json(tr, d, "trends_data.json")

    # ---- taxonomy_map ----
    mp = {"generated": generated, "source": source,
          "terms": [{"term": t["term"], "lenses": lenses_of(t["term"]),
                     "m": common.metric_row(t)} for t in terms],
          "layouts": layouts, "lens_meta": lens_meta,
          "weight_metrics": common.WEIGHT_METRICS,
          "mit_gaps": [], "cooccur_modularity": mod}
    common.write_json(mp, d, "taxonomy_map.json")

    print("DONE %s: %d terms, %d papers, lenses=%s"
          % (source, len(terms), len(papers), lens_order))


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    a.add_argument("source", choices=["raw2", "openalex"])
    s2.add_key_arg(a)
    a.add_argument("--font", default=cloud.DEFAULT_FONT,
                   help="TTF for the cloud; default is the font wordcloud ships")
    args = a.parse_args()
    main(args.source, args.api_key, args.font)
