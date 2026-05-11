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


# Only expose OS-level variables to subprocesses — never secrets or tokens.
_WINDOWS_WHITELIST = {
    "PATH", "PATHEXT", "TEMP", "TMP", "USERPROFILE", "HOME",
    "COMSPEC", "SystemRoot", "SystemDrive", "WINDIR", "OS",
    "APPDATA", "LOCALAPPDATA", "USERNAME", "COMPUTERNAME",
    "PROCESSOR_ARCHITECTURE", "TERM", "LANG", "LC_ALL",
}
_POSIX_WHITELIST = {
    "PATH", "HOME", "USER", "LOGNAME", "SHELL",
    "TERM", "LANG", "LC_ALL", "LC_CTYPE",
    "XDG_RUNTIME_DIR", "TMPDIR", "TMP", "TEMP",
}


def _build_env() -> dict:
    whitelist = _WINDOWS_WHITELIST if os.name == "nt" else _POSIX_WHITELIST
    env = {k: v for k, v in os.environ.items() if k in whitelist}
    path = env.get("PATH", "")

    if os.name == "nt":
        # Windows: add global npm directory so `claude` is reachable
        npm_global = str(Path.home() / "AppData" / "Roaming" / "npm")
        if npm_global not in path:
            env["PATH"] = npm_global + os.pathsep + path
    else:
        # POSIX: add common user-local bin directories
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
            env=_build_env(),
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
        traceback.print_exc()
        task.log.append(LogLine(time=_now(), text=f"LOOPGATE ERROR: {exc}"))
        task.status = TaskStatus.ERROR
        task.exit_code = -1

    task.finished_at = _now()
    # If the process failed silently (e.g. cd to nonexistent dir on Windows),
    # add the exit code so the user sees something in the log panel.
    if task.status == TaskStatus.ERROR and not task.log:
        task.log.append(LogLine(time=_now(), text=f"[exit code {task.exit_code}]"))
    task_store.update(task)
    manager.broadcast_sync({"type": "task_updated", "task": task.model_dump()})


def run_task(task: Task):
    """Kick off task execution in a background thread."""
    thread = threading.Thread(target=_run, args=(task.id,), daemon=True)
    thread.start()
