"""
niche_research.py - Niche signal scraping via Apify, persisted to Supabase.

Scrapes platform-specific content (starting with Reddit) via Apify actors,
then writes raw signals to a Supabase table for later scoring and curation
by other crews.

Apify actor IDs are kept here as a Python dict, not a markdown reference doc,
so they are version-controlled with the code that uses them.

Build status:
  - Reddit: implemented
  - Meta Ads / TikTok / Instagram / YouTube / LinkedIn / X: actor IDs registered,
    `customBody` shape pending (port from R46 reference when needed)

Env vars:
  - APIFY_API_TOKEN  (required at call time, not import time)
  - SUPABASE_HOST / SUPABASE_USER / SUPABASE_PASSWORD_B64 / SUPABASE_DB / SUPABASE_PORT
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


# Apify actors discovered via R46 (RoboNuggets Ultimate Extract). One per platform.
# Source: https://www.skool.com/robonuggets/classroom/5203b4f0
APIFY_ACTORS: dict[str, dict[str, str]] = {
    "reddit": {
        "actor_id": "oAuCIx3ItNrs2okjQ",
        "name": "Reddit Scraper Lite",
        "publisher": "trudax",
    },
    "meta_ads": {
        "actor_id": "XtaWFhbtfxyzqrFmd",
        "name": "Meta Ads Library Scraper",
        "publisher": "(unknown)",
    },
    "tiktok": {
        "actor_id": "GdWCkxBtKWOsKjdch",
        "name": "TikTok Scraper",
        "publisher": "(unknown)",
    },
    "instagram": {
        "actor_id": "reGe1ST3OBgYZSsZJ",
        "name": "Instagram Scraper",
        "publisher": "(unknown)",
    },
    "youtube": {
        "actor_id": "h7sDV53CddomktSi5",
        "name": "YouTube Scraper (Long & Shorts)",
        "publisher": "(unknown)",
    },
    "linkedin": {
        "actor_id": "5QnEH5N71IK2mFLrP",
        "name": "LinkedIn Scraper",
        "publisher": "(unknown)",
    },
    "x_twitter": {
        "actor_id": "61RPP7dywgiy0JPD0",
        "name": "X / Twitter Scraper",
        "publisher": "(unknown)",
    },
}


# ---- Supabase persistence ----------------------------------------------------

SUPABASE_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS niche_research_signals (
    id              BIGSERIAL PRIMARY KEY,
    platform        TEXT NOT NULL,
    search_term     TEXT NOT NULL,
    source_url      TEXT,
    title           TEXT,
    body            TEXT,
    author          TEXT,
    score           NUMERIC,
    raw             JSONB,
    scraped_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (platform, source_url)
);
CREATE INDEX IF NOT EXISTS idx_niche_signals_term
    ON niche_research_signals (search_term, platform, scraped_at DESC);
"""


def _get_supabase_conn():
    """Lazy import of orchestrator.db to avoid hard coupling at module import."""
    from orchestrator.db import get_crm_connection
    return get_crm_connection()


def ensure_table() -> None:
    """Idempotent table creation. Safe to call before every scrape."""
    conn = _get_supabase_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(SUPABASE_TABLE_DDL)
        conn.commit()
        logger.info("niche_research_signals table ready")
    finally:
        conn.close()


def write_signals(platform: str, search_term: str, items: list[dict[str, Any]]) -> int:
    """
    Insert rows into niche_research_signals. Skips duplicates on (platform, source_url).
    Returns the count of newly inserted rows.
    """
    if not items:
        return 0
    ensure_table()
    conn = _get_supabase_conn()
    inserted = 0
    try:
        with conn.cursor() as cur:
            for it in items:
                try:
                    cur.execute(
                        """
                        INSERT INTO niche_research_signals
                            (platform, search_term, source_url, title, body, author, score, raw)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (platform, source_url) DO NOTHING
                        """,
                        (
                            platform,
                            search_term,
                            it.get("source_url"),
                            it.get("title"),
                            it.get("body"),
                            it.get("author"),
                            it.get("score"),
                            json.dumps(it.get("raw", {})),
                        ),
                    )
                    inserted += cur.rowcount or 0
                except Exception as e:
                    logger.warning(f"signal insert failed for {it.get('source_url')}: {e}")
        conn.commit()
    finally:
        conn.close()
    logger.info(f"niche_research: {inserted} new {platform} signals for '{search_term}'")
    return inserted


# ---- Reddit scraper (first end-to-end branch) --------------------------------

def _normalize_reddit_item(item: dict[str, Any]) -> dict[str, Any]:
    """Map Apify Reddit Scraper Lite output -> our signal schema."""
    return {
        "source_url": item.get("url") or item.get("permalink"),
        "title": item.get("title") or item.get("dataType"),
        "body": item.get("body") or item.get("selftext") or item.get("text"),
        "author": item.get("username") or item.get("author"),
        "score": item.get("upVotes") or item.get("score") or item.get("numberOfUpvotes"),
        "raw": item,
    }


def scrape_reddit(
    search_term: str,
    max_items: int = 25,
    persist: bool = True,
    timeout_seconds: int = 300,
) -> dict[str, Any]:
    """
    Run the Reddit Scraper Lite Apify actor for a search term and (optionally)
    persist normalized rows to Supabase.

    Returns:
        {
          "platform": "reddit",
          "search_term": ...,
          "actor_id": ...,
          "items_returned": int,
          "items_inserted": int,  # 0 if persist=False
          "items": [...]          # normalized signals (full list)
        }

    Raises:
        RuntimeError if APIFY_API_TOKEN is not set.
    """
    token = os.environ.get("APIFY_API_TOKEN")
    if not token:
        raise RuntimeError("APIFY_API_TOKEN is not set")

    from apify_client import ApifyClient

    actor_id = APIFY_ACTORS["reddit"]["actor_id"]
    run_input = {
        "debugMode": False,
        "ignoreStartUrls": False,
        "includeNSFW": False,
        "maxItems": max_items,
        "proxy": {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"]},
        "scrollTimeout": 40,
        "searchComments": False,
        "searchCommunities": False,
        "searchPosts": True,
        "searchUsers": False,
        "searches": [search_term],
        "skipComments": True,
    }

    client = ApifyClient(token=token)
    logger.info(f"niche_research: starting Reddit scrape for '{search_term}' (max {max_items})")
    started = time.time()
    run = client.actor(actor_id).call(run_input=run_input, timeout_secs=timeout_seconds)
    if not run or not run.get("defaultDatasetId"):
        raise RuntimeError(f"Apify run did not produce a dataset: {run}")

    raw_items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    items = [_normalize_reddit_item(x) for x in raw_items]
    elapsed = round(time.time() - started, 1)
    logger.info(f"niche_research: Reddit returned {len(items)} items in {elapsed}s")

    inserted = 0
    if persist and items:
        inserted = write_signals("reddit", search_term, items)

    return {
        "platform": "reddit",
        "search_term": search_term,
        "actor_id": actor_id,
        "items_returned": len(items),
        "items_inserted": inserted,
        "items": items,
        "elapsed_seconds": elapsed,
    }


# ---- CrewAI tool wrapper -----------------------------------------------------

def _build_tool():
    """Lazy import of crewai.tools.BaseTool so this module imports cleanly even
    when crewai is in a half-installed state during tests."""
    from crewai.tools import BaseTool

    class NicheResearchRedditTool(BaseTool):
        """
        Searches Reddit for posts matching a search term via Apify, persists
        results to Supabase niche_research_signals, and returns a summary.

        Input (JSON string or dict):
          - search_term (str, required)
          - max_items (int, default 25)
          - persist (bool, default True)

        Output (str): JSON summary with counts and a head sample of items.
        """

        name: str = "niche_research_reddit"
        description: str = (
            "Search Reddit for posts about a topic. Returns titles, bodies, "
            "scores, authors. Persists to Supabase for cross-session reuse. "
            "Input JSON: {\"search_term\": \"...\", \"max_items\": 25}."
        )

        def _run(self, input_data: str | dict) -> str:
            try:
                data = json.loads(input_data) if isinstance(input_data, str) else input_data
                term = data.get("search_term")
                if not term:
                    return json.dumps({"error": "search_term is required"})
                max_items = int(data.get("max_items", 25))
                persist = bool(data.get("persist", True))
                result = scrape_reddit(term, max_items=max_items, persist=persist)
                # trim items in tool output (full set is in supabase / scraper return)
                head = result["items"][:5]
                return json.dumps(
                    {
                        "platform": result["platform"],
                        "search_term": result["search_term"],
                        "items_returned": result["items_returned"],
                        "items_inserted": result["items_inserted"],
                        "elapsed_seconds": result["elapsed_seconds"],
                        "head": head,
                    },
                    ensure_ascii=False,
                )[:8000]
            except Exception as e:
                logger.exception("niche_research_reddit tool failed")
                return json.dumps({"error": str(e)})

    return NicheResearchRedditTool()


def get_tools() -> list[Any]:
    """Returns the niche-research bundle for tools.py to import."""
    return [_build_tool()]


# ---- CLI smoke test ----------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Niche research smoke test")
    parser.add_argument("search_term", help="topic to search Reddit for")
    parser.add_argument("--max", type=int, default=10, help="max items (default 10)")
    parser.add_argument("--no-persist", action="store_true", help="skip Supabase write")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if not os.environ.get("APIFY_API_TOKEN"):
        print("APIFY_API_TOKEN is not set. Aborting smoke test.")
        raise SystemExit(2)

    result = scrape_reddit(args.search_term, max_items=args.max, persist=not args.no_persist)
    print(json.dumps({k: v for k, v in result.items() if k != "items"}, indent=2))
    print(f"\nFirst item:\n{json.dumps(result['items'][:1], indent=2, default=str)[:1500]}")
