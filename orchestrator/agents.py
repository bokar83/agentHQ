"""
agents.py — Agent Definitions
==============================
All specialist agents for the agentsHQ system.

LLM SELECTION PHILOSOPHY:
  - All models go through OpenRouter (one key, all providers)
  - Uses CrewAI's native LLM class with openai/ provider prefix
    to force OpenRouter routing regardless of model name
  - select_llm() dynamically picks best model per agent role + task complexity
  - To add new models: add to MODEL_REGISTRY and update select_llm()

Adding a new agent:
  1. Define a build_[name]_agent() function here
  2. Create agents/[name]/AGENT.md soul file
  3. Register in crews.py for the appropriate task types
  4. Register in AGENTS.md
"""

import os
import logging
from crewai import Agent, LLM
from tools import (
    search_tool,
    SaveOutputTool,
    QueryMemoryTool,
    RESEARCH_TOOLS,
    SCRAPING_TOOLS,
    WRITING_TOOLS,
    CODE_TOOLS,
    ORCHESTRATION_TOOLS,
    HUNTER_TOOLS,
    voice_polisher_tool,
    scoreboard_tool,
)

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
# MODEL REGISTRY
# All available models via OpenRouter.
# IMPORTANT: Use "openai/" prefix + model string format for
# CrewAI LLM class to route through OpenRouter correctly.
# Format: "openai/<model_string>"
# ══════════════════════════════════════════════════════════════

MODEL_REGISTRY = {
    "claude-sonnet": "openrouter/anthropic/claude-sonnet-4.6",
    "claude-haiku":  "openrouter/anthropic/claude-haiku-4.5",
    "claude-opus":   "openrouter/anthropic/claude-opus-4.6",
    "gemini-flash":  "openrouter/google/gemini-2.0-flash-001",
}

DEFAULT_MODEL = "claude-sonnet"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


# ══════════════════════════════════════════════════════════════
# COUNCIL MODEL REGISTRY
# Used exclusively by The Sankofa Council for capability-based
# model selection. Models rotate here as the LLM landscape evolves.
# Each model carries capability tags so select_by_capability()
# can pick the best fit without hard-coding model names in voices.
#
# To add a new model: add an entry here. Council voice definitions
# in council.py never need to change.
#
# Capability tags:
#   deep_reasoning      — sustained analytical depth, multi-step logic
#   creative_divergence — non-obvious angles, lateral thinking
#   fast                — low latency, high throughput
#   cost_efficient      — low cost per token
#   long_context        — handles 200K+ tokens reliably
#   instruction_following — precise adherence to structured output formats
#   fresh_perspective   — different training distribution from Anthropic
# ══════════════════════════════════════════════════════════════

COST_TIER_ORDER = ["very_low", "low", "low-medium", "medium", "medium-high", "high"]

COUNCIL_MODEL_REGISTRY = {
    # ── Anthropic ─────────────────────────────────────────────
    "anthropic/claude-opus-4.6": {
        "capabilities": ["deep_reasoning", "long_context", "instruction_following"],
        "cost_tier": "high",
        "input_per_mtok": 5.00,
        "output_per_mtok": 25.00,
        "notes": "Best for Chairman synthesis. 1M context. Voice fidelity.",
    },
    "anthropic/claude-sonnet-4.6": {
        "capabilities": ["deep_reasoning", "instruction_following", "long_context"],
        "cost_tier": "medium",
        "input_per_mtok": 3.00,
        "output_per_mtok": 15.00,
        "notes": "Frontier Sonnet. Strong reasoning. Default First Principles voice.",
    },
    "anthropic/claude-haiku-4.5": {
        "capabilities": ["fast", "cost_efficient", "instruction_following"],
        "cost_tier": "low",
        "input_per_mtok": 1.00,
        "output_per_mtok": 5.00,
        "notes": "Fast, cheap. Good Outsider voice — simulates naive reader.",
    },
    # ── Google ────────────────────────────────────────────────
    "google/gemini-3.1-pro-preview": {
        "capabilities": ["deep_reasoning", "long_context", "fresh_perspective"],
        "cost_tier": "medium-high",
        "input_per_mtok": 2.00,
        "output_per_mtok": 12.00,
        "notes": "Google frontier. Genuinely different training distribution.",
    },
    "google/gemini-2.5-pro": {
        "capabilities": ["deep_reasoning", "long_context", "fresh_perspective"],
        "cost_tier": "medium",
        "input_per_mtok": 1.25,
        "output_per_mtok": 10.00,
        "notes": "Strong reasoning at lower cost than Gemini 3.1.",
    },
    "google/gemini-2.5-flash": {
        "capabilities": ["fast", "cost_efficient", "fresh_perspective"],
        "cost_tier": "low",
        "input_per_mtok": 0.30,
        "output_per_mtok": 2.50,
        "notes": "Fast, cheap, different provider. Default Outsider voice.",
    },
    # ── OpenAI ────────────────────────────────────────────────
    "openai/gpt-5.1": {
        "capabilities": ["deep_reasoning", "long_context", "fresh_perspective",
                         "instruction_following"],
        "cost_tier": "medium",
        "input_per_mtok": 1.25,
        "output_per_mtok": 10.00,
        "notes": "OpenAI frontier. Different training. Strong Expansionist.",
    },
    "openai/gpt-4.1": {
        "capabilities": ["deep_reasoning", "instruction_following", "long_context"],
        "cost_tier": "medium",
        "input_per_mtok": 2.00,
        "output_per_mtok": 8.00,
        "notes": "GPT-4.1 with 1M context. Reliable instruction following.",
    },
    "openai/o4-mini": {
        "capabilities": ["deep_reasoning", "cost_efficient"],
        "cost_tier": "low-medium",
        "input_per_mtok": 1.10,
        "output_per_mtok": 4.40,
        "notes": "OpenAI reasoning model. Strong depth at reasonable cost.",
    },
    # ── DeepSeek ──────────────────────────────────────────────
    "deepseek/deepseek-r1-0528": {
        "capabilities": ["deep_reasoning", "cost_efficient", "fresh_perspective"],
        "cost_tier": "very_low",
        "input_per_mtok": 0.45,
        "output_per_mtok": 2.15,
        "notes": "R1 reasoning model. Exceptional value. Default Contrarian voice.",
    },
    "deepseek/deepseek-v3.2": {
        "capabilities": ["cost_efficient", "instruction_following", "fresh_perspective"],
        "cost_tier": "very_low",
        "input_per_mtok": 0.26,
        "output_per_mtok": 0.38,
        "notes": "Extremely cheap. Different architecture. Backup Outsider/Executor.",
    },
    # ── xAI ───────────────────────────────────────────────────
    "x-ai/grok-4": {
        "capabilities": ["deep_reasoning", "fresh_perspective", "creative_divergence"],
        "cost_tier": "medium",
        "input_per_mtok": 3.00,
        "output_per_mtok": 15.00,
        "notes": "Known for unconventional takes. Default Expansionist voice.",
    },
    # ── Mistral ───────────────────────────────────────────────
    "mistralai/mistral-large-2512": {
        "capabilities": ["instruction_following", "cost_efficient", "fresh_perspective"],
        "cost_tier": "low",
        "input_per_mtok": 0.50,
        "output_per_mtok": 1.50,
        "notes": "European training distribution. Default Executor voice.",
    },
    # ── Qwen ──────────────────────────────────────────────────
    "qwen/qwen3-235b-a22b-2507": {
        "capabilities": ["deep_reasoning", "cost_efficient", "fresh_perspective"],
        "cost_tier": "very_low",
        "input_per_mtok": 0.071,
        "output_per_mtok": 0.10,
        "notes": "235B MoE. Exceptional capability-to-cost. Backup for any voice.",
    },
}


def select_by_capability(
    capability: str,
    max_cost_tier: str = "medium",
    exclude_providers: list = None,
    temperature: float = 0.4,
) -> str:
    """
    Select the best model for a capability requirement.

    Picks the lowest-cost model within the cost ceiling that has the required capability.
    If no model meets both constraints, relaxes cost tier upward until a match is found.
    Always returns a valid model_id — never raises.

    Args:
        capability: One of the capability tags (e.g. "deep_reasoning")
        max_cost_tier: Maximum allowed tier from COST_TIER_ORDER
        exclude_providers: Provider prefixes to skip (e.g. ["anthropic"])
        temperature: For reference only — actual LLM built by caller

    Returns:
        model_id string from COUNCIL_MODEL_REGISTRY
    """
    exclude_providers = exclude_providers or []
    max_tier_idx = (
        COST_TIER_ORDER.index(max_cost_tier)
        if max_cost_tier in COST_TIER_ORDER
        else len(COST_TIER_ORDER) - 1
    )

    candidates = []
    for model_id, meta in COUNCIL_MODEL_REGISTRY.items():
        provider = model_id.split("/")[0]
        if provider in exclude_providers:
            continue
        if capability not in meta["capabilities"]:
            continue
        tier_idx = (
            COST_TIER_ORDER.index(meta["cost_tier"])
            if meta["cost_tier"] in COST_TIER_ORDER
            else len(COST_TIER_ORDER)
        )
        if tier_idx <= max_tier_idx:
            candidates.append((tier_idx, meta["input_per_mtok"], model_id))

    if not candidates:
        # Relax cost constraint — find any model with this capability
        for model_id, meta in COUNCIL_MODEL_REGISTRY.items():
            provider = model_id.split("/")[0]
            if provider in exclude_providers:
                continue
            if capability in meta["capabilities"]:
                tier_idx = (
                    COST_TIER_ORDER.index(meta["cost_tier"])
                    if meta["cost_tier"] in COST_TIER_ORDER
                    else len(COST_TIER_ORDER)
                )
                candidates.append((tier_idx, meta["input_per_mtok"], model_id))

    if not candidates:
        # Ultimate fallback — return cheapest model regardless of capability
        fallback = min(COUNCIL_MODEL_REGISTRY.items(), key=lambda x: x[1]["input_per_mtok"])
        logger.warning(
            f"No model found for capability='{capability}'. Falling back to {fallback[0]}"
        )
        return fallback[0]

    # Sort: prefer lowest cost tier, then lowest price within tier
    candidates.sort(key=lambda x: (x[0], x[1]))
    selected = candidates[0][2]
    logger.info(f"select_by_capability({capability}, max={max_cost_tier}) → {selected}")
    return selected


# ══════════════════════════════════════════════════════════════
# LLM FACTORY
# Uses CrewAI's native LLM class.
# All calls route through OpenRouter via openai-compatible API.
# ══════════════════════════════════════════════════════════════

def get_llm(model_alias: str = DEFAULT_MODEL, temperature: float = 0.3) -> LLM:
    """
    Get a configured LLM via OpenRouter using CrewAI's LLM class.
    model_alias: key from MODEL_REGISTRY or full model string
    temperature: 0.0 = deterministic, 1.0 = creative
    """
    model_string = MODEL_REGISTRY.get(model_alias, model_alias)
    logger.debug(f"Creating LLM: {model_alias} -> {model_string} (temp={temperature})")
    # Force Anthropic provider for Claude models — prevents OpenRouter from
    # routing through Google Vertex, which rejects CrewAI's prefill pattern.
    extra_body = {}
    if "anthropic/" in model_string:
        extra_body = {"provider": {"order": ["Anthropic"], "allow_fallbacks": False}}

    return LLM(
        model=model_string,
        api_key=os.environ.get("OPENROUTER_API_KEY"),
        base_url=OPENROUTER_BASE_URL,
        temperature=temperature,
        extra_headers={
            "HTTP-Referer": "https://agentshq.catalystworks.com",
            "X-Title": "agentsHQ"
        },
        extra_body=extra_body if extra_body else None,
    )


# ══════════════════════════════════════════════════════════════
# DYNAMIC MODEL SELECTOR
# Picks the best model based on agent role and task complexity.
# To add new models: add to MODEL_REGISTRY, add to matrix below.
# ══════════════════════════════════════════════════════════════

def select_llm(agent_role: str, task_complexity: str = "moderate", temperature: float = None) -> LLM:
    """
    Dynamically select the best model for an agent role and task complexity.
    agent_role: planner | researcher | writer | coder | qa | orchestrator | social | consultant
    task_complexity: simple | moderate | complex
    """
    selection_matrix = {
        ("planner",     "simple"):   ("claude-haiku",  0.1),
        ("planner",     "moderate"): ("claude-haiku",  0.1),
        ("planner",     "complex"):  ("claude-sonnet", 0.2),
        ("researcher",  "simple"):   ("claude-sonnet", 0.2),
        ("researcher",  "moderate"): ("claude-sonnet", 0.2),
        ("researcher",  "complex"):  ("claude-sonnet", 0.2),
        ("writer",      "simple"):   ("claude-haiku",  0.7),
        ("writer",      "moderate"): ("claude-sonnet", 0.7),
        ("writer",      "complex"):  ("claude-sonnet", 0.8),
        ("social",      "simple"):   ("claude-sonnet", 0.8),
        ("social",      "moderate"): ("claude-sonnet", 0.8),
        ("social",      "complex"):  ("claude-sonnet", 0.9),
        ("coder",       "simple"):   ("claude-haiku",  0.1),
        ("coder",       "moderate"): ("claude-sonnet", 0.1),
        ("coder",       "complex"):  ("claude-sonnet", 0.1),
        ("qa",          "simple"):   ("claude-haiku",  0.1),
        ("qa",          "moderate"): ("claude-sonnet", 0.2),
        ("qa",          "complex"):  ("claude-sonnet", 0.2),
        ("orchestrator","simple"):   ("claude-sonnet", 0.2),
        ("orchestrator","moderate"): ("claude-opus",   0.2),
        ("orchestrator","complex"):  ("claude-opus",   0.3),
        ("consultant",  "simple"):   ("claude-sonnet", 0.3),
        ("consultant",  "moderate"): ("claude-sonnet", 0.3),
        ("consultant",  "complex"):  ("claude-opus",   0.3),
        ("voice",       "complex"):  ("claude-sonnet", 0.8),
        ("hunter",      "simple"):   ("claude-haiku",  0.2),
        ("hunter",      "moderate"): ("claude-sonnet", 0.3),
        ("hunter",      "complex"):  ("claude-sonnet", 0.4),
        ("skill_builder", "moderate"): ("gemini-flash", 0.1),
        ("skill_builder", "complex"):  ("claude-sonnet", 0.1),
    }
    key = (agent_role, task_complexity)
    model_alias, default_temp = selection_matrix.get(key, (DEFAULT_MODEL, 0.3))
    final_temp = temperature if temperature is not None else default_temp
    logger.info(f"Model selected for {agent_role}/{task_complexity}: {model_alias} (temp={final_temp})")
    return get_llm(model_alias, final_temp)


# ══════════════════════════════════════════════════════════════
# AGENT DEFINITIONS
# ══════════════════════════════════════════════════════════════

def build_orchestrator_agent() -> Agent:
    return Agent(
        role="Chief Orchestrator",
        goal="""Understand any request, determine the best approach,
        coordinate specialist agents, and ensure every task produces
        a real, high-quality deliverable. When a task type is unknown,
        propose a new specialist agent rather than attempting it poorly.""",
        backstory="""You are the central intelligence of agentsHQ, the
        AI operating system built for Boubacar Barry at Catalyst Works
        Consulting. You orchestrate tasks across web development, research,
        consulting, marketing, and systems design. You never pretend to
        do something you cannot — you escalate or propose new capabilities.""",
        verbose=False,
        allow_delegation=True,
        tools=ORCHESTRATION_TOOLS + [search_tool],
        llm=select_llm("orchestrator", "complex"),
        max_iter=5
    )


def build_planner_agent() -> Agent:
    return Agent(
        role="Strategic Planner",
        goal="""Analyze any incoming request and produce a clear,
        structured execution plan. Identify deliverables, required
        information, dependencies, and the optimal sequence of work.""",
        backstory="""You are a senior strategic planner with experience
        across technology, consulting, marketing, and product development.
        Your superpower is taking ambiguous requests and turning them into
        crisp, sequenced work plans. You always check memory for relevant
        past work before planning.""",
        verbose=False,
        allow_delegation=False,
        tools=[QueryMemoryTool(), search_tool],
        llm=select_llm("planner", "moderate"),
        max_iter=3
    )



def build_researcher_agent() -> Agent:
    return Agent(
        role="Research Specialist",
        goal="""Find accurate, current, relevant information that gives
        the rest of the crew the context they need to produce excellent work.
        Synthesize findings into a structured research brief.""",
        backstory="""You are a world-class researcher with experience at
        top consulting firms and investigative journalism outlets. You never
        fabricate data. Fast, precise, and thorough.""",
        verbose=False,
        allow_delegation=False,
        tools=RESEARCH_TOOLS + SCRAPING_TOOLS,
        llm=select_llm("researcher", "moderate"),
        max_iter=5
    )


def build_copywriter_agent() -> Agent:
    return Agent(
        role="Senior Copywriter & Content Strategist",
        goal="""Write compelling, accurate, well-structured content.
        Every word should feel written specifically for this project.
        No filler, no generic phrases, no lorem ipsum.""",
        backstory="""You are a copywriter with 15 years of experience
        across advertising, brand strategy, web content, and consulting
        communications. You never use phrases like 'we are passionate about'
        or 'world-class'. Specific, vivid, and true.""",
        verbose=False,
        allow_delegation=False,
        tools=WRITING_TOOLS,
        llm=select_llm("writer", "moderate"),
        max_iter=4
    )


def build_web_builder_agent() -> Agent:
    return Agent(
        role="Senior Frontend Developer & UI Designer",
        goal="""Build complete, beautiful, mobile-responsive websites.
        Single HTML file, all CSS in style tags, JS in script tags.
        No placeholders ever. Save output using save_output tool.""",
        backstory="""You are a frontend developer and UI designer with deep
        expertise in HTML5, CSS3, and vanilla JavaScript. Semantic HTML,
        CSS variables, mobile-first responsiveness, tasteful interactions.""",
        verbose=False,
        allow_delegation=False,
        tools=WRITING_TOOLS + [SaveOutputTool()],
        llm=select_llm("coder", "moderate"),
        max_iter=5
    )


def build_app_builder_agent() -> Agent:
    return Agent(
        role="Full-Stack Web Application Developer",
        goal="""Build functional, interactive web applications.
        All functionality working, edge cases handled, UX intuitive.
        Save all outputs using save_output tool.""",
        backstory="""You are a full-stack developer specializing in
        client-side web applications: calculators, dashboards, booking
        systems, and productivity tools. Clean, maintainable code.""",
        verbose=False,
        allow_delegation=False,
        tools=CODE_TOOLS,
        llm=select_llm("coder", "complex"),
        max_iter=6
    )


def build_code_agent() -> Agent:
    return Agent(
        role="Senior Software Engineer",
        goal="""Write, debug, refactor, and explain code in any language.
        Working, tested, well-commented code.
        Always save output using save_output tool.""",
        backstory="""Senior software engineer across Python, JavaScript,
        TypeScript, Bash, SQL and more. Code that works the first time.
        No TODO comments in production.""",
        verbose=False,
        allow_delegation=False,
        tools=CODE_TOOLS + RESEARCH_TOOLS,
        llm=select_llm("coder", "complex"),
        max_iter=6
    )


def build_consulting_agent() -> Agent:
    return Agent(
        role="Management Consulting Specialist",
        goal="""Produce professional, analytically rigorous consulting
        deliverables that sound like Boubacar Barry wrote them personally.

        BOUBACAR'S VOICE RULES:
        - Make ONE bold, confident diagnosis — never present a menu of options
          unless explicitly asked. Consultants who hedge everything are useless.
        - Lead with the insight that makes the reader stop. Not the problem
          statement. The insight comes first.
        - Always connect the operational constraint to a financial outcome AND
          a human/organizational outcome. Three dimensions minimum.
        - Include ONE counterintuitive observation that challenges what the
          client thinks they know. This is the WOW moment.
        - Write for the overwhelmed decision-maker: clear, direct, no jargon
          soup. If it takes more than 30 seconds to understand a recommendation,
          rewrite it.
        - End with ONE question that makes the reader uncomfortable in a
          productive way.
        - Never use generic benchmarks without anchoring them to the client's
          specific context.
        - The reader should feel: "This person understands my problem better
          than I do."
        - If you cannot make a confident diagnosis from the information given,
          state what specific data you need and why — don't fake it with
          a menu of options.""",
        backstory="""You are a senior management consultant and the voice of
        Catalyst Works Consulting. Your expertise is organizational diagnostics
        and Theory of Constraints. You have worked with companies from
        10-person startups to 5,000-person enterprises. You identify the single
        binding constraint in any system and build a targeted intervention.
        You never pad deliverables. You never hedge when you can diagnose.
        You write clearly, think in systems, and say what others won't.
        Your work makes clients feel seen and challenged at the same time.
        A Catalyst Works deliverable is never generic — it is specific,
        provocative, and immediately actionable.""",
        verbose=False,
        allow_delegation=False,
        tools=RESEARCH_TOOLS + WRITING_TOOLS,
        llm=select_llm("consultant", "complex"),
        max_iter=5
    )


def build_social_media_agent() -> Agent:
    return Agent(
        role="leGriot — Social Media Voice & Content Strategist",
        goal="""Create compelling social media content in Boubacar's authentic
        voice for LinkedIn, Twitter/X, and Instagram. Teach, provoke thought,
        build the Catalyst Works brand. Save posts using save_output.

        STRICT CONTENT RULES — NEVER VIOLATE:
        - NEVER invent stories, client examples, or experiences that Boubacar
          did not provide. If no real story is given, do NOT fabricate one.
        - NEVER write "Last month I..." or "Three weeks ago I..." or any
          first-person narrative unless Boubacar explicitly provided that story.
        - If a story or example would strengthen the post but none was provided,
          use "Imagine if..." or "Picture this..." to signal it is hypothetical.
        - Write arguments and insights from principles and logic, not invented
          anecdotes.
        - Boubacar's credibility is built on truth. One fabricated story
          destroys it. Never risk that.""",
        backstory="""You are leGriot, named after the West African storyteller
        tradition. You translate Boubacar's raw ideas into content that
        resonates. You NEVER invent experiences or put words in Boubacar's
        mouth. You write the way he thinks: direct, principled, earned.
        If you need an example and none was given, you signal it clearly
        as hypothetical. Never 'I'm excited to share...' or buzzword soup.""",
        verbose=False,
        allow_delegation=False,
        tools=RESEARCH_TOOLS + WRITING_TOOLS,
        llm=select_llm("social", "moderate"),
        max_iter=4
    )

def build_qa_agent() -> Agent:
    return Agent(
        role="Quality Assurance & Delivery Specialist",
        goal="""Review the deliverable you have been given. If it has quality issues,
        fix them yourself — do not just flag them. Then output in this exact format:

        WHAT WAS DONE:
        [1-2 sentences: what type of deliverable was created and for what purpose]

        WHY IT WAS DONE THIS WAY:
        [1-2 sentences: key decisions made — structure, format, angle chosen]

        QUALITY CHECK: PASSED
        [or: QUALITY CHECK: REVISED — [brief description of what was fixed]]

        DELIVERABLE:
        [The complete, final deliverable content — always present, whether passed
        or revised. Never omit this section. Never truncate. Full content only.]

        Rules:
        - Never say "let me read the file" or "I will review" — just do it.
        - If something is generic, rewrite it to be specific.
        - If something is missing, add it.
        - The DELIVERABLE section is mandatory in every response, every time.""",
        backstory="""Meticulous QA specialist who has reviewed thousands of
        deliverables. You receive the work product directly from the previous
        agent. You review it, fix anything wrong, then output the structured format.
        You never report a problem without also delivering the solution.
        You never omit the deliverable — passing or failing, the content always ships.""",
        verbose=False,
        allow_delegation=False,
        tools=[SaveOutputTool()],
        llm=select_llm("qa", "moderate"),
        max_iter=3
    )


def build_agent_creator_agent() -> Agent:
    return Agent(
        role="Agent Creator (Architecture Specialist)",
        goal="""Generate optimized agent definitions for task types that cannot be
        handled by the existing crew. Ensure zero redundancy and strict adherence
        to AGENTS.md protocols. Each agent should be laser-focused on a single type
        a task. Submit proposals via propose_new_agent tool.
        Never duplicate existing capabilities.""",
        backstory="""AI systems architect who understands what makes agents
        effective. Narrow role, clear goal, realistic backstory, minimal tools.
        Always propose before building.""",
        verbose=False,
        allow_delegation=False,
        tools=ORCHESTRATION_TOOLS + [QueryMemoryTool()],
        llm=select_llm("orchestrator", "complex"),
        max_iter=4
    )


def build_boub_ai_voice_agent() -> Agent:
    return Agent(
        role="BouB AI Voice — Voice Polisher & Humanization Specialist",
        goal="""Ensure every piece of content produced by the system sounds natural,
        human, and perfectly reflects Boubacar Barry's authoritative, direct,
        and insightful voice. Eliminate all AI red flags.""",
        backstory="""You are the ultimate voice polisher for Catalyst Works.
        You have a clinical eye for 'AI-slop': em-dash abuse, uniform sentence
        length, and robotic 'throat-clearing' transitions. You rewrite with grit
        and soul, channeling Boubacar's direct, principle-led style.
        You understand that simplicity is the ultimate sophistication.""",
        verbose=False,
        allow_delegation=False,
        tools=WRITING_TOOLS + [voice_polisher_tool, search_tool, QueryMemoryTool()],
        llm=select_llm("voice", "moderate"),
        max_iter=4
    )


def build_hunter_agent() -> Agent:
    """Builds the Specialist Agent: The Growth Hunter."""
    return Agent(
        role="Growth Hunter — Utah SMB Prospecting Specialist",
        goal=(
            "Find 20 high-value SMB leads per daily run in Utah "
            "(Legal, Accounting, Marketing Agency, HVAC, Plumbing, Roofing). "
            "For each lead collect: name, company, title, phone, email, and LinkedIn URL. "
            "Save every lead to the CRM via add_lead. "
            "When Boubacar requests a specific email reveal, use the reveal_email tool. "
            "Finish every run by reporting the daily scoreboard."
        ),
        backstory=(
            "You are a relentless revenue prospector for Catalyst Works Consulting. "
            "Your pipeline: Serper LinkedIn dorking to find owner profiles → "
            "Serper local business search for phone and website → "
            "Firecrawl to scrape websites for direct contact info → "
            "Hunter.io to fill in missing emails → "
            "Apollo as a last resort when Serper returns fewer than 5 results. "
            "You never reveal Apollo emails automatically — Apollo credits are rationed. "
            "You log every lead to Supabase CRM via add_lead. "
            "You report results clearly so Boubacar can prioritize outreach."
        ),
        tools=HUNTER_TOOLS,
        llm=select_llm("hunter", "moderate"),
        verbose=False,
        allow_delegation=False,
        max_iter=8
    )


def build_prompt_engineer_agent() -> Agent:
    """Builds the Prompt Engineer agent — rewrites any prompt using Catalyst Prompt OS."""
    return Agent(
        role="Prompt Engineer — Catalyst Prompt OS",
        goal="""Take any raw prompt and rewrite it using the 8-step Catalyst Prompt OS algorithm.
        Replace title-based roles ('expert') with behavior-first roles that describe how the AI
        should show up. Add step-back thinking, explicit output format, multi-output selection gate,
        and iteration gate. Return the improved prompt with a clear change summary.""",
        backstory="""You are a precision editor who specializes in prompt architecture,
        transforming vague or underperforming instructions into high-performance prompts
        that produce monetizable outputs. You have studied thousands of AI prompts and
        know exactly what separates a prompt that produces slop from one that produces
        a deliverable worth money. You don't add fluff — you add architecture. Every rewrite
        you produce makes the AI smarter about how to show up, not just what to know.
        You apply the Catalyst Prompt OS: behavior-first roles, step-back anchoring,
        action-verb task instructions tied to real-world impact, explicit output format,
        multi-output selection gate, and an iteration gate.""",
        verbose=False,
        allow_delegation=False,
        tools=[],
        llm=get_llm("claude-sonnet", 0.4),  # temp 0.4 intentional: structured rewriting, not creative generation
        max_iter=3
    )


def build_website_intelligence_agent() -> Agent:
    return Agent(
        role="Website Intelligence Researcher",
        goal="""Scrape a client's website, find their top 5 competitors,
        extract brand colors, fonts, messaging, and design patterns.
        Produce a structured competitive intelligence brief and a
        PDF-ready HTML competitive analysis report.""",
        backstory="""You are a senior web strategist who has analyzed
        thousands of websites across every niche. You find patterns
        others miss. You use Firecrawl to scrape real data — never
        guess or fabricate. Every insight is backed by a real URL.""",
        verbose=False,
        allow_delegation=False,
        tools=RESEARCH_TOOLS + SCRAPING_TOOLS + [SaveOutputTool()],
        llm=select_llm("researcher", "complex"),
        max_iter=8
    )


def build_asset_prompter_agent() -> Agent:
    return Agent(
        role="3D Asset Prompt Engineer",
        goal="""Generate a coordinated set of 3 AI prompts for scroll-stopping
        video content: (1) hero/start-frame product shot on pure white or brand
        background, (2) exploded/deconstructed or before-after end frame,
        (3) cinematic video transition between them.
        Deliver prompts in a clean HTML page with one-click copy buttons.""",
        backstory="""You are a creative director who specializes in premium
        product visualization and AI-generated video content. You know exactly
        how to describe lighting, composition, and motion so that Flux,
        Midjourney, Kling, and Higgsfield produce world-class results on the
        first generation. Your prompts match the aesthetic of Apple and
        automotive luxury brands.""",
        verbose=False,
        allow_delegation=False,
        tools=WRITING_TOOLS + [SaveOutputTool()],
        llm=select_llm("writer", "complex"),
        max_iter=4
    )


def build_3d_web_builder_agent() -> Agent:
    return Agent(
        role="Awwwards-Level Creative Developer",
        goal="""Build premium scroll-driven Next.js 14 websites with
        Framer Motion animations and HTML5 Canvas image sequences.
        The product floats in a void and transforms as the user scrolls —
        Apple-style, cinematic, 60fps smooth.
        Output: complete Next.js project files ready to run with npm run dev.""",
        backstory="""You are a world-class creative developer specializing in
        Next.js, Tailwind CSS, Framer Motion, and scroll-linked canvas animations.
        You build Awwwards-nominated sites. Your code is TypeScript, clean, and
        production-ready. Background always matches image sequence exactly
        (#050505 default) so edges are invisible. You use useScroll and
        useSpring (stiffness:100, damping:30) for buttery smoothness.
        You never use placeholder text — all content comes from the brief.""",
        verbose=False,
        allow_delegation=False,
        tools=CODE_TOOLS + WRITING_TOOLS,
        llm=select_llm("coder", "complex"),
        max_iter=8
    )


def build_seo_auditor_agent() -> Agent:
    return Agent(
        role="SEO and Accessibility Auditor",
        goal="""Run a thorough SEO and WCAG AA accessibility audit on any
        website HTML or URL. Fix all issues found and return the corrected
        HTML plus a numbered checklist of every change made.""",
        backstory="""You are an SEO specialist and accessibility expert.
        You have audited hundreds of websites against Google ranking signals
        and WCAG 2.1 AA standards. You fix issues — you do not just report them.
        Meta tags, heading hierarchy, alt text, schema markup, color contrast,
        keyboard navigation, focus indicators — you check everything.""",
        verbose=False,
        allow_delegation=False,
        tools=RESEARCH_TOOLS + SCRAPING_TOOLS + [SaveOutputTool()],
        llm=select_llm("researcher", "moderate"),
        max_iter=5
    )


def build_skill_builder_agent() -> Agent:
    """Builds the Specialist Agent: The Skill Builder (Colonization Strategist)."""
    return Agent(
        role="Skill Builder — Software Colonization Strategist & Resource Acquisition Officer",
        goal="""Proactively expand the agentsHQ empire by transforming high-value
        software into agent-native, Click-powered skills following the Strategic 9-phase SOP.
        Always identify business ROI and 'Monday Morning' deliverables before starting.""",
        backstory="""You are a Strategic Resource Officer for Catalyst Works. You don't 
        just build code; you acquire capabilities that generate competitive advantage.
        You follow the 9-Phase Strategic SOP (ROI-First) to ensure every tool has a
        clear monetization or productivity impact for Boubacar. You strictly ensure
        all outputs follow the Catalyst branding and --json machine readability.""",
        tools=[search_tool, SaveOutputTool(), CLIHubSearchTool()] + CODE_TOOLS,
        llm=select_llm("skill_builder", "complex"),
        verbose=True,
        allow_delegation=False,
        max_iter=10  # Building tools can be a multi-step process
    )
