"""
studio_trend_scout.py - Content Intelligence Scout (Phase 1).

Monday-only heartbeat that scans 9 niches for relevant content picks:
  - 3 Studio niches via YouTube Data API v3 (view velocity scoring)
  - 6 Catalyst Works niches via Serper news search

Each pick goes through a single Haiku classifier call (fit 1-5, medium,
first line, unique angle). Low-fit picks (<=2) are dropped silently.
Passing picks are written to Notion (Content Board for CW niches, Studio
Pipeline for Studio niches) and sent to Telegram with Approve/Reject
buttons wired to the approval_queue.

Phase 2 (2026-05-12): add niches 7-10, dedup check, leGriot auto-draft.

Seeds config: data/studio_trend_seeds.json (gitignored, machine-local)
or orchestrator/studio_trend_seeds.default.json (committed default).
DB IDs: NOTION_STUDIO_PIPELINE_DB_ID (Studio), FORGE_CONTENT_DB (CW).
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
CONTENT_BOARD_DB_ID = os.environ.get("FORGE_CONTENT_DB", "339bcf1a-3029-81d1-8377-dc2f2de13a20")
TOP_N_PER_NICHE = int(os.environ.get("STUDIO_TREND_SCOUT_TOP_N", "3"))
LOOKBACK_DAYS = int(os.environ.get("STUDIO_TREND_SCOUT_LOOKBACK_DAYS", "7"))
FIT_THRESHOLD = int(os.environ.get("STUDIO_TREND_SCOUT_FIT_THRESHOLD", "3"))

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
    """One trend-scout pick. Becomes a row in the Notion Pipeline DB or Content Board."""
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
    # Classifier fields (set by _classify_pick)
    fit_score: int = 0
    medium: str = ""
    first_line: str = ""
    unique_add: str = ""
    destination: str = "Studio Pipeline"  # "Content Board" or "Studio Pipeline"
    snippet: str = ""


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


# ═════════════════════════════════════════════════════════════════════════════
# Serper news search (for Catalyst Works niches)
# ═════════════════════════════════════════════════════════════════════════════

def _serper_search(query: str, max_results: int = 5) -> list:
    """Search Serper news API. Returns list of {title, link, snippet, source, date}.
    Graceful degrade: returns [] if SERPER_API_KEY not set.
    Direct HTTP call -- do NOT use SerperDevTool (CrewAI-only abstraction).
    """
    api_key = os.environ.get("SERPER_API_KEY", "")
    if not api_key:
        logger.warning("studio_trend_scout: SERPER_API_KEY not set; skipping Serper search")
        return []
    try:
        import httpx
        resp = httpx.post(
            "https://google.serper.dev/news",
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": query, "num": max_results, "gl": "us", "hl": "en"},
            timeout=15,
        )
        if resp.status_code != 200:
            logger.warning(f"studio_trend_scout: Serper returned {resp.status_code} for '{query}'")
            return []
        news = resp.json().get("news", [])
        return [
            {
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "source": item.get("source", ""),
                "date": item.get("date", ""),
            }
            for item in news
        ]
    except Exception as e:
        logger.warning(f"studio_trend_scout: Serper search '{query}' error: {e}")
        return []


# ═════════════════════════════════════════════════════════════════════════════
# Haiku classifier (replaces full Council -- correct tool for triage)
# ═════════════════════════════════════════════════════════════════════════════

_CLASSIFIER_PROMPT = """You are a content triage assistant for Boubacar Barry, a consulting strategist and founder of Catalyst Works.

Given a content item, score it and suggest how Boubacar can use it. Respond with valid JSON only.

Boubacar's audience: business owner-operators navigating AI adoption, operational efficiency, and building sustainable margins.
Core topics: AI governance, hidden costs, operational failures, SMB-specific AI, workforce transitions, leadership accountability.
Voice: warm colleague walking alongside the reader, not a professor. Wit and directness required.

CONTENT ITEM:
Title: {title}
Source: {source}
Snippet: {snippet}

OUTPUT FORMAT (JSON only, no markdown):
{{
  "fit": 1,
  "medium": "LinkedIn post",
  "first_line": "one sentence Boubacar could open with, in his voice",
  "unique_add": "what Boubacar uniquely contributes that the source misses",
  "destination": "Content Board"
}}

fit: 1-5 (1=irrelevant to Boubacar's audience, 5=perfect fit)
medium: one of "LinkedIn post", "X post", "Newsletter", "LinkedIn article", "YouTube video"
first_line: one concrete opening sentence in Boubacar's voice (not generic)
unique_add: one sentence on the angle only Boubacar can add
destination: "Content Board" for Catalyst Works niches, "Studio Pipeline" for Studio niches
"""


def _classify_pick(cand: TrendCandidate) -> TrendCandidate:
    """Run Haiku classifier on a single pick. Returns updated candidate.
    Sets fit_score=0 on any error (will be dropped by caller).
    """
    try:
        from llm_helpers import call_llm
        import json as _json
        prompt = _CLASSIFIER_PROMPT.format(
            title=cand.title[:300],
            source=cand.source_channel or cand.channel,
            snippet=cand.snippet[:400] if cand.snippet else cand.hook[:400],
        )
        response = call_llm(
            messages=[{"role": "user", "content": prompt}],
            model="anthropic/claude-haiku-4.5",
            temperature=0.3,
        )
        raw = (response.choices[0].message.content or "").strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = _json.loads(raw)
        cand.fit_score = int(parsed.get("fit", 0))
        cand.medium = parsed.get("medium", "LinkedIn post")
        cand.first_line = parsed.get("first_line", "")
        cand.unique_add = parsed.get("unique_add", "")
        cand.destination = parsed.get("destination", cand.destination)
    except Exception as e:
        logger.warning(f"studio_trend_scout: classifier failed for '{cand.title[:60]}': {e}")
        cand.fit_score = 0
    return cand


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
    """Scout one niche. Returns up to TOP_N_PER_NICHE classified TrendCandidates.

    Source routing:
    - youtube_seed_search_terms present -> YouTube Data API
    - serper_search_terms present -> Serper news search
    Picks are classified by Haiku. Low-fit picks (fit <= FIT_THRESHOLD) dropped.
    """
    source_type = niche_config.get("source", "youtube")
    default_destination = niche_config.get("destination", "Studio Pipeline")
    candidates = []

    if source_type == "serper":
        seen_urls: set = set()
        for term in niche_config.get("serper_search_terms", []):
            results = _serper_search(term, max_results=5)
            for item in results:
                url = item.get("link", "")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                candidates.append(TrendCandidate(
                    niche=niche_tag,
                    channel=niche_config.get("channel", "Catalyst Works"),
                    source_url=url,
                    source_channel=item.get("source", ""),
                    title=item.get("title", ""),
                    views=0,
                    published_at=item.get("date", ""),
                    velocity_per_hour=0.0,
                    snippet=item.get("snippet", ""),
                    destination=default_destination,
                ))
    else:
        # YouTube path (existing logic)
        seen_video_ids: set = set()
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
            return []

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
                destination=default_destination,
            ))
        candidates.sort(key=lambda c: c.velocity_per_hour, reverse=True)
        candidates = candidates[:TOP_N_PER_NICHE * 2]  # classify more, keep top N after filter

    # Classify each candidate with Haiku, drop low-fit picks
    classified = []
    for cand in candidates:
        cand = _classify_pick(cand)
        if cand.fit_score >= FIT_THRESHOLD:
            classified.append(cand)

    classified.sort(key=lambda c: c.fit_score, reverse=True)
    return classified[:TOP_N_PER_NICHE]


# ═════════════════════════════════════════════════════════════════════════════
# Notion writes -- two separate functions, one per destination schema
# ═════════════════════════════════════════════════════════════════════════════

def _write_to_studio_pipeline(notion, cand: TrendCandidate) -> Optional[str]:
    """Write a Studio-niche pick to the Notion Studio Pipeline DB.
    Returns Notion page id or None on failure.
    """
    db_id = os.environ.get("NOTION_STUDIO_PIPELINE_DB_ID", "") or PIPELINE_DB_ID
    if not db_id:
        logger.warning("studio_trend_scout: NOTION_STUDIO_PIPELINE_DB_ID not set; cannot write")
        return None

    hook_text = cand.first_line or cand.hook or ""
    properties = {
        "Title": {"title": [{"text": {"content": cand.title[:200] or "(no title)"}}]},
        "Channel": {"select": {"name": cand.channel}},
        "Niche tag": {"select": {"name": cand.niche}},
        "Status": {"select": {"name": "scouted"}},
        "Source URL": {"url": cand.source_url},
        "Source channel": {"rich_text": [{"text": {"content": cand.source_channel[:200]}}]},
        "Source views": {"number": int(cand.views)},
    }
    if hook_text:
        properties["Hook"] = {"rich_text": [{"text": {"content": hook_text[:1000]}}]}
    if cand.unique_add:
        properties["Twist"] = {"rich_text": [{"text": {"content": cand.unique_add[:1000]}}]}

    try:
        page = notion.create_page(database_id=db_id, properties=properties)
        return page.get("id") if page else None
    except Exception as e:
        logger.error(f"studio_trend_scout: Studio Pipeline write failed for {cand.source_url}: {e}")
        return None


def _write_to_content_board(notion, cand: TrendCandidate) -> Optional[str]:
    """Write a CW-niche pick to the Notion Content Board as Status=Draft.
    Returns Notion page id or None on failure.
    """
    if not CONTENT_BOARD_DB_ID:
        logger.warning("studio_trend_scout: FORGE_CONTENT_DB not set; cannot write to Content Board")
        return None

    # Source note: surface the URL and unique angle for Boubacar
    source_note = f"Scout pick: {cand.source_url}"
    if cand.unique_add:
        source_note += f"\nAngle: {cand.unique_add}"

    properties = {
        "Title": {"title": [{"text": {"content": cand.title[:200] or "(no title)"}}]},
        "Status": {"select": {"name": "Draft"}},
        "Source Note": {"rich_text": [{"text": {"content": source_note[:2000]}}]},
    }
    if cand.first_line:
        properties["Hook"] = {"rich_text": [{"text": {"content": cand.first_line[:1000]}}]}
    if cand.medium:
        # Map medium to Platform field
        platform_map = {
            "LinkedIn post": "LinkedIn",
            "LinkedIn article": "LinkedIn",
            "X post": "X",
            "Newsletter": None,
            "YouTube video": "YouTube",
        }
        platform = platform_map.get(cand.medium)
        if platform:
            properties["Platform"] = {"multi_select": [{"name": platform}]}

    try:
        page = notion.create_page(database_id=CONTENT_BOARD_DB_ID, properties=properties)
        return page.get("id") if page else None
    except Exception as e:
        logger.error(f"studio_trend_scout: Content Board write failed for {cand.source_url}: {e}")
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
# Telegram brief with per-pick Approve/Reject buttons
# ═════════════════════════════════════════════════════════════════════════════

def _telegram_chat_id() -> Optional[str]:
    return os.environ.get("OWNER_TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")


def _send_pick_with_buttons(cand: TrendCandidate, notion_page_id: str) -> None:
    """Send one pick to Telegram with Approve/Reject inline buttons."""
    chat_id = _telegram_chat_id()
    if not chat_id:
        return
    try:
        from notifier import send_message_with_buttons
        dest_label = "Content Board" if cand.destination == "Content Board" else "Studio Pipeline"
        text = (
            f"Scout pick [{cand.niche}]\n"
            f"{cand.title[:120]}\n"
            f"Medium: {cand.medium} | Dest: {dest_label}\n"
            f"Opening: {cand.first_line[:200]}\n"
            f"Boubacar adds: {cand.unique_add[:200]}\n"
            f"{cand.source_url}"
        )
        buttons = [[
            (f"Approve", f"scout_approve:{notion_page_id}"),
            (f"Reject", f"scout_reject:{notion_page_id}"),
        ]]
        send_message_with_buttons(str(chat_id), text, buttons)
    except Exception as e:
        logger.warning(f"studio_trend_scout: per-pick Telegram send failed: {e}")


def _send_summary(total: int, today_iso: str) -> None:
    """Send a one-line summary after all per-pick messages."""
    chat_id = _telegram_chat_id()
    if not chat_id:
        return
    try:
        from notifier import send_message
        msg = f"Content Scout {today_iso}: {total} pick(s) queued. Tap Approve on each to queue for publishing."
        if total == 0:
            msg = f"Content Scout {today_iso}: 0 picks this run (check YOUTUBE_API_KEY / SERPER_API_KEY)."
        send_message(str(chat_id), msg)
    except Exception as e:
        logger.warning(f"studio_trend_scout: summary send failed: {e}")


# ═════════════════════════════════════════════════════════════════════════════
# Main wake callback
# ═════════════════════════════════════════════════════════════════════════════

def studio_trend_scout_tick() -> None:
    """Heartbeat callback. Monday-only. Scouts each configured niche, classifies
    picks with Haiku, writes to Notion (Content Board or Studio Pipeline depending
    on niche), sends per-pick Telegram messages with Approve/Reject buttons.

    Per-crew gate `studio.enabled` must be True in autonomy_state.json for
    this to fire (heartbeat substrate handles the gate).
    """
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)

    # Monday-only gate (weekday 0 = Monday)
    if now.weekday() != 0:
        logger.debug("studio_trend_scout: not Monday, skipping")
        return

    today = now.date().isoformat()
    seeds = _load_seeds()
    logger.info(f"studio_trend_scout: Monday tick start, {len(seeds)} niches configured")

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

    written_count = 0
    skipped_count = 0

    for niche_tag, niche_config in seeds.items():
        try:
            picks = scout_niche(niche_tag, niche_config)
        except Exception as e:
            logger.error(f"studio_trend_scout: scout_niche '{niche_tag}' raised: {e}", exc_info=True)
            continue

        # Filter dupes
        new_picks = [p for p in picks if p.source_url not in existing]
        skipped_count += len(picks) - len(new_picks)

        for p in new_picks:
            # Route to correct Notion DB based on destination
            if p.destination == "Content Board":
                page_id = _write_to_content_board(notion, p)
            else:
                page_id = _write_to_studio_pipeline(notion, p)

            if page_id:
                written_count += 1
                existing.add(p.source_url)
                _send_pick_with_buttons(p, page_id)

        logger.info(
            f"studio_trend_scout: niche '{niche_tag}': {len(new_picks)} new picks "
            f"({len(picks) - len(new_picks)} dupes skipped)"
        )

    _send_summary(written_count, today)
    logger.info(
        f"studio_trend_scout: tick done written={written_count} "
        f"skipped_dupes={skipped_count} niches={len(seeds)}"
    )
