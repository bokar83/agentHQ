"""Reddit RSS scout. One adapter per subreddit feed URL."""

from __future__ import annotations

import logging
import re
from typing import Optional

import httpx

logger = logging.getLogger("agentsHQ.absorb_scout.reddit")

MAX_PER_TICK = 5
USER_AGENT = "agentsHQ-absorb-scout/1.0 (+https://github.com/bokar83/agentHQ)"


def fetch(state: dict, feed_url: str) -> list[dict]:
    """Pull the RSS feed, return up to MAX_PER_TICK candidates newer than cursor.

    Cursor is the most recent <id> seen. Reddit RSS uses Atom; the <entry>'s
    <id> tag is a Reddit thing id like 't3_abc123'.
    """
    last_seen = (state or {}).get("cursor")
    try:
        r = httpx.get(feed_url, timeout=20, headers={"User-Agent": USER_AGENT})
    except Exception as e:
        logger.warning(f"reddit_rss: GET failed for {feed_url}: {e}")
        return []
    if r.status_code != 200:
        logger.warning(f"reddit_rss: status={r.status_code} for {feed_url}")
        return []

    body = r.text
    entries = re.findall(r"<entry>(.*?)</entry>", body, flags=re.S)
    out: list[dict] = []
    first_id: Optional[str] = None
    for raw in entries:
        m_id = re.search(r"<id>([^<]+)</id>", raw)
        m_link = re.search(r'<link[^>]+href="([^"]+)"', raw)
        m_title = re.search(r"<title>([^<]+)</title>", raw)
        m_updated = re.search(r"<updated>([^<]+)</updated>", raw)
        if not (m_id and m_link):
            continue
        eid = m_id.group(1).strip()
        url = m_link.group(1).strip()
        if first_id is None:
            first_id = eid
        if last_seen and eid == last_seen:
            break
        out.append({
            "url": url,
            "kind": "url",
            "source": "scout-reddit",
            "title": (m_title.group(1).strip() if m_title else "")[:200],
            "ts": (m_updated.group(1).strip() if m_updated else ""),
            "cursor_value": eid,
        })
        if len(out) >= MAX_PER_TICK:
            break

    if first_id is not None:
        state["cursor_value"] = first_id
    return out
