"""
===============================================================
agentsHQ ORCHESTRATOR v2.0
===============================================================
Owner: Boubacar Diallo — Catalyst Works Consulting
System: agentsHQ — Self-hosted multi-agent intelligence

This is the main FastAPI service. It receives tasks from:
  - WhatsApp (via WAHA → n8n → this service)
  - Direct HTTP POST (from Cursor, Claude Code, any tool)
  - n8n workflows (automated triggers)

Architecture:
  1. Request arrives at /run
  2. Router classifies the task type
  3. Orchestrator assembles the right crew
  4. Crew executes autonomously
  5. Output is saved, memory is updated, result is returned

See AGENTS.md for the full system architecture.
See CLAUDE.md for development guidelines.
===============================================================
"""

import os
import json
import logging
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# Configure logging
LOG_DIR = os.environ.get("AGENTS_LOG_DIR", "/app/logs")
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(LOG_DIR, "orchestrator.log"), mode="a")
    ]
)
logger = logging.getLogger("agentsHQ")

# ── App setup ──────────────────────────────────────────────────
app = FastAPI(
    title="agentsHQ Orchestrator",
    description="Self-hosted multi-agent intelligence for Catalyst Works Consulting",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request/Response models ────────────────────────────────────
class TaskRequest(BaseModel):
    task: str
    from_number: str = "unknown"
    session_key: str = "default"
    context: Optional[dict] = None  # optional extra context from caller

class TaskResponse(BaseModel):
    success: bool
    result: str
    task_type: str = "unknown"
    files_created: list = []
    execution_time: float = 0.0
    agent_log: list = []

class TeamTaskRequest(BaseModel):
    subtasks: list           # [{"crew_type": str, "task": str, "label": str}]
    original_request: str
    from_number: str = "unknown"
    session_key: str = "default"

class StatusResponse(BaseModel):
    status: str
    service: str
    version: str
    task_types: list
    agents: list
    uptime_seconds: float

# Track service start time
_start_time = time.time()


# ══════════════════════════════════════════════════════════════
# CORE ORCHESTRATION LOGIC
# ══════════════════════════════════════════════════════════════

def run_orchestrator(task_request: str, from_number: str = "unknown") -> dict:
    """
    Main orchestration function.
    
    1. Route: classify the task type
    2. Assemble: build the right crew
    3. Execute: run the crew autonomously
    4. Save: store output to memory
    5. Return: structured result for the caller
    """
    start_time = datetime.now()
    
    # Step 1: Route
    from router import classify_task, get_crew_type, TASK_TYPES
    classification = classify_task(task_request)
    task_type = classification.get("task_type", "unknown")
    is_unknown = classification.get("is_unknown", False)
    
    logger.info(f"Task classified as '{task_type}' (confidence: {classification.get('confidence', 0)})")
    
    # Step 2: Assemble crew
    from crews import assemble_crew
    
    if is_unknown:
        crew_type = "unknown_crew"
    else:
        crew_type = get_crew_type(task_type) or "unknown_crew"
    
    crew = assemble_crew(crew_type, task_request)
    
    # Step 3: Execute
    logger.info(f"Kicking off crew: {crew_type}")
    result = crew.kickoff()
    result_str = result.raw if hasattr(result, 'raw') else str(result)

    end_time = datetime.now()
    execution_time = (end_time - start_time).total_seconds()
    
    # Step 4: Collect files created
    files_created = []
    output_dir = os.environ.get("AGENTS_OUTPUT_DIR", "/app/outputs")
    if os.path.exists(output_dir):
        all_files = os.listdir(output_dir)
        # Get files created in this execution window
        recent_files = [
            f for f in all_files
            if os.path.getmtime(os.path.join(output_dir, f)) >= start_time.timestamp()
        ]
        files_created = recent_files
    
    # Step 5: Save to memory
    try:
        from memory import save_to_memory
        result_summary = result_str[:1000] if len(result_str) > 1000 else result_str
        save_to_memory(
            task_request=task_request,
            task_type=task_type,
            result_summary=result_summary,
            files_created=files_created,
            execution_time=execution_time,
            from_number=from_number
        )
    except Exception as e:
        logger.warning(f"Memory save failed (non-fatal): {e}")
    
    # Build WhatsApp-friendly summary
    summary = _build_summary(task_type, result_str, files_created, execution_time)
    
    return {
        "success": True,
        "result": summary,
        "full_output": result_str,
        "task_type": task_type,
        "files_created": files_created,
        "execution_time": execution_time,
        "classification": classification
    }


def run_team_orchestrator(subtasks: list, original_request: str, from_number: str = "unknown") -> dict:
    """
    Run multiple crews in parallel and synthesize results.
    Called by POST /run-team.

    subtasks: [{"crew_type": str, "task": str, "label": str}, ...]
    """
    from crews import run_parallel_team, build_team_synthesis_crew

    start_time = datetime.now()

    # Phase 1: run all subtasks in parallel
    teammate_results = run_parallel_team(subtasks)

    successful = [r for r in teammate_results if r["success"]]
    failed     = [r for r in teammate_results if not r["success"]]

    if failed:
        logger.warning(f"[agent-team] {len(failed)} teammate(s) failed: {[f['label'] for f in failed]}")

    if not successful:
        raise RuntimeError("All teammates failed — no results to synthesize.")

    # Phase 2: synthesize
    synthesis_crew = build_team_synthesis_crew(original_request, successful)
    final_result   = synthesis_crew.kickoff()
    result_str     = final_result.raw if hasattr(final_result, 'raw') else str(final_result)

    execution_time = (datetime.now() - start_time).total_seconds()

    # Collect files created
    files_created = []
    output_dir = os.environ.get("AGENTS_OUTPUT_DIR", "/app/outputs")
    if os.path.exists(output_dir):
        files_created = [
            f for f in os.listdir(output_dir)
            if os.path.getmtime(os.path.join(output_dir, f)) >= start_time.timestamp()
        ]

    # Save to memory
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
        logger.warning(f"Memory save failed (non-fatal): {e}")

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


def _build_summary(
    task_type: str,
    full_output: str,
    files_created: list,
    execution_time: float
) -> str:
    """
    Build a concise, WhatsApp-friendly summary of the task result.
    The full output is saved to disk — the summary goes to the user.
    """
    
    type_labels = {
        "agent_team":    "🤝 Team task complete",
        "website_build": "🌐 Website built",
        "app_build": "⚙️ App built",
        "research_report": "📊 Research complete",
        "consulting_deliverable": "📋 Deliverable ready",
        "social_content": "📱 Content created",
        "code_task": "💻 Code complete",
        "general_writing": "✍️ Document ready",
        "agent_creation": "🤖 Agent proposal submitted",
        "unknown": "✅ Task complete",
    }
    
    label = type_labels.get(task_type, "✅ Task complete")
    
    lines = [
        f"{label}!",
        f"",
        f"⏱ Completed in {execution_time:.0f}s",
    ]
    
    if files_created:
        lines.append(f"📁 Files saved: {', '.join(files_created)}")
    
    # Send full output up to Telegram's 4096 char limit
    # Reserve ~100 chars for the header lines above
    MAX_CONTENT = 3800
    if full_output and len(full_output) > 50:
        content = full_output.strip()
        if len(content) > MAX_CONTENT:
            content = content[:MAX_CONTENT] + "\n\n[...truncated — reply 'more' for rest]"
        lines.append(f"\n{content}")

    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════
# API ENDPOINTS
# ══════════════════════════════════════════════════════════════

@app.get("/", response_model=StatusResponse)
def status():
    """System status and capability overview."""
    from router import TASK_TYPES
    
    return StatusResponse(
        status="running",
        service="agentsHQ Orchestrator",
        version="2.0.0",
        task_types=list(TASK_TYPES.keys()),
        agents=[
            "planner", "researcher", "copywriter",
            "web_builder", "app_builder", "code_agent",
            "consulting_agent", "social_media_agent",
            "qa_agent", "orchestrator", "agent_creator"
        ],
        uptime_seconds=time.time() - _start_time
    )


@app.get("/health")
def health():
    """Health check endpoint. Called by Docker and n8n."""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": time.time() - _start_time
    }


@app.post("/run", response_model=TaskResponse)
async def run_task(request: TaskRequest):
    """
    Main endpoint. Receives a task and runs it through the agent crew.
    
    Called by:
    - n8n WhatsApp workflow
    - Direct HTTP from any tool (Cursor, Claude Code, etc.)
    
    Returns a TaskResponse with result summary and metadata.
    """
    logger.info(f"Task received from {request.from_number}: {request.task[:100]}...")
    
    try:
        result = run_orchestrator(
            task_request=request.task,
            from_number=request.from_number
        )
        
        return TaskResponse(
            success=result["success"],
            result=result["result"],
            task_type=result.get("task_type", "unknown"),
            files_created=result.get("files_created", []),
            execution_time=result.get("execution_time", 0.0)
        )
        
    except Exception as e:
        logger.error(f"Orchestrator execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Agent execution failed: {str(e)}"
        )


@app.post("/run-team", response_model=TaskResponse)
async def run_team(request: TeamTaskRequest):
    """
    Run multiple crews in parallel (agent teams pattern).

    The caller decomposes the request into independent subtasks.
    All subtasks run concurrently; results are synthesized into one output.

    Example body:
    {
      "original_request": "I need research + a LinkedIn post + a Python script about AI in HR",
      "from_number": "7792432594",
      "subtasks": [
        {"crew_type": "research_crew", "task": "Research AI in HR", "label": "research"},
        {"crew_type": "social_crew",   "task": "Write LinkedIn post on AI in HR", "label": "social"},
        {"crew_type": "code_crew",     "task": "Write CV scorer Python script", "label": "code"}
      ]
    }
    """
    logger.info(f"/run-team received {len(request.subtasks)} subtasks from {request.from_number}")

    if not request.subtasks:
        raise HTTPException(status_code=400, detail="subtasks list cannot be empty")

    try:
        result = run_team_orchestrator(
            subtasks=request.subtasks,
            original_request=request.original_request,
            from_number=request.from_number
        )
        return TaskResponse(
            success=result["success"],
            result=result["result"],
            task_type=result["task_type"],
            files_created=result.get("files_created", []),
            execution_time=result.get("execution_time", 0.0)
        )
    except Exception as e:
        logger.error(f"/run-team failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Team execution failed: {str(e)}")


@app.get("/classify")
def classify_only(task: str):
    """
    Classify a task without running it.
    Useful for testing the router and understanding what crew would be used.
    """
    from router import classify_task, get_crew_type
    classification = classify_task(task)
    crew_type = get_crew_type(classification.get("task_type", "unknown"))
    return {
        "task": task,
        "classification": classification,
        "crew_type": crew_type
    }


@app.get("/capabilities")
def capabilities():
    """List all task types the system can handle."""
    from router import TASK_TYPES
    return {
        "task_types": {
            k: {
                "description": v["description"],
                "crew": v["crew"],
                "example_keywords": v["keywords"][:5]
            }
            for k, v in TASK_TYPES.items()
        }
    }


@app.get("/outputs")
def list_outputs():
    """List all files created by the agents."""
    output_dir = os.environ.get("AGENTS_OUTPUT_DIR", "/app/outputs")
    if not os.path.exists(output_dir):
        return {"files": [], "count": 0}
    
    files = []
    for f in os.listdir(output_dir):
        if not f.startswith("."):
            filepath = os.path.join(output_dir, f)
            files.append({
                "name": f,
                "size_bytes": os.path.getsize(filepath),
                "created": datetime.fromtimestamp(
                    os.path.getctime(filepath)
                ).isoformat()
            })
    
    files.sort(key=lambda x: x["created"], reverse=True)
    return {"files": files, "count": len(files)}


@app.get("/outputs/{filename}")
def get_output(filename: str):
    """Retrieve a specific output file."""
    # Security: prevent path traversal
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    filepath = f"/app/outputs/{filename}"
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    return {
        "filename": filename,
        "content": content,
        "size_bytes": len(content)
    }


@app.get("/memory/search")
def search_memory(query: str, top_k: int = 3):
    """Search agent memory for relevant past tasks."""
    try:
        from memory import query_memory
        results = query_memory(query, top_k=top_k)
        return {"query": query, "results": results, "count": len(results)}
    except Exception as e:
        return {"query": query, "results": [], "error": str(e)}


@app.get("/history/{session_id}")
def get_history(session_id: str, limit: int = 10):
    """Get conversation history for a WhatsApp session."""
    try:
        from memory import get_conversation_history
        history = get_conversation_history(session_id, limit=limit)
        return {"session_id": session_id, "history": history}
    except Exception as e:
        return {"session_id": session_id, "history": [], "error": str(e)}


# ── Run directly for testing ───────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    
    # Ensure required directories exist
    os.makedirs("/app/outputs", exist_ok=True)
    os.makedirs("/app/logs", exist_ok=True)
    os.makedirs("/app/outputs/proposals", exist_ok=True)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
