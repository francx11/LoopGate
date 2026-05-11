"""
Loopgate — Backend API
Human-in-the-loop approval layer for AI agent tasks.
"""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api import tasks, websocket
from app.core.config import settings
from app.core.limiter import limiter
from app.core.ws_manager import manager

FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    manager.set_loop(asyncio.get_running_loop())
    auth_status = "TOKEN ACTIVO" if settings.SECRET_TOKEN else "SIN TOKEN (modo dev)"
    print(f"Loopgate iniciando en puerto {settings.PORT} — {auth_status}")
    if FRONTEND_DIST.exists():
        print(f"Sirviendo frontend desde {FRONTEND_DIST}")
    else:
        print("Frontend no compilado — ejecuta 'npm run build' en frontend/")
    yield
    print("Loopgate cerrando")


app = FastAPI(
    title="Loopgate API",
    description="Human-in-the-loop approval layer for AI agent tasks",
    version="0.2.0",
    lifespan=lifespan,
    docs_url=None if settings.SECRET_TOKEN else "/docs",
    redoc_url=None if settings.SECRET_TOKEN else "/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "connect-src 'self' ws: wss:; "
    "font-src 'self'; "
    "frame-ancestors 'none'"
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Content-Security-Policy"] = _CSP
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


app.include_router(tasks.router, prefix="/api/v1")
app.include_router(websocket.router)


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "version": "0.2.0", "auth_required": bool(settings.SECRET_TOKEN)}


# Must come last — catches all unmatched routes for SPA client-side routing
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
