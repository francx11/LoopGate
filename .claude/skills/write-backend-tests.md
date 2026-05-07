# Skill: Write Backend Tests

## When to apply
Adding pytest tests for FastAPI routes, store logic, or the task executor. CI runs `pytest tests/ -v` — no tests exist yet.

## Setup (first time)

```bash
cd backend
pip install httpx pytest pytest-asyncio  # not in requirements.txt yet
# Add to requirements.txt after confirming they work
```

Create `backend/tests/__init__.py` (empty) and `backend/tests/conftest.py`:
```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.store import store

@pytest.fixture(autouse=True)
def reset_store():
    store._tasks.clear()
    yield
    store._tasks.clear()

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
```

## Writing a route test

`backend/tests/test_tasks.py`:
```python
import pytest

@pytest.mark.asyncio
async def test_create_task(client):
    res = await client.post("/api/v1/tasks", json={
        "name": "Test",
        "command": "echo hello",
        "description": "",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "pending_approval"
    assert len(data["id"]) == 8

@pytest.mark.asyncio
async def test_approve_task(client):
    create = await client.post("/api/v1/tasks", json={"name": "T", "command": "echo 1", "description": ""})
    task_id = create.json()["id"]

    approve = await client.post(f"/api/v1/tasks/{task_id}/approve", json={"approve": True})
    assert approve.status_code == 200
    assert approve.json()["status"] == "queued"

@pytest.mark.asyncio
async def test_reject_task(client):
    create = await client.post("/api/v1/tasks", json={"name": "T", "command": "echo 1", "description": ""})
    task_id = create.json()["id"]

    reject = await client.post(f"/api/v1/tasks/{task_id}/approve", json={"approve": False, "reason": "no"})
    assert reject.json()["status"] == "rejected"
```

## Writing a store unit test

`backend/tests/test_store.py`:
```python
from app.core.store import store
from app.models.task import Task

def test_store_add_and_get():
    task = Task(id="abc12345", name="T", command="ls", description="")
    store.add(task)
    assert store.get("abc12345").name == "T"

def test_store_list():
    store._tasks.clear()
    task = Task(id="xyz99999", name="T2", command="pwd", description="")
    store.add(task)
    assert len(store.list()) == 1
```

## Run tests

```bash
cd backend
python -m pytest tests/ -v
```

## What not to do
- Don't test the executor subprocess directly in unit tests — it shells out and is slow/flaky; test the store and routes instead
- Don't share state between tests — `autouse` fixture in conftest clears the store
- [HUMAN APPROVAL REQUIRED] Don't add `httpx` or `pytest-asyncio` to `requirements.txt` without confirming — they affect the production image if Dockerfile is added later; consider a `requirements-dev.txt`
- Don't use `requests` library — FastAPI async tests require `httpx` with `ASGITransport`
