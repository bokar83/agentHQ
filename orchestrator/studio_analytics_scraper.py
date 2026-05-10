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


def _scrape_views(url: str, platform: str) -> int | None:
    if platform == "x":
        return None
    response = httpx.get(url, follow_redirects=True, timeout=20.0)
    response.raise_for_status()
    if platform == "tiktok":
        match = re.search(r'"playCount":(\d+)', response.text)
    elif platform == "youtube":
        match = re.search(r'"viewCount":"(\d+)"', response.text)
    else:
        return None
    return int(match.group(1)) if match else None


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