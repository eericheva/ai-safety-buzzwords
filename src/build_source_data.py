# -*- coding: utf-8 -*-
"""Turn a collected candidate source (data/src_<source>/terms.json + papers.csv)
into the SAME page data shapes as the curated corpus. Grouping lenses:
  co-occurrence  (local, from paper term co-occurrence)
  semantic       (SPECTER2 embeddings from S2 -> k-means + PCA)
glossary/MIT don't apply to bottom-up candidate terms.

Writes data/src_<source>/{viz_data,trends_data,taxonomy_map}.json
"""
import csv, json, os, re, sys, time, urllib.request
from collections import Counter, defaultdict
import numpy as np
import networkx as nx
from wordcloud import WordCloud
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

from taxonomy_map import packed_layout

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Y0, Y1 = 2015, 2026
API_KEY = "s2k-ZOHSvEHee6VvgAyjrfPDQ88TXPswpt5ts8AOMUuU"
BATCH = "https://api.semanticscholar.org/graph/v1/paper/batch?fields=embedding.specter_v2"
CAT_L = ['#2a78d6', '#008300', '#e87ba4', '#eda100', '#1baf7a', '#eb6834', '#4a3aa7', '#e34948']
CAT_D = ['#3987e5', '#38ad38', '#e87ba4', '#eda100', '#1baf7a', '#eb6834', '#9085e9', '#e66767']

WEIGHT_METRICS = [{"key": "papers", "label": "Papers"}, {"key": "citations", "label": "Citations"},
                  {"key": "cpp", "label": "Citations / paper"}, {"key": "recency", "label": "Recency"},
                  {"key": "momentum", "label": "Momentum"}, {"key": "debut", "label": "Debut yr"},
                  {"key": "peak", "label": "Peak yr"}]


def cloud_svg(freqs):
    wc = None
    for mn in (7, 8, 9, 10, 12, 14):        # bump min font on PIL "division by zero" at tiny sizes
        try:
            wc = WordCloud(background_color="#faf9f6", width=2100, height=1150, prefer_horizontal=0.94,
                           relative_scaling=0.40, min_font_size=mn, max_font_size=115, font_step=1,
                           margin=1, collocations=False, random_state=42, max_words=400,
                           font_path="/System/Library/Fonts/Helvetica.ttc")
            wc.generate_from_frequencies(freqs)
            break
        except (ZeroDivisionError, OSError):
            wc = None
    if wc is None:
        raise RuntimeError("wordcloud failed for all min_font_size")
    svg = wc.to_svg(embed_font=False)
    svg = re.sub(r'<svg xmlns="([^"]*)" width="(\d+)" height="(\d+)"',
                 r'<svg xmlns="\1" viewBox="0 0 \2 \3" width="100%" preserveAspectRatio="xMidYMid meet"', svg, 1)
    svg = re.sub(r'<rect\b[^>]*/?>', '', svg, 1)
    svg = svg.replace("font-family:'Helvetica';", "font-family:'Helvetica',Arial,system-ui,sans-serif;")
    import html as _h
    svg = re.sub(r'(<text\b[^>]*)>([^<]*)</text>',
                 lambda m: '%s data-term="%s">%s</text>' % (m.group(1), _h.escape(m.group(2), quote=True), m.group(2)), svg)
    return svg


def fetch_emb(ids, npz):
    cache = {}
    if os.path.exists(npz):
        z = np.load(npz, allow_pickle=True)
        cache = {k: v for k, v in zip(z["ids"], z["vecs"])}
    need = [i for i in ids if i not in cache]
    print("  embeddings: cached=%d need=%d" % (len(cache), len(need)))
    for s in range(0, len(need), 400):
        chunk = need[s:s + 400]
        body = json.dumps({"ids": ["ARXIV:" + i for i in chunk]}).encode()
        req = urllib.request.Request(BATCH, data=body,
              headers={"x-api-key": API_KEY, "Content-Type": "application/json"})
        data = None
        for a in range(6):
            try:
                with urllib.request.urlopen(req, timeout=90) as r:
                    data = json.load(r); break
            except Exception as e:
                print("    retry", a + 1, e); time.sleep(3 * (a + 1))
        if data is None:
            continue
        for i, pp in zip(chunk, data):
            v = ((pp or {}).get("embedding") or {}).get("vector")
            if v:
                cache[i] = np.asarray(v, dtype=np.float32)
        print("    fetched %d/%d" % (min(s + 400, len(need)), len(need)))
        time.sleep(1.2)
    np.savez_compressed(npz, ids=np.array(list(cache.keys())),
                        vecs=np.array(list(cache.values()), dtype=np.float32))
    return cache


def cooccur_lens(tmap, papers, deg):
    pair = Counter()
    for p in papers:
        ts = [x for x in p["terms"].split("; ") if x in tmap]
        for i in range(len(ts)):
            for j in range(i + 1, len(ts)):
                a, b = sorted((ts[i], ts[j])); pair[(a, b)] += 1
    G = nx.Graph()
    for t in tmap:
        G.add_node(t)
    for (a, b), w in pair.items():
        if w >= 2:
            G.add_edge(a, b, weight=w)
    comms = sorted(nx.community.louvain_communities(G, weight="weight", seed=42), key=len, reverse=True)
    ISO = "Isolated"
    grp, groups = {}, []
    for cs in [c for c in comms if len(c) >= 3]:
        members = sorted(cs, key=lambda t: deg[t], reverse=True)
        lab = "%s +" % members[0]; groups.append(lab)
        for m in members:
            grp[m] = lab
    groups.append(ISO)
    for t in tmap:
        grp.setdefault(t, ISO)
    if len(groups) > 8:
        keep = groups[:7]
        for t in list(grp):
            if grp[t] not in keep:
                grp[t] = ISO
        groups = keep + [ISO]
    mod = round(nx.community.modularity(G, comms, weight="weight"), 3)
    return grp, groups, packed_layout({t: grp[t] for t in tmap}, groups), mod


def semantic_lens(tmap, papers, npz):
    emb = fetch_emb([p["arxiv_id"] for p in papers], npz)
    tv = defaultdict(list)
    for p in papers:
        v = emb.get(p["arxiv_id"])
        if v is None:
            continue
        for x in p["terms"].split("; "):
            if x in tmap:
                tv[x].append(v)
    terms = [t for t in tmap if tv.get(t)]
    if len(terms) < 4:
        return None
    X = np.array([np.mean(tv[t], axis=0) for t in terms], dtype=np.float32)
    Xn = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-9)
    K = min(8, max(3, len(terms) // 10))
    labels = KMeans(n_clusters=K, n_init=10, random_state=42).fit_predict(Xn)
    xy = PCA(n_components=2, random_state=42).fit_transform(Xn)
    xy = (xy - xy.min(0)) / (xy.max(0) - xy.min(0) + 1e-9)
    clusters = defaultdict(list)
    for i, t in enumerate(terms):
        clusters[int(labels[i])].append(t)
    grp, groups = {}, []
    for k in sorted(clusters):
        members = sorted(clusters[k], key=lambda t: -tmap[t]["n_papers"])
        lab = "S%d · %s" % (k, ", ".join(members[:2]))
        groups.append(lab)
        for m in members:
            grp[m] = lab
    pos = {terms[i]: [round(float(xy[i, 0]), 4), round(float(xy[i, 1]), 4)] for i in range(len(terms))}
    for t in tmap:                      # terms without embeddings -> first cluster, centre
        grp.setdefault(t, groups[0])
        pos.setdefault(t, [0.5, 0.5])
    return grp, groups, pos


def main(source):
    d = os.path.join(HERE, "data", "src_" + source)
    terms = json.load(open(os.path.join(d, "terms.json")))
    papers = list(csv.DictReader(open(os.path.join(d, "papers.csv"))))
    for p in papers:
        p["citationCount"] = int(p["citationCount"] or 0)
    tmap = {t["term"]: t for t in terms}
    deg = Counter()
    for p in papers:
        for x in p["terms"].split("; "):
            if x in tmap:
                deg[x] += 1

    # ---- lenses ----
    LENS = {}
    layouts = {}
    co_grp, co_groups, co_layout, mod = cooccur_lens(tmap, papers, deg)
    LENS["cooccur"] = (co_grp, co_groups); layouts["cooccur"] = co_layout
    sem = semantic_lens(tmap, papers, os.path.join(d, "embeddings.npz"))
    if sem:
        sem_grp, sem_groups, sem_pos = sem
        LENS["semantic"] = (sem_grp, sem_groups); layouts["semantic"] = sem_pos

    lens_meta = {}
    for ln, (grp, groups) in LENS.items():
        lens_meta[ln] = {"label": "Semantic" if ln == "semantic" else "Co-occurrence",
                         "groups": groups,
                         "colors": {g: CAT_L[i % 8] for i, g in enumerate(groups)},
                         "colors_dark": {g: CAT_D[i % 8] for i, g in enumerate(groups)}}
    lens_order = list(LENS.keys())

    def lenses_of(t):
        return {ln: LENS[ln][0][t] for ln in lens_order}

    def col(ln, g):
        return lens_meta[ln]["colors"][g]

    # primary lens for the legacy 'group' field + group_color = first lens (cooccur)
    p0 = "cooccur"

    # ---- cloud SVGs per metric ----
    def mv(t, k):
        if k == "debut": return max((t["debut"] or 2005) - 2004, 1)
        if k == "peak": return max((t["peak"] or 2005) - 2004, 1)
        return t[{"papers": "n_papers", "citations": "sum_citations"}.get(k, k)]
    cloud_svgs = {}
    for m in WEIGHT_METRICS:
        cloud_svgs[m["key"]] = cloud_svg({t["term"]: max(mv(t, m["key"]) ** 0.5, 0.05) for t in terms})
    print("  clouds done")

    # ---- viz_data ----
    stats = []
    for t in terms:
        stats.append({"term": t["term"], "group": co_grp[t["term"]], "lenses": lenses_of(t["term"]),
                      "n_papers": t["n_papers"], "sum_citations": t["sum_citations"], "cpp": t["cpp"],
                      "recency": t["recency"], "momentum": t["momentum"],
                      "median_year": t["median_year"], "first_year": t["first_year"],
                      "debut": t["debut"], "peak": t["peak"]})
    yearly = defaultdict(int)
    for p in papers:
        if p["year"]:
            yearly[int(p["year"])] += 1
    viz = {"generated": "2026-07-19", "source": source,
           "n_papers": len(papers), "n_buzzwords": len(terms),
           "total_citations": sum(p["citationCount"] for p in papers),
           "year_min": min(yearly) if yearly else Y0, "year_max": max(yearly) if yearly else Y1,
           "groups": lens_meta[p0]["groups"], "group_color": lens_meta[p0]["colors"],
           "group_color_dark": lens_meta[p0]["colors_dark"], "lens_meta": lens_meta,
           "cloud_svg": cloud_svgs["papers"], "cloud_svgs": cloud_svgs, "cloud_metrics": WEIGHT_METRICS,
           "stats": stats, "yearly": [{"year": y, "n": yearly[y]} for y in sorted(yearly)]}
    json.dump(viz, open(os.path.join(d, "viz_data.json"), "w"), ensure_ascii=False)

    # ---- trends_data (streams per lens) ----
    axcit = {}
    lens_year = {ln: defaultdict(lambda: defaultdict(set)) for ln in lens_order}
    for p in papers:
        y = int(p["year"]) if p["year"] else None
        if not y or not (Y0 <= y <= Y1):
            continue
        axcit[p["arxiv_id"]] = p["citationCount"]
        for x in p["terms"].split("; "):
            if x in tmap:
                for ln in lens_order:
                    lens_year[ln][LENS[ln][0][x]][y].add(p["arxiv_id"])
    streams, streams_c = {}, {}
    for ln in lens_order:
        rows, rows_c = [], []
        for y in range(Y0, Y1 + 1):
            r, rc = {"y": y}, {"y": y}
            for g in lens_meta[ln]["groups"]:
                ax = lens_year[ln][g].get(y, ())
                r[g] = len(ax); rc[g] = sum(axcit.get(a, 0) for a in ax)
            rows.append(r); rows_c.append(rc)
        streams[ln] = rows; streams_c[ln] = rows_c
    terms_out = []
    for t in terms:
        terms_out.append({"term": t["term"], "group": co_grp[t["term"]], "series": t["series"],
                          "total_n": t["n_papers"], "total_c": t["sum_citations"],
                          "metrics": {"papers": t["n_papers"], "citations": t["sum_citations"], "cpp": t["cpp"],
                                      "recency": t["recency"], "momentum": t["momentum"],
                                      "debut": t["debut"], "peak": t["peak"]},
                          "peak_year": t["peak"], "debut": t["debut"], "first_year": t["first_year"],
                          "lenses": lenses_of(t["term"])})
    terms_out.sort(key=lambda t: t["total_n"], reverse=True)
    tr = {"generated": "2026-07-19", "source": source, "y0": Y0, "y1": Y1,
          "groups": lens_meta[p0]["groups"], "group_color": lens_meta[p0]["colors"],
          "group_color_dark": lens_meta[p0]["colors_dark"], "lens_meta": lens_meta,
          "weight_metrics": WEIGHT_METRICS, "streams": streams, "streams_c": streams_c,
          "terms": terms_out, "stream": streams[p0]}
    json.dump(tr, open(os.path.join(d, "trends_data.json"), "w"), ensure_ascii=False)

    # ---- taxonomy_map ----
    trows = [{"term": t["term"], "lenses": lenses_of(t["term"]),
              "m": {"papers": t["n_papers"], "citations": t["sum_citations"], "cpp": t["cpp"],
                    "recency": t["recency"], "momentum": t["momentum"], "debut": t["debut"] or 0, "peak": t["peak"] or 0}}
             for t in terms]
    mp = {"generated": "2026-07-19", "source": source, "terms": trows, "layouts": layouts,
          "lens_meta": lens_meta, "weight_metrics": WEIGHT_METRICS, "mit_gaps": [], "cooccur_modularity": mod}
    json.dump(mp, open(os.path.join(d, "taxonomy_map.json"), "w"), ensure_ascii=False)

    print("DONE %s: %d terms, %d papers, lenses=%s" % (source, len(terms), len(papers), lens_order))


if __name__ == "__main__":
    main(sys.argv[1])
