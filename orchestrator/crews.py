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
    get_llm,
)

logger = logging.getLogger(__name__)


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
        - Use the design direction from the plan
        - Professional, polished appearance
        - Clear visual hierarchy
        - Accessible color contrast ratios

        OUTPUT:
        - The COMPLETE HTML file. Start with <!DOCTYPE html>. End with </html>.
        - Do NOT truncate. Do NOT summarize. The full file.
        - Save using the save_output tool with an appropriate filename.
        """,
        expected_output="A complete HTML file starting with <!DOCTYPE html> and ending with </html>, saved to outputs",
        agent=web_builder,
        context=[task_plan, task_research, task_copy]
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
        agents=[planner, researcher, copywriter, web_builder, qa],
        tasks=[task_plan, task_research, task_copy, task_build, task_seo, task_qa],
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

        OUTPUT FILES (save to site/ directory):
        - site/app/page.tsx
        - site/components/ScrollCanvas.tsx
        - site/app/globals.css (Tailwind base + dark custom scrollbar)
        - site/package.json (Next.js 14, Tailwind, Framer Motion)
        - site/README.md (npm install && npm run dev, where to drop frames, Vercel deploy)
        """,
        expected_output="Complete Next.js project files saved to site/ directory",
        agent=web_builder_3d,
        context=[task_plan, task_intelligence, task_asset_prompts]
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
        agents=[planner, intelligence, asset_prompter, web_builder_3d, seo_auditor, qa],
        tasks=[task_plan, task_intelligence, task_competitive_report, task_asset_prompts, task_3d_build, task_seo, task_qa],
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

        task_consult = Task(
            description=f"""
            Create the consulting deliverable for:
            REQUEST: {user_request}

            Apply Theory of Constraints thinking where relevant.
            Be analytically rigorous. Be direct. Avoid filler.
            Every recommendation must be specific and implementable.
            Save using save_output.
            """,
            expected_output="Complete consulting deliverable saved to outputs",
            agent=consultant,
            context=[task_plan, task_research]
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
            agents=[planner, researcher, consultant, qa],
            tasks=[task_plan, task_research, task_consult, task_qa],
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

    task_build = Task(
        description=f"""
        Build the complete web application for:
        REQUEST: {user_request}
        All functionality working. Clean UX. Handles edge cases.
        Save using save_output.
        """,
        expected_output="Complete working web application saved to outputs",
        agent=app_builder,
        context=[task_plan, task_research]
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
        agents=[planner, researcher, app_builder, qa],
        tasks=[task_plan, task_research, task_build, task_qa],
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


def build_unknown_crew(user_request: str) -> Crew:
    """
    Fallback crew for unknown task types.
    Either attempts the task or escalates with a new agent proposal.
    """
    orchestrator = build_orchestrator_agent()
    agent_creator = build_agent_creator_agent()

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


def build_hierarchical_crew(user_request: str, specialist_agents: list) -> Crew:
    """
    Mode 2: Hierarchical crew where a manager LLM (Claude Opus) coordinates
    agents dynamically. Use when agents need to inform each other or debate findings.

    specialist_agents: list of pre-built Agent objects
    """
    from agents import select_llm

    tasks = [
        Task(
            description=(
                f"Work on this request as directed by the team lead: {user_request}\n"
                f"Your role: {agent.role}\n"
                f"Apply your expertise and report findings clearly."
            ),
            agent=agent,
            expected_output=f"Specialist output from {agent.role}."
        )
        for agent in specialist_agents
    ]

    return Crew(
        agents=specialist_agents,
        tasks=tasks,
        process=Process.hierarchical,
        manager_llm=select_llm("orchestrator", "complex"),
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
            f"GOAL: Find 20 high-quality Utah SMB leads.\n"
            f"INDUSTRIES: Legal, Accounting, Marketing Agency, HVAC, Plumbing, Roofing.\n"
            f"LOCATIONS: Salt Lake City, Provo, Orem, Lehi, Murray, Sandy.\n"
            f"TITLES: Owner, Founder, CEO, President, Managing Partner.\n"
            f"ACTION: Call discover_leads with the user's query override if provided. "
            f"For every lead returned, call add_lead to save it to the CRM. "
            f"Collect phone, email, LinkedIn URL, company, and title for each lead.\n"
            f"USER REQUEST: {user_request}\n\n"
            f"IMPORTANT: Do NOT auto-reveal Apollo emails. "
            f"Hunter.io enrichment runs automatically inside discover_leads — that is fine. "
            f"Only use reveal_email if Boubacar explicitly names a specific person."
        ),
        agent=hunter,
        expected_output=(
            "A numbered list of all leads found and saved to CRM. "
            "Each entry: Name | Company | Title | Phone | Email | LinkedIn URL | Source."
        )
    )

    scoreboard_task = Task(
        description=(
            "Run get_daily_scoreboard and report today's stats to Boubacar.\n"
            "Format the output clearly with emojis for readability."
        ),
        agent=hunter,
        expected_output=(
            "Daily scoreboard with: leads found, messages sent, replies, "
            "calls booked, leads with email, total leads in CRM."
        )
    )

    return Crew(
        agents=[hunter],
        tasks=[discovery_task, scoreboard_task],
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


CREW_REGISTRY = {
    "website_crew":        build_website_crew,
    "app_crew":            build_app_crew,
    "research_crew":       build_research_crew,
    "consulting_crew":     build_consulting_crew,
    "social_crew":         build_social_crew,
    "code_crew":           build_code_crew,
    "writing_crew":        build_writing_crew,
    "agent_creator_crew":  build_agent_creator_crew,
    "voice_polisher_crew":    build_voice_polisher_crew,
    "hunter_crew":            build_hunter_crew,
    "prompt_engineer_crew":   build_prompt_engineer_crew,
    "3d_website_crew":        build_3d_website_crew,
    "unknown_crew":           build_unknown_crew,
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