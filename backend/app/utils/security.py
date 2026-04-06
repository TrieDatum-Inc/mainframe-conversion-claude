"""
Security utilities: JWT creation/verification and bcrypt password hashing.

COBOL origin:
  bcrypt hashing → replaces plain-text SEC-USR-PWD X(08) in USRSEC VSAM.
  JWT creation   → replaces CARDDEMO-COMMAREA passed between CICS programs.
  JWT decoding   → replaces EIBCALEN check and COMMAREA user-type read.

Security rules from spec section 7:
  - Passwords stored only as bcrypt hashes; never in plain text.
  - JWT sub = user_id, user_type claim drives RBAC.
  - Admin endpoints require user_type='A' in JWT claims.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

logger = logging.getLogger(__name__)

# bcrypt context — replaces plain-text SEC-USR-PWD comparison in COSGN00C
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """
    Hash a plain-text password with bcrypt.

    COBOL origin: Replaces MOVE PASSWDI TO SEC-USR-PWD (plain-text storage).
    The hash is stored in users.password_hash; the original password is discarded.
    """
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a stored bcrypt hash.

    COBOL origin: Replaces COSGN00C: IF CDEMO-SIGNON-PASSWD = SEC-USR-PWD
    (plain-text comparison in legacy system).
    """
    return _pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: str, user_type: str) -> str:
    """
    Create a signed JWT access token.

    COBOL origin: Replaces CICS RETURN COMMAREA passing CDEMO-USER-ID and
    CDEMO-USER-TYPE between programs. JWT is stateless; COMMAREA was stateful.

    JWT claims:
      sub       = user_id   (CDEMO-USER-ID X(08))
      user_type = user_type (CDEMO-USER-TYPE X(01): 'A' or 'U')
      iat       = issued at
      exp       = issued at + jwt_expire_minutes
      iss       = 'carddemo-api'
    """
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": user_id,
        "user_type": user_type,
        "iat": now,
        "exp": expire,
        "iss": "carddemo-api",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT access token. Returns the payload dict or None.

    COBOL origin: Replaces reading DFHCOMMAREA + checking EIBCALEN > 0.
    Returns None on any decode failure (expired, tampered, invalid).
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as exc:
        logger.debug("JWT decode failed: %s", exc)
        return None
