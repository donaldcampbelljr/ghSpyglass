import json
from datetime import datetime

import responses

from gh_spyglass import build_query, github_search_count, count_range


def test_build_query():
    q = build_query(["cli"], ["tool"])
    assert "topic:cli" in q
    assert "tool in:name,description,readme" in q


@responses.activate
def test_github_search_count_and_count_range():
    # mock search API
    url = "https://api.github.com/search/repositories"
    # for aggregate
    body = {"total_count": 42, "items": []}
    responses.add(responses.GET, url, json=body, status=200)

    resp = github_search_count("created:2020-01-01..2020-12-31")
    assert resp["total_count"] == 42

    # count_range should return the same
    start = datetime(2020, 1, 1)
    end = datetime(2020, 12, 31)
    cnt = count_range("topic:cli", start, end, token=None, exact=False)
    assert cnt == 42
