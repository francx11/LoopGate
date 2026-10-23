# ── Stage 1: build frontend ───────────────────────────────────────────────────
FROM node:24-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --silent
COPY frontend/ ./
RUN npm run build

# ── Stage 2: production image ─────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# App source
COPY backend/ ./

# Compiled frontend
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Non-root user
RUN useradd -r -u 1001 loopgate && chown -R loopgate /app
USER loopgate

# Data volume for SQLite persistence
VOLUME ["/app/data"]

EXPOSE 8000

ENV HOST=0.0.0.0 \
    PORT=8000 \
    LOG_LEVEL=info \
    STORE_BACKEND=sqlite \
    SQLITE_PATH=/app/data/loopgate.db \
    PROJECTS_ROOT=/app/data/projects

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "run.py"]
