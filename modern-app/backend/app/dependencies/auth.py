"""FastAPI auth dependencies for the CardDemo User Administration module.

Provides:
  get_current_user — decodes JWT, loads user from DB
  require_admin    — enforces user_type == 'A' (mirrors COBOL admin-only guard)

JWT format mirrors COSGN00C auth logic:
  - subject ("sub") = user_id (SEC-USR-ID)
  - "user_type" claim = 'A' or 'U'
"""
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import USER_TYPE_ADMIN, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def _decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token, raising 401 on any failure."""
    try:
        return jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def _extract_user_id(payload: dict[str, Any]) -> str:
    """Pull the user_id claim from a decoded JWT payload."""
    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing subject",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id


async def _load_user_from_db(user_id: str, db: AsyncSession) -> User:
    """Fetch the user row by user_id, raising 401 if not found."""
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Decode the JWT and return the authenticated User ORM object.

    Mirrors COSGN00C authentication flow:
      1. Decode token (equivalent to VSAM READ on USRSEC)
      2. Verify user exists in DB
      3. Return fully-populated user record
    """
    payload = _decode_token(token)
    user_id = _extract_user_id(payload)
    return await _load_user_from_db(user_id, db)


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Enforce admin-only access — user_type must be 'A'.

    Mirrors the COBOL admin menu guard in COADM01C:
    all COUSR00C-03C programs are only reachable via the admin menu.

    Raises HTTP 403 for non-admin users (COBOL equivalent: XCTL back to sign-on).
    """
    if current_user.user_type != USER_TYPE_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
