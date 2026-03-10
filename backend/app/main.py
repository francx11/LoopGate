"""
Loopgate — Backend API
Human-in-the-loop approval layer for AI agent tasks.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import tasks, websocket
from app.core.config import settings
from app.core.store import task_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 Loopgate server starting on port {settings.PORT}")
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
