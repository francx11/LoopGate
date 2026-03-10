"""
WebSocket connection manager.
Handles broadcasting events to all connected clients.
"""

import asyncio
import json
from typing import Set
import websockets


class ConnectionManager:
    def __init__(self):
        self._clients: Set = set()

    def add(self, ws):
        self._clients.add(ws)

    def remove(self, ws):
        self._clients.discard(ws)

    @property
    def count(self) -> int:
        return len(self._clients)

    async def broadcast(self, event: dict):
        if not self._clients:
            return
        message = json.dumps(event)
        results = await asyncio.gather(
            *[client.send(message) for client in self._clients],
            return_exceptions=True,
        )
        # Remove dead connections
        dead = {
            client
            for client, result in zip(self._clients, results)
            if isinstance(result, Exception)
        }
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
