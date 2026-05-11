"""CRUD + approval flow tests for the /api/v1/tasks endpoints."""

import json
import pytest
from fastapi.testclient import TestClient


# ── helpers ──────────────────────────────────────────────────────────────────

def _create(client: TestClient, name="Deploy", command="echo hi", description=""):
    return client.post(
        "/api/v1/tasks",
        json={"name": name, "command": command, "description": description},
    )


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── creation ─────────────────────────────────────────────────────────────────

def test_create_task_open_mode(client, without_token):
    r = _create(client)
    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "pending_approval"
    assert data["command"] == "echo hi"


def test_create_task_without_token_returns_401(client, with_token):
    r = client.post("/api/v1/tasks", json={"name": "x", "command": "y"})
    assert r.status_code == 401


def test_create_task_with_valid_token(client, with_token):
    r = client.post(
        "/api/v1/tasks",
        json={"name": "Deploy", "command": "echo ok"},
        headers=_auth_headers(with_token),
    )
    assert r.status_code == 201


def test_list_tasks_empty(client, without_token):
    r = client.get("/api/v1/tasks")
    assert r.status_code == 200
    assert r.json() == []


def test_get_task_not_found(client, without_token):
    r = client.get("/api/v1/tasks/nonexistent")
    assert r.status_code == 404


# ── approval flow ─────────────────────────────────────────────────────────────

def test_approve_task(client, without_token):
    task_id = _create(client).json()["id"]
    r = client.post(f"/api/v1/tasks/{task_id}/approve", json={"action": "approve"})
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_reject_task(client, without_token):
    task_id = _create(client).json()["id"]
    r = client.post(
        f"/api/v1/tasks/{task_id}/approve",
        json={"action": "reject", "reason": "too risky"},
    )
    assert r.status_code == 200
    task = client.get(f"/api/v1/tasks/{task_id}").json()
    assert task["status"] == "rejected"
    assert task["reject_reason"] == "too risky"


def test_cannot_approve_twice(client, without_token):
    task_id = _create(client).json()["id"]
    client.post(f"/api/v1/tasks/{task_id}/approve", json={"action": "approve"})
    r = client.post(f"/api/v1/tasks/{task_id}/approve", json={"action": "approve"})
    assert r.status_code == 400


def test_approve_missing_task(client, without_token):
    r = client.post("/api/v1/tasks/missing/approve", json={"action": "approve"})
    assert r.status_code == 404


# ── delete ────────────────────────────────────────────────────────────────────

def test_delete_task(client, without_token):
    task_id = _create(client).json()["id"]
    r = client.delete(f"/api/v1/tasks/{task_id}")
    assert r.status_code == 200
    assert client.get(f"/api/v1/tasks/{task_id}").status_code == 404


def test_delete_missing_task(client, without_token):
    assert client.delete("/api/v1/tasks/nope").status_code == 404


# ── Claude prompt endpoint ────────────────────────────────────────────────────

def test_claude_prompt_creates_task(client, without_token):
    r = client.post(
        "/api/v1/tasks/claude-prompt",
        json={"prompt": "Add unit tests", "project_path": ""},
    )
    assert r.status_code == 201
    data = r.json()
    assert "claude" in data["command"]
    assert data["status"] == "pending_approval"


def test_claude_prompt_rejects_shell_injection(client, without_token):
    r = client.post(
        "/api/v1/tasks/claude-prompt",
        json={"prompt": "do something && rm -rf /", "project_path": ""},
    )
    assert r.status_code == 422


def test_claude_prompt_invalid_project_path(client, without_token):
    r = client.post(
        "/api/v1/tasks/claude-prompt",
        json={"prompt": "hello", "project_path": "C:/Windows/System32"},
    )
    assert r.status_code == 400


# ── health endpoint ───────────────────────────────────────────────────────────

def test_health(client, without_token):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["auth_required"] is False


def test_health_with_token_required(client, with_token):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["auth_required"] is True


# ── security headers ──────────────────────────────────────────────────────────

def test_security_headers_present(client, without_token):
    headers = client.get("/health").headers
    assert "content-security-policy" in headers
    assert "x-content-type-options" in headers
    assert "x-frame-options" in headers
