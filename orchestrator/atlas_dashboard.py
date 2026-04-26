"""
atlas_dashboard.py -- Pure data fetchers for the Atlas M8 dashboard.

One function per card. Returns plain dicts ready for json.dumps().
No FastAPI imports. No side effects. All I/O is read-only except
action helpers (added later) which are at the bottom of this file.
"""
from __future__ import annotations

import logging

logger = logging.getLogger("agentsHQ.atlas_dashboard")


def get_state() -> dict:
    """Atlas State card: autonomy kill switch + per-crew flags."""
    from autonomy_guard import get_guard
    return get_guard().state_summary()


def get_queue() -> dict:
    """Approval Queue card: pending items, newest first."""
    import approval_queue
    rows = approval_queue.list_pending(limit=20)
    items = []
    for r in rows:
        preview = ""
        if isinstance(r.payload, dict):
            preview = str(r.payload.get("title") or r.payload.get("hook") or r.payload.get("content") or "")[:120]
        items.append({
            "id": r.id,
            "ts_created": r.ts_created.isoformat() if r.ts_created else None,
            "crew_name": r.crew_name,
            "proposal_type": r.proposal_type,
            "preview": preview,
            "status": r.status,
        })
    return {"items": items, "count": len(items)}


def _fetch_content_board() -> list:
    """Fetch this-week content items from Notion Content Board."""
    import os
    from datetime import date, timedelta
    try:
        from skills.forge_cli.notion_client import NotionClient
        secret = os.environ.get("NOTION_SECRET") or os.environ.get("NOTION_API_KEY")
        db_id = os.environ.get("NOTION_CONTENT_BOARD_DB_ID", "")
        if not db_id:
            return []
        nc = NotionClient(secret=secret)
        today = date.today()
        week_end = today + timedelta(days=7)
        results = nc.query_database(
            db_id,
            filter={
                "and": [
                    {"property": "Scheduled Date", "date": {"on_or_after": today.isoformat()}},
                    {"property": "Scheduled Date", "date": {"on_or_before": week_end.isoformat()}},
                ]
            },
            sorts=[{"property": "Scheduled Date", "direction": "ascending"}],
        )
        items = []
        for page in (results or []):
            props = page.get("properties", {})
            title = ""
            title_prop = props.get("Title") or props.get("Name") or {}
            title_list = title_prop.get("title", [])
            if title_list:
                title = title_list[0].get("text", {}).get("content", "")
            status_prop = props.get("Status", {})
            status = (status_prop.get("select") or {}).get("name", "")
            sched_prop = props.get("Scheduled Date", {}).get("date") or {}
            platform_prop = props.get("Platform", {})
            platform = (platform_prop.get("select") or {}).get("name", "")
            items.append({
                "title": title[:80],
                "status": status,
                "scheduled_date": sched_prop.get("start"),
                "platform": platform,
            })
        return items
    except Exception as e:
        logger.warning(f"get_content: Notion fetch failed: {e}")
        return []


def get_content() -> dict:
    """Content Board card: this-week scheduled posts."""
    items = _fetch_content_board()
    return {"items": items, "count": len(items)}


def _spend_7d_by_day() -> list:
    """7-day daily spend from llm_calls. Returns [{date, usd}] newest-last."""
    try:
        from memory import _pg_conn
        conn = _pg_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT DATE(ts AT TIME ZONE 'UTC') AS day, SUM(cost_usd) AS total
              FROM llm_calls
             WHERE ts >= NOW() - INTERVAL '7 days'
               AND autonomous = TRUE
             GROUP BY day
             ORDER BY day ASC
            """
        )
        rows = cur.fetchall()
        cur.close()
        return [{"date": str(r[0]), "usd": float(r[1] or 0)} for r in rows]
    except Exception as e:
        logger.warning(f"_spend_7d_by_day: {e}")
        return []


def get_spend() -> dict:
    """Spend card: today's spend vs cap + 7-day daily breakdown."""
    from autonomy_guard import get_guard
    snap = get_guard().snapshot()
    by_day = _spend_7d_by_day()
    return {
        "today": {
            "spent_usd": round(snap.spent_today_usd, 4),
            "cap_usd": round(snap.cap_usd, 4),
            "remaining_usd": round(snap.remaining_usd, 4),
            "per_crew": {k: round(v, 4) for k, v in snap.per_crew.items()},
        },
        "by_day": by_day,
    }


def get_heartbeats() -> dict:
    """Heartbeats card: registered wakes and their last-fire state."""
    from datetime import datetime, timezone
    from heartbeat import list_wakes
    wakes = list_wakes()
    items = []
    for w in wakes:
        last_fired = None
        if w.last_fired_epoch is not None:
            last_fired = datetime.fromtimestamp(w.last_fired_epoch, tz=timezone.utc).isoformat()
        elif w.last_fired_date is not None:
            last_fired = str(w.last_fired_date)
        items.append({
            "name": w.name,
            "crew_name": w.crew_name,
            "at_hour": w.at_hour,
            "at_minute": w.at_minute,
            "every_seconds": w.every_seconds,
            "last_fired": last_fired,
        })
    return {"wakes": items, "count": len(items)}
