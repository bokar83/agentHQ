"""
===============================================================
agentsHQ ORCHESTRATOR v2.0
===============================================================
Owner: Boubacar Barry — Catalyst Works Consulting
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
import json
import asyncio
import threading
import uuid
import logging
import time
from datetime import datetime
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# OpenSpace Evolution Hook
try:
    from skills.openspace_skill.openspace_tool import openspace_tool
except ImportError:
    openspace_tool = None  # type: ignore[assignment]

# Catalyst Daily Ignition Scheduler
try:
    from scheduler import start_scheduler
except ImportError:
    start_scheduler = None

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

@app.on_event("startup")
async def startup_event():
    """Run at service startup."""
    if start_scheduler:
        start_scheduler()
        logger.info("Catalyst Daily Ignition initiated.")
    
    # Start Telegram Polling in background
    asyncio.create_task(telegram_polling_loop())
    logger.info("Telegram Polling Loop scheduled.")

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

# Git lock — all local git operations must acquire this before running.
# Prevents concurrent agents from corrupting the working tree.
_git_lock = threading.Lock()


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

FILE RETRIEVAL:
You have a retrieve_output_file tool. Use it immediately when Boubacar asks to see,
read, get, or retrieve a file the agents created. Do NOT say "let me grab that" and
stop — call the tool and include the full content + Drive link in your reply.

TASKS:
When Boubacar asks you to DO something (write posts, build a website, research a topic),
remind him that's a crew job — send it as a regular message and the agents will handle it.
Keep that redirect short. One line max."""

    # Tool definitions
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
                "parameters": {"type": "object", "properties": {}, "required": []}
            }
        },
        {
            "type": "function",
            "function": {
                "name": "retrieve_output_file",
                "description": (
                    "Read and return the full content of a saved output file, plus its Google Drive link. "
                    "Call this when the user asks to see, read, retrieve, or get the content of a file "
                    "that was previously created by the agents. Also call this when the user asks for "
                    "the Drive link or GitHub link for a specific output file."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename_hint": {
                            "type": "string",
                            "description": "Partial filename or keywords to match. E.g. 'disruptive ai startups' or '5-most-disruptive'."
                        }
                    },
                    "required": ["filename_hint"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "save_memory",
                "description": (
                    "Persist a fact, preference, or note to long-term memory. "
                    "Call this when the user says 'remember this', 'add to memory', "
                    "'save this', 'store this', 'note this down', or shares information "
                    "they want kept (brand colors, preferences, facts, etc.). "
                    "Do NOT call for ideas — use the crew for that."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fact": {
                            "type": "string",
                            "description": "The fact or preference to save, written as a complete sentence."
                        },
                        "category": {
                            "type": "string",
                            "description": "Category label e.g. 'brand', 'preference', 'contact', 'system'."
                        }
                    },
                    "required": ["fact"]
                }
            }
        },
    ]

    def _retrieve_output_file(filename_hint: str) -> str:
        """Find a matching output file and return its content + Drive link."""
        output_dir = os.environ.get("AGENTS_OUTPUT_DIR", "/app/outputs")
        all_files = []
        try:
            for root, dirs, files in os.walk(output_dir):
                for f in files:
                    all_files.append(os.path.join(root, f))
        except Exception as e:
            return f"Could not scan output directory: {e}"

        if not all_files:
            return "No output files found in the outputs directory."

        # Score files by hint keyword match
        hint_lower = filename_hint.lower()
        hint_words = hint_lower.replace("-", " ").replace("_", " ").split()
        scored = []
        for fp in all_files:
            name = os.path.basename(fp).lower().replace("-", " ").replace("_", " ")
            score = sum(1 for w in hint_words if w in name)
            scored.append((score, os.path.getmtime(fp), fp))

        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        best_score, _, best_path = scored[0]

        if best_score == 0:
            # Fall back to most recent file
            all_files.sort(key=os.path.getmtime, reverse=True)
            best_path = all_files[0]

        try:
            with open(best_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return f"Found file {os.path.basename(best_path)} but could not read it: {e}"

        # Try to get Drive link by uploading
        drive_url = None
        try:
            from saver import save_to_drive
            title = os.path.basename(best_path).replace("-", " ").replace("_", " ")
            drive_url = save_to_drive(title, "research_report", content)
        except Exception:
            pass

        result_parts = [f"File: {os.path.basename(best_path)}", ""]
        if drive_url:
            result_parts.append(f"Drive link: {drive_url}")
            result_parts.append("")
        result_parts.append(content[:3000])
        if len(content) > 3000:
            result_parts.append("\n[... content truncated — reply 'more' for the rest]")
        return "\n".join(result_parts)

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

        # Handle tool calls
        if msg.tool_calls:
            messages.append(msg)
            for tool_call in msg.tool_calls:
                fn_name = tool_call.function.name
                if fn_name == "query_system":
                    tool_result = _query_system()
                    logger.info("Chat used query_system tool")
                elif fn_name == "retrieve_output_file":
                    args = json.loads(tool_call.function.arguments or "{}")
                    tool_result = _retrieve_output_file(args.get("filename_hint", ""))
                    logger.info(f"Chat used retrieve_output_file: {args.get('filename_hint')}")
                elif fn_name == "save_memory":
                    args = json.loads(tool_call.function.arguments or "{}")
                    fact = args.get("fact", "")
                    category = args.get("category", "general")
                    try:
                        from memory import save_conversation_turn, save_to_memory
                        tag = f"[MEMORY:{category.upper()}] {fact}"
                        save_conversation_turn(session_key, "assistant", tag)
                        save_to_memory(
                            task_request=tag,
                            task_type="memory_capture",
                            result_summary=fact,
                            files_created=[],
                            execution_time=0,
                            from_number=session_key,
                        )
                        logger.info(f"Chat used save_memory: {fact[:80]}")
                        tool_result = f"Saved to memory: {fact}"
                    except Exception as mem_e:
                        tool_result = f"Memory save failed: {mem_e}"
                else:
                    tool_result = "Unknown tool."
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })
            followup = client.chat.completions.create(
                model="anthropic/claude-haiku-4.5",
                messages=messages,
                temperature=0.85,
            )
            reply = (followup.choices[0].message.content or "").strip()
        else:
            reply = (msg.content or "").strip()

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
    today = start_time.strftime("%B %d, %Y")
    enriched_task = f"[Today's date: {today}. All research, recommendations, and references should reflect the current state as of {today}.]\n\n{task_request}"
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

    # Step 3: Direct dispatch for crm_outreach (no crew -- pure Supabase + Gmail API)
    if task_type == "crm_outreach":
        try:
            from skills.outreach.outreach_tool import run_outreach
            contact_all = "contact all" in task_request.lower() or "all leads" in task_request.lower()
            outreach_result = run_outreach(contact_all=contact_all)
            drafted = outreach_result.get("drafted", 0)
            skipped = outreach_result.get("skipped", 0)
            results = outreach_result.get("results", [])
            error = outreach_result.get("error")

            if error:
                deliverable = f"Outreach failed: {error}"
            elif drafted == 0:
                deliverable = (
                    "No drafts created. Either no leads have confirmed emails yet, "
                    "or all eligible leads have already been contacted. "
                    "Run 'find leads' to add new ones."
                )
            else:
                lines = [f"Cold outreach drafts created in catalystworks.ai@gmail.com ({drafted} drafts):\n"]
                for r in results:
                    if r.get("status") == "drafted":
                        lines.append(f"- {r['name']} | {r['company']} | {r['email']} | {r['subject']}")
                if skipped:
                    lines.append(f"\n{skipped} lead(s) failed (Gmail API error -- check logs).")
                deliverable = "\n".join(lines)

            return {
                "success": True,
                "task_type": task_type,
                "deliverable": deliverable,
                "execution_time": (datetime.now() - start_time).total_seconds(),
            }
        except Exception as e:
            logger.error(f"crm_outreach direct dispatch failed: {e}")
            return {"success": False, "task_type": task_type, "deliverable": f"Outreach error: {e}", "execution_time": 0}

    # Step 3: Assemble crew
    from crews import assemble_crew

    if is_unknown:
        crew_type = "unknown_crew"
    else:
        crew_type = get_crew_type(task_type) or "unknown_crew"

    crew = assemble_crew(crew_type, enriched_task)

    # Step 4: Execute
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
        "linkedin_x_campaign":     "LinkedIn/X campaign ready",
        "code_task":               "Code task complete",
        "general_writing":         "Document ready",
        "agent_creation":          "Agent proposal submitted",
        "gws_task":                "Google Workspace task complete",
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
    classification: dict = None,
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
    # First ping at 60s so user knows it's working, then every 5 min.
    # Watchdog at 10 min: if still running, send an error and bail.
    _stop_ping = threading.Event()

    def _ping_loop():
        # First ping after 60s
        if _stop_ping.wait(60):
            return
        send_progress_ping(chat_id)
        # Subsequent pings every 5 min, watchdog at 10 min total (1 more ping)
        if _stop_ping.wait(300):
            return
        send_progress_ping(chat_id)
        # Watchdog: if still running after ~10 min total, something is hung
        if not _stop_ping.wait(300):
            send_message(chat_id, "⚠️ Task is taking longer than expected (10+ min). It may be stuck — please try again or check with the team.")
            _stop_ping.set()

    ping_thread = threading.Thread(target=_ping_loop, daemon=True)
    ping_thread.start()

    result = {}  # ensure result is always defined before try/finally
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

        # ── Compound request: email follow-up ────────────────────
        # If the original message asked to "also send me an email about this",
        # spin a minimal GWS crew to draft the summary email after the main task.
        _has_email_followup = (classification or {}).get("has_email_followup", False)
        if _has_email_followup and task_type not in ("chat", "gws_task", "crm_outreach"):
            try:
                from crews import build_gws_crew
                email_task_text = (
                    f"Create a Gmail draft to bokar83@gmail.com and catalystworks.ai@gmail.com "
                    f"with subject 'agentsHQ Result: {title[:60]}'. "
                    f"Body: Format the following result as clean HTML with a header, "
                    f"bullet points for key findings, and a closing note. "
                    f"Result to format:\n\n{summary[:3000]}"
                )
                email_crew = build_gws_crew(email_task_text)
                email_crew.kickoff()
                send_message(chat_id, "Email draft created in your Gmail — go check it.")
                logger.info(f"Compound email follow-up draft created for job {job_id}")
            except Exception as e:
                logger.warning(f"Compound email follow-up failed (non-fatal): {e}")

        # ── Email hunter results ──────────────────────────────
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
            from notifier import send_message
            send_message(chat_id, f"Sorry — something went wrong with your task. Error: {str(e)[:200]}")
        except Exception:
            logger.critical(f"Background job {job_id}: result delivery AND error notification both failed. User received nothing.")
    finally:
        _stop_ping.set()  # cancel ping loop regardless of success/failure
        
        # ── Trigger Evolution (Self-Learning) ────────────────
        # We run this in a separate thread to avoid blocking the main background task completion
        # and to keep it completely "background" as requested.
        try:
            if result.get("success"):
                threading.Thread(
                    target=_trigger_evolution,
                    args=(task, result.get("full_output", "")),
                    daemon=True
                ).start()
        except Exception as e:
            logger.warning(f"Evolution trigger failed: {e}")

def _trigger_evolution(task_instruction: str, result_output: str) -> None:
    """
    Helper to run OpenSpace evolution in the background.
    Uses the tool wrapper to either evolve a skill or suggest a new one.
    """
    import asyncio
    try:
        # Check if evolution is explicitly disabled via env
        if os.environ.get("DISABLE_EVOLUTION") == "true":
            return

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Only evolve if the task was significant (token efficiency)
        if openspace_tool is not None and (len(task_instruction) > 20 or len(result_output) > 100):
            logger.info("Triggering OpenSpace evolution...")
            loop.run_until_complete(openspace_tool.execute_async(
                command="evolve",
                task_instruction=f"Task: {task_instruction}\n\nResult:\n{result_output}"
            ))
            logger.info("OpenSpace evolution check complete.")
            
    except Exception as e:
        logger.error(f"Background evolution failed: {e}")
    finally:
        loop.close()


_TASK_KEYWORDS = [
    "write", "create", "build", "research", "analyze", "make",
    "draft", "generate", "code", "script", "website", "report",
    "proposal", "post", "email", "article",
    "find", "hunt", "leads", "prospect", "run the", "hunter",
    "news", "brief", "headlines",
]
_CHAT_PREFIXES = (
    "what is my", "what's my", "how much", "do you", "can you tell",
    "hey", "hi ", "hello", "thanks", "thank you", "what did",
    "do you remember", "remind me", "what have we", "what was",
)

def _shortcut_classify(msg: str):
    """
    Run keyword shortcuts BEFORE the obvious-chat pre-filter.
    Returns a task_type string if matched, else None.
    This prevents short messages from being swallowed by _classify_obvious_chat().
    """
    from router import _keyword_shortcut
    return _keyword_shortcut(msg)


def _classify_obvious_chat(msg: str) -> bool:
    """
    Fast pre-check before calling the LLM classifier.
    Returns True if the message is almost certainly casual chat,
    so we can skip classification and go straight to run_chat().
    """
    m = msg.strip().lower()
    return (
        len(m) < 60 and not any(w in m for w in _TASK_KEYWORDS)
    ) or m.startswith(_CHAT_PREFIXES)


# ══════════════════════════════════════════════════════════════
# API ENDPOINTS
# ══════════════════════════════════════════════════════════════

async def process_telegram_update(update: dict):
    """
    Unified processor for Telegram updates (webhook or polling).
    """
    message = update.get("message") or update.get("edited_message")
    if not message:
        return

    text = message.get("text", "").strip()
    chat_id = str(message.get("chat", {}).get("id", ""))
    sender_id = str(message.get("from", {}).get("id", ""))

    if not text or not chat_id:
        return

    # ── Sender authentication ────────────────────────────────────
    _allowed_raw = os.environ.get("ALLOWED_USER_IDS", "")
    _allowed_ids = {uid.strip() for uid in _allowed_raw.split(",") if uid.strip()}
    if _allowed_ids and sender_id not in _allowed_ids:
        from notifier import send_message as _send
        _send(chat_id, "Sorry, you are not authorised to use this bot.")
        logger.warning(f"Unauthorised Telegram access attempt from sender_id={sender_id}")
        return

    job_id = str(uuid.uuid4())
    from notifier import send_briefing, send_message

    # 1. Classify first so the briefing is accurate
    # Shortcut classify runs FIRST — catches task phrases before obvious-chat filter eats them
    _shortcut = _shortcut_classify(text)
    if _shortcut and _shortcut != "memory_capture":
        task_type = _shortcut
        classification = {"task_type": _shortcut, "confidence": 0.95, "is_unknown": False, "has_email_followup": False}
    elif _shortcut == "memory_capture":
        # memory_capture is handled in chat via save_memory tool — treat as chat
        task_type = "chat"
        classification = {"task_type": "chat", "confidence": 0.95, "is_unknown": False, "has_email_followup": False}
    elif _classify_obvious_chat(text):
        task_type = "chat"
        classification = {"task_type": "chat", "confidence": 0.95, "is_unknown": False, "has_email_followup": False}
    else:
        from router import classify_task, extract_metadata
        classification = classify_task(text)
        metadata = extract_metadata(text)
        classification.update(metadata)
        task_type = classification.get("task_type", "unknown")

    # 2. Send briefing (no-op for chat; includes crew + one-line plan for tasks)
    send_briefing(chat_id, task_type, text)

    # 3. Execute
    loop = asyncio.get_running_loop()
    if task_type == "chat":
        # Chat runs in threadpool — non-blocking
        result = await loop.run_in_executor(None, lambda: run_chat(message=text, session_key=chat_id))
        send_message(chat_id, result["result"])
    else:
        # Complex tasks run in threadpool — non-blocking, avoids freezing the polling loop
        crew_session_key = f"{chat_id}:{job_id[:8]}"
        loop.run_in_executor(
            None,
            lambda: _run_background_job(
                task=text,
                from_number=chat_id,
                session_key=crew_session_key,
                job_id=job_id,
                classification=classification,
            )
        )

async def telegram_polling_loop():
    """
    The ultimate fallback: poll for updates instead of waiting for webhooks.
    Bypasses port exposure, SSL, and DNS issues.
    """
    token = os.environ.get("ORCHESTRATOR_TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_POLLING: No token found. Polling disabled.")
        return

    logger.info("TELEGRAM_POLLING: Starting loop...")
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    offset = 0

    # Ensure webhook is cleared so polling works
    try:
        async with httpx.AsyncClient() as client:
            await client.get(f"https://api.telegram.org/bot{token}/deleteWebhook")
    except Exception:
        pass

    while True:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url, params={"offset": offset, "timeout": 20})
                if resp.status_code == 200:
                    data = resp.json()
                    for update in data.get("result", []):
                        offset = update["update_id"] + 1
                        # Process update without blocking the loop
                        asyncio.create_task(process_telegram_update(update))
                elif resp.status_code == 401:
                    logger.error("TELEGRAM_POLLING: Invalid Token. Stopping.")
                    break
                else:
                    await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"TELEGRAM_POLLING: Error: {e}")
            await asyncio.sleep(10)

@app.post("/telegram")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Keep webhook endpoint as a backup, though polling is now primary.
    """
    try:
        body = await request.json()
        background_tasks.add_task(process_telegram_update, body)
    except Exception:
        pass
    return {"ok": True}


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


class HealthReportRequest(BaseModel):
    status: str      # "GREEN", "YELLOW", or "RED"
    report: str      # full Markdown report text
    date: str        # e.g. "2026-04-07"


@app.post("/internal/health-report")
async def receive_health_report(request: HealthReportRequest, req: Request):
    """
    Internal webhook called by the agentsHQ Weekly Health Check remote agent.
    Accepts the report, renders it as HTML, and emails it to all three addresses.
    Protected by X-Internal-Token header — token set via HEALTH_REPORT_TOKEN env var.
    """
    expected_token = os.environ.get("HEALTH_REPORT_TOKEN", "")
    provided_token = req.headers.get("X-Internal-Token", "")
    if not expected_token or provided_token != expected_token:
        raise HTTPException(status_code=401, detail="Unauthorised")

    try:
        from notifier import send_health_check_report
        email_sent = send_health_check_report(request.status, request.report, request.date)
        logger.info(f"Health check report received: status={request.status}, date={request.date}, email_sent={email_sent}")
        return {"ok": True, "email_sent": email_sent}
    except Exception as e:
        logger.error(f"Health report delivery failed: {e}")
        return {"ok": True, "email_sent": False}


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

    # Classify first so the briefing is accurate
    from notifier import send_briefing, send_message
    # Shortcut classify runs FIRST — catches task phrases before obvious-chat filter eats them
    _shortcut = _shortcut_classify(request.task)
    if _shortcut and _shortcut != "memory_capture":
        task_type = _shortcut
        classification = {"task_type": _shortcut, "confidence": 0.95, "is_unknown": False, "has_email_followup": False}
    elif _shortcut == "memory_capture":
        task_type = "chat"
        classification = {"task_type": "chat", "confidence": 0.95, "is_unknown": False, "has_email_followup": False}
    elif _classify_obvious_chat(request.task):
        task_type = "chat"
        classification = {"task_type": "chat", "confidence": 0.95, "is_unknown": False, "has_email_followup": False}
    else:
        from router import classify_task, extract_metadata
        classification = classify_task(request.task)
        metadata = extract_metadata(request.task)
        classification.update(metadata)
        task_type = classification.get("task_type", "unknown")

    send_briefing(request.from_number, task_type, request.task)

    # For chat, run in executor (non-blocking) and deliver directly
    if task_type == "chat":
        import asyncio
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, lambda: run_chat(message=request.task, session_key=request.session_key))
        send_message(request.from_number, result["result"])
        return AsyncTaskResponse(job_id=job_id, status="completed", message="Chat response delivered.")

    # Each crew job gets its own session key to prevent concurrent task collision
    crew_session_key = f"{request.session_key}:{job_id[:8]}"

    # Queue crew job in background
    background_tasks.add_task(
        _run_background_job,
        task=request.task,
        from_number=request.from_number,
        session_key=crew_session_key,
        job_id=job_id,
        classification=classification,
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

        if _classify_obvious_chat(request.task):
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
    """Get conversation history for a Telegram session."""
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
