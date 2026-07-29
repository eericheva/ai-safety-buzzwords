# -*- coding: utf-8 -*-
"""Word-cloud SVG, one implementation.

Both branches rendered clouds with the same three regex fixups afterwards, and both
hardcoded `font_path="/System/Library/Fonts/Helvetica.ttc"` -- a macOS path that makes
this step fail everywhere else. In build_source_data.py the failure was worse than a
crash: an `except OSError` swallowed it and retried at six font sizes, reporting a
missing font as a sizing problem. The font is now an explicit parameter defaulting to
the one wordcloud ships, so the step runs anywhere; the SVGs committed to data/ were
rendered with Helvetica and will differ slightly in metrics when regenerated.

Isolated in its own module because it is the pipeline's only wordcloud dependency and
the page builders must import common.py on a bare interpreter.
"""
import html
import os
import re

import wordcloud
from wordcloud import WordCloud

DEFAULT_FONT = os.path.join(os.path.dirname(wordcloud.__file__), "DroidSansMono.ttf")


def svg(freqs, font):
    """Interactive cloud: a viewBox instead of fixed pixels so it scales, no background
    rect so the page's own colour shows through, and `data-term` on every <text> so the
    JS can recolour and cross-filter by term."""
    wc = WordCloud(background_color="#faf9f6", width=2100, height=1150,
                   prefer_horizontal=0.94, relative_scaling=0.40, min_font_size=7,
                   max_font_size=115, font_step=1, margin=1, collocations=False,
                   random_state=42, max_words=400, font_path=font)
    wc.generate_from_frequencies(freqs)
    out = wc.to_svg(embed_font=False)
    out = re.sub(r'<svg xmlns="([^"]*)" width="(\d+)" height="(\d+)"',
                 r'<svg xmlns="\1" viewBox="0 0 \2 \3" width="100%" '
                 r'preserveAspectRatio="xMidYMid meet"', out, count=1)
    out = re.sub(r'<rect\b[^>]*/?>', '', out, count=1)
    out = out.replace("font-family:'Helvetica';",
                      "font-family:'Helvetica',Arial,system-ui,sans-serif;")
    out = re.sub(r'(<text\b[^>]*)>([^<]*)</text>',
                 lambda m: '%s data-term="%s">%s</text>'
                           % (m.group(1), html.escape(m.group(2), quote=True), m.group(2)),
                 out)
    return out, len(wc.layout_)
