# Skill: Add Task Status or FSM Transition

## When to apply
Extending the task lifecycle: adding a new status value, a new transition (e.g., `paused`, `cancelled`), or a new approval action.

## Steps

### 1. Update the backend model

`backend/app/models/task.py` — extend the `TaskStatus` literal/enum:
```python
TaskStatus = Literal[
    "pending_approval",
    "queued",
    "running",
    "done",
    "error",
    "rejected",
    "my_new_status",   # add here
]
```

### 2. Add transition logic in the store

`backend/app/core/store.py` — add a method if the transition requires guarding:
```python
def cancel_task(self, task_id: str) -> Task | None:
    with self._lock:
        task = self._tasks.get(task_id)
        if not task or task.status not in ("queued", "pending_approval"):
            return None
        task.status = "my_new_status"
        return task
```

### 3. Expose via REST endpoint

`backend/app/api/tasks.py`:
```python
@router.post("/{task_id}/cancel")
async def cancel_task(task_id: str):
    task = store.cancel_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found or cannot be cancelled")
    await ws_manager.broadcast({"type": "task_updated", "task": task.model_dump()})
    return task
```

### 4. Update executor guard

`backend/app/services/executor.py` — if the executor must skip or handle the new status:
```python
if task.status != "queued":
    continue   # executor only runs queued tasks
```

### 5. Frontend: update TypeScript type

`frontend/src/services/api.ts` or the Task interface:
```typescript
export type TaskStatus =
  | "pending_approval" | "queued" | "running"
  | "done" | "error" | "rejected"
  | "my_new_status";  // add here
```

### 6. Frontend: render the new status

`frontend/src/components/TaskList.tsx` — add a badge/label case:
```typescript
const STATUS_LABEL: Record<TaskStatus, string> = {
  // ...existing
  my_new_status: "Cancelado",   // Spanish label
};
```

### 7. Update CLAUDE.md FSM diagram

Add the new arrow to the Task Status FSM section.

## What not to do
- [HUMAN APPROVAL REQUIRED] Don't add a transition that can interrupt a `running` process without also sending SIGTERM to the subprocess in `executor.py`
- Don't add status values without updating both backend `Literal` type AND frontend `TaskStatus` type — they will desync
- Don't allow arbitrary status strings from the client — always validate against the defined literal set
