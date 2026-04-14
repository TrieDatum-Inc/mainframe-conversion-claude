"""
Password hashing and JWT token utilities.

COBOL origin: Replaces the plain-text password comparison in COSGN00C:
    IF CDEMO-SIGNON-PASSWD = SEC-USR-PWD  (plain-text equality check)

Security improvements:
  1. Passwords are hashed with bcrypt (rounds=12) — one-way, timing-safe.
  2. JWT tokens replace CICS COMMAREA for session state.
  3. Token blacklist enables explicit logout (PF3 / RETURN-TO-PREV-SCREEN equivalent).
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.BCRYPT_ROUNDS,
)


def hash_password(plain_password: str) -> str:
    """
    Hash a plain-text password using bcrypt.

    COBOL origin: Replaces plain-text SEC-USR-PWD X(8) storage in USRSEC VSAM.
    The original COBOL stored passwords verbatim; bcrypt makes them irreversible.
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against its bcrypt hash.

    Uses constant-time comparison to prevent timing side-channel attacks.

    COBOL origin: Replaces the byte-by-byte equality test:
        IF CDEMO-SIGNON-PASSWD = SEC-USR-PWD
    The original comparison was vulnerable to timing attacks; bcrypt.verify is not.
    """
    return pwd_context.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# JWT token management
# ---------------------------------------------------------------------------

# In-memory token blacklist for logout support.
# Production deployments should replace this with Redis for distributed state.
_token_blacklist: set[str] = set()


def create_access_token(
    subject: str,
    user_type: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Issue a signed JWT access token.

    COBOL origin: Replaces CICS COMMAREA population in PROCESS-ENTER-KEY:
        MOVE 'COSGN00C' TO CDEMO-FROM-PROGRAM
        SET CDEMO-USRTYP-ADMIN TO TRUE/FALSE
        SET CDEMO-SIGNED-ON-FLAG TO TRUE
        MOVE SEC-USR-ID TO CDEMO-USER-ID

    JWT claims:
        sub       → CDEMO-USER-ID
        user_type → SEC-USR-TYPE (A/U)
        iat, exp  → replaces implicit CICS task lifetime
        iss       → identifies this API server
        jti       → unique token ID; stored in blacklist on logout
    """
    if expires_delta is None:
        expires_delta = timedelta(seconds=settings.ACCESS_TOKEN_EXPIRE_SECONDS)

    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    payload = {
        "sub": subject,
        "user_type": user_type,
        "iat": now,
        "exp": expire,
        "iss": "carddemo-api",
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT access token.

    Raises JWTError if the token is invalid, expired, or blacklisted.
    """
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )
    jti = payload.get("jti")
    if jti and jti in _token_blacklist:
        raise JWTError("Token has been revoked")
    return payload


def revoke_token(token: str) -> None:
    """
    Add a token's jti to the blacklist, effectively revoking it.

    COBOL origin: Replaces the PF3 / RETURN-TO-PREV-SCREEN path in COSGN00C
    which executed a bare EXEC CICS RETURN (no TRANSID) to terminate the session.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        jti = payload.get("jti")
        if jti:
            _token_blacklist.add(jti)
    except JWTError:
        # Token was already invalid; nothing to revoke
        pass


def is_token_revoked(jti: str) -> bool:
    """Check whether a token jti has been revoked."""
    return jti in _token_blacklist
