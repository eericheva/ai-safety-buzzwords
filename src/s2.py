# -*- coding: utf-8 -*-
"""Semantic Scholar access: one place for the API key and the two endpoints this
pipeline calls.

The key is optional, because the service treats it that way. Both endpoints answer
unauthenticated requests -- bulk search returns full results with abstracts, and the
batch endpoint returns 768-d SPECTER2 vectors -- just from a shared rate-limit pool.
Demanding `os.environ["S2_API_KEY"]` would therefore refuse runs that the API itself
allows, so the key arrives as a parameter from argparse whose default is
`os.environ.get("S2_API_KEY")`, the same shape discover.py uses for `--mailto`. With
no key the header is simply not sent.

The retry here replaced three separate `except Exception` loops that also swallowed
NameError and TypeError and then returned None, which the callers turned into an
empty result. Only 429 is retried, because 429 is the endpoint asking the caller to
wait rather than a failure; everything else propagates at the call that caused it.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BULK = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"
BATCH = "https://api.semanticscholar.org/graph/v1/paper/batch?fields=embedding.specter_v2"
FIELDS = "title,abstract,year,publicationDate,citationCount,externalIds"

SEARCH_YEAR = "2005-"     # retrieval window, the same for the curated and mined branches
SEARCH_SORT = "citationCount:desc"

RATE_LIMIT_WAITS = 6      # pauses allowed per call before a 429 is left to propagate
RATE_LIMIT_PAUSE = 5      # seconds, when the response carries no Retry-After


def _headers(api_key, extra):
    h = dict(extra)
    if api_key:
        h["x-api-key"] = api_key
    return h


def _load(req, timeout):
    for attempt in range(RATE_LIMIT_WAITS):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == RATE_LIMIT_WAITS - 1:
                raise
            wait = int(e.headers.get("Retry-After") or RATE_LIMIT_PAUSE)
            print("    S2 rate limit, waiting %ds" % wait, file=sys.stderr)
            time.sleep(wait)


def search_bulk(query, sort, api_key):
    params = {"query": query, "year": SEARCH_YEAR, "fields": FIELDS,
              "fieldsOfStudy": "Computer Science", "sort": sort}
    req = urllib.request.Request(BULK + "?" + urllib.parse.urlencode(params),
                                 headers=_headers(api_key, {}))
    return _load(req, 60)


def embeddings(arxiv_ids, api_key):
    body = json.dumps({"ids": ["ARXIV:" + i for i in arxiv_ids]}).encode()
    req = urllib.request.Request(BATCH, data=body,
                                 headers=_headers(api_key, {"Content-Type": "application/json"}))
    return _load(req, 90)


def add_key_arg(parser):
    """Every entry point that talks to S2 takes the key the same way."""
    parser.add_argument("--api-key", default=os.environ.get("S2_API_KEY"),
                        help="Semantic Scholar key; default $S2_API_KEY. Optional - "
                             "the endpoints work unauthenticated at a lower rate limit")
