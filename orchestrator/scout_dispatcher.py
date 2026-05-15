"""
scout_dispatcher.py -- Phase 2 absorb scout heartbeat.

Iterates absorb_scout.ADAPTERS, calls each adapter, de-dupes URLs against
absorb_queue, calls absorb_inbound.enqueue() per new candidate. Updates
scout_state with the new cursor + counters per source.

Gating:
  - Sabbath rule (memory feedback_sabbath_no_work_sunday.md):
    skip Sunday entirely; Saturday runs but skips heavy scrapes.
  - Daytime rule: only fire between 06:00 and 22:00 America/Denver.
  - Per-source auto-mute: when total_phase0_fail / total_enqueued > 0.8
    with total_enqueued >= 25, flip muted=true and skip subsequent ticks.

The mute counters increment in absorb_crew.absorb_tick after each verdict;
this module only reads them.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Optional

import pytz

logger = logging.getLogger("agentsHQ.scout_dispatcher")

TIMEZONE = os.environ.get("GENERIC_TIMEZONE", "America/Denver")
DAYTIME_HOURS = range(6, 22)


def _conn():
    from memory import _pg_conn
    return _pg_conn()


def _now_local() -> datetime:
    return datetime.now(pytz.timezone(TIMEZONE))


def _should_run(now: Optional[datetime] = None) -> tuple[bool, str]:
    now = now or _now_local()
    if now.weekday() == 6:
        return False, "sabbath: sunday is no-work per feedback_sabbath_no_work_sunday.md"
    if now.hour not in DAYTIME_HOURS:
        return False, f"outside daytime window (hour={now.hour})"
    if now.weekday() == 5:
        return True, "saturday: light scrapes only (rss adapters are light)"
    return True, "weekday daytime"


def _load_state(source_key: str) -> dict:
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT cursor, muted, total_enqueued, total_phase0_fail
          FROM scout_state WHERE source = %s
        """,
        (source_key,),
    )
    row = cur.fetchone()
    cur.close()
    if not row:
        return {"cursor": None, "muted": False, "total_enqueued": 0, "total_phase0_fail": 0}
    return {
        "cursor": row[0],
        "muted": bool(row[1]),
        "total_enqueued": int(row[2] or 0),
        "total_phase0_fail": int(row[3] or 0),
    }


def _save_state(source_key: str, new_cursor: Optional[str], enqueued_n: int) -> None:
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO scout_state (source, cursor, last_run_at, last_enqueued_count, total_enqueued)
        VALUES (%s, %s, now(), %s, %s)
        ON CONFLICT (source) DO UPDATE
           SET cursor = COALESCE(EXCLUDED.cursor, scout_state.cursor),
               last_run_at = now(),
               last_enqueued_count = EXCLUDED.last_enqueued_count,
               total_enqueued = scout_state.total_enqueued + EXCLUDED.last_enqueued_count
        """,
        (source_key, new_cursor, enqueued_n, enqueued_n),
    )
    conn.commit()
    cur.close()


def _already_seen(url: str) -> bool:
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM absorb_queue WHERE url = %s LIMIT 1", (url,))
    hit = cur.fetchone() is not None
    cur.close()
    return hit


def scout_tick() -> dict:
    """Heartbeat entry: iterate adapters, enqueue new candidates."""
    ok, reason = _should_run()
    if not ok:
        logger.info(f"scout_dispatcher: skip ({reason})")
        return {"ran": False, "reason": reason}

    from absorb_scout import ADAPTERS
    from absorb_inbound import enqueue

    summary: dict[str, int] = {}
    for key, (source_label, fetcher, arg) in ADAPTERS.items():
        state = _load_state(key)
        if state["muted"]:
            summary[key] = -1
            continue
        try:
            candidates = fetcher(state, arg) or []
        except Exception as e:
            logger.error(f"scout: {key} fetch raised: {e}", exc_info=True)
            summary[key] = 0
            continue

        enqueued = 0
        last_cursor = state.get("cursor")
        for c in candidates:
            url = c.get("url")
            if not url or _already_seen(url):
                continue
            try:
                enqueue(url, source_label, submitted_by=key)
                enqueued += 1
                last_cursor = c.get("cursor_value") or last_cursor
            except Exception as e:
                logger.error(f"scout: {key} enqueue {url} failed: {e}")
        _save_state(key, last_cursor, enqueued)
        summary[key] = enqueued
        logger.info(f"scout: {key} +{enqueued}")
    return {"ran": True, "summary": summary}
