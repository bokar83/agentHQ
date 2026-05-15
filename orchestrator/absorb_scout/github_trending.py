"""GitHub trending scout. Polls the search API for repos under a given topic,
sorted by star count, filtered to repos pushed in the last 7 days. Cursor is
the highest stargazers_count seen so we only enqueue repos that have crossed
a higher star bar since the last tick."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import httpx

logger = logging.getLogger("agentsHQ.absorb_scout.gh")

MAX_PER_TICK = 5
SEARCH_API = "https://api.github.com/search/repositories"


def _headers() -> dict:
    h = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "agentsHQ-absorb-scout/1.0",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def fetch(state: dict, topic: str) -> list[dict]:
    """Search recent repos with the given topic, newest-pushed-first."""
    pushed_since = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
    q = f"topic:{topic} pushed:>{pushed_since}"
    params = {"q": q, "sort": "stars", "order": "desc", "per_page": 10}
    try:
        r = httpx.get(SEARCH_API, params=params, headers=_headers(), timeout=20)
    except Exception as e:
        logger.warning(f"gh: search failed for topic={topic}: {e}")
        return []
    if r.status_code != 200:
        logger.warning(f"gh: status={r.status_code} for topic={topic} body={r.text[:200]}")
        return []

    items = r.json().get("items") or []
    last_seen_full = (state or {}).get("cursor") or ""
    out: list[dict] = []
    cursor_full: Optional[str] = None
    for it in items:
        full_name = it.get("full_name")
        if not full_name:
            continue
        if cursor_full is None:
            cursor_full = full_name
        if last_seen_full and full_name == last_seen_full:
            break
        out.append({
            "url": it.get("html_url"),
            "kind": "github-repo",
            "source": "scout-gh",
            "title": (it.get("description") or full_name)[:200],
            "ts": it.get("pushed_at", ""),
            "cursor_value": full_name,
        })
        if len(out) >= MAX_PER_TICK:
            break

    if cursor_full is not None:
        state["cursor_value"] = cursor_full
    return out
