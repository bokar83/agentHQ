"""
handlers_commands.py - Slash command dispatch for Telegram.

One function per command, grouped by era:
- Original ops commands (pre-autonomy): /cost, /projects, /status, /lessons,
  /purge-lesson, /scan-drive, /switch
- Phase 0 autonomy rails:                /autonomy_status, /pause_autonomy,
  /resume_autonomy
- Phase 1 approval queue:                /queue, /approve, /reject, /outcomes
- Phase 2 heartbeat:                     /heartbeat_status, /trigger_heartbeat

dispatch_command(text, chat_id) is the single entry point called from
handlers.process_telegram_update. Returns True if a command fired, False
otherwise. Each handler is responsible for its own Telegram reply.

DB access routes through memory._pg_conn() per the refactor consolidation
goal. Side-effects (threading, state dict writes) mirror the monolith
exactly so runtime behavior does not drift.
"""
import logging
import os
import re
import threading
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

from state import _last_completed_job, _active_project

logger = logging.getLogger("agentsHQ.handlers_commands")


# ══════════════════════════════════════════════════════════════
# Original ops commands
# ══════════════════════════════════════════════════════════════

def _cmd_scan_drive(text: str, chat_id: str) -> bool:
    if text.lower().strip() != "/scan-drive":
        return False
    from notifier import send_message as _send
    _send(chat_id, "Scanning Drive inbox, will process all unclassified files and report back.")

    def _do_scan():
        try:
            from scheduler import _run_drive_watch
            _run_drive_watch(scan_all=True)
            _send(chat_id, "Drive scan complete.")
        except Exception as e:
            logger.error(f"/scan-drive error: {e}")
            _send(chat_id, f"Drive scan failed: {e}")

    threading.Thread(target=_do_scan, daemon=True).start()
    return True


def _cmd_lessons(text: str, chat_id: str) -> bool:
    if not text.lower().startswith("/lessons"):
        return False
    from notifier import send_message as _send
    parts = text.strip().split(maxsplit=1)
    task_type_filter = parts[1].strip() if len(parts) > 1 else None
    from memory import list_lessons
    rows = list_lessons(task_type=task_type_filter, limit=10)
    if not rows:
        _send(chat_id, "No lessons found" + (f" for '{task_type_filter}'" if task_type_filter else "") + ".")
    else:
        lines = ["Recent lessons" + (f" ({task_type_filter})" if task_type_filter else "") + ":"]
        for r in rows:
            sign = "+" if r["learning_type"] != "negative" else "-"
            lines.append(f"[{r['id']}] {sign} [{r['task_type']}] {r['content'][:120]}")
        _send(chat_id, "\n".join(lines))
    return True


def _cmd_purge_lesson(text: str, chat_id: str) -> bool:
    if not text.lower().startswith("/purge-lesson"):
        return False
    from notifier import send_message as _send
    parts = text.strip().split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip().isdigit():
        _send(chat_id, "Usage: /purge-lesson [id]. Get the id from /lessons.")
        return True
    lesson_id = int(parts[1].strip())
    from memory import purge_lesson
    ok = purge_lesson(lesson_id)
    _send(chat_id, f"Lesson {lesson_id} purged." if ok else f"Lesson {lesson_id} not found.")
    return True


def _cmd_status(text: str, chat_id: str) -> bool:
    # NOTE: must check before /status/<id> HTTP route (this is Telegram side only)
    # and must NOT swallow /status_command-like unrelated prefixes.
    if not text.lower().startswith("/status"):
        return False
    # Guard against future collisions like /status_foo by requiring space or end.
    if len(text) > len("/status") and not text[len("/status")].isspace():
        return False
    from notifier import send_message as _send
    from memory import get_job
    parts = text.strip().split(maxsplit=1)
    if len(parts) < 2:
        if chat_id in _last_completed_job:
            prior = _last_completed_job[chat_id]
            _send(chat_id, f"Last job: {prior['job_id'][:8]} | {prior['task_type']} | delivered {prior['delivered_at'].strftime('%H:%M')}")
        else:
            _send(chat_id, "No recent jobs. Send /projects to see history.")
        return True
    job_id_hint = parts[1].strip()
    job = get_job(job_id_hint)
    if not job:
        _send(chat_id, f"Job '{job_id_hint}' not found.")
        return True
    status = job.get("status", "unknown")
    task_type = job.get("task_type", "?")
    created = job.get("created_at", "?")
    result_preview = (job.get("result") or "")[:200]
    _send(chat_id, f"Job {job_id_hint[:8]}\nStatus: {status}\nType: {task_type}\nStarted: {created}\n\n{result_preview}")
    return True


def _cmd_projects(text: str, chat_id: str) -> bool:
    if not text.lower().startswith("/projects"):
        return False
    from notifier import send_message as _send
    try:
        from memory import _pg_conn
        conn = _pg_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT job_id, task_type, status, created_at
                FROM job_queue
                WHERE from_number = %s
                ORDER BY created_at DESC
                LIMIT 10
                """,
                (chat_id,),
            )
            rows = cur.fetchall()
            cur.close()
        finally:
            conn.close()
        if not rows:
            _send(chat_id, "No projects found for this session yet.")
        else:
            lines = ["Recent projects:"]
            for r in rows:
                jid, jtype, jstatus, jcreated = r
                ts = str(jcreated)[:16] if jcreated else "?"
                lines.append(f"{ts} | {jid[:8]} | {jtype or '?'} | {jstatus}")
            _send(chat_id, "\n".join(lines))
    except Exception as e:
        _send(chat_id, f"Could not load projects: {e}")
    return True


def _cmd_cost(text: str, chat_id: str) -> bool:
    if not text.lower().startswith("/cost"):
        return False
    from notifier import send_message as _send
    from memory import _pg_conn
    parts = text.strip().split(maxsplit=1)
    try:
        days = int(parts[1]) if len(parts) > 1 else 30
    except ValueError:
        days = 30
    try:
        # 1. OpenRouter ground truth (CrewAI + all routed LLM calls)
        or_today = or_week = or_month = or_lifetime = or_balance = None
        try:
            from spend_snapshot import _fetch_openrouter
            or_data = _fetch_openrouter()
            or_today    = or_data["usd_today"]
            or_week     = or_data["usd_week"]
            or_month    = or_data["usd_month"]
            or_lifetime = or_data["usd_lifetime"]
            or_balance  = or_data["balance_usd"]
        except Exception as e:
            logger.warning(f"_cmd_cost: OpenRouter fetch failed: {e}")

        # 2. Direct Anthropic SDK calls (council, etc.) not routed via OpenRouter
        sdk_calls = sdk_usd = sdk_council = 0
        top_agents = []
        try:
            conn = _pg_conn()
            try:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT
                        COUNT(*),
                        ROUND(SUM(cost_usd)::numeric, 4),
                        COUNT(DISTINCT council_run_id) FILTER (WHERE council_run_id IS NOT NULL)
                    FROM llm_calls
                    WHERE ts > NOW() - INTERVAL '%s days'
                    """,
                    (days,),
                )
                row = cur.fetchone()
                sdk_calls, sdk_usd, sdk_council = int(row[0] or 0), float(row[1] or 0), int(row[2] or 0)

                cur.execute(
                    """
                    SELECT COALESCE(agent_name, crew_name, model, 'unknown') AS name,
                           COUNT(*) AS calls,
                           ROUND(SUM(cost_usd)::numeric, 4) AS usd
                    FROM llm_calls
                    WHERE ts > NOW() - INTERVAL '%s days'
                    GROUP BY name
                    ORDER BY usd DESC NULLS LAST
                    LIMIT 6
                    """,
                    (days,),
                )
                top_agents = cur.fetchall()

                # 3. ElevenLabs from cost_ledger
                cur.execute(
                    """
                    SELECT
                        COUNT(*),
                        ROUND(SUM(amount_usd)::numeric, 4)                                                            AS period_usd,
                        ROUND(SUM(amount_usd) FILTER (WHERE date >= CURRENT_DATE)::numeric, 4)                        AS today_usd,
                        ROUND(SUM(amount_usd) FILTER (WHERE date >= date_trunc('month', CURRENT_DATE)::date)::numeric, 4) AS month_usd
                    FROM cost_ledger
                    WHERE tool = 'elevenlabs_tts'
                      AND date >= CURRENT_DATE - INTERVAL '%s days'
                    """,
                    (days,),
                )
                el_row = cur.fetchone()
                el_calls = int(el_row[0] or 0)
                el_period = float(el_row[1] or 0)
                el_today  = float(el_row[2] or 0)
                el_month  = float(el_row[3] or 0)

                cur.close()
            finally:
                conn.close()
        except Exception as e:
            logger.warning(f"_cmd_cost: DB fetch failed: {e}")
            el_calls = el_period = el_today = el_month = 0

        # 4. Kie credit balance (no spend history table yet)
        kie_credits = None
        try:
            from kie_media import check_credits
            kie_credits = check_credits()
        except Exception:
            pass

        lines = [f"Spend report (last {days}d)", ""]

        # OpenRouter headline
        lines.append("LLM (OpenRouter -- ground truth)")
        if or_today is not None:
            lines.append(f"  Today:    ${or_today:.4f}")
            lines.append(f"  Week:     ${or_week:.4f}")
            lines.append(f"  Month:    ${or_month:.4f}")
            lines.append(f"  Lifetime: ${or_lifetime:.2f}")
            lines.append(f"  Balance:  ${or_balance:.2f}")
        else:
            lines.append("  (unavailable)")

        # Direct SDK calls (council)
        if sdk_calls > 0:
            lines.append("")
            lines.append(f"Direct SDK ({sdk_calls} calls, {sdk_council} council runs): ${sdk_usd:.4f}")
            for name, calls, usd in top_agents:
                lines.append(f"  ${usd or 0:.4f}  {name}  ({calls})")

        # ElevenLabs
        lines.append("")
        lines.append("ElevenLabs TTS")
        if el_calls > 0:
            lines.append(f"  Period:   ${el_period:.4f}  ({el_calls} renders)")
            lines.append(f"  Today:    ${el_today:.4f}")
            lines.append(f"  MTD:      ${el_month:.4f}")
        else:
            lines.append("  $0.0000  (no renders yet)")

        # Kie
        lines.append("")
        lines.append("Kie (kie.ai media)")
        if kie_credits is not None:
            lines.append(f"  Credits remaining: {kie_credits:,}")
            lines.append("  (per-render spend not yet tracked)")
        else:
            lines.append("  (balance unavailable)")

        # Grand total: OpenRouter MTD + ElevenLabs MTD
        if or_month is not None:
            grand = round(or_month + el_month, 2)
            lines.append("")
            lines.append(f"MTD TOTAL (OR + ElevenLabs): ${grand:.2f}")

        _send(chat_id, "\n".join(lines))
    except Exception as e:
        _send(chat_id, f"Could not load cost: {e}")
    return True


def _cmd_switch(text: str, chat_id: str) -> bool:
    if not text.lower().startswith("/switch"):
        return False
    from notifier import send_message as _send
    parts = text.strip().split(maxsplit=1)
    if len(parts) < 2:
        current = _active_project.get(chat_id, "default")
        _send(chat_id, f"Active project: {current}\nUsage: /switch <project-name>")
        return True
    project_name = parts[1].strip().lower().replace(" ", "-")
    _active_project[chat_id] = project_name
    _send(chat_id, f"Switched to project: {project_name}\nAll tasks will use this context until you switch again.")
    return True


# ══════════════════════════════════════════════════════════════
# Phase 0: autonomy safety rails
# ══════════════════════════════════════════════════════════════

def _cmd_autonomy_status(text: str, chat_id: str) -> bool:
    if not text.lower().startswith("/autonomy_status"):
        return False
    from notifier import send_message as _send
    from autonomy_guard import get_guard
    g = get_guard()
    snap = g.snapshot()
    summary = g.state_summary()
    lines = []
    if summary["killed"]:
        lines.append(f"KILLED: {summary['killed_reason']}")
    else:
        lines.append("Autonomy live")
    lines.append(f"Spent today: ${snap.spent_today_usd:.4f} / ${snap.cap_usd:.2f}")
    lines.append(f"Remaining:   ${snap.remaining_usd:.4f}")
    lines.append("")
    lines.append("Crews:")
    for name, cfg in summary["crews"].items():
        flag = "on" if cfg["enabled"] else "off"
        mode = "dry-run" if cfg["dry_run"] else "LIVE"
        lines.append(f"  {name}: {flag} ({mode})")
    _send(chat_id, "\n".join(lines))
    return True


def _cmd_pause_autonomy(text: str, chat_id: str) -> bool:
    if not text.lower().startswith("/pause_autonomy"):
        return False
    from notifier import send_message as _send
    from autonomy_guard import get_guard
    g = get_guard()
    g.kill("telegram /pause_autonomy")
    _send(chat_id, "Autonomy KILLED. All autonomous crews blocked.\nRun /resume_autonomy to restore.")
    return True


def _cmd_resume_autonomy(text: str, chat_id: str) -> bool:
    if not text.lower().startswith("/resume_autonomy"):
        return False
    from notifier import send_message as _send
    from autonomy_guard import get_guard
    g = get_guard()
    g.unkill()
    snap = g.snapshot()
    _send(chat_id, f"Autonomy resumed. ${snap.spent_today_usd:.4f} / ${snap.cap_usd:.2f} spent today.")
    return True



# ══════════════════════════════════════════════════════════════
# Phase 1: approval queue
# ══════════════════════════════════════════════════════════════

def _cmd_queue(text: str, chat_id: str) -> bool:
    if not text.lower().startswith("/queue"):
        return False
    from notifier import send_message as _send
    from unified_queue import list_all_pending
    items = list_all_pending(limit=15)
    if not items:
        _send(chat_id, "Queue empty. No pending proposals.")
        return True
    lines = [f"Pending ({len(items)}):"]
    now = datetime.now(timezone.utc)
    for item in items:
        created = item.get("created_at") or ""
        try:
            from datetime import datetime as _dt
            ts = _dt.fromisoformat(created.replace("Z", "+00:00"))
            age_min = int((now - ts).total_seconds() / 60)
            age = f"{age_min}m"
        except Exception:
            age = "?"
        lines.append(f"  {item['label']}  {item['crew_name']}  {item['proposal_type']}  ({age})")
    lines.append("\nApprove: /approve <id>  |  Reject: /reject <id>")
    lines.append("(Q# = content queue, P# = commit proposal)")
    _send(chat_id, "\n".join(lines))
    return True


def _cmd_approve(text: str, chat_id: str) -> bool:
    if not text.lower().startswith("/approve"):
        return False
    from notifier import send_message as _send
    from unified_queue import approve_any
    parts = text.strip().split(maxsplit=2)
    if len(parts) < 2:
        _send(chat_id, "Usage: /approve <id> [note]\n(Q# for content queue, P<hex> for commit proposals)")
        return True
    id_str = parts[1]
    note = parts[2] if len(parts) > 2 else None
    result = approve_any(id_str, note=note)
    if result.get("ok"):
        _send(chat_id, f"{id_str}: approved.")
    else:
        _send(chat_id, f"{id_str}: {result.get('error', 'failed')}")
    return True


def _cmd_reject(text: str, chat_id: str) -> bool:
    if not text.lower().startswith("/reject"):
        return False
    from notifier import send_message as _send
    from unified_queue import reject_any
    from approval_queue import KNOWN_FEEDBACK_TAGS
    parts = text.strip().split(maxsplit=3)
    if len(parts) < 2:
        _send(chat_id, "Usage: /reject <id> [tag] [note]\n(Q# for content queue, P<hex> for commit proposals)")
        return True
    id_str = parts[1]
    tag = None
    note = None
    if len(parts) > 2:
        if parts[2].lower() in KNOWN_FEEDBACK_TAGS:
            tag = parts[2].lower()
            note = parts[3] if len(parts) > 3 else None
        else:
            note = " ".join(parts[2:])
    result = reject_any(id_str, note=note, feedback_tag=tag)
    if result.get("ok"):
        _send(chat_id, f"{id_str}: rejected. Tag: {tag or 'none'}")
    else:
        _send(chat_id, f"{id_str}: {result.get('error', 'failed')}")
    return True


def _cmd_outcomes(text: str, chat_id: str) -> bool:
    if not text.lower().startswith("/outcomes"):
        return False
    from notifier import send_message as _send
    from episodic_memory import crew_stats
    parts = text.strip().split()
    crew = parts[1] if len(parts) > 1 else None
    try:
        days = int(parts[2]) if len(parts) > 2 else 7
    except ValueError:
        days = 7
    if crew is None:
        _send(chat_id, "Usage: /outcomes <crew> [days].  Crews: griot, hunter, concierge, chairman")
        return True
    stats = crew_stats(crew, days=days)
    lines = [
        f"Outcomes for {crew} (last {days} days):",
        f"  total:        {stats['total']}",
        f"  approved:     {stats['approved']}",
        f"  rejected:     {stats['rejected']}",
        f"  edited:       {stats['edited']}",
        f"  approval rate: {stats['approval_rate']*100:.1f}%",
        f"  avg cost:      ${stats['avg_cost_usd']:.4f}",
    ]
    if stats["top_feedback_tags"]:
        lines.append("  top feedback tags:")
        for tag, n in stats["top_feedback_tags"]:
            lines.append(f"    {tag}: {n}")
    _send(chat_id, "\n".join(lines))
    return True


# ══════════════════════════════════════════════════════════════
# Phase 2: heartbeat
# ══════════════════════════════════════════════════════════════

def _cmd_heartbeat_status(text: str, chat_id: str) -> bool:
    if not text.lower().startswith("/heartbeat_status"):
        return False
    from notifier import send_message as _send
    import heartbeat as _hb
    wakes = _hb.list_wakes()
    if not wakes:
        _send(chat_id, "Heartbeat: no wakes registered.")
        return True
    lines = [f"Heartbeat: {len(wakes)} wake(s) registered"]
    for w in wakes:
        info = _hb.dry_run_next(w.name)
        if w.at_hour is not None:
            cadence = f"at {w.at_hour:02d}:{(w.at_minute or 0):02d}"
        else:
            cadence = f"every {w.every_seconds}s"
        lines.append(f"  {w.name} ({w.crew_name}) {cadence}")
        lines.append(f"    next: {info['next_fire_local']}  guard_allow={info['guard_would_allow']}")
    _send(chat_id, "\n".join(lines))
    return True


def _cmd_trigger_heartbeat(text: str, chat_id: str) -> bool:
    if not text.lower().startswith("/trigger_heartbeat"):
        return False
    from notifier import send_message as _send
    import heartbeat as _hb
    parts = text.strip().split(maxsplit=1)
    if len(parts) < 2:
        _send(chat_id, "Usage: /trigger_heartbeat <wake_name>.  Use /heartbeat_status to list.")
        return True
    info = _hb.dry_run_next(parts[1].strip())
    if "error" in info:
        _send(chat_id, info["error"])
        return True
    out = [
        f"Wake: {info['name']}",
        f"Crew: {info['crew_name']}",
        f"Next fire: {info['next_fire_local']} (in {info['seconds_until_fire']}s)",
        f"Guard would allow: {info['guard_would_allow']}",
    ]
    if info.get("guard_reason"):
        out.append(f"Guard reason: {info['guard_reason']}")
    out.append("(Phase 2: dry-run only; no actual fire)")
    _send(chat_id, "\n".join(out))
    return True


# ══════════════════════════════════════════════════════════════
# Phase 3: Griot
# ══════════════════════════════════════════════════════════════

def _cmd_griot_dryrun(text: str, chat_id: str) -> bool:
    """Manually exercise the Griot picker without enqueuing to approval_queue.

    Fetches the Content Board, runs the split + dedup + scoring, reports the
    top candidate (or empty-backlog message) back to Telegram. Useful for
    tuning SCORING_WEIGHTS before flipping griot.enabled=true.
    """
    if not text.lower().startswith("/griot_dryrun"):
        return False
    from notifier import send_message as _send
    try:
        import griot as _griot
        from skills.forge_cli.notion_client import NotionClient
        import os as _os
        from datetime import date as _date
        notion_secret = _os.environ.get("NOTION_SECRET") or _os.environ.get("NOTION_API_KEY")
        notion = NotionClient(secret=notion_secret)
        rows = _griot._fetch_board_rows(notion)
        today = _date.today().isoformat()
        candidates_all, recent_posts = _griot._split_pool(rows, today)
        candidates = [c for c in candidates_all if not _griot._candidate_already_proposed(c["notion_id"])]
        dedup_dropped = len(candidates_all) - len(candidates)

        lines = [f"Griot dryrun ({len(rows)} board rows)"]
        lines.append(f"  candidates (Ready without Scheduled Date): {len(candidates_all)}")
        lines.append(f"  after dedup (not proposed in last {_griot.CANDIDATE_DEDUP_DAYS}d): {len(candidates)}")
        lines.append(f"  recent_posts (window {_griot.RECENCY_WINDOW_DAYS}d): {len(recent_posts)}")
        if dedup_dropped:
            lines.append(f"  skipped (already proposed recently): {dedup_dropped}")
        if not candidates:
            lines.append("")
            lines.append("No candidates. Backlog empty.")
            _send(chat_id, "\n".join(lines))
            return True
        top = _griot._pick_top_candidate(candidates, recent_posts)
        lines.append("")
        lines.append("Top pick:")
        lines.append(f"  title: {top['title'][:80]}")
        lines.append(f"  platform: {(top['platform'] or [None])[0]}")
        lines.append(f"  arc_priority: {top.get('arc_priority')}")
        lines.append(f"  arc_phase: {top.get('arc_phase')}")
        lines.append(f"  total_score (Notion): {top.get('total_score')}")
        lines.append(f"  computed_score: {top.get('score'):.1f}")
        lines.append(f"  why: {top.get('why_chosen')}")
        if top.get("hook"):
            lines.append(f"  hook preview: {top['hook'][:160]}")
        lines.append("")
        lines.append("(dry-run: no approval_queue write)")
        _send(chat_id, "\n".join(lines))
    except Exception as e:
        logger.error(f"/griot_dryrun error: {e}", exc_info=True)
        _send(chat_id, f"Griot dryrun failed: {e}")
    return True


# ══════════════════════════════════════════════════════════════
# Task add
# ══════════════════════════════════════════════════════════════

VALID_OWNERS = ("Boubacar", "Coding", "agentsHQ", "Decision")
VALID_SPRINTS = (
    "Backlog",
    "Week 1", "Week 2", "Week 3", "Week 4", "Week 5", "Week 6",
    "Week 7", "Week 8", "Week 9", "Week 10", "Week 11", "Week 12",
    "Archive",
)
NOTION_TASK_DB_ID = os.environ.get("NOTION_TASK_DB_ID", "249bcf1a302980739c26c61cad212477")
NOTION_VERSION = "2022-06-28"


@dataclass
class TaskAddParse:
    ok: bool
    title: str = ""
    owner: str = "Boubacar"
    sprint: str = "Backlog"
    p0: bool = False
    error: str = ""


def _closest_owner(name: str) -> str | None:
    """Case-insensitive prefix or substring match. Returns the canonical owner if 1 match."""
    needle = name.lower()
    matches = [o for o in VALID_OWNERS if needle in o.lower() or o.lower().startswith(needle)]
    if len(matches) == 1:
        return matches[0]
    return None


def parse_task_add(text: str) -> TaskAddParse:
    """Parse `/task add "<title>" [--owner=X] [--sprint=Y] [--p0]`.

    Returns TaskAddParse with ok=True or ok=False+error.
    """
    body = text.strip()
    if body.lower().startswith("/task add"):
        body = body[len("/task add"):].strip()
    else:
        return TaskAddParse(ok=False, error='Expected "/task add" prefix.')

    if not body:
        return TaskAddParse(ok=False, error='Missing title. Usage: /task add "<title>" [--owner=X] [--sprint=Y] [--p0]')

    m = re.match(r'"([^"]*)"\s*(.*)$', body)
    if not m:
        return TaskAddParse(
            ok=False,
            error='Title must be in quotes. Usage: /task add "<title>" [--owner=X] [--sprint=Y] [--p0]',
        )
    title = m.group(1).strip()
    rest = m.group(2).strip()

    if not title:
        return TaskAddParse(ok=False, error="Title cannot be empty.")

    owner = "Boubacar"
    sprint = "Backlog"
    p0 = False

    flag_re = re.compile(r'--(\w+)(?:=("[^"]+"|\S+))?')
    pos = 0
    rest_lower = rest.lower()
    while pos < len(rest):
        m2 = flag_re.search(rest, pos)
        if not m2:
            break
        key = m2.group(1).lower()
        val = m2.group(2)
        if val is not None and val.startswith('"') and val.endswith('"'):
            val = val[1:-1]
        if key == "p0":
            p0 = True
        elif key == "owner":
            if val is None:
                return TaskAddParse(ok=False, error="--owner requires a value")
            cand = _closest_owner(val)
            if cand is None:
                return TaskAddParse(
                    ok=False,
                    error=f'Owner "{val}" not found. Valid: {", ".join(VALID_OWNERS)}.',
                )
            owner = cand
        elif key == "sprint":
            if val is None:
                return TaskAddParse(ok=False, error="--sprint requires a value")
            tail_after = rest[m2.end():]
            tail_match = re.match(r'\s+(\d+)', tail_after)
            if val.lower() == "week" and tail_match:
                val = f"Week {tail_match.group(1)}"
                pos = m2.end() + tail_match.end()
            else:
                pos = m2.end()
            if val not in VALID_SPRINTS:
                return TaskAddParse(
                    ok=False,
                    error=f'Sprint "{val}" not found. Valid: Backlog, Week 1-12, Archive.',
                )
            sprint = val
            continue
        else:
            return TaskAddParse(ok=False, error=f"Unknown flag --{key}. Valid: --owner, --sprint, --p0")
        pos = m2.end()

    return TaskAddParse(ok=True, title=title, owner=owner, sprint=sprint, p0=p0)


def _notion_headers_for_tasks() -> dict:
    token = os.environ.get("NOTION_SECRET")
    if not token:
        raise RuntimeError("NOTION_SECRET not in environment.")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _query_database(database_id: str, filter_body=None, sorts=None) -> list:
    """Thin wrapper to the existing skills.notion_skill helper, importable here for monkeypatching."""
    from skills.notion_skill.notion_tool import query_database
    return query_database(database_id, filter_body=filter_body, sorts=sorts)


def _next_task_id(database_id: str) -> str:
    """Find max T-YYxxx, increment by 1. Year prefix from current UTC year."""
    today_year = datetime.now(timezone.utc).strftime("%y")
    rows = _query_database(
        database_id,
        sorts=[{"timestamp": "created_time", "direction": "descending"}],
    )
    max_n = 0
    prefix = f"T-{today_year}"
    for r in rows[:200]:
        rt = r.get("properties", {}).get("Task ID", {}).get("rich_text", [])
        if not rt:
            continue
        tid = rt[0].get("plain_text", "")
        if tid.startswith(prefix):
            try:
                n = int(tid[len(prefix):])
                if n > max_n:
                    max_n = n
            except ValueError:
                continue
    return f"{prefix}{max_n + 1:03d}"


def _clear_existing_p0(database_id: str) -> None:
    """Patch every P0=true row to P0=false. Single-P0 invariant."""
    rows = _query_database(
        database_id,
        filter_body={"property": "P0", "checkbox": {"equals": True}},
    )
    headers = _notion_headers_for_tasks()
    for r in rows:
        body = {"properties": {"P0": {"checkbox": False}}}
        httpx.patch(
            f"https://api.notion.com/v1/pages/{r['id']}",
            headers=headers,
            json=body,
            timeout=30,
        )


def _top_3_boubacar() -> list:
    """Top 3 active Boubacar tasks for echo. Returns list of dicts {task_id, title, p0}."""
    rows = _query_database(
        NOTION_TASK_DB_ID,
        filter_body={
            "and": [
                {"property": "Owner", "multi_select": {"contains": "Boubacar"}},
                {"property": "Status", "select": {"does_not_equal": "Done"}},
            ]
        },
        sorts=[
            {"property": "P0", "direction": "descending"},
            {"property": "Priority", "direction": "ascending"},
            {"property": "Task ID", "direction": "ascending"},
        ],
    )
    out = []
    for r in rows[:3]:
        props = r.get("properties", {})
        title_arr = props.get("Task", {}).get("title", [])
        title = title_arr[0].get("plain_text", "") if title_arr else ""
        tid_arr = props.get("Task ID", {}).get("rich_text", [])
        task_id = tid_arr[0].get("plain_text", "") if tid_arr else ""
        p0 = bool(props.get("P0", {}).get("checkbox", False))
        out.append({"task_id": task_id, "title": title, "p0": p0})
    return out


def _format_top_3_lines(items: list) -> str:
    if not items:
        return ""
    lines = ["Top 3:"]
    for it in items:
        flag = "P0" if it.get("p0") else "  "
        lines.append(f"  {it.get('task_id', '?')}  {flag}  {it.get('title', '')[:50]}")
    return "\n".join(lines)


def handle_task_add(text: str) -> str:
    """Handle /task add command. Returns Telegram-friendly reply string."""
    parsed = parse_task_add(text)
    if not parsed.ok:
        return parsed.error

    db_id = NOTION_TASK_DB_ID
    try:
        new_id = _next_task_id(db_id)
        if parsed.p0:
            _clear_existing_p0(db_id)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        props = {
            "Task": {"title": [{"text": {"content": parsed.title}}]},
            "Status": {"select": {"name": "Not Started"}},
            "Owner": {"multi_select": [{"name": parsed.owner}]},
            "Sprint": {"multi_select": [{"name": parsed.sprint}]},
            "Task ID": {"rich_text": [{"text": {"content": new_id}}]},
            "Source": {"rich_text": [{"text": {"content": f"Manual: {today}"}}]},
            "P0": {"checkbox": parsed.p0},
        }
        body = {"parent": {"database_id": db_id}, "properties": props}
        httpx.post(
            "https://api.notion.com/v1/pages",
            headers=_notion_headers_for_tasks(),
            json=body,
            timeout=30,
        ).raise_for_status()
    except httpx.HTTPError as e:
        logger.warning(f"handle_task_add: Notion API error ({e})")
        return "Notion API error. Try again in 1 min."

    top3 = _top_3_boubacar()
    reply_lines = [f'Added {new_id}: "{parsed.title}"']
    top3_block = _format_top_3_lines(top3)
    if top3_block:
        reply_lines.append("")
        reply_lines.append(top3_block)
    return "\n".join(reply_lines)


def _cmd_task_add(text: str, chat_id: str) -> bool:
    if not text.lower().startswith("/task add"):
        return False
    from notifier import send_message as _send
    _send(chat_id, handle_task_add(text))
    return True


# ══════════════════════════════════════════════════════════════
# Dream: memory consolidation
# ══════════════════════════════════════════════════════════════

def _cmd_gate_approve(text: str, chat_id: str) -> bool:
    """
    /gate-approve <branch> — approve a Gate-held high-risk branch for merge.

    Writes a marker file under data/gate_approvals/. Gate's next tick reads markers,
    matches against held branches, runs tests + merges + pushes main + deploys.
    Auth: chat_id must equal OWNER_TELEGRAM_CHAT_ID.
    Async by design — does not block the bot handler with a slow merge.
    """
    if not text.lower().startswith("/gate-approve"):
        return False
    import os, json, pathlib
    from datetime import datetime, timezone
    from notifier import send_message as _send

    owner_id = os.environ.get("OWNER_TELEGRAM_CHAT_ID", "")
    if owner_id and str(chat_id) != str(owner_id):
        _send(chat_id, "Not authorized. Gate approvals require owner chat.")
        return True

    parts = text.strip().split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        _send(chat_id, "Usage: /gate-approve <branch-name>")
        return True

    branch = parts[1].strip()
    repo_root = pathlib.Path(os.environ.get("REPO_ROOT", "/app"))
    marker_dir = pathlib.Path(os.environ.get("GATE_DATA_DIR", str(repo_root / "data"))) / "gate_approvals"
    marker_dir.mkdir(parents=True, exist_ok=True)

    marker_name = branch.replace("/", "__") + ".approve.json"
    marker_path = marker_dir / marker_name
    marker_path.write_text(json.dumps({
        "branch": branch,
        "decision": "approve",
        "approved_by": str(chat_id),
        "ts": datetime.now(timezone.utc).isoformat(),
    }, indent=2), encoding="utf-8")

    _send(chat_id, f"Gate approval queued for {branch}. Will process on next tick (within 60s).")
    return True


def _cmd_gate_reject(text: str, chat_id: str) -> bool:
    """
    /gate-reject <branch> — reject a Gate-held branch. Writes a reject marker so
    Gate clears the held state without merging.
    """
    if not text.lower().startswith("/gate-reject"):
        return False
    import os, json, pathlib
    from datetime import datetime, timezone
    from notifier import send_message as _send

    owner_id = os.environ.get("OWNER_TELEGRAM_CHAT_ID", "")
    if owner_id and str(chat_id) != str(owner_id):
        _send(chat_id, "Not authorized. Gate approvals require owner chat.")
        return True

    parts = text.strip().split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        _send(chat_id, "Usage: /gate-reject <branch-name>")
        return True

    branch = parts[1].strip()
    repo_root = pathlib.Path(os.environ.get("REPO_ROOT", "/app"))
    marker_dir = pathlib.Path(os.environ.get("GATE_DATA_DIR", str(repo_root / "data"))) / "gate_approvals"
    marker_dir.mkdir(parents=True, exist_ok=True)

    marker_name = branch.replace("/", "__") + ".reject.json"
    marker_path = marker_dir / marker_name
    marker_path.write_text(json.dumps({
        "branch": branch,
        "decision": "reject",
        "rejected_by": str(chat_id),
        "ts": datetime.now(timezone.utc).isoformat(),
    }, indent=2), encoding="utf-8")

    _send(chat_id, f"Gate rejection queued for {branch}. Branch will be left untouched.")
    return True


def _cmd_dream(text: str, chat_id: str) -> bool:
    if not text.lower().startswith("/dream"):
        return False
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).parent))
    from notifier import send_message as _send
    from dream_handler import run_dream_async, _apply_decision, PROPOSAL_FILE

    parts = text.strip().split()

    # /dream approve [except x, y]
    if len(parts) >= 2 and parts[1].lower() == "approve":
        excluded: set = set()
        if len(parts) >= 4 and parts[2].lower() == "except":
            excluded = {f.strip() for f in " ".join(parts[3:]).split(",") if f.strip()}
        _apply_decision("APPROVE", excluded, chat_id)
        return True

    # /dream reject
    if len(parts) >= 2 and parts[1].lower() == "reject":
        _apply_decision("REJECT", set(), chat_id)
        return True

    # /dream status
    if len(parts) >= 2 and parts[1].lower() == "status":
        if PROPOSAL_FILE.exists():
            summary = PROPOSAL_FILE.read_text(encoding="utf-8")[:1500]
            _send(chat_id, f"Active dream proposal:\n\n{summary}")
        else:
            _send(chat_id, "No active dream proposal. Run /dream to start a new scan.")
        return True

    # /dream [N] — run scan (optional session count)
    n_sessions = 30
    if len(parts) >= 2:
        try:
            n_sessions = int(parts[1])
        except ValueError:
            pass
    run_dream_async(chat_id, n_sessions=n_sessions)
    return True




# ══════════════════════════════════════════════════════════════
# On-demand digest + publish triggers
# ══════════════════════════════════════════════════════════════

def _cmd_digest(text: str, chat_id: str) -> bool:
    if text.lower().strip() != '/digest':
        return False
    owner_id = os.environ.get('OWNER_TELEGRAM_CHAT_ID', '')
    from notifier import send_message as _send
    if owner_id and str(chat_id) != str(owner_id):
        _send(chat_id, 'Not authorized.')
        return True
    snippet = _get_latest_synthesis_snippet()
    if snippet:
        _send_memory(chat_id, snippet)
    _send(chat_id, 'Digest firing. Full morning report incoming (~30s).')

    def _do_digest():
        try:
            from scheduler import _run_morning_digest
            _run_morning_digest()
        except Exception as e:
            logger.error(f'/digest error: {e}')
            _send(chat_id, f'Digest failed: {e}')

    threading.Thread(target=_do_digest, daemon=True).start()
    return True


def _cmd_publish(text: str, chat_id: str) -> bool:
    if text.lower().strip() != '/publish':
        return False
    owner_id = os.environ.get('OWNER_TELEGRAM_CHAT_ID', '')
    from notifier import send_message as _send
    if owner_id and str(chat_id) != str(owner_id):
        _send(chat_id, 'Not authorized.')
        return True
    _send(chat_id, 'Auto-publisher tick fired.')

    def _do_publish():
        try:
            from auto_publisher import auto_publisher_tick
            auto_publisher_tick()
        except Exception as e:
            logger.error(f'/publish error: {e}')
            _send(chat_id, f'Publish tick failed: {e}')

    threading.Thread(target=_do_publish, daemon=True).start()
    return True


def _cmd_multiply(text: str, chat_id: str) -> bool:
    if not text.lower().startswith("/multiply"):
        return False
    if len(text) > len("/multiply") and not text[len("/multiply")].isspace():
        return False
    from notifier import send_message as _send
    parts = text.strip().split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        _send(chat_id, "Usage: /multiply <notion_page_id_or_url>")
        return True
    source = parts[1].strip()
    _send(chat_id, f"Multiplier fired for {source[:80]}.")

    def _do_multiply():
        try:
            try:
                from content_multiplier_crew import multiply_from_page_id, multiply_source
            except ImportError:
                from orchestrator.content_multiplier_crew import multiply_from_page_id, multiply_source
            # URL -> direct multiply. Otherwise treat as Notion page_id and use page-extraction path.
            if "://" in source or source.lower().startswith(("http", "www.")):
                multiply_source(source)
            else:
                multiply_from_page_id(source)
        except Exception as e:
            logger.error(f'/multiply error: {e}', exc_info=True)
            _send(chat_id, f"Multiplier failed: {e}")

    threading.Thread(target=_do_multiply, daemon=True).start()
    return True

# ══════════════════════════════════════════════════════════════
# SW pipeline trigger
# ══════════════════════════════════════════════════════════════

def _cmd_sw(text: str, chat_id: str) -> bool:
    if text.lower().strip() not in ('/sw',):
        return False
    from notifier import send_message as _send
    _send(chat_id, 'SW pipeline fired. Lead harvest + enrichment running (~2 min).')

    def _do_sw():
        try:
            from scheduler import _run_daily_harvest
            _run_daily_harvest()
            _send(chat_id, 'SW harvest complete. Check Telegram report.')
        except Exception as e:
            logger.error(f'/sw error: {e}')
            _send(chat_id, f'SW pipeline failed: {e}')

    threading.Thread(target=_do_sw, daemon=True).start()
    return True

# ── Memory commands (/remember, /query) ───────────────────────────────────────

def _send_memory(chat_id: str, msg: str) -> None:
    from notifier import send_message
    send_message(chat_id, msg)


def _get_latest_synthesis_snippet() -> str:
    """Return first 300 chars of latest weekly synthesis, or empty string."""
    try:
        import psycopg2, os
        conn = psycopg2.connect(
            host=os.environ.get("POSTGRES_HOST", "agentshq-postgres-1"),
            database=os.environ.get("POSTGRES_DB", "postgres"),
            user=os.environ.get("POSTGRES_USER", "postgres"),
            password=os.environ.get("POSTGRES_PASSWORD", ""),
            port=5432,
        )
        cur = conn.cursor()
        cur.execute("SELECT date, content FROM weekly_synthesis ORDER BY date DESC LIMIT 1")
        row = cur.fetchone()
        conn.close()
        if not row:
            return ""
        return f"Last synthesis ({row[0]}): {row[1][:280]}..."
    except Exception:
        return ""


def _memory_write(model):
    from orchestrator.memory_store import write
    return write(model)


def _memory_query_text(text: str, **kwargs):
    from orchestrator.memory_store import query_text
    return query_text(text, **kwargs)


def _memory_query_filter(**kwargs):
    from orchestrator.memory_store import query_filter
    return query_filter(**kwargs)


def _memory_synthesize(rows: list, question: str) -> str:
    from llm_helpers import call_llm
    rows_text = "\n\n".join(
        f"[{r['category']}] {r.get('title') or ''}\n{r['content'][:400]}"
        for r in rows[:15]
    )
    prompt = f"""You are the agentsHQ memory query agent.

Question: {question}

Memory records:
{rows_text}

Answer the question using only the provided records. Be direct and specific.
If no records are relevant, say so plainly. No padding."""
    response = call_llm(
        messages=[{"role": "user", "content": prompt}],
        model="anthropic/claude-haiku-4-5",
        max_tokens=600,
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


def _cmd_remember(text: str, chat_id: str) -> bool:
    if not text.lower().startswith("/remember"):
        return False
    parts = text.strip().split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        _send_memory(chat_id, "Usage: /remember <text>\nExample: /remember Build roofing page for SW soon")
        return True
    content = parts[1].strip()
    from orchestrator.memory_models import Idea
    model = Idea(
        title=content[:100],
        context="Captured via Telegram /remember",
        pipeline="general",
        priority="soon",
        source="telegram",
    )
    row_id = _memory_write(model)
    if row_id:
        _send_memory(chat_id, f"Saved to memory (id={row_id}). Query with: /query {content[:40]}")
    else:
        _send_memory(chat_id, "Saved locally (DB write failed silently — check logs).")
    return True


def _cmd_query(text: str, chat_id: str) -> bool:
    if not text.lower().startswith("/query"):
        return False
    parts = text.strip().split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        _send_memory(chat_id, (
            "Usage:\n"
            "  /query <natural language question>\n"
            "  /query --filter category=<cat>\n"
            "  /query --filter pipeline=<pipe>\n"
            "  /query --filter entity=<entity_ref>\n\n"
            "Examples:\n"
            "  /query tell me about Elevate Roofing\n"
            "  /query --filter category=hard_rule"
        ))
        return True

    query_str = parts[1].strip()

    # Synthesis mode: return latest weekly synthesis
    if query_str.startswith("--synthesis"):
        try:
            import psycopg2, os
            conn = psycopg2.connect(
                host=os.environ.get("POSTGRES_HOST", "agentshq-postgres-1"),
                database=os.environ.get("POSTGRES_DB", "postgres"),
                user=os.environ.get("POSTGRES_USER", "postgres"),
                password=os.environ.get("POSTGRES_PASSWORD", ""),
                port=5432,
            )
            cur = conn.cursor()
            cur.execute("SELECT date, content FROM weekly_synthesis ORDER BY date DESC LIMIT 1")
            row = cur.fetchone()
            conn.close()
            if row:
                _send_memory(chat_id, f"Weekly synthesis ({row[0]}):\n\n{row[1][:3000]}")
            else:
                _send_memory(chat_id, "No weekly synthesis yet. Runs Sunday 20:00 MT.")
        except Exception as e:
            _send_memory(chat_id, f"Could not fetch synthesis: {e}")
        return True

    if query_str.startswith("--filter"):
        filter_str = query_str[len("--filter"):].strip()
        kwargs = {}
        for token in filter_str.split():
            if "=" in token:
                k, v = token.split("=", 1)
                k = k.strip()
                if k == "category":
                    kwargs["category"] = v.strip()
                elif k == "pipeline":
                    kwargs["pipeline"] = v.strip()
                elif k == "entity":
                    kwargs["entity_ref"] = v.strip()
        rows = _memory_query_filter(**kwargs)
        if not rows:
            _send_memory(chat_id, "No records found for that filter.")
            return True
        lines = [f"Found {len(rows)} record(s):"]
        for r in rows[:10]:
            title = r.get("title") or r["category"]
            snippet = r["content"][:120].replace("\n", " ")
            lines.append(f"• [{r['category']}] {title}: {snippet}")
        _send_memory(chat_id, "\n".join(lines))
        return True

    rows = _memory_query_text(query_str)
    if not rows:
        _send_memory(chat_id, f"No memory records found for: {query_str}")
        return True

    try:
        answer = _memory_synthesize(rows, query_str)
        _send_memory(chat_id, answer)
    except Exception as e:
        logger.warning(f"/query LLM synthesis failed, returning raw rows: {e}")
        lines = [f"(synthesis unavailable) Top {min(5, len(rows))} records:"]
        for r in rows[:5]:
            title = r.get("title") or r["category"]
            snippet = r["content"][:150].replace("\n", " ")
            lines.append(f"• [{r['category']}] {title}: {snippet}")
        _send_memory(chat_id, "\n".join(lines))
    return True


# ══════════════════════════════════════════════════════════════
# Dispatcher (order matters: longest prefix first to avoid collisions)
# ══════════════════════════════════════════════════════════════

def _cmd_callsheet(text: str, chat_id: str) -> bool:
    if text.lower().strip() != '/callsheet':
        return False
    owner_id = os.environ.get('OWNER_TELEGRAM_CHAT_ID', '')
    from notifier import send_message as _send
    if owner_id and str(chat_id) != str(owner_id):
        _send(chat_id, 'Not authorized.')
        return True

    _OPENERS = {
        'no_website': "I went looking for {name} on Google and couldn't find a website.",
        'low_reviews': "I was looking at {name} on Google and noticed you only have {review_count} reviews.",
        'chatgpt': 'Open ChatGPT and type: "who is the best {niche} in {city}?" — if {name} doesn\'t show up, someone ready to hire just called a competitor.',
        'generic': 'AI tools like ChatGPT are now how people find local businesses. {name} may not be showing up.',
    }

    try:
        import sys as _sys; _sys.path.insert(0, '/app')
        try:
            from db import get_crm_connection as _crm
        except ImportError:
            from orchestrator.db import get_crm_connection as _crm
        conn = _crm()
        cur = conn.cursor()
        cur.execute("""
            SELECT name, phone, city, niche, gmb_opener, review_count
            FROM leads
            WHERE source LIKE 'signal_works%'
              AND sequence_touch = 1
              AND phone IS NOT NULL AND phone != ''
              AND email_drafted_at::date = CURRENT_DATE
            ORDER BY email_drafted_at ASC
            LIMIT 20
        """)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()

        if not rows:
            _send(chat_id, 'No SW leads emailed today with phone numbers. Check again after morning runner fires.')
            return True

        lines = [f"SW CALL SHEET — {len(rows)} leads emailed today\n"]
        for i, r in enumerate(rows, 1):
            opener_tpl = _OPENERS.get(r.get('gmb_opener') or 'generic', _OPENERS['generic'])
            opener = opener_tpl.format(
                name=r.get('name', 'this business'),
                review_count=int(r.get('review_count', 0) or 0),
                niche=r.get('niche', 'business') or 'business',
                city=r.get('city', 'your area') or 'your area',
            )
            lines.append(
                f"{i}. {r.get('name', '?')} — {r.get('phone', '?')}\n"
                f"   {r.get('city', '')} | {r.get('niche', '')}\n"
                f"   Opener: {opener}"
            )
        _send(chat_id, '\n\n'.join(lines))
    except Exception as e:
        logger.error(f'/callsheet error: {e}')
        from notifier import send_message as _send2
        _send2(chat_id, f'callsheet failed: {e}')
    return True


def _cmd_shipped(text: str, chat_id: str) -> bool:
    """/shipped <codename> <mid> -- mark a milestone shipped in the milestones DB."""
    if not text.lower().startswith("/shipped"):
        return False
    from notifier import send_message as _send
    parts = text.strip().split()
    if len(parts) < 3:
        _send(chat_id, "Usage: `/shipped <codename> <mid>`\nExample: `/shipped atlas M5`\nCodenames: atlas, echo, compass, studio, harvest")
        return True
    codename = parts[1].lower()
    mid = parts[2]
    if codename not in {"atlas", "echo", "compass", "studio", "harvest"}:
        _send(chat_id, f"Unknown codename `{codename}`. Valid: atlas, echo, compass, studio, harvest")
        return True
    try:
        import sys as _sys, pathlib as _pl
        _sys.path.insert(0, str(_pl.Path(__file__).parent))
        from atlas_dashboard import flip_milestone
        r = flip_milestone(codename, mid, "shipped")
        if r["ok"]:
            _send(chat_id, f"Shipped: `{codename}/{mid}` ({r['old_status']} -> shipped). Roadmap updates within 60s.")
        else:
            _send(chat_id, f"Could not mark shipped: {r['error']}")
    except Exception as e:
        _send(chat_id, f"/shipped error: {e}")
    return True


def _cmd_milestones(text: str, chat_id: str) -> bool:
    """/milestones <codename> [status] -- list milestones from DB."""
    if not text.lower().startswith("/milestones"):
        return False
    from notifier import send_message as _send
    parts = text.strip().split()
    if len(parts) < 2:
        _send(chat_id, "Usage: `/milestones <codename> [status]`\nExample: `/milestones atlas active`")
        return True
    codename = parts[1].lower()
    status_filter = parts[2].lower() if len(parts) >= 3 else None
    try:
        import sys as _sys, pathlib as _pl
        _sys.path.insert(0, str(_pl.Path(__file__).parent))
        from memory import _pg_conn
        conn = _pg_conn()
        cur = conn.cursor()
        if status_filter:
            cur.execute(
                "SELECT mid, title, status FROM milestones WHERE codename=%s AND status=%s ORDER BY id",
                (codename, status_filter),
            )
        else:
            cur.execute(
                "SELECT mid, title, status FROM milestones WHERE codename=%s ORDER BY id",
                (codename,),
            )
        rows = cur.fetchall()
        conn.close()
        STATUS_ICON = {
            "shipped": "OK", "active": ">>", "blocked": "[]",
            "queued": "..", "deferred": "--", "descoped": "XX",
        }
        if not rows:
            msg = f"No milestones for `{codename}`"
            if status_filter:
                msg += f" with status `{status_filter}`"
            _send(chat_id, msg)
            return True
        lines = [f"*{codename.upper()}*" + (f" ({status_filter})" if status_filter else "") + ":"]
        for row in rows:
            mid_v  = row["mid"]    if isinstance(row, dict) else row[0]
            title_v = row["title"] if isinstance(row, dict) else row[1]
            st_v   = row["status"] if isinstance(row, dict) else row[2]
            icon = STATUS_ICON.get(st_v, "?")
            lines.append(f"[{icon}] `{mid_v}` {title_v[:50]}")
        _send(chat_id, "\n".join(lines))
    except Exception as e:
        _send(chat_id, f"/milestones error: {e}")
    return True


# Ordered by specificity. /heartbeat_status must come before a hypothetical
# /heartbeat. /autonomy_status, /pause_autonomy, /resume_autonomy each have
# unique prefixes so order within the Phase 0 group does not matter. /status
# has a guard against /status_foo inside its own handler.
_COMMANDS = [
    _cmd_gate_approve,  # must come before _cmd_approve (longer prefix)
    _cmd_gate_reject,   # must come before _cmd_reject (longer prefix)
    _cmd_dream,
    _cmd_task_add,
    _cmd_heartbeat_status,
    _cmd_trigger_heartbeat,
    _cmd_griot_dryrun,
    _cmd_autonomy_status,
    _cmd_pause_autonomy,
    _cmd_resume_autonomy,
    _cmd_queue,
    _cmd_approve,
    _cmd_reject,
    _cmd_outcomes,
    _cmd_callsheet,
    _cmd_shipped,
    _cmd_milestones,
    _cmd_remember,
    _cmd_query,
    _cmd_digest,
    _cmd_publish,
    _cmd_multiply,
    _cmd_sw,
    _cmd_scan_drive,
    _cmd_lessons,
    _cmd_purge_lesson,
    _cmd_status,
    _cmd_projects,
    _cmd_cost,
    _cmd_switch,
]


def dispatch_command(text: str, chat_id: str) -> bool:
    """
    Try each command handler in order. Returns True as soon as one handles it.
    Returns False if no command matched (caller falls through to feedback + classify).
    """
    if not text.startswith("/"):
        return False
    for handler in _COMMANDS:
        try:
            if handler(text, chat_id):
                return True
        except Exception as e:
            logger.error(f"Command handler {handler.__name__} raised: {e}", exc_info=True)
            # Do not eat the command - return True so caller does not also dispatch it
            return True
    return False
