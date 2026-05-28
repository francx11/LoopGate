import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class TaskStatus(StrEnum):
    PENDING_APPROVAL = "pending_approval"
    QUEUED           = "queued"
    RUNNING          = "running"
    DONE             = "done"
    ERROR            = "error"
    REJECTED         = "rejected"


class LogLine(BaseModel):
    time: str
    text: str


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    command: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING_APPROVAL
    created_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    started_at: str | None = None
    finished_at: str | None = None
    exit_code: int | None = None
    reject_reason: str | None = None
    log: list[LogLine] = []
    claude_session_id: str | None = None
    claude_result: str | None = None
    claude_cost_usd: float | None = None


# ── Request/Response schemas ──────────────────────────────────────────────────

class CreateTaskRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    command: str = Field(..., min_length=1, max_length=8192)
    description: str = Field("", max_length=300)


class ApproveTaskRequest(BaseModel):
    action: str = Field(..., pattern="^(approve|reject)$")
    reason: str = ""
