# -*- coding: utf-8 -*-
"""The co-occurrence graph: two terms are linked when one paper mentions both.

Both branches build it - the curated one over the per-term cache, the mined one over a
source's papers.csv - and both then name the communities differently, the curated one by
its dominant glossary theme and the mined one by its biggest member. So the shared part
is the graph and the Louvain step, not the labelling, and that is all this holds.

Separate from common.py because it is the pipeline's only networkx dependency, and the
page builders have to import common on a bare interpreter.
"""
from collections import Counter

import networkx as nx

MIN_PAIR = 2          # a single co-mention is coincidence, not an edge
SEED = 42             # Louvain is randomised; pinning it makes the lens reproducible


def communities(paper_terms, terms):
    """`paper_terms` iterates one term set per paper; `terms` lists every node that must
    exist, so a term nobody co-mentions stays in the graph as an isolate rather than
    vanishing from the lens.

    Returns the graph, its communities largest first, the per-term paper count, and the
    modularity of that partition.
    """
    pair, deg = Counter(), Counter()
    for ts in paper_terms:
        ts = sorted(ts)
        for t in ts:
            deg[t] += 1
        for i in range(len(ts)):
            for j in range(i + 1, len(ts)):
                pair[(ts[i], ts[j])] += 1

    G = nx.Graph()
    G.add_nodes_from(terms)
    G.add_edges_from((a, b, {"weight": w}) for (a, b), w in pair.items() if w >= MIN_PAIR)
    comms = sorted(nx.community.louvain_communities(G, weight="weight", seed=SEED),
                   key=len, reverse=True)
    return G, comms, deg, round(nx.community.modularity(G, comms, weight="weight"), 3)


def strongest_edges(G, min_weight, limit):
    """Heaviest edges for a small network view, ordered by weight then name so that ties
    do not depend on graph insertion order."""
    edges = [{"a": a, "b": b, "w": w} for a, b, w in G.edges(data="weight")
             if w >= min_weight]
    edges.sort(key=lambda e: (-e["w"], e["a"], e["b"]))
    return edges[:limit]
