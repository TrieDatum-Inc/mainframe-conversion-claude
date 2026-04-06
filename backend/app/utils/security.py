"""
Security utilities: JWT token creation and validation.
Replaces CICS EIBCALEN check and RACF user authentication.
This module is the canonical location for get_current_user dependency,
referenced by all protected endpoints across all modules.

COBOL equivalent:
  IF EIBCALEN = 0 → unauthenticated → redirect to login
  CARDDEMO-COMMAREA user context → JWT claims (sub, user_type)
"""
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import settings

bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(data: dict[str, Any]) -> str:
    """
    Create a JWT access token.
    Replaces: CICS COMMAREA user context + RACF session token.
    Claims: sub=user_id, user_type='A'|'U', exp=now+3600.
    """
    import time

    payload = dict(data)
    payload["exp"] = int(time.time()) + settings.access_token_expire_minutes * 60
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "INVALID_TOKEN",
                "message": "Token is invalid or expired",
                "details": [],
            },
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ] = None,
) -> dict[str, Any]:
    """
    FastAPI dependency: validate Bearer token and return user claims.
    Replaces: COPAUS0C/COPAUS1C EIBCALEN check (IF EIBCALEN = 0 → unauthenticated).
    All authorization endpoints require this dependency.
    Returns dict with keys: sub (user_id), user_type ('A' or 'U').
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "UNAUTHORIZED",
                "message": "Authentication required",
                "details": [],
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_access_token(credentials.credentials)


async def get_admin_user(
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> dict[str, Any]:
    """
    Dependency for admin-only endpoints.
    Replaces: COBOL IF CDEMO-USRTYP-ADMIN check.
    Raises 403 if user_type != 'A'.
    """
    if current_user.get("user_type") != "A":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "FORBIDDEN",
                "message": "Administrator access required",
                "details": [],
            },
        )
    return current_user
