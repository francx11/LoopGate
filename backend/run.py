#!/usr/bin/env python3
"""
Loopgate — entry point
Starts the FastAPI REST server and the WebSocket server concurrently.
"""

import asyncio
import threading

import uvicorn

from app.core.config import settings
from app.api.websocket import start_ws_server


def run_ws():
    asyncio.run(start_ws_server(settings.WS_PORT))


if __name__ == "__main__":
    # WebSocket in background thread
    ws_thread = threading.Thread(target=run_ws, daemon=True)
    ws_thread.start()

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        log_level=settings.LOG_LEVEL,
        reload=False,
    )
