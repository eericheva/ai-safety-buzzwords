# -*- coding: utf-8 -*-
"""Alternative groupings of the buzzwords, as extra 'lenses' beside the manual
glossary/8-theme grouping:

  cooccur  -- community detection on the buzzword co-occurrence graph
              (two terms linked if they appear in the same arXiv paper).
              Purely data-driven: which buzzwords actually travel together.
  mit      -- map each glossary cluster onto the MIT AI Risk Repository domain
              taxonomy (arXiv:2408.12622) + coverage/gap analysis.

Semantic-embedding clustering lives in groupings_embed.py (needs the S2 API).

Outputs: data/grouping_cooccur.json, data/grouping_mit.json
"""
import csv, json, os, re
from collections import defaultdict, Counter
import networkx as nx

from build_viz import group_of, GROUP_COLOR, slug
from buzzwords import BUZZWORDS, variants

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, "data", "raw2")
term_cluster = {t: c for t, c, _ in BUZZWORDS}
term_group = {t: group_of(c) for t, c, _ in BUZZWORDS}


def paper_terms():
    """{arxiv_id: set(terms)} over the FULL verified sets (not the capped table)."""
    p2t = defaultdict(set)
    for t, c, _ in BUZZWORDS:
        pats = [re.compile(r"\b" + re.escape(v), re.IGNORECASE) for v in variants(t)]
        d = json.load(open(os.path.join(RAW, slug(t) + ".json")))
        for pp in (d.get("data") or []):
            axid = (pp.get("externalIds") or {}).get("ArXiv")
            if not axid:
                continue
            text = (pp.get("title") or "") + " . " + (pp.get("abstract") or "")
            if any(p.search(text) for p in pats):
                p2t[axid].add(t)
    return p2t


# ---------------------------------------------------------------- co-occurrence
def cooccur():
    p2t = paper_terms()
    pair = Counter()
    deg = Counter()
    for terms in p2t.values():
        terms = sorted(terms)
        for t in terms:
            deg[t] += 1
        for i in range(len(terms)):
            for j in range(i + 1, len(terms)):
                pair[(terms[i], terms[j])] += 1

    G = nx.Graph()
    for t in term_cluster:
        G.add_node(t)
    for (a, b), w in pair.items():
        if w >= 2:                      # ignore one-off co-mentions
            G.add_edge(a, b, weight=w)

    # Louvain community detection (weighted)
    comms = nx.community.louvain_communities(G, weight="weight", seed=42, resolution=1.0)
    comms = sorted(comms, key=len, reverse=True)

    # label each community by its dominant glossary macro-theme + top terms
    clusters = []
    for i, cset in enumerate(comms):
        members = sorted(cset, key=lambda t: deg[t], reverse=True)
        theme_ct = Counter(term_group[t] for t in members)
        dom_theme, _ = theme_ct.most_common(1)[0]
        purity = round(theme_ct[dom_theme] / len(members), 2)
        clusters.append({
            "id": i, "size": len(members),
            "dominant_theme": dom_theme, "purity": purity,
            "top_terms": members[:8], "members": members,
        })

    # strongest edges for a small network view
    edges = sorted(({"a": a, "b": b, "w": w} for (a, b), w in pair.items() if w >= 5),
                   key=lambda e: -e["w"])[:400]
    out = {
        "n_nodes": G.number_of_nodes(), "n_edges": G.number_of_edges(),
        "modularity": round(nx.community.modularity(G, comms, weight="weight"), 3),
        "n_clusters": len(clusters),
        "clusters": clusters,
        "deg": dict(deg),
        "edges": edges,
        "term_group": term_group, "group_color": GROUP_COLOR,
    }
    json.dump(out, open(os.path.join(HERE, "data", "grouping_cooccur.json"), "w"),
              ensure_ascii=False)
    print("cooccur: %d nodes, %d edges, %d communities, modularity %.3f"
          % (out["n_nodes"], out["n_edges"], out["n_clusters"], out["modularity"]))
    for c in clusters:
        print(f"  C{c['id']} (n={c['size']}, {c['dominant_theme'].split(',')[0]}, purity {c['purity']}): "
              + ", ".join(c["top_terms"][:6]))
    return out


# --------------------------------------------------------------------- MIT map
# MIT AI Risk Repository Domain Taxonomy (arXiv:2408.12622v2): 7 domains / 24 subdomains.
# Each glossary cluster -> (domain, subdomain). Method/measurement clusters that are
# not themselves a *risk* are flagged is_method=True (MIT is a risk taxonomy).
CLUSTER_MIT = {
    "1":  ("Misinformation", "False or misleading information", False),
    "2":  ("Malicious actors & misuse", "Cyberattacks, weapon development or use, and mass harm", False),
    "3":  ("Discrimination & toxicity", "Unfair discrimination and misrepresentation", False),
    "4":  ("Human-computer interaction", "Overreliance and unsafe use", False),
    "5":  ("AI system safety, failures & limitations", "AI pursuing its own goals in conflict with human values", False),
    "6":  ("Privacy & security", "AI system security vulnerabilities and attacks", False),
    "7":  ("Privacy & security", "Compromise of privacy by obtaining, leaking or correctly inferring sensitive information", False),
    "8":  ("Human-computer interaction", "Loss of human agency and autonomy", False),
    "9":  ("AI system safety, failures & limitations", "Lack of transparency or interpretability", True),
    "11": ("Misinformation", "False or misleading information", False),
    "12": ("AI system safety, failures & limitations", "Lack of transparency or interpretability", True),
    "13": ("AI system safety, failures & limitations", "AI pursuing its own goals in conflict with human values", True),
    "14": ("Discrimination & toxicity", "Unequal performance across groups", False),
    "15": ("AI system safety, failures & limitations", "Multi-agent risks", False),
    "16": ("Human-computer interaction", "Overreliance and unsafe use", False),
    "17": ("Privacy & security", "AI system security vulnerabilities and attacks", True),
    "18": ("AI system safety, failures & limitations", "AI pursuing its own goals in conflict with human values", True),
    "19": ("Socioeconomic & environmental", "Power centralization and unfair distribution of benefits", False),
    "20": ("AI system safety, failures & limitations", "AI welfare and rights", False),
}
MIT_DOMAINS = ["Discrimination & toxicity", "Privacy & security", "Misinformation",
               "Malicious actors & misuse", "Human-computer interaction",
               "Socioeconomic & environmental", "AI system safety, failures & limitations"]
MIT_SUBS = {  # all 24 subdomains per domain, for coverage
    "Discrimination & toxicity": ["Unfair discrimination and misrepresentation",
        "Exposure to toxic content", "Unequal performance across groups"],
    "Privacy & security": ["Compromise of privacy by obtaining, leaking or correctly inferring sensitive information",
        "AI system security vulnerabilities and attacks"],
    "Misinformation": ["False or misleading information",
        "Pollution of information ecosystem and loss of consensus reality"],
    "Malicious actors & misuse": ["Disinformation, surveillance, and influence at scale",
        "Cyberattacks, weapon development or use, and mass harm", "Fraud, scams, and targeted manipulation"],
    "Human-computer interaction": ["Overreliance and unsafe use", "Loss of human agency and autonomy"],
    "Socioeconomic & environmental": ["Power centralization and unfair distribution of benefits",
        "Increased inequality and decline in employment quality", "Economic and cultural devaluation of human effort",
        "Competitive dynamics", "Governance failure", "Environmental harm"],
    "AI system safety, failures & limitations": ["AI pursuing its own goals in conflict with human values",
        "AI possessing dangerous capabilities", "Lack of capability or robustness",
        "Lack of transparency or interpretability", "AI welfare and rights", "Multi-agent risks"],
}


# term-level refinements where a cluster default is too coarse (better coverage)
TERM_MIT = {
    "toxicity": ("Discrimination & toxicity", "Exposure to toxic content", False),
    "dangerous capabilities": ("AI system safety, failures & limitations", "AI possessing dangerous capabilities", False),
    "adversarial robustness": ("AI system safety, failures & limitations", "Lack of capability or robustness", False),
    "prompt sensitivity": ("AI system safety, failures & limitations", "Lack of capability or robustness", False),
    "influence operations": ("Malicious actors & misuse", "Disinformation, surveillance, and influence at scale", False),
    "manipulation": ("Malicious actors & misuse", "Fraud, scams, and targeted manipulation", False),
    "emotional manipulation": ("Malicious actors & misuse", "Fraud, scams, and targeted manipulation", False),
    "persuasion": ("Malicious actors & misuse", "Fraud, scams, and targeted manipulation", False),
    "dark patterns": ("Malicious actors & misuse", "Fraud, scams, and targeted manipulation", False),
    "hallucination": ("Misinformation", "False or misleading information", False),
    "delusional spiral": ("Misinformation", "Pollution of information ecosystem and loss of consensus reality", False),
    "gradual disempowerment": ("Socioeconomic & environmental", "Power centralization and unfair distribution of benefits", False),
    "automated decision-making": ("Discrimination & toxicity", "Unfair discrimination and misrepresentation", False),
    "advice in regulated industries": ("Human-computer interaction", "Overreliance and unsafe use", False),
}


def cluster_num(c):
    return c.split(".")[0].strip()


def mit_map():
    stats = list(csv.DictReader(open(os.path.join(HERE, "data", "buzzword_stats.csv"))))
    n_by_term = {r["term"]: int(r["n_papers"]) for r in stats}

    term_rows = []
    sub_cover = defaultdict(lambda: {"terms": [], "papers": 0})
    for t, c, _ in BUZZWORDS:
        if t in TERM_MIT:
            dom, sub, is_method = TERM_MIT[t]
        else:
            dom, sub, is_method = CLUSTER_MIT[cluster_num(c)]
        term_rows.append({"term": t, "cluster": c, "domain": dom, "subdomain": sub,
                          "is_method": is_method, "n_papers": n_by_term.get(t, 0)})
        sub_cover[(dom, sub)]["terms"].append(t)
        sub_cover[(dom, sub)]["papers"] += n_by_term.get(t, 0)

    coverage = []
    for dom in MIT_DOMAINS:
        for sub in MIT_SUBS[dom]:
            cov = sub_cover.get((dom, sub))
            coverage.append({"domain": dom, "subdomain": sub,
                             "n_terms": len(cov["terms"]) if cov else 0,
                             "n_papers": cov["papers"] if cov else 0,
                             "terms": sorted(cov["terms"], key=lambda x: -n_by_term.get(x, 0))[:10] if cov else []})
    n_cov = sum(1 for c in coverage if c["n_terms"] > 0)
    out = {"domains": MIT_DOMAINS, "term_rows": term_rows, "coverage": coverage,
           "n_subdomains": len(coverage), "n_covered": n_cov,
           "n_method_terms": sum(1 for r in term_rows if r["is_method"])}
    json.dump(out, open(os.path.join(HERE, "data", "grouping_mit.json"), "w"), ensure_ascii=False)
    print("\nMIT: %d/%d subdomains covered; %d method-terms don't fit a risk domain"
          % (n_cov, len(coverage), out["n_method_terms"]))
    print("  uncovered subdomains:")
    for c in coverage:
        if c["n_terms"] == 0:
            print("   -", c["domain"].split(",")[0], "/", c["subdomain"][:55])
    return out


if __name__ == "__main__":
    cooccur()
    mit_map()
