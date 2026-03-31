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
from crewai import Agent, Task, Crew, Process
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

        CHECK:
        1. Does the website fully deliver what was requested?
        2. Is there any placeholder text or lorem ipsum? (FAIL if yes)
        3. Is the HTML complete? (starts with DOCTYPE, ends with /html)
        4. Are all planned sections present?
        5. Does the design match the business type?
        6. Is it mobile responsive?
        7. Would Boubacar be proud to show this to a client?

        If PASS: Return "QUALITY CHECK: PASSED" + the complete HTML
        If NEEDS WORK: Fix the issues, return "QUALITY CHECK: REVISED" + corrected HTML

        Either way: the final output MUST be the complete HTML file.
        Save the final version using save_output.
        """,
        expected_output="QUALITY CHECK: PASSED or REVISED, followed by the complete HTML file",
        agent=qa,
        context=[task_seo]
    )

    return Crew(
        agents=[planner, researcher, copywriter, web_builder, qa],
        tasks=[task_plan, task_research, task_copy, task_build, task_seo, task_qa],
        process=Process.sequential,
        verbose=True,
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
        Original request: {user_request}
        Fix any issues found. Save final version.
        """,
        expected_output="QUALITY CHECK: PASSED/REVISED + final report",
        agent=qa,
        context=[task_write]
    )

    return Crew(
        agents=[planner, researcher, copywriter, qa],
        tasks=[task_plan, task_research, task_write, task_qa],
        process=Process.sequential,
        verbose=True,
        memory=False,

    )


def build_consulting_crew(user_request: str) -> Crew:
    """
    Crew for: consulting_deliverable
    Creates professional consulting artifacts.
    """
    planner = build_planner_agent()
    researcher = build_researcher_agent()
    consultant = build_consulting_agent()
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
        Review the consulting deliverable for quality, completeness,
        and professional standards. Original: {user_request}
        """,
        expected_output="QUALITY CHECK: PASSED/REVISED + final deliverable",
        agent=qa,
        context=[task_consult]
    )

    return Crew(
        agents=[planner, researcher, consultant, qa],
        tasks=[task_plan, task_research, task_consult, task_qa],
        process=Process.sequential,
        verbose=True,
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
        Review the social content. Does it sound like Boubacar?
        Is it specific enough? Does it teach or provoke thought?
        Original: {user_request}
        """,
        expected_output="QUALITY CHECK: PASSED/REVISED + final content",
        agent=qa,
        context=[task_write]
    )

    return Crew(
        agents=[planner, griot, qa],
        tasks=[task_plan, task_write, task_qa],
        process=Process.sequential,
        verbose=True,
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
        Review the code for correctness, completeness, and quality.
        Original: {user_request}
        Check: does it work? Are edge cases handled? Is it readable?
        """,
        expected_output="QUALITY CHECK: PASSED/REVISED + final code",
        agent=qa,
        context=[task_code]
    )

    return Crew(
        agents=[planner, coder, qa],
        tasks=[task_plan, task_code, task_qa],
        process=Process.sequential,
        verbose=True,
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
        Original: {user_request}
        """,
        expected_output="QUALITY CHECK: PASSED/REVISED + final document",
        agent=qa,
        context=[task_write]
    )

    return Crew(
        agents=[planner, copywriter, qa],
        tasks=[task_plan, task_write, task_qa],
        process=Process.sequential,
        verbose=True,
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
        Test and review the application for:
        REQUEST: {user_request}
        Does everything work? Are edge cases handled? Is the UX intuitive?
        """,
        expected_output="QUALITY CHECK: PASSED/REVISED + final application",
        agent=qa,
        context=[task_build]
    )

    return Crew(
        agents=[planner, researcher, app_builder, qa],
        tasks=[task_plan, task_research, task_build, task_qa],
        process=Process.sequential,
        verbose=True,
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
        verbose=True,
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
        verbose=True,
        memory=False,

    )


# ── Crew Registry ──────────────────────────────────────────────
# Maps crew type strings (from router.py) to crew builder functions.
# Add new entries here when adding new task types.

CREW_REGISTRY = {
    "website_crew":       build_website_crew,
    "app_crew":           build_app_crew,
    "research_crew":      build_research_crew,
    "consulting_crew":    build_consulting_crew,
    "social_crew":        build_social_crew,
    "code_crew":          build_code_crew,
    "writing_crew":       build_writing_crew,
    "agent_creator_crew": build_agent_creator_crew,
    "unknown_crew":       build_unknown_crew,
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