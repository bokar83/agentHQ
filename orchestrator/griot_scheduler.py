"""
griot_scheduler.py - Phase 3.75: schedule approved Griot candidates.

Runs on a 5-minute heartbeat wake. For each approval_queue row that is:
  - crew_name = 'griot'
  - proposal_type = 'post_candidate'
  - status = 'approved'
  - not yet scheduled (tracked in scheduler_runs table or via Notion status)

...the scheduler picks the next open slot for the post's platform and writes
Scheduled Date + status=Queued back to the Content Board. Then marks the
approval row as scheduled (payload.scheduled_date) so we don't reschedule it.

Slot rules:
  LinkedIn: Tuesday + Thursday only
  X:        every weekday

Occupancy: one post per (platform, date). Walk forward from tomorrow (or
Monday if tomorrow is weekend) until the first open slot for the platform.

Zero LLM calls. Pure deterministic scheduling.
"""
from __future__ import annotations

import logging
import os
from datetime import date, datetime, timedelta
from typing import Optional

import pytz

logger = logging.getLogger("agentsHQ.griot_scheduler")

TIMEZONE = os.environ.get("HEARTBEAT_TIMEZONE", "America/Denver")
CONTENT_DB_ID = os.environ.get("FORGE_CONTENT_DB", "339bcf1a-3029-81d1-8377-dc2f2de13a20")

# How far forward to look for an open slot. 30 days is plenty for the
# current backlog. If the backlog grows past a month, bump this.
MAX_SCHEDULE_HORIZON_DAYS = 30

# Weekday cadence (updated 2026-04-25 in M7b):
# Old rule: LinkedIn Tue+Thu only, X every weekday. That was a manual-author
# cadence. With M7b auto-publisher live, Boubacar wants daily Mon-Sat for
# both platforms; skip Sunday only.
LINKEDIN_WEEKDAYS = {0, 1, 2, 3, 4, 5}  # Mon-Sat
X_WEEKDAYS = {0, 1, 2, 3, 4, 5}          # Mon-Sat


# ═════════════════════════════════════════════════════════════════════════════
# Notion helpers (identical shape to griot.py)
# ═════════════════════════════════════════════════════════════════════════════

def _title(prop):
    arr = prop.get("title") if prop else None
    return arr[0].get("plain_text", "") if arr else ""


# ═════════════════════════════════════════════════════════════════════════════
# Atlas M2: backfill of recently-Skipped slots.
# When Boubacar replies 'skip' to a publish brief (M1), the Notion record
# flips to Status=Skipped but its Scheduled Date stays. That date+platform
# slot is then "burned" until griot_scheduler_tick reclaims it. M2 makes the
# 5-min scheduler scan for Skipped rows in a yesterday-or-today window and
# backfill the slot with an approved candidate from the queue.
# ═════════════════════════════════════════════════════════════════════════════

def _find_recent_skipped_slots(notion, today_iso: str) -> list:
    """Return a list of dicts describing Skipped Notion rows whose Scheduled
    Date is yesterday or today. Each dict has: platform, date_iso, notion_id, title.

    Used by griot_scheduler_tick to identify slots eligible for backfill.
    """
    yesterday_iso = (date.fromisoformat(today_iso) - timedelta(days=1)).isoformat()
    eligible = {yesterday_iso, today_iso}

    posts = notion.query_database(CONTENT_DB_ID, filter_obj=None)
    out = []
    for p in posts:
        props = p.get("properties", {})
        if _select(props.get("Status", {})) != "Skipped":
            continue
        sd = _date_start(props.get("Scheduled Date", {}))
        if not sd or sd[:10] not in eligible:
            continue
        for pf in _multi(props.get("Platform", {})):
            if pf in ("LinkedIn", "X"):
                out.append({
                    "platform": pf,
                    "date_iso": sd[:10],
                    "notion_id": p["id"],
                    "title": _title(props.get("Title", {})),
                })
                break  # match the forward-scheduling pattern: one slot per row
    # Stable order helps tests + log readability.
    out.sort(key=lambda s: (s["date_iso"], s["platform"]))
    return out


def _pick_candidate_for_platform(approvals: list, platform: str):
    """Return the (queue_id, payload) of the oldest approval whose payload
    platform matches, or None if no candidate matches. approvals is the
    list returned by _fetch_unscheduled_approvals (already sorted oldest-first
    by ts_decided).
    """
    for queue_id, payload in approvals:
        if payload.get("platform") == platform:
            return (queue_id, payload)
    return None


def _select(prop):
    if not prop:
        return None
    sel = prop.get("select") or prop.get("status")
    return sel.get("name") if sel else None


def _multi(prop):
    arr = prop.get("multi_select") if prop else None
    return [x.get("name") for x in arr] if arr else []


def _date_start(prop):
    d = prop.get("date") if prop else None
    return d.get("start") if d else None


# ═════════════════════════════════════════════════════════════════════════════
# Slot occupancy + picking
# ═════════════════════════════════════════════════════════════════════════════

def _fetch_occupancy(notion) -> dict:
    """Return a set-like dict mapping (platform, date_iso) -> True for every
    existing Queued / Ready / Posted / Publishing / PublishFailed record with
    a Scheduled Date.

    Atlas M7b note: Publishing means in-flight via Blotato API; PublishFailed
    means terminal failure that needs human attention. Both block the slot
    from new scheduling.
    """
    posts = notion.query_database(CONTENT_DB_ID, filter_obj=None)
    occupied = {}
    for p in posts:
        props = p.get("properties", {})
        status = _select(props.get("Status", {}))
        if status not in ("Queued", "Ready", "Published", "Publishing", "PublishFailed"):
            continue
        sd = _date_start(props.get("Scheduled Date", {}))
        if not sd:
            continue
        for pf in _multi(props.get("Platform", {})):
            if pf in ("LinkedIn", "X"):
                occupied[(pf, sd[:10])] = True
    return occupied


def _pick_next_slot(platform: str, occupied: dict, start: date) -> Optional[date]:
    """Walk forward from `start` (inclusive) and return the first date that is:
      - a valid weekday for this platform
      - not already occupied by a post on this platform
    Returns None if no slot found within MAX_SCHEDULE_HORIZON_DAYS.
    """
    if platform == "LinkedIn":
        allowed = LINKEDIN_WEEKDAYS
    elif platform == "X":
        allowed = X_WEEKDAYS
    else:
        logger.warning(f"_pick_next_slot: unknown platform {platform!r}")
        return None

    for i in range(MAX_SCHEDULE_HORIZON_DAYS):
        d = start + timedelta(days=i)
        if d.weekday() not in allowed:
            continue
        if (platform, d.isoformat()) in occupied:
            continue
        return d
    return None


# ═════════════════════════════════════════════════════════════════════════════
# Approval queue scan
# ═════════════════════════════════════════════════════════════════════════════

def _fetch_unscheduled_approvals() -> list:
    """Return approval_queue rows where:
      crew_name = 'griot'
      proposal_type = 'post_candidate'
      status = 'approved'
      payload does not yet contain 'scheduled_date' (our marker for done)
    """
    try:
        from memory import _pg_conn
    except ImportError:
        logger.error("griot_scheduler: memory._pg_conn unavailable")
        return []

    conn = _pg_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, payload
            FROM approval_queue
            WHERE crew_name = 'griot'
              AND proposal_type = 'post_candidate'
              AND status = 'approved'
              AND (payload->>'scheduled_date' IS NULL)
            ORDER BY ts_decided ASC
            """
        )
        rows = cur.fetchall()
        cur.close()
    finally:
        conn.close()
    return [(r[0], r[1]) for r in rows]


def _mark_scheduled(queue_id: int, scheduled_date_iso: str) -> None:
    """Write the scheduled date into the approval_queue row's payload so we
    don't process it again. Uses jsonb_set to preserve existing payload keys.
    """
    try:
        from memory import _pg_conn
    except ImportError:
        return

    conn = _pg_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE approval_queue
               SET payload = jsonb_set(
                     payload,
                     '{scheduled_date}',
                     to_jsonb(%s::text),
                     true
                   )
             WHERE id = %s
            """,
            (scheduled_date_iso, queue_id),
        )
        conn.commit()
        cur.close()
    finally:
        conn.close()


# ═════════════════════════════════════════════════════════════════════════════
# Notion update: Scheduled Date + Status
# ═════════════════════════════════════════════════════════════════════════════

def _update_notion_schedule(notion, notion_id: str, scheduled_date_iso: str) -> dict:
    """Set Scheduled Date + Status=Queued on the Content Board record.

    This Content Board stores Status as a `select` property (verified via
    get_database_schema on 2026-04-24). If it is ever migrated to a Notion
    `status` property, update this wrapper accordingly.
    """
    properties = {
        "Scheduled Date": {"date": {"start": scheduled_date_iso}},
        "Status": {"select": {"name": "Queued"}},
    }
    return notion.update_page(notion_id, properties)


# ═════════════════════════════════════════════════════════════════════════════
# Main wake callback
# ═════════════════════════════════════════════════════════════════════════════

def griot_scheduler_tick() -> None:
    """Heartbeat callback. Process all approved unscheduled Griot candidates.

    Fires every 5 minutes. Idempotent: already-scheduled rows skip via the
    payload.scheduled_date marker.
    """
    approvals = _fetch_unscheduled_approvals()
    if not approvals:
        logger.debug("griot_scheduler_tick: nothing to schedule")
        return

    logger.info(f"griot_scheduler_tick: {len(approvals)} approved candidates to schedule")

    # Open a Notion client once, reuse across multiple approvals.
    try:
        from skills.forge_cli.notion_client import NotionClient
        notion_secret = os.environ.get("NOTION_SECRET") or os.environ.get("NOTION_API_KEY")
        notion = NotionClient(secret=notion_secret)
    except Exception as e:
        logger.error(f"griot_scheduler_tick: cannot open Notion client: {e}")
        return

    try:
        occupied = _fetch_occupancy(notion)
    except Exception as e:
        logger.error(f"griot_scheduler_tick: occupancy fetch failed: {e}")
        return

    tz = pytz.timezone(TIMEZONE)
    today_local = datetime.now(tz).date()
    today_iso = today_local.isoformat()
    start_from = today_local + timedelta(days=1)  # start tomorrow for forward-scheduling

    # ─────────────────────────────────────────────────────────────────────
    # Atlas M2: backfill phase. Consume approvals to fill yesterday-or-today
    # Skipped slots BEFORE the forward-scheduling loop runs. Backfilled
    # candidates are removed from `approvals` so they're not double-scheduled.
    # ─────────────────────────────────────────────────────────────────────
    approvals = list(approvals)  # mutable copy for backfill consumption
    backfilled_count = 0
    try:
        skipped_slots = _find_recent_skipped_slots(notion, today_iso)
    except Exception as e:
        logger.warning(f"griot_scheduler_tick: skipped-slot scan failed: {e}")
        skipped_slots = []

    for slot in skipped_slots:
        key = (slot["platform"], slot["date_iso"])
        if key in occupied:
            # Slot was already filled (e.g., previous tick backfilled it,
            # or another Queued/Posted row sits on the same date+platform).
            continue
        pick = _pick_candidate_for_platform(approvals, slot["platform"])
        if pick is None:
            logger.info(
                f"griot_scheduler_tick: no candidate available to backfill "
                f"Skipped slot {slot['platform']} {slot['date_iso']}"
            )
            continue
        queue_id, payload = pick
        cand_notion_id = payload.get("notion_id")
        cand_title = payload.get("title", "")
        if not cand_notion_id:
            logger.warning(
                f"griot_scheduler_tick: queue #{queue_id} missing notion_id, "
                f"cannot backfill {slot['platform']} {slot['date_iso']}"
            )
            continue
        try:
            _update_notion_schedule(notion, cand_notion_id, slot["date_iso"])
            occupied[key] = True
            _mark_scheduled(queue_id, slot["date_iso"])
            approvals.remove((queue_id, payload))  # consume from forward loop
            backfilled_count += 1
            logger.info(
                f"griot_scheduler_tick: backfilled {slot['platform']} {slot['date_iso']} "
                f"with queue #{queue_id} '{cand_title[:50]}' "
                f"(replacing Skipped '{slot['title'][:50]}')"
            )
            try:
                from notifier import send_message
                chat_id = os.environ.get("OWNER_TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")
                if chat_id:
                    send_message(
                        str(chat_id),
                        f"Backfilled {slot['date_iso']} ({slot['platform']}): "
                        f"'{cand_title[:60]}' (replacing Skipped: '{slot['title'][:60]}')",
                    )
            except Exception as ne:
                logger.warning(f"griot_scheduler_tick: backfill Telegram notify failed: {ne}")
        except Exception as e:
            logger.error(
                f"griot_scheduler_tick: backfill of {slot['platform']} {slot['date_iso']} "
                f"failed: {e}", exc_info=True,
            )

    if backfilled_count:
        logger.info(f"griot_scheduler_tick: backfilled {backfilled_count} Skipped slot(s)")

    scheduled_count = 0
    failed_count = 0
    for queue_id, payload in approvals:
        try:
            platform = payload.get("platform")
            notion_id = payload.get("notion_id")
            title = payload.get("title", "")

            if platform not in ("LinkedIn", "X"):
                logger.warning(f"griot_scheduler_tick: queue #{queue_id} has unknown platform {platform!r}, skipping")
                continue
            if not notion_id:
                logger.warning(f"griot_scheduler_tick: queue #{queue_id} missing notion_id, skipping")
                continue

            slot = _pick_next_slot(platform, occupied, start_from)
            if slot is None:
                logger.error(f"griot_scheduler_tick: queue #{queue_id} no open slot for {platform} within {MAX_SCHEDULE_HORIZON_DAYS} days")
                failed_count += 1
                continue

            slot_iso = slot.isoformat()

            # Update Notion first (the authoritative source of truth).
            _update_notion_schedule(notion, notion_id, slot_iso)
            logger.info(
                f"griot_scheduler_tick: queue #{queue_id} scheduled "
                f"{platform} '{title[:50]}' -> {slot_iso} ({slot.strftime('%A')})"
            )

            # Reserve the slot in-memory so the next approval in this batch
            # doesn't claim the same date.
            occupied[(platform, slot_iso)] = True

            # Mark the approval row as done.
            _mark_scheduled(queue_id, slot_iso)

            # Telegram confirmation to owner.
            try:
                from notifier import send_message
                chat_id = os.environ.get("OWNER_TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")
                if chat_id:
                    send_message(
                        str(chat_id),
                        f"Scheduled: '{title[:60]}'\n"
                        f"Platform: {platform}\n"
                        f"Date: {slot_iso} ({slot.strftime('%A')})\n"
                        f"Status: Queued",
                    )
            except Exception as ne:
                logger.warning(f"griot_scheduler_tick: Telegram notify failed for queue #{queue_id}: {ne}")

            scheduled_count += 1

        except Exception as e:
            failed_count += 1
            logger.error(f"griot_scheduler_tick: queue #{queue_id} scheduling failed: {e}", exc_info=True)

    logger.info(
        f"griot_scheduler_tick: done scheduled={scheduled_count} failed={failed_count} "
        f"total_pending_before={len(approvals)}"
    )
