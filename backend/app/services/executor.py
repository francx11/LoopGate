"""
Task execution service.
Runs commands in subprocesses and streams output via WebSocket.
"""

import os
import subprocess
import threading
import traceback
from datetime import datetime
from pathlib import Path


# Strip known secrets/session vars — pass everything else through intact.
_SECRET_DENYLIST = {
    "SECRET_TOKEN",
    "CLAUDECODE", "CLAUDE_CODE_SESSION_ID", "CLAUDE_CODE_ENTRYPOINT",
    "CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING", "AI_AGENT",
    "CLAUDE_AGENT_SDK_VERSION", "MCP_CONNECTION_NONBLOCKING",
    "VSCODE_IPC_HOOK", "VSCODE_PID",
    "CHROME_CRASHPAD_PIPE_NAME",
}


def _build_env() -> dict:
    env = {k: v for k, v in os.environ.items() if k not in _SECRET_DENYLIST}
    path = env.get("PATH", "")

    if os.name == "nt":
        npm_global = str(Path.home() / "AppData" / "Roaming" / "npm")
        if npm_global not in path:
            env["PATH"] = npm_global + os.pathsep + path
    else:
        extra = [
            str(Path.home() / ".npm-global" / "bin"),
            str(Path.home() / ".local" / "bin"),
            "/usr/local/bin",
        ]
        additions = [p for p in extra if p not in path]
        if additions:
            env["PATH"] = os.pathsep.join(additions) + os.pathsep + path

    return env

from app.core.store import task_store
from app.core.ws_manager import manager
from app.models.task import Task, TaskStatus, LogLine


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _emit(task: Task, task_id: str, text: str):
    line = LogLine(time=_now(), text=text)
    task.log.append(line)
    task_store.update(task)
    manager.broadcast_sync({"type": "task_log", "task_id": task_id, "line": line.model_dump()})


def _run(task_id: str):
    task = task_store.get(task_id)
    if not task:
        return

    task.status = TaskStatus.RUNNING
    task.started_at = _now()
    task_store.update(task)
    manager.broadcast_sync({"type": "task_updated", "task": task.model_dump()})

    cwd = str(Path.home())
    _emit(task, task_id, f"[loopgate] cwd={cwd}")
    _emit(task, task_id, f"[loopgate] cmd={task.command}")

    try:
        process = subprocess.Popen(
            task.command,
            shell=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd,
            env=_build_env(),
        )

        def _drain_stderr():
            for raw in iter(process.stderr.readline, ""):
                _emit(task, task_id, f"[stderr] {raw.rstrip()}")

        stderr_thread = threading.Thread(target=_drain_stderr, daemon=True)
        stderr_thread.start()

        for raw_line in iter(process.stdout.readline, ""):
            _emit(task, task_id, raw_line.rstrip())

        process.wait()
        stderr_thread.join(timeout=5)
        task.exit_code = process.returncode
        task.status = TaskStatus.DONE if process.returncode == 0 else TaskStatus.ERROR

    except Exception as exc:
        traceback.print_exc()
        _emit(task, task_id, f"[loopgate] EXCEPTION: {exc}")
        task.status = TaskStatus.ERROR
        task.exit_code = -1

    task.finished_at = _now()
    _emit(task, task_id, f"[loopgate] exit={task.exit_code} status={task.status}")
    task_store.update(task)
    manager.broadcast_sync({"type": "task_updated", "task": task.model_dump()})


def run_task(task: Task):
    """Kick off task execution in a background thread."""
    thread = threading.Thread(target=_run, args=(task.id,), daemon=True)
    thread.start()
