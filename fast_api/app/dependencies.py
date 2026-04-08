"""
FastAPI shared dependencies.

Replaces CICS COMMAREA (COCOM01Y) for session/context passing.
JWT tokens carry the state that COMMAREA held:
  CDEMO-USER-ID   → token.sub
  CDEMO-USER-TYPE → token.role ('A' or 'U')

Security levels enforced here match original CICS transaction security:
  - require_authenticated: any logged-in user
  - require_admin: CDEMO-USRTYP-ADMIN (SEC-USR-TYPE = 'A') only
"""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.user import USER_TYPE_ADMIN
from app.schemas.auth import TokenData

settings = get_settings()

bearer_scheme = HTTPBearer(auto_error=False)


def _decode_token(token: str) -> TokenData:
    """
    Decode and validate a JWT bearer token.

    Raises HTTP 401 if token is invalid or expired.
    Maps to CICS COMMAREA validation — if EIBCALEN = 0 or
    commarea data is invalid, COSGN00C sends the signon screen.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        sub: str = payload.get("sub", "")
        role: str = payload.get("role", "U")
        if not sub:
            raise credentials_exception
        return TokenData(sub=sub, role=role)
    except JWTError:
        raise credentials_exception


async def get_current_user(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]) -> TokenData:
    """
    Dependency: require a valid authenticated user.

    Equivalent to CICS COMMAREA check — if EIBCALEN > 0 and
    CDEMO-USER-ID is populated, the user is authenticated.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _decode_token(credentials.credentials)


async def require_admin(current_user: Annotated[TokenData, Depends(get_current_user)]) -> TokenData:
    """
    Dependency: require admin user (CDEMO-USRTYP-ADMIN = 'A').

    Used for:
      - COUSR01C/02C/03C (user management — admin only)
      - COACTUPC group_id field (only admin can change ACCT-GROUP-ID)
    """
    if current_user.role != USER_TYPE_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


# Type aliases for cleaner endpoint signatures
CurrentUser = Annotated[TokenData, Depends(get_current_user)]
AdminUser = Annotated[TokenData, Depends(require_admin)]
DBSession = Annotated[AsyncSession, Depends(get_db)]
