"""
Thread-safe task store with two backends:
  - memory (default): fast, no persistence, works everywhere
  - sqlite: optional persistence across restarts

Select via STORE_BACKEND env var ("memory" or "sqlite").
The public interface (add/get/update/delete/all) is identical for both.
"""

import json
import sqlite3
import threading
from typing import Dict, List, Optional

from app.core.config import settings
from app.models.task import Task


class _MemoryStore:
    def __init__(self):
        self._tasks: Dict[str, Task] = {}
        self._lock = threading.Lock()

    def add(self, task: Task) -> Task:
        with self._lock:
            self._tasks[task.id] = task
        return task

    def get(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def update(self, task: Task) -> Task:
        with self._lock:
            self._tasks[task.id] = task
        return task

    def delete(self, task_id: str) -> bool:
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                return True
        return False

    def all(self) -> List[Task]:
        return list(self._tasks.values())


class _SQLiteStore:
    def __init__(self, db_path: str):
        self._lock = threading.Lock()
        self._db_path = db_path
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    data TEXT NOT NULL
                )
            """)
            conn.commit()

    def _row_to_task(self, row) -> Task:
        return Task.model_validate_json(row["data"])

    def add(self, task: Task) -> Task:
        with self._lock:
            with self._conn() as conn:
                conn.execute(
                    "INSERT INTO tasks (id, data) VALUES (?, ?)",
                    (task.id, task.model_dump_json()),
                )
                conn.commit()
        return task

    def get(self, task_id: str) -> Optional[Task]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT data FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
        return self._row_to_task(row) if row else None

    def update(self, task: Task) -> Task:
        with self._lock:
            with self._conn() as conn:
                conn.execute(
                    "UPDATE tasks SET data = ? WHERE id = ?",
                    (task.model_dump_json(), task.id),
                )
                conn.commit()
        return task

    def delete(self, task_id: str) -> bool:
        with self._lock:
            with self._conn() as conn:
                changed = conn.execute(
                    "DELETE FROM tasks WHERE id = ?", (task_id,)
                ).rowcount
                conn.commit()
        return changed > 0

    def all(self) -> List[Task]:
        with self._conn() as conn:
            rows = conn.execute("SELECT data FROM tasks").fetchall()
        return [self._row_to_task(r) for r in rows]


def _make_store():
    backend = settings.STORE_BACKEND.lower()
    if backend == "sqlite":
        print(f"Loopgate store: SQLite at {settings.SQLITE_PATH}")
        return _SQLiteStore(settings.SQLITE_PATH)
    return _MemoryStore()


task_store = _make_store()
