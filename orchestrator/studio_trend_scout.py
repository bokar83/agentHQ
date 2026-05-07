"""
studio_trend_scout.py - Content Intelligence Scout (Phase 1).

Daily heartbeat (Mon-Sat) that scans niches for relevant content picks:
  - 3 Studio niches (UTB/FGM/AIC) via YouTube Data API v3 -- DAILY
  - 6 Catalyst Works niches via Serper news search -- Mon/Wed/Fri only
  - Sunday: skip everything (Sabbath)

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
from datetime import date, datetime, timedelta, timezone
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
    notion_page_id: str = ""


_yt_key_index = 0  # round-robin state


def _yt_api_key() -> Optional[str]:
    keys = [k for k in [
        os.environ.get("YOUTUBE_API_KEY"),
        os.environ.get("YOUTUBE_API_KEY_2"),
        os.environ.get("GOOGLE_API_KEY"),
    ] if k]
    return keys[0] if keys else None


def _yt_api_key_rotate() -> list[str]:
    """Return all available keys for rotation."""
    return [k for k in [
        os.environ.get("YOUTUBE_API_KEY"),
        os.environ.get("YOUTUBE_API_KEY_2"),
        os.environ.get("GOOGLE_API_KEY"),
    ] if k]


def _yt_search(query: str, max_results: int = 10) -> list:
    """YouTube Data API v3 search. Returns list of video items.
    Rotates across all available API keys on 403 quota errors.
    Returns [] if no API key configured.
    """
    keys = _yt_api_key_rotate()
    if not keys:
        return []
    import httpx
    published_after = (datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)).isoformat()
    for key in keys:
        try:
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
            if resp.status_code == 403:
                logger.warning(f"studio_trend_scout: key ending ...{key[-6:]} quota exceeded, trying next")
                continue
            if resp.status_code != 200:
                logger.warning(f"studio_trend_scout: YouTube search '{query}' returned {resp.status_code}: {resp.text[:200]}")
                return []
            return resp.json().get("items", [])
        except Exception as e:
            logger.warning(f"studio_trend_scout: YouTube search '{query}' error: {e}")
            return []
    logger.warning(f"studio_trend_scout: all API keys exhausted for query '{query}'")
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
    Direct HTTP call. Do NOT use SerperDevTool (CrewAI-only abstraction).
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
# Haiku classifier (replaces full Council, correct tool for triage)
# ═════════════════════════════════════════════════════════════════════════════

_NICHE_CLASSIFIER_CONTEXTS = {
    "african-folktales": {
        "channel_desc": "Under the Baobab — animated African storytelling channel for kids and families",
        "scoring_guide": (
            "Score HIGH (4-5) if: story has a clear moral, features animals/heroes/tricksters, has "
            "emotional arc, strong visual potential, or could be retold with African setting/characters. "
            "Score MEDIUM (3) if: not African but the story structure or moral could be Africanized — "
            "a Japanese fable, a Native American legend, a universal fairy tale. "
            "Score LOW (1-2) if: pure drama/soap opera with no adaptable story structure."
        ),
        "inspiration_note": (
            "We don't need to clone directly. A Japanese kitsune story becomes a West African spirit tale. "
            "A Greek myth becomes a griot legend. Score for INSPIRATION POTENTIAL, not exact fit."
        ),
        "medium_options": "YouTube video",
        "destination": "Studio Pipeline",
    },
    "parenting-psychology": {
        "channel_desc": "Under the Baobab — African family storytelling, parenting through story and wisdom",
        "scoring_guide": (
            "Score HIGH (4-5) if: touches childhood development, parenting styles, family dynamics, "
            "or emotional/behavioral psychology — especially if it has an African or diaspora angle. "
            "Score MEDIUM (3) if: universal parenting insight we could reframe through African lens. "
            "Score LOW (1-2) if: purely clinical with no storytelling or cultural adaptation potential."
        ),
        "inspiration_note": (
            "Western parenting psychology content can be reframed through African family values. "
            "Score for whether we could tell this story our way."
        ),
        "medium_options": "YouTube video",
        "destination": "Studio Pipeline",
    },
    "first-gen-money": {
        "channel_desc": "First Generation Money — financial education for diaspora, immigrants, first-gens who never got the kitchen-table money talk",
        "scoring_guide": (
            "Score HIGH (4-5) if: covers wealth building, budgeting, debt, investing, homebuying, "
            "mortgages, credit, taxes, starting a business, saving for college/vacation/emergencies — "
            "especially if explained simply for beginners. "
            "Score MEDIUM (3) if: general personal finance we can reframe for first-gen audience "
            "(e.g. 'how compound interest works' becomes 'what your parents never told you about money'). "
            "Score LOW (1-2) if: targets high-net-worth or already-wealthy audience with no first-gen angle."
        ),
        "inspiration_note": (
            "Any solid money education video is fair game. We take the idea and tell it for the person "
            "whose parents never had a 401k. Score for reframe potential."
        ),
        "medium_options": "YouTube video",
        "destination": "Studio Pipeline",
    },
    "ai-displacement-first-gen": {
        "channel_desc": "AI Catalyst — helping working-class and first-gen professionals navigate the AI economy",
        "scoring_guide": (
            "Score HIGH (4-5) if: covers AI job displacement, future of work, career pivoting, "
            "AI-proof skills, or automation impact on blue-collar/service workers. "
            "Score MEDIUM (3) if: general AI or career content we can angle toward first-gen workers. "
            "Score LOW (1-2) if: targets executives or investors with no working-class relevance."
        ),
        "inspiration_note": "Score for whether a first-gen worker would find this urgent and actionable.",
        "medium_options": "YouTube video",
        "destination": "Studio Pipeline",
    },
}

_CLASSIFIER_PROMPT_STUDIO = """You are a creative video producer for a faceless YouTube studio. A content scout has found a video. Your job: decide if we can make OUR version of this idea, then design that video.

OUR CHANNEL: {channel_desc}

SCORING GUIDE:
{scoring_guide}

KEY RULE — INSPIRATION OVER CLONING:
{inspiration_note}
The source video does NOT need to match our niche. If a Japanese folktale, a Portuguese finance video, or a Korean parenting clip sparks an idea we can make for our audience — that counts. Score the IDEA we'd make, not the source.

SOURCE VIDEO:
Title: {title}
From channel: {source}
Description: {snippet}

Think step by step:
1. What is the core idea or insight in this video?
2. How would WE tell that idea for OUR specific audience?
3. What's our title, our hook, our angle?

OUTPUT FORMAT (JSON only, no markdown):
{{
  "fit": 3,
  "our_title": "the title of the video WE would make",
  "first_line": "the exact opening line of our video — arresting, specific, in our channel voice",
  "our_concept": "2-3 sentences: the video we make, who it's for, what insight it delivers, how it ends",
  "source_spark": "one sentence on what in the source video sparked this — could be the structure, the emotion, the data point, or just the topic",
  "destination": "{destination}"
}}

fit: 1-5
  1 = no usable idea even with creativity
  2 = weak spark, not worth pursuing
  3 = solid inspiration — we make an adjacent video
  4 = strong idea — direct adaptation with our twist
  5 = clone-worthy — same structure, same hook energy, just our audience and voice
our_title: the actual title we'd publish, not a description of it
first_line: write it as if you're the narrator — this is the first sentence of the script
our_concept: specific enough that a scriptwriter could run with it immediately
"""

_CLASSIFIER_PROMPT_CW = """You are a content triage assistant for Boubacar Barry, a consulting strategist and founder of Catalyst Works.

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
        niche_ctx = _NICHE_CLASSIFIER_CONTEXTS.get(cand.niche)
        if niche_ctx:
            prompt = _CLASSIFIER_PROMPT_STUDIO.format(
                channel_desc=niche_ctx["channel_desc"],
                scoring_guide=niche_ctx["scoring_guide"],
                inspiration_note=niche_ctx["inspiration_note"],
                title=cand.title[:300],
                source=cand.source_channel or cand.channel,
                snippet=cand.snippet[:400] if cand.snippet else cand.hook[:400],
                destination=niche_ctx["destination"],
            )
        else:
            prompt = _CLASSIFIER_PROMPT_CW.format(
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
        cand.medium = parsed.get("medium", "YouTube video")
        cand.first_line = parsed.get("first_line", "")
        # Studio niches: our_title overrides source title, our_concept goes in unique_add
        if parsed.get("our_title"):
            cand.hook = parsed["our_title"]
        if parsed.get("our_concept"):
            cand.unique_add = parsed["our_concept"]
        elif parsed.get("unique_add"):
            cand.unique_add = parsed["unique_add"]
        if parsed.get("source_spark"):
            cand.twist = parsed["source_spark"]
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
# Notion writes. Two separate functions, one per destination schema
# ═════════════════════════════════════════════════════════════════════════════

def _write_to_studio_pipeline(notion, cand: TrendCandidate) -> Optional[str]:
    """Write a Studio-niche pick to the Notion Studio Pipeline DB.
    Returns Notion page id or None on failure.
    """
    db_id = os.environ.get("NOTION_STUDIO_PIPELINE_DB_ID", "") or PIPELINE_DB_ID
    if not db_id:
        logger.warning("studio_trend_scout: NOTION_STUDIO_PIPELINE_DB_ID not set; cannot write")
        return None

    # our_title (video we'll make) lives in cand.hook; source title in cand.title
    our_title = cand.hook or cand.title or "(no title)"
    properties = {
        "Title": {"title": [{"text": {"content": our_title[:200]}}]},
        "Channel": {"select": {"name": cand.channel}},
        "Niche tag": {"select": {"name": cand.niche}},
        "Status": {"select": {"name": "scouted"}},
        "Source URL": {"url": cand.source_url},
        "Source channel": {"rich_text": [{"text": {"content": cand.source_channel[:200]}}]},
        "Source views": {"number": int(cand.views)},
    }
    # Hook = first_line (opening sentence the scriptwriter starts with)
    if cand.first_line:
        properties["Hook"] = {"rich_text": [{"text": {"content": cand.first_line[:1000]}}]}
    # Twist = our_concept (full video brief — who it's for, insight, ending)
    if cand.unique_add:
        properties["Twist"] = {"rich_text": [{"text": {"content": cand.unique_add[:1000]}}]}
    # Store source title + spark in Draft field (QA notes alt — only field available)
    if cand.title and cand.title != our_title:
        source_note = f"Source: {cand.title[:300]}"
        if cand.twist:
            source_note += f"\nSpark: {cand.twist[:300]}"
        properties["Draft"] = {"rich_text": [{"text": {"content": source_note[:2000]}}]}

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
        our_title = cand.hook or cand.title
        inspired_by = f"\nInspired by: {cand.title[:80]}" if cand.hook and cand.hook != cand.title else ""
        text = (
            f"🎬 [{cand.niche}] {our_title[:100]}\n"
            f"{inspired_by}"
            f"\nOpening: {cand.first_line[:200]}"
            f"\nConcept: {cand.unique_add[:250]}"
            f"\nSource: {cand.source_url}"
        )
        buttons = [[
            (f"Approve", f"scout_approve:{notion_page_id}"),
            (f"Reject", f"scout_reject:{notion_page_id}"),
        ]]
        if cand.destination == "Content Board":
            buttons[0].append((f"Newsletter", f"scout_newsletter:{notion_page_id}"))
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


def get_reply_for_week(week_start_date: date) -> Optional[str]:
    """Lazy import wrapper for the Sunday editorial reply lookup."""
    try:
        from newsletter_editorial_input import get_reply_for_week as _get_reply_for_week
        return _get_reply_for_week(week_start_date)
    except ImportError:
        return None


def _send_anchor_alert(text: str) -> None:
    """Send a one-off Telegram alert for anchor selection outcomes."""
    chat_id = _telegram_chat_id()
    if not chat_id:
        return
    try:
        from notifier import send_message

        send_message(str(chat_id), text)
    except Exception as e:
        logger.warning(f"studio_trend_scout: anchor alert send failed: {e}")


def _anchor_date_newsletter_filter(week_iso: str) -> dict:
    return {
        "and": [
            {"property": "Anchor Date", "date": {"equals": week_iso}},
            {"property": "Type", "select": {"equals": "Newsletter"}},
        ]
    }


def _find_existing_newsletter_anchor(notion, week_iso: str) -> Optional[dict]:
    """Return an existing Content Board row already tagged as this week's anchor."""
    if not CONTENT_BOARD_DB_ID:
        return None
    try:
        rows = notion.query_database(
            CONTENT_BOARD_DB_ID,
            filter_obj=_anchor_date_newsletter_filter(week_iso),
        )
    except Exception as e:
        logger.warning(f"studio_trend_scout: existing anchor lookup failed: {e}")
        return None
    return rows[0] if rows else None


def _page_type_name(page: Optional[dict]) -> Optional[str]:
    props = (page or {}).get("properties", {})
    type_select = props.get("Type", {}).get("select")
    if not type_select:
        return None
    return type_select.get("name")


def _newsletter_rank_key(cand: TrendCandidate) -> tuple:
    return (-int(cand.fit_score or 0), -float(cand.velocity_per_hour or 0.0), cand.source_url)


def _build_sunday_reply_anchor_properties(reply_text: str, week_iso: str) -> dict:
    title = reply_text.strip()[:120] or "Weekly newsletter anchor"
    return {
        "Title": {"title": [{"text": {"content": title}}]},
        "Status": {"select": {"name": "Ready"}},
        "Type": {"select": {"name": "Newsletter"}},
        "Source Note": {"rich_text": [{"text": {"content": reply_text[:2000]}}]},
        "Anchor Date": {"date": {"start": week_iso}},
    }


def _newsletter_anchor_update_properties(week_iso: str) -> dict:
    return {
        "Status": {"select": {"name": "Ready"}},
        "Type": {"select": {"name": "Newsletter"}},
        "Anchor Date": {"date": {"start": week_iso}},
    }


def _select_and_tag_anchor(
    notion,
    cw_picks_written: list[TrendCandidate],
    week_monday: date,
) -> Optional[str]:
    """Choose the weekly newsletter anchor with idempotent, tag-aware writes."""
    week_iso = week_monday.isoformat()
    existing_anchor = _find_existing_newsletter_anchor(notion, week_iso)
    if existing_anchor:
        page_id = existing_anchor.get("id")
        logger.info(f"studio_trend_scout: anchor=reused page={page_id}")
        return page_id

    sunday_reply = get_reply_for_week(week_monday)
    if sunday_reply:
        try:
            page = notion.create_page(
                database_id=CONTENT_BOARD_DB_ID,
                properties=_build_sunday_reply_anchor_properties(sunday_reply.strip(), week_iso),
            )
        except Exception as e:
            logger.error(f"studio_trend_scout: synthetic anchor create failed: {e}")
            _send_anchor_alert("newsletter anchor failed to write")
            return None
        page_id = page.get("id") if page else None
        logger.info(f"studio_trend_scout: anchor=synthetic page={page_id}")
        return page_id

    for cand in sorted(cw_picks_written, key=_newsletter_rank_key):
        if not cand.notion_page_id:
            continue
        try:
            page = notion.get_page(cand.notion_page_id)
        except Exception as e:
            logger.warning(
                f"studio_trend_scout: anchor page read failed for {cand.notion_page_id}: {e}"
            )
            continue

        if _page_type_name(page):
            continue

        try:
            notion.update_page(
                cand.notion_page_id,
                properties=_newsletter_anchor_update_properties(week_iso),
            )
        except Exception as e:
            logger.error(
                f"studio_trend_scout: anchor tag update failed for {cand.notion_page_id}: {e}"
            )
            _send_anchor_alert("newsletter anchor tag update failed")
            return None

        logger.info(
            f"studio_trend_scout: anchor=scout-pick page={cand.notion_page_id} "
            f"title={cand.title[:60]}"
        )
        return cand.notion_page_id

    if cw_picks_written:
        _send_anchor_alert("all top picks already typed; tag manually")
        return None

    _send_anchor_alert(f"no anchor today for {week_iso}")
    return None


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

    # Cadence (changed 2026-05-07):
    #   Studio niches (UTB/FGM/AIC) -- DAILY, including weekends
    #   CW niches (6 personal-brand niches) -- Mon/Wed/Fri only
    # Per-niche skip happens inside the scout loop via _is_niche_due_today.
    # Sunday: skip everything per Boubacar's Sabbath rule.
    weekday = now.weekday()  # Mon=0, Sun=6
    if weekday == 6:
        logger.info("studio_trend_scout: Sunday Sabbath, skipping all niches")
        return

    today = now.date().isoformat()

    # One-run-per-day guard: prevents repeated Telegram briefs on container restarts.
    # Writes a marker file after first successful run; cleared at midnight by date change.
    _run_marker = pathlib.Path("/app/data/scout_ran_today.txt")
    try:
        _run_marker.parent.mkdir(parents=True, exist_ok=True)
        if _run_marker.exists() and _run_marker.read_text().strip() == today:
            logger.info("studio_trend_scout: already ran today (%s), skipping duplicate", today)
            return
    except Exception:
        pass  # If we can't check the marker, run anyway

    seeds = _load_seeds()
    weekday_name = now.strftime("%A")
    logger.info(f"studio_trend_scout: {weekday_name} tick start, {len(seeds)} niches configured")

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
    cw_picks_written: list[TrendCandidate] = []

    # CW personal-brand niches run Mon/Wed/Fri only (weekdays 0,2,4).
    # Studio niches (Under the Baobab, AI Catalyst, First Gen Money) run daily Mon-Sat.
    cw_due_today = weekday in (0, 2, 4)

    for niche_tag, niche_config in seeds.items():
        niche_dest = niche_config.get("destination", "Studio Pipeline")
        if niche_dest == "Content Board" and not cw_due_today:
            logger.info(
                f"studio_trend_scout: skipping CW niche '{niche_tag}' "
                f"(weekday={weekday}, only fires Mon/Wed/Fri)"
            )
            continue
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
                if page_id:
                    p.notion_page_id = page_id
                    cw_picks_written.append(p)
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

    try:
        _select_and_tag_anchor(notion, cw_picks_written, now.date())
    except Exception as e:
        logger.error(f"studio_trend_scout: anchor selection raised: {e}", exc_info=True)

    # Write run marker so restarts don't re-send Telegram briefs today
    try:
        _run_marker.write_text(today)
    except Exception:
        pass

    _send_summary(written_count, today)
    logger.info(
        f"studio_trend_scout: tick done written={written_count} "
        f"skipped_dupes={skipped_count} niches={len(seeds)}"
    )
