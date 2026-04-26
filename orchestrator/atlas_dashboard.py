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
            filter_obj={
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
        return [{"date": str(r[0]), "usd": round(float(r[1] or 0), 4)} for r in rows]
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


def _router_log_fallbacks(limit: int = 20) -> list:
    """Last `limit` router_log rows where fallback=true, last 24h."""
    try:
        from memory import _pg_conn
        conn = _pg_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT ts, task_type
              FROM router_log
             WHERE fallback = TRUE
               AND ts >= NOW() - INTERVAL '24 hours'
             ORDER BY ts DESC
             LIMIT %s
            """,
            (limit,),
        )
        rows = cur.fetchall()
        cur.close()
        return [
            {
                "ts": r[0].isoformat() if r[0] else None,
                "task_type": str(r[1] or ""),
            }
            for r in rows
        ]
    except Exception as e:
        logger.warning(f"_router_log_fallbacks: {e}")
        return []


def _error_log_tail(lines: int = 30) -> list:
    """Last `lines` lines from /var/log/error_monitor.log."""
    import os
    log_path = os.environ.get("ERROR_MONITOR_LOG", "/var/log/error_monitor.log")
    try:
        with open(log_path, "r") as f:
            all_lines = f.readlines()
        return [l.rstrip() for l in all_lines[-lines:] if l.strip()]
    except FileNotFoundError:
        return []
    except Exception as e:
        logger.warning(f"_error_log_tail: {e}")
        return []


def get_errors() -> dict:
    """Errors card: router_log fallbacks + error_monitor.log tail."""
    return {
        "fallbacks": _router_log_fallbacks(limit=20),
        "log_lines": _error_log_tail(lines=30),
    }


def _last_autonomous_action() -> dict:
    """Latest task_outcomes row from an autonomous crew."""
    try:
        from memory import _pg_conn
        conn = _pg_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT ts_started, task_type, status, summary
              FROM task_outcomes
             WHERE autonomous = TRUE
             ORDER BY ts_started DESC
             LIMIT 1
            """
        )
        row = cur.fetchone()
        cur.close()
        if row is None:
            return {"ts": None, "description": "No autonomous actions yet"}
        return {
            "ts": row[0].isoformat() if row[0] else None,
            "task_type": str(row[1] or ""),
            "status": str(row[2] or ""),
            "description": str(row[3] or "")[:120],
        }
    except Exception as e:
        logger.warning(f"_last_autonomous_action: {e}")
        return {"ts": None, "description": "Unavailable"}


def _next_scheduled_fire() -> dict:
    """Earliest upcoming daily wake from heartbeat registry."""
    import os
    from datetime import datetime
    try:
        import pytz
        from heartbeat import list_wakes
        tz = pytz.timezone(os.environ.get("GENERIC_TIMEZONE", "America/Denver"))
        now_local = datetime.now(tz)
        best = None
        best_mins = None
        for w in list_wakes():
            if w.at_hour is None:
                continue
            if w.last_fired_date == now_local.date():
                continue
            fire_mins = w.at_hour * 60 + (w.at_minute or 0)
            now_mins = now_local.hour * 60 + now_local.minute
            remaining = fire_mins - now_mins
            if remaining < 0:
                remaining += 24 * 60
            if best_mins is None or remaining < best_mins:
                best_mins = remaining
                best = w
        if best is None:
            return {"name": None, "at": None, "in_minutes": None}
        return {
            "name": best.name,
            "at": f"{best.at_hour:02d}:{best.at_minute or 0:02d}",
            "in_minutes": best_mins,
        }
    except Exception as e:
        logger.warning(f"_next_scheduled_fire: {e}")
        return {"name": None, "at": None, "in_minutes": None}


def get_hero() -> dict:
    """Hero strip: system_status, last_action, next_fire, spend_pacing."""
    from autonomy_guard import get_guard
    guard = get_guard()
    snap = guard.snapshot()
    killed = guard.is_killed()
    errors = _router_log_fallbacks(limit=1)
    pct = (snap.spent_today_usd / snap.cap_usd * 100) if snap.cap_usd else 0.0
    if killed:
        system_status = "red"
    elif errors or pct > 90:
        system_status = "amber"
    else:
        system_status = "green"
    return {
        "system_status": system_status,
        "killed": killed,
        "last_action": _last_autonomous_action(),
        "next_fire": _next_scheduled_fire(),
        "spend_pacing": {
            "spent_usd": round(snap.spent_today_usd, 4),
            "cap_usd": round(snap.cap_usd, 4),
            "pct": round(pct, 1),
        },
    }


def _priority_score(impact: str, effort: str) -> int:
    """Compute numeric priority from Impact + Effort selects. Higher = more important."""
    impact_map = {"High": 3, "Medium": 2, "Low": 1}
    effort_map = {"Low": 3, "Medium": 2, "High": 1}
    return impact_map.get(impact, 0) + effort_map.get(effort, 0)


def _fetch_ideas(limit: int = 10) -> list:
    """Fetch top-ranked active ideas from the agentsHQ Ideas Notion DB."""
    import os
    try:
        from skills.forge_cli.notion_client import NotionClient
        secret = os.environ.get("NOTION_SECRET") or os.environ.get("NOTION_API_KEY")
        db_id = os.environ.get("IDEAS_DB_ID", "")
        if not db_id:
            return []
        nc = NotionClient(secret=secret)
        results = nc.query_database(
            db_id,
            filter_obj={
                "and": [
                    {"property": "Status", "select": {"does_not_equal": "Done"}},
                    {"property": "Status", "select": {"does_not_equal": "Killed"}},
                    {"property": "Status", "select": {"does_not_equal": "Archived"}},
                ]
            },
        )
        items = []
        for page in (results or []):
            props = page.get("properties", {})
            title = ""
            title_prop = props.get("Name") or {}
            title_list = title_prop.get("title", [])
            if title_list:
                title = title_list[0].get("text", {}).get("content", "")
            impact = (props.get("Impact", {}).get("select") or {}).get("name", "")
            effort = (props.get("Effort", {}).get("select") or {}).get("name", "")
            category = (props.get("Category", {}).get("select") or {}).get("name", "")
            status = (props.get("Status", {}).get("select") or {}).get("name", "")
            score = _priority_score(impact, effort)
            items.append({
                "title": title[:80],
                "impact": impact,
                "effort": effort,
                "category": category,
                "status": status,
                "score": score,
            })
        items.sort(key=lambda x: x["score"], reverse=True)
        return items[:limit]
    except Exception as e:
        logger.warning(f"_fetch_ideas: {e}")
        return []


def get_ideas() -> dict:
    """Top Ideas card: top-ranked active ideas sorted by priority score."""
    items = _fetch_ideas(limit=10)
    return {"items": items, "count": len(items)}
