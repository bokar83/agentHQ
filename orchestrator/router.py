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
        "crew": "web_builder_crew",
    },
    "app_build": {
        "description": "Interactive web app / tool build",
        "keywords": ["app", "tool", "calculator", "dashboard", "form", "tracker", "build an app"],
        "crew": "app_builder_crew",
    },
    "vercel_task": {
        "description": "Vercel deployment & monitoring",
        "keywords": ["vercel", "deploy", "build status", "logs", "projects"],
        "crew": "code_crew",
    },
    "github_task": {
        "description": "GitHub repository & PR management",
        "keywords": ["github", "repo", "repository", "issue", "pull request", "pr"],
        "crew": "code_crew",
    },
    "notion_task": {
        "description": "Notion database & architecting",
        "keywords": ["notion", "database", "log", "page", "dashboard", "wiki"],
        "crew": "notion_crew",
    },
    "practice_runner_task": {
        "description": "Practice Runner Mission execution",
        "keywords": ["practice runner", "marathon prep", "running prep", "training plan"],
        "crew": "practice_runner_crew",
    },
    "research_report": {
        "description": "Research & report writing",
        "keywords": [
            "research", "write a report", "find information",
            "summarize", "analyse", "analyze", "deep dive", "compare",
        ],
        "crew": "research_crew",
    },
    "social_content": {
        "description": "Social media post drafting",
        "keywords": [
            "write a post", "linkedin post", "twitter post", "x post",
            "social post", "draft post", "content post", "instagram", "caption",
        ],
        "crew": "social_crew",
    },
    "linkedin_x_campaign": {
        "description": "Multi-platform content campaign",
        "keywords": ["linkedin and x", "7 posts", "post campaign", "linkedin x posts", "content series"],
        "crew": "griot_crew",
    },
    "code_task": {
        "description": "Code engineering & debugging",
        "keywords": ["code", "script", "function", "debug", "build", "automate"],
        "crew": "code_crew",
    },
    "general_writing": {
        "description": "Drafting letters, emails, and documents",
        "keywords": ["write", "draft", "letter", "email", "document"],
        "crew": "writing_crew",
    },
    "voice_polishing": {
        "description": "Humanizing content with Boub AI Voice",
        "keywords": ["humanize", "polish", "voice match"],
        "crew": "voice_crew",
    },
    "hunter_task": {
        "description": "Lead sourcing & prospect hunting",
        "keywords": ["find leads", "prospect", "utah leads", "growth engine", "hunter"],
        "crew": "hunter_crew",
    },
    "skill_build": {
        "description": "Building new tools & skills (CLI-Anything)",
        "keywords": ["colonize", "build tool", "wrap software", "cli-anything"],
        "crew": "skill_builder_crew",
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


# Alias used by orchestrator.py _shortcut_classify()
def _keyword_shortcut(user_request: str):
    """Return task_type if keyword match found, else None."""
    result = classify_task(user_request)
    return result if result != "unknown" else None


def get_crew_type(task_type: str) -> str:
    """Return the crew key for a given task_type. Alias for get_crew_for_task."""
    return TASK_TYPES.get(task_type, {}).get("crew", "unknown_crew")


def extract_metadata(user_message: str) -> dict:
    """Extract basic metadata from a user message. Returns a dict with task_type."""
    task_type = classify_task(user_message)
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
