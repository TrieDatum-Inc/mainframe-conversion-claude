"""JWT authentication dependency and role-based access control.

Replaces CICS COMMAREA validation in COMEN01C / COADM01C MAIN-PARA:
  COBOL: IF EIBCALEN = 0 → RETURN-TO-SIGNON-SCREEN (security guard)
  Modern: Bearer token required; missing/invalid token → 401

Role-based access:
  COADM01C only allows admin users (user_type='A').
  COMEN01C allows regular users (user_type='U').
  These are enforced via the require_admin / require_user dependencies.
"""
import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.schemas.auth import TokenPayload, UserInfo
from app.utils.security import decode_token

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)
    ],
) -> TokenPayload:
    """Validate JWT token and return token payload.

    Replaces CICS EIBCALEN > 0 check + COMMAREA copy in all CardDemo programs.
    Returns 401 when token is missing or invalid (equivalent to RETURN-TO-SIGNON-SCREEN).
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token_data = decode_token(credentials.credentials)
    except JWTError as exc:
        logger.info("Invalid JWT token: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return token_data


async def get_current_user_info(
    token_data: Annotated[TokenPayload, Depends(get_current_user)],
) -> UserInfo:
    """Extract UserInfo from token — convenience dependency."""
    return UserInfo(
        user_id=token_data.sub,
        first_name=token_data.first_name,
        last_name=token_data.last_name,
        user_type=token_data.user_type,
    )


async def require_admin(
    user: Annotated[UserInfo, Depends(get_current_user_info)],
) -> UserInfo:
    """Require admin role — replaces COADM01C's implicit admin-only access.

    COSGN00C BR-006: Only user_type='A' is routed to COADM01C.
    Modern equivalent: 403 Forbidden if regular user attempts admin routes.
    """
    if user.user_type != "A":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


async def require_regular_user(
    user: Annotated[UserInfo, Depends(get_current_user_info)],
) -> UserInfo:
    """Require regular user role — replaces COMEN01C's regular-user-only access.

    Both 'U' and 'A' users can access the main menu in COMEN01C spec
    (admin users go to COADM01C but could theoretically access COMEN01C too).
    This dependency allows both roles but excludes unauthenticated requests.
    """
    if user.user_type not in ("U", "A"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User access required",
        )
    return user
