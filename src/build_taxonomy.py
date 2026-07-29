# -*- coding: utf-8 -*-
"""Assemble web/taxonomy.html - ONE unified grouping map of the 125 buzzwords.
Three independent controls: Layout (position), Colour, Size (radius).

    python build_taxonomy.py
"""
import page

if __name__ == "__main__":
    page.build("taxonomy_map.json", "taxonomy.html", drop_papers=False)
