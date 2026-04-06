"""JWT authentication dependency shared across all routers.

All transaction, bill-payment, and report endpoints require a valid Bearer token.
This mirrors the CICS COMMAREA security model where the user-id and user-type
are passed in CDEMO-USER-ID / CDEMO-USER-TYPE.
"""

from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


class TokenData(BaseModel):
    """Decoded JWT payload."""

    user_id: str
    user_type: str = "regular"


class User(BaseModel):
    """Authenticated user context — maps to COBOL CDEMO-USER-ID / CDEMO-USER-TYPE."""

    user_id: str
    user_type: str = "regular"


def create_access_token(user_id: str, user_type: str = "regular") -> str:
    """Create a signed JWT token."""
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": user_id, "user_type": user_type, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """FastAPI dependency: decode and validate JWT token.

    Raises HTTP 401 if the token is missing, expired, or invalid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str | None = payload.get("sub")
        user_type: str = payload.get("user_type", "regular")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    return User(user_id=user_id, user_type=user_type)
