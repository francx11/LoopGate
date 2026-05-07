# LoopGate

Remote shell-command approval system. A mobile phone connects via ngrok to a FastAPI + WebSocket backend running locally. Commands submitted by the backend (or any client) are held in `pending_approval` status until approved/rejected from the mobile UI.

## Stack

| Layer | Tech | Version |
|---|---|---|
| Backend | Python / FastAPI | 3.11 / 0.111 |
| ASGI server | Uvicorn | 0.30.1 |
| WebSocket server | websockets lib | 12.0 |
| Validation | Pydantic v2 | 2.7.1 |
| Frontend | React + TypeScript | 18.3 / 5.4 |
| Build | Vite | 5.3.1 |
| State | Zustand | 4.5.2 |
| Styling | Tailwind CSS + CSS Modules | 3.4.4 |

## Commands

```bash
# One-shot start (Windows) — builds frontend + starts backend + launches ngrok
./start.bat

# Backend (manual)
cd backend
python -m venv venv && venv\Scripts\activate   # first time
pip install -r requirements.txt                 # first time
python run.py                                   # starts on :8000

# Frontend (dev mode only — not needed in production)
cd frontend
npm install          # first time
npm run dev          # dev server :5173
npm run build        # production build → dist/ (served by FastAPI)

# CI-equivalent checks
cd backend && python -m pytest tests/ -v
cd frontend && npm run build
```

## Architecture

```
mobile browser
    │ HTTPS/WSS via ngrok tunnel (single URL)
    ▼
FastAPI :8000
    ├── GET  /health          health check
    ├── *    /api/v1/tasks    REST CRUD
    ├── WS   /ws              WebSocket (real-time events)
    └── *    /                frontend/dist/ static files (SPA)
    │
    ▼
TaskStore (in-memory, thread-safe with Lock)
    │
    ▼
TaskExecutor (background daemon thread)
    └─ subprocess.Popen shell=True → streams stdout/stderr to WS clients
```

**Single-port design:** frontend is compiled (`npm run build`) into `frontend/dist/`
and served by FastAPI via `StaticFiles`.
The frontend auto-detects same-origin backend on load — no manual URL setup needed.

**Remote access (Tailscale preferred):** `start.bat` runs `tailscale ip -4` to get
the stable private IP and prints `http://<IP>:8000`. Mobile opens that URL directly.
Falls back to ngrok if Tailscale is not available.

## Task Status FSM

```
pending_approval → queued → running → done | error
pending_approval → rejected
```

## WebSocket Events (server → client)

| Event | When |
|---|---|
| `init` | On connect: full task snapshot |
| `task_created` | New task created |
| `task_updated` | Status or fields changed |
| `task_log` | Stdout/stderr line streamed |
| `task_deleted` | Task removed |

## Code Conventions

**Backend**
- Pydantic v2 models for all request/response shapes (`backend/app/models/`)
- `BaseSettings` in `backend/app/core/config.py` — all config via env vars or `.env`
- Store mutations go through `backend/app/core/store.py` (`TaskStore` singleton)
- WebSocket broadcasts via `ws_manager.broadcast_sync()` from sync threads, `broadcast()` from async
- New API routes: add to `backend/app/api/`, import in `backend/app/main.py`

**Frontend**
- Global state in `frontend/src/store/index.ts` (Zustand) — all WS events update store
- API calls in `frontend/src/services/api.ts`
- Component styles: CSS Modules (`.module.css` co-located with component)
- UI language: Spanish (labels, messages)
- Color tokens: use CSS vars from `frontend/src/index.css` (never hardcode colors)
- Dark theme always — no light mode

**Naming**
- Python: `snake_case` functions/vars, `PascalCase` classes
- TypeScript: `camelCase` vars/functions, `PascalCase` components/interfaces
- Task IDs: 8-char UUID prefix

## Ignore

```
backend/venv/
frontend/node_modules/
frontend/dist/
**/__pycache__/
**/*.pyc
.env          # never read or commit — use .env.example as reference
```

## Security Rules

- [HUMAN APPROVAL REQUIRED] Never modify `executor.py` subprocess invocation (shell injection risk)
- [HUMAN APPROVAL REQUIRED] Never disable CORS `allow_origins=["*"]` without a controlled list
- [HUMAN APPROVAL REQUIRED] Never commit `.env` files or tokens
- [HUMAN APPROVAL REQUIRED] Never force-push `main`
- The `SECRET_TOKEN` field in `.env` exists but is not enforced yet — do not add enforcement silently; discuss with user first

## Git Workflow

**Commit format (mandatory):**
- Language: **English only** — subject line and body
- Style: Conventional Commits — `feat:`, `fix:`, `refactor:`, `chore:`, `docs:`, `test:`
- **No co-authorship trailer** — never append `Co-Authored-By:` lines
- One commit per logical unit — don't batch unrelated changes, don't split a coherent change

**Auto-commit on completion:**
- When a unit of change is self-contained and verifiable (new endpoint, finished component, complete migration), commit without waiting for explicit instruction.

**Ramas para features grandes:**
- Si el trabajo toca más de un subsistema (ej. backend + frontend + config) o requiere más de ~3 commits, crear una rama dedicada antes de empezar: `git checkout -b feature/<nombre-descriptivo>`.
- Hacer merge a `main` solo cuando la feature esté completa y funcional.
- Nombre de rama: `feature/` para funcionalidades, `fix/` para bugs, `chore/` para mantenimiento.

**Criterio de tamaño:**
- Pequeño (commit directo en rama actual): un archivo o subsistema, cambio reversible, < 1 hora de trabajo.
- Grande (rama dedicada): múltiples subsistemas, cambio estructural, o dependencias entre pasos intermedios que podrían romper `main`.

## Self-Maintenance

When a new recurring pattern appears (new model field shape, new WS event type, new component pattern), propose an update to this CLAUDE.md with the specific addition needed.
