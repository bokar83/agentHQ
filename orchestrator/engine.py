import os
import threading
import logging
from datetime import datetime
from typing import Optional

from constants import MEMORY_GATED_TASK_TYPES

logger = logging.getLogger("agentsHQ.engine")

def run_orchestrator(task_request: str, from_number: str = "unknown", session_key: str = "default") -> dict:
    """
    Main orchestration function.
    """
    start_time = datetime.now()

    # Step 1: Load recent conversation history for this session
    today = start_time.strftime("%B %d, %Y")
    enriched_task = f"[Today's date: {today}. All research, recommendations, and references should reflect the current state as of {today}.]\n\n{task_request}"
    try:
        from memory import get_conversation_history
        history = get_conversation_history(session_key, limit=6)
        if history:
            history_text = "\n".join(
                f"[{h['role'].upper()}]: {h['content'][:800]}"
                for h in history
            )
            enriched_task = (
                f"--- CONVERSATION HISTORY (most recent first) ---\n"
                f"{history_text}\n"
                f"--- END HISTORY ---\n\n"
                f"CURRENT REQUEST: {task_request}"
            )
            logger.info(f"Injected {len(history)} history entries for session '{session_key}'")
    except Exception as e:
        logger.warning(f"History injection failed (non-fatal): {e}")

    # Step 2: Route
    from router import classify_task, get_crew_type
    classification = classify_task(task_request)
    task_type = classification.get("task_type", "unknown")
    is_unknown = classification.get("is_unknown", False)

    logger.info(f"Task classified as '{task_type}' (confidence: {classification.get('confidence', 0)})")

    # Step 0b: Pre-task memory recall
    if (
        os.environ.get("MEMORY_LEARNING_ENABLED", "false").lower() == "true"
        and task_type in MEMORY_GATED_TASK_TYPES
    ):
        try:
            from memory import query_memory
            memory_lines = []

            past_work = query_memory(task_request, top_k=3)
            if past_work:
                memory_lines.append("--- RELEVANT PAST WORK ---")
                for pw in past_work:
                    memory_lines.append(
                        f"- [{pw.get('task_type','?')}] {pw.get('summary','')[:200]} (date: {pw.get('date','?')})"
                    )

            past_lessons = query_memory(task_request, top_k=5, collection="agentshq_learnings")
            positive = [l for l in past_lessons if l.get("lesson_type") == "positive"]
            negative = [l for l in past_lessons if l.get("lesson_type") == "negative"]
            if positive:
                memory_lines.append("--- WHAT WORKED WELL FOR THIS TASK TYPE ---")
                for l in positive:
                    memory_lines.append(f"- {l.get('extracted_pattern','')[:200]}")
            if negative:
                memory_lines.append("--- WHAT TO AVOID FOR THIS TASK TYPE ---")
                for l in negative:
                    memory_lines.append(f"- {l.get('extracted_pattern','')[:200]}")

            if memory_lines:
                memory_block = "\n".join(memory_lines) + "\n--- END MEMORY ---\n\n"
                combined = memory_block + enriched_task
                if len(combined) > 6000:
                    allowed = max(0, 6000 - len(enriched_task))
                    memory_block = memory_block[:allowed]
                enriched_task = memory_block + enriched_task
                logger.info(f"Memory recall: {len(past_work)} past tasks + {len(past_lessons)} lessons injected for {task_type}")
        except Exception as e:
            logger.warning(f"Memory recall failed (non-fatal): {e}")

    # Step 3: Direct dispatch for crm_outreach
    if task_type == "crm_outreach":
        try:
            from skills.outreach.outreach_tool import run_outreach
            contact_all = "contact all" in task_request.lower() or "all leads" in task_request.lower()
            outreach_result = run_outreach(contact_all=contact_all)
            drafted = outreach_result.get("drafted", 0)
            skipped = outreach_result.get("skipped", 0)
            results = outreach_result.get("results", [])
            error = outreach_result.get("error")

            if error:
                deliverable = f"Outreach failed: {error}"
            elif drafted == 0:
                deliverable = (
                    "No drafts created. Either no leads have confirmed emails yet, "
                    "or all eligible leads have already been contacted."
                )
            else:
                lines = [f"Cold outreach drafts created in boubacar@catalystworks.consulting ({drafted} drafts):\n"]
                for r in results:
                    if r.get("status") == "drafted":
                        lines.append(f"- {r['name']} | {r['company']} | {r['email']} | {r['subject']}")
                if skipped:
                    lines.append(f"\n{skipped} lead(s) failed (Gmail API error).")
                deliverable = "\n".join(lines)

            return {
                "success": True,
                "task_type": task_type,
                "deliverable": deliverable,
                "execution_time": (datetime.now() - start_time).total_seconds(),
            }
        except Exception as e:
            logger.error(f"crm_outreach direct dispatch failed: {e}")
            return {"success": False, "task_type": task_type, "deliverable": f"Outreach error: {e}", "execution_time": 0}

    # Step 3a: Direct dispatch for research_report: bypass CrewAI entirely.
    # CrewAI's max_iter fallback triggers Anthropic's "assistant message prefill"
    # 400 on heavy research prompts. See docs/superpowers/plans/2026-04-20-research-engine-bypass.md.
    if task_type == "research_report":
        try:
            from research_engine import run_research
            research_result = run_research(user_prompt=enriched_task)
            deliverable = research_result.get("answer") or ""
            execution_time = (datetime.now() - start_time).total_seconds()

            if not research_result.get("success"):
                err = research_result.get("error", "unknown")
                logger.error(f"research_engine failed: {err}")
                deliverable = (
                    "Research couldn't complete. Try narrowing the request to one question "
                    f"or one zip code, then ask again. (Diagnostic: {err})"
                )

            try:
                from memory import save_to_memory, save_conversation_turn
                save_to_memory(
                    task_request=task_request,
                    task_type=task_type,
                    result_summary=deliverable[:1000],
                    files_created=[],
                    execution_time=execution_time,
                    from_number=from_number,
                )
                save_conversation_turn(session_key, "user", task_request)
                save_conversation_turn(session_key, "assistant", deliverable[:1000])
            except Exception as mem_err:
                logger.warning(f"Memory save failed (non-fatal): {mem_err}")

            summary = _build_summary(task_type, deliverable, [], execution_time)
            return {
                "success": True,
                "result": summary,
                "task_type": task_type,
                "files_created": [],
                "execution_time": execution_time,
                "title": task_request[:80].strip(),
                "deliverable": deliverable,
            }
        except Exception as e:
            logger.error(f"research_engine dispatch failed, falling back to CrewAI: {e}", exc_info=True)
            # fall through to CrewAI crew below

    # Step 3: Assemble crew
    from crews import assemble_crew
    crew_type = get_crew_type(task_type) or "unknown_crew"
    if is_unknown:
        crew_type = "unknown_crew"

    crew = assemble_crew(crew_type, enriched_task)

    # Step 4: Execute
    logger.info(f"Kicking off crew: {crew_type}")
    result = crew.kickoff()
    result_str = result.raw if hasattr(result, 'raw') else str(result)
    
    try:
        from skills.boub_voice_mastery.voice_polisher import polish_voice
        result_str = polish_voice(result_str)
    except Exception:
        pass

    # Extract deliverable
    lower = result_str.lower()
    idx = lower.find("deliverable:")
    deliverable = result_str[idx + len("deliverable:"):].strip() if idx != -1 else result_str.strip()
    title = task_request[:80].strip()

    end_time = datetime.now()
    execution_time = (end_time - start_time).total_seconds()
    
    # Track files
    files_created = []
    output_dir = os.environ.get("AGENTS_OUTPUT_DIR", "/app/outputs")
    if os.path.exists(output_dir):
        all_files = os.listdir(output_dir)
        recent_files = [
            f for f in all_files
            if os.path.getmtime(os.path.join(output_dir, f)) >= start_time.timestamp()
        ]
        files_created = recent_files
    
    # Step 5: Save to memory
    try:
        from memory import save_to_memory, save_conversation_turn
        result_summary = result_str[:1000] if len(result_str) > 1000 else result_str
        save_to_memory(
            task_request=task_request,
            task_type=task_type,
            result_summary=result_summary,
            files_created=files_created,
            execution_time=execution_time,
            from_number=from_number
        )
        save_conversation_turn(session_key, "user", task_request)
        save_conversation_turn(session_key, "assistant", result_summary)
    except Exception as e:
        logger.warning(f"Memory save failed (non-fatal): {e}")

    # Step 6: Sync artifact to Notion
    try:
        from memory import sync_artifact_to_notion
        threading.Thread(
            target=sync_artifact_to_notion,
            args=(task_request, task_type, result_summary, files_created, execution_time, session_key),
            daemon=True
        ).start()
    except Exception:
        pass

    summary = _build_summary(task_type, result_str, files_created, execution_time)
    _save_overflow_if_needed(session_key, result_str, task_type)

    return {
        "success": True,
        "result": summary,
        "task_type": task_type,
        "files_created": files_created,
        "execution_time": execution_time,
        "title": title,
        "deliverable": deliverable,
    }

def run_team_orchestrator(subtasks: list, original_request: str, from_number: str = "unknown") -> dict:
    """
    Run multiple crews in parallel and synthesize results.
    """
    from crews import run_parallel_team, build_team_synthesis_crew

    start_time = datetime.now()
    teammate_results = run_parallel_team(subtasks)

    successful = [r for r in teammate_results if r["success"]]
    failed     = [r for r in teammate_results if not r["success"]]

    if failed:
        logger.warning(f"[agent-team] {len(failed)} teammate(s) failed")

    if not successful:
        raise RuntimeError("All teammates failed.")

    synthesis_crew = build_team_synthesis_crew(original_request, successful)
    final_result   = synthesis_crew.kickoff()
    result_str     = final_result.raw if hasattr(final_result, 'raw') else str(final_result)

    execution_time = (datetime.now() - start_time).total_seconds()
    
    files_created = []
    output_dir = os.environ.get("AGENTS_OUTPUT_DIR", "/app/outputs")
    if os.path.exists(output_dir):
        files_created = [
            f for f in os.listdir(output_dir)
            if os.path.getmtime(os.path.join(output_dir, f)) >= start_time.timestamp()
        ]

    try:
        from memory import save_to_memory
        save_to_memory(
            task_request=original_request,
            task_type="agent_team",
            result_summary=result_str[:1000],
            files_created=files_created,
            execution_time=execution_time,
            from_number=from_number
        )
    except Exception as e:
        logger.warning(f"Memory save failed: {e}")

    summary = _build_summary("agent_team", result_str, files_created, execution_time)

    return {
        "success": True,
        "result": summary,
        "full_output": result_str,
        "task_type": "agent_team",
        "teammate_count": len(subtasks),
        "teammates_succeeded": len(successful),
        "teammates_failed": len(failed),
        "files_created": files_created,
        "execution_time": execution_time,
    }

def _build_summary(task_type: str, full_output: str, files_created: list, execution_time: float) -> str:
    type_labels = {
        "agent_team": "Team task complete",
        "website_build": "Website built",
        "app_build": "App built",
        "research_report": "Research complete",
        "consulting_deliverable": "Consulting deliverable ready",
        "social_content": "Social content created",
        "linkedin_x_campaign": "LinkedIn/X campaign ready",
        "code_task": "Code task complete",
        "general_writing": "Document ready",
        "agent_creation": "Agent proposal submitted",
        "gws_task": "Google Workspace task complete",
        "design_review": "Design review complete",
        "unknown": "Task complete",
    }

    label = type_labels.get(task_type, "Task complete")
    lines = [f"--- {label} ---", f"Time: {execution_time:.0f}s"]
    if files_created:
        lines.append(f"Files saved: {', '.join(files_created)}")
    lines.append("")

    MAX_CONTENT = 3700
    if full_output and len(full_output) > 50:
        content = full_output.strip()
        if len(content) > MAX_CONTENT:
            content = content[:MAX_CONTENT] + "\n\n[reply 'more' to see the rest]"
        lines.append(content)
    else:
        lines.append("[No output content returned by agents]")

    return "\n".join(lines)

def _save_overflow_if_needed(session_key: str, full_output: str, task_type: str) -> None:
    MAX_CONTENT = 3700
    if full_output and len(full_output.strip()) > MAX_CONTENT:
        try:
            from memory import save_overflow
            save_overflow(session_key, full_output.strip(), MAX_CONTENT, task_type)
        except Exception as e:
            logger.warning(f"Overflow save failed: {e}")
