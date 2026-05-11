# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.2.x   | ✅ Yes    |
| 0.1.x   | ❌ No     |

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Email **franexca@gmail.com** with:
- A description of the vulnerability
- Steps to reproduce
- Impact assessment

You will receive a response within 72 hours and a fix within 14 days for critical issues.

## Threat Model

Loopgate is designed to run **on a trusted local machine** and be accessed from a
personal mobile device over a private tunnel (Tailscale) or authenticated ngrok tunnel.

### In scope

| Threat | Mitigation |
|--------|-----------|
| Unauthenticated API access | `SECRET_TOKEN` Bearer auth on all `/api/v1/*` routes |
| WebSocket token leakage via proxy logs | First-message auth (token never in URL query params) |
| Token brute force | Constant-time comparison (`secrets.compare_digest`), rate-limiting (30 req/min) |
| Shell injection via task command | Human approval required before execution; server-side validation for Claude prompts; `executor.py` runs in isolated subprocess environment with whitelisted env vars |
| Cross-origin requests | `CORS_ORIGINS` defaults to empty (same-origin only) |
| Clickjacking | `X-Frame-Options: DENY`, `frame-ancestors 'none'` CSP directive |
| Content sniffing | `X-Content-Type-Options: nosniff` |
| Path traversal in project listing | `is_relative_to(PROJECTS_ROOT)` check |

### Out of scope / known trade-offs

| Issue | Decision |
|-------|----------|
| Token stored in `localStorage` | Accepted: XSS is not a realistic risk on a same-origin, single-user internal tool |
| `shell=True` subprocess | Accepted: human approval is the primary control; changing this would break all shell pipelines |
| In-memory task store (data lost on restart) | Use `STORE_BACKEND=sqlite` for persistence — see [docs/DEPLOY.md](docs/DEPLOY.md) |
| Single shared `SECRET_TOKEN` | Sufficient for single-user personal use; multi-user support is on the roadmap |

## Security Headers

Every HTTP response includes:

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'; …
Permissions-Policy: geolocation=(), microphone=(), camera=()
Strict-Transport-Security: max-age=31536000 (HTTPS only)
```

## Audit Log

All task lifecycle events (created, approved, rejected, deleted) are written to
`loopgate.audit.log` with timestamp, task ID, and client IP.

To enable persistent audit logs set `LOG_LEVEL=info` in `.env` (default).
