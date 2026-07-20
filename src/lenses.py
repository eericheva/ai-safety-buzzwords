# -*- coding: utf-8 -*-
"""Unified grouping 'lenses' shared by every artifact.

Builds, for all 125 buzzwords:
  TERM_LENS[term] = {"glossary":g, "mit":g, "semantic":g, "cooccur":g}
  LENS_META[lens] = {"label", "groups":[ordered], "colors":{g:hex}, "colors_dark":{g:hex}}

Sources: build_viz (glossary), data/grouping_mit.json, grouping_embed.json,
grouping_cooccur.json — so this reflects the last groupings run.
"""
import json, os
from build_viz import group_of, GROUP_ORDER, GROUP_COLOR
from buzzwords import BUZZWORDS

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CAT_LIGHT = ['#2a78d6', '#008300', '#e87ba4', '#eda100', '#1baf7a', '#eb6834', '#4a3aa7', '#e34948']
CAT_DARK  = ['#3987e5', '#38ad38', '#e87ba4', '#eda100', '#1baf7a', '#eb6834', '#9085e9', '#e66767']
GROUP_COLOR_DARK = {
    "Truth & hallucination": "#5598e7", "Harm, bias & fairness": "#38ad38",
    "Interaction & affective": "#e87ba4", "Alignment, goals & control": "#eda100",
    "Attacks, robustness & training": "#1baf7a", "Privacy, data & memory": "#eb6834",
    "Agents & multi-agent": "#9085e9", "Interpretability & self-knowledge": "#e66767",
}


def _load(name):
    return json.load(open(os.path.join(HERE, "data", name)))


def build():
    terms = [t for t, _, _ in BUZZWORDS]
    term_lens = {t: {} for t in terms}

    # ---- glossary (8 macro-themes) ----
    for t, c, _ in BUZZWORDS:
        term_lens[t]["glossary"] = group_of(c)
    lens_meta = {"glossary": {"label": "Glossary theme", "groups": GROUP_ORDER,
                              "colors": GROUP_COLOR, "colors_dark": GROUP_COLOR_DARK}}

    # ---- MIT risk domains (7) ----
    mit = _load("grouping_mit.json")
    for r in mit["term_rows"]:
        term_lens[r["term"]]["mit"] = r["domain"]
    mit_groups = mit["domains"]
    lens_meta["mit"] = {"label": "MIT risk domain", "groups": mit_groups,
        "colors": {g: CAT_LIGHT[i % 8] for i, g in enumerate(mit_groups)},
        "colors_dark": {g: CAT_DARK[i % 8] for i, g in enumerate(mit_groups)}}

    # ---- semantic k-means clusters (8) ----
    # concise human names for the 8 (deterministic, seed=42) semantic clusters;
    # falls back to the two most-central terms if a cluster's content shifts.
    SEM_NAMES = {
        0: "interpretability methods", 1: "oversight & honesty",
        2: "companion & affective", 3: "calibration & truthfulness",
        4: "refusal & jailbreak", 5: "agentic goals & risk",
        6: "bias & fairness", 7: "privacy & security",
    }
    emb = _load("grouping_embed.json")
    cl_label = {}
    for c in emb["clusters"]:
        name = SEM_NAMES.get(c["id"]) or ", ".join(c["top_terms"][:2])
        cl_label[c["id"]] = "S%d · %s" % (c["id"], name)
    for n in emb["nodes"]:
        term_lens[n["term"]]["semantic"] = cl_label[n["cluster"]]
    sem_groups = [cl_label[c["id"]] for c in sorted(emb["clusters"], key=lambda c: c["id"])]
    lens_meta["semantic"] = {"label": "Semantic cluster", "groups": sem_groups,
        "colors": {g: CAT_LIGHT[i % 8] for i, g in enumerate(sem_groups)},
        "colors_dark": {g: CAT_DARK[i % 8] for i, g in enumerate(sem_groups)}}

    # ---- co-occurrence communities (6 big + Isolated) ----
    co = _load("grouping_cooccur.json")
    big = [c for c in co["clusters"] if c["size"] >= 3]
    co_label = {}
    for i, c in enumerate(big):
        lab = "%s +" % c["dominant_theme"].split(",")[0]
        for m in c["members"]:
            co_label[m] = lab
    ISO = "Isolated (niche)"
    co_groups = []
    for c in big:
        lab = "%s +" % c["dominant_theme"].split(",")[0]
        if lab not in co_groups:
            co_groups.append(lab)
    co_groups.append(ISO)
    for t in terms:
        term_lens[t]["cooccur"] = co_label.get(t, ISO)
    lens_meta["cooccur"] = {"label": "Co-occurrence community", "groups": co_groups,
        "colors": {g: CAT_LIGHT[i % 8] for i, g in enumerate(co_groups)},
        "colors_dark": {g: CAT_DARK[i % 8] for i, g in enumerate(co_groups)}}

    return term_lens, lens_meta


# artifact cross-navigation (published URLs)
NAV = [
    {"key": "cloud",    "label": "Word cloud",  "url": "https://claude.ai/code/artifact/925356f2-6bd0-48bd-931e-4da6525c7b00"},
    {"key": "trends",   "label": "Trends",      "url": "https://claude.ai/code/artifact/77473750-146a-4348-a4c1-5d476b986789"},
    {"key": "taxonomy", "label": "Groupings",   "url": "https://claude.ai/code/artifact/8f0e56b3-eed4-414d-8414-585d553a26fe"},
]


if __name__ == "__main__":
    tl, lm = build()
    for lens, meta in lm.items():
        print(f"{lens:9s} ({len(meta['groups'])} groups): {meta['groups']}")
    print("\nsample term memberships:")
    for t in ["jailbreak", "sparse autoencoder", "membership inference", "gradual disempowerment"]:
        print(" ", t, "->", tl[t])
