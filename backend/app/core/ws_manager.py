"""
WebSocket connection manager.
Handles broadcasting events to all connected FastAPI WebSocket clients.
"""

import asyncio
import json
from typing import Set

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self._clients: Set[WebSocket] = set()

    def add(self, ws: WebSocket):
        self._clients.add(ws)

    def remove(self, ws: WebSocket):
        self._clients.discard(ws)

    @property
    def count(self) -> int:
        return len(self._clients)

    async def broadcast(self, event: dict):
        if not self._clients:
            return
        message = json.dumps(event)
        dead: Set[WebSocket] = set()
        for client in list(self._clients):
            try:
                await client.send_text(message)
            except Exception:
                dead.add(client)
        for client in dead:
            self._clients.discard(client)

    def broadcast_sync(self, event: dict):
        """For use from sync threads (e.g. task execution)."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(self.broadcast(event), loop)
            else:
                asyncio.run(self.broadcast(event))
        except Exception:
            pass


manager = ConnectionManager()
