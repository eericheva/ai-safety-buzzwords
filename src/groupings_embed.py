# -*- coding: utf-8 -*-
"""Semantic grouping: embed each buzzword as the mean SPECTER2 vector of its
papers, then k-means cluster + PCA-2D map. Data-driven 'meaning' grouping,
independent of the glossary and of co-occurrence.

Embeddings come from Semantic Scholar (field embedding.specter_v2, 768-d),
cached to data/embeddings.npz so re-runs are free.

Output: data/grouping_embed.json
"""
import csv, json, os, time, urllib.request
from collections import defaultdict
import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

from build_viz import group_of, GROUP_COLOR
from buzzwords import BUZZWORDS

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_KEY = "s2k-ZOHSvEHee6VvgAyjrfPDQ88TXPswpt5ts8AOMUuU"
BATCH = "https://api.semanticscholar.org/graph/v1/paper/batch?fields=embedding.specter_v2"
NPZ = os.path.join(HERE, "data", "embeddings.npz")
K = 8  # compare against the 8 manual macro-themes
term_group = {t: group_of(c) for t, c, _ in BUZZWORDS}


def fetch_embeddings(ids):
    cache = {}
    if os.path.exists(NPZ):
        z = np.load(NPZ, allow_pickle=True)
        cache = {k: v for k, v in zip(z["ids"], z["vecs"])}
    need = [i for i in ids if i not in cache]
    print("embeddings cached=%d  need=%d" % (len(cache), len(need)))
    for s in range(0, len(need), 500):
        chunk = need[s:s + 500]
        body = json.dumps({"ids": ["ARXIV:" + i for i in chunk]}).encode()
        req = urllib.request.Request(BATCH, data=body,
              headers={"x-api-key": API_KEY, "Content-Type": "application/json"})
        for attempt in range(5):
            try:
                with urllib.request.urlopen(req, timeout=90) as r:
                    data = json.load(r)
                break
            except Exception as e:
                print("  retry", attempt + 1, e); time.sleep(3 * (attempt + 1))
        else:
            continue
        for i, pp in zip(chunk, data):
            emb = (pp or {}).get("embedding") or {}
            v = emb.get("vector")
            if v:
                cache[i] = np.asarray(v, dtype=np.float32)
        print("  fetched %d/%d" % (min(s + 500, len(need)), len(need)))
        time.sleep(1.0)
    # persist
    ids_arr = np.array(list(cache.keys()))
    vecs_arr = np.array(list(cache.values()), dtype=np.float32)
    np.savez_compressed(NPZ, ids=ids_arr, vecs=vecs_arr)
    return cache


def main():
    papers = list(csv.DictReader(open(os.path.join(HERE, "data", "papers.csv"))))
    ids = [p["arxiv_id"] for p in papers]
    emb = fetch_embeddings(ids)

    # term -> list of its papers' vectors
    term_vecs = defaultdict(list)
    for p in papers:
        v = emb.get(p["arxiv_id"])
        if v is None:
            continue
        for t in p["matched_terms"].split("; "):
            if t:
                term_vecs[t].append(v)

    terms = [t for t, _, _ in BUZZWORDS if term_vecs.get(t)]
    X = np.array([np.mean(term_vecs[t], axis=0) for t in terms], dtype=np.float32)
    # L2-normalise centroids (SPECTER2 works with cosine)
    Xn = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-9)

    km = KMeans(n_clusters=K, n_init=10, random_state=42).fit(Xn)
    labels = km.labels_
    sil = silhouette_score(Xn, labels, metric="cosine")
    xy = PCA(n_components=2, random_state=42).fit_transform(Xn)
    # scale xy to [0,1] for the plot
    xy = (xy - xy.min(0)) / (xy.max(0) - xy.min(0) + 1e-9)

    # describe each semantic cluster by dominant manual theme + representative terms
    from collections import Counter
    clusters = []
    for k in range(K):
        members = [terms[i] for i in range(len(terms)) if labels[i] == k]
        # order members by closeness to cluster centroid
        c = Xn[labels == k].mean(0)
        members.sort(key=lambda t: -float(np.dot(Xn[terms.index(t)], c)))
        theme_ct = Counter(term_group[t] for t in members)
        dom, dom_n = theme_ct.most_common(1)[0]
        clusters.append({
            "id": int(k), "size": len(members),
            "dominant_theme": dom, "purity": round(dom_n / len(members), 2),
            "top_terms": members[:8], "members": members,
            "theme_mix": theme_ct.most_common(),
        })
    clusters.sort(key=lambda c: -c["size"])

    nodes = [{"term": terms[i], "x": round(float(xy[i, 0]), 4), "y": round(float(xy[i, 1]), 4),
              "cluster": int(labels[i]), "theme": term_group[terms[i]],
              "n": len(term_vecs[terms[i]])} for i in range(len(terms))]

    out = {"k": K, "silhouette": round(float(sil), 3), "n_terms": len(terms),
           "clusters": clusters, "nodes": nodes,
           "term_group": term_group, "group_color": GROUP_COLOR}
    json.dump(out, open(os.path.join(HERE, "data", "grouping_embed.json"), "w"), ensure_ascii=False)
    print("\nembed: %d terms, k=%d, silhouette=%.3f" % (len(terms), K, sil))
    for c in clusters:
        print(f"  S{c['id']} (n={c['size']}, {c['dominant_theme'].split(',')[0]}, purity {c['purity']}): "
              + ", ".join(c["top_terms"][:6]))


if __name__ == "__main__":
    main()
