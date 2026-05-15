"""
absorb_digest.py -- Phase 3 daily digest for absorb_crew.

Once-a-day Telegram digest (07:00 America/Denver, M-F only) summarizing
the prior 24 hours of absorb_queue activity:

  - PROCEED verdicts grouped by tier (big-surface already alerted via
    approval_queue at the time; small-tier flagged here)
  - ARCHIVE-AND-NOTE counts by source
  - DONT_PROCEED counts
  - failed rows (worth investigating)
  - top 3 noisiest scout sources (most candidates, lowest PROCEED rate)

Auto-spawn coding subagents on small-tier PROCEED is deferred to Phase 4
pending a Hermes write-boundary expansion (skills/ is currently forbidden;
auto-PR for `enhance skills/X` follow-ups requires that). Tracking task:
docs/roadmap/compass.md (Hermes M7+).
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import pytz

logger = logging.getLogger("agentsHQ.absorb_digest")

TIMEZONE = os.environ.get("GENERIC_TIMEZONE", "America/Denver")
DIGEST_WINDOW_HOURS = 24
SMALL_TIER = ("enhance", "extend", "new_tool")
BIG_TIER = ("new_skill", "new_agent", "satellite", "replace_existing")


def _conn():
    from memory import _pg_conn
    return _pg_conn()


def _now_local() -> datetime:
    return datetime.now(pytz.timezone(TIMEZONE))


def _is_sunday() -> bool:
    return _now_local().weekday() == 6


def _summarize_window() -> dict:
    """Pull aggregate counts + lists from absorb_queue for last DIGEST_WINDOW_HOURS."""
    conn = _conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT verdict, placement, COUNT(*) AS n
          FROM absorb_queue
         WHERE ts_processed > now() - (%s || ' hours')::interval
           AND status = 'done'
         GROUP BY verdict, placement
         ORDER BY n DESC
        """,
        (str(DIGEST_WINDOW_HOURS),),
    )
    breakdown = [{"verdict": r[0], "placement": r[1], "n": int(r[2])} for r in cur.fetchall()]

    cur.execute(
        """
        SELECT id, source, url, placement, dossier
          FROM absorb_queue
         WHERE status = 'done' AND verdict = 'PROCEED'
           AND placement = ANY(%s)
           AND ts_processed > now() - (%s || ' hours')::interval
         ORDER BY ts_processed DESC
         LIMIT 15
        """,
        (list(SMALL_TIER), str(DIGEST_WINDOW_HOURS)),
    )
    small_proceeds = [
        {"id": r[0], "source": r[1], "url": r[2], "placement": r[3], "dossier": r[4]}
        for r in cur.fetchall()
    ]

    cur.execute(
        """
        SELECT source, COUNT(*) AS total,
               SUM(CASE WHEN verdict = 'PROCEED' THEN 1 ELSE 0 END) AS proceeds
          FROM absorb_queue
         WHERE status = 'done'
           AND ts_processed > now() - (%s || ' hours')::interval
           AND source LIKE 'scout-%%'
         GROUP BY source
         HAVING COUNT(*) >= 3
         ORDER BY total DESC
         LIMIT 5
        """,
        (str(DIGEST_WINDOW_HOURS),),
    )
    scout_stats = [
        {"source": r[0], "total": int(r[1]), "proceeds": int(r[2] or 0)}
        for r in cur.fetchall()
    ]

    cur.execute(
        """
        SELECT id, source, url, error
          FROM absorb_queue
         WHERE status = 'failed'
           AND ts_processed > now() - (%s || ' hours')::interval
         ORDER BY ts_processed DESC
         LIMIT 10
        """,
        (str(DIGEST_WINDOW_HOURS),),
    )
    failures = [
        {"id": r[0], "source": r[1], "url": r[2], "error": (r[3] or "")[:200]}
        for r in cur.fetchall()
    ]

    cur.execute(
        "SELECT COUNT(*) FROM absorb_queue WHERE status = 'pending'"
    )
    pending = int(cur.fetchone()[0] or 0)

    cur.close()
    return {
        "breakdown": breakdown,
        "small_proceeds": small_proceeds,
        "scout_stats": scout_stats,
        "failures": failures,
        "pending": pending,
    }


def _format_digest(data: dict) -> str:
    lines = []
    today = _now_local().strftime("%Y-%m-%d %a")
    lines.append(f"Absorb digest -- {today} (last {DIGEST_WINDOW_HOURS}h)")
    lines.append("---")

    total = sum(b["n"] for b in data["breakdown"])
    proceeds = sum(b["n"] for b in data["breakdown"] if b["verdict"] == "PROCEED")
    archives = sum(b["n"] for b in data["breakdown"] if b["verdict"] == "ARCHIVE-AND-NOTE")
    dontprocs = sum(b["n"] for b in data["breakdown"] if b["verdict"] == "DONT_PROCEED")
    lines.append(
        f"Processed: {total}   PROCEED: {proceeds}   ARCHIVE: {archives}   "
        f"DONT: {dontprocs}   Pending: {data['pending']}"
    )

    if data["small_proceeds"]:
        lines.append("")
        lines.append(f"Small-tier PROCEED ({len(data['small_proceeds'])}):")
        for p in data["small_proceeds"]:
            target = ""
            try:
                target = (p["dossier"] or {}).get("placement_target", "") if isinstance(p.get("dossier"), dict) else ""
            except Exception:
                target = ""
            lines.append(f"  #{p['id']} {p['placement']} {target}".rstrip() + f" -- {p['url']}")

    if data["scout_stats"]:
        lines.append("")
        lines.append("Scout sources (last 24h):")
        for s in data["scout_stats"]:
            rate = (s["proceeds"] / s["total"]) if s["total"] else 0.0
            lines.append(f"  {s['source']}: {s['proceeds']}/{s['total']} PROCEED ({rate:.0%})")

    if data["failures"]:
        lines.append("")
        lines.append(f"Failed ({len(data['failures'])}):")
        for f in data["failures"][:5]:
            lines.append(f"  #{f['id']} ({f['source']}) {f['url']} -- {f['error']}")

    return "\n".join(lines)


def _send_digest(text: str) -> Optional[int]:
    try:
        from notifier import send_message
    except Exception as e:
        logger.error(f"absorb_digest: notifier import failed: {e}")
        return None
    chat_id = os.environ.get("OWNER_TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")
    if not chat_id:
        logger.warning("absorb_digest: no OWNER_TELEGRAM_CHAT_ID; printing instead")
        print(text)
        return None
    try:
        return send_message(str(chat_id), text)
    except Exception as e:
        logger.error(f"absorb_digest: send_message failed: {e}")
        return None


def digest_tick() -> dict:
    """Heartbeat entry: emit one Telegram digest, skip Sun."""
    if _is_sunday():
        logger.info("absorb_digest: sunday skip (sabbath rule)")
        return {"sent": False, "reason": "sabbath"}

    data = _summarize_window()
    total = sum(b["n"] for b in data["breakdown"]) + data["pending"] + len(data["failures"])
    if total == 0:
        logger.info("absorb_digest: no activity in window, skip")
        return {"sent": False, "reason": "empty"}

    text = _format_digest(data)
    msg_id = _send_digest(text)
    return {"sent": msg_id is not None, "msg_id": msg_id, "rows": total}
