import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.auth import is_valid_token
from app.core.config import settings
from app.core.store import task_store
from app.core.ws_manager import manager

router = APIRouter(tags=["websocket"])

AUTH_TIMEOUT_SECONDS = 5
WS_CLOSE_INVALID_TOKEN = 4001


async def _authenticate(websocket: WebSocket) -> bool:
    """
    Auth strategy when SECRET_TOKEN is set:
      1. Accept a token in the ?token= query param (legacy clients).
      2. Otherwise wait for a first message {"type":"auth","token":"..."}.
    On failure, notify the client and close with code 4001.
    """
    if not settings.SECRET_TOKEN:
        return True

    token = websocket.query_params.get("token", "")
    if is_valid_token(token):
        return True

    try:
        raw = await asyncio.wait_for(
            websocket.receive_text(), timeout=AUTH_TIMEOUT_SECONDS
        )
        msg = json.loads(raw)
        if msg.get("type") == "auth":
            token = msg.get("token", "")
    except (TimeoutError, json.JSONDecodeError, WebSocketDisconnect):
        token = ""

    if is_valid_token(token):
        return True

    try:
        await websocket.send_text(
            json.dumps({"type": "auth_error", "reason": "invalid_token"})
        )
    except Exception:  # noqa: S110
        pass
    await websocket.close(code=WS_CLOSE_INVALID_TOKEN, reason="invalid token")
    return False


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Always accept the handshake first — rejecting pre-accept yields HTTP 403
    # at the proxy level, which confuses clients and complicates retries.
    await websocket.accept()

    if not await _authenticate(websocket):
        return

    manager.add(websocket)
    try:
        await websocket.send_text(json.dumps({
            "type": "init",
            "tasks": [t.model_dump() for t in task_store.all()],
        }))
        async for raw in websocket.iter_text():
            try:
                msg = json.loads(raw)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except Exception:  # noqa: S110
                pass
    except WebSocketDisconnect:
        pass
    finally:
        manager.remove(websocket)
