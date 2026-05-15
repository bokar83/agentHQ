"""Hacker News scout via Algolia search API. Pulls stories matching a
keyword in the last 7 days, sorted by points. Cursor = highest story id seen."""

from __future__ import annotations

import logging
import time
from typing import Optional

import httpx

logger = logging.getLogger("agentsHQ.absorb_scout.hn")

MAX_PER_TICK = 5
SEARCH_API = "https://hn.algolia.com/api/v1/search"


def fetch(state: dict, keyword: str) -> list[dict]:
    seven_days_ago = int(time.time()) - 7 * 86400
    params = {
        "query": keyword,
        "tags": "story",
        "numericFilters": f"created_at_i>{seven_days_ago}",
        "hitsPerPage": 10,
    }
    try:
        r = httpx.get(SEARCH_API, params=params, timeout=20,
                      headers={"User-Agent": "agentsHQ-absorb-scout/1.0"})
    except Exception as e:
        logger.warning(f"hn: search failed for {keyword}: {e}")
        return []
    if r.status_code != 200:
        logger.warning(f"hn: status={r.status_code} for {keyword}")
        return []

    hits = r.json().get("hits") or []
    last_seen = (state or {}).get("cursor")
    out: list[dict] = []
    cursor_val: Optional[str] = None
    for h in hits:
        sid = str(h.get("objectID") or "")
        url = h.get("url") or f"https://news.ycombinator.com/item?id={sid}"
        if not sid or not url:
            continue
        if cursor_val is None:
            cursor_val = sid
        if last_seen and sid == last_seen:
            break
        out.append({
            "url": url,
            "kind": "url",
            "source": "scout-hn",
            "title": (h.get("title") or "")[:200],
            "ts": h.get("created_at", ""),
            "cursor_value": sid,
        })
        if len(out) >= MAX_PER_TICK:
            break

    if cursor_val is not None:
        state["cursor_value"] = cursor_val
    return out
