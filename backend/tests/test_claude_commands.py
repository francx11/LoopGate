"""Unit tests for server-side Claude command builder."""

import os
import pytest
from fastapi import HTTPException

from app.models.claude import build_claude_command, CreateClaudePromptRequest


def test_build_no_project_path(tmp_path):
    cmd = build_claude_command("Add tests", "", str(tmp_path))
    assert '--output-format stream-json --verbose --dangerously-skip-permissions' in cmd
    assert '-p "Add tests"' in cmd
    assert "cd" not in cmd


def test_build_with_valid_project(tmp_path):
    project = tmp_path / "myapp"
    project.mkdir()
    cmd = build_claude_command("Fix bug", str(project), str(tmp_path))
    assert "cd" in cmd
    assert "claude" in cmd


def test_build_rejects_path_outside_root(tmp_path):
    with pytest.raises(HTTPException) as exc:
        build_claude_command("test", "/etc/passwd", str(tmp_path))
    assert exc.value.status_code == 400


def test_build_rejects_nonexistent_path(tmp_path):
    with pytest.raises(HTTPException) as exc:
        build_claude_command("test", str(tmp_path / "nope"), str(tmp_path))
    assert exc.value.status_code == 400


def test_prompt_validator_blocks_injection():
    with pytest.raises(Exception):
        CreateClaudePromptRequest(prompt="echo hi && rm -rf /", project_path="")


def test_prompt_validator_blocks_backtick():
    with pytest.raises(Exception):
        CreateClaudePromptRequest(prompt="do `rm -rf /`", project_path="")


def test_prompt_validator_blocks_dollar():
    with pytest.raises(Exception):
        CreateClaudePromptRequest(prompt="value is $(id)", project_path="")


def test_prompt_allows_normal_text():
    req = CreateClaudePromptRequest(
        prompt="Add unit tests for the authentication module",
        project_path="",
    )
    assert req.prompt.startswith("Add")


def test_prompt_escapes_double_quotes():
    cmd = build_claude_command('say "hello"', "", "/")
    assert '\\"hello\\"' in cmd
