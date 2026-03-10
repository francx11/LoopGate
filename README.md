# 🔁 Loopgate

> **Human-in-the-loop approval layer for AI agent tasks.**  
> Monitor, approve, and control your AI agent's actions from anywhere in the world — right from your phone.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://react.dev)

---

## 🧠 What is Loopgate?

Modern AI coding agents like Kiro, Cursor, or custom LLM agents can execute tasks autonomously. But sometimes you need a human to review and approve actions before they run — especially for risky operations like deployments, database migrations, or file deletions.

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
- 🌐 **Remote access** — Works over the internet via ngrok tunnel
- 🔌 **REST + WebSocket API** — Integrate with any AI agent or automation tool
- 🪟 **Cross-platform** — Works on macOS, Linux, and Windows 10+
- 🔒 **Optional auth token** — Protect your server with a secret token

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Loopgate Server (PC)                 │
│                                                          │
│  ┌──────────────┐    ┌──────────────┐                   │
│  │  FastAPI     │    │  WebSocket   │                   │
│  │  REST API    │    │  Server      │                   │
│  │  :8000       │    │  :8765       │                   │
│  └──────┬───────┘    └──────┬───────┘                   │
│         │                   │                            │
│  ┌──────▼───────────────────▼──────┐                    │
│  │         In-memory Task Store    │                    │
│  └─────────────────────────────────┘                    │
└──────────────────────┬──────────────────────────────────┘
                       │ ngrok tunnel
                       │
              ┌────────▼────────┐
              │   Public URL    │
              │ https://xxx.    │
              │ ngrok-free.app  │
              └────────┬────────┘
                       │
              ┌────────▼────────┐
              │  Mobile React   │
              │  Dashboard      │
              └─────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+ (for frontend)
- [ngrok](https://ngrok.com) account (free tier works)

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/loopgate.git
cd loopgate
```

### 2. Start the backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python run.py
```

### 3. Open a public tunnel

```bash
ngrok http 8000
```

Copy the `https://xxx.ngrok-free.app` URL — you'll need it in the mobile app.

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your mobile browser and enter the ngrok URL.

---

## 📱 Usage

### From an AI agent / script

```bash
# Create a task (it will wait for your approval on mobile)
curl -X POST https://YOUR-NGROK-URL/api/v1/tasks \
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

LOOPGATE = "https://YOUR-NGROK-URL"

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

# Usage
success = run_with_approval(
    name="Database migration",
    command="python manage.py migrate"
)
print("✅ Done" if success else "❌ Failed or rejected")
```

---

## 📡 API Reference

Full interactive docs available at `http://localhost:8000/docs` when the server is running.

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/tasks` | List all tasks |
| `GET` | `/api/v1/tasks/{id}` | Get task details + log |
| `POST` | `/api/v1/tasks` | Create a new task |
| `POST` | `/api/v1/tasks/{id}/approve` | Approve or reject a task |
| `DELETE` | `/api/v1/tasks/{id}` | Delete a task |
| `GET` | `/health` | Server health check |

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

### WebSocket Events

Connect to `ws://HOST:8765`

| Event | Direction | Payload |
|-------|-----------|---------|
| `init` | server → client | `{ tasks: Task[] }` |
| `task_created` | server → client | `{ task: Task }` |
| `task_updated` | server → client | `{ task: Task }` |
| `task_log` | server → client | `{ task_id, line: { time, text } }` |
| `task_deleted` | server → client | `{ task_id }` |

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

## 🗺️ Roadmap

- [ ] Persistent storage (SQLite)
- [ ] Push notifications (mobile)
- [ ] Authentication (JWT)
- [ ] Task scheduling / cron
- [ ] Kiro native plugin
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
```

---

## 📄 License

MIT © 2025 — See [LICENSE](LICENSE) for details.
