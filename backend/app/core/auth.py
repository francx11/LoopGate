"""
Authentication helpers.
All API routes and the WebSocket endpoint validate a Bearer token when
SECRET_TOKEN is set in the environment.  If SECRET_TOKEN is empty the server
runs in open mode (dev/localhost only — do not expose to internet).
"""

from fastapi import HTTPException, Security, WebSocket
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

_bearer = HTTPBearer(auto_error=False)


def verify_token(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
) -> None:
    """FastAPI dependency — raises 401 when token is wrong or missing."""
    if not settings.SECRET_TOKEN:
        return
    if not credentials or credentials.credentials != settings.SECRET_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Token inválido o ausente",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def verify_ws_token(websocket: WebSocket) -> bool:
    """
    WebSocket auth — reads ?token= query param.
    Closes the socket with code 4001 and returns False when auth fails.
    """
    if not settings.SECRET_TOKEN:
        return True
    token = websocket.query_params.get("token", "")
    if token != settings.SECRET_TOKEN:
        await websocket.close(code=4001, reason="Token inválido")
        return False
    return True
