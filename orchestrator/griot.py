"""
griot.py - Phase 3 L0.5 autonomous content pilot.

Heartbeat wake callback that runs every weekday morning (07:00 America/Denver).
Deterministic picker (zero LLM calls at this level). Reads the Notion Content
Board, filters to Ready drafts that are not yet scheduled, scores each against
recency + arc coverage, enqueues the top candidate to approval_queue.

L0.5 design decision: propose candidates, not drafts. The actual leGriot copy
work only runs after Boubacar approves the candidate (Phase 3.5). This keeps
morning cost at $0 even when enabled, so the autonomy spend cap is never the
first line of defense.

Safety layers (defense in depth, outermost to innermost):
  1. heartbeat._fire checks guard killed + per-crew enabled (Phase 2.6)
  2. Callback weekday gate: no weekend proposals
  3. Double-fire guard: skip if a successful griot outcome fired in last 20h
  4. Candidate dedup: skip candidates proposed via approval_queue in last 7 days
  5. Empty backlog: Telegram heads-up, no queue write

Tests for each layer live in tests/test_griot.py.
"""
from __future__ import annotations

import logging
import os
from datetime import date, datetime, timedelta, timezone
from typing import Optional

import pytz

logger = logging.getLogger("agentsHQ.griot")

# Timezone anchor (matches heartbeat).
TIMEZONE = os.environ.get("HEARTBEAT_TIMEZONE", "America/Denver")


def _pg_conn():
    """Thin wrapper around memory._pg_conn. Module-level so tests can patch griot._pg_conn."""
    from memory import _pg_conn as _mem_pg_conn  # noqa: PLC0415
    return _mem_pg_conn()

# Notion Content Board database id (same env var that content_board_reorder.py uses).
CONTENT_DB_ID = os.environ.get("FORGE_CONTENT_DB", "339bcf1a-3029-81d1-8377-dc2f2de13a20")

# ═════════════════════════════════════════════════════════════════════════════
# Scoring weights. Exposed as a module-level dict so they can be tuned in one
# place without editing the scoring function. Boubacar can override by editing
# this block and rebuilding; future Phase 5 Chairman may learn these.
# ═════════════════════════════════════════════════════════════════════════════

SCORING_WEIGHTS = {
    # Base: the Content Board's Total Score is the primary signal (0..50).
    "total_score_weight": 1.0,
    # +N for the smallest unused Arc Priority that still has a pending draft.
    "next_arc_bonus": 5,
    # -N for each idea whose Topic overlaps a post in the last 7 days.
    "topic_overlap_penalty": 10,
    # -N for same Arc Phase fired in last 3 days.
    "recent_arc_phase_penalty": 20,
}

# How far back to consider a "recent" post for overlap math.
RECENCY_WINDOW_DAYS = 7
ARC_PHASE_WINDOW_DAYS = 3

# Idempotency window: skip if a successful griot outcome already fired within this.
DOUBLE_FIRE_GUARD_HOURS = 20

# Dedup window: don't propose the same Notion record twice within this window.
CANDIDATE_DEDUP_DAYS = 7


# ═════════════════════════════════════════════════════════════════════════════
# Notion field extractors. Content Board stores multi-select on Topic and
# Platform, select on Status and Arc Phase, number on Arc Priority + Total
# Score, date on Scheduled Date. Pattern mirrors content_board_reorder.py.
# ═════════════════════════════════════════════════════════════════════════════

def _get_title(prop: dict) -> str:
    arr = prop.get("title") if prop else None
    if not arr:
        return ""
    return arr[0].get("plain_text", "")


def _get_text(prop: dict) -> str:
    arr = prop.get("rich_text") if prop else None
    if not arr:
        return ""
    return "".join(t.get("plain_text", "") for t in arr)


def _get_select(prop: dict) -> Optional[str]:
    if not prop:
        return None
    sel = prop.get("select") or prop.get("status")
    if not sel:
        return None
    return sel.get("name")


def _get_multi(prop: dict) -> list:
    arr = prop.get("multi_select") if prop else None
    if not arr:
        return []
    return [x.get("name") for x in arr if x.get("name")]


def _get_number(prop: dict) -> Optional[float]:
    return prop.get("number") if prop else None


def _get_date(prop: dict) -> Optional[str]:
    d = prop.get("date") if prop else None
    if not d:
        return None
    return d.get("start")


def _row_from_notion(p: dict) -> dict:
    """Flatten one Notion page into the fields Griot cares about."""
    props = p.get("properties", {})
    return {
        "notion_id": p["id"],
        "title": _get_title(props.get("Title", {})),
        "status": _get_select(props.get("Status", {})),
        "platform": _get_multi(props.get("Platform", {})),
        "topic": _get_multi(props.get("Topic", {})),
        "arc_priority": _get_number(props.get("Arc Priority", {})),
        "arc_phase": _get_select(props.get("Arc Phase", {})),
        "total_score": _get_number(props.get("Total Score", {})),
        "hook": _get_text(props.get("Hook", {})),
        "draft": _get_text(props.get("Draft", {})),
        "scheduled_date": _get_date(props.get("Scheduled Date", {})),
    }


# ═════════════════════════════════════════════════════════════════════════════
# Safety guards
# ═════════════════════════════════════════════════════════════════════════════

def _is_weekend(now: datetime) -> bool:
    # datetime.weekday(): Monday=0, Sunday=6. Saturday=5, Sunday=6.
    return now.weekday() >= 5


def _recently_fired_successfully() -> bool:
    """Skip if a griot task_outcome with a proposal result fired in last 20h.

    Distinguishes from skipped fires (which do NOT write task_outcomes rows per
    the Council's start_task-below-skips ordering). See griot_morning_tick.
    """
    try:
        from memory import _pg_conn
        conn = _pg_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT 1
                FROM task_outcomes
                WHERE crew_name = %s
                  AND ts_started > NOW() - INTERVAL '%s hours'
                  AND (result_summary IS NULL OR result_summary NOT LIKE 'skip:%%')
                LIMIT 1
                """,
                ("griot", DOUBLE_FIRE_GUARD_HOURS),
            )
            row = cur.fetchone()
            cur.close()
        finally:
            conn.close()
        return row is not None
    except Exception as e:
        logger.warning(f"Griot: _recently_fired_successfully check failed ({e}); assume no recent fire")
        return False


def _candidate_already_proposed(notion_id: str) -> bool:
    """Skip a specific Notion record if it was proposed via approval_queue recently.

    Separate from double-fire guard. This prevents proposing the same idea
    twice in a week regardless of whether the previous proposal was approved,
    rejected, or edited.
    """
    try:
        from memory import _pg_conn
        conn = _pg_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT 1
                FROM approval_queue
                WHERE crew_name = 'griot'
                  AND payload->>'notion_id' = %s
                  AND ts_created > NOW() - INTERVAL '%s days'
                LIMIT 1
                """,
                (notion_id, CANDIDATE_DEDUP_DAYS),
            )
            row = cur.fetchone()
            cur.close()
        finally:
            conn.close()
        return row is not None
    except Exception as e:
        logger.warning(f"Griot: _candidate_already_proposed check for {notion_id} failed ({e}); assume not duplicate")
        return False


# ═════════════════════════════════════════════════════════════════════════════
# Fetch + score
# ═════════════════════════════════════════════════════════════════════════════

def _fetch_board_rows(notion_client) -> list:
    """Return all Content Board rows as flattened dicts."""
    posts = notion_client.query_database(CONTENT_DB_ID, filter_obj=None)
    return [_row_from_notion(p) for p in posts]


def _split_pool(rows: list, today_iso: str) -> tuple:
    """Partition rows into (candidates, recent_posts).

    candidates: status=Ready, no scheduled date, has platform in {LinkedIn, X}
                and has Hook or Title content to act on.
    recent_posts: status in {Queued, Posted} with Scheduled Date within
                  RECENCY_WINDOW_DAYS of today.
    """
    candidates = []
    recent_posts = []
    cutoff = (date.fromisoformat(today_iso) - timedelta(days=RECENCY_WINDOW_DAYS)).isoformat()
    for r in rows:
        if r["status"] == "Ready" and not r["scheduled_date"]:
            if any(pl in {"LinkedIn", "X"} for pl in r["platform"]):
                if r["title"] or r["hook"] or r["draft"]:  # body optional -- Enhance can fill it
                    candidates.append(r)
        elif r["status"] in {"Queued", "Posted", "Ready"} and r["scheduled_date"]:
            if r["scheduled_date"] >= cutoff:
                recent_posts.append(r)
    return candidates, recent_posts


def _score_candidate(cand: dict, recent_posts: list, next_arc_priority: Optional[float]) -> tuple:
    """Return (score, score_breakdown_str) for one candidate."""
    w = SCORING_WEIGHTS
    breakdown = []

    # Base score from Notion.
    base = (cand.get("total_score") or 0) * w["total_score_weight"]
    score = base
    breakdown.append(f"base={base:.0f}")

    # Next-in-arc bonus.
    if (
        next_arc_priority is not None
        and cand.get("arc_priority") is not None
        and cand["arc_priority"] == next_arc_priority
    ):
        score += w["next_arc_bonus"]
        breakdown.append(f"+{w['next_arc_bonus']} next-in-arc")

    # Topic overlap penalty against any recent post within window.
    cand_topics = set(cand.get("topic") or [])
    recent_topics = set()
    for rp in recent_posts:
        recent_topics.update(rp.get("topic") or [])
    if cand_topics & recent_topics:
        score -= w["topic_overlap_penalty"]
        breakdown.append(f"-{w['topic_overlap_penalty']} topic overlap")

    # Arc Phase recency penalty.
    if cand.get("arc_phase"):
        today = datetime.now(timezone.utc).date()
        cutoff = today - timedelta(days=ARC_PHASE_WINDOW_DAYS)
        for rp in recent_posts:
            if rp.get("arc_phase") != cand["arc_phase"]:
                continue
            sd = rp.get("scheduled_date")
            if not sd:
                continue
            try:
                sd_date = date.fromisoformat(sd[:10])
            except Exception:
                continue
            if sd_date >= cutoff:
                score -= w["recent_arc_phase_penalty"]
                breakdown.append(f"-{w['recent_arc_phase_penalty']} recent arc phase")
                break

    return score, ", ".join(breakdown)


def _min_unused_arc_priority(candidates: list, recent_posts: list) -> Optional[float]:
    """Return the smallest Arc Priority present in candidates but NOT in recent_posts.

    Arc Priority is not globally unique (LinkedIn + X share the same number per
    arc position). Griot picks the smallest candidate priority whose paired
    recent posts don't already cover it.
    """
    cand_priorities = {c["arc_priority"] for c in candidates if c.get("arc_priority") is not None}
    recent_priorities = {r["arc_priority"] for r in recent_posts if r.get("arc_priority") is not None}
    unused = cand_priorities - recent_priorities
    if not unused:
        return None
    return min(unused)


def _pick_top_candidate(candidates: list, recent_posts: list) -> Optional[dict]:
    """Return the candidate dict with the highest score, augmented with 'why_chosen'.

    Tiebreak: smallest Arc Priority (None arcs sort last).
    """
    if not candidates:
        return None
    next_arc = _min_unused_arc_priority(candidates, recent_posts)
    scored = []
    for cand in candidates:
        score, breakdown = _score_candidate(cand, recent_posts, next_arc)
        scored.append((score, cand.get("arc_priority") if cand.get("arc_priority") is not None else 999, cand, breakdown))
    scored.sort(key=lambda x: (-x[0], x[1]))
    score, _tiebreak, top, breakdown = scored[0]
    chosen = dict(top)
    chosen["score"] = score
    chosen["why_chosen"] = breakdown
    return chosen


# ═════════════════════════════════════════════════════════════════════════════
# Main callback
# ═════════════════════════════════════════════════════════════════════════════

def griot_morning_tick() -> None:
    """
    Heartbeat callback. Runs every morning when the griot-morning wake fires
    AND heartbeat._per_crew_allowed('griot') returns True.

    Skip conditions (in order; each returns without writing task_outcomes):
      1. Weekend
      2. Recent successful fire (double-fire guard)
      3. Empty candidate pool (notifies owner via Telegram, no queue write)
      4. Notion unreachable (logs, no queue write)

    On success: writes one proposal row to approval_queue via enqueue, which
    also sends the Telegram preview. Completes the episodic_memory outcome.
    """
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    today_iso = now.date().isoformat()
    logger.info(f"griot_morning_tick: start at {now.isoformat()}")

    # Skip 1: weekend.
    if _is_weekend(now):
        logger.info(f"griot_morning_tick: skip (weekend, weekday={now.weekday()})")
        return

    # Skip 2: double-fire guard.
    if _recently_fired_successfully():
        logger.info("griot_morning_tick: skip (successful fire within DOUBLE_FIRE_GUARD_HOURS)")
        return

    # Now we are committing to real work; open an outcome row.
    outcome_id: Optional[int] = None
    try:
        from episodic_memory import start_task, complete_task
        outcome = start_task(
            crew_name="griot",
            plan_summary=f"Griot L0.5 morning pick at {now.isoformat()}",
        )
        outcome_id = outcome.id
    except Exception as e:
        logger.warning(f"griot_morning_tick: could not start task_outcome ({e}); continuing without it")

    result_summary = "unknown"
    try:
        # Fetch rows.
        try:
            from skills.forge_cli.notion_client import NotionClient
            notion_secret = os.environ.get("NOTION_SECRET") or os.environ.get("NOTION_API_KEY")
            notion = NotionClient(secret=notion_secret)
            rows = _fetch_board_rows(notion)
        except Exception as e:
            result_summary = f"notion_unreachable: {e}"
            logger.error(f"griot_morning_tick: Notion fetch failed: {e}")
            return

        candidates_all, recent_posts = _split_pool(rows, today_iso)

        # Dedup: drop candidates proposed in the last CANDIDATE_DEDUP_DAYS.
        candidates = [c for c in candidates_all if not _candidate_already_proposed(c["notion_id"])]
        dedup_dropped = len(candidates_all) - len(candidates)
        logger.info(
            f"griot_morning_tick: pool candidates={len(candidates_all)} "
            f"after_dedup={len(candidates)} recent_posts={len(recent_posts)}"
        )

        # Skip 3: empty backlog.
        if not candidates:
            result_summary = "skip: empty candidate backlog"
            try:
                from notifier import send_message
                chat_id = os.environ.get("OWNER_TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")
                if chat_id:
                    msg = "Griot: no Ready drafts without a scheduled date. Backlog empty."
                    if dedup_dropped:
                        msg += f" ({dedup_dropped} already proposed in last {CANDIDATE_DEDUP_DAYS} days)"
                    send_message(chat_id, msg)
            except Exception as ne:
                logger.warning(f"griot_morning_tick: empty-backlog notify failed: {ne}")
            return

        # Pick + enqueue.
        top = _pick_top_candidate(candidates, recent_posts)
        if top is None:
            result_summary = "skip: picker returned None"
            return

        payload = {
            "notion_id": top["notion_id"],
            "title": top["title"],
            "platform": top["platform"][0] if top["platform"] else None,
            "arc_phase": top["arc_phase"],
            "arc_priority": top["arc_priority"],
            "total_score": top["total_score"],
            "hook_preview": (top.get("hook") or "")[:280],
            "text": (top.get("draft") or ""),  # full post body for Telegram preview
            "why_chosen": top.get("why_chosen", ""),
            "score": top.get("score"),
        }

        try:
            from approval_queue import enqueue
            row = enqueue(
                crew_name="griot",
                proposal_type="post_candidate",
                payload=payload,
                outcome_id=outcome_id,
            )
            result_summary = f"proposed: {top['title'][:80]} (queue #{row.id})"
            logger.info(f"griot_morning_tick: enqueued {row.id} for {top['title'][:60]}")
        except Exception as e:
            result_summary = f"enqueue_failed: {e}"
            logger.error(f"griot_morning_tick: enqueue failed: {e}")

    finally:
        # Close the outcome row, even on exception.
        if outcome_id is not None:
            try:
                from episodic_memory import complete_task
                complete_task(outcome_id, result_summary=result_summary, total_cost_usd=0.0)
            except Exception as e:
                logger.warning(f"griot_morning_tick: complete_task failed: {e}")


# =============================================================================
# Approval signal recorder
# =============================================================================

def record_content_approval(
    notion_page_id: str,
    attempt_number: int,
    decision: str,
    evergreen: bool,
    platform: str,
    griot_score: Optional[float] = None,
    decided_at=None,
) -> None:
    """Write one row to content_approvals. Non-fatal on DB error.

    Called by the approval handler whenever Boubacar taps approve/reject/skip.
    attempt_number=1 for first submission; increment for revised re-submissions.
    """
    try:
        conn = _pg_conn()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO content_approvals
                (notion_page_id, attempt_number, decision, evergreen,
                 platform, griot_score, decided_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                notion_page_id,
                attempt_number,
                decision,
                evergreen,
                platform,
                griot_score,
                decided_at,
            ),
        )
        conn.commit()
        cur.close()
    except Exception as e:
        logger.warning(f"griot: record_content_approval failed (non-fatal): {e}")
