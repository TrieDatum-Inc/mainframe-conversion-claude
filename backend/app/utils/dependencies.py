"""
FastAPI dependency functions for authentication and authorization.

COBOL origin:
  get_current_user → replaces EIBCALEN=0 check + MOVE DFHCOMMAREA TO CARDDEMO-COMMAREA
  require_admin    → replaces implicit admin-only access enforced by CICS menu routing
                     (COUSR00C/01C/02C/03C are only reachable from COADM01C,
                      which is only shown to users with CDEMO-USER-TYPE='A')
"""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.exceptions.errors import AdminRequiredError, UnauthorizedError
from app.utils.security import decode_access_token

_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> dict:
    """
    Extract and validate the JWT from the Authorization header.

    COBOL origin: Replaces EIBCALEN check at top of every COUSR program:
      IF EIBCALEN = 0: MOVE 'COSGN00C' TO CDEMO-TO-PROGRAM; PERFORM RETURN-TO-PREV-SCREEN

    Returns the decoded JWT payload dict containing:
      sub       - user_id
      user_type - 'A' or 'U'
    Raises 401 if token is absent or invalid.
    """
    if credentials is None:
        raise UnauthorizedError()

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise UnauthorizedError()

    return payload


def require_admin(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Enforce admin-only access for user management endpoints.

    COBOL origin: All COUSR programs (00C, 01C, 02C, 03C) are accessible
    only from COADM01C (admin menu), which is shown only when
    CDEMO-USER-TYPE='A'. This dependency enforces that gate programmatically.

    Raises 403 if user_type is not 'A'.
    Returns the current user payload for use in the endpoint.
    """
    if current_user.get("user_type") != "A":
        raise AdminRequiredError()
    return current_user
