import os
import json
import asyncio
import logging
import threading
import httpx
from datetime import datetime
from typing import Optional

from state import _last_completed_job, _active_project
from engine import run_orchestrator
from constants import SAVE_REQUIRED_TASK_TYPES
from handlers_chat import handle_feedback
from handlers_doc import handle_doc_emoji

logger = logging.getLogger("agentsHQ.handlers")

def run_chat(message: str, session_key: str = "default") -> dict:
    """Direct chat response — runs the base agent without complex orchestration."""
    from crewai import Agent, Task, Crew
    
    agent = Agent(
        role="Catalyst Assistant",
        goal="Provide fast, helpful, and accurate assistance to Boubacar.",
        backstory="You are the core interface of agentsHQ. You are professional, concise, and efficient.",
        allow_delegation=False,
        verbose=True
    )
    
    task = Task(
        description=message,
        agent=agent,
        expected_output="A helpful and concise response."
    )
    
    crew = Crew(agents=[agent], tasks=[task], verbose=True)
    result = crew.kickoff()
    result_str = result.raw if hasattr(result, 'raw') else str(result)
    
    return {"success": True, "result": result_str, "task_type": "chat"}

async def process_telegram_update(update: dict):
    """Unified processor for Telegram updates. Ported from monolithic orchestrator.py."""
    
    from notifier import send_message as _send, send_briefing
    from router import classify_task, extract_metadata
    from worker import _run_background_job
    
    message = update.get("message") or update.get("edited_message")
    if not message:
        return

    text = message.get("text", "").strip()
    chat_id = str(message.get("chat", {}).get("id", ""))
    sender_id = str(message.get("from", {}).get("id", ""))

    if not text or not chat_id:
        return

    # 1. Sender Authentication (Fail-Closed)
    allowed_raw = os.environ.get("ALLOWED_USER_IDS", "")
    allowed_ids = {uid.strip() for uid in allowed_raw.split(",") if uid.strip()}
    if allowed_ids and sender_id not in allowed_ids:
        _send(chat_id, "Sorry, you are not authorised to use this bot.")
        logger.warning(f"Unauthorised access attempt: {sender_id}")
        return

    # 2. Doc Routing Emoji / Command Check
    EMOJI_COMMANDS = ("✅", "✏️", "🆕", "❌", "➕")
    TEXT_ALIASES = {"yes": "✅", "confirm": "✅", "approved": "✅", "reject": "❌", "edit": "✏️"}
    
    matched_emoji = next((e for e in EMOJI_COMMANDS if text.startswith(e)), None)
    if not matched_emoji:
        first_word = text.lower().split()[0] if text else ""
        matched_emoji = TEXT_ALIASES.get(first_word)

    if matched_emoji:
        reply_id = message.get("reply_to_message", {}).get("message_id")
        if handle_doc_emoji(matched_emoji, text, chat_id, reply_id):
            return

    # 3. Handle Slash Commands
    if text.startswith("/"):
        if text.startswith("/switch"):
            project = text.replace("/switch", "").strip() or "default"
            _active_project[chat_id] = project
            _send(chat_id, f"Switched to project: {project}")
            return
        
        if text.startswith("/status"):
            from memory import get_job
            parts = text.split()
            if len(parts) > 1:
                job = get_job(parts[1])
                if job:
                    _send(chat_id, f"Job {parts[1][:8]}: {job.get('status')} | {job.get('task_type')}")
                else:
                    _send(chat_id, "Job not found.")
            else:
                prior = _last_completed_job.get(chat_id)
                if prior:
                    _send(chat_id, f"Last job: {prior['job_id'][:8]} | {prior['task_type']}")
                else:
                    _send(chat_id, "No recent jobs.")
            return

    # 4. Handle Praise/Critique Learning
    if handle_feedback(text, chat_id):
        return

    # 5. Core Task Routing
    classification = classify_task(text)
    task_type = classification.get("task_type", "unknown")
    
    active_project = _active_project.get(chat_id, "default")
    session_key = f"{active_project}:{chat_id}"
    
    send_briefing(chat_id, task_type, text)

    if task_type == "chat":
        # Run chat in executor to avoid blocking the loop
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, lambda: run_chat(text, session_key))
        _send(chat_id, result["result"])
    else:
        # Run complex task in threadpool
        job_id = f"tg-{datetime.now().strftime('%m%d%H%M')}-{sender_id[-4:]}"
        threading.Thread(
            target=_run_background_job,
            args=(text, chat_id, session_key, job_id, classification),
            daemon=True
        ).start()
        _send(chat_id, f"🚀 Job started: {job_id}")

async def telegram_polling_loop():
    """Fallback polling loop for Telegram updates."""
    token = os.environ.get("ORCHESTRATOR_TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("No Telegram token found.")
        return

    url = f"https://api.telegram.org/bot{token}/getUpdates"
    offset = 0
    
    # Clear webhook first
    async with httpx.AsyncClient() as client:
        await client.get(f"https://api.telegram.org/bot{token}/deleteWebhook")

    while True:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url, params={"offset": offset, "timeout": 20})
                if resp.status_code == 200:
                    updates = resp.json().get("result", [])
                    for update in updates:
                        offset = update["update_id"] + 1
                        asyncio.create_task(process_telegram_update(update))
        except Exception as e:
            logger.error(f"Telegram polling error: {e}")
            await asyncio.sleep(10)

def _shortcut_classify(msg: str):
    """Fast prefix classification."""
    msg_low = msg.lower().strip()
    if msg_low.startswith(("find leads", "get prospects")): return "hunter_task"
    if msg_low.startswith("research"): return "research_report"
    return None

def _classify_obvious_chat(msg: str) -> bool:
    """Check if message is clearly interactive."""
    msg_low = msg.lower().strip()
    chat_triggers = ["hello", "hi ", "who are you", "what can you do", "thanks", "praise", "good job"]
    return any(trigger in msg_low for trigger in chat_triggers)
