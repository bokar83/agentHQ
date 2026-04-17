import threading
import logging
from typing import Optional
from constants import SAVE_REQUIRED_TASK_TYPES
from engine import run_orchestrator

logger = logging.getLogger("agentsHQ.worker")

def _run_background_job(
    task: str,
    from_number: str,
    session_key: str,
    job_id: str,
    classification: dict = None,
) -> None:
    """
    Background worker: runs the crew, sends progress pings, saves output,
    and delivers the final result to Telegram.
    Called via FastAPI BackgroundTasks.
    """
    from notifier import send_progress_ping, send_result, send_message
    from saver import save_to_github, save_to_drive

    chat_id = from_number

    # Register job in queue
    try:
        from memory import create_job, update_job
        create_job(job_id, session_key, from_number, task)
    except Exception as e:
        logger.warning(f"Job {job_id}: could not register in queue: {e}")

    # ── Progress ping timer ──────────────────────────────────
    _stop_ping = threading.Event()

    def _ping_loop():
        # First ping after 60s
        if _stop_ping.wait(60):
            return
        send_progress_ping(chat_id)
        # Subsequent pings every 5 min
        if _stop_ping.wait(300):
            return
        send_progress_ping(chat_id)
        # Watchdog: 10 min total
        if not _stop_ping.wait(300):
            send_message(chat_id, "⚠️ Task is taking longer than expected (10+ min). It may be stuck.")
            _stop_ping.set()

    ping_thread = threading.Thread(target=_ping_loop, daemon=True)
    ping_thread.start()

    result = {}
    try:
        # ── Run the engine ─────────────────────────────────────
        result = run_orchestrator(
            task_request=task,
            from_number=from_number,
            session_key=session_key,
        )

        summary     = result.get("result", "")
        task_type   = result.get("task_type", "unknown")
        title       = result.get("title", task[:80])
        deliverable = result.get("deliverable", summary)

        # ── Save ─────────────────────────────────────────────
        github_url = ""
        drive_url  = ""
        if task_type in SAVE_REQUIRED_TASK_TYPES:
            github_url = save_to_github(title, task_type, deliverable)
            drive_url  = save_to_drive(title, task_type, deliverable)
        else:
            logger.info(f"Job {job_id}: task_type '{task_type}' is query-only — skipping save")

        # ── Deliver ──────────────────────────────────────────
        send_result(chat_id, summary, drive_url, github_url)
        try:
            update_job(job_id, status="completed", result=summary)
        except Exception as e:
            logger.warning(f"Job {job_id}: could not update job status: {e}")

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        send_message(chat_id, f"❌ Task failed: {e}")
        try:
            update_job(job_id, status="failed", result=str(e))
        except:
            pass
    finally:
        _stop_ping.set()
