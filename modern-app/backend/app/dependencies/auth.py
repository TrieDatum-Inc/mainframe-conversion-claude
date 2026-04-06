"""Reusable FastAPI auth dependencies.

Maps to COBOL COMMAREA propagation: every program checks CDEMO-USER-TYPE
to decide if it should proceed or redirect. Here we express those same
guards as injectable FastAPI dependencies.

- get_current_user  -> ensures a valid JWT is present (authenticated)
- require_admin     -> ensures CDEMO-USER-TYPE = 'A'  (admin check)

Other modules (user management, transaction types) depend on require_admin
to replicate the admin-only access control from COADM01C.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.models.user import User, UserType
from app.schemas.auth import TokenPayload
from app.utils.security import decode_access_token

# Tells FastAPI where clients obtain a token (used in OpenAPI UI)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login/form")

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

_ADMIN_ONLY_EXCEPTION = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Administrator access required",
)


def _extract_token_payload(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    """Decode the Bearer token and return its claims.

    Raises HTTP 401 if the token is missing, expired, or tampered.
    """
    try:
        return decode_access_token(token)
    except ValueError as exc:
        raise _CREDENTIALS_EXCEPTION from exc


def get_current_user(payload: TokenPayload = Depends(_extract_token_payload)) -> TokenPayload:
    """Return the decoded token payload for the authenticated caller.

    COBOL equivalent: any program validates EIBCALEN > 0 and that
    CDEMO-USER-ID is populated in the COMMAREA before proceeding.

    Usage:
        @router.get("/some-endpoint")
        async def handler(current_user: TokenPayload = Depends(get_current_user)):
            ...
    """
    return payload


def require_admin(payload: TokenPayload = Depends(get_current_user)) -> TokenPayload:
    """Enforce that the caller is an admin user (user_type == 'A').

    COBOL equivalent: COADM01C validates CDEMO-USER-TYPE = 'A' before
    allowing access to admin menu options. This dependency is reusable
    by all admin-only endpoints (user management, transaction type maintenance).

    Raises HTTP 403 if the caller is not an admin.
    """
    if payload.user_type != UserType.ADMIN:
        raise _ADMIN_ONLY_EXCEPTION
    return payload


# Convenience type aliases for use in endpoint signatures
CurrentUser = TokenPayload
AdminUser = TokenPayload
