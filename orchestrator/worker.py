"""
worker.py - Background job execution.

_run_background_job is called out-of-band (thread pool or background task) to:
  1. Register the job in the job queue.
  2. Start a progress-ping watchdog.
  3. Run the orchestrator (crew dispatch).
  4. Save output to GitHub + Drive for save-required task types.
  5. Deliver the result to Telegram.
  6. Record _last_completed_job so later praise/critique can pair with it.
  7. Compound email follow-up if classification asked for one.
  8. Hunter report email for hunter_task.
  9. _trigger_evolution (OpenSpace) in a daemon thread after success.
 10. extract_and_save_learnings in a daemon thread after success (gated).

Background job runner for async /run endpoint.
"""
import logging
import os
import threading
from datetime import datetime

from constants import SAVE_REQUIRED_TASK_TYPES, MEMORY_GATED_TASK_TYPES
from engine import run_orchestrator
from state import _last_completed_job

logger = logging.getLogger("agentsHQ.worker")

# OpenSpace Evolution Hook - lazy import so worker module loads even when
# the skill is unavailable in a dev env.
try:
    from skills.openspace_skill.openspace_tool import openspace_tool
except ImportError:
    openspace_tool = None  # type: ignore[assignment]


def _trigger_evolution(task_instruction: str, result_output: str) -> None:
    """
    Run OpenSpace evolution in a new event loop. Logs entry/skip/exit so we
    can tell from docker logs whether the hook is actually firing.
    """
    import asyncio

    loop = None
    try:
        if os.environ.get("DISABLE_EVOLUTION") == "true":
            logger.info("Evolution skipped: DISABLE_EVOLUTION=true")
            return
        if openspace_tool is None:
            logger.info("Evolution skipped: openspace_tool not loaded")
            return
        if len(task_instruction) <= 20 and len(result_output) <= 100:
            logger.info(
                "Evolution skipped: task/result below threshold "
                f"(task={len(task_instruction)} chars, result={len(result_output)} chars)"
            )
            return

        logger.info(
            f"Evolution started: task={len(task_instruction)} chars, "
            f"result={len(result_output)} chars"
        )
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(openspace_tool.execute_async(
            command="evolve",
            task_instruction=f"Task: {task_instruction}\n\nResult:\n{result_output}",
        ))
        logger.info("Evolution complete")
    except Exception as e:
        logger.error(f"Evolution failed: {e}", exc_info=True)
    finally:
        if loop is not None:
            loop.close()


def _run_background_job(
    task: str,
    from_number: str,
    session_key: str,
    job_id: str,
    classification: dict = None,
) -> None:
    """
    Background worker: runs the crew, sends progress pings, saves output,
    and delivers the final result to Telegram. Runs in a thread pool.
    """
    from notifier import send_progress_ping, send_result, send_message
    from saver import save_to_github, save_to_drive

    chat_id = from_number  # from_number IS the Telegram chat ID

    # Register job in queue so Telegram tasks are traceable
    try:
        from memory import create_job, update_job
        create_job(job_id, session_key, from_number, task)
    except Exception as e:
        logger.warning(f"Job {job_id}: could not register in queue: {e}")

    # ── Progress ping timer ──────────────────────────────────
    # First ping at 60s so user knows it is working, then every 5 min.
    # Watchdog at 10 min total: if still running, warn and bail.
    _stop_ping = threading.Event()

    def _ping_loop():
        if _stop_ping.wait(60):
            return
        send_progress_ping(chat_id)
        if _stop_ping.wait(300):
            return
        send_progress_ping(chat_id)
        if not _stop_ping.wait(300):
            send_message(
                chat_id,
                "Task is taking longer than expected (10+ min). It may be stuck, please try again or check with the team.",
            )
            _stop_ping.set()

    ping_thread = threading.Thread(target=_ping_loop, daemon=True)
    ping_thread.start()

    result: dict = {}
    try:
        # ── Run the crew ─────────────────────────────────────
        result = run_orchestrator(
            task_request=task,
            from_number=from_number,
            session_key=session_key,
        )

        summary = result.get("result", "")
        task_type = result.get("task_type", "unknown")
        title = result.get("title", task[:80])
        deliverable = result.get("deliverable", summary)

        # ── Save (only for tasks that produce tangible artifacts) ─────
        github_url = ""
        drive_url = ""
        if task_type in SAVE_REQUIRED_TASK_TYPES:
            github_url = save_to_github(title, task_type, deliverable)
            drive_url = save_to_drive(title, task_type, deliverable)
        else:
            logger.info(f"Job {job_id}: task_type '{task_type}' is query-only, skipping Drive/GitHub save")

        # ── Deliver ──────────────────────────────────────────
        send_result(chat_id, summary, drive_url, github_url)
        try:
            update_job(job_id, status="completed", result=summary)
        except Exception as e:
            logger.warning(f"Job {job_id}: could not update job status to completed: {e}")

        # ── Record last completed job for feedback pairing ────────────
        _last_completed_job[chat_id] = {
            "job_id": job_id,
            "task_type": task_type,
            "task_request": task,
            "result_summary": summary[:1000],
            "delivered_at": datetime.utcnow(),
        }

        # ── Compound request: email follow-up ────────────────────────
        # If the classification flagged has_email_followup, spin a minimal
        # GWS crew to draft the summary email after the main task. Skipped
        # for chat, gws_task, and crm_outreach where email is implicit.
        has_email_followup = (classification or {}).get("has_email_followup", False)
        if has_email_followup and task_type not in ("chat", "gws_task", "crm_outreach"):
            try:
                from crews import build_gws_crew
                email_task_text = (
                    f"Create a Gmail draft to bokar83@gmail.com, catalystworks.ai@gmail.com, and boubacar@catalystworks.consulting "
                    f"with subject 'agentsHQ Result: {title[:60]}'. "
                    f"Body: Format the following result as clean HTML with a header, "
                    f"bullet points for key findings, and a closing note. "
                    f"Result to format:\n\n{summary[:3000]}"
                )
                email_crew = build_gws_crew(email_task_text)
                email_crew.kickoff()
                send_message(chat_id, "Email draft created in your Gmail, go check it.")
                logger.info(f"Compound email follow-up draft created for job {job_id}")
            except Exception as e:
                logger.warning(f"Compound email follow-up failed (non-fatal): {e}")

        # ── Hunter report email ──────────────────────────────────────
        if task_type == "hunter_task":
            try:
                from notifier import send_hunter_report
                send_hunter_report(leads_output=deliverable, scoreboard=summary)
                logger.info("Hunter report emailed to Boubacar.")
            except Exception as e:
                logger.warning(f"Hunter email failed (non-fatal): {e}")

    except Exception as e:
        logger.error(f"Background job {job_id} failed: {e}", exc_info=True)
        try:
            send_message(chat_id, f"Sorry, something went wrong with your task. Error: {str(e)[:200]}")
        except Exception:
            logger.critical(f"Background job {job_id}: result delivery AND error notification both failed. User received nothing.")
        try:
            update_job(job_id, status="failed", result=str(e))
        except Exception:
            pass
    finally:
        _stop_ping.set()  # cancel ping loop regardless of outcome

        # ── Evolution (self-learning) ────────────────────────────────
        # Runs in a daemon thread so it never blocks job completion.
        try:
            if result.get("success"):
                threading.Thread(
                    target=_trigger_evolution,
                    args=(task, result.get("full_output", "")),
                    daemon=True,
                ).start()
        except Exception as e:
            logger.warning(f"Evolution trigger failed: {e}")

        # ── Learning extraction (gated) ──────────────────────────────
        # Fires on success + MEMORY_LEARNING_ENABLED + gated task types.
        try:
            if (
                result.get("success")
                and os.environ.get("MEMORY_LEARNING_ENABLED", "false").lower() == "true"
                and result.get("task_type", "") in MEMORY_GATED_TASK_TYPES
            ):
                from memory import extract_and_save_learnings
                threading.Thread(
                    target=extract_and_save_learnings,
                    args=(task, result.get("task_type", "unknown"), result.get("result", "")[:1000]),
                    daemon=True,
                ).start()
        except Exception as e:
            logger.warning(f"Learning extraction trigger failed (non-fatal): {e}")
