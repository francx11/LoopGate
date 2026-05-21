"""
Task execution service.
Runs commands in subprocesses and streams output via WebSocket.
"""

import json
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

from app.core.store import task_store, session_store
from app.core.ws_manager import manager
from app.models.task import Task, TaskStatus, LogLine


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _emit(task: Task, task_id: str, text: str):
    line = LogLine(time=_now(), text=text)
    task.log.append(line)
    task_store.update(task)
    manager.broadcast_sync({"type": "task_log", "task_id": task_id, "line": line.model_dump()})


def _parse_stream_event(raw: str) -> tuple[str | None, str | None, float | None]:
    """
    Parse one stream-json event line.
    Returns (display_text, session_id, cost_usd).
    Any field may be None if not present/applicable.
    """
    try:
        ev = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return raw, None, None  # plain text — display as-is

    t = ev.get("type", "")
    session_id: str | None = ev.get("session_id")
    cost_usd: float | None = None
    display: str | None = None

    if t == "system":
        # init event — only extract session_id, nothing to display
        pass

    elif t == "assistant":
        msg = ev.get("message", {})
        texts = [
            block["text"]
            for block in msg.get("content", [])
            if block.get("type") == "text" and block.get("text", "").strip()
        ]
        display = "\n".join(texts) or None

    elif t == "tool_use":
        name = ev.get("name", "?")
        inp = ev.get("input", {})
        # Show the most meaningful input field as a short preview
        preview = ""
        for key in ("file_path", "path", "command", "query", "pattern", "content"):
            if key in inp:
                preview = str(inp[key])[:120]
                break
        if not preview and inp:
            preview = str(next(iter(inp.values())))[:120]
        display = f"[→ {name}] {preview}" if preview else f"[→ {name}]"

    elif t == "tool_result":
        content = ev.get("content", [])
        if isinstance(content, list):
            parts = [b.get("text", "") for b in content if b.get("type") == "text"]
            text = "\n".join(p for p in parts if p)
        elif isinstance(content, str):
            text = content
        else:
            text = ""
        if text.strip():
            first_line = text.strip().split("\n")[0][:120]
            display = f"[✓] {first_line}"

    elif t == "result":
        cost_usd = ev.get("cost_usd") or ev.get("total_cost_usd")
        result_text = ev.get("result", "").strip()
        subtype = ev.get("subtype", "")
        if subtype == "error_during_execution":
            display = f"[error] {result_text[:300]}" if result_text else "[error]"
        elif result_text:
            display = f"[resultado] {result_text[:300]}"

    # For unknown types just skip display

    return display, session_id, cost_usd


def _run(task_id: str, project_path: str = ""):
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

    collected_session_id: str | None = None
    collected_cost: float | None = None
    collected_result: str | None = None

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

        is_claude_cmd = "--output-format stream-json" in task.command
        stderr_buffer: list[str] = []

        def _drain_stderr():
            for raw in iter(process.stderr.readline, ""):
                line = raw.rstrip()
                if line:
                    stderr_buffer.append(line)
                    if not is_claude_cmd:
                        _emit(task, task_id, f"[stderr] {line}")

        stderr_thread = threading.Thread(target=_drain_stderr, daemon=True)
        stderr_thread.start()

        for raw_line in iter(process.stdout.readline, ""):
            line = raw_line.rstrip()
            if not line:
                continue
            display, sid, cost = _parse_stream_event(line)
            if sid:
                collected_session_id = sid
            if cost is not None:
                collected_cost = cost
            # Capture result text from "result" events
            try:
                ev = json.loads(line)
                if ev.get("type") == "result":
                    collected_result = ev.get("result", "").strip() or None
            except (json.JSONDecodeError, ValueError):
                pass
            if display:
                _emit(task, task_id, display)

        process.wait()
        stderr_thread.join(timeout=5)
        task.exit_code = process.returncode
        task.status = TaskStatus.DONE if process.returncode == 0 else TaskStatus.ERROR

        if is_claude_cmd and process.returncode != 0 and stderr_buffer:
            for line in stderr_buffer:
                _emit(task, task_id, f"[stderr] {line}")

    except Exception as exc:
        traceback.print_exc()
        _emit(task, task_id, f"[loopgate] EXCEPTION: {exc}")
        task.status = TaskStatus.ERROR
        task.exit_code = -1

    # Persist structured output fields
    if collected_session_id:
        task.claude_session_id = collected_session_id
        if project_path:
            session_store.set(project_path, collected_session_id)
            manager.broadcast_sync({
                "type": "session_updated",
                "project_path": project_path,
                "session_id": collected_session_id,
            })
    if collected_result:
        task.claude_result = collected_result
    if collected_cost is not None:
        task.claude_cost_usd = collected_cost

    task.finished_at = _now()
    cost_str = f" cost=${collected_cost:.4f}" if collected_cost else ""
    _emit(task, task_id, f"[loopgate] exit={task.exit_code} status={task.status}{cost_str}")
    task_store.update(task)
    manager.broadcast_sync({"type": "task_updated", "task": task.model_dump()})


def run_task(task: Task, project_path: str = ""):
    """Kick off task execution in a background thread."""
    thread = threading.Thread(target=_run, args=(task.id, project_path), daemon=True)
    thread.start()
