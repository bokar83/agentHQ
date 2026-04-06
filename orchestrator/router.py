"""
router.py — Task Classification Engine
=======================================
Every request hitting agentsHQ passes through here first.
The Router reads the incoming message, classifies the intent,
and returns a task_type that tells the Orchestrator which
crew to assemble.

This is a living file. New task types are added here as the
system grows. See AGENTS.md Task Type Registry for the full list.
"""

import os
import json
import logging
from typing import Optional
from crewai import LLM

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# ── Task Type Registry ─────────────────────────────────────────

TASK_TYPES = {
    "chat": {
        "description": "Casual conversation, follow-up questions, greetings, memory recall, or anything that isn't a structured task",
        "keywords": ["hey", "hi", "hello", "thanks", "what did", "do you remember", "what was", "tell me", "how are", "who am", "what's up", "remind me", "recap", "summary of", "what have we"],
        "crew": None,  # no crew — handled by run_chat() directly
    },
    "website_build": {
        "description": "Build a website, landing page, or web presence for a business or project",
        "keywords": ["website", "landing page", "web presence", "homepage", "site", "web page", "online presence"],
        "crew": "website_crew",
    },
    "3d_website_build": {
        "description": "Build a premium 3D animated scroll-driven website with competitive intelligence, AI-generated image/video asset prompts, and Next.js/Framer Motion implementation",
        "keywords": ["3d website", "animated website", "scroll animation", "scroll-driven", "3d animation", "framer motion", "scrollytelling", "apple-style website", "premium animated site", "exploded view website"],
        "crew": "3d_website_crew",
    },
    "app_build": {
        "description": "Build a web application, tool, calculator, dashboard, form, or interactive system",
        "keywords": ["app", "application", "tool", "calculator", "dashboard", "tracker", "form", "portal", "system", "platform"],
        "crew": "app_crew",
    },
    "research_report": {
        "description": "Research a topic and produce a structured, factual report or analysis",
        "keywords": ["research", "analyze", "analysis", "find", "summarize", "summary", "compare", "report", "investigate", "look into", "what is", "how does", "explain"],
        "crew": "research_crew",
    },
    "consulting_deliverable": {
        "description": "Create a consulting artifact: proposal, brief, diagnostic, strategy framework, or client deliverable",
        "keywords": ["proposal", "brief", "diagnostic", "framework", "strategy", "consulting", "engagement", "client", "recommendation", "assessment", "roadmap", "playbook"],
        "crew": "consulting_crew",
    },
    "social_content": {
        "description": "Create social media content: posts, captions, threads, or campaigns",
        "keywords": ["post", "tweet", "linkedin", "instagram", "twitter", "caption", "social", "thread", "content calendar", "social media", "tiktok", "facebook"],
        "crew": "social_crew",
    },
    "linkedin_x_campaign": {
        "description": "Create a full LinkedIn + X content campaign: long-form article, 7 LinkedIn posts, and 7 matching X posts in the fixed Challenger/Insight/Contrarian/Personal/Data/Insight/Challenger sequence",
        "keywords": [
            "linkedin and x", "linkedin x posts", "7 posts", "post campaign",
            "content series", "full campaign", "linkedin x campaign",
            "post sequence", "7 linkedin", "linkedin series"
        ],
        "crew": "linkedin_x_crew",
    },
    "notion_overhaul": {
        "description": "Perform a premium visual and structural redesign of a Notion page or workspace hub",
        "keywords": ["notion", "redesign", "workspace", "dashboard", "page layout", "notion hub", "organize notion"],
        "crew": "notion_overhaul",
    },
    "code_task": {
        "description": "Write, debug, refactor, or explain code in any language",
        "keywords": ["code", "script", "function", "debug", "fix", "python", "javascript", "automate", "program", "build script", "api", "endpoint"],
        "crew": "code_crew",
    },
    "general_writing": {
        "description": "Write any document: email, letter, article, essay, documentation",
        "keywords": ["write", "draft", "letter", "email", "article", "essay", "document", "memo", "announcement", "bio", "description"],
        "crew": "writing_crew",
    },
    "agent_creation": {
        "description": "Design and create a new specialist agent for the agentsHQ system",
        "keywords": ["create agent", "new agent", "build agent", "add agent", "teach yourself", "learn to", "new skill", "add capability"],
        "crew": "agent_creator_crew",
    },
    "voice_polishing": {
        "description": "Humanize text, remove AI markers, and match Boubacar Barry's specific voice and style",
        "keywords": ["humanize", "polish voice", "fix ai slop", "make it human", "sound like me", "voice match", "remove em-dashes", "clean text"],
        "crew": "voice_polisher_crew",
    },
    "hunter_task": {
        "description": "Proactive growth engine: FIND and DISCOVER new Utah service SMB leads, add them to CRM. Use when the goal is finding NEW leads, not emailing existing ones.",
        "keywords": ["find leads", "get prospects", "utah leads", "smb prospects", "growth engine", "hunting", "daily leads", "fill pipeline", "prospect for leads", "discover leads"],
        "crew": "hunter_crew",
    },
    "prompt_engineering": {
        "description": "Rewrite, improve, or optimize an AI prompt or instruction — not general writing tasks like emails or articles",
        "keywords": ["improve this prompt", "rewrite prompt", "better prompt", "fix my prompt",
                     "prompt engineer", "make this prompt", "optimize prompt", "prompt for",
                     "write me a prompt", "improve prompt", "rewrite this prompt", "make this better"],
        "crew": "prompt_engineer_crew",
    },
    "news_brief": {
        "description": "Curate and summarize current news on AI, economics, business, solopreneur topics, Africa tech, or any specified topic — with impact analysis for Catalyst Works",
        "keywords": ["news", "headlines", "what's happening", "brief me", "news of the day",
                     "daily brief", "current events", "catch me up", "what's going on",
                     "trending", "latest in", "news brief", "tell me the news", "what should i know"],
        "crew": "news_brief_crew",
    },
    "gws_task": {
        "description": "Interact with Google Workspace: list or create or delete calendar events, check schedule, draft Gmail emails, or search Gmail inbox",
        "keywords": [
            "calendar", "add event", "create event", "schedule meeting", "book meeting",
            "delete event", "remove event", "what's on my calendar", "check my calendar",
            "list events", "upcoming events", "schedule", "my schedule",
            "draft email", "write email", "gmail", "compose email", "send email",
            "search email", "find email", "inbox", "check email",
        ],
        "crew": "gws_crew",
    },
    "crm_outreach": {
        "description": "Send cold outreach emails to CRM leads who have not yet been contacted — reveals missing emails then creates Gmail drafts from templates",
        "keywords": [
            "outreach", "cold email", "contact leads", "email leads", "draft outreach",
            "send outreach", "email prospects", "reach out", "contact prospects",
            "uncontacted leads", "never contacted", "cold outreach", "email campaign",
            "draft emails", "outreach campaign", "contact everyone",
        ],
        "crew": "crm_outreach_crew",
    },
}


# ── Metadata extraction ────────────────────────────────────────

HIGH_STAKES_TRIGGERS = [
    "council this",
    "high stakes",
    "high-stakes",
    "critical decision",
    "sankofa",
    "council review",
]


def extract_metadata(user_request: str) -> dict:
    """
    Extract routing metadata from the raw request string.
    Currently extracts: high_stakes (bool)
    Returns a dict merged into task routing decisions.
    """
    lower = user_request.lower()
    return {
        "high_stakes": any(trigger in lower for trigger in HIGH_STAKES_TRIGGERS),
    }


def get_router_llm() -> LLM:
    return LLM(
        model="openrouter/anthropic/claude-haiku-4.5",
        api_key=os.environ.get("OPENROUTER_API_KEY"),
        base_url=OPENROUTER_BASE_URL,
        temperature=0.0,
        extra_headers={
            "HTTP-Referer": "https://agentshq.catalystworks.com",
            "X-Title": "agentsHQ Router"
        }
    )


def _keyword_shortcut(user_request: str) -> Optional[str]:
    """
    Fast keyword pre-check before hitting the LLM.
    Returns a task_type string if a high-confidence keyword match is found, else None.
    Checked in priority order — more specific rules first.
    """
    lower = user_request.lower()

    # crm_outreach — must match before hunter_task (both share "outreach")
    crm_outreach_triggers = [
        "cold outreach", "cold email", "contact leads", "email leads",
        "uncontacted leads", "never contacted", "draft outreach",
        "outreach emails", "email prospects", "reach out to leads",
        "contact everybody", "contact everyone", "email everybody", "email everyone",
        "outreach to leads", "outreach to prospects", "send outreach",
    ]
    if any(t in lower for t in crm_outreach_triggers):
        return "crm_outreach"

    # hunter_task — finding NEW leads
    hunter_triggers = [
        "find leads", "get leads", "find prospects", "get prospects",
        "utah leads", "daily leads", "fill pipeline", "prospect for",
        "discover leads", "lead harvest",
    ]
    if any(t in lower for t in hunter_triggers):
        return "hunter_task"

    return None


def classify_task(user_request: str) -> dict:
    """
    Classify an incoming request into a task type.
    Returns a dict with task_type, confidence, reasoning, is_unknown.
    """
    # Fast path: keyword shortcut before LLM call
    shortcut = _keyword_shortcut(user_request)
    if shortcut:
        logger.info(f"Keyword shortcut: '{user_request[:50]}' → '{shortcut}'")
        return {
            "task_type": shortcut,
            "confidence": 0.95,
            "reasoning": "Matched via keyword shortcut.",
            "is_unknown": False,
        }
    task_registry_str = "\n".join([
        f"- {k}: {v['description']}"
        for k, v in TASK_TYPES.items()
    ])

    prompt = f"""You are a task router for an AI agent system. Classify the incoming request into exactly one task type.

AVAILABLE TASK TYPES:
{task_registry_str}

ROUTING RULES:
- Use "chat" for: greetings, casual questions, follow-ups referencing prior conversation,
  memory recall ("what did we discuss", "do you remember"), short replies, thanks, or
  anything that doesn't require a specialist crew to produce a deliverable.
- Use a specialist type (research_report, social_content, etc.) only when the request
  clearly asks for a specific deliverable to be produced.
- When in doubt between "chat" and another type, prefer "chat".
- CRITICAL DISTINCTION — hunter_task vs crm_outreach:
  * hunter_task = FIND new leads (discovery, prospecting, searching for people)
  * crm_outreach = EMAIL existing CRM leads (contact, draft emails, outreach to people already in database)
  * If the request mentions "uncontacted", "already in CRM", "draft emails", "cold email", "reach out to leads", "contact leads" → use crm_outreach
  * If the request mentions "find", "discover", "prospect", "search for" → use hunter_task

INCOMING REQUEST:
"{user_request}"

Respond with a JSON object only. No explanation. No markdown. Just raw JSON:
{{
    "task_type": "<one of the task type keys above, or 'unknown'>",
    "confidence": <0.0 to 1.0>,
    "reasoning": "<one sentence why>",
    "is_unknown": <true if confidence < 0.75 or truly doesn't fit — false for 'chat'>,
    "proposed_agent_name": "<if unknown, suggest a name for a new agent>",
    "proposed_agent_description": "<if unknown, describe what the new agent would do>"
}}"""

    try:
        llm = get_router_llm()
        response = llm.call([{"role": "user", "content": prompt}])

        # Handle both string and object responses
        if hasattr(response, 'content'):
            content = response.content.strip()
        else:
            content = str(response).strip()

        # Strip markdown fences if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        result = json.loads(content)

        valid_types = set(TASK_TYPES.keys()) | {"unknown"}
        if result.get("task_type") not in valid_types:
            result["task_type"] = "unknown"
            result["is_unknown"] = True

        # chat is never "unknown" — it's a first-class type
        if result.get("task_type") == "chat":
            result["is_unknown"] = False

        logger.info(f"Classified '{user_request[:50]}' as '{result['task_type']}' (confidence: {result['confidence']})")
        return result

    except Exception as e:
        logger.error(f"Router classification failed: {e}")
        return {
            "task_type": "unknown",
            "confidence": 0.0,
            "reasoning": f"Classification failed: {str(e)}",
            "is_unknown": True,
            "proposed_agent_name": None,
            "proposed_agent_description": None
        }


def get_crew_type(task_type: str) -> Optional[str]:
    """Return the crew type string for a given task type."""
    if task_type in TASK_TYPES:
        return TASK_TYPES[task_type]["crew"]
    return None


