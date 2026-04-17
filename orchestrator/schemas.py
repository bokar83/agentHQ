from pydantic import BaseModel
from typing import Optional, List

class TaskRequest(BaseModel):
    task: str
    from_number: str = "unknown"
    session_key: str = "default"
    context: Optional[dict] = None  # optional extra context from caller
    callback_url: Optional[str] = None  # webhook URL to POST result when async job completes
    file_id: Optional[str] = None   # ID from /upload — orchestrator prepends extracted text
    source: Optional[str] = None    # "browser" | "telegram" | "api"

class TaskResponse(BaseModel) :
    success: bool
    result: str
    task_type: str = "unknown"
    files_created: list = []
    execution_time: float = 0.0
    title: str = ""
    deliverable: str = ""

class AsyncTaskResponse(BaseModel):
    job_id: str
    status: str = "pending"
    message: str = "Job queued. Poll /status/{job_id} for updates."

class JobStatusResponse(BaseModel):
    job_id: str
    status: str          # pending | running | completed | failed
    task_type: str = ""
    result: str = ""
    files_created: list = []
    execution_time: float = 0.0

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
