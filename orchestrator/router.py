"""
router.py — Task Classification Engine
=======================================
Maps incoming user requests to the correct crew type.
Used by orchestrator.py to determine which crew to assemble.
"""

import re
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

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
        ],
        "crew": "social_crew",
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
        ],
        "crew": "content_board_fetch_crew",
    },
    "gws_task": {
        "description": "Google Workspace automation (Gmail/Calendar)",
        "keywords": ["calendar", "add event", "check schedule", "gmail", "draft email", "search email"],
        "crew": "gws_crew",
    },
    "chat": {
        "description": "General chat / Q&A",
        "keywords": ["chat", "talk", "question", "ask", "help me", "what is", "how do", "explain"],
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
}



# ---------------------------------------------------------------------------
# Helper: classify a raw user message
# ---------------------------------------------------------------------------

def _classify_raw(user_message: str) -> str:
    """Internal: return task_type string. Used by classify_task and _keyword_shortcut."""
    msg = user_message.lower().strip()

    # High-priority explicit task prefixes checked first
    if any(kw in msg for kw in TASK_TYPES["content_push_to_drive"]["keywords"]):
        return "content_push_to_drive"
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
    if any(kw in msg for kw in TASK_TYPES["notion_capture"]["keywords"]):
        return "notion_capture"
    if any(kw in msg for kw in TASK_TYPES["design_review"]["keywords"]):
        return "design_review"

    _PRIORITY_CHECKED = {
        "content_push_to_drive", "inline_post_review", "content_review",
        "content_board_fetch", "agent_creation",
        "forge_kpi_refresh", "doc_routing", "notion_capture", "design_review",
    }
    for task_type, config in TASK_TYPES.items():
        if task_type in _PRIORITY_CHECKED:
            continue
        if any(kw in msg for kw in config["keywords"]):
            return task_type
    return "unknown"


def classify_task(user_message: str) -> dict:
    """
    Classify user message. Returns dict: {task_type, crew, confidence, is_unknown}.
    This format is expected by orchestrator.py at lines 594-599.
    """
    task_type = _classify_raw(user_message)
    crew = TASK_TYPES.get(task_type, {}).get("crew", "unknown_crew")
    confidence = 0.3 if task_type == "unknown" else 0.95
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
    """Extract basic metadata from a user message."""
    task_type = _classify_raw(user_message)
    return {"task_type": task_type, "crew": get_crew_type(task_type)}


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
