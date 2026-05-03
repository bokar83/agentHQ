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
        notion_url = ""
        if isinstance(r.payload, dict):
            preview = str(r.payload.get("title") or r.payload.get("hook") or r.payload.get("content") or "")[:120]
            # Lift Notion link: prefer explicit notion_url, then notion_id (page UUID).
            notion_url = str(r.payload.get("notion_url") or "")
            if not notion_url:
                pid = r.payload.get("notion_id") or r.payload.get("page_id")
                if pid:
                    notion_url = f"https://www.notion.so/{str(pid).replace('-', '')}"
        items.append({
            "id": r.id,
            "ts_created": r.ts_created.isoformat() if r.ts_created else None,
            "crew_name": r.crew_name,
            "proposal_type": r.proposal_type,
            "preview": preview,
            "status": r.status,
            "notion_url": notion_url,
        })
    return {"items": items, "count": len(items)}


def _fetch_content_board() -> dict:
    """
    Fetch content board entries:
    - recent: last 3 Posted items (any date)
    - upcoming: next 7 days from today, all statuses except Posted/Archived/Done
    - past_due: scheduled before today, not yet Posted/Skipped/Archived/Done
    """
    import os
    from datetime import date, timedelta
    try:
        from skills.forge_cli.notion_client import NotionClient
        secret = os.environ.get("NOTION_SECRET") or os.environ.get("NOTION_API_KEY")
        db_id = os.environ.get("FORGE_CONTENT_DB", "")
        if not db_id:
            logger.warning("get_content: FORGE_CONTENT_DB env var not set")
            return {"recent": [], "upcoming": [], "past_due": []}
        nc = NotionClient(secret=secret)
        today = date.today()
        week_end = today + timedelta(days=7)

        def _parse_page(page):
            props = page.get("properties", {})
            title_prop = props.get("Title") or props.get("Name") or {}
            title_list = title_prop.get("title", [])
            title = title_list[0].get("text", {}).get("content", "") if title_list else ""
            status = (props.get("Status", {}).get("select") or {}).get("name", "")
            sched_prop = (props.get("Scheduled Date") or {}).get("date") or {}
            # Platform is multi_select -- take first value
            platform_list = (props.get("Platform") or {}).get("multi_select") or []
            platform = platform_list[0].get("name", "") if platform_list else ""
            return {
                "title": title[:80],
                "status": status,
                "scheduled_date": sched_prop.get("start"),
                "platform": platform,
                "notion_url": page.get("url") or "",
                "page_id": page.get("id") or "",
            }

        # 1. Upcoming: today through +7 days, exclude done/archived
        upcoming_results = nc.query_database(
            db_id,
            filter_obj={
                "and": [
                    {"property": "Scheduled Date", "date": {"on_or_after": today.isoformat()}},
                    {"property": "Scheduled Date", "date": {"on_or_before": week_end.isoformat()}},
                ]
            },
            sorts=[{"property": "Scheduled Date", "direction": "ascending"}],
        )
        upcoming = [_parse_page(p) for p in (upcoming_results or [])]
        upcoming = [i for i in upcoming if i["status"] not in ("Archived", "Done")]

        # 2. Past due: before today, not yet resolved
        past_due_results = nc.query_database(
            db_id,
            filter_obj={
                "and": [
                    {"property": "Scheduled Date", "date": {"before": today.isoformat()}},
                ]
            },
            sorts=[{"property": "Scheduled Date", "direction": "descending"}],
        )
        past_due = [_parse_page(p) for p in (past_due_results or [])]
        past_due = [i for i in past_due if i["status"] not in ("Posted", "Skipped", "Archived", "Done")][:5]

        # 3. Recent posted: last 3 Posted items
        recent_results = nc.query_database(
            db_id,
            filter_obj={
                "property": "Status", "select": {"equals": "Posted"}
            },
            sorts=[{"property": "Scheduled Date", "direction": "descending"}],
        )
        recent = [_parse_page(p) for p in (recent_results or [])][:3]

        return {"recent": recent, "upcoming": upcoming, "past_due": past_due}
    except Exception as e:
        logger.warning(f"get_content: Notion fetch failed: {e}")
        return {"recent": [], "upcoming": [], "past_due": []}


def get_content() -> dict:
    """Content Board card: recent posted + upcoming 7 days + past due."""
    data = _fetch_content_board()
    total = len(data["recent"]) + len(data["upcoming"]) + len(data["past_due"])
    return {**data, "count": total}


def _spend_aggregates() -> dict:
    """
    Today's spend, most-recent-day spend (last 7 days before today),
    week-to-date, and month-to-date totals -- plus token totals (prompt +
    completion + cache read + cache write) for the same windows.
    When today=0, the UI shows the most recent day that had actual spend.

    Also returns ledger_last_ts (UTC ISO) so the UI can flag a stale ledger
    when no rows have been inserted recently. Today, only council + direct
    Anthropic SDK calls hit llm_calls; CrewAI calls bypass it (see usage_logger.py).
    """
    try:
        from memory import _pg_conn
        conn = _pg_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                  SUM(CASE WHEN ts >= date_trunc('day', NOW() AT TIME ZONE 'America/Denver')
                           THEN cost_usd ELSE 0 END)                              AS today_usd,
                  SUM(CASE WHEN ts >= date_trunc('week',  NOW() AT TIME ZONE 'America/Denver')
                           THEN cost_usd ELSE 0 END)                              AS week_usd,
                  SUM(CASE WHEN ts >= date_trunc('month', NOW() AT TIME ZONE 'America/Denver')
                           THEN cost_usd ELSE 0 END)                              AS month_usd,
                  SUM(CASE WHEN ts >= date_trunc('day', NOW() AT TIME ZONE 'America/Denver')
                           THEN COALESCE(tokens_prompt,0) + COALESCE(tokens_completion,0)
                              + COALESCE(tokens_cached_read,0) + COALESCE(tokens_cached_write,0)
                           ELSE 0 END)                                            AS today_tokens,
                  SUM(CASE WHEN ts >= date_trunc('week', NOW() AT TIME ZONE 'America/Denver')
                           THEN COALESCE(tokens_prompt,0) + COALESCE(tokens_completion,0)
                              + COALESCE(tokens_cached_read,0) + COALESCE(tokens_cached_write,0)
                           ELSE 0 END)                                            AS week_tokens,
                  SUM(CASE WHEN ts >= date_trunc('month', NOW() AT TIME ZONE 'America/Denver')
                           THEN COALESCE(tokens_prompt,0) + COALESCE(tokens_completion,0)
                              + COALESCE(tokens_cached_read,0) + COALESCE(tokens_cached_write,0)
                           ELSE 0 END)                                            AS month_tokens,
                  MAX(ts)                                                         AS last_ts
                FROM llm_calls
                WHERE ts >= date_trunc('month', NOW() AT TIME ZONE 'America/Denver')
                                 - INTERVAL '60 days'
                """
            )
            row = cur.fetchone()
            today_usd = round(float(row[0] or 0), 4)

            # Find most recent day with actual spend (up to 7 days back)
            cur.execute(
                """
                SELECT DATE(ts AT TIME ZONE 'America/Denver') AS day,
                       SUM(cost_usd)                           AS total
                  FROM llm_calls
                 WHERE ts >= NOW() - INTERVAL '7 days'
                   AND ts <  date_trunc('day', NOW() AT TIME ZONE 'America/Denver')
                 GROUP BY day
                 ORDER BY day DESC
                 LIMIT 1
                """
            )
            last_row = cur.fetchone()
            cur.close()

            last_day_usd = round(float(last_row[1] or 0), 4) if last_row else 0.0
            last_day_date = str(last_row[0]) if last_row else None
            ledger_last_ts = row[6].isoformat() if row[6] else None

            return {
                "today_usd":    today_usd,
                "last_day_usd": last_day_usd,
                "last_day_date": last_day_date,
                "show_last_day": today_usd == 0.0 and last_day_usd > 0.0,
                "week_usd":  round(float(row[1] or 0), 4),
                "month_usd": round(float(row[2] or 0), 4),
                "today_tokens": int(row[3] or 0),
                "week_tokens":  int(row[4] or 0),
                "month_tokens": int(row[5] or 0),
                "ledger_last_ts": ledger_last_ts,
            }
        finally:
            conn.close()
    except Exception as e:
        logger.warning(f"_spend_aggregates: {e}")
        return {"today_usd": 0.0, "last_day_usd": 0.0, "last_day_date": None,
                "show_last_day": False, "week_usd": 0.0, "month_usd": 0.0,
                "today_tokens": 0, "week_tokens": 0, "month_tokens": 0,
                "ledger_last_ts": None}


def _spend_7d_by_day() -> list:
    """7-day daily spend from llm_calls. Returns [{date, usd}] oldest-first."""
    try:
        from memory import _pg_conn
        conn = _pg_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT DATE(ts AT TIME ZONE 'America/Denver') AS day, SUM(cost_usd) AS total
                  FROM llm_calls
                 WHERE ts >= NOW() - INTERVAL '7 days'
                 GROUP BY day
                 ORDER BY day ASC
                """
            )
            rows = cur.fetchall()
            cur.close()
            return [{"date": str(r[0]), "usd": round(float(r[1] or 0), 4)} for r in rows]
        finally:
            conn.close()
    except Exception as e:
        logger.warning(f"_spend_7d_by_day: {e}")
        return []


def _fetch_provider_spend() -> dict:
    """
    Pull live spend figures from OpenRouter's auth/key endpoint.
    Returns usage_daily/weekly/monthly in USD (raw, not cents).
    Non-fatal: returns None values on any error.
    """
    import os, urllib.request, json as _json
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        return {"provider_today": None, "provider_week": None, "provider_month": None, "provider_balance": None}
    try:
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/auth/key",
            headers={"Authorization": f"Bearer {key}"},
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            data = _json.loads(r.read()).get("data", {})

        credits_req = urllib.request.Request(
            "https://openrouter.ai/api/v1/credits",
            headers={"Authorization": f"Bearer {key}"},
        )
        with urllib.request.urlopen(credits_req, timeout=8) as r:
            cdata = _json.loads(r.read()).get("data", {})
        balance = round(float(cdata.get("total_credits", 0)) - float(cdata.get("total_usage", 0)), 4)

        return {
            "provider_today":   round(float(data.get("usage_daily",   0) or 0), 4),
            "provider_week":    round(float(data.get("usage_weekly",  0) or 0), 4),
            "provider_month":   round(float(data.get("usage_monthly", 0) or 0), 4),
            "provider_balance": balance,
        }
    except Exception as e:
        logger.warning(f"_fetch_provider_spend: {e}")
        return {"provider_today": None, "provider_week": None, "provider_month": None, "provider_balance": None}


def _get_historical_comparisons() -> dict:
    """
    Build week-over-week, month-over-month, and YTD comparisons from
    provider_billing snapshots. Returns empty dict gracefully if no data yet.
    """
    try:
        from spend_snapshot import get_historical
        rows = get_historical(days=400)
        if not rows:
            return {}

        import datetime as _dt
        today = _dt.date.today()

        def _week_start(d): return d - _dt.timedelta(days=d.weekday())
        def _month_key(d): return (d.year, d.month)

        this_week_start  = _week_start(today)
        last_week_start  = this_week_start - _dt.timedelta(weeks=1)
        last_week_end    = this_week_start - _dt.timedelta(days=1)
        this_month       = _month_key(today)
        last_month_end   = today.replace(day=1) - _dt.timedelta(days=1)
        last_month       = _month_key(last_month_end)
        ytd_start        = today.replace(month=1, day=1)

        this_week_total = last_week_total = 0.0
        this_month_total = last_month_total = ytd_total = 0.0

        for r in rows:
            d = _dt.date.fromisoformat(r["day"])
            usd = r["usd_today"]
            if _week_start(d) == this_week_start:
                this_week_total += usd
            elif last_week_start <= d <= last_week_end:
                last_week_total += usd
            if _month_key(d) == this_month:
                this_month_total += usd
            elif _month_key(d) == last_month:
                last_month_total += usd
            if d >= ytd_start:
                ytd_total += usd

        def _delta_pct(current, prior):
            if not prior:
                return None
            return round((current - prior) / prior * 100, 1)

        return {
            "this_week":        round(this_week_total, 4),
            "last_week":        round(last_week_total, 4),
            "week_delta_pct":   _delta_pct(this_week_total, last_week_total),
            "this_month":       round(this_month_total, 4),
            "last_month":       round(last_month_total, 4),
            "month_delta_pct":  _delta_pct(this_month_total, last_month_total),
            "ytd":              round(ytd_total, 4),
        }
    except Exception as e:
        logger.warning(f"_get_historical_comparisons: {e}")
        return {}


MONTHLY_BUDGET_USD = 60.0


def get_spend() -> dict:
    """Spend card: today/week/month totals from both ledger and provider (ground truth).

    Also returns historical comparisons (week-over-week, month-over-month, YTD)
    from provider_billing snapshots, and hero pacing vs $50/mo budget.
    """
    import calendar, datetime as _dt
    from autonomy_guard import get_guard
    snap = get_guard().snapshot()
    agg = _spend_aggregates()
    by_day = _spend_7d_by_day()
    provider = _fetch_provider_spend()
    historical = _get_historical_comparisons()
    today_usd = max(snap.spent_today_usd, agg["today_usd"])

    # Pacing: provider_today vs daily share of $50/mo budget
    today = _dt.date.today()
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    daily_budget = MONTHLY_BUDGET_USD / days_in_month
    provider_today = provider["provider_today"] or 0.0
    pacing_pct = round(provider_today / daily_budget * 100, 1) if daily_budget else 0.0

    return {
        "today": {
            "spent_usd":      round(today_usd, 4),
            "cap_usd":        round(snap.cap_usd, 4),
            "remaining_usd":  round(snap.cap_usd - today_usd, 4),
            "per_crew":       {k: round(v, 4) for k, v in snap.per_crew.items()},
        },
        "last_day_usd":   agg["last_day_usd"],
        "last_day_date":  agg["last_day_date"],
        "show_last_day":  agg["show_last_day"],
        "week_usd":       agg["week_usd"],
        "month_usd":      agg["month_usd"],
        "today_tokens":   agg.get("today_tokens", 0),
        "week_tokens":    agg.get("week_tokens", 0),
        "month_tokens":   agg.get("month_tokens", 0),
        "ledger_last_ts": agg.get("ledger_last_ts"),
        "by_day":         by_day,
        "provider_today":   provider["provider_today"],
        "provider_week":    provider["provider_week"],
        "provider_month":   provider["provider_month"],
        "provider_balance": provider["provider_balance"],
        "monthly_budget":   MONTHLY_BUDGET_USD,
        "daily_budget":     round(daily_budget, 4),
        "pacing_pct":       pacing_pct,
        "historical":       historical,
    }


def get_cost_ledger(days: int = 30) -> dict:
    """
    Cost ledger: LLM spend from llm_calls (by project) + manual entries
    from cost_ledger, merged and grouped by date + project + tool.
    Returns rows for the last `days` days, newest first.
    """
    try:
        from memory import _pg_conn
        conn = _pg_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                  DATE(ts AT TIME ZONE 'America/Denver') AS day,
                  COALESCE(project, 'agentsHQ')          AS project,
                  NULL                                    AS customer,
                  'llm'                                   AS category,
                  COALESCE(crew_name, model, 'unknown')   AS tool,
                  COUNT(*)                                AS calls,
                  ROUND(SUM(cost_usd)::numeric, 6)        AS amount_usd
                FROM llm_calls
                WHERE ts >= NOW() - INTERVAL '%s days'
                GROUP BY day, project, tool
                UNION ALL
                SELECT
                  date                                    AS day,
                  project,
                  customer,
                  category,
                  tool,
                  1                                       AS calls,
                  amount_usd
                FROM cost_ledger
                WHERE date >= CURRENT_DATE - INTERVAL '%s days'
                ORDER BY day DESC, amount_usd DESC
                """,
                (days, days),
            )
            rows = cur.fetchall()
            cur.close()
            entries = []
            for r in rows:
                entries.append({
                    "date":       str(r[0]),
                    "project":    str(r[1] or "agentsHQ"),
                    "customer":   str(r[2]) if r[2] else None,
                    "category":   str(r[3] or ""),
                    "tool":       str(r[4] or ""),
                    "calls":      int(r[5] or 0),
                    "amount_usd": float(r[6] or 0),
                })
            total = round(sum(e["amount_usd"] for e in entries), 4)
            return {"entries": entries, "total_usd": total, "days": days}
        finally:
            conn.close()
    except Exception as e:
        logger.warning(f"get_cost_ledger: {e}")
        return {"entries": [], "total_usd": 0.0, "days": days}


def add_cost_ledger_entry(
    amount_usd: float,
    tool: str,
    category: str,
    project: str = "agentsHQ",
    customer: str | None = None,
    description: str | None = None,
    date_str: str | None = None,
) -> dict:
    """Insert a manual cost entry into cost_ledger."""
    from datetime import date as _date
    try:
        from memory import _pg_conn
        conn = _pg_conn()
        try:
            cur = conn.cursor()
            entry_date = _date.fromisoformat(date_str) if date_str else _date.today()
            cur.execute(
                """
                INSERT INTO cost_ledger (date, project, customer, category, tool, description, amount_usd, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'api')
                RETURNING id
                """,
                (entry_date, project, customer, category, tool, description, round(amount_usd, 6)),
            )
            row = cur.fetchone()
            conn.commit()
            cur.close()
            return {"ok": True, "id": row[0]}
        finally:
            conn.close()
    except Exception as e:
        logger.warning(f"add_cost_ledger_entry: {e}")
        return {"ok": False, "error": str(e)}


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
    """Last `limit` router_log rows with no crew assigned (unrouted), last 24h."""
    try:
        from memory import _pg_conn
        conn = _pg_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT ts, task_type, crew
                  FROM router_log
                 WHERE crew IS NULL
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
                    "crew": str(r[2] or "unrouted"),
                }
                for r in rows
            ]
        finally:
            conn.close()
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
    """Latest task_outcomes row from an autonomous crew, excluding heartbeat probes.

    heartbeat-self-test fires every minute as a liveness check and would otherwise
    dominate LIMIT 1 forever, hiding real autonomous work (auto_publisher, griot, etc.).
    """
    try:
        from memory import _pg_conn
        conn = _pg_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT ts_started, crew_name, success, result_summary
                  FROM task_outcomes
                 WHERE crew_name <> 'heartbeat-self-test'
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
                "status": "ok" if row[2] else "failed",
                "description": str(row[3] or "")[:120],
            }
        finally:
            conn.close()
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
    """Hero strip: system_status, last_action, next_fire, spend_pacing, health_check."""
    import calendar, datetime as _dt
    from autonomy_guard import get_guard
    guard = get_guard()
    killed = guard.is_killed()
    log_errors = _error_log_tail(lines=5)

    # Spend pacing: provider ground-truth today vs daily share of $50/mo budget.
    # Ledger (snap.spent_today_usd) misses CrewAI calls so use provider directly.
    provider = _fetch_provider_spend()
    provider_today = provider.get("provider_today") or 0.0
    today = _dt.date.today()
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    daily_budget = MONTHLY_BUDGET_USD / days_in_month
    pct = round(provider_today / daily_budget * 100, 1) if daily_budget else 0.0

    if killed:
        system_status = "red"
    elif log_errors or pct > 100:
        system_status = "amber"
    else:
        system_status = "green"

    try:
        from health_sweep import read_sweep_state
        sweep = read_sweep_state()
    except Exception:
        sweep = {}

    return {
        "system_status": system_status,
        "killed": killed,
        "last_action": _last_autonomous_action(),
        "next_fire": _next_scheduled_fire(),
        "spend_pacing": {
            "spent_usd":    round(provider_today, 4),
            "cap_usd":      round(daily_budget, 4),
            "pct":          pct,
            "monthly_budget": MONTHLY_BUDGET_USD,
            "balance_usd":  provider.get("provider_balance"),
        },
        "health_check": sweep,
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
                "notion_url": page.get("url") or "",
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
