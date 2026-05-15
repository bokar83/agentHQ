"""
studio_analytics_scraper.py - Studio M5-lite.

Scrape public view counts from posted Studio Pipeline URLs and write them
back to Notion. Intended for low-volume daily heartbeat use.
"""
from __future__ import annotations

import logging
import os
import re

import httpx

logger = logging.getLogger("agentsHQ.studio_analytics_scraper")

PIPELINE_DB_ID = os.environ.get(
    "NOTION_STUDIO_PIPELINE_DB_ID",
    "34ebcf1a-3029-8140-a565-f7c26fe9de86",
)


def _notion_client():
    from skills.forge_cli.notion_client import NotionClient

    api_key = os.environ.get("NOTION_API_KEY") or os.environ.get("NOTION_SECRET") or os.environ.get("NOTION_TOKEN")
    if not api_key:
        raise ValueError("NOTION_API_KEY not set")
    return NotionClient(api_key)


def _prop_text(record: dict, name: str) -> str:
    prop = record.get("properties", {}).get(name, {})
    ptype = prop.get("type", "")
    if ptype == "rich_text":
        return "".join(p.get("plain_text", "") for p in prop.get("rich_text", []))
    if ptype == "title":
        return "".join(p.get("plain_text", "") for p in prop.get("title", []))
    if ptype in ("select", "status"):
        return (prop.get(ptype) or {}).get("name", "")
    if ptype == "url":
        return prop.get("url") or ""
    return ""


def _detect_platform(url: str) -> str:
    lowered = (url or "").lower()
    if "tiktok.com" in lowered:
        return "tiktok"
    if "youtube.com" in lowered or "youtu.be" in lowered:
        return "youtube"
    if "twitter.com" in lowered or "x.com" in lowered:
        return "x"
    return "unknown"


# Accept-Language forces YouTube to serve view-count text in English
# ("14 views"), avoiding locale variants like "14 tontonan" (Indonesian),
# "14 vistas" (Spanish), "14 vues" (French) when the VPS resolves to a
# non-US edge. Belt: parser is locale-tolerant either way.
_HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def _parse_leading_int(text: str) -> int | None:
    """Extract the leading integer from a view-count phrase, ignoring
    trailing locale-specific words ("views", "tontonan", "vistas", etc.)
    and thousands separators ("1,234" / "1.234" / "1 234")."""
    if not text:
        return None
    # Grab the leading numeric run including , . and whitespace separators.
    m = re.match(r"\s*([\d][\d,.  \s]*)", text)
    if not m:
        return None
    digits = re.sub(r"[^\d]", "", m.group(1))
    if not digits:
        return None
    return int(digits)


def _parse_youtube_views(html: str) -> int | None:
    """Extract YouTube view count from raw watch-page HTML.

    Strategy (in order):
      1. videoViewCountRenderer.viewCount.simpleText -- always populated
         even for low-view videos (where originalViewCount is "0").
      2. shortViewCount.simpleText -- compact form ("1.2K views").
      3. originalViewCount -- numeric string, but YouTube returns "0"
         for videos under some threshold, so it cannot be trusted alone.
    """
    # 1. Full simpleText: "14 views" / "14 tontonan" / "1,234 views"
    m = re.search(
        r'"videoViewCountRenderer"\s*:\s*\{[^{}]*?"viewCount"\s*:\s*\{\s*"simpleText"\s*:\s*"([^"]+)"',
        html,
    )
    if m:
        parsed = _parse_leading_int(m.group(1))
        if parsed is not None:
            return parsed

    # 2. Short form -- only useful if it's purely numeric
    m = re.search(
        r'"shortViewCount"\s*:\s*\{\s*"simpleText"\s*:\s*"([^"]+)"',
        html,
    )
    if m:
        parsed = _parse_leading_int(m.group(1))
        if parsed is not None:
            return parsed

    # 3. originalViewCount -- last resort, only trust if non-zero
    m = re.search(r'"originalViewCount"\s*:\s*"(\d+)"', html)
    if m:
        val = int(m.group(1))
        if val > 0:
            return val
    return None


def _scrape_views(url: str, platform: str) -> int | None:
    if platform == "x":
        return None
    response = httpx.get(
        url, follow_redirects=True, timeout=20.0, headers=_HTTP_HEADERS
    )
    response.raise_for_status()
    if platform == "tiktok":
        match = re.search(r'"playCount":(\d+)', response.text)
        return int(match.group(1)) if match else None
    if platform == "youtube":
        return _parse_youtube_views(response.text)
    return None


def studio_analytics_tick() -> dict:
    summary = {"processed": 0, "updated": 0, "errors": 0}
    notion = _notion_client()
    rows = notion.query_database(
        PIPELINE_DB_ID,
        filter_obj={
            "and": [
                {"property": "Status", "select": {"equals": "published"}},
                {"property": "Posted URL", "url": {"is_not_empty": True}},
            ]
        },
    )

    for record in rows or []:
        summary["processed"] += 1
        page_id = record.get("id", "")
        url = _prop_text(record, "Posted URL")
        platform = _detect_platform(url)
        if platform == "x":
            logger.info("studio analytics: skipping X URL for page %s", page_id)
            continue
        try:
            views = _scrape_views(url, platform)
            if views is None:
                logger.info("studio analytics: no view count found for page %s url=%s", page_id, url)
                continue
            notion.update_page(page_id, {"Views": {"number": views}})
            summary["updated"] += 1
            logger.info("studio analytics: updated page %s platform=%s views=%s", page_id, platform, views)
        except Exception as e:
            summary["errors"] += 1
            logger.warning("studio analytics: failed page %s url=%s: %s", page_id, url, e)

    logger.info("studio analytics: summary %s", summary)
    return summary