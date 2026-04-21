"""
crews.py — Dynamic Crew Assembly
==================================
Assembles the right CrewAI Crew for each task type.

Each crew_*() function:
  1. Builds the appropriate agents
  2. Defines task-agnostic task templates
  3. Returns a configured Crew ready to kickoff()

The actual task content (what to build, for whom) is injected
at runtime by the orchestrator. Crews define STRUCTURE,
not CONTENT.

Adding a new crew:
  1. Create a build_[type]_crew() function here
  2. Map it in CREW_REGISTRY
  3. Register the task type in router.py
  4. Update AGENTS.md

See CLAUDE.md for full checklist.
"""

import os
import logging
import concurrent.futures
from crewai import Agent, Task, Crew, Process
from council import SankofaCouncil, should_invoke_council, CouncilTier
from agents import (
    build_planner_agent,
    build_researcher_agent,
    build_copywriter_agent,
    build_web_builder_agent,
    build_app_builder_agent,
    build_code_agent,
    build_consulting_agent,
    build_social_media_agent,
    build_qa_agent,
    build_orchestrator_agent,
    build_agent_creator_agent,
    build_boub_ai_voice_agent,
    build_hunter_agent,
    build_prompt_engineer_agent,
    build_website_intelligence_agent,
    build_asset_prompter_agent,
    build_3d_web_builder_agent,
    build_seo_auditor_agent,
    build_notion_visual_architect_agent, # Added
    build_content_reviewer_agent,
    build_design_agent,
    get_llm,
)
from design_context import DesignContextLoader

logger = logging.getLogger(__name__)

try:
    # Use relative path for skills to work across environments
    import sys as _sys
    skills_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "skills"))
    if skills_path not in _sys.path:
        _sys.path.insert(0, skills_path)
    from doc_routing.doc_routing_crew import build_doc_routing_crew
except ImportError as e:
    import logging as _logging
    _logging.getLogger(__name__).warning(f"doc_routing_crew import failed: {e}")
    def build_doc_routing_crew(user_request: str, context=None):
        return build_unknown_crew(user_request)


# ── Shared embedder config ─────────────────────────────────────
# Used by all crews for shared memory
EMBEDDER_CONFIG = {
    "provider": "openai",
    "config": {
        "model": "text-embedding-3-small",
        "api_key": os.environ.get("OPENROUTER_API_KEY"),
        "api_base": "https://openrouter.ai/api/v1"
    }
}



def build_website_crew(user_request: str) -> Crew:
    """
    Crew for: website_build
    Builds complete, production-quality HTML websites.
    """
    planner = build_planner_agent()
    researcher = build_researcher_agent()
    copywriter = build_copywriter_agent()
    web_builder = build_web_builder_agent()
    qa = build_qa_agent()

    # Design layer — silent fallback if styleguide files not found
    design_ctx = DesignContextLoader.load("website_build")
    design_agent = build_design_agent() if design_ctx else None

    task_plan = Task(
        description=f"""
        Analyze this website build request and create a detailed execution plan:

        REQUEST: {user_request}

        Your plan must include:
        1. Business type and target audience analysis
        2. Website sections needed (e.g., hero, about, services, contact)
        3. Key messages to communicate
        4. Design direction (colors, tone, feel)
        5. Research questions for the Researcher to answer
        6. Content requirements for the Copywriter
        7. Technical requirements for the Web Builder

        Check memory for any relevant past website projects.
        """,
        expected_output="A structured execution plan covering all 7 points above",
        agent=planner
    )

    task_research = Task(
        description=f"""
        Research the business/project described in this request:
        REQUEST: {user_request}

        Using the execution plan above, find:
        1. Industry context and best practices for this type of business
        2. 2-3 examples of excellent websites in this space (describe their key features)
        3. Typical customer pain points and desires for this business type
        4. Specific details about this business (location, cuisine type, etc.)
        5. SEO considerations and key terms for this type of business

        Be specific. Real data only. No fabrication.
        """,
        expected_output="A structured research brief with all 5 sections addressed",
        agent=researcher,
        context=[task_plan]
    )

    task_copy = Task(
        description=f"""
        Write all website copy based on the plan and research above.

        REQUEST: {user_request}

        Produce complete, final copy for every section:
        - Headline and subheadline (hero section)
        - About/story section (2-3 paragraphs)
        - Services/offerings section (with specific items and descriptions)
        - Any specialty sections called for in the plan
        - Contact section copy
        - Call-to-action text throughout

        Rules:
        - No placeholder text. No lorem ipsum. Real copy only.
        - Write for the actual business, not a generic version.
        - Use the research to make it specific and credible.
        - Match the tone to the business type (warm for restaurants, professional for B2B).
        """,
        expected_output="Complete website copy for all sections, clearly labeled",
        agent=copywriter,
        context=[task_plan, task_research]
    )

    task_design_brief = None
    if design_agent:
        task_design_brief = Task(
            description=f"""
            Produce a concrete design brief for this website build.

            REQUEST: {user_request}

            {design_ctx}

            STEP 1 — Identify output type:
            If the request mentions "catalyst works", "boubacar", "my consulting",
            "our brand", "cw", or "catalystworks.consulting": this is Catalyst Works
            branded output. State: "Loaded Catalyst Works Styleguide v1.0 — 2026-03-29."
            Use the injected styleguide above. Skip steps 2-4.

            STEP 2 — Check for prior design decision:
            Check docs/design-decisions/ for a file matching a slug from the request.
            If found, load and use it. Skip step 3.

            STEP 3 — Extract client brand (if URL in request):
            Use firecrawl_scrape on any client URL to extract brand colors (hex),
            fonts, logo URL, tone. Use this to inform reference selection.

            STEP 4 — Select from docs/design-references/INDEX.md:
            Read the index. Pick the reference that best matches the project type
            and emotional register. State: "Using [name] reference because [reason]."

            STEP 5 — Produce the brief with ALL of:
            - background_color: #hex
            - primary_text_color: #hex
            - accent_color: #hex
            - secondary_color: #hex
            - border_color: #hex
            - heading_font: [name] | import: [Google Fonts URL]
            - body_font: [name] | import: [Google Fonts URL]
            - mono_font: [name] | import: [Google Fonts URL]
            - spacing_base: [px]
            - button_radius: [px]
            - card_style: [description]
            - max_width: [px]
            - anti_patterns: [3 specific things NOT to do for this output]
            - builder_checklist: [5 items the builder must verify before returning]
            """,
            expected_output="Complete design brief with all token values, font imports, and builder checklist",
            agent=design_agent,
            context=[task_plan, task_research],
        )

    task_build = Task(
        description=f"""
        Build a complete, production-ready HTML website using all the copy above.

        REQUEST: {user_request}

        TECHNICAL REQUIREMENTS:
        - Single HTML file, all CSS in <style> tags, all JS in <script> tags
        - Mobile-first responsive design (works perfectly on phone and desktop)
        - Google Fonts (choose appropriate fonts for the brand)
        - CSS custom properties (variables) for color consistency
        - Smooth scroll navigation
        - Tasteful CSS animations (no JavaScript animation libraries)
        - Semantic HTML5 elements
        - All copy from the Copywriter used verbatim

        DESIGN REQUIREMENTS:
        - Follow the design brief from the Design Intelligence Specialist EXACTLY.
        - Use the exact hex values, font names, and spacing from the brief.
        - Do not substitute fonts or colors — use what was specified.
        - Before returning output, run the builder_checklist from the brief and
          confirm each item passes. Include "DESIGN QA: PASSED" in your output.

        OUTPUT:
        - The COMPLETE HTML file. Start with <!DOCTYPE html>. End with </html>.
        - Do NOT truncate. Do NOT summarize. The full file.
        - Save using the save_output tool with an appropriate filename.
        """,
        expected_output="A complete HTML file starting with <!DOCTYPE html> and ending with </html>, saved to outputs",
        agent=web_builder,
        context=[task_plan, task_research, task_copy] + ([task_design_brief] if task_design_brief else [])
    )

    task_seo = Task(
        description=f"""
        Run a thorough SEO and accessibility audit on the website HTML just built.

        REQUEST CONTEXT: {user_request}

        Check every item and fix any issues directly in the HTML:

        SEO:
        - Single H1 per page, logical H2/H3 hierarchy
        - Unique <title> tag (60 chars max) and <meta name="description"> (160 chars max)
        - Alt text on all <img> tags
        - Open Graph tags: og:title, og:description, og:type
        - Schema markup: LocalBusiness or relevant type
        - Canonical <link rel="canonical"> tag

        Accessibility:
        - Color contrast ratios pass WCAG AA (4.5:1 for text)
        - All interactive elements keyboard accessible
        - Skip navigation link at top of page
        - Form labels associated with inputs via for/id
        - Focus indicators visible on interactive elements
        - prefers-reduced-motion media query wraps CSS animations

        Performance:
        - Images have explicit width/height attributes
        - No render-blocking scripts without async/defer
        - Google Fonts loaded with display=swap

        OUTPUT FORMAT:
        FIXES APPLIED: [numbered list of every change made]
        DELIVERABLE:
        [The complete updated HTML file]
        """,
        expected_output="List of SEO/accessibility fixes followed by complete updated HTML",
        agent=web_builder,
        context=[task_build]
    )

    task_qa = Task(
        description=f"""
        Review the website built above against the original request.
        ORIGINAL REQUEST: {user_request}

        CHECK: no placeholder text, complete HTML, all sections present,
        mobile responsive, appropriate design. Fix any issues yourself.

        OUTPUT FORMAT (mandatory every time):
        WHAT WAS DONE: [what was built and why]
        WHY IT WAS DONE THIS WAY: [key design/structure decisions]
        QUALITY CHECK: PASSED or QUALITY CHECK: REVISED — [what was fixed]
        DELIVERABLE:
        [The complete HTML file — always included, never omitted]

        Save final version using save_output.
        """,
        expected_output="Structured QA report followed by complete HTML file",
        agent=qa,
        context=[task_seo]
    )

    return Crew(
        agents=[planner, researcher, copywriter] + ([design_agent] if design_agent else []) + [web_builder, qa],
        tasks=[task_plan, task_research, task_copy] + ([task_design_brief] if task_design_brief else []) + [task_build, task_seo, task_qa],
        process=Process.sequential,
        verbose=False,
        memory=False,
    )


def build_3d_website_crew(user_request: str) -> Crew:
    """
    Crew for: 3d_website_build
    Builds premium scroll-driven 3D animated websites.
    Pipeline: plan → intelligence → competitive report → asset prompts → 3D build → SEO audit → QA
    """
    planner = build_planner_agent()
    intelligence = build_website_intelligence_agent()
    asset_prompter = build_asset_prompter_agent()
    web_builder_3d = build_3d_web_builder_agent()
    seo_auditor = build_seo_auditor_agent()
    qa = build_qa_agent()

    # Design layer — 3D websites share the website_build styleguide
    design_ctx = DesignContextLoader.load("website_build")
    design_agent = build_design_agent() if design_ctx else None

    task_plan = Task(
        description=f"""
        Analyze this 3D website build request and create a detailed execution plan:

        REQUEST: {user_request}

        Your plan must include:
        1. Business type, niche, and target audience
        2. Client website URL to scrape (if provided) or business type for research
        3. Key product or service that needs the 3D scroll animation treatment
        4. Design direction: background color (default #050505), accent color, overall vibe
        5. Research questions for the Intelligence Researcher
        6. Asset direction: what should the scroll animation show?
           (product assembly/deconstruction, before-after transformation, or exploded components)
        7. Site sections needed beyond the 3D hero
        """,
        expected_output="Structured execution plan covering all 7 points",
        agent=planner
    )

    task_intelligence = Task(
        description=f"""
        Run full competitive intelligence research for this project:

        REQUEST: {user_request}

        PHASE 1 — Client brand extraction (if URL provided):
        - Scrape client's existing site with firecrawl_scrape
        - Extract: logo URL, brand colors (hex), fonts, tone, key messaging, site structure

        PHASE 2 — Competitive research:
        - Use firecrawl_search to find top 5 competitors in this niche
        - Score each on: search visibility, visual design, content depth, social proof, CTA strategy
        - Deep-scrape the top 3 with firecrawl_crawl
        - Extract: colors, fonts, headline formulas, CTA copy, site architecture

        PHASE 3 — Synthesis:
        - Identify 3-5 patterns the top competitors share
        - Identify gaps the client can exploit
        - Recommend: color palette, typography, animation direction, page structure

        Save research brief as: research/01-intelligence-brief.md
        """,
        expected_output="Competitive intelligence brief saved to research/01-intelligence-brief.md",
        agent=intelligence,
        context=[task_plan]
    )

    task_competitive_report = Task(
        description=f"""
        Build a polished, print-ready HTML competitive analysis report.

        REQUEST: {user_request}

        Using the intelligence brief, create a single-file HTML report containing:
        1. Cover: report title, business name, date
        2. Executive summary (3-4 sentences)
        3. Top 5 competitor profiles with key strengths, design score, color swatches
        4. Side-by-side comparison table
        5. SEO keyword landscape and gaps
        6. Winning patterns (what all top sites do)
        7. Recommended design direction for this client

        DESIGN SPECS:
        - Background: #f6f4f0, accent: #c45d3e
        - Instrument Serif headings + DM Sans body (Google Fonts)
        - Cards with 4px left border in accent color
        - @media print rules for PDF export
        - No JavaScript — pure HTML + CSS
        - Mobile-responsive at 640px breakpoint

        Save as: competitive-analysis.html
        """,
        expected_output="competitive-analysis.html saved in project directory",
        agent=intelligence,
        context=[task_intelligence]
    )

    task_design_brief = None
    if design_agent:
        task_design_brief = Task(
            description=f"""
            Produce a concrete design brief for this 3D website build.

            REQUEST: {user_request}

            {design_ctx}

            STEP 1 — Identify output type:
            If the request mentions "catalyst works", "boubacar", "my consulting",
            "our brand", "cw", or "catalystworks.consulting": this is Catalyst Works
            branded output. State: "Loaded Catalyst Works Styleguide v1.0 — 2026-03-29."
            Use the injected styleguide above. Skip steps 2-4.

            STEP 2 — Check for prior design decision:
            Check docs/design-decisions/ for a file matching a slug from the request.
            If found, load and use it. Skip step 3.

            STEP 3 — Extract client brand (if URL in request):
            Use firecrawl_scrape on any client URL to extract brand colors (hex),
            fonts, logo URL, tone. Use this to inform reference selection.

            STEP 4 — Select from docs/design-references/INDEX.md:
            Read the index. Pick the reference that best matches the project type
            and emotional register. State: "Using [name] reference because [reason]."

            STEP 5 — Produce the brief with ALL of:
            - background_color: #hex
            - primary_text_color: #hex
            - accent_color: #hex
            - secondary_color: #hex
            - border_color: #hex
            - heading_font: [name] | import: [Google Fonts URL]
            - body_font: [name] | import: [Google Fonts URL]
            - mono_font: [name] | import: [Google Fonts URL]
            - spacing_base: [px]
            - button_radius: [px]
            - card_style: [description]
            - max_width: [px]
            - anti_patterns: [3 specific things NOT to do for this output]
            - builder_checklist: [5 items the builder must verify before returning]
            """,
            expected_output="Complete design brief with all token values, font imports, and builder checklist",
            agent=design_agent,
            context=[task_plan, task_competitive_report],
        )

    task_asset_prompts = Task(
        description=f"""
        Generate 3 coordinated AI image/video prompts for the scroll-stop animation.

        REQUEST: {user_request}

        Based on the plan and intelligence brief, determine animation type:
        - Products with internals: assembled hero + exploded view + assembly video
        - Services/transformations: before state + after state + transformation video

        PROMPT 1 — START FRAME (hero/assembled/before):
        Product perfectly centered, slight natural tilt. Pure solid background matching
        the site's background color (default #050505). Soft studio lighting, glossy,
        dimensional, premium. 16:9. Clean edges for masking. Apple/luxury DTC aesthetic.

        PROMPT 2 — END FRAME (exploded/after):
        Cinematic exploded technical view OR dramatic after-state. Components floating
        in mid-air, perfectly aligned along a clear axis. Same background, same lighting
        direction as Prompt 1. Hyper-realistic Apple industrial design. 16:9.
        No text, no labels, no UI.

        PROMPT 3 — VIDEO TRANSITION (Google Flow style):
        Smooth cinematic transition from Prompt 1 to Prompt 2. Begin with product in
        mid-rotation pose. Components/transformation builds progressively. Energy effect
        midway (light pulse, air displacement). All elements ultra-sharp. 5-6 seconds.
        16:9. Works in Kling, Higgsfield, Runway, Pika.

        Also include user instructions:
        - Recommended image generator settings (16:9, 2K, 4 generations)
        - Recommended video model settings (1080p, 5-6 seconds, no audio)
        - Where to save output: public/sequence/ (for frames) or as hero video

        Save as: asset-prompts.html (tabbed page with copy buttons) and asset-prompts.md
        """,
        expected_output="asset-prompts.html and asset-prompts.md saved in project directory",
        agent=asset_prompter,
        context=[task_plan, task_intelligence]
    )

    task_3d_build = Task(
        description=f"""
        Build the complete Next.js 14 scroll-driven 3D animated website.

        REQUEST: {user_request}

        TECH STACK (mandatory):
        - Next.js 14 with App Router
        - Tailwind CSS
        - Framer Motion (useScroll, useSpring, useTransform)
        - HTML5 Canvas for image sequence
        - TypeScript throughout

        SCROLL ANIMATION:
        - Wrapper div: height 400vh
        - Canvas: sticky, top-0, h-screen, w-full
        - Load frames from /public/sequence/ named frame_0.webp → frame_N.webp
        - useScroll progress 0→1, useSpring (stiffness:100, damping:30)
        - Frame index: Math.floor(scrollProgress * FRAME_COUNT)
        - drawImage() scaled to cover viewport with devicePixelRatio support
        - Preload all frames, show progress bar before revealing experience

        BACKGROUND: must match image sequence exactly (default #050505)

        SCROLLYTELLING BEATS (4 text overlays with real content from brief):
        - Beat A (0-20%): Hero phrase, centered, huge (text-7xl+)
        - Beat B (25-45%): Feature 1, left-aligned
        - Beat C (50-70%): Feature 2, right-aligned
        - Beat D (75-95%): CTA, centered
        - All use useTransform: opacity [0,1,1,0] with 10% fade in/out
        - Subtle vertical: enter y:20→0, exit y:0→-20

        TYPOGRAPHY: Inter or SF Pro, tracking-tight, headings text-white/90, body text-white/60

        SITE SECTIONS below scroll animation:
        - Services/features grid
        - About section
        - Testimonials
        - Contact/CTA
        - Footer

        PLACEHOLDER: If no video provided, create placeholder canvas with comment
        <!-- DROP FRAMES INTO /public/sequence/ --> and instructions in README

        DESIGN REQUIREMENTS:
        - Follow the design brief from the Design Intelligence Specialist EXACTLY.
        - Use the exact hex values, font names, and spacing from the brief.
        - Do not substitute fonts or colors — use what was specified.
        - Before returning output, run the builder_checklist from the brief and
          confirm each item passes. Include "DESIGN QA: PASSED" in your output.

        OUTPUT FILES (save to site/ directory):
        - site/app/page.tsx
        - site/components/ScrollCanvas.tsx
        - site/app/globals.css (Tailwind base + dark custom scrollbar)
        - site/package.json (Next.js 14, Tailwind, Framer Motion)
        - site/README.md (npm install && npm run dev, where to drop frames, Vercel deploy)
        """,
        expected_output="Complete Next.js project files saved to site/ directory",
        agent=web_builder_3d,
        context=[task_plan, task_intelligence, task_asset_prompts] + ([task_design_brief] if task_design_brief else [])
    )

    task_seo = Task(
        description=f"""
        Run SEO and accessibility audit on the Next.js website built above.

        REQUEST: {user_request}

        Audit site/app/page.tsx and site/components/ScrollCanvas.tsx for:

        SEO:
        - <title> and <meta name="description"> in app/layout.tsx
        - Open Graph tags (og:title, og:description, og:type, og:image)
        - Single H1, logical heading hierarchy
        - Alt text on all images
        - JSON-LD schema markup for the business type
        - Canonical link tag

        Accessibility:
        - prefers-reduced-motion wrapping ALL Framer Motion animations
        - Skip navigation link
        - Keyboard accessible interactive elements
        - Focus indicators visible

        Performance:
        - Use Next.js Image component for images where possible
        - Font display swap on Google Fonts

        Fix all issues directly in the relevant files.

        OUTPUT FORMAT:
        FIXES APPLIED: [numbered list]
        FILES MODIFIED: [list]
        """,
        expected_output="Numbered list of SEO/accessibility fixes with files modified",
        agent=seo_auditor,
        context=[task_3d_build]
    )

    task_qa = Task(
        description=f"""
        Final quality check on the complete 3D website project.

        ORIGINAL REQUEST: {user_request}

        Verify all deliverables are present and complete:
        - competitive-analysis.html exists and is well-formed HTML
        - asset-prompts.html exists with all 3 prompts
        - site/app/page.tsx exists with real content (not Lorem ipsum)
        - site/components/ScrollCanvas.tsx exists
        - site/app/globals.css exists
        - site/package.json has Next.js 14, Tailwind, Framer Motion
        - site/README.md explains setup and deployment
        - SEO/accessibility fixes were applied

        OUTPUT FORMAT (mandatory):
        WHAT WAS BUILT: [summary]
        QUALITY CHECK: PASSED or QUALITY CHECK: REVISED — [what was fixed]
        DELIVERABLES:
        - competitive-analysis.html ✓
        - asset-prompts.html ✓
        - site/app/page.tsx ✓
        - site/components/ScrollCanvas.tsx ✓
        - site/README.md ✓
        """,
        expected_output="QA report confirming all deliverables present",
        agent=qa,
        context=[task_seo]
    )

    return Crew(
        agents=[planner, intelligence, asset_prompter] + ([design_agent] if design_agent else []) + [web_builder_3d, seo_auditor, qa],
        tasks=[task_plan, task_intelligence, task_competitive_report] + ([task_design_brief] if task_design_brief else []) + [task_asset_prompts, task_3d_build, task_seo, task_qa],
        process=Process.sequential,
        verbose=False,
        memory=False,
    )


def build_research_crew(user_request: str) -> Crew:
    """
    Crew for: research_report
    Produces structured research reports and analyses.
    """
    planner = build_planner_agent()
    researcher = build_researcher_agent()
    copywriter = build_copywriter_agent()
    qa = build_qa_agent()

    task_plan = Task(
        description=f"""
        Plan a comprehensive research response for:
        REQUEST: {user_request}

        Define: research questions, required depth, output format,
        and any constraints or focus areas.
        """,
        expected_output="Research plan with defined questions and output format",
        agent=planner
    )

    task_research = Task(
        description=f"""
        Conduct thorough research for:
        REQUEST: {user_request}

        Following the research plan, gather comprehensive, accurate,
        current information. Cite sources. Distinguish facts from opinions.
        Identify key findings, notable data points, and open questions.
        """,
        expected_output="Comprehensive research findings with sources",
        agent=researcher,
        context=[task_plan]
    )

    task_write = Task(
        description=f"""
        Write a clear, structured report based on the research above for:
        REQUEST: {user_request}

        Format: Executive Summary → Key Findings → Analysis → Implications → Sources
        Length: As long as needed to fully address the request — no padding.
        Tone: Clear, direct, professional.
        Save using save_output.
        """,
        expected_output="Complete structured research report saved to outputs",
        agent=copywriter,
        context=[task_plan, task_research]
    )

    task_qa = Task(
        description=f"""
        Review the research report for accuracy, completeness, and clarity.
        Fix any issues yourself. Original request: {user_request}

        OUTPUT FORMAT (mandatory every time):
        WHAT WAS DONE: [what was researched and reported]
        WHY IT WAS DONE THIS WAY: [structure and angle chosen]
        QUALITY CHECK: PASSED or QUALITY CHECK: REVISED — [what was fixed]
        DELIVERABLE:
        [The complete report — always included, never omitted]
        """,
        expected_output="Structured QA report followed by complete research report",
        agent=qa,
        context=[task_write]
    )

    return Crew(
        agents=[planner, researcher, copywriter, qa],
        tasks=[task_plan, task_research, task_write, task_qa],
        process=Process.sequential,
        verbose=False,
        memory=False,
    )


def build_consulting_crew(user_request: str, metadata: dict = None) -> Crew:
    """
    Crew for: consulting_deliverable
    Creates professional consulting artifacts.

    When CouncilTier.FULL is active (default for this task type):
      planner → researcher → [SankofaCouncil] → qa
    Fallback on council error:
      planner → researcher → consultant → qa (original path)
    """
    metadata = metadata or {}
    council_tier = should_invoke_council("consulting_deliverable", metadata)

    planner = build_planner_agent()
    researcher = build_researcher_agent()
    qa = build_qa_agent()

    # Design layer — silent fallback if styleguide files not found
    design_ctx = DesignContextLoader.load("consulting_deliverable")
    design_agent = build_design_agent() if design_ctx else None

    task_plan = Task(
        description=f"""
        Plan a consulting deliverable for:
        REQUEST: {user_request}

        Identify: deliverable type, client context, key messages,
        structure, and evidence needed. Check memory for similar
        past engagements.
        """,
        expected_output="Consulting deliverable plan with structure and evidence requirements",
        agent=planner
    )

    task_research = Task(
        description=f"""
        Research context and evidence for:
        REQUEST: {user_request}

        Find: industry benchmarks, best practices, case studies,
        relevant frameworks, and data points that strengthen the deliverable.
        """,
        expected_output="Research brief with supporting evidence and context",
        agent=researcher,
        context=[task_plan]
    )

    if council_tier == CouncilTier.FULL:
        # Run SankofaCouncil directly via litellm BEFORE crew assembly.
        # A CrewAI agent cannot execute Python — asking it to "run the council"
        # causes max-iterations → handle_max_iterations_exceeded → Anthropic
        # prefill error. Council runs independently; result injected into QA task.
        council_ran = False
        chairman_synthesis = ""
        convergence_note = ""
        try:
            _council = SankofaCouncil()
            _result = _council.run(
                query=user_request,
                context="",
                task_type="consulting_deliverable",
            )
            chairman_synthesis = _result.get("chairman_synthesis", "")
            convergence_note = _result.get("convergence_note", "")
            council_ran = bool(chairman_synthesis)
        except Exception as e:
            logger.warning(f"SankofaCouncil failed, falling back to single-consultant: {e}")

        if council_ran:
            # Council ran successfully — chairman synthesis IS the deliverable.
            # Do NOT route through a CrewAI QA agent: the QA agent uses an
            # Anthropic model that hits max_iter on large prompts, triggering
            # handle_max_iterations_exceeded → assistant-prefill → 400 error.
            # Instead: use a single Gemini Flash formatter task (non-Anthropic,
            # no prefill restriction, succeeds on iteration 1).
            formatter = Agent(
                role="Output Formatter",
                goal="Format the council synthesis into the required output structure",
                backstory="You format pre-written consulting content into the required output template. You do not add, remove, or analyze content.",
                llm=get_llm("gemini-flash"),
                max_iter=2,
                verbose=False,
            )
            task_format = Task(
                description=f"""Format this pre-written council synthesis into the required output structure.
Do not change, add, or remove any content. Only apply the format below.

ORIGINAL REQUEST: {user_request}

COUNCIL OUTPUT:
{chairman_synthesis}

{('COUNCIL NOTE: ' + convergence_note) if convergence_note else ''}

OUTPUT FORMAT (copy exactly, fill in brackets):
WHAT WAS DONE: [one sentence: deliverable type and purpose]
WHY IT WAS DONE THIS WAY: [one sentence: strategic framing]
QUALITY CHECK: PASSED
DELIVERABLE:
[Paste the full council output here verbatim]
""",
                expected_output="Formatted output with WHAT WAS DONE, WHY, QUALITY CHECK, and DELIVERABLE sections",
                agent=formatter,
            )
            return Crew(
                agents=[formatter],
                tasks=[task_format],
                process=Process.sequential,
                verbose=False,
                memory=False,
            )

    else:
        # Fallback: original single-consultant path
        consultant = build_consulting_agent()

        task_design_brief = None
        if design_agent:
            task_design_brief = Task(
                description=f"""
                Produce a concrete design brief for this consulting deliverable.

                REQUEST: {user_request}

                {design_ctx}

                STEP 1 — Identify output type:
                If the request mentions "catalyst works", "boubacar", "my consulting",
                "our brand", "cw", or "catalystworks.consulting": this is Catalyst Works
                branded output. State: "Loaded Catalyst Works Styleguide v1.0 — 2026-03-29."
                Use the injected styleguide above. Skip steps 2-4.

                STEP 2 — Check for prior design decision:
                Check docs/design-decisions/ for a file matching a slug from the request.
                If found, load and use it. Skip step 3.

                STEP 3 — Extract client brand (if URL in request):
                Use firecrawl_scrape on any client URL to extract brand colors (hex),
                fonts, logo URL, tone. Use this to inform reference selection.

                STEP 4 — Select from docs/design-references/INDEX.md:
                Read the index. Pick the reference that best matches the project type
                and emotional register. State: "Using [name] reference because [reason]."

                STEP 5 — Produce the brief with ALL of:
                - background_color: #hex
                - primary_text_color: #hex
                - accent_color: #hex
                - secondary_color: #hex
                - border_color: #hex
                - heading_font: [name] | import: [Google Fonts URL]
                - body_font: [name] | import: [Google Fonts URL]
                - mono_font: [name] | import: [Google Fonts URL]
                - spacing_base: [px]
                - button_radius: [px]
                - card_style: [description]
                - max_width: [px]
                - anti_patterns: [3 specific things NOT to do for this output]
                - builder_checklist: [5 items the builder must verify before returning]

                NOTE: This is a consulting deliverable. If Catalyst Works branded,
                focus on PDF document specs: cover page (#1B2A4A background, #C49A2E gold rule),
                Plus Jakarta Sans headings, Source Serif 4 body text, callout box styling.
                """,
                expected_output="Complete design brief with all token values, font imports, and builder checklist",
                agent=design_agent,
                context=[task_plan, task_research],
            )

        task_consult = Task(
            description=f"""
            Create the consulting deliverable for:
            REQUEST: {user_request}

            DESIGN REQUIREMENTS:
            - Follow the design brief from the Design Intelligence Specialist EXACTLY.
            - Use the exact hex values, font names, and spacing from the brief.
            - Do not substitute fonts or colors — use what was specified.
            - Before returning output, run the builder_checklist from the brief and
              confirm each item passes. Include "DESIGN QA: PASSED" in your output.

            Be analytically rigorous. Be direct. Avoid filler.
            Every recommendation must be specific and implementable.
            Save using save_output.
            """,
            expected_output="Complete consulting deliverable saved to outputs",
            agent=consultant,
            context=[task_plan, task_research] + ([task_design_brief] if task_design_brief else [])
        )

        task_qa = Task(
            description=f"""
            Review the consulting deliverable for quality, completeness, and
            professional standards. Fix any issues yourself. Original: {user_request}

            OUTPUT FORMAT (mandatory every time):
            WHAT WAS DONE: [deliverable type and purpose]
            WHY IT WAS DONE THIS WAY: [strategic framing chosen]
            QUALITY CHECK: PASSED or QUALITY CHECK: REVISED — [what was fixed]
            DELIVERABLE:
            [The complete consulting deliverable — always included, never omitted]
            """,
            expected_output="Structured QA report followed by complete consulting deliverable",
            agent=qa,
            context=[task_consult]
        )

        return Crew(
            agents=[planner, researcher] + ([design_agent] if design_agent else []) + [consultant, qa],
            tasks=[task_plan, task_research] + ([task_design_brief] if task_design_brief else []) + [task_consult, task_qa],
            process=Process.sequential,
            verbose=False,
            memory=False,
        )


def build_social_crew(user_request: str) -> Crew:
    """
    Crew for: social_content
    Creates social media content in Boubacar's voice.
    """
    planner = build_planner_agent()
    griot = build_social_media_agent()
    qa = build_qa_agent()

    task_plan = Task(
        description=f"""
        Plan social content for:
        REQUEST: {user_request}

        Identify: platform(s), content angle, key idea to communicate,
        tone, and format (single post, thread, carousel text, etc.)
        """,
        expected_output="Social content plan with platform, format, and angle",
        agent=planner
    )

    task_write = Task(
        description=f"""
        Write the social content for:
        REQUEST: {user_request}

        Write in Boubacar's voice: direct, insightful, specific, and real.
        No "I'm excited to share..." No buzzword soup.
        Include platform-appropriate formatting (hashtags for Instagram,
        thread numbering for X, professional framing for LinkedIn).
        Provide 2-3 variations so Boubacar can choose.
        Save using save_output.
        """,
        expected_output="2-3 variations of the social content, platform-formatted",
        agent=griot,
        context=[task_plan]
    )

    task_qa = Task(
        description=f"""
        Review the social content. Does it sound like Boubacar — direct,
        specific, earned? Does it teach or provoke thought?
        If any post is too generic, rewrite it. Original: {user_request}

        OUTPUT FORMAT (mandatory every time):
        WHAT WAS DONE: [what content was created and for which platform]
        WHY IT WAS DONE THIS WAY: [voice and angle decisions]
        QUALITY CHECK: PASSED or QUALITY CHECK: REVISED — [what was fixed]
        DELIVERABLE:
        [All posts in full — always included, never omitted, even if revised]
        """,
        expected_output="Structured QA report followed by all final posts",
        agent=qa,
        context=[task_write]
    )

    return Crew(
        agents=[planner, griot, qa],
        tasks=[task_plan, task_write, task_qa],
        process=Process.sequential,
        verbose=False,
        memory=False,
    )


def build_linkedin_x_crew(user_request: str) -> Crew:
    """
    Crew for: linkedin_x_campaign
    Produces full 7-post LinkedIn + X sequence plus long-form article.
    Fires when user asks for LinkedIn and X posts on a topic.
    """
    griot = build_social_media_agent()
    qa = build_qa_agent()

    LEGRIOT_SYSTEM_PROMPT = """You are leGriot, Boubacar Barry's social media content agent.

Boubacar is the founder of Catalyst Works, a solo AI strategy
consulting practice targeting SMB leadership teams (CEOs, COOs,
operations leaders). His methodology is constraint-led: he
identifies the single bottleneck limiting organizational throughput
before recommending any AI intervention. His differentiator is
intellectual honesty -- he will tell clients when AI is not
the answer.

Voice Profile:
- Direct. No hedging. No throat-clearing.
- Specific and grounded. Sounds like a practitioner, not a pundit.
- Earned confidence. He knows this from real work, not theory.
- Occasionally provocative. The best content disagrees with something.
- Warm but precise. Never robotic, never salesy, never corporate.
- Never uses: "I'm excited to share", "In today's fast-paced world",
  "game-changer", "leverage", "synergy", "disruptive"
- Never uses em dashes anywhere.
- NEVER fabricate stories or invent client examples.
- If no real story was provided, use "Imagine if..." or "Picture this..."
  to signal it is hypothetical.

Post Mix (fixed sequence -- do not reorder):
Post 1 -- Challenger: creates tension, names the problem directly
Post 2 -- Insight: behavioral science, research, or mechanism explanation
Post 3 -- Contrarian: disagrees with a common assumption or practice
Post 4 -- Personal: specific real experience that earns the point
Post 5 -- Insight (Data): 2 to 3 sharp statistics that reframe the situation
Post 6 -- Insight: deepens the mechanism or names the human cost
Post 7 -- Challenger: closes with a direct call to action or decision prompt

Hook Quality Test (apply to every hook before finalizing):
- Does it create immediate curiosity or provocation?
- Does it make a specific, surprising claim?
- Would someone stop scrolling for this?
If no to any of these, rewrite the hook.

Format Rules:

LinkedIn Long-Form Article (tied to Post 1):
- 400 to 600 words
- Opens with same hook as Post 1, then goes deeper
- Structure: Hook -> Problem -> Mechanism -> Evidence -> Personal anchor -> Implication -> CTA
- CTA must be specific: a question, a reflection prompt, or an invitation to connect
- No hashtags
- No em dashes

LinkedIn Posts (Posts 1 through 7):
- 150 to 300 words each
- Short punchy lines. One idea per line where possible.
- End with a question, call to reflection, or soft CTA
- No hashtags unless specifically requested
- No em dashes

X Posts (one per LinkedIn post):
- Default to standalone posts of 280 characters maximum
- Use numbered thread (1/ 2/ 3/) ONLY when idea cannot be compressed
- Hook must work in the first line alone
- No em dashes

Output Structure (deliver in this exact order and format):

---
## LinkedIn Article -- Post 1 Expanded
[article]
---
### Post 1 -- Challenger

**LinkedIn:**
[post]

**X:**
[post or thread]
---
### Post 2 -- Insight

**LinkedIn:**
[post]

**X:**
[post or thread]
---
[continue through Post 7 in the same format]"""

    task_write = Task(
        description=f"""
{LEGRIOT_SYSTEM_PROMPT}

## Topic
{user_request}

Write the full campaign now. Follow the output structure exactly.
Save the completed output using save_output.
        """,
        expected_output=(
            "LinkedIn long-form article followed by all 7 LinkedIn posts "
            "and 7 matching X posts in the required format"
        ),
        agent=griot,
    )

    task_qa = Task(
        description=f"""
Review this LinkedIn/X campaign for Boubacar Barry.

Check each item:
1. Hook quality: does every post open with curiosity, provocation, or a specific surprising claim?
2. Voice: direct, practitioner-grounded, no buzzwords, no em dashes?
3. Post types: are all 7 types present in the correct order (Challenger, Insight, Contrarian, Personal, Data, Insight, Challenger)?
4. Word counts: LinkedIn article 400-600 words, LinkedIn posts 150-300 words, X posts 280 chars max?
5. No fabricated stories presented as real?

If any item fails, rewrite the affected post inline. Do not just flag -- fix it.

Original topic: {user_request}

OUTPUT FORMAT (mandatory):
WHAT WAS DONE: [what campaign was created and for which topic]
WHY IT WAS DONE THIS WAY: [voice and structural decisions]
QUALITY CHECK: PASSED or QUALITY CHECK: REVISED -- [what was fixed]
DELIVERABLE:
[Complete campaign in full -- article then all 7 post pairs -- never omit, never truncate]
        """,
        expected_output="QA report followed by complete campaign with article and all 7 post pairs",
        agent=qa,
        context=[task_write],
    )

    return Crew(
        agents=[griot, qa],
        tasks=[task_write, task_qa],
        process=Process.sequential,
        verbose=False,
        memory=False,
    )


def build_code_crew(user_request: str) -> Crew:
    """
    Crew for: code_task
    Handles programming tasks of any kind.
    """
    planner = build_planner_agent()
    coder = build_code_agent()
    qa = build_qa_agent()

    task_plan = Task(
        description=f"""
        Plan the coding task:
        REQUEST: {user_request}

        Define: language, approach, inputs/outputs, edge cases,
        and any libraries or APIs needed.
        """,
        expected_output="Code task plan with technical specifications",
        agent=planner
    )

    task_code = Task(
        description=f"""
        Implement the solution for:
        REQUEST: {user_request}

        Write complete, working, well-commented code.
        Include usage instructions as a comment at the top.
        Test mentally against edge cases before finalizing.
        Save using save_output with an appropriate filename and extension.
        """,
        expected_output="Complete, working code saved to outputs",
        agent=coder,
        context=[task_plan]
    )

    task_qa = Task(
        description=f"""
        Review the code for correctness, completeness, and readability.
        Fix any issues yourself. Original: {user_request}

        OUTPUT FORMAT (mandatory every time):
        WHAT WAS DONE: [what was coded and why]
        WHY IT WAS DONE THIS WAY: [technical approach chosen]
        QUALITY CHECK: PASSED or QUALITY CHECK: REVISED — [what was fixed]
        DELIVERABLE:
        [The complete final code — always included, never omitted]
        """,
        expected_output="Structured QA report followed by complete final code",
        agent=qa,
        context=[task_code]
    )

    return Crew(
        agents=[planner, coder, qa],
        tasks=[task_plan, task_code, task_qa],
        process=Process.sequential,
        verbose=False,
        memory=False,
    )


def build_writing_crew(user_request: str) -> Crew:
    """
    Crew for: general_writing
    Handles any writing task: emails, articles, documents.
    """
    planner = build_planner_agent()
    copywriter = build_copywriter_agent()
    qa = build_qa_agent()

    task_plan = Task(
        description=f"""
        Plan the writing task:
        REQUEST: {user_request}
        Define: document type, audience, tone, length, and structure.
        """,
        expected_output="Writing plan with defined structure and requirements",
        agent=planner
    )

    task_write = Task(
        description=f"""
        Write the document for:
        REQUEST: {user_request}
        Complete, polished, ready to use. No drafts. No placeholders.
        Save using save_output.
        """,
        expected_output="Complete document saved to outputs",
        agent=copywriter,
        context=[task_plan]
    )

    task_qa = Task(
        description=f"""
        Review the document for quality and completeness.
        Fix any issues yourself. Original: {user_request}

        OUTPUT FORMAT (mandatory every time):
        WHAT WAS DONE: [document type and purpose]
        WHY IT WAS DONE THIS WAY: [structure and tone chosen]
        QUALITY CHECK: PASSED or QUALITY CHECK: REVISED — [what was fixed]
        DELIVERABLE:
        [The complete document — always included, never omitted]
        """,
        expected_output="Structured QA report followed by complete final document",
        agent=qa,
        context=[task_write]
    )

    return Crew(
        agents=[planner, copywriter, qa],
        tasks=[task_plan, task_write, task_qa],
        process=Process.sequential,
        verbose=False,
        memory=False,
    )


def build_app_crew(user_request: str) -> Crew:
    """
    Crew for: app_build
    Builds interactive web applications.
    """
    planner = build_planner_agent()
    researcher = build_researcher_agent()
    app_builder = build_app_builder_agent()
    qa = build_qa_agent()

    # Design layer — silent fallback if styleguide files not found
    design_ctx = DesignContextLoader.load("app_build")
    design_agent = build_design_agent() if design_ctx else None

    task_plan = Task(
        description=f"""
        Plan the web application for:
        REQUEST: {user_request}
        Define: features, user flows, data model, tech stack, UI structure.
        """,
        expected_output="Complete app specification and technical plan",
        agent=planner
    )

    task_research = Task(
        description=f"""
        Research UX patterns, technical approaches, and examples for:
        REQUEST: {user_request}
        Find best practices for this type of application.
        """,
        expected_output="Research brief with UX patterns and technical recommendations",
        agent=researcher,
        context=[task_plan]
    )

    task_design_brief = None
    if design_agent:
        task_design_brief = Task(
            description=f"""
            Produce a concrete design brief for this app build.

            REQUEST: {user_request}

            {design_ctx}

            STEP 1 — Identify output type:
            If the request mentions "catalyst works", "boubacar", "my consulting",
            "our brand", "cw", or "catalystworks.consulting": this is Catalyst Works
            branded output. State: "Loaded Catalyst Works Styleguide v1.0 — 2026-03-29."
            Use the injected styleguide above. Skip steps 2-4.

            STEP 2 — Check for prior design decision:
            Check docs/design-decisions/ for a file matching a slug from the request.
            If found, load and use it. Skip step 3.

            STEP 3 — Extract client brand (if URL in request):
            Use firecrawl_scrape on any client URL to extract brand colors (hex),
            fonts, logo URL, tone. Use this to inform reference selection.

            STEP 4 — Select from docs/design-references/INDEX.md:
            Read the index. Pick the reference that best matches the project type
            and emotional register. State: "Using [name] reference because [reason]."

            STEP 5 — Produce the brief with ALL of:
            - background_color: #hex
            - primary_text_color: #hex
            - accent_color: #hex
            - secondary_color: #hex
            - border_color: #hex
            - heading_font: [name] | import: [Google Fonts URL]
            - body_font: [name] | import: [Google Fonts URL]
            - mono_font: [name] | import: [Google Fonts URL]
            - spacing_base: [px]
            - button_radius: [px]
            - card_style: [description]
            - max_width: [px]
            - anti_patterns: [3 specific things NOT to do for this output]
            - builder_checklist: [5 items the builder must verify before returning]
            """,
            expected_output="Complete design brief with all token values, font imports, and builder checklist",
            agent=design_agent,
            context=[task_plan, task_research],
        )

    task_build = Task(
        description=f"""
        Build the complete web application for:
        REQUEST: {user_request}

        DESIGN REQUIREMENTS:
        - Follow the design brief from the Design Intelligence Specialist EXACTLY.
        - Use the exact hex values, font names, and spacing from the brief.
        - Do not substitute fonts or colors — use what was specified.
        - Before returning output, run the builder_checklist from the brief and
          confirm each item passes. Include "DESIGN QA: PASSED" in your output.

        All functionality working. Clean UX. Handles edge cases.
        Save using save_output.
        """,
        expected_output="Complete working web application saved to outputs",
        agent=app_builder,
        context=[task_plan, task_research] + ([task_design_brief] if task_design_brief else [])
    )

    task_qa = Task(
        description=f"""
        Review the application: does everything work, are edge cases handled,
        is the UX intuitive? Fix any issues yourself. Original: {user_request}

        OUTPUT FORMAT (mandatory every time):
        WHAT WAS DONE: [what app was built and why]
        WHY IT WAS DONE THIS WAY: [tech and UX decisions]
        QUALITY CHECK: PASSED or QUALITY CHECK: REVISED — [what was fixed]
        DELIVERABLE:
        [The complete application code — always included, never omitted]
        """,
        expected_output="Structured QA report followed by complete final application",
        agent=qa,
        context=[task_build]
    )

    return Crew(
        agents=[planner, researcher] + ([design_agent] if design_agent else []) + [app_builder, qa],
        tasks=[task_plan, task_research] + ([task_design_brief] if task_design_brief else []) + [task_build, task_qa],
        process=Process.sequential,
        verbose=False,
        memory=False,
    )


def build_agent_creator_crew(user_request: str) -> Crew:
    """
    Crew for: agent_creation
    Designs new specialist agents for the system.
    This is how agentsHQ expands its own capabilities.
    """
    orchestrator = build_orchestrator_agent()
    agent_creator = build_agent_creator_agent()

    task_assess = Task(
        description=f"""
        Assess the request for a new agent capability:
        REQUEST: {user_request}

        First, review all existing agents and task types in the system.
        Determine:
        1. Is this truly a new capability or can existing agents handle it?
        2. What specifically can't the current system do?
        3. What would the new agent need to be able to do?
        """,
        expected_output="Gap analysis: what exists, what's missing, what needs to be created",
        agent=orchestrator
    )

    task_design = Task(
        description=f"""
        Design the new agent spec for:
        REQUEST: {user_request}

        Produce a complete specification and submit it for approval
        using the propose_new_agent tool. Include:
        - agent_name (snake_case)
        - role (professional title)
        - goal (what they optimize for)
        - backstory (2-3 sentences shaping their reasoning)
        - tools_needed (list of tool names)
        - task_type_key (snake_case identifier)
        - trigger_keywords (list of 5-10 words)
        """,
        expected_output="Complete agent specification submitted via propose_new_agent tool",
        agent=agent_creator,
        context=[task_assess]
    )

    return Crew(
        agents=[orchestrator, agent_creator],
        tasks=[task_assess, task_design],
        process=Process.sequential,
        verbose=False,
        memory=False,

    )


def build_forge_kpi_crew(user_request: str) -> Crew:  # noqa: ARG001
    """
    Direct trigger for the Forge KPI refresh.
    Calls kpi_refresh() as a Python function — no LLM agent loop, no prefill risk.
    Returns a single-agent crew with a pre-executed result injected as context.
    """
    from skills.forge_cli.forge import kpi_refresh

    try:
        kpi_refresh()
        result_text = "Forge KPI refresh completed successfully. Quotes, streak, motivation, phase, and week grid callout blocks have been updated on The Forge Notion dashboard."
    except Exception as e:
        result_text = f"Forge KPI refresh failed: {e}"

    formatter = Agent(
        role="Status Reporter",
        goal="Report the outcome of a system operation",
        backstory="You relay pre-computed system results to the user. You do not add analysis or take further actions.",
        llm=get_llm("gemini-flash"),
        max_iter=1,
        verbose=False,
    )
    task_report = Task(
        description=f"Report this system result to the user verbatim:\n\n{result_text}",
        expected_output="The system result message, reported as-is",
        agent=formatter,
    )
    return Crew(
        agents=[formatter],
        tasks=[task_report],
        process=Process.sequential,
        verbose=False,
        memory=False,
    )


def _infer_media_task_type(user_request: str) -> tuple[str, str]:
    """
    Return (modality, task_subtype):
      modality: 'image' or 'video'
      task_subtype: text_to_image | image_to_image | text_to_video | image_to_video
    """
    msg = user_request.lower()
    has_ref = "http://" in msg or "https://" in msg or "reference:" in msg or "from this image" in msg
    if any(k in msg for k in ["video", "animate", "animation", "mp4", "clip"]):
        return ("video", "image_to_video" if has_ref else "text_to_video")
    return ("image", "image_to_image" if has_ref else "text_to_image")


def _extract_media_prompt(user_request: str) -> str:
    """Strip the imperative 'create a video/image of ...' so the prompt is clean."""
    msg = user_request.strip()
    for prefix in [
        "create a video of ", "create a video ", "create video of ", "create video ",
        "generate a video of ", "generate a video ", "generate video of ", "generate video ",
        "make a video of ", "make a video ", "make video of ", "make video ",
        "create an image of ", "create an image ", "create image of ", "create image ",
        "generate an image of ", "generate an image ", "generate image of ", "generate image ",
        "make an image of ", "make an image ", "make image of ", "make image ",
        "picture of ", "image of ", "video of ",
    ]:
        if msg.lower().startswith(prefix):
            return msg[len(prefix):].strip().rstrip(".") or msg
    return msg


def build_media_crew(user_request: str) -> Crew:
    """
    Crew for: create_media
    Generates an image or video via Kai (kie.ai). Picks top-ranked model for the
    inferred task type, retries with fallback ranks on failure, uploads to
    Google Drive 05_Asset_Library/, logs metadata to Supabase and the Notion
    Media_Index DB.

    Pattern follows build_forge_kpi_crew: direct Python call, single reporter agent.
    Keeps the LLM out of the generation loop so cost is predictable.
    """
    try:
        from kie_media import generate_image, generate_video, KieMediaError
    except ImportError as e:
        logger.error(f"kie_media import failed: {e}")
        return build_unknown_crew(user_request)

    modality, task_subtype = _infer_media_task_type(user_request)
    prompt = _extract_media_prompt(user_request)

    try:
        if modality == "video":
            result = generate_video(prompt=prompt, task_type=task_subtype)
        else:
            result = generate_image(prompt=prompt, task_type=task_subtype)
        result_text = (
            f"Generated {modality} successfully.\n"
            f"Model used: {result['model_used']} (rank {result['rank_used']})\n"
            f"Drive: {result['drive_url']}\n"
            f"File: {result['filename']}\n"
            f"Local: {result['local_path']}\n"
            f"Attempts: {len(result['attempts'])}"
        )
    except KieMediaError as e:
        result_text = (
            f"{modality.capitalize()} generation failed after all retries.\n"
            f"Error: {e}\n"
            f"Prompt attempted: {prompt[:200]}\n"
            f"Suggest: review docs/kai_model_registry.md and rerank models, "
            f"or check `kie_check_credits` balance."
        )
    except Exception as e:
        result_text = f"{modality.capitalize()} generation hit unexpected error: {type(e).__name__}: {e}"

    formatter = Agent(
        role="Media Generation Reporter",
        goal="Report the outcome of a Kai media generation operation",
        backstory=(
            "You relay pre-computed media generation results to the user. "
            "You do not retry, re-prompt, or call the model again. "
            "When the user sees your reply they should see the Drive URL if it succeeded, "
            "or the exact failure reason if it did not."
        ),
        llm=get_llm("gemini-flash"),
        max_iter=1,
        verbose=False,
    )
    task_report = Task(
        description=f"Report this media generation result to the user verbatim:\n\n{result_text}",
        expected_output="The media generation result message, reported as-is",
        agent=formatter,
    )
    return Crew(
        agents=[formatter],
        tasks=[task_report],
        process=Process.sequential,
        verbose=False,
        memory=False,
    )


def build_unknown_crew(user_request: str) -> Crew:
    """
    Fallback crew for unknown task types.
    Either attempts the task or escalates with a new agent proposal.
    Uses Gemini Flash to avoid Anthropic assistant-prefill errors on max_iter exhaustion.
    """
    orchestrator = build_orchestrator_agent()
    agent_creator = build_agent_creator_agent()

    # Override the orchestrator's LLM to Gemini Flash for this crew.
    # Anthropic models reject the assistant-prefill message that CrewAI sends
    # when max_iter is hit (handle_max_iterations_exceeded). Gemini Flash does not
    # have this restriction and succeeds on iteration 1 for most unknown tasks.
    orchestrator.llm = get_llm("gemini-flash")
    orchestrator.max_iter = 3

    task_assess = Task(
        description=f"""
        An unknown request has arrived that doesn't match any task type:
        REQUEST: {user_request}

        Your options:
        1. If you can handle it reasonably well with existing capabilities, do so.
        2. If not, use the propose_new_agent tool to design and submit a new
           agent specification for Boubacar's approval.
        3. If it's truly ambiguous, use escalate_to_owner to ask for clarification.

        Never hallucinate. Never pretend to do something you can't.
        """,
        expected_output="Either a completed deliverable OR a submitted agent proposal OR an escalation",
        agent=orchestrator
    )

    return Crew(
        agents=[orchestrator, agent_creator],
        tasks=[task_assess],
        process=Process.sequential,
        verbose=False,
        memory=False,
    )


# ══════════════════════════════════════════════════════════════
# AGENT TEAMS — PARALLEL EXECUTION
# ══════════════════════════════════════════════════════════════

def run_parallel_team(subtasks: list) -> list:
    """
    Run multiple crews in parallel using ThreadPoolExecutor.

    Each subtask is a dict: {"crew_type": str, "task": str, "label": str}
    Returns a list of result dicts: {"label", "crew_type", "result", "success"}

    Capped at 5 parallel workers to avoid API rate limits.
    """
    def _run_one(subtask: dict) -> dict:
        crew_type = subtask["crew_type"]
        task = subtask["task"]
        label = subtask.get("label", crew_type)
        try:
            crew = assemble_crew(crew_type, task)
            result = crew.kickoff()
            logger.info(f"[agent-team] Teammate '{label}' completed")
            return {"label": label, "crew_type": crew_type, "result": str(result), "success": True}
        except Exception as e:
            logger.error(f"[agent-team] Teammate '{label}' failed: {e}")
            return {"label": label, "crew_type": crew_type, "result": f"ERROR: {e}", "success": False}

    max_workers = min(len(subtasks), 5)
    logger.info(f"[agent-team] Dispatching {len(subtasks)} teammates ({max_workers} parallel workers)")

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_run_one, st): st for st in subtasks}
        results = [future.result() for future in concurrent.futures.as_completed(futures)]

    return results


def build_team_synthesis_crew(original_request: str, teammate_results: list) -> Crew:
    """
    Synthesis step: combines all teammate outputs into one coherent deliverable.
    Called after run_parallel_team() completes.
    """
    consultant = build_consulting_agent()
    qa = build_qa_agent()

    results_context = "\n\n".join([
        f"### {r['label'].upper()} (via {r['crew_type']})\n{r['result']}"
        for r in teammate_results
    ])

    synthesis_task = Task(
        description=(
            f"Original request: {original_request}\n\n"
            f"Multiple specialist teams completed their work in parallel. "
            f"Synthesize their outputs into one coherent, well-structured deliverable.\n\n"
            f"Teammate outputs:\n{results_context}\n\n"
            f"Produce a unified result that integrates all findings, eliminates redundancy, "
            f"and presents a clear actionable conclusion. "
            f"Save the final output using the save_output tool."
        ),
        agent=consultant,
        expected_output="A unified, synthesized deliverable combining all teammate outputs."
    )

    qa_task = Task(
        description=(
            f"Review the synthesized output against the original request: '{original_request}'. "
            f"Verify it is complete, coherent, and addresses what was asked. "
            f"Fix anything missing or contradictory.\n\n"
            f"OUTPUT FORMAT (mandatory every time):\n"
            f"WHAT WAS DONE: [what was synthesized]\n"
            f"WHY IT WAS DONE THIS WAY: [synthesis approach]\n"
            f"QUALITY CHECK: PASSED or QUALITY CHECK: REVISED — [what was fixed]\n"
            f"DELIVERABLE:\n[Complete synthesized output — always included, never omitted]"
        ),
        agent=qa,
        expected_output="Structured QA report followed by complete synthesized deliverable",
        context=[synthesis_task]
    )

    return Crew(
        agents=[consultant, qa],
        tasks=[synthesis_task, qa_task],
        process=Process.sequential,
        verbose=False,
        memory=False,
    )


def build_hunter_crew(user_request: str) -> Crew:
    """
    Hunter Crew — daily lead prospecting engine.

    Pipeline:
      1. discover_leads  → Serper LinkedIn dork + local business + Firecrawl + Hunter.io + Apollo fallback
      2. save_to_crm     → add_lead() for each result
      3. scoreboard      → report today's stats

    Triggered by: "find leads", "prospect", "hunter", "daily run"
    """
    hunter = build_hunter_agent()

    discovery_task = Task(
        description=(
            f"GOAL: Find high-quality Utah SMB leads and FULLY ENRICH them.\n"
            f"INDUSTRIES: Legal, Accounting, Marketing Agency, HVAC, Plumbing, Roofing.\n"
            f"LOCATIONS: Salt Lake City, Provo, Orem, Lehi, Murray, Sandy.\n"
            f"TITLES: Owner, Founder, CEO, President, Managing Partner.\n"
            f"ACTION: Call discover_leads with the user's query override if provided. "
            f"For every lead returned, call add_lead to save it to the CRM. "
            f"Collect phone, email, LinkedIn URL, company, and title for each lead.\n"
            f"USER REQUEST: {user_request}\n\n"
            f"IMPORTANT: Ensure ALL leads are enriched with emails. Use reveal_email_for_lead "
            f"automatically if discover_leads does not return an email, ensuring 100% "
            f"coverage for the daily harvest."
        ),
        agent=hunter,
        expected_output=(
            "A numbered list of all leads found and saved to CRM. "
            "Each entry: Name | Company | Title | Phone | Email | LinkedIn URL | Source."
        )
    )

    enrichment_task = Task(
        description=(
            "Run enrich_leads to find emails and LinkedIn URLs for every lead just discovered.\n"
            "This MUST run after discovery and before the scoreboard report.\n"
            "Call enrich_leads with no arguments (uses default limit of 50).\n"
            "Wait for it to complete and note how many emails were found."
        ),
        agent=hunter,
        expected_output=(
            "Enrichment summary: number of emails found, LinkedIn found, "
            "leads with no website, and leads still missing email."
        )
    )

    scoreboard_task = Task(
        description=(
            "Run get_daily_scoreboard and compile the final Growth Hunter report.\n"
            "You MUST output the report using EXACTLY these section headers and formats:\n\n"
            "### PIPELINE METRICS\n"
            "A markdown table with columns: Metric | Value | Status\n"
            "Rows: Total Leads Today, Leads With Email, Leads With LinkedIn, Total in CRM\n\n"
            "### LEADS BY INDUSTRY\n"
            "A markdown table with columns: Industry | Count | Avg Score\n\n"
            "### TOP PRIORITY LEADS\n"
            "A markdown table with columns: Name | Company | Email | Industry | Why Priority\n"
            "Include medal emojis (🥇 🥈 🥉) in the Name column for top 3.\n\n"
            "### ACTION ITEMS\n"
            "3-5 action items. Each item must use this format:\n"
            "**1. Title**, description of the action\n\n"
            "### SCOREBOARD HEALTH CHECK\n"
            "Progress bar lines using block characters. Each line must include a percentage.\n"
            "Use 🟢 for on-track, 🔴 for behind, 💰 for revenue items.\n"
            "Example: 🟢 Email Coverage ███████░░░ 70% — 14/20 leads have emails\n\n"
            "DO NOT deviate from these section names or table structures. "
            "The email report renderer depends on exact header matching."
        ),
        agent=hunter,
        expected_output=(
            "A structured Growth Hunter report with exactly these five sections in order: "
            "### PIPELINE METRICS (table), ### LEADS BY INDUSTRY (table), "
            "### TOP PRIORITY LEADS (table with medal emojis), "
            "### ACTION ITEMS (numbered bold items), "
            "### SCOREBOARD HEALTH CHECK (progress bar lines with percentages). "
            "All section headers must match exactly as shown."
        )
    )

    return Crew(
        agents=[hunter],
        tasks=[discovery_task, enrichment_task, scoreboard_task],
        process=Process.sequential,
        verbose=False,
        memory=False,
    )


# ── Crew Registry ──────────────────────────────────────────────
# Maps crew type strings (from router.py) to crew builder functions.
# Add new entries here when adding new task types.

def build_voice_polisher_crew(text_to_polish: str) -> Crew:
    """
    Crew for: voice_polishing
    Standalone humanization and voice matching.
    """
    voice_agent = build_boub_ai_voice_agent()
    
    task_polish = Task(
        description=f"""
        Humanize the following text to match Boubacar Barry's voice:
        
        TEXT: {text_to_polish}
        
        1. STRIP AI MARKERS: Use the voice_polisher tool.
        2. ENFORCE HUMANITY: Rewrite sections that sound robotic.
        3. CHANNEL BOUBACAR: Authoritative, direct, diagnosis-first.
        4. NO HEDGING: Remove all qualifiers and filler.
        """,
        expected_output="The final, polished text in Boubacar's authentic voice.",
        agent=voice_agent
    )
    
    return Crew(
        agents=[voice_agent],
        tasks=[task_polish],
        process=Process.sequential,
        verbose=False,
        memory=False
    )


def build_prompt_engineer_crew(user_request: str) -> Crew:
    """
    Crew for: prompt_engineering
    Rewrites any prompt using the 8-step Catalyst Prompt OS algorithm.
    Single-agent, no QA — the multi-output gate in the task IS the self-QA.
    """
    agent = build_prompt_engineer_agent()

    task_rewrite = Task(
        description=f"""
        Rewrite the following prompt using the Catalyst Prompt OS algorithm:

        ORIGINAL PROMPT:
        {user_request}

        Follow ALL 8 steps in sequence:

        STEP 1 — DEFINE OBJECTIVE
        Identify: what exact outcome must this prompt produce? What decision, asset, or action?

        STEP 2 — STEP-BACK THINKING
        Answer internally before rewriting:
        - What are the key principles of a high-quality output for this task?
        - What separates average from exceptional for this specific use case?
        - What common mistakes does this type of prompt usually produce?

        STEP 3 — BEHAVIOR-FIRST ROLE
        Replace any "expert" title (or knowledge-only role) with a behavior-first role:
        "You are a [behavior] who specializes in [domain] explaining this to [audience]."
        Choose behavior from: storyteller, diagnostician, coach, challenger, precision editor,
        translator, strategist, skeptic, systems thinker — whichever fits the task.

        STEP 4 — FEW-SHOT EXAMPLE (if applicable)
        If the prompt targets structured or creative output, add one ideal output example.
        Skip for conversational or open-ended prompts.

        STEP 5 — TASK INSTRUCTIONS
        Rewrite task instructions using action verbs (Analyze, Build, Evaluate, Recommend,
        Compare, Generate, Diagnose). Tie output to real-world impact: revenue, time saved,
        or risk reduced.

        STEP 6 — OUTPUT FORMAT
        Add explicit structure:
        1. Direct Answer
        2. Reasoning (concise, structured)
        3. Alternatives + Trade-offs
        4. Practical Next Action
        Override with tables, JSON, or code blocks when the task requires it.

        STEP 7 — MULTI-OUTPUT + SELECTION GATE
        Add this instruction to the prompt:
        "Generate 2-3 variations. Score each on Clarity, Depth, Usefulness, Actionability (1-5).
        Select the best. Improve it once more before final output."

        STEP 8 — ITERATION GATE
        End the rewritten prompt with:
        "After completing your output, ask yourself: what would make this 10x more useful?
        Refine once before delivering."

        YOUR OUTPUT FORMAT (mandatory, every time):

        SOURCE (first 200 chars):
        [first 200 characters of the original prompt, for reader context]

        WHAT WAS IMPROVED:
        • Role: [what changed — e.g., "expert in marketing → strategist who specializes in B2B GTM"]
        • Step-back thinking: [the 3 principles applied]
        • Output format: [what structure was added]
        • Multi-output gate: added
        • Iteration gate: added
        • Few-shot example: [added / not applicable — reason]
        • Other: [any other meaningful change]

        IMPROVED PROMPT:
        [full rewritten prompt — complete, copy-pasteable, no truncation]
        """,
        expected_output=(
            "Structured response with: ORIGINAL PROMPT summary, WHAT WAS IMPROVED bullets, "
            "and IMPROVED PROMPT as a complete copy-pasteable block."
        ),
        agent=agent
    )

    return Crew(
        agents=[agent],
        tasks=[task_rewrite],
        process=Process.sequential,
        verbose=False,
        memory=False,
    )


def build_news_brief_crew(user_request: str) -> Crew:
    """
    Crew for: news_brief
    Curates and analyses daily news with impact analysis for Catalyst Works.
    Single-agent: research + synthesis in one pass.
    """
    from agents import build_news_brief_agent
    agent = build_news_brief_agent()

    topic_clause = f"\n\nFocus areas requested by user: {user_request}" if user_request.strip() else ""

    task_brief = Task(
        description=f"""
        Produce today's Daily Intelligence Brief for Boubacar Barry / Catalyst Works Consulting.

        MANDATORY COVERAGE — scan and summarise the top stories in each category:

        1. **AI & Automation** — model releases, major product launches, policy moves, funding
        2. **Business & Economics** — macro trends, consulting/services sector, freelance economy
        3. **Solopreneur / Boutique Firm News** — tools, platforms, pricing changes, opportunities
        4. **Africa Tech** — startups, funding, policy, mobile money, edtech, healthtech
        5. **Catalyst Works Watchlist** — anything touching: AI consulting, sales automation,
           CRM tools, lead gen, LinkedIn strategy, content marketing for consultants
        {topic_clause}

        FOR EACH STORY (aim for 3-5 stories per category, pick the most impactful):
        - **Headline** (your own clear, direct headline — not clickbait)
        - **What happened** (2-3 sentences, facts only)
        - **Why it matters to Boubacar** (1-2 sentences — connect to Catalyst Works, agentsHQ, or his clients)
        - **Action item** (if any — "monitor", "reach out", "test this", "nothing now")

        CLOSE WITH:
        - **3 Big Themes of the Day** (cross-cutting patterns across all categories)
        - **One Opportunity** (the single most actionable thing from today's news for Catalyst Works)

        Use Firecrawl and Serper to find today's actual news — do not fabricate stories.
        Date: today.
        """,
        expected_output=(
            "A structured Daily Intelligence Brief with sections for each news category, "
            "3-5 stories per section (headline / what happened / why it matters / action item), "
            "followed by 3 Big Themes and One Opportunity. "
            "Scannable, no filler, direct language."
        ),
        agent=agent
    )

    return Crew(
        agents=[agent],
        tasks=[task_brief],
        process=Process.sequential,
        verbose=False,
        memory=False,
    )


def build_notion_overhaul_crew(user_request: str) -> Crew:
    """
    Crew for: notion_overhaul
    Transforms Notion pages into premium branded dashboards.
    """
    planner = build_planner_agent()
    copywriter = build_copywriter_agent()
    designer = build_notion_visual_architect_agent()
    qa = build_qa_agent()

    task_plan = Task(
        description=f"""
        Analyze the Notion overhaul request and create a visual and structural plan:
        REQUEST: {user_request}

        Plan must include:
        1. Hierarchy of pages and databases
        2. Visual theme (Covers, Icons, Colors - Teal/Orange)
        3. Columnar layout structures for the landing page
        4. Copy requirements for 'leGriot' voice consistency
        """,
        expected_output="A structured aesthetic and structural plan for the Notion hub",
        agent=planner
    )

    task_design = Task(
        description=f"""
        Execute the visual redesign using the Notion Styling Tools:
        1. Apply branded covers and icons to the main hub and core databases.
        2. Structure the landing page using multi-column layouts (add_notion_nav_tool).
        3. Use Callout blocks for high-impact mission statements (add_callout).
        
        Ensure everything matches the Catalyst Works style guide.
        """,
        expected_output="Notion hub visually transformed with branded assets and premium layouts",
        agent=designer,
        context=[task_plan]
    )

    task_content = Task(
        description=f"""
        Inject high-impact 'leGriot' copy into the newly structured layouts.
        Focus on 'Outcome-First Intelligence' and 'Theoretical Constraints'.
        Ensure formatting (bolding, lists) matches the premium feel.
        """,
        expected_output="Premium business copy live in the Notion hub",
        agent=copywriter,
        context=[task_plan, task_design]
    )

    return Crew(
        agents=[planner, designer, copywriter, qa],
        tasks=[task_plan, task_design, task_content],
        process=Process.sequential,
        verbose=False,
        embedder=EMBEDDER_CONFIG
    )


def build_gws_crew(user_request: str) -> Crew:
    """
    Crew for: gws_task
    Single-agent crew for Google Calendar and Gmail interactions.
    """
    from agents import build_gws_agent
    agent = build_gws_agent()

    task = Task(
        description=f"""
        Execute the following Google Workspace request on behalf of Boubacar Barry:

        REQUEST: {user_request}

        Use the available tools (calendar_list_events, calendar_create_event,
        calendar_delete_event, gmail_create_draft, gmail_search) as needed.

        Rules:
        - For calendar events: use ISO 8601 datetime strings (e.g. 2026-04-07T09:00:00)
        - Timezone: America/New_York unless the user specifies otherwise
        - For Gmail drafts: write in Boubacar's voice — direct, no filler
        - Always report exactly what was done (event ID, draft ID, search results count)
        - If an action fails, report the error clearly — never fabricate success
        """,
        expected_output=(
            "A clear confirmation of what was done: event created/listed/deleted with details, "
            "or Gmail draft created with subject/recipient, "
            "or search results returned with count and summaries."
        ),
        agent=agent
    )

    return Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
        memory=False,
    )


def _notion_capture_is_review(user_request: str) -> bool:
    """
    Determine whether the user wants to retrieve/list ideas (True)
    or save a new idea (False). Uses LLM for robustness — no keyword list to maintain.
    Falls back to False (save mode) on any error so we never lose data.
    """
    import os, openai
    try:
        client = openai.OpenAI(
            api_key=os.environ.get("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            default_headers={"HTTP-Referer": "https://agentshq.catalystworks.com", "X-Title": "agentsHQ"},
        )
        resp = client.chat.completions.create(
            model="anthropic/claude-haiku-4.5",
            messages=[
                {"role": "system", "content": (
                    "You classify whether the user wants to RETRIEVE existing ideas or SAVE a new idea.\n"
                    "Reply with exactly one word: retrieve or save"
                )},
                {"role": "user", "content": user_request},
            ],
            temperature=0,
            max_tokens=5,
            timeout=8,
        )
        answer = resp.choices[0].message.content.strip().lower()
        return answer.startswith("retrieve")
    except Exception:
        return False


def build_notion_capture_crew(user_request: str) -> Crew:
    """
    Crew for: notion_capture
    Single-agent crew that saves an idea to or retrieves ideas from the agentsHQ Ideas database.
    Write mode: triggered by "add to my ideas", "save this", "brain dump", etc.
    Review mode: triggered by "review my ideas", "what ideas do I have", etc.
    """
    from agents import build_notion_capture_agent
    agent = build_notion_capture_agent()

    is_review = _notion_capture_is_review(user_request)

    if is_review:
        task_description = (
            f"The user wants to review their saved ideas.\n\n"
            f"REQUEST: {user_request}\n\n"
            f"Steps:\n"
            f"1. Call query_notion_ideas with an empty input to get all recent ideas.\n"
            f"2. Format the results clearly: group by Status (New first), show title, category, and a one-line summary.\n"
            f"3. If there are more than 10 ideas, summarize the oldest ones and show the 10 most recent in full.\n"
            f"4. Flag any ideas with Status='New' that look particularly actionable."
        )
        expected_output = (
            "A clean formatted list of all ideas from the Notion database, "
            "grouped by status, with titles, categories, and summaries. "
            "Actionable 'New' ideas are highlighted."
        )
    else:
        task_description = (
            f"The user wants to save a new idea or note.\n\n"
            f"REQUEST: {user_request}\n\n"
            f"Steps:\n"
            f"1. Extract a short, clear title (5-10 words max) from the request.\n"
            f"2. Use the full request text as the content — do not summarize or truncate.\n"
            f"3. Pick the most fitting category: Tool, Agent, Feature, Business, or Personal.\n"
            f"4. Call create_notion_idea with the title, content, and category.\n"
            f"5. Confirm to the user: what was saved, the title, and that it's in Notion."
        )
        expected_output = (
            "Confirmation that the idea was saved: title, category, and Notion URL. "
            "One sentence confirmation to the user."
        )

    task = Task(
        description=task_description,
        expected_output=expected_output,
        agent=agent,
    )

    return Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
        memory=False,
    )


def build_notion_tasks_crew(user_request: str) -> Crew:
    """
    Crew for: notion_tasks
    Single-agent crew that queries the Notion task database for open/overdue/due-today tasks.
    """
    from agents import build_notion_capture_agent
    from tools import NOTION_TASK_TOOLS
    from datetime import date

    agent = build_notion_capture_agent()
    agent.tools = NOTION_TASK_TOOLS
    agent.role = "Task Manager"
    agent.goal = (
        "Query the Notion task database and return open, overdue, or due-today tasks. "
        "Always filter by due date when the user specifies one."
    )

    today = date.today().isoformat()
    due_filter = today  # default: due on or before today

    task_description = (
        f"The user wants to see their Notion tasks.\n\n"
        f"REQUEST: {user_request}\n\n"
        f"Steps:\n"
        f"1. Call query_notion_tasks with input: {{\"due_on_or_before\": \"{due_filter}\"}} "
        f"to get all open tasks due on or before {due_filter}.\n"
        f"2. Format the results clearly: show task title, status, and due date.\n"
        f"3. Group into: OVERDUE (due before today) and DUE TODAY.\n"
        f"4. If no tasks found, say so clearly."
    )
    expected_output = (
        "A clean formatted list of open tasks from Notion grouped by OVERDUE and DUE TODAY, "
        "with title, status, and due date for each task."
    )

    task = Task(
        description=task_description,
        expected_output=expected_output,
        agent=agent,
    )

    return Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
        memory=False,
    )


def build_crm_query_crew(user_request: str) -> Crew:
    """
    Lightweight read-only crew for CRM questions.
    Calls query_crm + get_daily_scoreboard and returns a plain-text answer.
    Triggered by: "how many leads", "leads contacted", "crm stats", etc.
    """
    from agents import build_hunter_agent
    from tools import crm_query_tool, scoreboard_tool

    agent = build_hunter_agent()
    agent.tools = [crm_query_tool, scoreboard_tool]

    task = Task(
        description=(
            f"The user is asking a question about the CRM. Answer it directly.\n\n"
            f"USER QUESTION: {user_request}\n\n"
            f"Call query_crm to get the full lead breakdown by status, email, industry, etc. "
            f"Then answer the user's specific question clearly and concisely in plain text. "
            f"No preamble, no markdown headers — just a direct answer with the relevant numbers."
        ),
        agent=agent,
        expected_output="A concise plain-text answer to the user's CRM question with the relevant numbers."
    )

    return Crew(agents=[agent], tasks=[task], verbose=False)


def build_crm_outreach_crew(user_request: str) -> Crew:
    """
    Crew for: crm_outreach
    Two-agent sequential crew:
      1. Hunter agent -- reveals missing emails for uncontacted leads
      2. GWS agent -- reads cold outreach templates, creates Gmail drafts, logs interactions

    Triggered by: "outreach", "cold email", "contact leads", "email prospects"
    """
    from agents import build_hunter_agent, build_gws_agent
    from tools import OUTREACH_TOOLS, GWS_TOOLS, crm_log_tool

    hunter = build_hunter_agent()
    gws = build_gws_agent()
    # Give GWS agent CRM log tool so it can log outreach_draft interactions
    gws.tools = GWS_TOOLS + [crm_log_tool]

    # Task 1: get uncontacted leads and reveal any missing emails
    enrich_task = Task(
        description=(
            "GOAL: Prepare a batch of uncontacted leads for outreach.\n\n"
            "STEPS:\n"
            "1. Call get_uncontacted_leads to retrieve leads with status='new' "
            "and no last_contacted_at date. Look at the FIRST 10 leads only.\n"
            "2. For each of those 10 leads that has no email address, call reveal_email "
            "to try Hunter.io then Apollo. Stop trying after 2 attempts per lead.\n"
            "3. Log any newly found emails with log_interaction (type: email_revealed).\n"
            "4. Return ONLY the leads from those 10 who have an email address -- "
            "maximum 10 leads. If more than 10 have emails, return the first 10 only. "
            "Include: id, name, company, title, industry, email.\n\n"
            f"USER REQUEST: {user_request}"
        ),
        agent=hunter,
        expected_output=(
            "A JSON list of leads ready for outreach. Each entry: "
            "id, name, company, title, industry, email. "
            "Also report how many had emails already vs how many were newly revealed."
        )
    )

    # Task 2: draft outreach emails for every ready lead
    draft_task = Task(
        description=(
            "GOAL: Create cold outreach Gmail drafts for the leads passed from the previous task.\n\n"
            "RULES:\n"
            "- LIMIT: Create a maximum of 10 drafts per run. Stop after 10.\n"
            "- CONFIRMED EMAILS ONLY: Only draft for leads where an email address was "
            "explicitly provided by the previous task. NEVER guess, infer, or construct "
            "an email address. If a lead has no confirmed email, skip them entirely.\n"
            "- Account: use boubacar@catalystworks.consulting for ALL outreach drafts.\n"
            "- Template: use the single cold outreach template from the cold outreach skill.\n"
            "- Body: fill in [First Name] with the recipient's actual first name. "
            "No other placeholders. No industry bracket. No size bracket.\n"
            "- Subject line: 'Where is your margin actually going?'\n"
            "- After creating each draft, call log_interaction with "
            "lead_id, type='outreach_draft', content=the subject line.\n"
            "- NEVER send. Only create drafts.\n\n"
            "Report total drafts created and any leads skipped (no confirmed email)."
        ),
        agent=gws,
        expected_output=(
            "Confirmation of drafts created: count, list of names and subject lines. "
            "Count of leads skipped due to missing email. "
            "Confirmation that all outreach attempts were logged in the CRM."
        ),
        context=[enrich_task]
    )

    return Crew(
        agents=[hunter, gws],
        tasks=[enrich_task, draft_task],
        process=Process.sequential,
        verbose=False,
        memory=False,
    )


def build_enrich_leads_crew(_user_request: str) -> Crew:
    """
    Single-agent crew that runs the full enrichment pipeline.
    Calls enrich_leads tool directly -- no discovery, no LLM guessing.
    Triggered by: "enrich leads", "find missing emails", "find phones", etc.
    """
    from agents import build_hunter_agent
    from tools import enrich_leads_tool, scoreboard_tool

    hunter = build_hunter_agent()
    hunter.tools = [enrich_leads_tool, scoreboard_tool]

    task = Task(
        description=(
            "Run the full enrichment pipeline on all leads currently missing "
            "an email address or phone number.\n\n"
            "STEPS:\n"
            "1. Call enrich_leads with no arguments.\n"
            "2. Report back: how many leads processed, how many emails found, "
            "how many phones found, how many still missing both.\n"
            "Do not do anything else. Do not search for new leads."
        ),
        agent=hunter,
        expected_output=(
            "A summary: X leads processed, Y emails found, Z phones found, "
            "N still missing both email and phone."
        )
    )

    return Crew(
        agents=[hunter],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
        memory=False,
    )


def build_mark_outreach_sent_crew(_user_request: str) -> Crew:
    """
    Single-agent crew that marks drafted leads as messaged.
    Called after the user manually sends Gmail drafts.
    Triggered by: "I sent the emails", "mark outreach sent", "emails sent", etc.
    """
    from agents import build_gws_agent
    from tools import crm_mark_sent_tool

    gws = build_gws_agent()
    gws.tools = [crm_mark_sent_tool]

    task = Task(
        description=(
            "The user has just manually sent their cold outreach emails from Gmail. "
            "Call mark_outreach_sent to find all leads that had outreach drafts logged "
            "in the last 48 hours and are still marked as 'new'. "
            "Mark them as messaged and report back exactly who was updated."
        ),
        agent=gws,
        expected_output=(
            "A confirmation message listing every lead marked as messaged, "
            "with their name and email. Include the total count."
        )
    )

    return Crew(
        agents=[gws],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
        memory=False,
    )


def build_content_review_crew(user_request: str) -> Crew:  # noqa: ARG001
    """
    Crew for: content_review
    Pulls all Ready posts from the Notion Content DB, runs the LLM review
    directly (not via a sub-crew to avoid Pydantic kickoff restrictions),
    sends the report to Telegram, sets statuses to 'In Review', and returns
    a simple reporter crew with the result summary.
    """
    import httpx as _httpx
    from skills.forge_cli.notion_client import NotionClient
    from crewai import LLM as _LLM

    CONTENT_DB_ID = os.environ.get("FORGE_CONTENT_DB", "339bcf1a-3029-81d1-8377-dc2f2de13a20")
    NOTION_SECRET = os.environ.get("NOTION_SECRET", "")
    CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
    BOT_TOKEN = os.environ.get(
        "ORCHESTRATOR_TELEGRAM_BOT_TOKEN",
        os.environ.get("TELEGRAM_BOT_TOKEN", ""),
    )

    # ── 1. Fetch Ready posts ───────────────────────────────────────
    notion = NotionClient(secret=NOTION_SECRET)
    try:
        posts = notion.query_database(
            CONTENT_DB_ID,
            filter_obj={"property": "Status", "select": {"equals": "Ready"}},
        )
    except Exception as e:
        posts = []
        logger.error(f"content_review_crew: Notion query failed: {e}")

    if not posts:
        result_text = "No posts with status 'Ready' found in the Content Board. Nothing to review."
        reporter = Agent(
            role="Status Reporter",
            goal="Report system status to the user",
            backstory="You relay pre-computed results verbatim.",
            llm=get_llm("gemini-flash"),
            max_iter=1,
            verbose=False,
        )
        task_none = Task(
            description=f"Report this to the user verbatim: {result_text}",
            expected_output="The status message, as-is.",
            agent=reporter,
        )
        return Crew(agents=[reporter], tasks=[task_none], process=Process.sequential, verbose=False, memory=False)

    # ── 2. Extract post data ───────────────────────────────────────
    def _get_text(prop, key="rich_text"):
        parts = prop.get(key, [])
        return "".join(p.get("plain_text", "") for p in parts) if parts else ""

    def _get_select(prop):
        sel = prop.get("select") or {}
        return sel.get("name", "")

    post_data = []
    for page in posts:
        props = page.get("properties", {})
        title_parts = props.get("Title", {}).get("title", [])
        title = "".join(p.get("plain_text", "") for p in title_parts)
        content = _get_text(props.get("Content", {}))
        platform = _get_select(props.get("Platform", {}))
        post_data.append({
            "id": page["id"],
            "title": title,
            "content": content,
            "platform": platform,
        })

    posts_block = "\n\n".join(
        f"POST {i+1} [{p['platform']}] | {p['title']}\nNOTION_ID: {p['id']}\n---\n{p['content']}"
        for i, p in enumerate(post_data)
    )

    # ── 3. Run the LLM review directly ────────────────────────────
    review_prompt = f"""You are reviewing social media posts for Boubacar Barry, founder of Catalyst Works Consulting.

VOICE RULES (non-negotiable):
- Short declarative sentences. Vary length deliberately.
- Open with a bold claim or question. NEVER "In today's fast-paced world" or any variant.
- One diagnosis per post. One constraint, one insight.
- No em-dashes. No leverage, synergy, tapestry, delve, complexities.
- No hedging: it might be, one could argue, it depends.
- No generic CTA: follow me for more, drop a comment below.
- Audience: SMB owner-operators. Direct. Earned. Specific.
- If it reads like generic AI content, it fails.

FOR EACH POST produce exactly:

POST [N]: [Title]
NOTION_ID: [id]
PLATFORM: [platform]
HOOK: [1-10] | [verdict]
BODY: [1-10] | [verdict]
CTA: [1-10] | [verdict]
VOICE: [1-10] | [verdict]
RESULT: PASS or NEEDS REWRITE
FINAL TEXT:
[original if PASS; full rewrite if NEEDS REWRITE]
---

POSTS:

{posts_block}

End with:
SUMMARY: N passed, M rewritten.
Reply "push content to drive" when you are happy with these."""

    review_text = "Review failed — LLM call error."
    try:
        llm = _LLM(
            model="openai/anthropic/claude-sonnet-4-5",
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ.get("OPENROUTER_API_KEY", ""),
            temperature=0.3,
        )
        review_text = str(llm.call([{"role": "user", "content": review_prompt}]))
    except Exception as e:
        logger.error(f"content_review LLM call failed: {e}")
        review_text = f"Review LLM call failed: {e}"

    # ── 4. Update Notion + send Telegram ──────────────────────────
    for p in post_data:
        try:
            notion.update_page(p["id"], {"Status": {"select": {"name": "In Review"}}})
        except Exception as e:
            logger.error(f"content_review Notion update failed for {p['id']}: {e}")

    header = (
        f"CONTENT REVIEW — {len(post_data)} posts reviewed\n"
        f"Reply 'push content to drive' when you are happy.\n\n"
    )
    full_report = header + review_text
    if BOT_TOKEN and CHAT_ID:
        chunks = [full_report[i:i+4000] for i in range(0, len(full_report), 4000)]
        for chunk in chunks:
            try:
                _httpx.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={"chat_id": str(CHAT_ID), "text": chunk},
                    timeout=15,
                )
            except Exception as e:
                logger.error(f"content_review Telegram send failed: {e}")

    # ── 5. Return simple reporter crew ────────────────────────────
    summary = (
        f"Content review complete. {len(post_data)} posts reviewed and set to 'In Review' in Notion. "
        f"Full scored report sent to Telegram. "
        f"Reply 'push content to drive' when approved."
    )
    reporter = Agent(
        role="Status Reporter",
        goal="Report the outcome of a system operation",
        backstory="You relay pre-computed system results to the user verbatim.",
        llm=get_llm("gemini-flash"),
        max_iter=1,
        verbose=False,
    )
    task_report = Task(
        description=f"Report this system result to the user verbatim:\n\n{summary}",
        expected_output="The system result message, reported as-is.",
        agent=reporter,
    )
    return Crew(agents=[reporter], tasks=[task_report], process=Process.sequential, verbose=False, memory=False)


def build_content_push_to_drive_crew(user_request: str) -> Crew:  # noqa: ARG001
    """
    Crew for: content_push_to_drive
    Takes all 'In Review' posts from the Notion Content DB, creates a Google Doc
    for each one in the 04_Content Drive folder, updates the Drive Link in
    Notion, and sets status to 'Published Ready'.
    """
    from skills.forge_cli.notion_client import NotionClient
    from tools import _gws_request

    CONTENT_DB_ID = os.environ.get("FORGE_CONTENT_DB", "339bcf1a-3029-81d1-8377-dc2f2de13a20")
    CONTENT_FOLDER_ID = os.environ.get("CONTENT_DRIVE_FOLDER_ID", "1lS7VT4aMfo7eQc-zVdOfFfvWvevytwNs")
    NOTION_SECRET = os.environ.get("NOTION_SECRET", "")

    notion = NotionClient(secret=NOTION_SECRET)
    try:
        posts = notion.query_database(
            CONTENT_DB_ID,
            filter_obj={"property": "Status", "select": {"equals": "In Review"}},
        )
    except Exception as e:
        posts = []
        logger.error(f"content_push_to_drive: Notion query failed: {e}")

    results = []
    errors = []
    for page in posts:
        props = page.get("properties", {})
        title_parts = props.get("Title", {}).get("title", [])
        title = "".join(p.get("plain_text", "") for p in title_parts) or "Untitled"
        notion_id = page["id"]
        try:
            data = _gws_request(
                "post",
                "https://www.googleapis.com/drive/v3/files?fields=id,webViewLink",
                json={
                    "name": title,
                    "mimeType": "application/vnd.google-apps.document",
                    "parents": [CONTENT_FOLDER_ID],
                },
            )
            file_id = data.get("id", "")
            web_link = data.get(
                "webViewLink", f"https://docs.google.com/document/d/{file_id}/edit"
            )
            notion.update_page(notion_id, {
                "Drive Link": {"url": web_link},
                "Status": {"select": {"name": "Published Ready"}},
            })
            results.append(f"OK: {title[:50]} -> {web_link}")
        except Exception as e:
            errors.append(notion_id)
            results.append(f"ERR: {title[:50]} -> {e}")
            logger.error(f"content_push_to_drive failed for {notion_id}: {e}")

    result_text = (
        f"Drive push complete. {len(posts) - len(errors)}/{len(posts)} docs created.\n\n"
        + "\n".join(results)
    ) if posts else (
        "No posts with status 'In Review' found. Run content review first, then approve."
    )

    reporter = Agent(
        role="Status Reporter",
        goal="Report the outcome of a system operation",
        backstory="You relay pre-computed system results to the user verbatim.",
        llm=get_llm("gemini-flash"),
        max_iter=1,
        verbose=False,
    )
    task_report = Task(
        description=f"Report this system result to the user verbatim:\n\n{result_text}",
        expected_output="The system result message, reported as-is.",
        agent=reporter,
    )
    return Crew(
        agents=[reporter],
        tasks=[task_report],
        process=Process.sequential,
        verbose=False,
        memory=False,
    )


def build_content_board_fetch_crew(user_request: str) -> Crew:
    """
    Crew for: content_board_fetch
    Reads posts from the Notion Content Board filtered by status detected from the request.
    Supports: Queued, Ready, Draft, Idea, In Review, Needs rework, Posted, Archived.
    Read-only. No status changes. No LLM review pass.
    """
    from skills.forge_cli.notion_client import NotionClient

    CONTENT_DB_ID = os.environ.get("FORGE_CONTENT_DB", "339bcf1a-3029-81d1-8377-dc2f2de13a20")
    NOTION_SECRET = os.environ.get("NOTION_SECRET", "")

    # Detect which status to fetch from the user request
    msg = user_request.lower()
    STATUS_MAP = {
        "Idea":         ["idea", "ideas", "brainstorm"],
        "Draft":        ["draft", "drafts"],
        "Queued":       ["queue", "queued"],
        "Ready":        ["ready"],
        "In Review":    ["in review", "review", "reviewing"],
        "Needs rework": ["needs rework", "rework", "needs work"],
        "Posted":       ["posted", "published", "live"],
        "Archived":     ["archived", "archive"],
    }
    target_status = "Queued"  # default
    for status, keywords in STATUS_MAP.items():
        if any(kw in msg for kw in keywords):
            target_status = status
            break

    notion = NotionClient(secret=NOTION_SECRET)
    try:
        posts = notion.query_database(
            CONTENT_DB_ID,
            filter_obj={"property": "Status", "select": {"equals": target_status}},
        )
    except Exception as e:
        posts = []
        logger.error(f"content_board_fetch: Notion query failed: {e}")

    def _get_text(prop, key="rich_text"):
        parts = prop.get(key, [])
        return "".join(p.get("plain_text", "") for p in parts) if parts else ""

    def _get_select(prop):
        sel = prop.get("select") or {}
        return sel.get("name", "")

    post_data = []
    for page in (posts or [])[:10]:
        props = page.get("properties", {})
        title_parts = props.get("Title", {}).get("title", [])
        title = "".join(p.get("plain_text", "") for p in title_parts)
        content = _get_text(props.get("Content", {}))
        platform = _get_select(props.get("Platform", {}))
        arc = _get_select(props.get("Arc", {}))
        post_data.append({
            "title": title,
            "platform": platform,
            "arc": arc,
            "content": content,
        })

    if not post_data:
        result_text = f"No posts with status '{target_status}' found in the Content Board."
    else:
        lines = [f"{target_status.upper()} POSTS ({len(post_data)} shown, up to 10)\n"]
        for i, p in enumerate(post_data, 1):
            meta = f"[{p['platform']}]" + (f" | Arc: {p['arc']}" if p["arc"] else "")
            body = p["content"][:400] + ("..." if len(p["content"]) > 400 else "")
            lines.append(f"POST {i} {meta}\n{p['title']}\n---\n{body}\n")
        result_text = "\n".join(lines)

    reporter = Agent(
        role="Content Board Reporter",
        goal="Return posts from the Notion Content Board",
        backstory="You relay pre-fetched Notion content verbatim. No edits, no opinions.",
        llm=get_llm("gemini-flash"),
        max_iter=1,
        verbose=False,
    )
    task_report = Task(
        description=f"Report this content to the user verbatim:\n\n{result_text}",
        expected_output="The list of posts, as-is.",
        agent=reporter,
    )
    return Crew(
        agents=[reporter],
        tasks=[task_report],
        process=Process.sequential,
        verbose=False,
        memory=False,
    )


def build_design_review_crew(user_request: str) -> Crew:
    """
    Crew for: design_review
    Reviews and enhances an existing visual artifact against the Catalyst Works
    styleguide (branded output) or the most appropriate awesome-design-md reference.

    Pipeline: design_agent (review + brief) -> web_builder (apply fixes + save)

    Trigger phrases: "review this design", "enhance this design",
    "design review", "make this look better", "improve the design"
    """
    design_agent = build_design_agent()
    web_builder = build_web_builder_agent()

    design_ctx = DesignContextLoader.load("design_review")

    task_review = Task(
        description=f"""
        Review the design of the artifact described or provided in this request.

        REQUEST: {user_request}

        {design_ctx if design_ctx else "(Load styleguide_master.md from docs/styleguides/ for Catalyst Works context)"}

        STEP 1 - Identify the artifact:
        Extract the HTML content or file path from the request.
        If no artifact is provided, state: "No artifact provided - cannot review."
        and stop.

        STEP 2 - Identify the brand context:
        Is this Catalyst Works branded output? Apply styleguide.
        Is this non-branded? Load docs/design-references/INDEX.md and identify
        which reference best fits, or load an existing design_decision.md.

        STEP 3 - Produce a numbered review:
        For each issue found, provide:
        [N]. ISSUE: [what is wrong]
            FIX: [exact value or instruction to apply]
            BEFORE: [what it currently is]
            AFTER: [what it should be]

        Minimum 5 issues. Maximum 20. Be specific. Vague feedback is not acceptable.
        Give exact pixel values, hex codes, and font names.

        STEP 4 - Rate the current design:
        DESIGN SCORE: [1-10]
        BIGGEST WIN: [the single change that will have the most impact]
        """,
        expected_output="Numbered design review with specific fixes, design score, and biggest win",
        agent=design_agent,
    )

    task_apply = Task(
        description=f"""
        Apply every fix from the design review to the artifact.

        REQUEST: {user_request}

        Apply each numbered fix from the review. Do not skip any.
        After applying all fixes, run the builder checklist:
        - [ ] Clay (#B47C57) appears somewhere if Catalyst Works branded
        - [ ] No red tones anywhere
        - [ ] Heading font is Plus Jakarta Sans (not Inter for headlines)
        - [ ] Specific claim in first visible element (not category description)
        - [ ] No purple gradients, no three rounded boxes in a row

        OUTPUT FORMAT:
        FIXES APPLIED: [numbered list matching the review]
        DESIGN QA: PASSED or DESIGN QA: REVISED - [what was adjusted]
        DELIVERABLE:
        [The complete updated HTML file - always included]

        Save using save_output tool.
        """,
        expected_output="Complete revised HTML with fixes applied and QA report, saved to outputs",
        agent=web_builder,
        context=[task_review],
    )

    return Crew(
        agents=[design_agent, web_builder],
        tasks=[task_review, task_apply],
        process=Process.sequential,
        verbose=False,
    )


CREW_REGISTRY = {
    "website_crew":        build_website_crew,
    "app_crew":            build_app_crew,
    "research_crew":       build_research_crew,
    "consulting_crew":     build_consulting_crew,
    "social_crew":         build_social_crew,
    "linkedin_x_crew":     build_linkedin_x_crew,
    "code_crew":           build_code_crew,
    "notion_overhaul":     build_notion_overhaul_crew,
    "writing_crew":        build_writing_crew,
    "agent_creator_crew":  build_agent_creator_crew,
    "voice_polisher_crew":    build_voice_polisher_crew,
    "hunter_crew":            build_hunter_crew,
    "prompt_engineer_crew":   build_prompt_engineer_crew,
    "3d_website_crew":        build_3d_website_crew,
    "news_brief_crew":        build_news_brief_crew,
    "gws_crew":               build_gws_crew,
    "notion_capture_crew":    build_notion_capture_crew,
    "notion_tasks_crew":      build_notion_tasks_crew,
    "crm_query_crew":         build_crm_query_crew,
    "crm_outreach_crew":      build_crm_outreach_crew,
    "mark_outreach_sent_crew": build_mark_outreach_sent_crew,
    "enrich_leads_crew":       build_enrich_leads_crew,
    "forge_kpi_crew":          build_forge_kpi_crew,
    "content_review_crew":        build_content_review_crew,
    "content_drive_crew":         build_content_push_to_drive_crew,
    "content_board_fetch_crew":   build_content_board_fetch_crew,
    "doc_routing_crew":           build_doc_routing_crew,
    "design_review_crew":         build_design_review_crew,
    "media_crew":                 build_media_crew,
    "unknown_crew":               build_unknown_crew,
}


def assemble_crew(crew_type: str, user_request: str) -> Crew:
    """
    Main entry point for crew assembly.
    Called by orchestrator.py with the crew_type from the router.
    """
    builder = CREW_REGISTRY.get(crew_type, build_unknown_crew)
    
    if crew_type not in CREW_REGISTRY:
        logger.warning(f"Unknown crew type '{crew_type}' — falling back to unknown_crew")
    
    logger.info(f"Assembling crew: {crew_type} for request: {user_request[:60]}...")
    return builder(user_request)