# Loopgate API Documentation

Base URL: `https://YOUR-SERVER/api/v1`  
Interactive Swagger UI: `https://YOUR-SERVER/docs`  
ReDoc: `https://YOUR-SERVER/redoc`

---

## Authentication

Authentication is optional. If `SECRET_TOKEN` is set in `.env`, include it in every request:

```
Authorization: Bearer YOUR_SECRET_TOKEN
```

---

## Tasks

### `GET /tasks`

Returns all tasks sorted by creation date.

**Response `200`**
```json
[
  {
    "id": "a3f9c1b2",
    "name": "Deploy to production",
    "command": "npm run deploy",
    "description": "Full production deploy",
    "status": "pending_approval",
    "created_at": "2025-06-15 14:32:01",
    "started_at": null,
    "finished_at": null,
    "exit_code": null,
    "reject_reason": null,
    "log": []
  }
]
```

---

### `GET /tasks/{task_id}`

Get a single task including its full log.

**Parameters**
| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `task_id` | path | string | ✅ | 8-char task ID |

**Response `200`** — Task object (see schema above)  
**Response `404`** — Task not found

---

### `POST /tasks`

Create a new task. The task will be created in `pending_approval` status and broadcast to all connected WebSocket clients.

**Request body**
```json
{
  "name": "string",        // required, max 120 chars
  "command": "string",     // required, shell command to execute
  "description": "string"  // optional, max 300 chars
}
```

**Response `201`** — Created Task object  
**Response `422`** — Validation error

**Example**
```bash
curl -X POST https://YOUR-SERVER/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Run migrations",
    "command": "python manage.py migrate --no-input",
    "description": "Apply pending database migrations"
  }'
```

---

### `POST /tasks/{task_id}/approve`

Approve or reject a task that is in `pending_approval` status.

- **Approving** transitions the task to `queued` → `running` and begins execution
- **Rejecting** transitions the task to `rejected`

**Parameters**
| Name | In | Type | Required |
|------|----|------|----------|
| `task_id` | path | string | ✅ |

**Request body**
```json
{
  "action": "approve",   // "approve" or "reject"
  "reason": "string"     // optional, used when rejecting
}
```

**Response `200`**
```json
{ "ok": true, "message": "Task approved and queued for execution" }
```

**Response `400`** — Task is not in `pending_approval` status  
**Response `404`** — Task not found

---

### `DELETE /tasks/{task_id}`

Delete a task and its log. The deletion is broadcast to all WebSocket clients.

**Response `200`** `{ "ok": true }`  
**Response `404`** — Task not found

---

## Health

### `GET /health`

```json
{
  "status": "ok",
  "version": "0.1.0",
  "tasks": 3
}
```

---

## WebSocket

**Endpoint:** `ws://YOUR-SERVER:8765`

On connection, the server immediately sends an `init` event with the full task list.

### Event reference

#### `init` — Initial state
```json
{
  "type": "init",
  "tasks": [ ...Task[] ]
}
```

#### `task_created` — New task added
```json
{
  "type": "task_created",
  "task": { ...Task }
}
```

#### `task_updated` — Task status changed
```json
{
  "type": "task_updated",
  "task": { ...Task }
}
```

#### `task_log` — New log line from a running task
```json
{
  "type": "task_log",
  "task_id": "a3f9c1b2",
  "line": {
    "time": "2025-06-15 14:32:45",
    "text": "Build successful"
  }
}
```

#### `task_deleted` — Task removed
```json
{
  "type": "task_deleted",
  "task_id": "a3f9c1b2"
}
```

---

## Task Status Flow

```
                    ┌─────────────────┐
   POST /tasks ───► │ pending_approval │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
           approve                       reject
              │                             │
         ┌────▼─────┐                 ┌─────▼────┐
         │  queued  │                 │ rejected │
         └────┬─────┘                 └──────────┘
              │
         ┌────▼─────┐
         │ running  │
         └────┬─────┘
              │
    ┌─────────┴──────────┐
 exit 0                exit ≠ 0
    │                      │
┌───▼───┐             ┌────▼────┐
│ done  │             │  error  │
└───────┘             └─────────┘
```

---

## Python SDK (minimal)

```python
import requests, time

class LoopgateClient:
    def __init__(self, base_url: str, token: str = ""):
        self.base = base_url.rstrip("/") + "/api/v1"
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}

    def create_task(self, name: str, command: str, description: str = "") -> dict:
        return requests.post(f"{self.base}/tasks", json={
            "name": name, "command": command, "description": description
        }, headers=self.headers).json()

    def get_task(self, task_id: str) -> dict:
        return requests.get(f"{self.base}/tasks/{task_id}", headers=self.headers).json()

    def wait_for_completion(self, task_id: str, poll_interval: float = 2.0) -> str:
        """Block until task reaches a terminal state. Returns final status."""
        terminal = {"done", "error", "rejected"}
        while True:
            task = self.get_task(task_id)
            if task["status"] in terminal:
                return task["status"]
            time.sleep(poll_interval)

    def run(self, name: str, command: str, description: str = "") -> str:
        """Create task and wait for human approval + execution."""
        task = self.create_task(name, command, description)
        print(f"⏳ Waiting for approval: {task['id']}")
        return self.wait_for_completion(task["id"])


# Usage
client = LoopgateClient("https://YOUR-NGROK-URL")
status = client.run("Deploy", "npm run deploy:prod")
print(f"Final status: {status}")
```
