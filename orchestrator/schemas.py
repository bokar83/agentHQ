from pydantic import BaseModel
from typing import Optional


class TaskRequest(BaseModel):
    task: str
    from_number: str = "unknown"
    session_key: str = "default"
    task_type: str = "unknown"
    context: Optional[dict] = None
    callback_url: Optional[str] = None
    file_id: Optional[str] = None
    source: Optional[str] = None


class TaskResponse(BaseModel):
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
    status: str
    task_type: Optional[str] = ""
    result: Optional[str] = ""
    files_created: list = []
    execution_time: Optional[float] = 0.0
    error: Optional[str] = None


class TeamTaskRequest(BaseModel):
    subtasks: list
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


class HealthReportRequest(BaseModel):
    status: str
    report: str
    date: str


class SyncSessionRequest(BaseModel):
    session_key: str
    summary: str
    source: str = "browser"
    notify_telegram: bool = False


class ChatTokenRequest(BaseModel):
    pin: str


class AutonomyApproveBody(BaseModel):
    decision: str
    note: Optional[str] = None
    feedback_tag: Optional[str] = None
    edited_payload: Optional[dict] = None
