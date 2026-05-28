# 🔁 Loopgate

> **Human-in-the-loop approval layer for AI agent tasks.**  
> Monitor, approve, and control your AI agent's actions from anywhere in the world — right from your phone.

[![CI](https://github.com/francx11/loopgate/actions/workflows/ci.yml/badge.svg)](https://github.com/francx11/loopgate/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://react.dev)

---

## 🧠 What is Loopgate?

Modern AI coding agents like Claude Code, Cursor, or custom LLM agents can execute tasks autonomously. But sometimes you need a human to review and approve actions before they run — especially for risky operations like deployments, database migrations, or file deletions.

**Loopgate** is the bridge: a lightweight server that sits between your AI agent and execution, exposing a mobile-friendly dashboard so you can approve or reject tasks from anywhere in the world.

```
AI Agent ──► Loopgate Server ──► [ Pending Approval ] ──► Your Phone
                                         │
                              ┌──────────┴──────────┐
                           Approve               Reject
                              │
                         [ Execute ] ──► Real-time log stream
```

---

## ✨ Features

- 📋 **Task queue** — Create tasks with name, description, and command
- ✅ **Mobile approval flow** — Approve or reject from any device, anywhere
- ⚡ **Real-time logs** — Stream command output line by line via WebSocket
- 🤖 **Claude Code integration** — Submit natural-language prompts; Loopgate builds the command, tracks sessions, and streams output
- 🔄 **Session continuity** — Claude Code sessions persist across tasks per project path
- 🌐 **Remote access** — Works over the network via Tailscale or ngrok
- 🔌 **REST + WebSocket API** — Integrate with any AI agent or automation tool
- 🪟 **Cross-platform** — Works on macOS, Linux, and Windows 10+
- 🔒 **Auth token + rate limiting** — Protect your server; docs hidden when token is active
- 🛡️ **Security headers** — CSP, X-Frame-Options, HSTS (on HTTPS), and more

---

## 🏗️ Architecture

Single-port design: the React frontend is compiled into `frontend/dist/` and served by FastAPI on the same port as the REST and WebSocket APIs.

```
┌──────────────────────────────────────────────────────────┐
│                    Loopgate Server (PC)                   │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  FastAPI :8001                                       │ │
│  │  ├── GET/POST/DELETE  /api/v1/tasks                  │ │
│  │  ├── GET              /api/v1/projects               │ │
│  │  ├── GET/DELETE       /api/v1/sessions               │ │
│  │  ├── WS               /ws  (real-time events)        │ │
│  │  ├── GET              /health                        │ │
│  │  └── *                /  (React SPA)                 │ │
│  └────────────────────┬────────────────────────────────┘ │
│                        │                                  │
│  ┌─────────────────────▼────────────────────────────────┐ │
│  │  TaskStore (in-memory, thread-safe)                  │ │
│  │  SessionStore (project → Claude session ID)          │ │
│  └─────────────────────┬────────────────────────────────┘ │
│                        │                                  │
│  ┌─────────────────────▼────────────────────────────────┐ │
│  │  TaskExecutor (background thread)                    │ │
│  │  subprocess.Popen → streams stdout/stderr to WS      │ │
│  └──────────────────────────────────────────────────────┘ │
└──────────────────────────┬───────────────────────────────┘
                           │ Tailscale / ngrok
                           │
                  ┌────────▼────────┐
                  │  Mobile React   │
                  │  Dashboard      │
                  └─────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- [Tailscale](https://tailscale.com) (recommended) or [ngrok](https://ngrok.com)

### Windows — one-shot launch

```bat
./start.bat
```

Builds the frontend, starts the backend, and prints the access URL (Tailscale IP or ngrok tunnel).

### Manual setup

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate        # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run.py                # starts on :8001
```

### Access from your phone

**Option A — Tailscale (recommended):**  
Install Tailscale on both your PC and phone. Join the same account.  
Open `http://<tailscale-ip>:8001` on your phone — the app auto-connects.

**Option B — ngrok:**
```bash
ngrok http 8001
```
Open the `https://xxx.ngrok-free.app` URL on your phone.

> The frontend is compiled into `frontend/dist/` and served by FastAPI on the same port. No separate server needed in production.

---

## 📱 Usage

### From an AI agent / script

```bash
# Create a task (it will wait for your approval on mobile)
curl -X POST http://YOUR-HOST:8001/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Deploy to production",
    "command": "cd /app && git pull && npm run build && pm2 restart app",
    "description": "Full production deploy"
  }'

# Response:
# { "id": "a3f9c1b2", "status": "pending_approval", ... }
```

Now pick up your phone, open Loopgate, and tap ✅ Approve or 🚫 Reject.

### Python integration

```python
import requests, time

LOOPGATE = "http://YOUR-HOST:8001"

def run_with_approval(name: str, command: str) -> bool:
    """Submit a task and block until it completes or is rejected."""
    task = requests.post(f"{LOOPGATE}/api/v1/tasks", json={
        "name": name,
        "command": command,
    }).json()

    task_id = task["id"]
    print(f"⏳ Task '{name}' waiting for approval (id: {task_id})")

    while True:
        status = requests.get(f"{LOOPGATE}/api/v1/tasks/{task_id}").json()["status"]
        if status == "done":
            return True
        if status in ("error", "rejected"):
            return False
        time.sleep(2)

success = run_with_approval(
    name="Database migration",
    command="python manage.py migrate"
)
print("✅ Done" if success else "❌ Failed or rejected")
```

---

## 📡 API Reference

Full interactive docs available at `http://localhost:8001/docs` when the server is running (hidden when `SECRET_TOKEN` is set).

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Server health + `auth_required` flag |
| `GET` | `/api/v1/tasks` | List all tasks |
| `GET` | `/api/v1/tasks/{id}` | Get task details + log |
| `POST` | `/api/v1/tasks` | Create a task |
| `POST` | `/api/v1/tasks/{id}/approve` | Approve or reject a task |
| `DELETE` | `/api/v1/tasks/{id}` | Delete a task |
| `POST` | `/api/v1/tasks/claude-prompt` | Create a Claude Code task from a natural-language prompt |
| `GET` | `/api/v1/projects` | List directories inside `PROJECTS_ROOT` |
| `GET` | `/api/v1/sessions` | List active Claude Code sessions |
| `DELETE` | `/api/v1/sessions?project_path=...` | Clear a Claude session by project path |

### POST /api/v1/tasks

```json
{
  "name": "string",
  "command": "string",
  "description": "string (optional)"
}
```

### POST /api/v1/tasks/{id}/approve

```json
{
  "action": "approve | reject",
  "reason": "string (optional, for rejections)"
}
```

### POST /api/v1/tasks/claude-prompt

Builds a `claude --output-format stream-json` command server-side and queues it for approval.

```json
{
  "prompt": "string (1–2000 chars, no shell metacharacters)",
  "project_path": "string (optional, must be inside PROJECTS_ROOT)",
  "new_session": false
}
```

When `new_session` is `false` (default), an existing session for `project_path` is resumed automatically.

### WebSocket Events

Connect to `ws://HOST:8001/ws`

| Event | Direction | Payload |
|-------|-----------|---------|
| `init` | server → client | `{ tasks: Task[] }` |
| `task_created` | server → client | `{ task: Task }` |
| `task_updated` | server → client | `{ task: Task }` |
| `task_log` | server → client | `{ task_id, line: { time, text } }` |
| `task_deleted` | server → client | `{ task_id }` |
| `session_deleted` | server → client | `{ project_path }` |

### Task object

```typescript
{
  id: string               // 8-char unique ID
  name: string
  command: string
  description: string
  status: "pending_approval" | "queued" | "running" | "done" | "error" | "rejected"
  created_at: string       // "YYYY-MM-DD HH:MM:SS"
  started_at: string | null
  finished_at: string | null
  exit_code: number | null
  reject_reason: string | null
  log: { time: string, text: string }[]
}
```

---

## ⚙️ Configuration

All settings can be set via environment variables or a `.env` file in the `backend/` directory.

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8001` | Port the server listens on |
| `HOST` | `0.0.0.0` | Bind address |
| `SECRET_TOKEN` | _(empty)_ | Bearer token required on all API requests when set |
| `CORS_ORIGINS` | _(empty)_ | Comma-separated allowed origins (empty = allow all) |
| `PROJECTS_ROOT` | `~/Documents/Projects` (Win) / `~/projects` | Root for project discovery |
| `LOG_LEVEL` | `info` | Uvicorn log level |

---

## 🗺️ Roadmap

- [ ] Persistent storage (SQLite)
- [ ] Push notifications (mobile)
- [ ] Authentication (JWT)
- [ ] Task scheduling / cron
- [ ] Slack / Telegram bot integration
- [ ] Task templates
- [ ] Multi-user support

---

## 🤝 Contributing

Contributions are welcome! Please open an issue first to discuss what you'd like to change.

```bash
# Run backend tests
cd backend && pytest

# Run frontend in dev mode
cd frontend && npm run dev

# Production build
cd frontend && npm run build
```

---

## 📄 License

MIT © 2025 — See [LICENSE](LICENSE) for details.
