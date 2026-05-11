# Deployment Guide

Three deployment paths, from simplest to most production-grade.

---

## Option A — Docker Compose on a VPS (recommended)

### 1. Provision a VPS

Any provider works (Hetzner, DigitalOcean, Linode, etc.). Minimum: 1 CPU, 512 MB RAM.
Ubuntu 22.04 LTS is used below.

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
```

### 2. Clone and configure

```bash
git clone https://github.com/francx11/loopgate.git
cd loopgate
cp backend/.env.example backend/.env
```

Edit `backend/.env`:
```ini
SECRET_TOKEN=<generate with: python3 -c "import secrets; print(secrets.token_urlsafe(32))">
STORE_BACKEND=sqlite
```

### 3. Start

```bash
docker compose up -d
```

The app is now available on port `8000`.

### 4. Add HTTPS with Caddy (optional but recommended)

```bash
# Uncomment the caddy service in docker-compose.yml
# Edit deploy/Caddyfile to set your domain
docker compose up -d caddy
```

Caddy obtains a Let's Encrypt certificate automatically on first request.

### Useful commands

```bash
docker compose logs -f loopgate   # live logs
docker compose restart loopgate   # restart after config change
docker compose pull && docker compose up -d  # update to latest build
```

---

## Option B — Bare-metal with systemd (Ubuntu/Debian)

### 1. Install

```bash
sudo useradd -r -s /bin/false loopgate
sudo mkdir -p /opt/loopgate/data
git clone https://github.com/francx11/loopgate.git /opt/loopgate

cd /opt/loopgate/frontend && npm ci && npm run build

cd /opt/loopgate/backend
python3 -m venv venv
venv/bin/pip install -r requirements.txt
cp .env.example .env
# Edit .env
```

### 2. Install systemd unit

```bash
sudo cp /opt/loopgate/deploy/loopgate.service /etc/systemd/system/
sudo chown -R loopgate:loopgate /opt/loopgate
sudo systemctl daemon-reload
sudo systemctl enable --now loopgate
sudo journalctl -u loopgate -f  # view logs
```

---

## Option C — PaaS (Fly.io)

```bash
fly launch --name loopgate --region mad
fly secrets set SECRET_TOKEN=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
fly volumes create loopgate_data --size 1
fly deploy
```

Add to `fly.toml`:
```toml
[mounts]
  source = "loopgate_data"
  destination = "/app/data"

[env]
  STORE_BACKEND = "sqlite"
  SQLITE_PATH = "/app/data/loopgate.db"
```

---

## Environment variables reference

| Variable | Default | Description |
|---|---|---|
| `SECRET_TOKEN` | `""` | Bearer token for all API/WS auth. **Set this in production.** |
| `PORT` | `8000` | Listening port |
| `HOST` | `0.0.0.0` | Bind address |
| `STORE_BACKEND` | `memory` | `memory` or `sqlite` |
| `SQLITE_PATH` | `loopgate.db` | Path to SQLite file (when `STORE_BACKEND=sqlite`) |
| `PROJECTS_ROOT` | `~/projects` (Linux) | Root directory for the project selector |
| `CORS_ORIGINS` | `[]` | List of allowed CORS origins. Leave empty for same-origin only. |
| `LOG_LEVEL` | `info` | `debug`, `info`, `warning`, `error` |

---

## Access from mobile

| Method | Setup | Notes |
|--------|-------|-------|
| Tailscale | Install on server + phone, same account | Private IP, no port exposure |
| ngrok | `ngrok http 8000` | Public URL, requires auth if `SECRET_TOKEN` set |
| Caddy + domain | Point DNS to VPS, uncomment caddy in compose | Full HTTPS, production-ready |
