"""
auto_publisher.py - Atlas M7b. Autonomous publish tick.

Heartbeat callback that closes Atlas L3 (Publish loop). Every 5 minutes:

  1. Query Notion Content Board for records where:
       Status = Queued AND Scheduled Date <= today AND Platform in (LinkedIn, X)
  2. For each record, in order:
       a. Flip Status to Publishing in Notion BEFORE the API call.
          This is the idempotency safeguard: if we crash between POST and
          the postSubmissionId write, the next tick sees Status=Publishing
          (not Queued) and skips, preventing a double-post.
       b. Call BlotatoPublisher.publish() to fire the post.
       c. Persist postSubmissionId to Notion's Submission ID field.
       d. Poll until terminal (published or failed or timeout).
       e. On published: flip Status=Posted, write LinkedIn/X Posted URL,
          set Posted Date, write task_outcomes row (Atlas L4 reconcile path).
       f. On failed: flip Status=PublishFailed, write errorMessage to Source
          Note, alert Telegram. Status=PublishFailed blocks the slot from M2
          backfill (audit trail; needs human attention).
       g. On timeout: leave Status=Publishing (next tick will poll the same
          submission), but cap the in-flight time at 24h via TTL check.

Coordination with publish_brief (M1):
  - publish_brief queries Status=Queued AND Scheduled Date=today
  - auto_publisher queries Status=Queued AND Scheduled Date<=today
  - Both will see today's records. publish_brief sends a Telegram brief;
    auto_publisher fires the actual post. This is intentional dual-channel:
    Boubacar sees the brief AND the post lands automatically. After
    auto_publisher flips Status=Publishing, publish_brief no longer sees
    the record (Status changed). No race, no double-publish.

Coordination with griot_scheduler M2 backfill:
  - M2 backfill scans Status=Skipped slots in the yesterday-or-today window
  - PublishFailed records intentionally do NOT get backfilled (they block
    the slot until human attention). Updated in griot_scheduler.py separately.

Built on the Blotato API contract verified end-to-end during M7a smoke test
(2026-04-25 22:01 UTC, LinkedIn 5 sec submit-to-live, X 9 sec).
"""
from __future__ import annotations

import json
import logging
import os
import pathlib
import time
from datetime import date, datetime, timedelta
from typing import Optional

import pytz

logger = logging.getLogger("agentsHQ.auto_publisher")

TIMEZONE = os.environ.get("HEARTBEAT_TIMEZONE", "America/Denver")
CONTENT_DB_ID = os.environ.get("FORGE_CONTENT_DB", "339bcf1a-3029-81d1-8377-dc2f2de13a20")

# Publishing TTL: if a record sits in Status=Publishing longer than this
# without resolving, the next tick promotes it to PublishFailed. Protects
# against orphaned in-flight rows from a process crash during polling.
PUBLISHING_TTL_HOURS = 24

# Default schedule when data/auto_publisher_schedule.json is missing.
_DEFAULT_SCHEDULE = {
    "platform_slots": {
        "LinkedIn": [
            {"slot": 0, "hour": 7, "minute": 0},
            {"slot": 1, "hour": 11, "minute": 0},
            {"slot": 2, "hour": 12, "minute": 0},
        ],
        "X": [
            {"slot": 0, "hour": 7, "minute": 0},
            {"slot": 1, "hour": 11, "minute": 0},
            {"slot": 2, "hour": 14, "minute": 0},
        ],
    },
    "past_due": {"stagger_seconds": 900, "max_per_tick": 4},
    "weekday_policy": {"publish_days": [0, 1, 2, 3, 4, 5], "skip_days": [6]},
}


def _should_hold_for_timely_check(
    content_type: str | None,
    approved_at,
    ttl_days: int = 14,
) -> bool:
    """Return True if this record should be held for a Telegram re-check.

    Evergreen records never expire. Timely records (or records with no Content Type,
    treated as Timely by default) expire after ttl_days days from approved_at.
    """
    if content_type == "Evergreen":
        return False
    if approved_at is None:
        return False
    from datetime import datetime, timezone
    if not hasattr(approved_at, "tzinfo") or approved_at.tzinfo is None:
        approved_at = approved_at.replace(tzinfo=timezone.utc)
    age_days = (datetime.now(timezone.utc) - approved_at).days
    return age_days > ttl_days


def _send_timely_recheck_telegram(record: dict) -> None:
    """Send Telegram re-check for a Timely record past its TTL.

    Boubacar replies 'posted' to confirm still relevant, 'skip' to skip.
    Non-fatal if Telegram send fails.
    """
    try:
        from notifier import send_message
        title = record.get("Title", record.get("id", "unknown"))
        platform = record.get("Platform", "unknown")
        approved_at = record.get("approved_at")
        days_old = "?"
        if approved_at is not None:
            from datetime import datetime, timezone
            if not hasattr(approved_at, "tzinfo") or approved_at.tzinfo is None:
                approved_at = approved_at.replace(tzinfo=timezone.utc)
            days_old = (datetime.now(timezone.utc) - approved_at).days
        chat_id = _telegram_chat_id()
        if chat_id:
            msg = (
                f'Timely post re-check: "{title}" ({platform}) was approved '
                f"{days_old} days ago. Still good to publish?\n"
                f"Reply `posted` to confirm, `skip` to skip."
            )
            send_message(str(chat_id), msg)
            logger.info(f"auto_publisher: sent Timely re-check for {title}")
    except Exception as e:
        logger.warning(f"auto_publisher: Timely re-check Telegram send failed: {e}")


def _load_schedule() -> dict:
    """Read auto_publisher_schedule.json. Search order:
      1. env AUTO_PUBLISHER_SCHEDULE_FILE
      2. data/auto_publisher_schedule.json (machine-local, gitignored)
      3. /app/data/auto_publisher_schedule.json (container path)
      4. orchestrator/auto_publisher_schedule.default.json (committed template,
         used when no machine-local override exists)
      5. _DEFAULT_SCHEDULE constant (last resort if even the template is missing)
    """
    here = pathlib.Path(__file__).parent
    candidates = [
        os.environ.get("AUTO_PUBLISHER_SCHEDULE_FILE"),
        "data/auto_publisher_schedule.json",
        "/app/data/auto_publisher_schedule.json",
        str(here / "auto_publisher_schedule.default.json"),
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
            logger.warning(f"auto_publisher: schedule file {p} unreadable: {e}; trying next candidate")
            continue
    return _DEFAULT_SCHEDULE


# ═════════════════════════════════════════════════════════════════════════════
# Notion helpers (mirror publish_brief.py + griot_scheduler.py shape)
# ═════════════════════════════════════════════════════════════════════════════

def _title(prop):
    arr = prop.get("title") if prop else None
    return arr[0].get("plain_text", "") if arr else ""


def _text(prop):
    arr = prop.get("rich_text") if prop else None
    return "".join(t.get("plain_text", "") for t in arr) if arr else ""


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


def _last_edited_time(page) -> Optional[str]:
    return page.get("last_edited_time")


# ═════════════════════════════════════════════════════════════════════════════
# Account ID lookup
# ═════════════════════════════════════════════════════════════════════════════

def _account_id_for_platform(platform: str) -> Optional[str]:
    """Resolve the Blotato accountId env var for a Notion-side platform name."""
    platform_lc = (platform or "").strip().lower()
    if platform == "LinkedIn":
        return os.environ.get("BLOTATO_LINKEDIN_ACCOUNT_ID")
    if platform == "X":
        return os.environ.get("BLOTATO_X_ACCOUNT_ID")
    if platform == "Facebook":
        return os.environ.get("BLOTATO_FACEBOOK_ACCOUNT_ID")
    if platform == "Instagram":
        return os.environ.get("BLOTATO_IG_ACCOUNT_ID") or os.environ.get("BLOTATO_INSTAGRAM_ACCOUNT_ID")
    if platform == "TikTok":
        return os.environ.get("BLOTATO_TIKTOK_ACCOUNT_ID")
    if platform == "Threads":
        return os.environ.get("BLOTATO_THREADS_ACCOUNT_ID")
    if platform == "youtube_shorts" or platform_lc == "youtube_shorts":
        return os.environ.get("BLOTATO_YT_SHORTS_ACCOUNT_ID", "")
    if platform == "YouTube" or platform_lc.startswith("youtube"):
        if "catalyst" in platform_lc:
            return os.environ.get("BLOTATO_YT_CATALYST_ACCOUNT_ID")
        return (
            os.environ.get("BLOTATO_YT_BAOBAB_ACCOUNT_ID")
            or os.environ.get("BLOTATO_YOUTUBE_ACCOUNT_ID")
        )
    if platform == "Pinterest":
        return os.environ.get("BLOTATO_PINTEREST_ACCOUNT_ID")
    if platform == "Bluesky":
        return os.environ.get("BLOTATO_BLUESKY_ACCOUNT_ID")
    return None


# ═════════════════════════════════════════════════════════════════════════════
# Fetch eligible records
# ═════════════════════════════════════════════════════════════════════════════

def _slot_index_for_platform_today(
    platform: str,
    today_iso: str,
    already_published_today_count: int,
) -> int:
    """Return the slot index for the next post of this platform today.

    `already_published_today_count` is how many of this platform's posts
    have already gone Posted (or Publishing) today. The next post claims
    the next slot (0-indexed). Used to pick the right time-of-day for
    the post that's about to fire.
    """
    return already_published_today_count


def _slot_time_today(schedule: dict, platform: str, slot_index: int, today_dt: datetime) -> Optional[datetime]:
    """Return the localized datetime when slot N for `platform` should fire today.
    Returns None if the platform has no slot for that index.
    """
    slots = schedule.get("platform_slots", {}).get(platform, [])
    if slot_index >= len(slots):
        return None
    s = slots[slot_index]
    return today_dt.replace(hour=int(s["hour"]), minute=int(s["minute"]), second=0, microsecond=0)


def _fetch_due_queued(notion, today_iso: str, now_local: Optional[datetime] = None,
                       schedule: Optional[dict] = None) -> list:
    """Return Content Board records where:
      Status = Queued
      Scheduled Date <= today
      Platform has an account_id configured

    Time-of-day gate (M7b time slots):
      - Past-due records (Scheduled Date < today): always included
      - Today records: included only if the slot's preferred fire-time
        for this platform has been reached AND the slot is not already taken
        by an earlier same-platform post today.

    `now_local` and `schedule` are injectable for tests; otherwise computed
    from current time + the auto_publisher_schedule.json file.
    """
    if schedule is None:
        schedule = _load_schedule()
    if now_local is None:
        tz = pytz.timezone(TIMEZONE)
        now_local = datetime.now(tz)

    posts = notion.query_database(CONTENT_DB_ID, filter_obj=None)

    # Count how many records per (platform, today) have already moved past
    # Queued (i.e. Publishing, Posted, or PublishFailed). Used to decide
    # which slot today's next record claims.
    already_today = {}  # platform -> count
    for p in posts:
        props = p.get("properties", {})
        st = _select(props.get("Status", {}))
        if st not in ("Publishing", "Published", "PublishFailed"):
            continue
        sd = _date_start(props.get("Scheduled Date", {}))
        if not sd or sd[:10] != today_iso:
            continue
        for pf in _multi(props.get("Platform", {})):
            if _account_id_for_platform(pf) is None:
                continue
            already_today[pf] = already_today.get(pf, 0) + 1

    due = []
    for p in posts:
        props = p.get("properties", {})
        if _select(props.get("Status", {})) != "Queued":
            continue
        sd = _date_start(props.get("Scheduled Date", {}))
        if not sd:
            continue
        sd_iso = sd[:10]
        if sd_iso > today_iso:
            continue  # future, not due yet
        platforms = _multi(props.get("Platform", {}))
        for pf in platforms:
            if _account_id_for_platform(pf) is None:
                continue

            # Time-of-day gate (only for today's records; past-due always fire)
            if sd_iso == today_iso:
                slot_idx = _slot_index_for_platform_today(pf, today_iso, already_today.get(pf, 0))
                slot_time = _slot_time_today(schedule, pf, slot_idx, now_local)
                if slot_time is None:
                    # No slot defined for this index; skip (over budget for the day)
                    continue
                if now_local < slot_time:
                    continue  # slot time hasn't arrived yet

            due.append({
                "notion_id": p["id"],
                "title": _title(props.get("Title", {})),
                "draft": _text(props.get("Draft", {})),
                "hook": _text(props.get("Hook", {})),
                "platform": pf,
                "scheduled_date": sd_iso,
                "is_past_due": sd_iso < today_iso,
            })
            break  # one publish per record (first matching platform)
    # Stable order: oldest scheduled first, then platform alpha.
    due.sort(key=lambda r: (r["scheduled_date"], r["platform"], r["notion_id"]))
    return due


def _fetch_stale_publishing(notion, now_utc: datetime) -> list:
    """Return Content Board records stuck in Status=Publishing for >TTL.

    Used at the start of each tick to promote orphaned in-flight rows to
    PublishFailed so they no longer block their slot indefinitely. Runs
    BEFORE _fetch_due_queued to clean up the queue first.
    """
    cutoff = now_utc - timedelta(hours=PUBLISHING_TTL_HOURS)
    posts = notion.query_database(CONTENT_DB_ID, filter_obj=None)
    stale = []
    for p in posts:
        props = p.get("properties", {})
        if _select(props.get("Status", {})) != "Publishing":
            continue
        last_edit = _last_edited_time(p)
        if not last_edit:
            continue
        try:
            last_edit_dt = datetime.fromisoformat(last_edit.replace("Z", "+00:00"))
        except Exception:
            continue
        if last_edit_dt < cutoff:
            stale.append({
                "notion_id": p["id"],
                "title": _title(props.get("Title", {})),
                "submission_id": _text(props.get("Submission ID", {})),
                "last_edited": last_edit,
            })
    return stale


# ═════════════════════════════════════════════════════════════════════════════
# Notion writes (each one self-contained so a failure mid-flow flips a
# specific Status without leaking partial state)
# ═════════════════════════════════════════════════════════════════════════════

def _flip_to_publishing(notion, notion_id: str) -> None:
    """Status=Queued -> Publishing. Idempotency safeguard: must succeed
    BEFORE the Blotato POST call.
    """
    notion.update_page(notion_id, {"Status": {"select": {"name": "Publishing"}}})


def _persist_submission_id(notion, notion_id: str, submission_id: str) -> None:
    """Write postSubmissionId to Notion's Submission ID field.

    Called immediately after a successful Blotato POST. If this write fails
    we log and continue to poll; the next tick will see Status=Publishing
    with no Submission ID and promote to PublishFailed via the TTL path
    (24h orphan cleanup). Better than re-POSTing.
    """
    notion.update_page(notion_id, {
        "Submission ID": {"rich_text": [{"text": {"content": submission_id}}]}
    })


def _flip_to_posted(
    notion, notion_id: str, platform: str, public_url: str, posted_at_iso: str
) -> None:
    """Terminal success: Status=Posted, write platform-specific Posted URL,
    set Posted Date.
    """
    url_field = "LinkedIn Posted URL" if platform == "LinkedIn" else "X Posted URL"
    properties = {
        "Status": {"select": {"name": "Published"}},
        url_field: {"url": public_url},
        "Posted Date": {"date": {"start": posted_at_iso}},
    }
    notion.update_page(notion_id, properties)


def _flip_to_publish_failed(notion, notion_id: str, error_message: str) -> None:
    """Terminal failure: Status=PublishFailed, append errorMessage to
    Source Note. Slot stays blocked (M2 backfill ignores PublishFailed).
    """
    truncated = (error_message or "")[:1500]
    properties = {
        "Status": {"select": {"name": "PublishFailed"}},
        "Source Note": {"rich_text": [{"text": {"content": f"PublishFailed: {truncated}"}}]},
    }
    notion.update_page(notion_id, properties)


# ═════════════════════════════════════════════════════════════════════════════
# Telegram alert helpers
# ═════════════════════════════════════════════════════════════════════════════

def _telegram_chat_id() -> Optional[str]:
    return os.environ.get("OWNER_TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")


def _alert_posted(title: str, platform: str, public_url: str) -> None:
    chat_id = _telegram_chat_id()
    if not chat_id:
        return
    try:
        from notifier import send_message
        send_message(
            str(chat_id),
            f"Posted (auto): {platform}\n{title[:80]}\n{public_url}",
        )
    except Exception as e:
        logger.warning(f"auto_publisher: posted Telegram notify failed: {e}")


def _alert_failed(title: str, platform: str, error_message: str) -> None:
    chat_id = _telegram_chat_id()
    if not chat_id:
        return
    try:
        from notifier import send_message
        send_message(
            str(chat_id),
            f"Publish FAILED: {platform}\n{title[:80]}\nError: {error_message[:300]}\n"
            f"Status set to PublishFailed; slot blocked until human acts.",
        )
    except Exception as e:
        logger.warning(f"auto_publisher: failed-alert Telegram notify failed: {e}")


# ═════════════════════════════════════════════════════════════════════════════
# Outcome row (Atlas L4 reconcile path)
# ═════════════════════════════════════════════════════════════════════════════

def _write_outcome(crew_name: str, summary: str, success: bool) -> None:
    """Mirror the L4 path used by handlers_approvals.handle_publish_reply.
    Failure-soft: if episodic_memory unreachable, log and continue.
    """
    try:
        from episodic_memory import start_task, complete_task
        outcome = start_task(crew_name=crew_name, plan_summary=summary)
        complete_task(
            outcome.id,
            result_summary=("success" if success else "failed"),
            total_cost_usd=0.0,
        )
    except Exception as e:
        logger.warning(f"auto_publisher: episodic_memory write failed: {e}")


# ═════════════════════════════════════════════════════════════════════════════
# Main wake callback
# ═════════════════════════════════════════════════════════════════════════════

def auto_publisher_tick() -> None:
    """Heartbeat callback. Fires every 5 minutes. 7-day cadence (the
    publishing schedule itself controls when to fire; this tick just executes
    whatever is due). Per-crew gate auto_publisher.enabled controls whether
    this is allowed to act.

    Called by heartbeat._fire after the kill-switch + per-crew checks pass.
    """
    tz = pytz.timezone(TIMEZONE)
    now_local = datetime.now(tz)
    now_utc = datetime.now(pytz.UTC)
    today_iso = now_local.date().isoformat()

    # Open a Notion client.
    try:
        from skills.forge_cli.notion_client import NotionClient
        notion_secret = (
            os.environ.get("NOTION_SECRET")
            or os.environ.get("NOTION_API_KEY")
            or os.environ.get("NOTION_TOKEN")
        )
        notion = NotionClient(secret=notion_secret)
    except Exception as e:
        logger.error(f"auto_publisher: cannot open Notion client: {e}")
        return

    # ─────────────────────────────────────────────────────────────────────
    # Stale-Publishing cleanup (TTL path). Promote orphaned in-flight rows
    # to PublishFailed so their slots stop blocking the queue.
    # ─────────────────────────────────────────────────────────────────────
    try:
        stale = _fetch_stale_publishing(notion, now_utc)
    except Exception as e:
        logger.warning(f"auto_publisher: stale-Publishing scan failed: {e}")
        stale = []

    for row in stale:
        try:
            _flip_to_publish_failed(
                notion,
                row["notion_id"],
                f"Orphaned in Publishing for >{PUBLISHING_TTL_HOURS}h "
                f"(submission_id={row['submission_id'] or 'unknown'}). "
                f"Last edited {row['last_edited']}. Promoted by TTL cleanup.",
            )
            _alert_failed(row["title"], "(unknown)", f"Orphaned in Publishing >{PUBLISHING_TTL_HOURS}h")
            _write_outcome("auto_publisher", f"TTL-orphan {row['title'][:60]}", success=False)
            logger.warning(
                f"auto_publisher: promoted stale Publishing row {row['notion_id']} "
                f"({row['title'][:60]}) to PublishFailed"
            )
        except Exception as e:
            logger.error(f"auto_publisher: stale cleanup failed for {row['notion_id']}: {e}")

    # ─────────────────────────────────────────────────────────────────────
    # Main publish loop.
    # ─────────────────────────────────────────────────────────────────────
    schedule = _load_schedule()

    # Weekday policy: skip publishing on disallowed days (default: skip Sunday).
    # Past-due records still fire (audit trail must catch up); only today-records
    # get gated by the weekday skip rule.
    weekday = now_local.weekday()
    skip_today_records = weekday in schedule.get("weekday_policy", {}).get("skip_days", [])

    try:
        due = _fetch_due_queued(notion, today_iso, now_local=now_local, schedule=schedule)
    except Exception as e:
        logger.error(f"auto_publisher: due-fetch failed: {e}")
        return

    # Apply weekday skip to TODAY's records only; past-due always fire.
    if skip_today_records:
        before = len(due)
        due = [r for r in due if r["is_past_due"]]
        if before != len(due):
            logger.info(
                f"auto_publisher: weekday {now_local.strftime('%A')} is in skip_days; "
                f"deferred {before - len(due)} today-records"
            )

    # Past-due stagger: cap how many past-dues fire per tick. Heartbeat fires
    # every 5 min so multiple ticks drain the backlog over time without bursting.
    past_due = [r for r in due if r["is_past_due"]]
    today_records = [r for r in due if not r["is_past_due"]]
    if past_due:
        max_pd = int(schedule.get("past_due", {}).get("max_per_tick", 4))
        if len(past_due) > max_pd:
            logger.info(
                f"auto_publisher: {len(past_due)} past-due records; "
                f"capping this tick at {max_pd} (rest fire on next tick)"
            )
            past_due = past_due[:max_pd]
        due = past_due + today_records
    else:
        due = today_records

    # Strict single-fire rate limit: cap the number of published posts per tick (default: 1)
    # This guarantees that under no circumstances do multiple platform posts fire in the
    # same 5-minute heartbeat loop, spreading out any concurrent or backlog posts.
    max_posts = int(schedule.get("past_due", {}).get("max_posts_per_tick", 1))
    if len(due) > max_posts:
        logger.info(
            f"auto_publisher: capping due list from {len(due)} to {max_posts} "
            f"to guarantee strictly staggered, one-at-a-time execution."
        )
        due = due[:max_posts]

    if not due:
        logger.debug("auto_publisher: no due records (after time-gate + weekday-skip + stagger)")
        return

    logger.info(f"auto_publisher: {len(due)} due record(s) to publish this tick")

    # Open the publisher once, reuse the httpx client across records.
    try:
        from blotato_publisher import BlotatoPublisher
        publisher = BlotatoPublisher()
    except Exception as e:
        logger.error(f"auto_publisher: BlotatoPublisher init failed: {e}")
        return

    posted_count = 0
    failed_count = 0
    timeout_count = 0

    try:
        for rec in due:
            notion_id = rec["notion_id"]
            title = rec["title"]
            platform = rec["platform"]
            text = rec["draft"] or rec["hook"]

            if not text or not text.strip():
                logger.warning(
                    f"auto_publisher: record {notion_id} ({title[:50]}) has no Draft "
                    f"or Hook text; flipping to PublishFailed"
                )
                try:
                    _flip_to_publish_failed(notion, notion_id, "No Draft or Hook text in Notion record")
                    _alert_failed(title, platform, "No Draft or Hook text")
                    _write_outcome("auto_publisher", f"empty-text {title[:60]}", success=False)
                    failed_count += 1
                except Exception as e:
                    logger.error(f"auto_publisher: empty-text flip failed for {notion_id}: {e}")
                continue

            account_id = _account_id_for_platform(platform)
            if not account_id:
                logger.warning(
                    f"auto_publisher: no Blotato account ID configured for "
                    f"platform {platform!r}, skipping {notion_id}"
                )
                continue

            # C13: Evergreen/Timely TTL gate
            content_type = rec.get("content_type")
            approved_at = rec.get("approved_at")
            ttl_days = int(os.environ.get("TIMELY_TTL_DAYS", "14"))
            if _should_hold_for_timely_check(content_type, approved_at, ttl_days):
                logger.info(
                    f"auto_publisher: holding {notion_id} for Timely re-check "
                    f"(approved_at={approved_at}, ttl={ttl_days}d)"
                )
                _send_timely_recheck_telegram({
                    "Title": title,
                    "Platform": platform,
                    "approved_at": approved_at,
                })
                continue

            # Step 1 (idempotency safeguard): flip Status to Publishing
            # BEFORE the Blotato POST. If this fails, we do NOT POST; the
            # record stays Queued and the next tick retries.
            try:
                _flip_to_publishing(notion, notion_id)
            except Exception as e:
                logger.error(
                    f"auto_publisher: pre-POST Status=Publishing flip failed "
                    f"for {notion_id}: {e}"
                )
                continue

            # Step 2: Blotato POST.
            submission_id = None
            try:
                submission_id = publisher.publish(
                    text=text,
                    account_id=account_id,
                    platform=platform,
                )
            except Exception as e:
                logger.error(
                    f"auto_publisher: Blotato POST failed for {notion_id} ({platform}): {e}"
                )
                try:
                    _flip_to_publish_failed(notion, notion_id, f"Blotato POST error: {e}")
                    _alert_failed(title, platform, str(e))
                    _write_outcome("auto_publisher", f"post-fail {title[:60]}", success=False)
                except Exception as e2:
                    logger.error(f"auto_publisher: PublishFailed flip after POST error failed: {e2}")
                failed_count += 1
                continue

            # Step 3: persist postSubmissionId immediately (idempotency).
            try:
                _persist_submission_id(notion, notion_id, submission_id)
            except Exception as e:
                # Logged but non-fatal: poll still proceeds. TTL cleanup will
                # promote to PublishFailed later if poll itself crashes.
                logger.warning(
                    f"auto_publisher: Submission ID persist failed for {notion_id}: {e}"
                )

            # Step 4: poll until terminal.
            result = publisher.poll_until_terminal(submission_id)

            # Step 5: terminal-state Notion write.
            if result.ok:
                posted_at_iso = datetime.now(pytz.UTC).isoformat()
                try:
                    _flip_to_posted(
                        notion, notion_id, platform, result.public_url or "", posted_at_iso
                    )
                    _alert_posted(title, platform, result.public_url or "")
                    _write_outcome("auto_publisher", f"posted {platform} {title[:50]}", success=True)
                    posted_count += 1
                except Exception as e:
                    logger.error(
                        f"auto_publisher: Posted-flip failed for {notion_id}: {e}. "
                        f"Post is LIVE on {platform} at {result.public_url} but Notion "
                        f"row stuck in Publishing. TTL cleanup will eventually flip."
                    )
            elif result.status == "failed":
                err = result.error_message or "unknown failure"
                try:
                    _flip_to_publish_failed(notion, notion_id, f"Blotato status=failed: {err}")
                    _alert_failed(title, platform, err)
                    _write_outcome("auto_publisher", f"failed {title[:60]}", success=False)
                    failed_count += 1
                except Exception as e:
                    logger.error(f"auto_publisher: PublishFailed flip after Blotato fail: {e}")
            else:
                # Timeout. Leave Status=Publishing with submission_id persisted.
                # Next tick's stale-Publishing cleanup will catch it after TTL.
                logger.warning(
                    f"auto_publisher: poll timeout for {notion_id} "
                    f"(submission_id={submission_id}); leaving Status=Publishing "
                    f"for next tick or TTL"
                )
                timeout_count += 1
    finally:
        publisher.close()

    logger.info(
        f"auto_publisher: tick done posted={posted_count} failed={failed_count} "
        f"timeout={timeout_count} stale_promoted={len(stale)}"
    )
