from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class TaskStatus(str, Enum):
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
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    exit_code: Optional[int] = None
    reject_reason: Optional[str] = None
    log: List[LogLine] = []
    claude_session_id: Optional[str] = None
    claude_result: Optional[str] = None
    claude_cost_usd: Optional[float] = None


# ── Request/Response schemas ──────────────────────────────────────────────────

class CreateTaskRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    command: str = Field(..., min_length=1, max_length=8192)
    description: str = Field("", max_length=300)


class ApproveTaskRequest(BaseModel):
    action: str = Field(..., pattern="^(approve|reject)$")
    reason: str = ""
