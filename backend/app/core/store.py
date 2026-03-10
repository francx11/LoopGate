"""
Thread-safe in-memory task store.
Can be swapped for a persistent backend (SQLite, Redis) in future versions.
"""

import threading
from typing import Dict, List, Optional
from app.models.task import Task


class TaskStore:
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


task_store = TaskStore()
