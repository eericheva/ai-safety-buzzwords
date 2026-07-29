# -*- coding: utf-8 -*-
"""SPECTER2 vectors with an on-disk cache, and the term-centroid clustering both
grouping lenses are built from.

This existed twice before -- groupings_embed.py fetched in batches of 500 with a 1.0 s
pause, build_source_data.py in batches of 400 with 1.2 s, against the same endpoint for
no stated reason. One copy, one batch size.
"""
import os
import time
from collections import defaultdict

import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

import s2

BATCH_SIZE = 400          # the endpoint's documented per-request ceiling is 500
BATCH_PAUSE = 1.2         # seconds between batches


def fetch(arxiv_ids, npz, api_key):
    """Return {arxiv_id: vector}, extending `npz` with whatever is missing.

    A paper with no vector is simply absent from the result. That is the endpoint's
    answer for preprints it has not embedded, not an error, and callers drop those
    papers rather than inventing a position for them.
    """
    cache = {}
    if os.path.exists(npz):
        z = np.load(npz, allow_pickle=True)
        cache = {k: v for k, v in zip(z["ids"], z["vecs"])}
    need = [i for i in arxiv_ids if i not in cache]
    print("  embeddings: cached=%d need=%d" % (len(cache), len(need)))
    for start in range(0, len(need), BATCH_SIZE):
        chunk = need[start:start + BATCH_SIZE]
        for i, pp in zip(chunk, s2.embeddings(chunk, api_key)):
            vector = ((pp or {}).get("embedding") or {}).get("vector")
            if vector:
                cache[i] = np.asarray(vector, dtype=np.float32)
        print("    fetched %d/%d" % (min(start + BATCH_SIZE, len(need)), len(need)))
        time.sleep(BATCH_PAUSE)
    np.savez_compressed(npz, ids=np.array(list(cache.keys())),
                        vecs=np.array(list(cache.values()), dtype=np.float32))
    return cache


def term_centroids(papers, terms_of, keep, npz, api_key):
    """L2-normalised mean vector per term, over the papers that matched it.

    `terms_of(paper)` yields the terms a paper matched; `keep` is an ordered list of the
    terms to restrict to. The result follows that order, minus any term whose papers all
    lack vectors - order matters because the cluster labels downstream are positional, so
    passing an unordered set here would make the output non-reproducible. SPECTER2 is a
    cosine space, hence the normalisation.
    """
    wanted = set(keep)
    vectors = fetch([p["arxiv_id"] for p in papers], npz, api_key)
    per_term = defaultdict(list)
    for p in papers:
        v = vectors.get(p["arxiv_id"])
        if v is None:
            continue
        for t in terms_of(p):
            if t in wanted:
                per_term[t].append(v)
    terms = [t for t in keep if per_term.get(t)]
    X = np.array([np.mean(per_term[t], axis=0) for t in terms], dtype=np.float32)
    return terms, X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-9), per_term


def kmeans_pca(Xn, k):
    """Cluster labels plus a 2-D PCA layout scaled into the unit square."""
    labels = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(Xn)
    xy = PCA(n_components=2, random_state=42).fit_transform(Xn)
    return labels, (xy - xy.min(0)) / (xy.max(0) - xy.min(0) + 1e-9)
