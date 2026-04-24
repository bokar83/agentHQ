"""
state.py - In-memory system state trackers.

Shared dicts and locks that span handler modules. Kept here so both the
live monolith (orchestrator.py) and the modular shadow (app.py + handlers*)
can import the same object during the cutover.

After the entrypoint flip, the monolith will still import from this module,
so state survives the transition within a single process. A container
restart clears all of these - that is intentional.
"""
import threading

# chat_id -> last completed job metadata
# Used by praise/critique detector to pair feedback with prior output.
_last_completed_job: dict = {}

# chat_id -> active project name
# Set via /switch <project-name>; used as session_key prefix for crews.
_active_project: dict = {}

# Phase 1: pending rejection-feedback windows.
# queue_id -> (chat_id, rejected_at_epoch). Closed by button tap or 5-min TTL.
_PENDING_FEEDBACK_WINDOWS: dict = {}

# Serializes git writes when multiple background jobs try to save outputs
# at the same time. Used by saver.py via the shadow entrypoint.
_git_lock = threading.Lock()

# Praise / critique signal word lists.
# Used by handlers_chat.handle_feedback to decide whether a short message
# is reacting to the last completed job. Short list is the one the monolith
# shipped with; extended list folds in the shadow's emoji/regex coverage.
_PRAISE_SIGNALS = {
    "good job", "great", "well done", "perfect", "excellent",
    "love it", "nice work", "brilliant", "solid", "nailed it",
    "that's great", "awesome", "fantastic", "good work", "nice",
    "wow", "amazing", "spot on", "exactly what i needed",
}

_CRITIQUE_SIGNALS = {
    "wrong", "bad", "not good", "don't like", "fix", "redo",
    "wasn't", "wasn't done", "missed", "forgot", "too long",
    "too short", "off", "incorrect", "weird", "not what",
    "could be better", "needs work", "poorly", "weak",
    "mistake", "error", "change", "broken", "failure",
    "missing", "wrong format",
}

# Emoji signals for praise/critique. Handlers_chat.handle_feedback runs a
# substring check using these sets plus the word lists above.
_PRAISE_EMOJIS = {"👍", "🚀", "🔥", "🙌"}
_CRITIQUE_EMOJIS = {"👎", "❌", "⚠️"}

# Narrow keyword lists kept for any future shortcut heuristics.
# These are NOT used by the live classifier - _shortcut_classify delegates to
# router._keyword_shortcut per docs/routing-architecture.md rule 4. Kept here
# so tools and debug endpoints can introspect without importing router.
_TASK_KEYWORDS = [
    "write", "create", "build", "research", "analyze", "make",
    "draft", "generate", "code", "script", "website", "report",
    "proposal", "post", "email", "article",
    "find", "hunt", "leads", "prospect", "run the", "hunter",
    "news", "brief", "headlines",
    "task", "tasks", "due", "overdue", "notion", "calendar",
    "open tasks", "past due", "pending",
]

_CHAT_PREFIXES = (
    "what is my", "what's my", "how much", "do you", "can you tell",
    "hey", "hi ", "hello", "thanks", "thank you", "what did",
    "do you remember", "remind me", "what have we", "what was",
)
