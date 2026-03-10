import json
import asyncio
import websockets
from fastapi import APIRouter

from app.core.store import task_store
from app.core.ws_manager import manager

router = APIRouter(tags=["websocket"])


# Standalone WebSocket server (runs on separate port 8765)
async def ws_handler(websocket, path=None):
    manager.add(websocket)
    try:
        # Send full current state on connect
        await websocket.send(json.dumps({
            "type": "init",
            "tasks": [t.model_dump() for t in task_store.all()],
        }))
        async for _ in websocket:
            pass  # server-driven only; clients don't send commands over WS
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        manager.remove(websocket)


async def start_ws_server(port: int = 8765):
    async with websockets.serve(ws_handler, "0.0.0.0", port):
        print(f"🔌 WebSocket server listening on ws://0.0.0.0:{port}")
        await asyncio.Future()
