"""
===============================================================
agentsHQ ORCHESTRATOR v2.0
===============================================================
Owner: Boubacar Diallo — Catalyst Works Consulting
System: agentsHQ — Self-hosted multi-agent intelligence

This is the main FastAPI service. It receives tasks from:
  - Telegram (primary channel)
  - Direct HTTP POST (from Cursor, Claude Code, any tool)
  - n8n workflows (automated triggers)

Architecture:
  1. Request arrives at /run
  2. Router classifies the task type
  3. Orchestrator assembles the right crew
  4. Crew executes autonomously
  5. Output is saved, memory is updated, result is returned

See AGENTS.md for the full system architecture.
See CLAUDE.md for development guidelines.
===============================================================
"""

import os
import logging
import time
import uuid
import threading
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# Configure logging
LOG_DIR = os.environ.get("AGENTS_LOG_DIR", "/app/logs")
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(LOG_DIR, "orchestrator.log"), mode="a")
    ]
)
logger = logging.getLogger("agentsHQ")

# ── App setup ──────────────────────────────────────────────────
app = FastAPI(
    title="agentsHQ Orchestrator",
    description="Self-hosted multi-agent intelligence for Catalyst Works Consulting",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request/Response models ────────────────────────────────────
class TaskRequest(BaseModel):
    task: str
    from_number: str = "unknown"
    session_key: str = "default"
    context: Optional[dict] = None  # optional extra context from caller
    callback_url: Optional[str] = None  # webhook URL to POST result when async job completes

class TaskResponse(BaseModel):
    success: bool
    result: str
    task_type: str = "unknown"
    files_created: list = []
    execution_time: float = 0.0
    title: str = ""
    deliverable: str = ""

class TeamTaskRequest(BaseModel):
    subtasks: list           # [{"crew_type": str, "task": str, "label": str}]
    original_request: str
    from_number: str = "unknown"
    session_key: str = "default"

class StatusResponse(BaseModel):
    status: str
    service: str
    version: str
    task_types: list
    agents: list
    uptime_seconds: float

class AsyncTaskResponse(BaseModel):
    job_id: str
    status: str = "pending"
    message: str = "Job queued. Poll /status/{job_id} for updates."

class JobStatusResponse(BaseModel):
    job_id: str
    status: str          # pending | running | completed | failed
    task_type: str = ""
    result: str = ""
    files_created: list = []
    execution_time: float = 0.0
    error: str = ""

# Track service start time
_start_time = time.time()


# ══════════════════════════════════════════════════════════════
# CORE ORCHESTRATION LOGIC
# ══════════════════════════════════════════════════════════════

def _query_system() -> str:
    """
    Live system introspection tool. Called by the chat LLM when the user
    asks about agents, task types, system config, or capabilities.
    Always returns accurate data from the running modules — never stale.
    """
    lines = ["=== agentsHQ LIVE SYSTEM STATE ===\n"]

    # Agent registry — read from agents.py builder functions
    try:
        import agents as agent_module
        builders = [f for f in dir(agent_module) if f.startswith("build_") and f.endswith("_agent")]
        lines.append(f"AGENTS ({len(builders)} registered):")
        agent_descriptions = {
            "build_planner_agent":       "Plans and structures every task before execution",
            "build_researcher_agent":    "Finds and synthesizes information using web search",
            "build_copywriter_agent":    "Writes reports, articles, documents, and long-form copy",
            "build_social_media_agent":  "Creates posts and content in Boubacar's voice (X, LinkedIn, etc.)",
            "build_consulting_agent":    "Produces frameworks, proposals, diagnostics, strategy briefs",
            "build_web_builder_agent":   "Builds complete single-file HTML/CSS/JS websites",
            "build_app_builder_agent":   "Builds interactive web applications",
            "build_code_agent":          "Writes, debugs, and explains code in any language",
            "build_qa_agent":            "Reviews all deliverables, fixes issues, ensures professional quality",
            "build_orchestrator_agent":  "Handles unknown/ambiguous requests, escalates or improvises",
            "build_agent_creator_agent": "Designs specs for new specialist agents when a gap is identified",
        }
        for b in sorted(builders):
            name = b.replace("build_", "").replace("_agent", "").replace("_", " ").title()
            desc = agent_descriptions.get(b, "Specialist agent")
            lines.append(f"  - {name}: {desc}")
    except Exception as e:
        lines.append(f"  [Could not load agent list: {e}]")

    # Task types — read live from router
    try:
        from router import TASK_TYPES
        lines.append(f"\nTASK TYPES ({len(TASK_TYPES) - 1} actionable):")
        for key, meta in TASK_TYPES.items():
            if key == "chat":
                continue
            lines.append(f"  - {key}: {meta['description']}")
            lines.append(f"    trigger keywords: {', '.join(meta.get('keywords', [])[:5])}")
    except Exception as e:
        lines.append(f"  [Could not load task types: {e}]")

    # Recent outputs
    try:
        output_dir = os.environ.get("AGENTS_OUTPUT_DIR", "/app/outputs")
        if os.path.exists(output_dir):
            files = sorted(
                [f for f in os.listdir(output_dir) if not os.path.isdir(os.path.join(output_dir, f))],
                key=lambda f: os.path.getmtime(os.path.join(output_dir, f)),
                reverse=True
            )[:10]
            if files:
                lines.append(f"\nRECENT OUTPUT FILES (last 10 in {output_dir}):")
                for f in files:
                    lines.append(f"  - {f}")
            else:
                lines.append(f"\nOUTPUT DIRECTORY: {output_dir} (empty)")
    except Exception:
        pass

    # Infrastructure
    lines.append("\nINFRASTRUCTURE:")
    lines.append("  VPS: 72.60.209.109 — orchestrator on port 8000")
    lines.append("  Telegram bot: @agentsHQ4Bou_bot")
    lines.append("  n8n: https://n8n.srv1040886.hstgr.cloud")
    lines.append("  GitHub: https://github.com/bokar83/agentHQ")
    lines.append("  Memory: Qdrant (vector) + PostgreSQL (conversation history)")

    return "\n".join(lines)


def run_chat(message: str, session_key: str = "default") -> dict:
    """
    Direct conversational response — no crew, no tasks.
    Uses the last 10 turns of session history so the bot remembers
    everything discussed. Fast (single LLM call, ~2-3 seconds).
    """
    start_time = datetime.now()

    # Load conversation history
    history_messages = []
    try:
        from memory import get_conversation_history
        history = get_conversation_history(session_key, limit=10)
        for turn in history:
            role = turn["role"] if turn["role"] in ("user", "assistant") else "user"
            history_messages.append({"role": role, "content": turn["content"]})
    except Exception as e:
        logger.warning(f"Chat history load failed (non-fatal): {e}")

    # Build system prompt
    system_prompt = """You are Boubacar's personal AI assistant, built into agentsHQ.
You know Boubacar well — he is the founder of Catalyst Works Consulting, a strategic
consulting firm. He works across AI, business development, and building systems.

PERSONALITY:
- Sarcastic, witty, and fun — think a brilliant friend who roasts you a little but
  clearly has your back. Like if Bart Simpson grew up and got an MBA.
- Drop a Simpsons quote naturally every few messages. Not every message — just when
  the moment calls for it. Make it land in context, don't force it.
- Short and punchy. No padding. Get to the point with a smirk.
- When Boubacar says something obvious, call it out. When he does something great,
  acknowledge it with minimal fanfare and move on.
- You're not a yes-man. If something is a bad idea, say so — briefly, with humor.

SIMPSONS QUOTES — use these (and others you know) when the vibe is right:
- "I am so smart! S-M-R-T." — Homer, when something goes surprisingly well
- "Trying is the first step towards failure." — Homer, when Boubacar overthinks
- "In this house we obey the laws of thermodynamics!" — when constraints come up
- "It's a perfectly cromulent word." — when something unconventional works
- "Mmm... [relevant thing]" — Homer drooling format, for anything exciting
- "Don't have a cow, man." — Bart, when Boubacar stress-tests something
- "Excellent." — Mr. Burns, when a plan comes together

MEMORY:
You have memory of past conversations. Refer to it naturally when relevant.
No need to announce "based on our history" — just use it the way a friend would.

TASKS:
When Boubacar asks you to DO something (write posts, build a website, research a topic),
remind him that's a crew job — send it as a regular message and the agents will handle it.
Keep that redirect short. One line max."""

    # Tool definition — LLM calls this when it needs live system info
    tools = [
        {
            "type": "function",
            "function": {
                "name": "query_system",
                "description": (
                    "Query the live agentsHQ system state. Call this when the user asks about: "
                    "what agents exist, what task types are available, what the system can do, "
                    "recent output files, infrastructure details, or any question about the "
                    "system's current configuration and capabilities."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
    ]

    # Assemble messages: system + history + current message
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history_messages)
    messages.append({"role": "user", "content": message})

    try:
        import openai
        client = openai.OpenAI(
            api_key=os.environ.get("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://agentshq.catalystworks.com",
                "X-Title": "agentsHQ Chat"
            }
        )

        response = client.chat.completions.create(
            model="anthropic/claude-haiku-4.5",
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.85,
        )

        msg = response.choices[0].message

        # If the LLM called query_system, execute it and send result back
        if msg.tool_calls:
            system_data = _query_system()
            messages.append(msg)  # assistant message with tool_calls
            messages.append({
                "role": "tool",
                "tool_call_id": msg.tool_calls[0].id,
                "content": system_data
            })
            # Second call with tool result injected
            followup = client.chat.completions.create(
                model="anthropic/claude-haiku-4.5",
                messages=messages,
                temperature=0.85,
            )
            reply = followup.choices[0].message.content.strip()
            logger.info("Chat used query_system tool")
        else:
            reply = msg.content.strip()

    except Exception as e:
        logger.error(f"Chat LLM call failed: {e}")
        reply = "Sorry, I hit an error. Try again in a moment."

    # Save this exchange to history
    try:
        from memory import save_conversation_turn
        save_conversation_turn(session_key, "user", message)
        save_conversation_turn(session_key, "assistant", reply)
    except Exception as e:
        logger.warning(f"Chat history save failed (non-fatal): {e}")

    execution_time = (datetime.now() - start_time).total_seconds()
    logger.info(f"Chat response for session '{session_key}' in {execution_time:.1f}s")

    return {
        "success": True,
        "result": reply,
        "full_output": reply,
        "task_type": "chat",
        "files_created": [],
        "execution_time": execution_time,
        "classification": {"task_type": "chat", "confidence": 1.0, "is_unknown": False}
    }


def run_orchestrator(task_request: str, from_number: str = "unknown", session_key: str = "default") -> dict:
    """
    Main orchestration function.

    1. Load session history for context
    2. Route: classify the task type
    3. Assemble: build the right crew
    4. Execute: run the crew autonomously
    5. Save: store output to memory + conversation history
    6. Return: structured result for the caller
    """
    start_time = datetime.now()

    # Step 1: Load recent conversation history for this session
    enriched_task = task_request
    try:
        from memory import get_conversation_history
        history = get_conversation_history(session_key, limit=6)
        if history:
            history_text = "\n".join(
                f"[{h['role'].upper()}]: {h['content'][:800]}"
                for h in history
            )
            enriched_task = (
                f"--- CONVERSATION HISTORY (most recent first) ---\n"
                f"{history_text}\n"
                f"--- END HISTORY ---\n\n"
                f"CURRENT REQUEST: {task_request}"
            )
            logger.info(f"Injected {len(history)} history entries for session '{session_key}'")
    except Exception as e:
        logger.warning(f"History injection failed (non-fatal): {e}")

    # Step 2: Route
    from router import classify_task, get_crew_type, TASK_TYPES
    classification = classify_task(task_request)  # classify on raw task, not enriched
    task_type = classification.get("task_type", "unknown")
    is_unknown = classification.get("is_unknown", False)

    logger.info(f"Task classified as '{task_type}' (confidence: {classification.get('confidence', 0)})")

    # Step 3: Assemble crew
    from crews import assemble_crew

    if is_unknown:
        crew_type = "unknown_crew"
    else:
        crew_type = get_crew_type(task_type) or "unknown_crew"

    crew = assemble_crew(crew_type, enriched_task)
    
    # Step 3: Execute
    logger.info(f"Kicking off crew: {crew_type}")
    result = crew.kickoff()
    result_str = result.raw if hasattr(result, 'raw') else str(result)
    try:
        from skills.boub_voice_mastery.voice_polisher import polish_voice
        result_str = polish_voice(result_str)
    except Exception:
        pass

    # Extract deliverable — everything after "DELIVERABLE:" marker
    lower = result_str.lower()
    idx = lower.find("deliverable:")
    deliverable = result_str[idx + len("deliverable:"):].strip() if idx != -1 else result_str.strip()
    title = task_request[:80].strip()

    end_time = datetime.now()
    execution_time = (end_time - start_time).total_seconds()
    
    # Step 4: Collect files created
    files_created = []
    output_dir = os.environ.get("AGENTS_OUTPUT_DIR", "/app/outputs")
    if os.path.exists(output_dir):
        all_files = os.listdir(output_dir)
        # Get files created in this execution window
        recent_files = [
            f for f in all_files
            if os.path.getmtime(os.path.join(output_dir, f)) >= start_time.timestamp()
        ]
        files_created = recent_files
    
    # Step 5: Save to memory + conversation history
    try:
        from memory import save_to_memory, save_conversation_turn
        result_summary = result_str[:1000] if len(result_str) > 1000 else result_str
        save_to_memory(
            task_request=task_request,
            task_type=task_type,
            result_summary=result_summary,
            files_created=files_created,
            execution_time=execution_time,
            from_number=from_number
        )
        # Save this exchange to conversation history for follow-up context
        save_conversation_turn(session_key, "user", task_request)
        save_conversation_turn(session_key, "assistant", result_summary)
    except Exception as e:
        logger.warning(f"Memory save failed (non-fatal): {e}")

    # Build Telegram-friendly summary
    summary = _build_summary(task_type, result_str, files_created, execution_time)

    # Save overflow so user can reply 'more' if output was truncated
    _save_overflow_if_needed(session_key, result_str, task_type)

    return {
        "success": True,
        "result": summary,
        "task_type": task_type,
        "files_created": files_created,
        "execution_time": execution_time,
        "title": title,
        "deliverable": deliverable,
    }


def run_team_orchestrator(subtasks: list, original_request: str, from_number: str = "unknown") -> dict:
    """
    Run multiple crews in parallel and synthesize results.
    Called by POST /run-team.

    subtasks: [{"crew_type": str, "task": str, "label": str}, ...]
    """
    from crews import run_parallel_team, build_team_synthesis_crew

    start_time = datetime.now()

    # Phase 1: run all subtasks in parallel
    teammate_results = run_parallel_team(subtasks)

    successful = [r for r in teammate_results if r["success"]]
    failed     = [r for r in teammate_results if not r["success"]]

    if failed:
        logger.warning(f"[agent-team] {len(failed)} teammate(s) failed: {[f['label'] for f in failed]}")

    if not successful:
        raise RuntimeError("All teammates failed — no results to synthesize.")

    # Phase 2: synthesize
    synthesis_crew = build_team_synthesis_crew(original_request, successful)
    final_result   = synthesis_crew.kickoff()
    result_str     = final_result.raw if hasattr(final_result, 'raw') else str(final_result)

    execution_time = (datetime.now() - start_time).total_seconds()

    # Collect files created
    files_created = []
    output_dir = os.environ.get("AGENTS_OUTPUT_DIR", "/app/outputs")
    if os.path.exists(output_dir):
        files_created = [
            f for f in os.listdir(output_dir)
            if os.path.getmtime(os.path.join(output_dir, f)) >= start_time.timestamp()
        ]

    # Save to memory
    try:
        from memory import save_to_memory
        save_to_memory(
            task_request=original_request,
            task_type="agent_team",
            result_summary=result_str[:1000],
            files_created=files_created,
            execution_time=execution_time,
            from_number=from_number
        )
    except Exception as e:
        logger.warning(f"Memory save failed (non-fatal): {e}")

    summary = _build_summary("agent_team", result_str, files_created, execution_time)

    return {
        "success": True,
        "result": summary,
        "full_output": result_str,
        "task_type": "agent_team",
        "teammate_count": len(subtasks),
        "teammates_succeeded": len(successful),
        "teammates_failed": len(failed),
        "files_created": files_created,
        "execution_time": execution_time,
    }


def _build_summary(
    task_type: str,
    full_output: str,
    files_created: list,
    execution_time: float
) -> str:
    """
    Build a Telegram message with the full deliverable content.
    Always includes: what was done, time taken, files saved, and full output.
    """

    type_labels = {
        "agent_team":              "Team task complete",
        "website_build":           "Website built",
        "app_build":               "App built",
        "research_report":         "Research complete",
        "consulting_deliverable":  "Consulting deliverable ready",
        "social_content":          "Social content created",
        "code_task":               "Code task complete",
        "general_writing":         "Document ready",
        "agent_creation":          "Agent proposal submitted",
        "unknown":                 "Task complete",
    }

    label = type_labels.get(task_type, "Task complete")

    lines = [
        f"--- {label} ---",
        f"Time: {execution_time:.0f}s",
    ]

    if files_created:
        lines.append(f"Files saved: {', '.join(files_created)}")

    lines.append("")  # blank line before content

    # Send full output up to Telegram's 4096 char limit
    # Reserve ~150 chars for the header lines above
    MAX_CONTENT = 3700
    if full_output and len(full_output) > 50:
        content = full_output.strip()
        if len(content) > MAX_CONTENT:
            content = content[:MAX_CONTENT] + "\n\n[reply 'more' to see the rest]"
        lines.append(content)
    else:
        lines.append("[No output content returned by agents]")

    return "\n".join(lines)


def _save_overflow_if_needed(session_key: str, full_output: str, task_type: str) -> None:
    """Save overflow to DB if output exceeds one Telegram message."""
    MAX_CONTENT = 3700
    if full_output and len(full_output.strip()) > MAX_CONTENT:
        try:
            from memory import save_overflow
            save_overflow(session_key, full_output.strip(), MAX_CONTENT, task_type)
        except Exception as e:
            logger.warning(f"Overflow save failed (non-fatal): {e}")


def _run_background_job(
    task: str,
    from_number: str,
    session_key: str,
    job_id: str,
) -> None:
    """
    Background worker: runs the crew, sends progress pings, saves output,
    and delivers the final result to Telegram.
    Called via FastAPI BackgroundTasks — runs in a thread pool.
    """
    from notifier import send_progress_ping, send_result, send_message
    from saver import save_to_github, save_to_drive

    chat_id = from_number  # from_number IS the Telegram chat ID

    # ── Progress ping timer ──────────────────────────────────
    _stop_ping = threading.Event()

    def _ping_loop():
        while not _stop_ping.wait(300):  # wait 5 min; returns True if event set
            send_progress_ping(chat_id)

    ping_thread = threading.Thread(target=_ping_loop, daemon=True)
    ping_thread.start()

    try:
        # ── Run the crew ─────────────────────────────────────
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
        github_url = save_to_github(title, task_type, deliverable)
        drive_url  = save_to_drive(title, task_type, deliverable)

        # ── Deliver ──────────────────────────────────────────
        send_result(chat_id, summary, drive_url, github_url)

    except Exception as e:
        logger.error(f"Background job {job_id} failed: {e}", exc_info=True)
        try:
            from notifier import send_message
            send_message(chat_id, f"Sorry — something went wrong with your task. Error: {str(e)[:200]}")
        except Exception:
            logger.critical(f"Background job {job_id}: result delivery AND error notification both failed. User received nothing.")
    finally:
        _stop_ping.set()  # cancel ping loop regardless of success/failure


# ══════════════════════════════════════════════════════════════
# API ENDPOINTS
# ══════════════════════════════════════════════════════════════

@app.get("/", response_model=StatusResponse)
def status():
    """System status and capability overview."""
    from router import TASK_TYPES
    
    return StatusResponse(
        status="running",
        service="agentsHQ Orchestrator",
        version="2.0.0",
        task_types=list(TASK_TYPES.keys()),
        agents=[
            "planner", "researcher", "copywriter",
            "web_builder", "app_builder", "code_agent",
            "consulting_agent", "social_media_agent",
            "qa_agent", "orchestrator", "agent_creator"
        ],
        uptime_seconds=time.time() - _start_time
    )


@app.get("/health")
def health():
    """Health check endpoint. Called by Docker and n8n."""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": time.time() - _start_time
    }


@app.post("/run", response_model=AsyncTaskResponse, status_code=202)
async def run_task(request: TaskRequest, background_tasks: BackgroundTasks):
    """
    Main endpoint — async, fire-and-forget.

    Returns 202 immediately after sending a Telegram ack.
    The crew runs in the background; result is pushed to Telegram when done.

    For synchronous callers (Cursor, Claude Code), use POST /run-sync instead.
    """
    logger.info(f"Request from {request.from_number}: {request.task[:100]}...")

    job_id = str(uuid.uuid4())

    # Handle 'more' command synchronously — it's instant
    if request.task.strip().lower() in ("more", "more please", "continue", "show more"):
        from memory import get_next_chunk
        from notifier import send_message
        chunk_result = get_next_chunk(request.session_key)
        if chunk_result["found"]:
            suffix = "\n\n[reply 'more' for the rest]" if chunk_result["has_more"] else "\n\n[end of output]"
            send_message(request.from_number, chunk_result["chunk"] + suffix)
        else:
            send_message(request.from_number, "Nothing more to show — that was the full output.")
        return AsyncTaskResponse(job_id=job_id, status="completed", message="Chunk delivered.")

    # Classify to get task_type for the ack message
    _msg = request.task.strip().lower()
    _is_obvious_chat = (
        len(_msg) < 60 and not any(w in _msg for w in [
            "write", "create", "build", "research", "analyze", "make",
            "draft", "generate", "code", "script", "website", "report",
            "proposal", "post", "email", "article"
        ])
    ) or _msg.startswith(("what is my", "what's my", "how much", "do you", "can you tell",
                           "hey", "hi ", "hello", "thanks", "thank you", "what did",
                           "do you remember", "remind me", "what have we", "what was"))

    if _is_obvious_chat:
        task_type = "chat"
    else:
        from router import classify_task
        classification = classify_task(request.task)
        task_type = classification.get("task_type", "unknown")

    # Send ack to Telegram immediately
    from notifier import send_ack
    send_ack(request.from_number, task_type)

    # For chat, run in executor (non-blocking) and deliver directly
    if task_type == "chat":
        import asyncio
        from notifier import send_message
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: run_chat(message=request.task, session_key=request.session_key))
        send_message(request.from_number, result["result"])
        return AsyncTaskResponse(job_id=job_id, status="completed", message="Chat response delivered.")

    # Queue crew job in background
    background_tasks.add_task(
        _run_background_job,
        task=request.task,
        from_number=request.from_number,
        session_key=request.session_key,
        job_id=job_id,
    )

    return AsyncTaskResponse(
        job_id=job_id,
        status="pending",
        message="Job queued. Result will be delivered to Telegram.",
    )


@app.post("/run-sync", response_model=TaskResponse)
async def run_task_sync(request: TaskRequest):
    """
    Synchronous endpoint — blocks until result is ready, returns TaskResponse.
    Use this for programmatic callers (Cursor, Claude Code, scripts).
    Does NOT send Telegram messages.
    """
    logger.info(f"[sync] Request from {request.from_number}: {request.task[:100]}...")

    try:
        if request.task.strip().lower() in ("more", "more please", "continue", "show more"):
            from memory import get_next_chunk
            chunk_result = get_next_chunk(request.session_key)
            if chunk_result["found"]:
                suffix = "\n\n[reply 'more' for the rest]" if chunk_result["has_more"] else "\n\n[end of output]"
                reply = chunk_result["chunk"] + suffix
            else:
                reply = "Nothing more to show — that was the full output."
            return TaskResponse(success=True, result=reply, task_type="more", files_created=[], execution_time=0.0)

        _msg = request.task.strip().lower()
        _is_obvious_chat = (
            len(_msg) < 60 and not any(w in _msg for w in [
                "write", "create", "build", "research", "analyze", "make",
                "draft", "generate", "code", "script", "website", "report",
                "proposal", "post", "email", "article"
            ])
        ) or _msg.startswith(("what is my", "what's my", "how much", "do you", "can you tell",
                               "hey", "hi ", "hello", "thanks", "thank you", "what did",
                               "do you remember", "remind me", "what have we", "what was"))

        if _is_obvious_chat:
            result = run_chat(message=request.task, session_key=request.session_key)
        else:
            result = run_orchestrator(
                task_request=request.task,
                from_number=request.from_number,
                session_key=request.session_key,
            )

        return TaskResponse(
            success=result["success"],
            result=result["result"],
            task_type=result.get("task_type", "unknown"),
            files_created=result.get("files_created", []),
            execution_time=result.get("execution_time", 0.0),
            title=result.get("title", ""),
            deliverable=result.get("deliverable", ""),
        )

    except Exception as e:
        logger.error(f"[sync] Request failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")


@app.post("/run-team", response_model=TaskResponse)
async def run_team(request: TeamTaskRequest):
    """
    Run multiple crews in parallel (agent teams pattern).

    The caller decomposes the request into independent subtasks.
    All subtasks run concurrently; results are synthesized into one output.

    Example body:
    {
      "original_request": "I need research + a LinkedIn post + a Python script about AI in HR",
      "from_number": "7792432594",
      "subtasks": [
        {"crew_type": "research_crew", "task": "Research AI in HR", "label": "research"},
        {"crew_type": "social_crew",   "task": "Write LinkedIn post on AI in HR", "label": "social"},
        {"crew_type": "code_crew",     "task": "Write CV scorer Python script", "label": "code"}
      ]
    }
    """
    logger.info(f"/run-team received {len(request.subtasks)} subtasks from {request.from_number}")

    if not request.subtasks:
        raise HTTPException(status_code=400, detail="subtasks list cannot be empty")

    try:
        result = run_team_orchestrator(
            subtasks=request.subtasks,
            original_request=request.original_request,
            from_number=request.from_number
        )
        return TaskResponse(
            success=result["success"],
            result=result["result"],
            task_type=result["task_type"],
            files_created=result.get("files_created", []),
            execution_time=result.get("execution_time", 0.0)
        )
    except Exception as e:
        logger.error(f"/run-team failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Team execution failed: {str(e)}")


@app.get("/classify")
def classify_only(task: str):
    """
    Classify a task without running it.
    Useful for testing the router and understanding what crew would be used.
    """
    from router import classify_task, get_crew_type
    classification = classify_task(task)
    crew_type = get_crew_type(classification.get("task_type", "unknown"))
    return {
        "task": task,
        "classification": classification,
        "crew_type": crew_type
    }


@app.get("/capabilities")
def capabilities():
    """List all task types the system can handle."""
    from router import TASK_TYPES
    return {
        "task_types": {
            k: {
                "description": v["description"],
                "crew": v["crew"],
                "example_keywords": v["keywords"][:5]
            }
            for k, v in TASK_TYPES.items()
        }
    }


@app.get("/outputs")
def list_outputs():
    """List all files created by the agents."""
    output_dir = os.environ.get("AGENTS_OUTPUT_DIR", "/app/outputs")
    if not os.path.exists(output_dir):
        return {"files": [], "count": 0}
    
    files = []
    for f in os.listdir(output_dir):
        if not f.startswith("."):
            filepath = os.path.join(output_dir, f)
            files.append({
                "name": f,
                "size_bytes": os.path.getsize(filepath),
                "created": datetime.fromtimestamp(
                    os.path.getctime(filepath)
                ).isoformat()
            })
    
    files.sort(key=lambda x: x["created"], reverse=True)
    return {"files": files, "count": len(files)}


@app.get("/outputs/{filename}")
def get_output(filename: str):
    """Retrieve a specific output file."""
    # Security: prevent path traversal
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    filepath = f"/app/outputs/{filename}"
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    return {
        "filename": filename,
        "content": content,
        "size_bytes": len(content)
    }


@app.get("/memory/search")
def search_memory(query: str, top_k: int = 3):
    """Search agent memory for relevant past tasks."""
    try:
        from memory import query_memory
        results = query_memory(query, top_k=top_k)
        return {"query": query, "results": results, "count": len(results)}
    except Exception as e:
        return {"query": query, "results": [], "error": str(e)}


@app.get("/history/{session_id}")
def get_history(session_id: str, limit: int = 10):
    """Get conversation history for a WhatsApp session."""
    try:
        from memory import get_conversation_history
        history = get_conversation_history(session_id, limit=limit)
        return {"session_id": session_id, "history": history}
    except Exception as e:
        return {"session_id": session_id, "history": [], "error": str(e)}


@app.post("/run-async", response_model=AsyncTaskResponse)
async def run_task_async(request: TaskRequest, background_tasks: BackgroundTasks):
    """
    Async task endpoint — returns job_id immediately, runs crew in background.

    Use for any task that might take >30s (website builds, app builds, research).
    Poll GET /status/{job_id} until status == 'completed' or 'failed'.

    n8n pattern:
      1. POST /run-async → get job_id (instant)
      2. Send "working on it..." to Telegram
      3. Poll /status/{job_id} every 10s
      4. When completed, send result to Telegram
    """
    job_id = str(uuid.uuid4())[:8]  # short 8-char ID, easy to reference

    from memory import create_job
    create_job(
        job_id=job_id,
        session_key=request.session_key,
        from_number=request.from_number,
        task=request.task
    )

    def _run_in_background():
        from memory import update_job
        try:
            update_job(job_id, status="running")

            # Chat tasks don't belong in async — run sync and complete immediately
            _msg = request.task.strip().lower()
            _is_chat = (
                len(_msg) < 60 and not any(w in _msg for w in [
                    "write", "create", "build", "research", "analyze", "make",
                    "draft", "generate", "code", "script", "website", "report",
                    "proposal", "post", "email", "article"
                ])
            )
            if _is_chat:
                result = run_chat(message=request.task, session_key=request.session_key)
            else:
                result = run_orchestrator(
                    task_request=request.task,
                    from_number=request.from_number,
                    session_key=request.session_key
                )

            update_job(
                job_id=job_id,
                status="completed",
                result=result["result"],
                task_type=result.get("task_type", "unknown"),
                files_created=result.get("files_created", []),
                execution_time=result.get("execution_time", 0.0)
            )
            logger.info(f"Async job {job_id} completed ({result.get('task_type')})")

            # Fire callback if provided
            if request.callback_url:
                try:
                    import requests as _requests
                    _requests.post(request.callback_url, json={
                        "job_id": job_id,
                        "status": "completed",
                        "result": result["result"],
                        "task_type": result.get("task_type", "unknown"),
                        "files_created": result.get("files_created", []),
                        "execution_time": result.get("execution_time", 0.0),
                        "from_number": request.from_number,
                        "chat_id": (request.context or {}).get("chat_id", request.from_number),
                        "success": True
                    }, timeout=10)
                    logger.info(f"Callback fired for job {job_id}")
                except Exception as cb_err:
                    logger.warning(f"Callback failed for job {job_id}: {cb_err}")

        except Exception as e:
            logger.error(f"Async job {job_id} failed: {e}", exc_info=True)
            from memory import update_job as uj
            uj(job_id=job_id, status="failed", error=str(e))

            # Fire failure callback if provided
            if request.callback_url:
                try:
                    import requests as _requests
                    _requests.post(request.callback_url, json={
                        "job_id": job_id,
                        "status": "failed",
                        "result": f"Task failed: {str(e)}",
                        "task_type": "unknown",
                        "files_created": [],
                        "execution_time": 0.0,
                        "from_number": request.from_number,
                        "chat_id": (request.context or {}).get("chat_id", request.from_number),
                        "success": False
                    }, timeout=10)
                except Exception:
                    pass

    background_tasks.add_task(_run_in_background)
    logger.info(f"Queued async job {job_id} for: {request.task[:60]}... callback={request.callback_url or 'none'} context={request.context}")

    return AsyncTaskResponse(
        job_id=job_id,
        status="pending",
        message=f"Job {job_id} queued. Poll /status/{job_id} for updates."
    )


@app.get("/status/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str):
    """
    Poll this endpoint after calling /run-async.
    Returns current status: pending | running | completed | failed.
    When completed, result and files_created are populated.
    """
    from memory import get_job
    job = get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    return JobStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        task_type=job.get("task_type") or "",
        result=job.get("result") or "",
        files_created=job.get("files_created") or [],
        execution_time=job.get("execution_time") or 0.0,
        error=job.get("error") or ""
    )


# ── Run directly for testing ───────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    
    # Ensure required directories exist
    os.makedirs("/app/outputs", exist_ok=True)
    os.makedirs("/app/logs", exist_ok=True)
    os.makedirs("/app/outputs/proposals", exist_ok=True)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
