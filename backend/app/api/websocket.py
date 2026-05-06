import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.auth import verify_ws_token
from app.core.store import task_store
from app.core.ws_manager import manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    if not await verify_ws_token(websocket):
        return
    await websocket.accept()
    manager.add(websocket)
    try:
        await websocket.send_text(json.dumps({
            "type": "init",
            "tasks": [t.model_dump() for t in task_store.all()],
        }))
        async for _ in websocket.iter_text():
            pass  # server-driven only; clients don't send commands over WS
    except WebSocketDisconnect:
        pass
    finally:
        manager.remove(websocket)
