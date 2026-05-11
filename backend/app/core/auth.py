"""
Authentication helpers.
All API routes and the WebSocket endpoint validate a Bearer token when
SECRET_TOKEN is set in the environment.  If SECRET_TOKEN is empty the server
runs in open mode (dev/localhost only — do not expose to internet).
"""

import secrets

from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

_bearer = HTTPBearer(auto_error=False)


def is_valid_token(token: str) -> bool:
    """Constant-time check against the configured SECRET_TOKEN.

    Returns True when no token is configured (open mode).
    """
    if not settings.SECRET_TOKEN:
        return True
    if not token:
        return False
    return secrets.compare_digest(token, settings.SECRET_TOKEN)


def verify_token(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
) -> None:
    """FastAPI dependency — raises 401 when token is wrong or missing."""
    if not settings.SECRET_TOKEN:
        return
    token = credentials.credentials if credentials else ""
    if not is_valid_token(token):
        raise HTTPException(
            status_code=401,
            detail="Token inválido o ausente",
            headers={"WWW-Authenticate": "Bearer"},
        )
