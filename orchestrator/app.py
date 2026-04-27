"""
app.py - FastAPI entrypoint for the agentsHQ orchestrator.

Startup hooks (in order):
  1. install_litellm_callback() , token ledger registration
  2. start_scheduler()           , daily cron + heartbeat wakes
  3. telegram_polling_loop()     , background task

Auth is fail-closed: if ORCHESTRATOR_API_KEY is unset and DEBUG_NO_AUTH is
not "true", every gated endpoint returns 500 on misconfig.
"""
import asyncio
import logging
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Optional

# Configure logging BEFORE importing any orchestrator modules, so every
# module's logger.info/warning lands in docker logs and the file.
_LOG_DIR = os.environ.get("AGENTS_LOG_DIR", "/app/logs")
os.makedirs(_LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(_LOG_DIR, "orchestrator.log"), mode="a"),
    ],
)

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware

from constants import SAVE_REQUIRED_TASK_TYPES
from engine import run_orchestrator, run_team_orchestrator
from handlers import (
    _classify_obvious_chat,
    _shortcut_classify,
    process_telegram_update,
    telegram_polling_loop,
)
from handlers_chat import run_chat
from health import health_registry
from webhooks import router as webhooks_router
from schemas import (
    AsyncTaskResponse,
    AutonomyApproveBody,
    ChatTokenRequest,
    HealthReportRequest,
    JobStatusResponse,
    StatusResponse,
    SyncSessionRequest,
    TaskRequest,
    TaskResponse,
    TeamTaskRequest,
)
from utils import _extract_file_text
from worker import _run_background_job

logger = logging.getLogger("agentsHQ.app")
_start_time = time.time()


# ══════════════════════════════════════════════════════════════
# App + middleware
# ══════════════════════════════════════════════════════════════

app = FastAPI(
    title="agentsHQ Orchestrator",
    description="Self-hosted multi-agent intelligence for Catalyst Works Consulting",
    version="2.0.0",
)

_CORS_ALLOWED = [
    "https://agentshq.boubacarbarry.com",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ALLOWED,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization", "X-Api-Key", "X-Internal-Token"],
    allow_credentials=True,
)
app.include_router(webhooks_router)


# ══════════════════════════════════════════════════════════════
# Auth
# ══════════════════════════════════════════════════════════════

def verify_api_key(
    x_api_key: Optional[str] = Header(default=None),
    authorization: Optional[str] = Header(default=None),
):
    """Reject requests without valid auth. Fail-closed when ORCHESTRATOR_API_KEY
    is unset. Accepts two forms:
      1. X-Api-Key: <raw key>         Telegram, n8n, existing integrations
      2. Authorization: Bearer <jwt>  browser chat UI (JWT signed in /chat-token)
         OR Authorization: Bearer <raw key>  for CLI tooling

    Dev override: set DEBUG_NO_AUTH=true to bypass. Only use locally.
    """
    expected = os.environ.get("ORCHESTRATOR_API_KEY", "")
    if not expected:
        if os.environ.get("DEBUG_NO_AUTH", "false").lower() == "true":
            return
        logger.error("verify_api_key: ORCHESTRATOR_API_KEY not configured (fail-closed)")
        raise HTTPException(status_code=500, detail="Server auth misconfigured.")

    # Raw API key header (primary path for X-Api-Key)
    if x_api_key == expected:
        return

    # Bearer token: either raw key OR signed JWT from /chat-token
    if authorization and authorization.startswith("Bearer "):
        import jwt as pyjwt
        token = authorization[7:]
        if token == expected:
            return
        try:
            pyjwt.decode(token, expected, algorithms=["HS256"])
            return
        except pyjwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Session expired. Refresh to get a new token.")
        except pyjwt.InvalidTokenError:
            pass

    raise HTTPException(status_code=401, detail="Invalid or missing auth. Use X-Api-Key or Authorization: Bearer <token>.")


def verify_chat_token(authorization: Optional[str] = Header(None)):
    """Dependency: accepts either the raw API key OR a valid browser JWT."""
    import jwt as pyjwt

    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header.")

    api_key = os.environ.get("ORCHESTRATOR_API_KEY", "")
    if authorization == api_key or authorization == f"Bearer {api_key}":
        return True

    if authorization.startswith("Bearer "):
        token = authorization[7:]
        try:
            pyjwt.decode(token, api_key, algorithms=["HS256"])
            return True
        except pyjwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Session expired. Refresh the page to get a new token.")
        except pyjwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token.")

    raise HTTPException(status_code=401, detail="Invalid authorization.")


# ══════════════════════════════════════════════════════════════
# Startup
# ══════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    """Run at service startup."""
    # Token ledger: register litellm callback BEFORE any crew or council
    # fires. Without this, llm_calls stops receiving rows after the flip.
    try:
        from usage_logger import install_litellm_callback
        install_litellm_callback()
    except Exception as e:
        logger.warning(f"usage_logger startup failed (non-fatal): {e}")

    # Daily cron + heartbeat. scheduler.start_scheduler internally calls
    # heartbeat.start(), registering the 3 default wakes.
    try:
        from scheduler import start_scheduler
        if start_scheduler:
            start_scheduler()
            logger.info("Catalyst Daily Ignition initiated.")
    except ImportError:
        pass

    # Telegram polling in the background (hardened loop in handlers.py).
    asyncio.create_task(telegram_polling_loop())
    logger.info("Telegram Polling Loop scheduled.")


# ══════════════════════════════════════════════════════════════
# Public routes (no auth)
# ══════════════════════════════════════════════════════════════

@app.get("/", response_model=StatusResponse)
def get_status():
    from router import TASK_TYPES
    return StatusResponse(
        status="running",
        service="agentsHQ Orchestrator",
        version="2.0.0",
        task_types=list(TASK_TYPES.keys()),
        agents=["planner", "researcher", "copywriter", "web_builder", "app_builder", "code_agent", "qa_agent"],
        uptime_seconds=time.time() - _start_time,
    )


@app.get("/health")
def health():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": time.time() - _start_time,
    }


@app.post("/telegram")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    """Keep webhook endpoint as a backup though polling is primary."""
    try:
        body = await request.json()
        background_tasks.add_task(process_telegram_update, body)
    except Exception:
        pass
    return {"ok": True}


@app.post("/internal/health-report")
async def receive_health_report(request: HealthReportRequest, req: Request):
    """
    Internal webhook called by the agentsHQ Weekly Health Check remote agent.
    Protected by X-Internal-Token header (HEALTH_REPORT_TOKEN env var).
    """
    expected_token = os.environ.get("HEALTH_REPORT_TOKEN", "")
    provided_token = req.headers.get("X-Internal-Token", "")
    if not expected_token or provided_token != expected_token:
        raise HTTPException(status_code=401, detail="Unauthorised")

    try:
        from notifier import send_health_check_report
        email_sent = send_health_check_report(request.status, request.report, request.date)
        logger.info(f"Health check report received: status={request.status}, date={request.date}, email_sent={email_sent}")
        return {"ok": True, "email_sent": email_sent}
    except Exception as e:
        logger.error(f"Health report delivery failed: {e}")
        return {"ok": True, "email_sent": False}


@app.post("/chat-token")
async def chat_token(req: ChatTokenRequest):
    """
    Issue a short-lived JWT for the browser chat UI.
    PIN via CHAT_UI_PIN env var (required). No PIN = endpoint disabled.
    """
    import jwt as pyjwt

    expected_pin = os.environ.get("CHAT_UI_PIN", "")
    if not expected_pin:
        raise HTTPException(status_code=503, detail="Chat UI not configured on this server.")
    if req.pin != expected_pin:
        raise HTTPException(status_code=401, detail="Invalid PIN.")

    secret = os.environ.get("ORCHESTRATOR_API_KEY")
    if not secret:
        logger.error("/chat-token: ORCHESTRATOR_API_KEY not configured, cannot sign JWT")
        raise HTTPException(status_code=503, detail="Chat token issuer not configured.")

    payload = {
        "sub": "browser-chat",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=8),
    }
    token = pyjwt.encode(payload, secret, algorithm="HS256")
    return {"token": token}


# ══════════════════════════════════════════════════════════════
# Task execution routes (auth-gated)
# ══════════════════════════════════════════════════════════════

@app.post("/run", response_model=AsyncTaskResponse, status_code=202, dependencies=[Depends(verify_api_key)])
async def run_task(request: TaskRequest, background_tasks: BackgroundTasks):
    """Main endpoint, async, fire-and-forget. 202 immediately."""
    logger.info(f"Request from {request.from_number}: {request.task[:100]}...")
    job_id = str(uuid.uuid4())

    # 'more' command: sync, instant
    if request.task.strip().lower() in ("more", "more please", "continue", "show more"):
        from memory import get_next_chunk
        from notifier import send_message
        chunk_result = get_next_chunk(request.session_key)
        if chunk_result["found"]:
            suffix = "\n\n[reply 'more' for the rest]" if chunk_result["has_more"] else "\n\n[end of output]"
            send_message(request.from_number, chunk_result["chunk"] + suffix)
        else:
            send_message(request.from_number, "Nothing more to show, that was the full output.")
        return AsyncTaskResponse(job_id=job_id, status="completed", message="Chunk delivered.")

    # Classify for an accurate briefing
    from notifier import send_briefing, send_message
    _shortcut = _shortcut_classify(request.task)
    if _shortcut and _shortcut != "memory_capture":
        task_type = _shortcut
        classification = {"task_type": _shortcut, "confidence": 0.95, "is_unknown": False, "has_email_followup": False}
    elif _shortcut == "memory_capture":
        task_type = "chat"
        classification = {"task_type": "chat", "confidence": 0.95, "is_unknown": False, "has_email_followup": False}
    elif _classify_obvious_chat(request.task):
        task_type = "chat"
        classification = {"task_type": "chat", "confidence": 0.95, "is_unknown": False, "has_email_followup": False}
    else:
        from router import classify_task
        classification = classify_task(request.task)
        task_type = classification.get("task_type", "unknown")

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
    """Synchronous task run for Cursor / Claude Code callers."""
    try:
        if _classify_obvious_chat(request.task):
            result = run_chat(message=request.task, session_key=request.session_key)
        else:
            result = run_orchestrator(
                task_request=request.task,
                from_number=request.from_number,
                session_key=request.session_key,
            )
        return TaskResponse(
            success=result["success"],
            result=result["result"],
            task_type=result.get("task_type", "unknown"),
            files_created=result.get("files_created", []),
            execution_time=result.get("execution_time", 0.0),
            title=result.get("title", ""),
            deliverable=result.get("deliverable", ""),
        )
    except Exception as e:
        logger.error(f"Sync request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/run-team", response_model=TaskResponse, dependencies=[Depends(verify_api_key)])
async def run_team(request: TeamTaskRequest):
    """Run multiple crews in parallel."""
    logger.info(f"/run-team received {len(request.subtasks)} subtasks from {request.from_number}")
    if not request.subtasks:
        raise HTTPException(status_code=400, detail="subtasks list cannot be empty")
    try:
        result = run_team_orchestrator(
            subtasks=request.subtasks,
            original_request=request.original_request,
            from_number=request.from_number,
        )
        return TaskResponse(
            success=result["success"],
            result=result["result"],
            task_type=result["task_type"],
            files_created=result.get("files_created", []),
            execution_time=result.get("execution_time", 0.0),
        )
    except Exception as e:
        logger.error(f"/run-team failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Team execution failed: {str(e)}")


@app.post("/run-async", response_model=AsyncTaskResponse, dependencies=[Depends(verify_api_key)])
async def run_task_async(request: TaskRequest, background_tasks: BackgroundTasks):
    """Async task endpoint used by the browser chat UI + n8n."""
    job_id = str(uuid.uuid4())[:8]

    from memory import create_job
    create_job(
        job_id=job_id,
        session_key=request.session_key,
        from_number=request.from_number,
        task=request.task,
    )

    def _run_in_background():
        from memory import update_job
        try:
            update_job(job_id, status="running")

            # Inject uploaded file content into task if file_id provided
            task_text = request.task
            if request.file_id:
                upload_dir = "/app/uploads"
                matches = [f for f in os.listdir(upload_dir) if f.startswith(request.file_id + "_")] if os.path.isdir(upload_dir) else []
                if matches:
                    txt_path = os.path.join(upload_dir, matches[0] + ".txt")
                    if os.path.exists(txt_path):
                        with open(txt_path, encoding="utf-8", errors="replace") as fh:
                            file_content = fh.read()
                        fname = matches[0][9:]  # strip file_id_ prefix
                        task_text = f"[Attached file: {fname}]\n{file_content}\n\n---\n{request.task}"

            # Same classification pipeline as /run and /run-sync
            _shortcut = _shortcut_classify(task_text)
            if _shortcut and _shortcut != "memory_capture":
                routed_as_chat = False
            elif _classify_obvious_chat(task_text):
                routed_as_chat = True
            else:
                routed_as_chat = False

            if routed_as_chat:
                result = run_chat(message=task_text, session_key=request.session_key)
            else:
                result = run_orchestrator(
                    task_request=task_text,
                    from_number=request.from_number,
                    session_key=request.session_key,
                )

            result_text = (
                result.get("result")
                or result.get("deliverable")
                or result.get("summary")
                or result.get("output")
                or ""
            )
            task_type_val = result.get("task_type", "unknown")
            title_val = result.get("title", task_text[:80])
            deliverable_val = result.get("deliverable", result_text)

            # Save to Drive only for tangible artifacts
            drive_url = ""
            if task_type_val in SAVE_REQUIRED_TASK_TYPES:
                try:
                    from saver import save_to_drive
                    drive_url = save_to_drive(title_val, task_type_val, deliverable_val)
                    if drive_url:
                        result_text = result_text + f"\n\nDrive: {drive_url}"
                except Exception as _drive_err:
                    logger.warning(f"Drive save failed for job {job_id}: {_drive_err}")
            else:
                logger.info(f"Async job {job_id}: task_type '{task_type_val}' is query-only, skipping Drive save")

            update_job(
                job_id=job_id,
                status="completed",
                result=result_text,
                task_type=task_type_val,
                files_created=result.get("files_created", []),
                execution_time=result.get("execution_time", 0.0),
            )
            logger.info(f"Async job {job_id} completed ({result.get('task_type')})")

            # Fire callback if provided
            if request.callback_url:
                try:
                    import requests as _requests
                    _requests.post(
                        request.callback_url,
                        json={
                            "job_id": job_id,
                            "status": "completed",
                            "result": result_text,
                            "task_type": result.get("task_type", "unknown"),
                            "files_created": result.get("files_created", []),
                            "execution_time": result.get("execution_time", 0.0),
                            "from_number": request.from_number,
                            "chat_id": (request.context or {}).get("chat_id", request.from_number),
                            "success": True,
                        },
                        timeout=10,
                    )
                    logger.info(f"Callback fired for job {job_id}")
                except Exception as cb_err:
                    logger.warning(f"Callback failed for job {job_id}: {cb_err}")

        except Exception as e:
            logger.error(f"Async job {job_id} failed: {e}", exc_info=True)
            from memory import update_job as uj
            raw = str(e)
            if "assistant message prefill" in raw or "must end with a user message" in raw:
                friendly = (
                    "The research agent hit a provider limit on this prompt. "
                    "Try asking one focused question at a time (for example, "
                    "'find 5 mechanic shops near 84095 that do safety inspection') "
                    "and I'll run each one cleanly."
                )
            elif "Provider returned error" in raw or "invalid_request_error" in raw:
                friendly = (
                    "The model provider rejected this request. Reword the prompt "
                    "or narrow its scope and try again. I've logged the full trace."
                )
            elif "rate" in raw.lower() and "limit" in raw.lower():
                friendly = "Hit a rate limit. Wait 30 seconds and try again."
            else:
                friendly = f"Task failed. (Diagnostic: {raw[:200]})"
            uj(job_id=job_id, status="failed", error=friendly, result=friendly)

            if request.callback_url:
                try:
                    import requests as _requests
                    _requests.post(
                        request.callback_url,
                        json={
                            "job_id": job_id,
                            "status": "failed",
                            "result": friendly,
                            "task_type": "unknown",
                            "files_created": [],
                            "execution_time": 0.0,
                            "from_number": request.from_number,
                            "chat_id": (request.context or {}).get("chat_id", request.from_number),
                            "success": False,
                        },
                        timeout=10,
                    )
                except Exception:
                    pass

    background_tasks.add_task(_run_in_background)
    logger.info(f"Queued async job {job_id} for: {request.task[:60]}... callback={request.callback_url or 'none'} context={request.context}")

    return AsyncTaskResponse(
        job_id=job_id,
        status="pending",
        message=f"Job {job_id} queued. Poll /status/{job_id} for updates.",
    )


# ══════════════════════════════════════════════════════════════
# Phase 1: laptop-parity approval endpoint
# ══════════════════════════════════════════════════════════════

@app.post("/autonomy/approve/{queue_id}", dependencies=[Depends(verify_api_key)])
def http_autonomy_approve(queue_id: int, body: AutonomyApproveBody):
    """Laptop-parity approval endpoint. Mirrors the Telegram reply flow."""
    from approval_queue import (
        approve as _aq_approve,
        edit as _aq_edit,
        get as _aq_get,
        reject as _aq_reject,
    )

    if body.decision == "approve":
        row = _aq_approve(queue_id, note=body.note)
    elif body.decision == "reject":
        row = _aq_reject(queue_id, note=body.note, feedback_tag=body.feedback_tag)
    elif body.decision == "edit":
        if not body.edited_payload:
            raise HTTPException(status_code=400, detail="edited_payload required for edit")
        row = _aq_edit(queue_id, body.edited_payload, note=body.note)
    else:
        raise HTTPException(status_code=400, detail="decision must be approve|reject|edit")

    if row is None:
        current = _aq_get(queue_id)
        if current is None:
            raise HTTPException(status_code=404, detail=f"queue #{queue_id} not found")
        raise HTTPException(status_code=409, detail=f"queue #{queue_id} already {current.status}")

    return {
        "id": row.id,
        "crew_name": row.crew_name,
        "proposal_type": row.proposal_type,
        "status": row.status,
        "ts_decided": row.ts_decided.isoformat() if row.ts_decided else None,
        "decision_note": row.decision_note,
        "boubacar_feedback_tag": row.boubacar_feedback_tag,
    }


# ══════════════════════════════════════════════════════════════
# Inbound lead webhook
# ══════════════════════════════════════════════════════════════

@app.post("/inbound-lead", dependencies=[Depends(verify_api_key)])
async def inbound_lead_webhook(request: Request, background_tasks: BackgroundTasks):
    """Webhook for n8n Calendly/Formspree inbound lead events."""
    try:
        body = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON body: {e}")

    logger.info(
        f"Inbound lead received: {body.get('email', '(no email)')} "
        f"source={body.get('source', '?')} booking={body.get('booking_id', '?')}"
    )

    def _run_inbound(payload: dict):
        try:
            from skills.inbound_lead.runner import run_inbound_lead
            from notifier import send_message
            result = run_inbound_lead(payload)
            try:
                from skills.inbound_lead.telegram_notify import format_inbound_telegram_message
                msg = format_inbound_telegram_message(result)
                telegram_chat = os.environ.get("TELEGRAM_CHAT_ID", "")
                if telegram_chat:
                    send_message(telegram_chat, msg)
            except Exception as notify_exc:
                logger.warning(f"Telegram notify failed: {notify_exc}")
            logger.info(
                f"Inbound lead done: status={result.status} "
                f"email={result.payload.email} page={(result.log.notion_page_id if result.log else None)}"
            )
        except Exception as exc:
            logger.error(f"Inbound lead background task failed: {exc}")

    background_tasks.add_task(_run_inbound, body)
    return {"status": "accepted", "message": "Inbound lead queued."}


# ══════════════════════════════════════════════════════════════
# Query / introspection endpoints (auth-gated)
# ══════════════════════════════════════════════════════════════

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
    return {
        "task": task,
        "classification": classification,
        "crew_type": get_crew_type(classification.get("task_type", "unknown")),
    }


@app.get("/capabilities", dependencies=[Depends(verify_api_key)])
def capabilities():
    from router import TASK_TYPES
    return {
        "task_types": {
            k: {
                "description": v["description"],
                "crew": v["crew"],
                "example_keywords": v["keywords"][:5],
            }
            for k, v in TASK_TYPES.items()
        }
    }


@app.get("/outputs", dependencies=[Depends(verify_api_key)])
def list_outputs():
    output_dir = os.environ.get("AGENTS_OUTPUT_DIR", "/app/outputs")
    if not os.path.exists(output_dir):
        return {"files": [], "count": 0}
    files = []
    for f in os.listdir(output_dir):
        if not f.startswith("."):
            filepath = os.path.join(output_dir, f)
            if os.path.isdir(filepath):
                continue
            files.append({
                "name": f,
                "size_bytes": os.path.getsize(filepath),
                "created": datetime.fromtimestamp(os.path.getctime(filepath)).isoformat(),
            })
    files.sort(key=lambda x: x["created"], reverse=True)
    return {"files": files, "count": len(files)}


@app.get("/outputs/{filename}", dependencies=[Depends(verify_api_key)])
def get_output(filename: str):
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    filepath = f"/app/outputs/{filename}"
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    return {"filename": filename, "content": content, "size_bytes": len(content)}


@app.get("/memory/search", dependencies=[Depends(verify_api_key)])
def search_memory(query: str, top_k: int = 3):
    try:
        from memory import query_memory
        results = query_memory(query, top_k=top_k)
        return {"query": query, "results": results, "count": len(results)}
    except Exception as e:
        return {"query": query, "results": [], "error": str(e)}


@app.get("/history/{session_id}", dependencies=[Depends(verify_api_key)])
def get_history(session_id: str, limit: int = 10):
    try:
        from memory import get_conversation_history
        history = get_conversation_history(session_id, limit=limit)
        return {"session_id": session_id, "history": history}
    except Exception as e:
        return {"session_id": session_id, "history": [], "error": str(e)}


# ══════════════════════════════════════════════════════════════
# Upload + session sync
# ══════════════════════════════════════════════════════════════

@app.post("/upload", dependencies=[Depends(verify_api_key)])
async def upload_file(file: UploadFile):
    upload_dir = "/app/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_id = str(uuid.uuid4())[:8]

    # Path traversal protection
    safe_name = os.path.basename(file.filename or "upload").replace(" ", "_")
    if ".." in safe_name or safe_name.startswith("/") or safe_name.startswith("\\"):
        raise HTTPException(status_code=400, detail="Invalid filename")

    dest = os.path.join(upload_dir, f"{file_id}_{safe_name}")

    try:
        with open(dest, "wb") as f:
            while chunk := await file.read(1024 * 1024):
                f.write(chunk)
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail="File upload failed")

    extracted = _extract_file_text(dest, safe_name)
    with open(dest + ".txt", "w", encoding="utf-8") as f:
        f.write(extracted)

    return {"file_id": file_id, "filename": safe_name, "preview": extracted[:300]}


@app.post("/sync-session", dependencies=[Depends(verify_api_key)])
async def sync_session(req: SyncSessionRequest):
    from memory import save_conversation_turn
    label = f"[Browser session via {req.source}]"
    content = f"{label}\n{req.summary}"
    save_conversation_turn(req.session_key, "assistant", content)
    save_conversation_turn(req.session_key, "user", f"(Context synced from {req.source}, ready to continue)")

    if req.notify_telegram:
        telegram_chat_id = req.session_key.split(":")[0]
        from notifier import send_message as _send
        _send(telegram_chat_id, "Browser session saved. Pick up here anytime, I remember what happened.")

    logger.info(f"sync-session: wrote {len(req.summary)} chars for session_key={req.session_key} source={req.source}")
    return {"success": True, "session_key": req.session_key, "chars_written": len(req.summary)}


# ======================================================================
# Atlas M8: Mission Control -- read-only data endpoints
# All gated by verify_chat_token (same JWT-PIN as /chat).
# ======================================================================

from fastapi.responses import JSONResponse
import atlas_dashboard as _atd


@app.get("/atlas/state")
async def atlas_state(_auth=Depends(verify_chat_token)):
    return JSONResponse(_atd.get_state())


@app.get("/atlas/queue")
async def atlas_queue(_auth=Depends(verify_chat_token)):
    return JSONResponse(_atd.get_queue())


@app.get("/atlas/content")
async def atlas_content(_auth=Depends(verify_chat_token)):
    return JSONResponse(_atd.get_content())


@app.get("/atlas/spend")
async def atlas_spend(_auth=Depends(verify_chat_token)):
    return JSONResponse(_atd.get_spend())


@app.get("/atlas/heartbeats")
async def atlas_heartbeats(_auth=Depends(verify_chat_token)):
    return JSONResponse(_atd.get_heartbeats())


@app.get("/atlas/errors")
async def atlas_errors(_auth=Depends(verify_chat_token)):
    return JSONResponse(_atd.get_errors())


@app.get("/atlas/hero")
async def atlas_hero(_auth=Depends(verify_chat_token)):
    return JSONResponse(_atd.get_hero())


@app.get("/atlas/ideas")
async def atlas_ideas(_auth=Depends(verify_chat_token)):
    return JSONResponse(_atd.get_ideas())


# ======================================================================
# Atlas M8: Mission Control -- write/action endpoints
# ======================================================================

from pydantic import BaseModel as _BaseModel


class _AtlasToggleBody(_BaseModel):
    enabled: bool


class _AtlasDryRunBody(_BaseModel):
    dry_run: bool


class _AtlasRejectBody(_BaseModel):
    note: str = ""


class _LedgerEntryBody(_BaseModel):
    amount_usd: float
    tool: str
    category: str
    project: str = "agentsHQ"
    customer: str | None = None
    description: str | None = None
    date: str | None = None


@app.get("/atlas/ledger")
async def atlas_ledger(days: int = 30, _auth=Depends(verify_chat_token)):
    return JSONResponse(_atd.get_cost_ledger(days=days))


@app.post("/atlas/ledger")
async def atlas_ledger_add(body: _LedgerEntryBody, _auth=Depends(verify_chat_token)):
    return JSONResponse(_atd.add_cost_ledger_entry(
        amount_usd=body.amount_usd,
        tool=body.tool,
        category=body.category,
        project=body.project,
        customer=body.customer,
        description=body.description,
        date_str=body.date,
    ))


@app.post("/atlas/toggle/griot")
async def atlas_toggle_griot(body: _AtlasToggleBody, _auth=Depends(verify_chat_token)):
    from autonomy_guard import get_guard
    get_guard().set_crew_enabled("griot", body.enabled)
    return JSONResponse(_atd.get_state())


@app.post("/atlas/toggle/dry_run")
async def atlas_toggle_dry_run(body: _AtlasDryRunBody, _auth=Depends(verify_chat_token)):
    from autonomy_guard import get_guard
    get_guard().set_crew_dry_run("griot", body.dry_run)
    return JSONResponse(_atd.get_state())


@app.post("/atlas/queue/{queue_id}/approve")
async def atlas_queue_approve(queue_id: int, _auth=Depends(verify_chat_token)):
    import approval_queue
    row = approval_queue.approve(queue_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Queue item not found or already decided")
    return JSONResponse(_atd.get_queue())


@app.post("/atlas/queue/{queue_id}/reject")
async def atlas_queue_reject(queue_id: int, body: _AtlasRejectBody, _auth=Depends(verify_chat_token)):
    import approval_queue
    row = approval_queue.reject(queue_id, note=body.note or None)
    if row is None:
        raise HTTPException(status_code=404, detail="Queue item not found or already decided")
    return JSONResponse(_atd.get_queue())


@app.post("/atlas/brief/posted")
async def atlas_brief_posted(_auth=Depends(verify_chat_token)):
    raise HTTPException(
        status_code=501,
        detail=(
            "posted/skip actions require a Telegram reply_to_msg_id to locate the "
            "publish-brief window. _PUBLISH_BRIEF_WINDOWS is keyed by Telegram message "
            "ID and cannot be looked up from the dashboard. Reply 'posted' or 'skip' "
            "directly in Telegram to the per-post brief message."
        ),
    )


@app.post("/atlas/brief/skip")
async def atlas_brief_skip(_auth=Depends(verify_chat_token)):
    raise HTTPException(
        status_code=501,
        detail=(
            "posted/skip actions require a Telegram reply_to_msg_id to locate the "
            "publish-brief window. _PUBLISH_BRIEF_WINDOWS is keyed by Telegram message "
            "ID and cannot be looked up from the dashboard. Reply 'posted' or 'skip' "
            "directly in Telegram to the per-post brief message."
        ),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
