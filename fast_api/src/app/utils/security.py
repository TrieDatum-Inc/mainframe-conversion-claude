"""Security utilities for password hashing and JWT token management.

Replaces COBOL plaintext password comparison in COSGN00C READ-USER-SEC-FILE:
  COBOL: IF SEC-USR-PWD = WS-USER-PWD  (plaintext compare, BR-005)
  Modern: bcrypt verify (constant-time comparison, bcrypt hash)

JWT token replaces CARDDEMO-COMMAREA session state passed between CICS programs.
"""
import logging
from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from app.config import settings
from app.schemas.auth import TokenPayload

logger = logging.getLogger(__name__)


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using bcrypt.

    Note: COBOL BR-003 uppercases input before comparison.
    The caller should uppercase before hashing for consistency.
    """
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash — replaces COBOL SEC-USR-PWD = WS-USER-PWD.

    COBOL BR-003: input must already be uppercased before calling this function.
    Returns False (wrong password) rather than raising — mirrors COBOL flow.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        logger.warning("Password verification error (likely invalid hash format)")
        return False


def create_access_token(payload: TokenPayload) -> str:
    """Create a signed JWT token — replaces CARDDEMO-COMMAREA passed on CICS RETURN.

    Token carries:
      sub       → CDEMO-USER-ID
      user_type → CDEMO-USER-TYPE (A or U)
      first_name, last_name → user display info

    Token expiry replaces CICS transaction timeout.
    """
    expire = datetime.now(UTC) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    data = payload.model_dump(exclude={"exp"})
    data["exp"] = int(expire.timestamp())
    return jwt.encode(data, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> TokenPayload:
    """Decode and validate a JWT token — replaces CICS COMMAREA length/content check.

    Raises JWTError on invalid/expired tokens.
    """
    payload = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm],
    )
    return TokenPayload(**payload)
