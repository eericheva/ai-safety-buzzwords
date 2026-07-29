# -*- coding: utf-8 -*-
"""Unified grouping 'lenses' shared by every artifact.

Builds, for all 125 buzzwords:
  TERM_LENS[term] = {"glossary":g, "mit":g, "semantic":g, "cooccur":g}
  LENS_META[lens] = {"label", "groups":[ordered], "colors":{g:hex}, "colors_dark":{g:hex}}

Sources: common (glossary themes), data/grouping_mit.json, grouping_embed.json,
grouping_cooccur.json - so this reflects the last groupings run.
"""
import common
from buzzwords import BUZZWORDS

# concise human names for the 8 (deterministic, seed=42) semantic clusters;
# falls back to the two most-central terms if a cluster's content shifts.
SEM_NAMES = {
    0: "interpretability methods", 1: "oversight & honesty",
    2: "companion & affective", 3: "calibration & truthfulness",
    4: "refusal & jailbreak", 5: "agentic goals & risk",
    6: "bias & fairness", 7: "privacy & security",
}
ISO = "Isolated (niche)"


def build():
    terms = [t for t, _, _ in BUZZWORDS]
    term_lens = {t: {} for t in terms}

    # ---- glossary (8 macro-themes) ----
    for t, c, _ in BUZZWORDS:
        term_lens[t]["glossary"] = common.group_of(c)
    lens_meta = {"glossary": {"label": "Glossary theme", "groups": common.GROUP_ORDER,
                              "colors": common.GROUP_COLOR,
                              "colors_dark": common.GROUP_COLOR_DARK}}

    # ---- MIT risk domains (7) ----
    mit = common.read_json(common.DATA, "grouping_mit.json")
    for r in mit["term_rows"]:
        term_lens[r["term"]]["mit"] = r["domain"]
    light, dark = common.lens_colors(mit["domains"])
    lens_meta["mit"] = {"label": "MIT risk domain", "groups": mit["domains"],
                        "colors": light, "colors_dark": dark}

    # ---- semantic k-means clusters (8) ----
    emb = common.read_json(common.DATA, "grouping_embed.json")
    cl_label = {}
    for c in emb["clusters"]:
        name = SEM_NAMES.get(c["id"]) or ", ".join(c["top_terms"][:2])
        cl_label[c["id"]] = "S%d · %s" % (c["id"], name)
    for n in emb["nodes"]:
        term_lens[n["term"]]["semantic"] = cl_label[n["cluster"]]
    sem_groups = [cl_label[c["id"]] for c in sorted(emb["clusters"], key=lambda c: c["id"])]
    light, dark = common.lens_colors(sem_groups)
    lens_meta["semantic"] = {"label": "Semantic cluster", "groups": sem_groups,
                             "colors": light, "colors_dark": dark}

    # ---- co-occurrence communities (6 big + Isolated) ----
    co = common.read_json(common.DATA, "grouping_cooccur.json")
    big = [c for c in co["clusters"] if c["size"] >= 3]
    co_label, co_groups = {}, []
    for c in big:
        lab = "%s +" % c["dominant_theme"].split(",")[0]
        for m in c["members"]:
            co_label[m] = lab
        if lab not in co_groups:
            co_groups.append(lab)
    co_groups.append(ISO)
    for t in terms:
        term_lens[t]["cooccur"] = co_label.get(t, ISO)
    light, dark = common.lens_colors(co_groups)
    lens_meta["cooccur"] = {"label": "Co-occurrence community", "groups": co_groups,
                            "colors": light, "colors_dark": dark}

    return term_lens, lens_meta


if __name__ == "__main__":
    tl, lm = build()
    for lens, meta in lm.items():
        print(f"{lens:9s} ({len(meta['groups'])} groups): {meta['groups']}")
    print("\nsample term memberships:")
    for t in ["jailbreak", "sparse autoencoder", "membership inference", "gradual disempowerment"]:
        print(" ", t, "->", tl[t])
