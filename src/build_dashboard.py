# -*- coding: utf-8 -*-
"""Assemble the self-contained dashboard artifact web/index.html from viz_data.json.

The word clouds are rendered in-page as interactive SVGs (DATA.cloud_svgs), not as
embedded images. The paper table is stripped from the payload - only per-term stats
travel into the page - and the full corpus stays in data/papers.csv.

    python src/build_dashboard.py
"""
import page

if __name__ == "__main__":
    page.build("viz_data.json", "index.html", drop_papers=True)
