"""
handlers_chat.py - Rich chat + praise/critique helpers.

Owns:
- run_chat(message, session_key) - command-center chat with 4 tools
  (query_system, retrieve_output_file, save_memory, forward_to_crew),
  conversation-history loading from Postgres, and session-memory injection.
- _is_praise / _is_feedback_on_prior_job - word-list + emoji detectors.
- handle_feedback - end-to-end praise/critique pairing against the last
  completed job, gated by MEMORY_LEARNING_ENABLED.
- run_chat_with_buttons - single-send wrapper (Fix 4: no double-send).

Word lists, emoji sets, and the chat prompt live here. Shared module-level
state (_last_completed_job etc) lives in state.py so the monolith and the
shadow both see the same dict during the cutover.
"""
import json
import logging
import os
import threading
from datetime import datetime
from typing import Optional

from state import _last_completed_job, _PRAISE_SIGNALS, _CRITIQUE_SIGNALS, _PRAISE_EMOJIS, _CRITIQUE_EMOJIS

logger = logging.getLogger("agentsHQ.handlers_chat")


# ══════════════════════════════════════════════════════════════
# PRAISE / CRITIQUE DETECTION
# ══════════════════════════════════════════════════════════════

def _is_praise(text: str) -> bool:
    """Return True if the message is short explicit praise (words or emoji)."""
    t = (text or "").lower().strip()
    if not t or len(t) > 80:
        return False
    if any(p in t for p in _PRAISE_SIGNALS):
        return True
    return any(emoji in text for emoji in _PRAISE_EMOJIS)


def _is_feedback_on_prior_job(text: str, chat_id: str) -> bool:
    """
    Return True if the message looks like critique on the last completed job.
    Requires: job delivered within 60 min AND critique signal words/emoji.
    """
    if chat_id not in _last_completed_job:
        return False
    job = _last_completed_job[chat_id]
    elapsed = (datetime.utcnow() - job["delivered_at"]).total_seconds()
    if elapsed > 3600:
        return False
    t = (text or "").lower()
    if any(s in t for s in _CRITIQUE_SIGNALS):
        return True
    return any(emoji in text for emoji in _CRITIQUE_EMOJIS)


def handle_feedback(text: str, chat_id: str) -> bool:
    """
    Process potential praise/critique. Returns True if the message was
    consumed as feedback, False otherwise. Gated by MEMORY_LEARNING_ENABLED.
    """
    if os.environ.get("MEMORY_LEARNING_ENABLED", "false").lower() != "true":
        return False

    from notifier import send_message

    if _is_praise(text) and chat_id in _last_completed_job:
        prior = _last_completed_job[chat_id]
        logger.info(f"Praise detected for job {prior['job_id']} (task_type={prior['task_type']})")
        from memory import extract_and_save_learnings
        threading.Thread(
            target=extract_and_save_learnings,
            args=(prior["task_request"], prior["task_type"], prior["result_summary"], "preference"),
            daemon=True,
        ).start()
        send_message(chat_id, "Got it, noted as a good pattern.")
        return True

    if _is_feedback_on_prior_job(text, chat_id):
        prior = _last_completed_job[chat_id]
        logger.info(f"Critique detected for job {prior['job_id']} (task_type={prior['task_type']})")
        from memory import extract_negative_lesson
        threading.Thread(
            target=extract_negative_lesson,
            args=(text, prior["task_type"], prior["result_summary"], chat_id),
            daemon=True,
        ).start()
        send_message(chat_id, "Got it, I'll avoid that next time.")
        return True

    return False


# ══════════════════════════════════════════════════════════════
# SYSTEM PROMPT (M9a: operator persona + JSON schema + sandbox)
# ══════════════════════════════════════════════════════════════

_SYSTEM_PROMPT_TEMPLATE = """You are Boubacar's agentsHQ command center.

You are a dispatcher and execution surface. You have direct access to the agentsHQ
system: content board, approval queue, spend, heartbeats, crew execution, Notion, and publishing.

RESPONSE FORMAT (required):
Always return a valid JSON object:
  {{"reply": "...", "actions": [...optional...], "artifact": {{...optional...}}}}

"reply": your response. Plain text or markdown.
"actions": optional array of {{"label": "Button text", "callback_data": "action:id"}}.
  Include only when offering a one-tap action. Omit otherwise.
"artifact": optional {{"type": "html"|"svg"|"markdown", "content": "...", "artifact_id": "..."}}.
  Include when generating a visual or document artifact.

SANDBOX MODE: {sandbox_status}
When sandbox is active, write actions are simulated. Tell the user.

BEHAVIOR:
When asked to do something, do it with your tools. Do not explain what you are about to do.
For write actions (approve, reject, queue): confirm once before executing.
For publish to a live platform: confirm once with exact text and platform, then execute.
For drafting: produce a first draft immediately. Ask for feedback after.
For tasks beyond your tool set: call forward_to_crew immediately. Never explain limitations.
  The orchestrator has many capabilities. Always assume it can handle the task.

Long-running tasks return a job ID. Tell the user the task is running and you will ping them with the result.

RESPONSE FORMAT FOR TELEGRAM: Keep reply under 3000 characters. Format data as plain text tables.
RESPONSE FORMAT FOR WEB: Full markdown is rendered. Tables, code blocks, bullet lists all work.

You remember recent sessions. Reference prior work naturally when relevant.
Short and direct. Get to the point.

SIMPSONS: Drop a Simpsons quote naturally every few messages when the vibe is right, never forced."""


def _build_system_prompt() -> str:
    from llm_helpers import CHAT_SANDBOX
    sandbox_status = "ACTIVE: write actions are simulated, not executed." if CHAT_SANDBOX else "inactive."
    return _SYSTEM_PROMPT_TEMPLATE.format(sandbox_status=sandbox_status)


# Backward-compat alias for any code that imports _SYSTEM_PROMPT directly.
_SYSTEM_PROMPT = _SYSTEM_PROMPT_TEMPLATE


# ══════════════════════════════════════════════════════════════
# RICH RUN_CHAT (command center + 4 tools + history)
# ══════════════════════════════════════════════════════════════

_TOOLS = [
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
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
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
                        "description": "Partial filename or keywords to match. E.g. 'disruptive ai startups' or '5-most-disruptive'.",
                    }
                },
                "required": ["filename_hint"],
            },
        },
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
                "Do NOT call for ideas, use the crew for that."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "fact": {
                        "type": "string",
                        "description": "The fact or preference to save, written as a complete sentence.",
                    },
                    "category": {
                        "type": "string",
                        "description": "Category label e.g. 'brand', 'preference', 'contact', 'system'.",
                    },
                },
                "required": ["fact"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "forward_to_crew",
            "description": (
                "Forward a task to the agentsHQ crew for execution. "
                "Call this for ANY real work: writing, rewriting, researching, building, "
                "voice matching, tweet polishing, post drafting, email drafting, "
                "lead queries, ideas capture, or anything requiring agents. "
                "Pass the user's exact original message as task_text."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "task_text": {
                        "type": "string",
                        "description": "The user's exact message to forward to the crew.",
                    }
                },
                "required": ["task_text"],
            },
        },
    },
]


def _retrieve_output_file(filename_hint: str) -> str:
    """Find a matching output file and return its content + Drive link."""
    output_dir = os.environ.get("AGENTS_OUTPUT_DIR", "/app/outputs")
    all_files = []
    try:
        for root, _dirs, files in os.walk(output_dir):
            for f in files:
                all_files.append(os.path.join(root, f))
    except Exception as e:
        return f"Could not scan output directory: {e}"

    if not all_files:
        return "No output files found in the outputs directory."

    hint_lower = filename_hint.lower()
    hint_words = hint_lower.replace("-", " ").replace("_", " ").split()
    scored = []
    for fp in all_files:
        name = os.path.basename(fp).lower().replace("-", " ").replace("_", " ")
        score = sum(1 for w in hint_words if w in name)
        scored.append((score, os.path.getmtime(fp), fp))

    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    best_score, _mtime, best_path = scored[0]

    if best_score == 0:
        all_files.sort(key=os.path.getmtime, reverse=True)
        best_path = all_files[0]

    try:
        with open(best_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return f"Found file {os.path.basename(best_path)} but could not read it: {e}"

    drive_url: Optional[str] = None
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
        result_parts.append("\n[... content truncated, reply 'more' for the rest]")
    return "\n".join(result_parts)


def run_chat(message: str, session_key: str = "default") -> dict:
    """
    Direct conversational response, no crew, no tasks.
    Uses the last 10 turns of session history so the bot remembers
    everything discussed. Fast (single LLM call, ~2-3 seconds).

    Returns M9 schema: {"reply": "...", "actions": [...], ...legacy keys...}
    """
    start_time = datetime.now()

    # Record session in Postgres (non-fatal if table not yet created).
    try:
        from session_store import upsert_session
        upsert_session(session_id=session_key, agent_name="chat", channel="telegram")
    except Exception as _sess_e:
        logger.warning(f"session_store upsert skipped: {_sess_e}")

    # Load conversation history (most-recent-last).
    history_messages = []
    try:
        from memory import get_conversation_history
        history = get_conversation_history(session_key, limit=100)
        for turn in history:
            role = turn["role"] if turn["role"] in ("user", "assistant") else "user"
            history_messages.append({"role": role, "content": turn["content"]})
        # Anthropic requires the last message to be from the user. Strip
        # trailing assistant messages so the current user message is last.
        while history_messages and history_messages[-1]["role"] == "assistant":
            history_messages.pop()
    except Exception as e:
        logger.warning(f"Chat history load failed (non-fatal): {e}")

    try:
        from prompt_loader import load_system_prompt
        _active_prompt = load_system_prompt("chat", fallback=_build_system_prompt())
    except Exception as _pl_e:
        logger.warning(f"prompt_loader failed, using hardcoded prompt: {_pl_e}")
        _active_prompt = _build_system_prompt()

    messages = [{"role": "system", "content": _active_prompt}]
    messages.extend(history_messages)
    messages.append({"role": "user", "content": message})

    actions: list = []

    try:
        from llm_helpers import call_llm, CHAT_MODEL, CHAT_TEMPERATURE, CHAT_SANDBOX

        response = call_llm(
            messages,
            model=CHAT_MODEL,
            tools=_TOOLS,
            tool_choice="auto",
            temperature=CHAT_TEMPERATURE,
        )

        msg = response.choices[0].message

        if msg.tool_calls:
            messages.append(msg)
            for tool_call in msg.tool_calls:
                fn_name = tool_call.function.name
                if fn_name == "query_system":
                    from utils import _query_system
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
                elif fn_name == "forward_to_crew":
                    args = json.loads(tool_call.function.arguments or "{}")
                    task_text = args.get("task_text", message)
                    if CHAT_SANDBOX:
                        tool_result = f"[SANDBOX] Would have forwarded to crew: {task_text[:120]}"
                        logger.info(f"Chat sandbox: suppressed forward_to_crew for: {task_text[:60]}")
                    else:
                        try:
                            from engine import run_orchestrator
                            fwd_result = run_orchestrator(
                                task_request=task_text,
                                from_number=session_key,
                                session_key=session_key,
                            )
                            tool_result = (
                                fwd_result.get("result")
                                or fwd_result.get("deliverable")
                                or "Crew completed the task."
                            )
                            logger.info(f"Chat forwarded to crew: {task_text[:60]}")
                        except Exception as fwd_e:
                            tool_result = f"Crew error: {fwd_e}"
                            logger.error(f"forward_to_crew failed: {fwd_e}")
                else:
                    tool_result = "Unknown tool."
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,
                })
            followup = call_llm(messages, model=CHAT_MODEL, temperature=CHAT_TEMPERATURE)
            raw_reply = (followup.choices[0].message.content or "").strip()
        else:
            raw_reply = (msg.content or "").strip()

        # Extract human-readable reply. Never lets raw JSON reach the user.
        reply = _extract_reply(raw_reply)
        try:
            parsed = json.loads(raw_reply.strip())
            actions = parsed.get("actions") or []
        except (json.JSONDecodeError, AttributeError, TypeError):
            actions = []

    except Exception as e:
        logger.error(f"Chat LLM call failed: {e}")
        reply = "Sorry, I hit an error. Try again in a moment."
        actions = []

    # Save text-only turns (never save actions arrays or tool messages).
    try:
        from memory import save_conversation_turn
        save_conversation_turn(session_key, "user", message)
        save_conversation_turn(session_key, "assistant", reply)
    except Exception as e:
        logger.warning(f"Chat history save failed (non-fatal): {e}")

    execution_time = (datetime.now() - start_time).total_seconds()
    logger.info(f"Chat response for session '{session_key}' in {execution_time:.1f}s")

    return {
        "reply": reply,
        "actions": actions,
        # Legacy keys kept for callers that still read result/full_output.
        "success": True,
        "result": reply,
        "full_output": reply,
        "task_type": "chat",
        "files_created": [],
        "execution_time": execution_time,
        "classification": {"task_type": "chat", "confidence": 1.0, "is_unknown": False},
    }


def run_chat_with_buttons(
    message: str,
    session_key: str,
    chat_id: str,
    channel: str = "telegram",
) -> None:
    """
    Single-send wrapper for Telegram: calls run_chat() then sends exactly one
    message -- with buttons if actions are present, plain text otherwise.
    Fixes the double-send bug where handlers.py called both send_message_with_buttons
    AND send_message in some code paths.
    """
    from notifier import send_message, send_message_with_buttons
    result = run_chat(message, session_key)
    if result.get("actions"):
        buttons = [[(a["label"], a["callback_data"]) for a in result["actions"]]]
        send_message_with_buttons(chat_id, result["reply"], buttons)
    else:
        send_message(chat_id, result["reply"])


# ══════════════════════════════════════════════════════════════
# ATLAS WEB CHAT (M9b): stateful, artifact-aware, channel="web"
# ══════════════════════════════════════════════════════════════

import re as _re
import uuid as _uuid
import time as _time


def _extract_reply(raw: str) -> str:
    """
    Pull the human-readable reply out of whatever the model returned.
    Handles three cases in priority order:
      1. Valid M9 JSON with a "reply" key -> extract and return that string
      2. Raw JSON-looking string (starts with { or [) -> strip the shell,
         try to pull "reply"/"text"/"content"/"message", else return empty
      3. Plain text -> return as-is
    The goal: the user NEVER sees raw JSON, HTML tags, or code wrapper
    unless they explicitly asked for code.
    """
    if not raw:
        return ""
    stripped = raw.strip()

    # Try standard M9 JSON parse first
    if stripped.startswith("{"):
        try:
            parsed = json.loads(stripped)
            # M9 schema: {"reply": "...", "actions": [...]}
            if "reply" in parsed:
                return (parsed["reply"] or "").strip()
            # Fallback keys used by some crew outputs
            for key in ("text", "content", "message", "result", "output"):
                if key in parsed and isinstance(parsed[key], str):
                    return parsed[key].strip()
            # JSON object but no recognisable text key -- return empty rather than dumping JSON
            return ""
        except (json.JSONDecodeError, TypeError):
            pass

    # Not valid JSON -- plain text or markdown, return as-is
    return stripped


def _resolve_artifact_refs(text: str) -> str:
    """Replace [artifact:art_id] placeholders with full artifact content from Postgres."""
    pattern = _re.compile(r"\[artifact:([a-zA-Z0-9_\-]+)\]")
    def _replace(m):
        art_id = m.group(1)
        try:
            from db import get_chat_artifact
            row = get_chat_artifact(art_id)
            if row:
                return f"[Artifact {art_id} ({row['artifact_type']})]\n{row['content']}"
        except Exception:
            pass
        return m.group(0)
    return pattern.sub(_replace, text)


def _evict_expired_confirms() -> None:
    """Remove confirm_store entries older than 5 minutes."""
    from state import _confirm_store
    now = _time.time()
    expired = [k for k, v in _confirm_store.items() if now - v.get("ts_created", 0) > 300]
    for k in expired:
        _confirm_store.pop(k, None)


def run_atlas_chat(messages: list, session_key: str, channel: str = "web") -> dict:
    """
    Atlas web chat handler. Loads 100 turns from Postgres (same as run_chat),
    merges with current user message, resolves artifact refs, calls the model,
    stores artifacts, dispatches forward_to_crew via confirm gate.

    Returns M9 schema: {"reply": "...", "actions": [...], "artifact": {...}, "job_id": "..."}
    """
    from llm_helpers import ATLAS_CHAT_MODEL, CHAT_TEMPERATURE, CHAT_SANDBOX

    _evict_expired_confirms()

    # Resolve any [artifact:id] placeholders in the latest user message
    if messages and messages[-1].get("role") == "user":
        messages[-1]["content"] = _resolve_artifact_refs(messages[-1]["content"])

    # Load Postgres history (100 turns) -- same depth as run_chat
    history_messages: list = []
    try:
        from memory import get_conversation_history
        history = get_conversation_history(session_key, limit=100)
        for turn in history:
            role = turn["role"] if turn["role"] in ("user", "assistant") else "user"
            history_messages.append({"role": role, "content": turn["content"]})
        while history_messages and history_messages[-1]["role"] == "assistant":
            history_messages.pop()
    except Exception as e:
        logger.warning(f"Atlas chat history load failed (non-fatal): {e}")

    try:
        from prompt_loader import load_system_prompt
        system_prompt = load_system_prompt("chat", fallback=_build_system_prompt())
    except Exception:
        system_prompt = _build_system_prompt()

    # Use postgres history + current user message; ignore client-managed prior turns
    current_user_msg = messages[-1] if messages and messages[-1].get("role") == "user" else None
    merged = history_messages + ([current_user_msg] if current_user_msg else messages)

    full_messages = [{"role": "system", "content": system_prompt}] + merged
    turn_number = len(merged)

    actions: list = []
    artifact: dict | None = None
    job_id: str | None = None

    try:
        from llm_helpers import call_llm

        response = call_llm(
            full_messages,
            model=ATLAS_CHAT_MODEL,
            tools=_TOOLS,
            tool_choice="auto",
            temperature=CHAT_TEMPERATURE,
        )

        msg = response.choices[0].message

        if msg.tool_calls:
            full_messages.append(msg)
            for tool_call in msg.tool_calls:
                fn_name = tool_call.function.name
                if fn_name == "query_system":
                    from utils import _query_system
                    tool_result = _query_system()
                elif fn_name == "retrieve_output_file":
                    args = json.loads(tool_call.function.arguments or "{}")
                    tool_result = _retrieve_output_file(args.get("filename_hint", ""))
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
                        tool_result = f"Saved to memory: {fact}"
                    except Exception as mem_e:
                        tool_result = f"Memory save failed: {mem_e}"
                elif fn_name == "forward_to_crew":
                    args = json.loads(tool_call.function.arguments or "{}")
                    task_text = args.get("task_text", "")
                    if CHAT_SANDBOX:
                        tool_result = f"[SANDBOX] Would have forwarded to crew: {task_text[:120]}"
                    else:
                        # Write-action confirmation gate
                        from state import _confirm_store
                        confirm_token = f"conf_{_uuid.uuid4().hex[:10]}"
                        _confirm_store[confirm_token] = {
                            "action": "forward_to_crew",
                            "payload": {"task_text": task_text},
                            "session_key": session_key,
                            "ts_created": _time.time(),
                        }
                        tool_result = (
                            f"Ready to run: {task_text[:120]}. "
                            f"Confirm token: {confirm_token}"
                        )
                        actions.append({
                            "label": "Confirm",
                            "callback_data": f"confirm:{confirm_token}",
                        })
                        actions.append({
                            "label": "Cancel",
                            "callback_data": f"cancel:{confirm_token}",
                        })
                else:
                    tool_result = "Unknown tool."

                full_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,
                })

            followup = call_llm(full_messages, model=ATLAS_CHAT_MODEL, temperature=CHAT_TEMPERATURE)
            raw_reply = (followup.choices[0].message.content or "").strip()
        else:
            raw_reply = (msg.content or "").strip()

        # Extract human-readable reply. Never lets raw JSON reach the user.
        reply = _extract_reply(raw_reply)
        try:
            parsed = json.loads(raw_reply.strip())
            if not actions:
                actions = parsed.get("actions") or []
            parsed_artifact = parsed.get("artifact")
            if parsed_artifact and parsed_artifact.get("content"):
                art_id = parsed_artifact.get("artifact_id") or f"art_{_uuid.uuid4().hex[:8]}"
                art_type = parsed_artifact.get("type", "html")
                try:
                    from db import save_chat_artifact
                    save_chat_artifact(art_id, session_key, turn_number, art_type,
                                       parsed_artifact["content"])
                except Exception as db_e:
                    logger.warning(f"artifact save failed: {db_e}")
                artifact = {"artifact_id": art_id, "type": art_type,
                            "content": parsed_artifact["content"]}
        except (json.JSONDecodeError, AttributeError, TypeError):
            pass

    except Exception as e:
        logger.error(f"run_atlas_chat LLM call failed: {e}")
        reply = "Sorry, I hit an error. Try again in a moment."

    # Save text turns only
    try:
        from memory import save_conversation_turn
        if messages and messages[-1].get("role") == "user":
            save_conversation_turn(session_key, "user", messages[-1]["content"][:2000])
        save_conversation_turn(session_key, "assistant", reply)
    except Exception as e:
        logger.warning(f"Atlas chat history save failed: {e}")

    result: dict = {"reply": reply, "actions": actions}
    if artifact:
        result["artifact"] = artifact
    if job_id:
        result["job_id"] = job_id
    return result
