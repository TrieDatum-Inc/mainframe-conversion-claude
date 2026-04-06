"""
FastAPI dependency functions for authentication and authorization.

COBOL origin:
  get_current_user → replaces EIBCALEN > 0 check + DFHCOMMAREA user context
  require_admin    → replaces CICS admin-program-only navigation logic
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.utils.security import decode_token as _decode_token

_bearer_scheme = HTTPBearer(auto_error=True)


class CurrentUser:
    """Minimal user context extracted from JWT — replaces CARDDEMO-COMMAREA fields."""

    def __init__(self, user_id: str, user_type: str) -> None:
        self.user_id = user_id
        self.user_type = user_type

    @property
    def is_admin(self) -> bool:
        """Maps CDEMO-USRTYP-ADMIN condition (user_type = 'A')."""
        return self.user_type == "A"


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer_scheme)],
) -> CurrentUser:
    """Decode and validate the JWT Bearer token."""
    token = credentials.credentials
    try:
        payload = _decode_token(token)
    except ValueError:
        payload = None

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "INVALID_TOKEN",
                "message": "Invalid or expired authentication token",
                "details": [],
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    user_type = payload.get("user_type")

    if not user_id or not user_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "INVALID_TOKEN",
                "message": "Token is missing required claims",
                "details": [],
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    return CurrentUser(user_id=user_id, user_type=user_type)


async def require_admin(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    """Enforce admin-only access (user_type='A')."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "ADMIN_REQUIRED",
                "message": "This operation requires administrator privileges",
                "details": [],
            },
        )
    return current_user
