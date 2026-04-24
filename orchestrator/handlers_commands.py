"""
handlers_commands.py - Slash command dispatch for Telegram.

One function per command, grouped by era:
- Original ops commands (pre-autonomy): /cost, /projects, /status, /lessons,
  /purge-lesson, /scan-drive, /switch
- Phase 0 autonomy rails:                /autonomy_status, /pause_autonomy,
  /resume_autonomy, /spend
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
import threading
from datetime import datetime, timezone

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
        days = int(parts[1]) if len(parts) > 1 else 7
    except ValueError:
        days = 7
    try:
        conn = _pg_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    COUNT(*) AS total_calls,
                    ROUND(SUM(cost_usd)::numeric, 4) AS total_usd,
                    ROUND(SUM(cost_usd) FILTER (WHERE ts > NOW() - INTERVAL '24 hours')::numeric, 4) AS today_usd,
                    COUNT(DISTINCT council_run_id) FILTER (WHERE council_run_id IS NOT NULL) AS council_runs
                FROM llm_calls
                WHERE ts > NOW() - INTERVAL '%s days'
                """,
                (days,),
            )
            total_calls, total_usd, today_usd, council_runs = cur.fetchone()
            cur.execute(
                """
                SELECT agent_name, COUNT(*) AS calls, ROUND(SUM(cost_usd)::numeric, 4) AS usd
                FROM llm_calls
                WHERE ts > NOW() - INTERVAL '%s days' AND agent_name IS NOT NULL
                GROUP BY agent_name
                ORDER BY usd DESC NULLS LAST
                LIMIT 8
                """,
                (days,),
            )
            top = cur.fetchall()
            cur.close()
        finally:
            conn.close()
        lines = [
            f"LLM spend (last {days} days):",
            f"  ${total_usd or 0:.4f} total over {total_calls or 0} calls",
            f"  ${today_usd or 0:.4f} in last 24h",
            f"  {council_runs or 0} council runs",
            "",
            "Top agents by spend:",
        ]
        for agent, calls, usd in top:
            lines.append(f"  ${usd or 0:.4f}  {agent}  ({calls} calls)")
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


def _cmd_spend(text: str, chat_id: str) -> bool:
    if not text.lower().startswith("/spend"):
        return False
    from notifier import send_message as _send
    from autonomy_guard import get_guard
    g = get_guard()
    snap = g.snapshot()
    lines = [f"Autonomous spend today: ${snap.spent_today_usd:.4f} / ${snap.cap_usd:.2f}"]
    lines.append(f"Remaining: ${snap.remaining_usd:.4f}")
    if snap.per_crew:
        lines.append("")
        lines.append("By crew:")
        for crew, usd in sorted(snap.per_crew.items(), key=lambda kv: -kv[1]):
            lines.append(f"  {crew}: ${usd:.4f}")
    else:
        lines.append("(no autonomous calls yet today)")
    _send(chat_id, "\n".join(lines))
    return True


# ══════════════════════════════════════════════════════════════
# Phase 1: approval queue
# ══════════════════════════════════════════════════════════════

def _cmd_queue(text: str, chat_id: str) -> bool:
    if not text.lower().startswith("/queue"):
        return False
    from notifier import send_message as _send
    from approval_queue import list_pending
    rows = list_pending(limit=10)
    if not rows:
        _send(chat_id, "Queue empty. No pending proposals.")
        return True
    lines = [f"Pending proposals ({len(rows)}):"]
    now = datetime.now(timezone.utc)
    for r in rows:
        age_min = int((now - r.ts_created).total_seconds() / 60) if r.ts_created else 0
        lines.append(f"  #{r.id}  {r.crew_name}  {r.proposal_type}  ({age_min}m)")
    _send(chat_id, "\n".join(lines))
    return True


def _cmd_approve(text: str, chat_id: str) -> bool:
    if not text.lower().startswith("/approve"):
        return False
    from notifier import send_message as _send
    from approval_queue import approve as _aq_approve
    parts = text.strip().split(maxsplit=2)
    if len(parts) < 2:
        _send(chat_id, "Usage: /approve <id> [note]")
        return True
    try:
        qid = int(parts[1])
    except ValueError:
        _send(chat_id, f"Invalid queue id: {parts[1]}")
        return True
    note = parts[2] if len(parts) > 2 else None
    row = _aq_approve(qid, note=note)
    if row is None:
        _send(chat_id, f"Queue #{qid}: not found or already decided.")
    else:
        _send(chat_id, f"Queue #{qid}: approved.")
    return True


def _cmd_reject(text: str, chat_id: str) -> bool:
    if not text.lower().startswith("/reject"):
        return False
    from notifier import send_message as _send
    from approval_queue import reject as _aq_reject, KNOWN_FEEDBACK_TAGS
    parts = text.strip().split(maxsplit=3)
    if len(parts) < 2:
        _send(chat_id, "Usage: /reject <id> [tag] [note]")
        return True
    try:
        qid = int(parts[1])
    except ValueError:
        _send(chat_id, f"Invalid queue id: {parts[1]}")
        return True
    tag = None
    note = None
    if len(parts) > 2:
        if parts[2].lower() in KNOWN_FEEDBACK_TAGS:
            tag = parts[2].lower()
            note = parts[3] if len(parts) > 3 else None
        else:
            note = " ".join(parts[2:])
    row = _aq_reject(qid, note=note, feedback_tag=tag)
    if row is None:
        _send(chat_id, f"Queue #{qid}: not found or already decided.")
    else:
        _send(chat_id, f"Queue #{qid}: rejected. Tag: {tag or 'none'}")
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
# Dispatcher (order matters: longest prefix first to avoid collisions)
# ══════════════════════════════════════════════════════════════

# Ordered by specificity. /heartbeat_status must come before a hypothetical
# /heartbeat. /autonomy_status, /pause_autonomy, /resume_autonomy each have
# unique prefixes so order within the Phase 0 group does not matter. /status
# has a guard against /status_foo inside its own handler.
_COMMANDS = [
    _cmd_heartbeat_status,
    _cmd_trigger_heartbeat,
    _cmd_autonomy_status,
    _cmd_pause_autonomy,
    _cmd_resume_autonomy,
    _cmd_spend,
    _cmd_queue,
    _cmd_approve,
    _cmd_reject,
    _cmd_outcomes,
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
