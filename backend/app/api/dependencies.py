"""
FastAPI dependency functions for authentication and authorization.

COBOL origin:
  get_current_user → replaces EIBCALEN > 0 check + DFHCOMMAREA user context read
  require_admin    → replaces CICS INQUIRE PROGRAM + admin-program-only navigation logic

In the original CICS application:
  - Non-admin users had access only to COMEN01C menu options
  - Admin programs (COUSR00C, COUSR01C, COUSR02C, COUSR03C, COTRTLIC, COTRTUPC)
    were accessible only from COADM01C (admin menu)
  - There was no per-request auth check; CICS terminal security enforced access

Here we use JWT claims (user_type='A' or 'U') to enforce the same rules per-request.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.utils.security import decode_token as _decode_token

_bearer_scheme = HTTPBearer(auto_error=True)


class CurrentUser:
    """Minimal user context extracted from JWT — replaces CARDDEMO-COMMAREA user fields."""

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
    """
    Decode and validate the JWT Bearer token.

    COBOL origin: Replaces EIBCALEN=0 check at the top of every CICS program.
    If EIBCALEN = 0: XCTL to COSGN00C (unauthenticated) — here we return 401.

    Returns a CurrentUser with user_id and user_type from the JWT claims.
    """
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
    """
    Enforce admin-only access to an endpoint.

    COBOL origin: Admin programs (COTRTLIC, COTRTUPC, COUSR0xC) were only accessible
    from COADM01C admin menu, which was only rendered for user_type='A'.
    Here we explicitly gate each admin endpoint with this dependency.

    Returns the CurrentUser if admin; raises 403 Forbidden otherwise.
    """
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
