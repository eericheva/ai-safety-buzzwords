# -*- coding: utf-8 -*-
"""Shared building blocks: paths, JSON io, phrase matching, the 8 macro-themes,
the categorical palettes and the weight-metric table.

Every name here used to be copy-pasted: `slug()` and the phrase matcher lived in
four files each, `HERE` in all sixteen, the weight metrics in four, the dark
palette in three. `GROUPS` sits here rather than in build_viz.py so lenses.py can
read it directly -- that import cycle is why `import lenses` used to hide in the
middle of build_viz.main().

Stdlib only, on purpose: the three page builders run on a bare interpreter, so
numpy goes in embed.py and wordcloud in cloud.py instead.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "data")
RAW = os.path.join(DATA, "raw2")           # per-term candidate cache, with abstracts
WEB = os.path.join(HERE, "web")
TEMPLATES = os.path.join(HERE, "templates")

Y0, Y1 = 2015, 2026                        # trend window
TOP_N = 60                                 # papers kept per term for the paper table


def read_json(*parts):
    with open(os.path.join(*parts), encoding="utf-8") as f:
        return json.load(f)


def write_json(obj, *parts):
    with open(os.path.join(*parts), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)


def slug(term):
    return re.sub(r"[^a-z0-9]+", "-", term.lower()).strip("-")


def matcher(surfaces):
    """Whole-word phrase test over title+abstract. Word-boundary at the start only,
    so any suffix matches while `scheme` still cannot satisfy `scheming`."""
    pats = [re.compile(r"\b" + re.escape(s), re.IGNORECASE) for s in surfaces]
    return lambda text: any(p.search(text) for p in pats)


# --- 8 macro-themes (glossary cluster number -> theme); keeps categorical hues <=8 ---
# Section 10 is absent deliberately: it is the umbrella-taxonomies meta-section and
# tracks no terms of its own.
GROUPS = {
    "Truth & hallucination":             {1, 11},
    "Harm, bias & fairness":             {2, 3},
    "Interaction & affective":           {4, 16},
    "Alignment, goals & control":        {5, 18, 19, 14, 20},
    "Attacks, robustness & training":    {6, 17},
    "Privacy, data & memory":            {7},
    "Agents & multi-agent":              {8, 15},
    "Interpretability & self-knowledge": {9, 12, 13},
}
GROUP_ORDER = list(GROUPS.keys())
CLUSTER_GROUP = {n: g for g, nums in GROUPS.items() for n in nums}

# readable-on-white hues, categorical order from the validated palette (deepened)
GROUP_COLOR = {
    "Truth & hallucination":              "#1f5fb0",  # blue
    "Harm, bias & fairness":              "#1f7a1f",  # green
    "Interaction & affective":            "#b03a6e",  # magenta
    "Alignment, goals & control":         "#9a6a00",  # amber
    "Attacks, robustness & training":     "#0f7a58",  # teal
    "Privacy, data & memory":             "#c14a1f",  # orange
    "Agents & multi-agent":               "#4a3aa7",  # violet
    "Interpretability & self-knowledge":  "#b3332f",  # red
}
GROUP_COLOR_DARK = {  # brighter hues for dark backgrounds
    "Truth & hallucination": "#5598e7", "Harm, bias & fairness": "#38ad38",
    "Interaction & affective": "#e87ba4", "Alignment, goals & control": "#eda100",
    "Attacks, robustness & training": "#1baf7a", "Privacy, data & memory": "#eb6834",
    "Agents & multi-agent": "#9085e9", "Interpretability & self-knowledge": "#e66767",
}

# per-lens categorical palettes, indexed by group position
CAT_LIGHT = ['#2a78d6', '#008300', '#e87ba4', '#eda100', '#1baf7a', '#eb6834', '#4a3aa7', '#e34948']
CAT_DARK = ['#3987e5', '#38ad38', '#e87ba4', '#eda100', '#1baf7a', '#eb6834', '#9085e9', '#e66767']


def cluster_num(cluster):
    return int(re.match(r"\s*(\d+)", cluster).group(1))


def group_of(cluster):
    """An unmapped cluster raises KeyError, and that is the point: this used to
    return "Alignment, goals & control" for anything it did not recognise, so
    adding a glossary section moved its terms into a real theme without a word."""
    return CLUSTER_GROUP[cluster_num(cluster)]


def lens_colors(groups):
    return ({g: CAT_LIGHT[i % 8] for i, g in enumerate(groups)},
            {g: CAT_DARK[i % 8] for i, g in enumerate(groups)})


# MIT AI Risk Repository Domain Taxonomy (arXiv:2408.12622v2, Table 6): 7 domains and
# their 24 subdomains, verbatim. groupings.py maps glossary clusters onto it, discover.py
# diffs it against the glossary to find gaps -- and each carried its own copy of the
# table, with the domain order repeated a third time as a separate list.
MIT_SUBS = {
    "Discrimination & toxicity": [
        "Unfair discrimination and misrepresentation",
        "Exposure to toxic content",
        "Unequal performance across groups"],
    "Privacy & security": [
        "Compromise of privacy by obtaining, leaking or correctly inferring sensitive information",
        "AI system security vulnerabilities and attacks"],
    "Misinformation": [
        "False or misleading information",
        "Pollution of information ecosystem and loss of consensus reality"],
    "Malicious actors & misuse": [
        "Disinformation, surveillance, and influence at scale",
        "Cyberattacks, weapon development or use, and mass harm",
        "Fraud, scams, and targeted manipulation"],
    "Human-computer interaction": [
        "Overreliance and unsafe use",
        "Loss of human agency and autonomy"],
    "Socioeconomic & environmental": [
        "Power centralization and unfair distribution of benefits",
        "Increased inequality and decline in employment quality",
        "Economic and cultural devaluation of human effort",
        "Competitive dynamics",
        "Governance failure",
        "Environmental harm"],
    "AI system safety, failures & limitations": [
        "AI pursuing its own goals in conflict with human values",
        "AI possessing dangerous capabilities",
        "Lack of capability or robustness",
        "Lack of transparency or interpretability",
        "AI welfare and rights",
        "Multi-agent risks"],
}
MIT_DOMAINS = list(MIT_SUBS)

WEIGHT_METRICS = [
    {"key": "papers", "label": "Papers"},
    {"key": "citations", "label": "Citations"},
    {"key": "cpp", "label": "Citations / paper"},
    {"key": "recency", "label": "Recency"},
    {"key": "momentum", "label": "Momentum"},
    {"key": "debut", "label": "Debut yr"},
    {"key": "peak", "label": "Peak yr"},
]
FIELD_OF = {"papers": "n_papers", "citations": "sum_citations"}


def metric_value(row, key):
    """Weight for one term under one metric. Year metrics are sized by (year - 2004)
    so a more recent debut or peak reads bigger. The curated and mined branches share
    these field names, which is why one table serves both."""
    if key in ("debut", "peak"):
        return max((row[key] or 2005) - 2004, 1)
    return row[FIELD_OF.get(key, key)]


def metric_row(row):
    """The per-term metric block the pages read, with the years left as years. A term
    with no papers has no debut or peak, and 0 is how the pages draw that."""
    out = {m["key"]: row[FIELD_OF.get(m["key"], m["key"])] for m in WEIGHT_METRICS}
    out["debut"] = row["debut"] or 0
    out["peak"] = row["peak"] or 0
    return out
