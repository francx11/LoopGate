import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.store import task_store
from app.main import app


@pytest.fixture
def token() -> str:
    return "test-secret-token-1234567890"


@pytest.fixture(autouse=True)
def reset_store():
    for task in task_store.all():
        task_store.delete(task.id)
    yield
    for task in task_store.all():
        task_store.delete(task.id)


@pytest.fixture
def with_token(monkeypatch, token):
    monkeypatch.setattr(settings, "SECRET_TOKEN", token)
    return token


@pytest.fixture
def without_token(monkeypatch):
    monkeypatch.setattr(settings, "SECRET_TOKEN", "")
    return None


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
