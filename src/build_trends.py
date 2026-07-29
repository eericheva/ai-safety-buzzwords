# -*- coding: utf-8 -*-
"""Assemble web/trends.html - the time-series visualizer (Atlas / Overlay / Themes).

    python build_trends.py
"""
import page

if __name__ == "__main__":
    page.build("trends_data.json", "trends.html", drop_papers=False)
