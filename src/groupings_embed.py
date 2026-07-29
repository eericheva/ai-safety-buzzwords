# -*- coding: utf-8 -*-
"""Semantic grouping: embed each buzzword as the mean SPECTER2 vector of its
papers, then k-means cluster + PCA-2D map. Data-driven 'meaning' grouping,
independent of the glossary and of co-occurrence.

Embeddings come from Semantic Scholar (field embedding.specter_v2, 768-d),
cached to data/embeddings.npz so re-runs are free.

Output: data/grouping_embed.json

    python groupings_embed.py
"""
import argparse
import csv
import os
from collections import Counter

import numpy as np
from sklearn.metrics import silhouette_score

import common
import embed
import s2
from buzzwords import BUZZWORDS

K = 8  # compare against the 8 manual macro-themes


def main(api_key):
    term_group = {t: common.group_of(c) for t, c, _ in BUZZWORDS}
    papers = list(csv.DictReader(open(os.path.join(common.DATA, "papers.csv"))))
    terms, Xn, per_term = embed.term_centroids(
        papers, lambda p: p["matched_terms"].split("; "),
        [t for t, _, _ in BUZZWORDS], os.path.join(common.DATA, "embeddings.npz"), api_key)

    labels, xy = embed.kmeans_pca(Xn, K)
    sil = silhouette_score(Xn, labels, metric="cosine")

    # describe each semantic cluster by dominant manual theme + representative terms
    clusters = []
    for k in range(K):
        centre = Xn[labels == k].mean(0)          # order members by closeness to it
        idx = sorted((i for i in range(len(terms)) if labels[i] == k),
                     key=lambda i: -float(np.dot(Xn[i], centre)))
        members = [terms[i] for i in idx]
        theme_ct = Counter(term_group[t] for t in members)
        dom, dom_n = theme_ct.most_common(1)[0]
        clusters.append({
            "id": int(k), "size": len(members),
            "dominant_theme": dom, "purity": round(dom_n / len(members), 2),
            "top_terms": members[:8], "members": members,
            "theme_mix": theme_ct.most_common(),
        })
    clusters.sort(key=lambda c: -c["size"])

    nodes = [{"term": terms[i], "x": round(float(xy[i, 0]), 4),
              "y": round(float(xy[i, 1]), 4), "cluster": int(labels[i]),
              "theme": term_group[terms[i]], "n": len(per_term[terms[i]])}
             for i in range(len(terms))]

    out = {"k": K, "silhouette": round(float(sil), 3), "n_terms": len(terms),
           "clusters": clusters, "nodes": nodes,
           "term_group": term_group, "group_color": common.GROUP_COLOR}
    common.write_json(out, common.DATA, "grouping_embed.json")
    print("\nembed: %d terms, k=%d, silhouette=%.3f" % (len(terms), K, sil))
    for c in clusters:
        print(f"  S{c['id']} (n={c['size']}, {c['dominant_theme'].split(',')[0]}, "
              f"purity {c['purity']}): " + ", ".join(c["top_terms"][:6]))


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    s2.add_key_arg(a)
    main(a.parse_args().api_key)
