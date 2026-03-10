"""
Task execution service.
Runs commands in subprocesses and streams output via WebSocket.
"""

import subprocess
import threading
from datetime import datetime
from pathlib import Path

from app.core.store import task_store
from app.core.ws_manager import manager
from app.models.task import Task, TaskStatus, LogLine


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _run(task_id: str):
    task = task_store.get(task_id)
    if not task:
        return

    task.status = TaskStatus.RUNNING
    task.started_at = _now()
    task_store.update(task)
    manager.broadcast_sync({"type": "task_updated", "task": task.model_dump()})

    try:
        process = subprocess.Popen(
            task.command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(Path.home()),
        )

        for raw_line in iter(process.stdout.readline, ""):
            line = LogLine(time=_now(), text=raw_line.rstrip())
            task.log.append(line)
            task_store.update(task)
            manager.broadcast_sync({
                "type": "task_log",
                "task_id": task_id,
                "line": line.model_dump(),
            })

        process.wait()
        task.exit_code = process.returncode
        task.status = TaskStatus.DONE if process.returncode == 0 else TaskStatus.ERROR

    except Exception as exc:
        task.log.append(LogLine(time=_now(), text=f"LOOPGATE ERROR: {exc}"))
        task.status = TaskStatus.ERROR
        task.exit_code = -1

    task.finished_at = _now()
    task_store.update(task)
    manager.broadcast_sync({"type": "task_updated", "task": task.model_dump()})


def run_task(task: Task):
    """Kick off task execution in a background thread."""
    thread = threading.Thread(target=_run, args=(task.id,), daemon=True)
    thread.start()
