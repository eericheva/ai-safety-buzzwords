# -*- coding: utf-8 -*-
"""Assemble a self-contained page: read one data file per source, inject them all into
the page's template as a single JS constant, write web/<page>.html.

The three artifacts differed only in which data file they read and which template they
filled, so the same twenty-line main() existed three times - and each carried its
template as a 250-to-510-line raw string inside the Python, where it got no syntax
highlighting, no linting and no readable diff. Templates now live in templates/.
"""
import json
import os

import common

SOURCE_LABELS = {"curated": "Curated", "raw2": "Mined phrases",
                 "openalex": "OpenAlex keywords"}
EXTRA_SOURCES = ("raw2", "openalex")


def build(data_file, page, drop_papers):
    """`page` names both the template and the output file, which is why they match."""
    curated = common.read_json(common.DATA, data_file)
    curated["label"] = SOURCE_LABELS["curated"]
    sources = {"curated": curated}
    for s in EXTRA_SOURCES:      # bottom-up branches, shown behind the Source toggle
        path = os.path.join(common.DATA, "src_" + s, data_file)
        if os.path.exists(path):
            sd = common.read_json(path)
            sd["label"] = SOURCE_LABELS[s]
            sources[s] = sd
    if drop_papers:              # the paper table is served from data/papers.csv instead
        for sd in sources.values():
            sd.pop("papers", None)   # mined sources never carried one

    template = os.path.join(common.TEMPLATES, page)
    with open(template, encoding="utf-8") as f:
        html = f.read()
    payload = json.dumps(sources, ensure_ascii=False, separators=(",", ":"))
    out = os.path.join(common.WEB, page)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html.replace("/*__DATA__*/", payload))
    # printing the source list keeps a missing optional branch visible rather than silent
    print("wrote %s (%.0f KB) sources=%s"
          % (out, os.path.getsize(out) / 1024, list(sources)))
