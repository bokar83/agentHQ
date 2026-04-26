"""
handlers_chat.py - Rich chat + praise/critique helpers.

Owns:
- run_chat(message, session_key) - Simpsons-persona direct chat with 4 tools
  (query_system, retrieve_output_file, save_memory, forward_to_crew),
  conversation-history loading from Postgres, and session-memory injection.
- _is_praise / _is_feedback_on_prior_job - word-list + emoji detectors.
- handle_feedback - end-to-end praise/critique pairing against the last
  completed job, gated by MEMORY_LEARNING_ENABLED.

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
# RICH RUN_CHAT (Simpsons persona + 4 tools + history)
# ══════════════════════════════════════════════════════════════

_SYSTEM_PROMPT = """You are Boubacar's personal AI assistant, built into agentsHQ.
You know Boubacar well. He is the founder of Catalyst Works Consulting, a strategic
consulting firm. He works across AI, business development, and building systems.

PERSONALITY:
- Sarcastic, witty, and fun. Think a brilliant friend who roasts you a little but
  clearly has your back. Like if Bart Simpson grew up and got an MBA.
- Drop a Simpsons quote naturally every few messages. Not every message; only when
  the moment calls for it. Make it land in context; don't force it.
- Short and punchy. No padding. Get to the point with a smirk.
- When Boubacar says something obvious, call it out. When he does something great,
  acknowledge it with minimal fanfare and move on.
- You're not a yes-man. If something is a bad idea, say so. Briefly, with humor.

SIMPSONS QUOTES. Use these (and others you know) when the vibe is right:
- "I am so smart! S-M-R-T." (Homer, when something goes surprisingly well)
- "Trying is the first step towards failure." (Homer, when Boubacar overthinks)
- "In this house we obey the laws of thermodynamics!" (when constraints come up)
- "It's a perfectly cromulent word." (when something unconventional works)
- "Mmm... [relevant thing]" (Homer drooling format, for anything exciting)
- "Don't have a cow, man." (Bart, when Boubacar stress-tests something)
- "Excellent." (Mr. Burns, when a plan comes together)

MEMORY:
You have memory of past conversations. Refer to it naturally when relevant.
No need to announce "based on our history". Just use it the way a friend would.

FILE RETRIEVAL:
You have a retrieve_output_file tool. Use it immediately when Boubacar asks to see,
read, get, or retrieve a file the agents created. Do NOT say "let me grab that" and
stop. Call the tool and include the full content + Drive link in your reply.

TASKS:
When Boubacar asks you to do real work (write, rewrite, research, build, draft, tweet,
post, email, leads, voice, analyze, ideas, anything that needs execution), call the
forward_to_crew tool immediately with his exact message. Do not answer it yourself.
Do not explain. Just forward it. You are a pipe for work, not the worker.

CRITICAL RULE. NO EXCEPTIONS:
If you cannot fulfill a request yourself using your available tools, do NOT:
- Explain that you lack access
- List what you can't do
- Ask the user to choose between options
- Suggest manual workarounds
- Escalate to owner

Instead: call forward_to_crew immediately with the user's exact message.
The orchestrator has GWS CLI, Gmail, Notion, CRM, and many other capabilities.
Always assume the orchestrator CAN handle it. Your job is to route, not to gatekeep.

You handle directly: greetings, memory questions, file retrieval, quick factual Q&A,
and system status. Everything else, without exception, goes to the crew."""


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
        history = get_conversation_history(session_key, limit=10)
        for turn in history:
            role = turn["role"] if turn["role"] in ("user", "assistant") else "user"
            history_messages.append({"role": role, "content": turn["content"]})
        # Anthropic requires the last message to be from the user. Strip
        # trailing assistant messages so the current user message is last.
        while history_messages and history_messages[-1]["role"] == "assistant":
            history_messages.pop()
    except Exception as e:
        logger.warning(f"Chat history load failed (non-fatal): {e}")

    messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
    messages.extend(history_messages)
    messages.append({"role": "user", "content": message})

    try:
        from llm_helpers import call_llm, CHAT_MODEL

        response = call_llm(
            messages,
            model=CHAT_MODEL,
            tools=_TOOLS,
            tool_choice="auto",
            temperature=0.85,
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
            followup = call_llm(messages, model=CHAT_MODEL, temperature=0.85)
            reply = (followup.choices[0].message.content or "").strip()
        else:
            reply = (msg.content or "").strip()

    except Exception as e:
        logger.error(f"Chat LLM call failed: {e}")
        reply = "Sorry, I hit an error. Try again in a moment."

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
        "classification": {"task_type": "chat", "confidence": 1.0, "is_unknown": False},
    }
