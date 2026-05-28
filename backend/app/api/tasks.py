import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.auth import verify_token
from app.core.config import settings
from app.core.limiter import limiter
from app.core.store import session_store, task_store
from app.core.ws_manager import manager
from app.models.claude import CreateClaudePromptRequest, build_claude_command
from app.models.task import ApproveTaskRequest, CreateTaskRequest, Task, TaskStatus
from app.services.executor import run_task

router = APIRouter(tags=["tasks"], dependencies=[Depends(verify_token)])
audit = logging.getLogger("loopgate.audit")


@router.get("/projects", summary="List directories in PROJECTS_ROOT")
@limiter.limit("60/minute")
def list_projects(request: Request):
    root = Path(settings.PROJECTS_ROOT).resolve()
    if not root.exists():
        return []
    return [
        {"name": d.name, "path": str(d)}
        for d in sorted(root.iterdir())
        if d.is_dir() and not d.name.startswith(".")
        and d.resolve().is_relative_to(root)
    ]


@router.get("/tasks", response_model=list[Task], summary="List all tasks")
@limiter.limit("120/minute")
def list_tasks(request: Request):
    return task_store.all()


@router.get("/tasks/{task_id}", response_model=Task, summary="Get a single task")
@limiter.limit("120/minute")
def get_task(request: Request, task_id: str):
    task = task_store.get(task_id)
    if not task:
        raise HTTPException(404, f"Task '{task_id}' not found")
    return task


@router.post("/tasks", response_model=Task, status_code=201, summary="Create a task")
@limiter.limit("30/minute")
async def create_task(request: Request, body: CreateTaskRequest):
    task = Task(name=body.name, command=body.command, description=body.description)
    task_store.add(task)
    await manager.broadcast({"type": "task_created", "task": task.model_dump()})
    audit.info("task_created id=%s name=%r ip=%s", task.id[:8], body.name, _ip(request))
    return task


@router.post(
    "/tasks/claude-prompt",
    response_model=Task,
    status_code=201,
    summary="Create a Claude Code task from a natural-language prompt",
)
@limiter.limit("20/minute")
async def create_claude_prompt(request: Request, body: CreateClaudePromptRequest):
    # Resume existing session unless caller requested a fresh one
    session_id: str | None = None
    if not body.new_session and body.project_path:
        session_id = session_store.get(body.project_path)

    command = build_claude_command(
        body.prompt, body.project_path, settings.PROJECTS_ROOT, session_id
    )
    project_label = Path(body.project_path).name if body.project_path else "—"
    session_label = f" · sesión {session_id[:8]}" if session_id else ""
    task = Task(
        name=body.prompt[:60],
        command=command,
        description=(
            f"Claude Code @ {project_label}{session_label}"
            if body.project_path
            else "Claude Code prompt"
        ),
    )
    task_store.add(task)
    await manager.broadcast({"type": "task_created", "task": task.model_dump()})
    audit.info(
        "claude_prompt_created id=%s project=%r session=%r ip=%s",
        task.id[:8], body.project_path, session_id, _ip(request),
    )
    return task


@router.post("/tasks/{task_id}/approve", summary="Approve or reject a pending task")
@limiter.limit("30/minute")
async def approve_task(request: Request, task_id: str, body: ApproveTaskRequest):
    task = task_store.get(task_id)
    if not task:
        raise HTTPException(404, f"Task '{task_id}' not found")
    if task.status != TaskStatus.PENDING_APPROVAL:
        raise HTTPException(400, f"Task status is '{task.status}', expected 'pending_approval'")

    if body.action == "approve":
        task.status = TaskStatus.QUEUED
        task_store.update(task)
        await manager.broadcast({"type": "task_updated", "task": task.model_dump()})
        # Extract project_path from command so executor can update session_store
        project_path = _extract_project_path(task.command)
        run_task(task, project_path)
        audit.info(
            "task_approved id=%s name=%r ip=%s",
            task.id[:8], task.name, _ip(request),
        )
        return {"ok": True, "message": "Task approved and queued for execution"}

    task.status = TaskStatus.REJECTED
    task.reject_reason = body.reason
    task_store.update(task)
    await manager.broadcast({"type": "task_updated", "task": task.model_dump()})
    audit.info(
        "task_rejected id=%s name=%r reason=%r ip=%s",
        task.id[:8], task.name, body.reason, _ip(request),
    )
    return {"ok": True, "message": "Task rejected"}


@router.delete("/tasks/{task_id}", summary="Delete a task")
@limiter.limit("30/minute")
async def delete_task(request: Request, task_id: str):
    if not task_store.delete(task_id):
        raise HTTPException(404, f"Task '{task_id}' not found")
    await manager.broadcast({"type": "task_deleted", "task_id": task_id})
    audit.info("task_deleted id=%s ip=%s", task_id[:8], _ip(request))
    return {"ok": True}


# ── Session endpoints ─────────────────────────────────────────────────────────

@router.get("/sessions", response_model=dict[str, str], summary="List active Claude sessions")
@limiter.limit("60/minute")
def list_sessions(request: Request):
    return session_store.all()


@router.delete("/sessions", summary="Clear a Claude session by project path")
@limiter.limit("30/minute")
async def clear_session(request: Request, project_path: str):
    deleted = session_store.delete(project_path)
    if deleted:
        await manager.broadcast({"type": "session_deleted", "project_path": project_path})
    return {"ok": True, "deleted": deleted}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _extract_project_path(command: str) -> str:
    """Best-effort extraction of the cd target from a claude command string."""
    import re
    m = re.search(r'cd(?:\s+/d)?\s+"([^"]+)"', command)
    return m.group(1) if m else ""
