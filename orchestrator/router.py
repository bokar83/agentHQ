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
        "description": "Humanize text, remove AI markers, and match Boubacar Diallo's specific voice and style",
        "keywords": ["humanize", "polish voice", "fix ai slop", "make it human", "sound like me", "voice match", "remove em-dashes", "clean text"],
        "crew": "voice_polisher_crew",
    },
    "hunter_task": {
        "description": "Proactive growth engine: find Utah service SMB leads, add to CRM, and draft discovery messages",
        "keywords": ["find leads", "get prospects", "utah leads", "smb prospects", "growth engine", "hunting", "outreach", "daily leads", "fill pipeline"],
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
    "skill_build": {
        "description": "Colonize new software by building agent-native CLIs (harnesses) using the CLI-Anything SOP",
        "keywords": ["colonize", "build tool for", "create harness", "wrap software", "cli-anything", "add skill for", "skill builder", "automate software"],
        "crew": "skill_builder_crew",
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


def classify_task(user_request: str) -> dict:
    """
    Classify an incoming request into a task type.
    Returns a dict with task_type, confidence, reasoning, is_unknown.
    """
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


def register_new_task_type(task_type_key: str, description: str, keywords: list, crew: str) -> bool:
    """Dynamically register a new task type at runtime."""
    if task_type_key in TASK_TYPES:
        logger.warning(f"Task type '{task_type_key}' already exists")
        return False
    TASK_TYPES[task_type_key] = {
        "description": description,
        "keywords": keywords,
        "crew": crew,
    }
    logger.info(f"Registered new task type: '{task_type_key}'")
    return True
