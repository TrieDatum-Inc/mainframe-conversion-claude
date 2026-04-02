"""
FastAPI dependency injection.
Provides current user context from JWT token (equivalent to CARDDEMO-COMMAREA).
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.exceptions import AuthenticationError, AuthorizationError, unauthorized_http, forbidden_http
from app.domain.services.auth_service import decode_access_token
from app.schemas.auth_schemas import UserContext

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserContext:
    """
    Extract current user from JWT Bearer token.
    Maps CARDDEMO-COMMAREA: CDEMO-USER-ID + CDEMO-USER-TYPE.
    """
    try:
        payload = decode_access_token(credentials.credentials)
        user_id: str = payload.get("sub", "")
        user_type: str = payload.get("user_type", "U")
        first_name: str = payload.get("first_name", "")
        last_name: str = payload.get("last_name", "")

        if not user_id:
            raise unauthorized_http("Invalid token: missing user_id.")

        return UserContext(
            user_id=user_id,
            user_type=user_type,
            first_name=first_name,
            last_name=last_name,
        )
    except AuthenticationError as exc:
        raise unauthorized_http(exc.message)


def require_admin(
    current_user: UserContext = Depends(get_current_user),
) -> UserContext:
    """
    Require admin user type ('A').
    Maps COADM01C guard: CDEMO-USRTYP-ADMIN VALUE 'A'.
    Admin-only: user management (COUSR*), transaction types (COTRTLIC/COTRTUPC).
    """
    if current_user.user_type != settings.user_type_admin:
        raise forbidden_http(
            "This operation requires Admin privileges (user type 'A')."
        )
    return current_user


def require_user(
    current_user: UserContext = Depends(get_current_user),
) -> UserContext:
    """
    Require authenticated user (any type).
    Maps COMEN01C guard: any logged-in user.
    """
    return current_user
