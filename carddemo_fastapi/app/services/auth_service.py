"""Authentication service ported from COSGN00C.cbl.

COSGN00C authenticates users against the USRSEC file and routes
to admin menu (COADM01C) or user menu (COMEN01C) based on user type.
"""

from datetime import datetime, timedelta, timezone

from jose import jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.exceptions import AuthenticationError


def authenticate_user(db: Session, user_id: str, password: str) -> dict:
    """Authenticate user and return JWT token.

    Ports COSGN00C logic:
    1. READ USRSEC by user_id (line ~132)
    2. If RESP=13 (not found): "User not found. Try again ..."
    3. If password mismatch: "Wrong Password. Try again ..."
    4. If match: return user_type ('A' or 'U')
    """
    user = db.query(User).filter(User.usr_id == user_id.upper()).first()

    if not user:
        raise AuthenticationError("User not found. Try again ...")

    if user.usr_pwd != password:
        raise AuthenticationError("Wrong Password. Try again ...")

    # Generate JWT (replaces COMMAREA with CDEMO-USER-ID, CDEMO-USER-TYPE)
    token = create_access_token(user.usr_id, user.usr_type)

    return {
        "token": token,
        "user_id": user.usr_id,
        "user_type": user.usr_type,
    }


def create_access_token(user_id: str, user_type: str) -> str:
    """Create JWT token carrying user context (replaces COMMAREA)."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_EXPIRE_MINUTES
    )
    payload = {
        "user_id": user_id,
        "user_type": user_type,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
