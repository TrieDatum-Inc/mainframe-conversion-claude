"""
FastAPI dependency injection for authentication and authorization.

Provides:
- get_current_user: validates JWT Bearer token, returns user dict
- require_admin: extends get_current_user to enforce admin role (for purge endpoint)
"""

from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import settings

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, Any]:
    """
    Validate JWT Bearer token and return decoded user payload.

    Used by all authorization endpoints.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception


async def require_admin(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Require admin role.

    Used only by the purge endpoint (mirrors admin-only batch job CBPAUP0C).
    User type 'A' maps to CardDemo admin user (COADM01C).
    """
    user_type = current_user.get("user_type", "")
    if user_type != "A":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required for this operation",
        )
    return current_user
