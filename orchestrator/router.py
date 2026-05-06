"""
router.py — Task Classification Engine
=======================================
Maps incoming user requests to the correct crew type.
Used by engine.run_orchestrator to determine which crew to assemble.
"""

import os
import re
import logging

logger = logging.getLogger(__name__)

# Named model constant -- update here when model version changes, nowhere else
ROUTER_LLM_MODEL = "anthropic/claude-haiku-4.5"

# Research-shaped prompts: location+service queries, explicit research framing,
# and multi-source web-research intent. These route to research_report (handled
# by the research_engine bypass in engine.py Step 3a). Needed because the keyword
# loop would otherwise misroute "mechanic shops in 84095" to hunter_task and
# "research report on X" to app_build/github_task.
_RESEARCH_REPORT_PHRASES = (
    "research report on", "research report about", "write a research report",
    "find me", "list of", "give me a list",
    "compare options", "compare the options", "compare my options",
    "best options for", "top options for",
    "what are the best", "what are the top",
    "near me", "nearby",
)

_RESEARCH_REPORT_REGEXES = (
    # Any 5-digit zip code in the message is a strong signal of a location query.
    # e.g. "mechanic shops in South Jordan 84095" or "list 84095 plumbers"
    re.compile(r"\b\d{5}\b"),
    # "<noun(s)> in <City, ST>": e.g. "dentists in Denver, CO"
    re.compile(r"\b[a-z][a-z\s]{2,40}\s+in\s+[a-z][a-z\s]{2,30},\s*[a-z]{2}\b"),
    # "<noun(s)> near <City or zip>": e.g. "plumbers near Salt Lake"
    re.compile(r"\b[a-z][a-z\s]{2,40}\s+near\s+(?:\d{5}|[a-z][a-z\s]{2,30})\b"),
    # "best <noun(s)> in <City>": e.g. "best sushi in austin"
    re.compile(r"\bbest\s+[a-z][a-z\s]{2,40}\s+in\s+[a-z][a-z\s]{2,30}\b"),
)


def _looks_like_research_report(msg: str) -> bool:
    """Return True when the message matches a research-shaped pattern."""
    if any(phrase in msg for phrase in _RESEARCH_REPORT_PHRASES):
        return True
    return any(rx.search(msg) for rx in _RESEARCH_REPORT_REGEXES)

# ---------------------------------------------------------------------------
# TASK_TYPES registry
# ---------------------------------------------------------------------------
# Each entry:
#   description  — human-readable label shown in Telegram status messages
#   keywords     — list of trigger phrases (case-insensitive substring match)
#   crew         — crew key passed to assemble_crew()
# ---------------------------------------------------------------------------

TASK_TYPES = {
    "website_build": {
        "description": "Premium landing page / website build",
        "keywords": ["website", "landing page", "web presence", "build a site", "site layout"],
        "crew": "website_crew",
    },
    "app_build": {
        "description": "Interactive web app / tool build",
        "keywords": ["app", "tool", "calculator", "dashboard", "form", "tracker", "build an app"],
        "crew": "app_crew",
    },
    "vercel_task": {
        "description": "Vercel deployment & monitoring",
        "keywords": ["vercel", "deploy", "build status", "logs", "projects"],
        "crew": "code_crew",
    },
    "github_task": {
        "description": "GitHub repository & PR management",
        "keywords": ["github", "repo", "repository", "pull request", "open pr", "merge pr", "review pr", "create pr", "close pr", "github issue"],
        "crew": "code_crew",
    },
    "notion_tasks": {
        "description": "Query Notion tasks — open, due today, overdue, or past due",
        "keywords": [
            "open tasks", "due today", "past due", "overdue", "tasks due",
            "tasks in notion", "notion tasks", "what tasks", "my tasks",
            "tasks that are due", "outstanding tasks", "incomplete tasks",
            "analytics", "engagement stats", "performance stats",
        ],
        "crew": "notion_tasks_crew",
    },
    "notion_task": {
        "description": "Notion database & architecting",
        "keywords": ["notion", "database", "log", "page", "dashboard", "wiki"],
        "crew": "notion_overhaul",
    },
    "practice_runner_task": {
        "description": "Practice Runner Mission execution",
        "keywords": ["practice runner", "marathon prep", "running prep", "training plan"],
        "crew": "unknown_crew",
    },
    "research_report": {
        "description": "Research & report writing",
        "keywords": [
            "research", "write a report", "find information",
            "summarize", "analyse", "analyze", "deep dive", "compare",
        ],
        "crew": "research_crew",
    },
    "inline_post_review": {
        "description": "Review & polish a social post provided inline in the message",
        "keywords": [
            "ready to publish", "is it ready", "review this post", "review my post",
            "can we make it stronger", "improve my voice", "improve our reach",
            "strengthen the post", "polish this post", "voice check this",
            "make this tweet", "make this post", "make this better",
            "rewrite this", "in my voice", "full on boubacar",
            "not my voice", "write in my voice",
        ],
        "crew": "social_crew",
    },
    "social_content": {
        "description": "Social media post drafting",
        "keywords": [
            "write a post", "linkedin post", "twitter post", "x post",
            "social post", "draft post", "content post", "instagram", "caption",
            "write me a post", "create a post",
            "schedule post", "schedule a post", "schedule for linkedin",
        ],
        "crew": "social_crew",
    },
    "newsletter": {
        "description": "Newsletter drafting and email content",
        "keywords": [
            "newsletter", "write a newsletter", "draft newsletter", "email newsletter",
            "weekly newsletter", "monthly newsletter", "newsletter issue",
            "email blast", "subscriber email", "nurture email", "email content",
        ],
        "crew": "newsletter_crew",
    },
    "linkedin_x_campaign": {
        "description": "Multi-platform content campaign",
        "keywords": ["linkedin and x", "7 posts", "post campaign", "linkedin x posts", "content series"],
        "crew": "linkedin_x_crew",
    },
    "code_task": {
        "description": "Code engineering & debugging",
        "keywords": ["code", "script", "function", "debug", "build", "automate"],
        "crew": "code_crew",
    },
    "crm_query": {
        "description": "Query CRM stats — lead counts, statuses, contacted, pipeline",
        "keywords": [
            "how many leads", "leads contacted", "lead count", "crm stats",
            "leads in the crm", "total leads", "how many contacts", "pipeline stats",
            "leads by status", "leads with email", "leads replied", "leads booked",
            "show me leads", "list leads", "who have been contacted", "contacted leads",
            "crm summary", "leads industry", "how many prospects",
            "open leads", "how many open", "uncontacted leads",
        ],
        "crew": "crm_query_crew",
    },
    "crm_outreach": {
        "description": "Cold outreach — create Gmail drafts for uncontacted CRM leads",
        "keywords": [
            "contact leads", "email leads", "cold outreach", "outreach drafts",
            "draft outreach", "cold email leads", "email the leads", "outreach emails",
            "draft cold emails", "email prospects", "send outreach",
        ],
        "crew": "crm_outreach_crew",
    },
    "mark_outreach_sent": {
        "description": "Mark drafted outreach emails as sent — update lead status to messaged",
        "keywords": [
            "mark as contacted", "mark contacted", "mark as sent", "emails sent",
            "i sent the emails", "mark outreach sent", "mark sent", "sent the drafts",
            "emails were sent", "outreach sent", "mark leads contacted",
            "i sent them", "sent emails", "emails are sent",
        ],
        "crew": "mark_outreach_sent_crew",
    },
    "general_writing": {
        "description": "Drafting letters, emails, and documents",
        "keywords": ["write", "draft", "letter", "email", "document"],
        "crew": "writing_crew",
    },
    "voice_polishing": {
        "description": "Humanizing content with Boub AI Voice",
        "keywords": ["humanize", "polish", "voice match", "boub voice", "boubacar voice"],
        "crew": "voice_polisher_crew",
    },
    "hunter_task": {
        "description": "Lead sourcing & prospect hunting",
        "keywords": ["find leads", "prospect", "utah leads", "growth engine", "hunter"],
        "crew": "hunter_crew",
    },
    "skill_build": {
        "description": "Building new tools & skills (CLI-Anything)",
        "keywords": ["colonize", "build tool", "wrap software", "cli-anything"],
        "crew": "unknown_crew",
    },
    "agent_creation": {
        "description": "Create a new agent or skill for the agentsHQ system",
        "keywords": [
            "build an agent", "create an agent", "agent build", "new agent",
            "build agent", "create agent", "make an agent", "agent creation",
            "build a new agent", "create a new agent", "new skill", "build a skill",
            "create a skill", "make a skill",
        ],
        "crew": "agent_creator_crew",
    },
    "content_board_fetch": {
        "description": "Fetch posts from the Notion Content Board by status (Queued, Ready, Draft, Idea, etc.)",
        "keywords": [
            "content board", "posts from content board", "content board posts",
            "queued posts", "get queued", "fetch queued", "pull queued", "show queued",
            "ready posts", "get ready", "fetch ready", "pull ready", "show ready",
            "draft posts", "get drafts", "fetch drafts", "pull drafts", "show drafts",
            "idea posts", "get ideas", "fetch ideas", "pull ideas", "show ideas from content",
            "in review posts", "posts in review",
            "pull posts", "get posts from notion", "fetch posts", "show me posts",
            "pull linkedin posts", "get linkedin posts", "queued from notion",
            "queued linkedin", "queued content",
            "approve post", "approve the post", "approve queued", "approve content",
        ],
        "crew": "content_board_fetch_crew",
    },
    "gws_task": {
        "description": "Google Workspace automation (Gmail/Calendar)",
        "keywords": [
            "calendar", "add event", "check schedule", "gmail", "draft email", "search email",
            "email me", "send me an email", "send email to me", "email me the", "email me a"
        ],
        "crew": "gws_crew",
    },
    "chat": {
        "description": "General chat / Q&A — greetings, casual questions, no specific task",
        "keywords": [],
        "crew": "chat_crew",
    },
    "doc_routing": {
        "description": "Classify and route an incoming document",
        "keywords": ["doc_routing:", "classify document", "route document", "taxonomy routing"],
        "crew": "doc_routing_crew",
    },
    "forge_kpi_refresh": {
        "description": "Re-run the Forge KPI refresh that updates The Forge Notion dashboard",
        "keywords": ["kpi refresh", "forge refresh", "run kpi", "re-run kpi", "rerun kpi",
                     "6am refresh", "6am kpi", "refresh the forge", "update the forge",
                     "run the forge", "forge dashboard", "update kpi", "refresh kpi",
                     "forge kpi", "the forge", "re-run the 6am"],
        "crew": "forge_kpi_crew",
    },
    "notion_capture": {
        "description": "Save an idea, thought, or note to the agentsHQ Ideas database, or list/retrieve existing ideas",
        "keywords": [
            "add to ideas", "save idea", "ideas database", "add to our ideas",
            "capture idea", "log idea", "add idea", "store idea",
            "list ideas", "show ideas", "show me ideas", "show me the list of ideas",
            "what ideas", "all ideas", "ideas list", "retrieve ideas",
            "add this idea", "put in ideas", "save this to ideas",
            "my list of ideas", "a list of my ideas", "list of my ideas",
            "send me my ideas", "see my ideas", "show my ideas", "get my ideas",
            "fetch my ideas", "pull my ideas", "see a list of",
            "suggestions on what i should do next",
        ],
        "crew": "notion_capture_crew",
    },
    "content_review": {
        "description": "Review Ready social posts against Boubacar's voice standards before Drive push",
        "keywords": ["review content", "review posts", "content review", "review my posts",
                     "check the posts", "check content", "review the content board",
                     "review linkedin posts", "review x posts", "quality check posts",
                     "post review", "check my posts", "voice check", "run content review"],
        "crew": "content_review_crew",
    },
    "schedule_content": {
        "description": "Schedule a post to the Notion Content Board with a date. Does NOT publish to social media.",
        "keywords": [
            "schedule it", "schedule this post", "schedule for today", "schedule for tomorrow",
            "schedule for monday", "schedule for", "add to content board scheduled",
            "schedule variation", "schedule post for", "schedule the post",
            "add scheduled date", "set scheduled date",
        ],
        "crew": "schedule_content_crew",
    },
    "content_push_to_drive": {
        "description": "Push approved In Review social posts to Google Drive and update Notion",
        "keywords": ["push content to drive", "push to drive", "create drive docs",
                     "push posts to drive", "send to drive", "drive push",
                     "create google docs", "push approved posts",
                     "push content", "posts to drive", "content to drive"],
        "crew": "content_drive_crew",
    },
    "design_review": {
        "description": "Review and enhance a visual design artifact",
        "keywords": [
            "review this design", "enhance this design", "design review",
            "improve the design", "make this look better", "design feedback",
            "review the design", "design critique", "enhance the design",
            "fix the design", "design check", "visual review",
        ],
        "crew": "design_review_crew",
    },
    "inbound_lead": {
        "description": "Webhook-triggered inbound lead routine (Calendly/Formspree): research, draft welcome email, log to Notion Pipeline. Not keyword-routed; invoked only by POST /inbound-lead.",
        "keywords": [],
        "crew": "inbound_lead_direct",
    },
    "create_media": {
        "description": "Generate an image or video via Kai (kie.ai); stored on Drive and logged to Supabase/Notion",
        "keywords": [
            "create a video", "create video", "generate a video", "generate video",
            "make a video", "make video", "render a video", "produce a video",
            "create an image", "create image", "generate an image", "generate image",
            "make an image", "make image", "render an image", "produce an image",
            "create a picture", "generate a picture", "make a picture",
            "make me a video", "make me an image", "make me a picture",
            "i want a video", "i want an image", "i need a video", "i need an image",
        ],
        "crew": "media_crew",
    },
    "video_job": {
        "description": "Unified video crew intake and queueing",
        "keywords": [
            "generate video", "batch video", "ugc video", "video ad",
            "remove watermark", "video job", "make video", "create video",
        ],
        "crew": "video_crew",
    },
}



# ---------------------------------------------------------------------------
# Helper: classify a raw user message
# ---------------------------------------------------------------------------

def _classify_raw(user_message: str) -> str:
    """Internal: return task_type string. Used by classify_task and _keyword_shortcut."""
    msg = user_message.lower().strip()

    # ABSOLUTE FIRST: content board signals must NEVER be overridden by CRM shortcuts.
    # "content board" anywhere = Notion content board, not CRM.
    _CONTENT_BOARD_SIGNALS = ("content board", "from the content board", "from content board")
    _SOCIAL_DRAFT_SIGNALS = ("write a post", "draft a post", "write me a post", "draft me a post",
                             "write one post", "draft one post", "write a linkedin post", "draft a linkedin post",
                             "write a x post", "draft a x post", "write an x post", "draft an x post")
    if any(s in msg for s in _CONTENT_BOARD_SIGNALS):
        # Sub-route: drafting intent → social_content; list/fetch intent → content_board_fetch
        if any(s in msg for s in ("draft", "write", "create", "build", "full post", "generate")):
            return "social_content"
        return "content_board_fetch"
    if any(s in msg for s in _SOCIAL_DRAFT_SIGNALS):
        return "social_content"

    # Read-intent shortcut: a reporting question about CRM entities must never
    # reach the action branches. Guards:
    #   - interrogative/listing starter
    #   - a CRM entity somewhere in the message
    #   - no imperative write verbs ("draft", "send", "write", "email",
    #     "contact" as a verb). Past-tense forms ("drafted", "emailed") are
    #     reporting and stay allowed.
    #   - no "best / strategy / template / should" (planning/prescription)
    _READ_STARTS = ("how many", "how much", "what's the", "whats the", "show me", "list ", "count ")
    _READ_ENTITIES = ("lead", "leads", "outreach", "email", "emails", "prospect", "prospects", "contact", "contacts", "pipeline", "draft", "drafts")
    _WRITE_VERBS = (" draft ", " drafts ", " send ", " write ", " email ", " contact ", " create ", " make ")
    _PRESCRIPTIVE = (" should ", " best ", " strategy", " template")
    padded = f" {msg} "
    if (
        msg.startswith(_READ_STARTS)
        and any(t in msg for t in _READ_ENTITIES)
        and not any(t in padded for t in _WRITE_VERBS)
        and not any(t in padded for t in _PRESCRIPTIVE)
    ):
        return "crm_query"

    # High-priority explicit task prefixes checked first
    if any(kw in msg for kw in TASK_TYPES["schedule_content"]["keywords"]):
        return "schedule_content"
    if any(kw in msg for kw in TASK_TYPES["content_push_to_drive"]["keywords"]):
        return "content_push_to_drive"
    if any(kw in msg for kw in TASK_TYPES["voice_polishing"]["keywords"]):
        return "voice_polishing"
    if any(kw in msg for kw in TASK_TYPES["linkedin_x_campaign"]["keywords"]):
        return "linkedin_x_campaign"
    if any(kw in msg for kw in TASK_TYPES["inline_post_review"]["keywords"]):
        return "inline_post_review"
    if any(kw in msg for kw in TASK_TYPES["content_review"]["keywords"]):
        return "content_review"
    if any(kw in msg for kw in TASK_TYPES["content_board_fetch"]["keywords"]):
        return "content_board_fetch"
    if any(kw in msg for kw in TASK_TYPES["agent_creation"]["keywords"]):
        return "agent_creation"
    if any(kw in msg for kw in TASK_TYPES["forge_kpi_refresh"]["keywords"]):
        return "forge_kpi_refresh"
    if msg.startswith("doc_routing:") or any(kw in msg for kw in TASK_TYPES["doc_routing"]["keywords"]):
        return "doc_routing"
    if any(kw in msg for kw in TASK_TYPES["notion_tasks"]["keywords"]):
        return "notion_tasks"
    if any(kw in msg for kw in TASK_TYPES["notion_capture"]["keywords"]):
        return "notion_capture"
    if any(kw in msg for kw in TASK_TYPES["design_review"]["keywords"]):
        return "design_review"
    if any(kw in msg for kw in TASK_TYPES["video_job"]["keywords"]):
        return "video_job"
    if any(kw in msg for kw in TASK_TYPES["create_media"]["keywords"]):
        return "create_media"

    # research_report is checked here (before the generic keyword loop) so that
    # location+service prompts like "mechanic shops in 84095" and explicit
    # research framing like "research report on X" reach the research_engine
    # bypass in engine.py Step 3a instead of misrouting to hunter_task / app_build.
    if _looks_like_research_report(msg):
        return "research_report"

    # chat is intentionally NOT keyword-matched here — conversational openers like
    # "how do", "help me", "what is" appear in almost every functional request.
    # Let the LLM fallback decide if it's truly chat vs a functional task.

    _PRIORITY_CHECKED = {
        "content_push_to_drive", "voice_polishing", "linkedin_x_campaign",
        "inline_post_review", "content_review",
        "content_board_fetch", "schedule_content", "agent_creation",
        "forge_kpi_refresh", "doc_routing", "notion_tasks", "notion_capture", "design_review",
        "video_job", "create_media", "research_report",
    }
    for task_type, config in TASK_TYPES.items():
        if task_type in _PRIORITY_CHECKED:
            continue
        if any(kw in msg for kw in config["keywords"]):
            return task_type
    return "unknown"


def _llm_classify(user_message: str) -> str:
    """
    LLM fallback classifier. Called when keyword matching returns 'unknown'.
    Sends a compact task registry to Haiku and asks for the best task_type.
    Returns a task_type string or 'unknown' on any failure.
    """
    import openai

    registry_lines = []
    for task_type, config in TASK_TYPES.items():
        registry_lines.append(f"- {task_type}: {config['description']}")
    registry = "\n".join(registry_lines)

    system_prompt = (
        "You are a task router for an AI assistant system called agentsHQ.\n"
        "Your only job is to classify the user's message into exactly one task type from the list below.\n\n"
        "TASK TYPES:\n"
        f"{registry}\n\n"
        "Rules:\n"
        "1. Reply with ONLY the task_type string — no explanation, no punctuation, nothing else.\n"
        "2. If nothing fits, reply with: unknown\n"
        "3. When in doubt between 'chat' and a functional task, pick the functional task.\n"
        "4. 'notion_capture' covers both saving new ideas AND retrieving/listing existing ideas.\n"
        "5. 'notion_tasks' covers queries about open tasks, due dates, overdue items.\n"
        "6. 'crm_query' covers any question about leads, contacts, pipeline stats.\n"
        "7. 'social_content' covers writing posts. 'inline_post_review' covers reviewing/improving a post.\n"
        "8. 'newsletter' covers email newsletter drafting and nurture emails.\n"
        "9. 'research_report' covers location+service queries (e.g. 'mechanic shops in 84095', 'dentists near Denver'), explicit research framing ('research report on X', 'find me', 'list of', 'compare options'), and any prompt that needs live web search across multiple sources to answer. 'hunter_task' is ONLY for explicit B2B lead-sourcing language like 'find leads', 'prospects', 'growth engine', 'utah leads'. When in doubt between the two, pick 'research_report'.\n"
    )

    try:
        client = openai.OpenAI(
            api_key=os.environ.get("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://agentshq.catalystworks.com",
                "X-Title": "agentsHQ Router",
            },
        )
        response = client.chat.completions.create(
            model=ROUTER_LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0,
            max_tokens=20,
            timeout=8,
        )
        result = response.choices[0].message.content.strip().lower()
        if result in TASK_TYPES:
            logger.info(f"LLM router classified '{user_message[:60]}' as '{result}'")
            return result
        logger.warning(f"LLM router returned unrecognised type '{result!r}' for message '{user_message[:60]}' — falling back to unknown")
        return "unknown"
    except Exception as e:
        logger.error(f"LLM router exception ({type(e).__name__}: {e}) — falling back to unknown")
        return "unknown"


ROUTER_VERSION = "2026-04-20-read-intent"


# Bounded queue + single worker thread for telemetry writes.
# Rationale: spawning one daemon thread per classify_task() call creates
# unbounded fan-out under DB slowness. A bounded queue drops writes cleanly
# when saturated (non-blocking put), and a single consumer thread keeps
# memory and connection-count flat regardless of request rate.
import queue as _queue
import threading as _threading

_ROUTER_LOG_QUEUE: "_queue.Queue[tuple]" = _queue.Queue(maxsize=256)
_ROUTER_LOG_WORKER_STARTED = False
_ROUTER_LOG_WORKER_LOCK = _threading.Lock()


def _router_log_worker() -> None:
    # router_log is operational telemetry, not CRM data. It lives in the
    # local orc-postgres alongside llm_calls and job_queue. Earlier code
    # imported get_crm_connection (Supabase) here by mistake -- that pointed
    # the writes at a table that does not exist in Supabase, so every row
    # was silently dropped. Switched to get_local_connection 2026-04-22.
    try:
        from orchestrator.db import get_local_connection  # local repo layout
    except ImportError:
        from db import get_local_connection  # flat /app layout inside container

    while True:
        item = _ROUTER_LOG_QUEUE.get()
        try:
            conn = get_local_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO router_log (message, task_type, crew, used_llm, router_version)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        item,
                    )
                conn.commit()
            finally:
                conn.close()
        except Exception as e:
            logger.debug(f"router_log write skipped: {type(e).__name__}: {e}")
        finally:
            _ROUTER_LOG_QUEUE.task_done()


def _ensure_router_log_worker() -> None:
    global _ROUTER_LOG_WORKER_STARTED
    if _ROUTER_LOG_WORKER_STARTED:
        return
    with _ROUTER_LOG_WORKER_LOCK:
        if _ROUTER_LOG_WORKER_STARTED:
            return
        _threading.Thread(target=_router_log_worker, name="router-log-worker", daemon=True).start()
        _ROUTER_LOG_WORKER_STARTED = True


def _log_routing_decision(user_message: str, task_type: str, crew: str, used_llm: bool) -> None:
    """Non-blocking telemetry enqueue. Drops the write if the queue is full."""
    _ensure_router_log_worker()
    try:
        _ROUTER_LOG_QUEUE.put_nowait(
            (user_message[:500], task_type, crew, used_llm, ROUTER_VERSION)
        )
    except _queue.Full:
        logger.debug("router_log queue full; dropping one telemetry row")


def classify_task(user_message: str, explicit_task_type: str = "") -> dict:
    """
    Classify user message. Returns dict: {task_type, crew, confidence, is_unknown}.
    Uses keyword fast-path first; falls back to LLM when keywords return unknown.
    If explicit_task_type is a valid TASK_TYPES key, skip classification entirely.
    """
    # When the engine passes conversation history, extract only the CURRENT REQUEST
    # so prior assistant replies (e.g. CRM results) don't poison the classifier.
    _classify_input = user_message
    if "--- CONVERSATION HISTORY" in user_message:
        import re as _re
        # Engine format: "CURRENT REQUEST: <actual user message>"
        m = _re.search(r'CURRENT REQUEST:\s*(.+)', user_message, _re.DOTALL)
        if m:
            _classify_input = m.group(1).strip()

    used_llm = False
    if explicit_task_type and explicit_task_type in TASK_TYPES:
        task_type = explicit_task_type
    else:
        task_type = _classify_raw(_classify_input)
        if task_type == "unknown":
            task_type = _llm_classify(_classify_input)
            used_llm = True

    crew = TASK_TYPES.get(task_type, {}).get("crew", "unknown_crew")
    confidence = 0.3 if task_type == "unknown" else 0.95

    _log_routing_decision(user_message, task_type, crew, used_llm)

    return {
        "task_type": task_type,
        "crew": crew,
        "confidence": confidence,
        "is_unknown": task_type == "unknown",
    }


def _keyword_shortcut(user_request: str):
    """Return task_type string if keyword match found, else None."""
    task_type = _classify_raw(user_request)
    return task_type if task_type != "unknown" else None


def get_crew_type(task_type: str) -> str:
    """Return the crew key for a given task_type."""
    return TASK_TYPES.get(task_type, {}).get("crew", "unknown_crew")


def extract_metadata(user_message: str) -> dict:
    """Extract basic metadata from a user message. Uses full classify_task (LLM fallback included)."""
    result = classify_task(user_message)
    return {"task_type": result["task_type"], "crew": result["crew"]}


def get_crew_for_task(task_type: str) -> str:
    """
    Return the crew key for a given task_type.
    Falls back to 'unknown_crew'.
    """
    return TASK_TYPES.get(task_type, {}).get("crew", "unknown_crew")


def describe_task(task_type: str) -> str:
    """
    Return a human-readable description for a task type.
    """
    return TASK_TYPES.get(task_type, {}).get("description", "Running agents")


def build_task_type_help() -> str:
    """
    Build a formatted help string listing all task types and their keywords.
    Used by the /help command handler.
    """
    lines = ["*Available task types:*\n"]
    for task_type, config in TASK_TYPES.items():
        keywords = ", ".join(f"`{kw}`" for kw in config["keywords"][:3])
        lines.append(f"*{task_type}*: {config['description']}\nKeywords: {keywords}\n")
    return "\n".join(lines)


def format_task_registry_summary() -> str:
    """
    Return a compact JSON-style summary of all registered task types.
    Used for diagnostics / admin commands.
    """
    import json
    summary = {
        task_type: {
            "crew": config["crew"],
            "keyword_count": len(config["keywords"]),
        }
        for task_type, config in TASK_TYPES.items()
    }
    return json.dumps(summary, indent=2)


def debug_classify(user_message: str) -> str:
    """Return a debug string showing classification result + matched keywords."""
    msg = user_message.lower().strip()
    matches = []
    for task_type, config in TASK_TYPES.items():
        matched_kws = [kw for kw in config["keywords"] if kw in msg]
        if matched_kws:
            matches.append(f"{task_type}: {matched_kws}")

    result = classify_task(user_message)
    return f"""DEBUG classify_task:
Input: {user_message!r}
Result: {result}
All keyword matches:
""" + ("\n".join(f"  {m}" for m in matches) or "  (none)")
