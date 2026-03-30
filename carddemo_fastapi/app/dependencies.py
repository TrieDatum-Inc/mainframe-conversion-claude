"""Common dependencies for FastAPI route handlers.

Replaces the CICS COMMAREA pattern for passing user context
between programs. JWT token carries user_id and user_type,
equivalent to CDEMO-USER-ID and CDEMO-USER-TYPE in COCOM01Y.cpy.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Extract and validate user context from JWT token.

    Equivalent to reading CDEMO-USER-ID and CDEMO-USER-TYPE
    from the CARDDEMO-COMMAREA (COCOM01Y.cpy).

    Returns:
        dict with 'user_id' and 'user_type' keys.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id: str = payload.get("user_id")
        user_type: str = payload.get("user_type")
        if user_id is None or user_type is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        return {"user_id": user_id, "user_type": user_type}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Require admin user type for admin-only routes.

    Equivalent to the COADM01C check where CDEMO-USER-TYPE must be 'A'.
    Maps the COBOL error: "No access - Admin Only option".
    """
    if current_user.get("user_type") != "A":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No access - Admin Only option",
        )
    return current_user
