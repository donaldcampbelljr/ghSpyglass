#!/usr/bin/env python3
"""ghSpyglass - small CLI to count GitHub repositories for topics/keywords in a date range

Usage: python gh_spyglass.py --start 2020-01-01 --end 2020-12-31 --topics cli api --keywords tool
"""
import argparse
import os
import sys
import time
from datetime import datetime, timedelta
from typing import List, Optional

import requests

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"


def parse_date(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d")


def build_query(topics: List[str], keywords: List[str]) -> str:
    parts = []
    if topics:
        # topic:token syntax
        parts += [f"topic:{t}" for t in topics]
    if keywords:
        # search keywords in name,description,readme
        parts += [f"{k} in:name,description,readme" for k in keywords]
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    return "(" + " OR ".join(parts) + ")"


def github_search_count(query: str, token: Optional[str] = None) -> dict:
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    params = {"q": query, "per_page": 1}
    r = requests.get(GITHUB_SEARCH_URL, headers=headers, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def count_range(query_base: str, start: datetime, end: datetime, token: Optional[str], exact: bool) -> int:
    """Count repos matching query_base within created:start..end.

    If exact is True and the search reports more than 1000 results we will split the date range
    to try to avoid the Search API 1000-result windowing limitation.
    """
    date_range = f"created:{start.date().isoformat()}..{end.date().isoformat()}"
    full_query = f"{query_base} {date_range}" if query_base else date_range
    resp = github_search_count(full_query, token)
    total = int(resp.get("total_count", 0))
    # If exact calculation requested and total >= 1000, split
    if exact and total >= 1000 and start < end:
        # split in half
        mid = start + (end - start) / 2
        left = count_range(query_base, start, mid, token, exact)
        # right starts the next second after mid to avoid overlap
        right_start = mid + timedelta(seconds=1)
        if right_start > end:
            return left
        right = count_range(query_base, right_start, end, token, exact)
        return left + right
    return total


def run(argv: List[str]) -> int:
    p = argparse.ArgumentParser(description="Count GitHub repositories for topics/keywords between dates")
    p.add_argument("--start", required=True, help="Start date YYYY-MM-DD")
    p.add_argument("--end", required=True, help="End date YYYY-MM-DD")
    p.add_argument("--topics", nargs="*", default=[], help="List of GitHub topics to search")
    p.add_argument("--keywords", nargs="*", default=[], help="List of keywords to search (name/desc/readme)")
    p.add_argument("--per-term", action="store_true", help="Show counts per-topic/keyword instead of aggregate")
    p.add_argument("--token", help="GitHub token (or set GITHUB_TOKEN env var)")
    p.add_argument("--exact", action="store_true", help="Try to compute exact counts by splitting large ranges (slower)")
    p.add_argument("--sleep", type=float, default=0.0, help="Sleep seconds between API calls (rate control)")
    args = p.parse_args(argv)

    try:
        start = parse_date(args.start)
        end = parse_date(args.end)
    except Exception as e:
        print(f"Invalid date: {e}")
        return 2
    if start > end:
        print("Start must be <= end")
        return 2

    token = args.token or os.getenv("GITHUB_TOKEN")

    query_base = build_query(args.topics, args.keywords)
    if not query_base:
        print("Provide at least one topic or keyword")
        return 2

    if args.per_term:
        results = {}
        terms = []
        terms += [f"topic:{t}" for t in args.topics]
        terms += [f"{k} in:name,description,readme" for k in args.keywords]
        for t in terms:
            cnt = count_range(t, start, end, token, args.exact)
            results[t] = cnt
            print(f"{t}: {cnt}")
            if args.sleep:
                time.sleep(args.sleep)
        total = sum(results.values())
        print(f"TOTAL (sum of terms): {total}")
    else:
        total = count_range(query_base, start, end, token, args.exact)
        print(f"TOTAL matching any provided topics/keywords: {total}")

    return 0


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))
