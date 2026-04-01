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
    file_writer,
    file_reader,
    code_interpreter,
    SaveOutputTool,
    QueryMemoryTool,
    EscalateTool,
    ProposeNewAgentTool,
    RESEARCH_TOOLS,
    SCRAPING_TOOLS,
    WRITING_TOOLS,
    CODE_TOOLS,
    ORCHESTRATION_TOOLS,
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
    "claude-sonnet": "openrouter/anthropic/claude-sonnet-4-5",
    "claude-haiku":  "openrouter/anthropic/claude-haiku-4.5",
    "claude-opus":   "openrouter/anthropic/claude-opus-4-5",
}

DEFAULT_MODEL = "claude-sonnet"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


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
    return LLM(
        model=model_string,
        api_key=os.environ.get("OPENROUTER_API_KEY"),
        base_url=OPENROUTER_BASE_URL,
        temperature=temperature,
        extra_headers={
            "HTTP-Referer": "https://agentshq.catalystworks.com",
            "X-Title": "agentsHQ"
        }
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
    }
    key = (agent_role, task_complexity)
    model_alias, default_temp = selection_matrix.get(key, (DEFAULT_MODEL, 0.3))
    final_temp = temperature if temperature is not None else default_temp
    logger.info(f"Model selected for {agent_role}/{task_complexity}: {model_alias} (temp={final_temp})")
    return get_llm(model_alias, final_temp)


# ══════════════════════════════════════════════════════════════
# METACLAW FACTORY
# Routes consulting, researcher, social_media agents through
# the MetaClaw proxy for skill injection and sample collection.
# Falls back to direct OpenRouter if proxy is down or disabled.
# Toggle: USE_METACLAW=false in .env to bypass instantly.
# ══════════════════════════════════════════════════════════════

_METACLAW_TEMPS = {"consultant": 0.3, "researcher": 0.2, "social": 0.8}


def get_llm_metaclaw(agent_role: str, task_complexity: str = "moderate", temperature: float = None) -> LLM:
    """
    MetaClaw-proxied LLM for consulting, researcher, social_media agents.
    Falls back to direct OpenRouter if USE_METACLAW=false or proxy unreachable.
    """
    if os.environ.get("USE_METACLAW", "true").lower() != "true":
        return select_llm(agent_role, task_complexity, temperature)

    final_temp = temperature if temperature is not None else _METACLAW_TEMPS.get(agent_role, 0.3)

    try:
        return LLM(
            model=MODEL_REGISTRY.get("claude-sonnet"),
            api_key=os.environ.get("METACLAW_API_KEY", "metaclaw-internal"),
            base_url="http://orc-metaclaw:30000/v1",
            temperature=final_temp,
            extra_headers={
                "HTTP-Referer": "https://agentshq.catalystworks.com",
                "X-Title": "agentsHQ"
            }
        )
    except (ConnectionError, TimeoutError, OSError):
        logger.warning("MetaClaw proxy unreachable — falling back to direct OpenRouter")
        return select_llm(agent_role, task_complexity, final_temp)


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
        AI operating system built for Boubacar Diallo at Catalyst Works
        Consulting. You orchestrate tasks across web development, research,
        consulting, marketing, and systems design. You never pretend to
        do something you cannot — you escalate or propose new capabilities.""",
        verbose=True,
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
        verbose=True,
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
        verbose=True,
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
        verbose=True,
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
        verbose=True,
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
        verbose=True,
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
        verbose=True,
        allow_delegation=False,
        tools=CODE_TOOLS + RESEARCH_TOOLS,
        llm=select_llm("coder", "complex"),
        max_iter=6
    )


def build_consulting_agent() -> Agent:
    return Agent(
        role="Management Consulting Specialist",
        goal="""Produce professional, analytically rigorous consulting
        deliverables that sound like Boubacar Diallo wrote them personally.

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
        verbose=True,
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
        verbose=True,
        allow_delegation=False,
        tools=RESEARCH_TOOLS + WRITING_TOOLS,
        llm=select_llm("social", "moderate"),
        max_iter=4
    )

def build_qa_agent() -> Agent:
    return Agent(
        role="Quality Assurance & Delivery Specialist",
        goal="""Review every deliverable before it reaches Boubacar.
        No errors, no placeholders, professional quality.
        Fix what is wrong. Your sign-off means the work is done.""",
        backstory="""Meticulous QA specialist who has reviewed thousands
        of deliverables across web development, consulting documents,
        research reports, and creative content. You notice everything.""",
        verbose=True,
        allow_delegation=False,
        tools=[file_reader, SaveOutputTool()],
        llm=select_llm("qa", "moderate"),
        max_iter=4
    )


def build_agent_creator_agent() -> Agent:
    return Agent(
        role="AI Systems Architect & Agent Designer",
        goal="""Design new specialist agents when the system cannot handle
        a task. Submit proposals via propose_new_agent tool.
        Never duplicate existing capabilities.""",
        backstory="""AI systems architect who understands what makes agents
        effective. Narrow role, clear goal, realistic backstory, minimal tools.
        Always propose before building.""",
        verbose=True,
        allow_delegation=False,
        tools=ORCHESTRATION_TOOLS + [QueryMemoryTool()],
        llm=select_llm("orchestrator", "complex"),
        max_iter=4
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