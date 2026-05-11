# Changelog

All notable changes to Loopgate are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.2.0] — 2026-05-11

### Added
- **WebSocket first-message auth** — handshake always accepted; token validated
  via `{type:"auth",token:"..."}` message, eliminating HTTP 403 at proxy level
- **`secrets.compare_digest`** for constant-time token comparison
- **Rate limiting** (slowapi) — mutating endpoints capped at 20-30 req/min per IP
- **Content-Security-Policy** header on every response
- **Audit logging** — task lifecycle events written to `loopgate.audit` logger
- **Backend Claude command builder** — `POST /api/v1/tasks/claude-prompt` endpoint;
  shell command constructed server-side with path and injection validation
- **Test suite** — `backend/tests/` with 32 tests covering auth, task CRUD,
  approval flow, command builder, and security headers
- **`pyproject.toml`** with ruff, mypy, pytest configuration
- **ESLint + Prettier** configuration for frontend
- **SECURITY.md** threat model and responsible disclosure policy
- **CONTRIBUTING.md** setup and workflow guide
- **Docker support** — multi-stage Dockerfile, docker-compose with Caddy TLS
- **Cross-platform executor** — Windows and POSIX path handling
- **Optional SQLite store** — set `STORE_BACKEND=sqlite` for persistence across restarts
- **deploy/** — systemd unit, Caddyfile, and `scripts/start.sh` for Linux

### Changed
- `PromptForm.tsx` no longer builds shell strings client-side
- CI workflow updated: ruff lint, full test run, pip-audit, npm audit
- Frontend `api.ts` clears stale token and redirects to SetupScreen on 401/403

### Fixed
- WebSocket token rejection no longer produces HTTP 403 at the handshake level
- 401 REST responses now reset the UI to SetupScreen instead of showing red text
- CI `pytest tests/` step was pointing at a non-existent directory

## [0.1.0] — 2026-05-06

### Added
- Initial release: FastAPI backend, React + TypeScript frontend
- Task queue with human approval flow
- Real-time log streaming via WebSocket
- Tailscale-first remote access with ngrok fallback
- Optional `SECRET_TOKEN` Bearer authentication
- `start.bat` one-shot launcher for Windows
