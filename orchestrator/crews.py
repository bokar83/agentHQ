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


def build_humanization_task(context_tasks: list) -> Task:
    """
    Reusable task for the BouB AI Voice agent to verify and polish 
    the output of any crew.
    """
    voice_agent = build_boub_ai_voice_agent()
    return Task(
        description="""
        As the final authority on voice, review the deliverable produced by the crew.
        
        1. STRIP AI MARKERS: Use the voice_polisher tool to programmatically clean the text.
        2. ENFORCE HUMANITY: Rewrite sections that sound robotic, repetitive, or overly formal.
        3. CHANNEL BOUBACAR: Ensure the tone is direct, opinionated, and diagnosis-first.
        4. NO HEDGING: Remove 'In my opinion', 'It seems', 'I believe'. State facts and insights clearly.
        5. VERIFY RED FLAGS: Check for em-dash abuse and uniform sentence lengths.
        
        The goal is a deliverable that feels like it was written by Boubacar Diallo himself.
        """,
        expected_output="The final, humanized version of the deliverable, free of AI-slop.",
        agent=voice_agent,
        context=context_tasks
    )


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
        context=[task_build]
    )

    task_voice = build_humanization_task([task_qa])

    return Crew(
        agents=[planner, researcher, copywriter, web_builder, qa, task_voice.agent],
        tasks=[task_plan, task_research, task_copy, task_build, task_qa, task_voice],
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

    task_voice = build_humanization_task([task_qa])

    return Crew(
        agents=[planner, researcher, copywriter, qa, task_voice.agent],
        tasks=[task_plan, task_research, task_write, task_qa, task_voice],
        process=Process.sequential,
        verbose=False,
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

    task_voice = build_humanization_task([task_qa])

    return Crew(
        agents=[planner, researcher, consultant, qa, task_voice.agent],
        tasks=[task_plan, task_research, task_consult, task_qa, task_voice],
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

    task_voice = build_humanization_task([task_qa])

    return Crew(
        agents=[planner, griot, qa, task_voice.agent],
        tasks=[task_plan, task_write, task_qa, task_voice],
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
    Mode 3: Hunter Crew for proactive lead gen.
    Finds leads, adds to CRM, and drafts discovery messages.
    """
    hunter = build_hunter_agent()
    voice = build_boub_ai_voice_agent()

    # Task 1: Find and log 5 leads
    hunting_task = Task(
        description=(
            f"GOAL: Find 5 high-quality Utah service SMB leads.\n"
            f"NICHE: Legal, Accounting, Agencies, or Home Services.\n"
            f"ACTION: Use Apollo to find them, then ADD each to the CRM.\n"
            f"INPUT: {user_request}"
        ),
        agent=hunter,
        expected_output="Confirmation of 5 leads added to CRM with IDs."
    )

    # Task 2: Draft personalized Discovery messages
    outreach_task = Task(
        description=(
            "For the 5 leads just added, draft a 'Discovery' message for each.\n"
            "Keep it human, brief, and focused on operational friction.\n"
            "No fluff. No 'I hope this find you well'. Just direct value."
        ),
        agent=hunter,
        expected_output="5 drafted messages, one for each lead."
    )

    # Task 3: Voice Polish (Humanization)
    humanization_task = Task(
        description=(
            "Review the 5 drafted messages. Remove all AI-isms (em-dashes, robotic transitions).\n"
            "Ensure the tone is direct and matches Boubacar's style.\n"
            "Output the final polished messages."
        ),
        agent=voice,
        expected_output="5 final polished, humanized discovery messages.",
        context=[outreach_task]
    )

    return Crew(
        agents=[hunter, voice],
        tasks=[hunting_task, outreach_task, humanization_task],
        process=Process.sequential,
        verbose=False,
        memory=True
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
        Humanize the following text to match Boubacar Diallo's voice:
        
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

        ORIGINAL PROMPT:
        [first 200 characters of the original for reference]

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