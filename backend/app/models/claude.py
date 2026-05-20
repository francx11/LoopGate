"""
Server-side builder for Claude Code shell commands.

Keeping command construction in the backend means the frontend only sends
structured data ({prompt, project_path}), never raw shell strings.
"""

import os
import re
from pathlib import Path

from fastapi import HTTPException
from pydantic import BaseModel, Field, field_validator

# Characters that are dangerous in Windows cmd.exe / POSIX shell context even
# when the prompt is placed inside double quotes.  We reject rather than escape
# to keep the validation surface simple and auditable.
_DANGEROUS = re.compile(r'[`$!]|&&|\|\|')


class CreateClaudePromptRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    project_path: str = Field("", max_length=512)
    new_session: bool = Field(False)

    @field_validator("prompt")
    @classmethod
    def prompt_no_shell_injection(cls, v: str) -> str:
        if _DANGEROUS.search(v):
            raise ValueError(
                "Prompt contains shell metacharacters (`$!&&||`). "
                "Rephrase without them."
            )
        return v


def _validate_project_path(project_path: str, projects_root: str) -> Path | None:
    """Return the resolved Path if safe, None if empty, raise 400 if invalid."""
    if not project_path:
        return None
    root = Path(projects_root).resolve()
    target = Path(project_path).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        raise HTTPException(
            400,
            f"project_path must be inside PROJECTS_ROOT ({root})",
        )
    if not target.exists():
        raise HTTPException(400, f"Project path does not exist: {target}")
    return target


def build_claude_command(
    prompt: str,
    project_path: str,
    projects_root: str,
    session_id: str | None = None,
) -> str:
    """Construct a safe claude --output-format stream-json -p '...' command."""
    safe_path = _validate_project_path(project_path, projects_root)

    # Escape double-quotes inside the prompt (works for both cmd.exe + POSIX sh)
    escaped = prompt.replace("\\", "\\\\").replace('"', '\\"')

    flags = "--output-format stream-json --dangerously-skip-permissions"
    if session_id:
        safe_sid = session_id.replace('"', "")
        flags += f' --resume "{safe_sid}"'

    claude_cmd = f'claude {flags} -p "{escaped}"'

    if safe_path is None:
        return claude_cmd

    if os.name == "nt":
        return f'cd /d "{safe_path}" && {claude_cmd}'
    return f'cd "{safe_path}" && {claude_cmd}'
