#!/usr/bin/env bash
# Loopgate start script (Linux / macOS)
# Usage: ./scripts/start.sh

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo ""
echo "======================================"
echo "           LOOPGATE"
echo "======================================"
echo ""

# ── 1. Build frontend ──────────────────────────────────────────────────────────
echo "[1/3] Building frontend..."
cd "$REPO_ROOT/frontend"
if [ ! -d node_modules ]; then
    echo "  Installing npm dependencies..."
    npm install --silent
fi
npm run build
cd "$REPO_ROOT"

# ── 2. Prepare backend ─────────────────────────────────────────────────────────
echo "[2/3] Setting up backend..."
cd "$REPO_ROOT/backend"
if [ ! -d venv ]; then
    echo "  Creating virtual environment..."
    python3 -m venv venv
fi
venv/bin/pip install -q -r requirements.txt
if [ ! -f .env ]; then
    echo "  Creating .env from .env.example..."
    cp .env.example .env
    echo "  Edit backend/.env and set SECRET_TOKEN before exposing to internet."
fi
cd "$REPO_ROOT"

# ── 3. Start backend ──────────────────────────────────────────────────────────
echo "[3/3] Starting backend..."
cd "$REPO_ROOT/backend"
venv/bin/python run.py &
BACKEND_PID=$!
sleep 2

# ── Detect access URL ────────────────────────────────────────────────────────
TS_IP=""
if command -v tailscale &>/dev/null; then
    TS_IP=$(tailscale ip -4 2>/dev/null || true)
fi

if [ -n "$TS_IP" ]; then
    echo ""
    echo "  ╔══════════════════════════════════════╗"
    echo "  ║  Loopgate ready via Tailscale        ║"
    echo "  ║                                      ║"
    echo "  ║  http://$TS_IP:8000"
    echo "  ║                                      ║"
    echo "  ║  Open that URL on your phone.        ║"
    echo "  ╚══════════════════════════════════════╝"
elif command -v ngrok &>/dev/null; then
    echo "  Starting ngrok tunnel..."
    ngrok http 8000 &
    sleep 2
    echo "  Tunnel active. Visit http://localhost:4040 for the public URL."
else
    echo "  Access locally: http://localhost:8000"
    echo ""
    echo "  For remote access install Tailscale:"
    echo "    https://tailscale.com/download"
fi

echo ""
echo "  Press Ctrl+C to stop."
wait $BACKEND_PID
