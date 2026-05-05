"""
Loopgate — Backend API
Human-in-the-loop approval layer for AI agent tasks.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import tasks, websocket
from app.core.config import settings
from app.core.store import task_store

FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 Loopgate starting on http://0.0.0.0:{settings.PORT}")
    if FRONTEND_DIST.exists():
        print(f"📦 Serving frontend from {FRONTEND_DIST}")
    else:
        print(f"⚠️  Frontend not built — run 'npm run build' in frontend/")
    yield
    print("🛑 Loopgate server shutting down")


app = FastAPI(
    title="Loopgate API",
    description="Human-in-the-loop approval layer for AI agent tasks",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router, prefix="/api/v1")
app.include_router(websocket.router)


@app.get("/health", tags=["system"])
def health():
    return {
        "status": "ok",
        "version": "0.1.0",
        "tasks": len(task_store.all()),
    }


# Must come last — catches all unmatched routes for SPA client-side routing
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
