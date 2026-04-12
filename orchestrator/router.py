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
    "research_report": {
        "description": "Research & report writing",
        "keywords": [
            "research", "write a report", "find information",
            "summarize", "analyse", "analyze", "deep dive",
        ],
        "crew": "research_crew",
    },
    "social_post": {
        "description": "Social media post drafting",
        "keywords": [
            "write a post", "linkedin post", "twitter post",
            "social post", "draft post", "content post",
        ],
        "crew": "social_crew",
    },
    "email_outreach": {
        "description": "Cold email / outreach writing",
        "keywords": [
            "write an email", "cold email", "outreach email",
            "email campaign", "email sequence",
        ],
        "crew": "email_crew",
    },
    "lead_generation": {
        "description": "Lead sourcing & prospecting",
        "keywords": [
            "find leads", "prospect", "lead generation",
            "find companies", "find contacts", "apollo",
            "hunter", "scrape leads",
        ],
        "crew": "lead_gen_crew",
    },
    "crm_update": {
        "description": "CRM data update",
        "keywords": [
            "update crm", "log contact", "update lead",
            "crm entry", "add to crm", "update contact",
        ],
        "crew": "crm_crew",
    },
    "content_calendar": {
        "description": "Content calendar planning",
        "keywords": [
            "content calendar", "plan content", "content plan",
            "editorial calendar", "content schedule",
        ],
        "crew": "content_crew",
    },
    "notion_update": {
        "description": "Notion page/database update",
        "keywords": [
            "update notion", "notion page", "add to notion",
            "notion entry", "notion database",
        ],
        "crew": "notion_crew",
    },
    "agent_team": {
        "description": "Full agent team task",
        "keywords": [
            "full team", "agent team", "all agents",
            "deploy team", "run team",
        ],
        "crew": "agent_team_crew",
    },
    "chat": {
        "description": "General chat / Q&A",
        "keywords": [
            "chat", "talk", "question", "ask", "help me",
            "what is", "how do", "explain",
        ],
        "crew": "chat_crew",
    },
    "enrich_leads": {
        "description": "Enrich existing leads with additional data",
        "keywords": [
            "enrich leads", "enrich lead", "lead enrichment",
            "enrich contacts", "enrich contact",
        ],
        "crew": "enrich_leads_crew",
    },
    "forge_kpi_refresh": {
        "description": "Refresh Forge KPI dashboard data",
        "keywords": [
            "forge kpi", "kpi refresh", "refresh kpi",
            "kpi dashboard", "forge dashboard",
        ],
        "crew": "forge_kpi_crew",
    },
    "content_review": {
        "description": "Review and score staged social media posts",
        "keywords": [
            "review content", "review posts", "score posts",
            "content review", "review social posts", "check posts",
            "review staged", "score staged",
        ],
        "crew": "content_review_crew",
    },
    "content_push_to_drive": {
        "description": "Push all approved 'In Review' social posts to Google Drive as Docs and update Notion with Drive links",
        "keywords": [
            "push content to drive", "push to drive", "create drive docs",
            "push posts to drive", "send to drive", "drive push",
            "create google docs", "create docs for posts", "push approved posts",
            "push content", "posts to drive", "content to drive",
        ],
        "crew": "content_drive_crew",
    },
    "doc_routing": {
        "description": (
            "Classify and route an incoming document to the correct NotebookLM_Library folder. "
            "Use when the task starts with 'doc_routing:' prefix. "
            "Input must include record_id, filename, extracted_text, mime_type, source in context dict."
        ),
        "keywords": ["doc_routing:", "classify document", "route document", "taxonomy routing"],
        "crew": "doc_routing_crew",
    },
}


# ---------------------------------------------------------------------------
# Helper: classify a raw user message
# ---------------------------------------------------------------------------

def classify_task(user_message: str) -> str:
    """
    Return the task_type key for the given user message.
    Falls back to 'unknown' if no keywords match.
    """
    msg = user_message.lower().strip()

    # Ordered checks for multi-word / specific patterns first

    # content_push_to_drive — must check before content_review (more specific)
    if any(kw in msg for kw in TASK_TYPES["content_push_to_drive"]["keywords"]):
        return "content_push_to_drive"

    # content_review
    if any(kw in msg for kw in TASK_TYPES["content_review"]["keywords"]):
        return "content_review"

    # forge_kpi_refresh
    if any(kw in msg for kw in TASK_TYPES["forge_kpi_refresh"]["keywords"]):
        return "forge_kpi_refresh"

    # doc_routing — prefix match
    if msg.startswith("doc_routing:") or any(kw in msg for kw in TASK_TYPES["doc_routing"]["keywords"]):
        return "doc_routing"

    # Generic keyword sweep
    for task_type, config in TASK_TYPES.items():
        if task_type in ("content_push_to_drive", "content_review", "forge_kpi_refresh", "doc_routing"):
            continue  # already handled above
        if any(kw in msg for kw in config["keywords"]):
            return task_type

    return "unknown"


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
