from pathlib import Path

from fastapi import APIRouter, HTTPException
from typing import List

from app.core.config import settings
from app.core.store import task_store
from app.core.ws_manager import manager
from app.models.task import Task, TaskStatus, CreateTaskRequest, ApproveTaskRequest
from app.services.executor import run_task

router = APIRouter(tags=["tasks"])


@router.get("/projects", summary="List directories in PROJECTS_ROOT")
def list_projects():
    root = Path(settings.PROJECTS_ROOT)
    if not root.exists():
        return []
    return [
        {"name": d.name, "path": str(d)}
        for d in sorted(root.iterdir())
        if d.is_dir() and not d.name.startswith(".")
    ]


@router.get("/tasks", response_model=List[Task], summary="List all tasks")
def list_tasks():
    return task_store.all()


@router.get("/tasks/{task_id}", response_model=Task, summary="Get a single task")
def get_task(task_id: str):
    task = task_store.get(task_id)
    if not task:
        raise HTTPException(404, f"Task '{task_id}' not found")
    return task


@router.post("/tasks", response_model=Task, status_code=201, summary="Create a task")
async def create_task(body: CreateTaskRequest):
    task = Task(name=body.name, command=body.command, description=body.description)
    task_store.add(task)
    await manager.broadcast({"type": "task_created", "task": task.model_dump()})
    return task


@router.post("/tasks/{task_id}/approve", summary="Approve or reject a pending task")
async def approve_task(task_id: str, body: ApproveTaskRequest):
    task = task_store.get(task_id)
    if not task:
        raise HTTPException(404, f"Task '{task_id}' not found")
    if task.status != TaskStatus.PENDING_APPROVAL:
        raise HTTPException(400, f"Task status is '{task.status}', expected 'pending_approval'")

    if body.action == "approve":
        task.status = TaskStatus.QUEUED
        task_store.update(task)
        await manager.broadcast({"type": "task_updated", "task": task.model_dump()})
        run_task(task)
        return {"ok": True, "message": "Task approved and queued for execution"}

    task.status = TaskStatus.REJECTED
    task.reject_reason = body.reason
    task_store.update(task)
    await manager.broadcast({"type": "task_updated", "task": task.model_dump()})
    return {"ok": True, "message": "Task rejected"}


@router.delete("/tasks/{task_id}", summary="Delete a task")
async def delete_task(task_id: str):
    if not task_store.delete(task_id):
        raise HTTPException(404, f"Task '{task_id}' not found")
    await manager.broadcast({"type": "task_deleted", "task_id": task_id})
    return {"ok": True}
