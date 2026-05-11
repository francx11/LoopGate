#!/usr/bin/env python3
"""
Loopgate — entry point
Starts the unified FastAPI server (REST + WebSocket + static frontend).
"""

import uvicorn

from app.core.config import settings

if __name__ == "__main__":
    print(f"Loopgate starting on http://{settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL,
        reload=False,
    )
