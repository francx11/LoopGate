# Skill: Security Audit — LoopGate

You are a security auditor for LoopGate, a FastAPI + React remote shell-command approval system.
When this skill is invoked, perform a full security audit of the current branch and report findings.

## What to audit

### 1. Authentication & Authorization
- [ ] `backend/app/core/auth.py` exists and exports `verify_token` and `verify_ws_token`
- [ ] Every route in `backend/app/api/tasks.py` has `dependencies=[Depends(verify_token)]` on the router
- [ ] `backend/app/api/websocket.py` calls `verify_ws_token` before `accept()`
- [ ] `SECRET_TOKEN` is defined in `backend/.env` (not `.env.example`)
- [ ] Token is non-empty and at least 32 characters long (run: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)

### 2. Network exposure
- [ ] `backend/run.py`: confirm `host` binding — `0.0.0.0` is acceptable when Tailscale is used + token auth is active; `127.0.0.1` if you only use localhost
- [ ] CORS: `CORS_ORIGINS` in `config.py` defaults to `[]` — confirm it is NOT `["*"]`
- [ ] Windows Firewall: port 8000 should NOT have a public inbound rule (`netsh advfirewall firewall show rule name=all dir=in | findstr 8000`)

### 3. Security headers
Run the server locally and check response headers with:
```
curl -s -I http://localhost:8000/health
```
Expected headers present:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: geolocation=(), microphone=(), camera=()`

### 4. Subprocess security (`executor.py`)
- [ ] `_build_env()` uses a whitelist (`_ENV_WHITELIST`), NOT `os.environ.copy()`
- [ ] `shell=True` is still in place (required for claude commands) — this is intentional and mitigated by token auth
- [ ] The `cwd` for Popen is a fixed path, not user-supplied

### 5. Input validation
- [ ] `CreateTaskRequest.command` has `max_length` set (prevents DoS via huge payloads)
- [ ] Task IDs use full `uuid4()` (not truncated 8-char prefix)
- [ ] `/projects` endpoint uses `.resolve().is_relative_to(root)` to prevent path traversal

### 6. Frontend secrets & injection
- [ ] `PromptForm.tsx`: `sanitizePath()` strips `'"<>|*?&;\`` from custom directory paths
- [ ] `api.ts`: all requests include `Authorization: Bearer <token>` when token is set
- [ ] `useWebSocket.ts`: WS URL includes `?token=<token>` when token is set
- [ ] Token is stored in `localStorage` under key `lg-token` — acceptable since app is single-user

### 7. OpenAPI docs
- [ ] When `SECRET_TOKEN` is set, `/docs` and `/redoc` return 404 (check in `main.py`: `docs_url=None`)

### 8. Information disclosure
- [ ] `/health` returns only `{status, version, auth_required}` — no task count, no internal state

## How to run a quick automated check

```bash
# From project root
cd backend

# 1. Confirm auth module exists
python -c "from app.core.auth import verify_token, verify_ws_token; print('auth OK')"

# 2. Confirm no wildcard CORS
python -c "from app.core.config import settings; assert settings.CORS_ORIGINS != ['*'], 'CORS wildcard!'; print('CORS OK')"

# 3. Confirm SECRET_TOKEN is set (requires .env)
python -c "from app.core.config import settings; assert settings.SECRET_TOKEN, 'SECRET_TOKEN empty!'; print(f'Token OK ({len(settings.SECRET_TOKEN)} chars)')"

# 4. Confirm env whitelist in executor
python -c "from app.services.executor import _ENV_WHITELIST; assert len(_ENV_WHITELIST) < 30, 'Whitelist too broad!'; print(f'Env whitelist OK ({len(_ENV_WHITELIST)} vars)')"

# 5. Build frontend (must succeed with 0 TS errors)
cd ../frontend && npm run build
```

## Severity classification

| Finding | Severity | Action |
|---|---|---|
| `SECRET_TOKEN` empty in production | CRITICAL | Set immediately |
| CORS `["*"]` | HIGH | Restrict to known origins |
| Token missing from API/WS calls in frontend | HIGH | Check store + api.ts |
| `os.environ.copy()` in executor | HIGH | Replace with whitelist |
| 8-char task IDs | MEDIUM | Use full UUID |
| No security headers | MEDIUM | Add middleware |
| Wildcard CORS methods (`["*"]`) | MEDIUM | Restrict to GET/POST/DELETE |
| OpenAPI exposed with token active | LOW | Set `docs_url=None` |
| Task count in `/health` | LOW | Remove from response |

## After each audit

If any check fails, open an issue or fix inline.
Update this skill if a new attack surface is introduced (new endpoint, new WS event type, new env var).
