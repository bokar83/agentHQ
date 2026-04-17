import os
import time
import uuid
import logging
import asyncio
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends, Header, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from orchestrator.constants import SAVE_REQUIRED_TASK_TYPES
from orchestrator.state import _active_project, _git_lock
from orchestrator.schemas import (
    TaskRequest, TaskResponse, TeamTaskRequest, StatusResponse, 
    AsyncTaskResponse, JobStatusResponse, HealthReportRequest,
    SyncSessionRequest, ChatTokenRequest
)
from orchestrator.health import health_registry
from orchestrator.engine import run_orchestrator, run_team_orchestrator
from orchestrator.worker import _run_background_job
from orchestrator.handlers import (
    process_telegram_update, telegram_polling_loop, run_chat, 
    _shortcut_classify, _classify_obvious_chat
)
from orchestrator.utils import _extract_file_text, _query_system, _build_summary, _save_overflow_if_needed

logger = logging.getLogger("agentsHQ.app")
_start_time = time.time()

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

def verify_api_key(x_api_key: str = Header(default=None), authorization: Optional[str] = Header(default=None)):
    """API Key verification (Fail-closed)."""
    expected = os.environ.get("ORCHESTRATOR_API_KEY", "")
    debug_no_auth = os.environ.get("DEBUG_NO_AUTH", "false").lower() == "true"

    if not expected:
        if debug_no_auth:
            return
        logger.error("Security Breach Attempt: No ORCHESTRATOR_API_KEY configured.")
        raise HTTPException(status_code=500, detail="Server Security Misconfiguration.")

    if x_api_key == expected:
        return
    if authorization and authorization.startswith("Bearer ") and authorization[7:] == expected:
        return

    raise HTTPException(status_code=401, detail="Invalid API key.")

@app.on_event("startup")
async def startup_event():
    """Run at service startup."""
    try:
        from scheduler import start_scheduler
        if start_scheduler:
            start_scheduler()
            logger.info("Catalyst Daily Ignition initiated.")
    except ImportError:
        pass
    
    asyncio.create_task(telegram_polling_loop())
    logger.info("Telegram Polling Loop started.")

# ── API Routes ────────────────────────────────────────────────

@app.get("/", response_model=StatusResponse)
def get_status():
    from router import TASK_TYPES
    return StatusResponse(
        status="running",
        service="agentsHQ Orchestrator",
        version="2.0.0",
        task_types=list(TASK_TYPES.keys()),
        agents=["planner", "researcher", "copywriter", "web_builder", "app_builder", "code_agent", "qa_agent"],
        uptime_seconds=time.time() - _start_time
    )

@app.get("/health")
def health():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": time.time() - _start_time
    }

@app.get("/health/report")
def health_report():
    return health_registry.get_report()

@app.post("/telegram")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        body = await request.json()
        background_tasks.add_task(process_telegram_update, body)
    except Exception:
        pass
    return {"ok": True}

@app.post("/run", response_model=AsyncTaskResponse, status_code=202, dependencies=[Depends(verify_api_key)])
async def run_task(request: TaskRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    logger.info(f"Request from {request.from_number}: {request.task[:100]}...")

    # Unified Routing Logic
    shortcut = _shortcut_classify(request.task)
    if shortcut:
        task_type = shortcut
        classification = {"task_type": shortcut, "confidence": 0.95, "is_unknown": False}
    elif _classify_obvious_chat(request.task):
        task_type = "chat"
        classification = {"task_type": "chat", "confidence": 0.95, "is_unknown": False}
    else:
        from router import classify_task
        classification = classify_task(request.task)
        task_type = classification.get("task_type", "unknown")

    from notifier import send_briefing, send_message
    send_briefing(request.from_number, task_type, request.task)

    if task_type == "chat":
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, lambda: run_chat(message=request.task, session_key=request.session_key))
        send_message(request.from_number, result["result"])
        return AsyncTaskResponse(job_id=job_id, status="completed", message="Chat response delivered.")

    crew_session_key = f"{request.session_key}:{job_id[:8]}"
    background_tasks.add_task(
        _run_background_job,
        task=request.task,
        from_number=request.from_number,
        session_key=crew_session_key,
        job_id=job_id,
        classification=classification,
    )

    return AsyncTaskResponse(job_id=job_id, message="Job queued. Result will be delivered to Telegram.")

@app.post("/run-sync", response_model=TaskResponse, dependencies=[Depends(verify_api_key)])
async def run_task_sync(request: TaskRequest):
    try:
        # Simplified routing for sync
        if _classify_obvious_chat(request.task):
            result = run_chat(message=request.task, session_key=request.session_key)
        else:
            result = run_orchestrator(task_request=request.task, from_number=request.from_number, session_key=request.session_key)

        return TaskResponse(
            success=result["success"],
            result=result["result"],
            task_type=result.get("task_type", "unknown"),
            files_created=result.get("files_created", []),
            execution_time=result.get("execution_time", 0.0)
        )
    except Exception as e:
        logger.error(f"Sync request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{job_id}", response_model=JobStatusResponse, dependencies=[Depends(verify_api_key)])
def get_job_status(job_id: str):
    from memory import get_job
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(**job)

@app.get("/classify", dependencies=[Depends(verify_api_key)])
def classify_only(task: str):
    from router import classify_task, get_crew_type
    classification = classify_task(task)
    return {"task": task, "classification": classification, "crew_type": get_crew_type(classification.get("task_type"))}

@app.post("/upload", dependencies=[Depends(verify_api_key)])
async def upload_file(file: UploadFile):
    upload_dir = "/app/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_id = str(uuid.uuid4())[:8]
    
    # Path Traversal Protection
    safe_name = os.path.basename(file.filename or "upload").replace(" ", "_")
    if ".." in safe_name or safe_name.startswith("/") or safe_name.startswith("\\"):
        raise HTTPException(status_code=400, detail="Invalid filename")
        
    dest = os.path.join(upload_dir, f"{file_id}_{safe_name}")
    
    # Streaming write for large files
    try:
        with open(dest, "wb") as f:
            while chunk := await file.read(1024 * 1024): # 1MB chunks
                f.write(chunk)
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail="File upload failed")

    extracted = _extract_file_text(dest, safe_name)
    # Save the extraction for the agent to read
    with open(dest + ".txt", "w", encoding="utf-8") as f:
        f.write(extracted)
        
    return {"file_id": file_id, "filename": safe_name, "preview": extracted[:300]}

@app.post("/sync-session", dependencies=[Depends(verify_api_key)])
async def sync_session(req: SyncSessionRequest):
    from memory import save_conversation_turn
    label = f"[Browser session via {req.source}]"
    content = f"{label}\n{req.summary}"
    save_conversation_turn(req.session_key, "assistant", content)
    save_conversation_turn(req.session_key, "user", f"(Context synced from {req.source} — ready to continue)")

    if req.notify_telegram:
        telegram_chat_id = req.session_key.split(":")[0]
        from notifier import send_message as _send
        _send(telegram_chat_id, f"Browser session saved. Pick up here anytime — I remember what happened.")

    logger.info(f"sync-session: wrote {len(req.summary)} chars for session_key={req.session_key} source={req.source}")
    return {"success": True, "session_key": req.session_key, "chars_written": len(req.summary)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
