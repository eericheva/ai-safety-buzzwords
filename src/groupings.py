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
import csv, os
from collections import defaultdict, Counter

import common
import cooccur_graph
from buzzwords import BUZZWORDS, variants

EDGE_MIN_WEIGHT = 5       # the network view only shows well-attested pairs
EDGE_LIMIT = 400
term_group = {t: common.group_of(c) for t, c, _ in BUZZWORDS}


def paper_terms():
    """{arxiv_id: set(terms)} over the FULL verified sets (not the capped table)."""
    p2t = defaultdict(set)
    for t, _, _ in BUZZWORDS:
        hit = common.matcher(variants(t))
        d = common.read_json(common.RAW, common.slug(t) + ".json")
        for pp in (d.get("data") or []):
            axid = (pp.get("externalIds") or {}).get("ArXiv")
            if not axid:
                continue
            text = (pp.get("title") or "") + " . " + (pp.get("abstract") or "")
            if hit(text):
                p2t[axid].add(t)
    return p2t


# ---------------------------------------------------------------- co-occurrence
def cooccur():
    G, comms, deg, mod = cooccur_graph.communities(paper_terms().values(), term_group)

    # label each community by its dominant glossary macro-theme + top terms
    clusters = []
    for i, cset in enumerate(comms):
        # tiebreak by name: communities are sets, so equal paper counts would otherwise
        # order members by PYTHONHASHSEED, moving top_terms and the dominant theme
        members = sorted(cset, key=lambda t: (-deg[t], t))
        theme_ct = Counter(term_group[t] for t in members)
        dom_theme, _ = theme_ct.most_common(1)[0]
        purity = round(theme_ct[dom_theme] / len(members), 2)
        clusters.append({
            "id": i, "size": len(members),
            "dominant_theme": dom_theme, "purity": purity,
            "top_terms": members[:8], "members": members,
        })

    out = {
        "n_nodes": G.number_of_nodes(), "n_edges": G.number_of_edges(),
        "modularity": mod,
        "n_clusters": len(clusters),
        "clusters": clusters,
        "deg": dict(deg),
        "edges": cooccur_graph.strongest_edges(G, EDGE_MIN_WEIGHT, EDGE_LIMIT),
        "term_group": term_group, "group_color": common.GROUP_COLOR,
    }
    common.write_json(out, common.DATA, "grouping_cooccur.json")
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
    1:  ("Misinformation", "False or misleading information", False),
    2:  ("Malicious actors & misuse", "Cyberattacks, weapon development or use, and mass harm", False),
    3:  ("Discrimination & toxicity", "Unfair discrimination and misrepresentation", False),
    4:  ("Human-computer interaction", "Overreliance and unsafe use", False),
    5:  ("AI system safety, failures & limitations", "AI pursuing its own goals in conflict with human values", False),
    6:  ("Privacy & security", "AI system security vulnerabilities and attacks", False),
    7:  ("Privacy & security", "Compromise of privacy by obtaining, leaking or correctly inferring sensitive information", False),
    8:  ("Human-computer interaction", "Loss of human agency and autonomy", False),
    9:  ("AI system safety, failures & limitations", "Lack of transparency or interpretability", True),
    11: ("Misinformation", "False or misleading information", False),
    12: ("AI system safety, failures & limitations", "Lack of transparency or interpretability", True),
    13: ("AI system safety, failures & limitations", "AI pursuing its own goals in conflict with human values", True),
    14: ("Discrimination & toxicity", "Unequal performance across groups", False),
    15: ("AI system safety, failures & limitations", "Multi-agent risks", False),
    16: ("Human-computer interaction", "Overreliance and unsafe use", False),
    17: ("Privacy & security", "AI system security vulnerabilities and attacks", True),
    18: ("AI system safety, failures & limitations", "AI pursuing its own goals in conflict with human values", True),
    19: ("Socioeconomic & environmental", "Power centralization and unfair distribution of benefits", False),
    20: ("AI system safety, failures & limitations", "AI welfare and rights", False),
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


def mit_map():
    stats = list(csv.DictReader(open(os.path.join(common.DATA, "buzzword_stats.csv"))))
    n_by_term = {r["term"]: int(r["n_papers"]) for r in stats}

    term_rows = []
    sub_cover = defaultdict(lambda: {"terms": [], "papers": 0})
    for t, c, _ in BUZZWORDS:
        dom, sub, is_method = TERM_MIT.get(t) or CLUSTER_MIT[common.cluster_num(c)]
        term_rows.append({"term": t, "cluster": c, "domain": dom, "subdomain": sub,
                          "is_method": is_method, "n_papers": n_by_term[t]})
        sub_cover[(dom, sub)]["terms"].append(t)
        sub_cover[(dom, sub)]["papers"] += n_by_term[t]

    coverage = []
    for dom in common.MIT_DOMAINS:
        for sub in common.MIT_SUBS[dom]:
            cov = sub_cover[(dom, sub)]    # empty entry for an uncovered subdomain
            coverage.append({"domain": dom, "subdomain": sub,
                             "n_terms": len(cov["terms"]), "n_papers": cov["papers"],
                             "terms": sorted(cov["terms"], key=lambda x: -n_by_term[x])[:10]})
    n_cov = sum(1 for c in coverage if c["n_terms"] > 0)
    out = {"domains": common.MIT_DOMAINS, "term_rows": term_rows, "coverage": coverage,
           "n_subdomains": len(coverage), "n_covered": n_cov,
           "n_method_terms": sum(1 for r in term_rows if r["is_method"])}
    common.write_json(out, common.DATA, "grouping_mit.json")
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
