"""
studio_trend_scout.py - Studio M1 Engine.

Trend Scout v0. Heartbeat callback that scans configured niches for viral
content patterns, scores candidates, and writes the top N per niche to the
Studio Pipeline Notion DB. Sends a daily Telegram brief with the picks.

Adapted from the clone-scout pattern (which scouts websites for cloning).
This version scouts video content for repurposing into Studio's faceless
channels.

Sources (v0): YouTube Data API v3 over a SEED LIST of reference channels
per niche. Each seed channel's recent uploads are pulled, scored by view
velocity (views per hour since publish), top picks queued in Notion.

Why seed-list (not generic discovery): YouTube's search API gives noisy
results and burns quota fast. A curated seed list per niche surfaces the
exact creators we want to clone-with-twist. Add seeds via
data/studio_trend_seeds.json.

Graceful degrade: if YOUTUBE_API_KEY is missing, scout writes ZERO
candidates and logs a warning. The heartbeat tick still fires and Telegram
still alerts, so silence is visible.

Pipeline DB schema lives in Notion (created 2026-04-25).
DB ID: NOTION_STUDIO_PIPELINE_DB_ID env var.
"""
from __future__ import annotations

import json
import logging
import os
import pathlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

import pytz

logger = logging.getLogger("agentsHQ.studio_trend_scout")

TIMEZONE = os.environ.get("HEARTBEAT_TIMEZONE", "America/Denver")
PIPELINE_DB_ID = os.environ.get("NOTION_STUDIO_PIPELINE_DB_ID", "")
TOP_N_PER_NICHE = int(os.environ.get("STUDIO_TREND_SCOUT_TOP_N", "5"))
LOOKBACK_DAYS = int(os.environ.get("STUDIO_TREND_SCOUT_LOOKBACK_DAYS", "7"))

# Default seeds. Override by writing data/studio_trend_seeds.json.
# Each entry: niche tag -> list of YouTube channel IDs (UCxxxx).
# Channels chosen as reference creators; not aspirational, just the pool we
# clone-with-twist from. Boubacar can swap any of these out.
_DEFAULT_SEEDS = {
    "african-folktales": {
        "channel": "Under the Baobab",
        "youtube_seed_channels": [
            # Tales of Africa, African Folk Tales by Gift, etc - Boubacar swaps these in
        ],
        "youtube_seed_search_terms": [
            "african folktales kids",
            "african bedtime story",
            "african children animation",
        ],
    },
    "ai-displacement": {
        "channel": "AI Catalyst",
        "youtube_seed_channels": [],
        "youtube_seed_search_terms": [
            "AI taking my job",
            "AI replacing workers",
            "is my job safe from AI",
            "AI proof career",
        ],
    },
    "first-gen-money": {
        "channel": "First Generation Money",
        "youtube_seed_channels": [],
        "youtube_seed_search_terms": [
            "first generation wealth",
            "immigrant family money",
            "first gen money advice",
            "no inheritance build wealth",
        ],
    },
}


def _load_seeds() -> dict:
    """Load seed config. Search order:
      1. env STUDIO_TREND_SEEDS_FILE
      2. data/studio_trend_seeds.json (gitignored, machine-local)
      3. /app/data/studio_trend_seeds.json (container path)
      4. orchestrator/studio_trend_seeds.default.json (committed default)
      5. _DEFAULT_SEEDS in this module
    """
    here = pathlib.Path(__file__).parent
    candidates = [
        os.environ.get("STUDIO_TREND_SEEDS_FILE"),
        "data/studio_trend_seeds.json",
        "/app/data/studio_trend_seeds.json",
        str(here / "studio_trend_seeds.default.json"),
    ]
    for path in candidates:
        if not path:
            continue
        p = pathlib.Path(path)
        if not p.exists():
            continue
        try:
            return json.loads(p.read_text())
        except Exception as e:
            logger.warning(f"studio_trend_scout: seeds file {p} unreadable: {e}; trying next")
            continue
    return _DEFAULT_SEEDS


# ═════════════════════════════════════════════════════════════════════════════
# YouTube Data API v3 client (graceful degrade if key missing)
# ═════════════════════════════════════════════════════════════════════════════

@dataclass
class TrendCandidate:
    """One trend-scout pick. Becomes a row in the Notion Pipeline DB."""
    niche: str
    channel: str
    source_url: str
    source_channel: str
    title: str
    views: int
    published_at: str
    velocity_per_hour: float
    hook: str = ""
    twist: str = ""


def _yt_api_key() -> Optional[str]:
    return os.environ.get("YOUTUBE_API_KEY") or os.environ.get("GOOGLE_API_KEY") or None


def _yt_search(query: str, max_results: int = 10) -> list:
    """YouTube Data API v3 search. Returns list of video items.
    Returns [] if no API key configured.
    """
    key = _yt_api_key()
    if not key:
        return []
    try:
        import httpx
        published_after = (datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)).isoformat()
        with httpx.Client(timeout=15) as client:
            resp = client.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    "key": key,
                    "part": "snippet",
                    "type": "video",
                    "q": query,
                    "publishedAfter": published_after,
                    "order": "viewCount",
                    "maxResults": max_results,
                },
            )
        if resp.status_code != 200:
            logger.warning(
                f"studio_trend_scout: YouTube search '{query}' returned {resp.status_code}: "
                f"{resp.text[:300]}"
            )
            return []
        return resp.json().get("items", [])
    except Exception as e:
        logger.warning(f"studio_trend_scout: YouTube search '{query}' error: {e}")
        return []


def _yt_video_stats(video_ids: list) -> dict:
    """Batch-fetch view counts for a list of video IDs.
    Returns {video_id: {"views": int, "duration": str}}.
    Returns {} if no API key.
    """
    key = _yt_api_key()
    if not key or not video_ids:
        return {}
    try:
        import httpx
        with httpx.Client(timeout=15) as client:
            resp = client.get(
                "https://www.googleapis.com/youtube/v3/videos",
                params={
                    "key": key,
                    "part": "statistics,contentDetails",
                    "id": ",".join(video_ids[:50]),  # API caps at 50 per call
                },
            )
        if resp.status_code != 200:
            return {}
        out = {}
        for item in resp.json().get("items", []):
            vid = item["id"]
            stats = item.get("statistics", {})
            details = item.get("contentDetails", {})
            out[vid] = {
                "views": int(stats.get("viewCount", 0)),
                "duration": details.get("duration", ""),
            }
        return out
    except Exception as e:
        logger.warning(f"studio_trend_scout: YouTube stats error: {e}")
        return {}


def _hours_since(iso_ts: str) -> float:
    """Parse ISO 8601 and return hours elapsed (UTC, never negative)."""
    try:
        dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - dt
        return max(0.1, delta.total_seconds() / 3600.0)
    except Exception:
        return 1.0


# ═════════════════════════════════════════════════════════════════════════════
# Scouting
# ═════════════════════════════════════════════════════════════════════════════

def scout_niche(niche_tag: str, niche_config: dict) -> list:
    """Scout one niche. Returns up to TOP_N_PER_NICHE TrendCandidates."""
    candidates = []

    # Search across configured search terms
    seen_video_ids = set()
    raw_items = []
    for term in niche_config.get("youtube_seed_search_terms", []):
        items = _yt_search(term, max_results=10)
        for item in items:
            vid = item.get("id", {}).get("videoId")
            if not vid or vid in seen_video_ids:
                continue
            seen_video_ids.add(vid)
            raw_items.append(item)

    if not raw_items:
        if not _yt_api_key():
            logger.warning(
                f"studio_trend_scout: niche '{niche_tag}' produced 0 candidates "
                f"(no YOUTUBE_API_KEY or GOOGLE_API_KEY set)"
            )
        else:
            logger.info(f"studio_trend_scout: niche '{niche_tag}' produced 0 candidates from seed terms")
        return []

    # Batch-fetch stats for view counts
    stats = _yt_video_stats([item["id"]["videoId"] for item in raw_items])

    for item in raw_items:
        vid = item["id"]["videoId"]
        snip = item.get("snippet", {})
        views = stats.get(vid, {}).get("views", 0)
        published = snip.get("publishedAt", "")
        velocity = views / _hours_since(published)
        candidates.append(TrendCandidate(
            niche=niche_tag,
            channel=niche_config.get("channel", "(unknown)"),
            source_url=f"https://youtube.com/watch?v={vid}",
            source_channel=snip.get("channelTitle", ""),
            title=snip.get("title", ""),
            views=views,
            published_at=published,
            velocity_per_hour=velocity,
        ))

    # Sort by velocity (views per hour since publish), top N
    candidates.sort(key=lambda c: c.velocity_per_hour, reverse=True)
    return candidates[:TOP_N_PER_NICHE]


# ═════════════════════════════════════════════════════════════════════════════
# Notion writes
# ═════════════════════════════════════════════════════════════════════════════

def _write_candidate_to_notion(notion, cand: TrendCandidate) -> Optional[str]:
    """Create a row in the Studio Pipeline DB. Returns Notion page id or None.

    Idempotency: skip if a record already exists with this Source URL today.
    Implementation: caller filters; this just writes.
    """
    db_id = os.environ.get("NOTION_STUDIO_PIPELINE_DB_ID", "") or PIPELINE_DB_ID
    if not db_id:
        logger.warning("studio_trend_scout: NOTION_STUDIO_PIPELINE_DB_ID not set; cannot write")
        return None
    pipeline_db = db_id

    properties = {
        "Title": {"title": [{"text": {"content": cand.title[:200] or "(no title)"}}]},
        "Channel": {"select": {"name": cand.channel}},
        "Niche tag": {"select": {"name": cand.niche}},
        "Status": {"select": {"name": "scouted"}},
        "Source URL": {"url": cand.source_url},
        "Source channel": {"rich_text": [{"text": {"content": cand.source_channel[:200]}}]},
        "Source views": {"number": int(cand.views)},
        "Hook": {"rich_text": [{"text": {"content": cand.hook[:1000]}}]} if cand.hook else None,
        "Twist": {"rich_text": [{"text": {"content": cand.twist[:1000]}}]} if cand.twist else None,
    }
    properties = {k: v for k, v in properties.items() if v is not None}

    try:
        page = notion.create_page(database_id=pipeline_db, properties=properties)
        return page.get("id") if page else None
    except Exception as e:
        logger.error(f"studio_trend_scout: Notion write failed for {cand.source_url}: {e}")
        return None


def _existing_source_urls_today(notion, today_iso: str) -> set:
    """Return set of Source URLs already in the Pipeline DB today (idempotency)."""
    db_id = os.environ.get("NOTION_STUDIO_PIPELINE_DB_ID", "") or PIPELINE_DB_ID
    if not db_id:
        return set()
    try:
        rows = notion.query_database(db_id, filter_obj=None)
    except Exception as e:
        logger.warning(f"studio_trend_scout: idempotency query failed: {e}")
        return set()
    out = set()
    for r in rows:
        url_field = r.get("properties", {}).get("Source URL", {}).get("url")
        if url_field:
            out.add(url_field)
    return out


# ═════════════════════════════════════════════════════════════════════════════
# Telegram daily brief
# ═════════════════════════════════════════════════════════════════════════════

def _format_brief(picks_per_niche: dict, today_iso: str) -> str:
    """Build a single Telegram message summarizing the day's scout picks."""
    lines = [f"Studio Trend Scout {today_iso}", ""]
    total = 0
    for niche, picks in picks_per_niche.items():
        lines.append(f"=== {niche} ({len(picks)} picks) ===")
        if not picks:
            lines.append("  (no candidates this run)")
        for i, p in enumerate(picks, 1):
            lines.append(f"  {i}. {p.title[:80]}")
            lines.append(f"     {p.views:,} views | {p.velocity_per_hour:.1f}/hr | {p.source_channel}")
            lines.append(f"     {p.source_url}")
        lines.append("")
        total += len(picks)
    if total == 0:
        lines.append("(0 total candidates this run; check YOUTUBE_API_KEY env)")
    else:
        lines.append(f"Total: {total} candidates queued in Studio Pipeline.")
    return "\n".join(lines)


def _telegram_chat_id() -> Optional[str]:
    return os.environ.get("OWNER_TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")


def _send_brief(message: str) -> None:
    chat_id = _telegram_chat_id()
    if not chat_id:
        logger.warning("studio_trend_scout: no OWNER_TELEGRAM_CHAT_ID; skipping brief send")
        return
    try:
        from notifier import send_message
        send_message(str(chat_id), message)
    except Exception as e:
        logger.warning(f"studio_trend_scout: Telegram send failed: {e}")


# ═════════════════════════════════════════════════════════════════════════════
# Main wake callback
# ═════════════════════════════════════════════════════════════════════════════

def studio_trend_scout_tick() -> None:
    """Heartbeat callback. Fires daily. Scouts each configured niche, writes
    candidates to Notion Studio Pipeline, sends Telegram brief.

    Per-crew gate `studio.enabled` must be True in autonomy_state.json for
    this to fire (heartbeat substrate handles the gate).
    """
    tz = pytz.timezone(TIMEZONE)
    today = datetime.now(tz).date().isoformat()

    seeds = _load_seeds()
    logger.info(f"studio_trend_scout: tick start, {len(seeds)} niches configured")

    # Open Notion client
    try:
        from skills.forge_cli.notion_client import NotionClient
        notion_secret = (
            os.environ.get("NOTION_SECRET")
            or os.environ.get("NOTION_API_KEY")
            or os.environ.get("NOTION_TOKEN")
        )
        notion = NotionClient(secret=notion_secret)
    except Exception as e:
        logger.error(f"studio_trend_scout: Notion init failed: {e}")
        return

    existing = _existing_source_urls_today(notion, today)
    logger.info(f"studio_trend_scout: {len(existing)} URLs already in pipeline (idempotency set)")

    picks_per_niche = {}
    written_count = 0
    skipped_count = 0
    for niche_tag, niche_config in seeds.items():
        try:
            picks = scout_niche(niche_tag, niche_config)
        except Exception as e:
            logger.error(f"studio_trend_scout: scout_niche '{niche_tag}' raised: {e}", exc_info=True)
            picks_per_niche[niche_tag] = []
            continue

        # Filter dupes
        new_picks = [p for p in picks if p.source_url not in existing]
        skipped_count += len(picks) - len(new_picks)

        # Write to Notion
        for p in new_picks:
            page_id = _write_candidate_to_notion(notion, p)
            if page_id:
                written_count += 1
                existing.add(p.source_url)

        picks_per_niche[niche_tag] = new_picks
        logger.info(
            f"studio_trend_scout: niche '{niche_tag}': {len(new_picks)} new picks "
            f"({len(picks) - len(new_picks)} dupes skipped)"
        )

    # Telegram brief
    brief = _format_brief(picks_per_niche, today)
    _send_brief(brief)

    logger.info(
        f"studio_trend_scout: tick done written={written_count} "
        f"skipped_dupes={skipped_count} niches={len(seeds)}"
    )
