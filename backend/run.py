#!/usr/bin/env python3
"""
Loopgate — entry point
Starts the unified FastAPI server (REST + WebSocket + static frontend).
"""

import sys

import uvicorn

from app.core.config import settings


def _patch_windows_connection_reset():
    if sys.platform != "win32":
        return
    import asyncio.proactor_events as _pe

    _orig = _pe._ProactorBasePipeTransport._call_connection_lost

    def _patched(self, exc):
        try:
            _orig(self, exc)
        except ConnectionResetError:
            pass

    _pe._ProactorBasePipeTransport._call_connection_lost = _patched


_patch_windows_connection_reset()

if __name__ == "__main__":
    print(f"Loopgate starting on http://{settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL,
        reload=settings.DEBUG,
    )
