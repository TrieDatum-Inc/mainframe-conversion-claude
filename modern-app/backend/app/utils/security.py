"""Security utilities: password hashing and JWT creation/verification.

COBOL equivalents:
- hash_password / verify_password  ->  plain-text compare SEC-USR-PWD = WS-PASSWD
  (COBOL stored plain text; we use bcrypt instead)
- create_access_token              ->  MOVE CDEMO-USER-ID / CDEMO-USER-TYPE to COMMAREA
- decode_access_token              ->  used by dependencies to re-derive COMMAREA context
"""

from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.schemas.auth import TokenPayload

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Mapping from COBOL RETURN-CODE equivalents to JWT error messages
_JWT_DECODE_ERROR = "Could not validate credentials"


def hash_password(plain_password: str) -> str:
    """Return a bcrypt hash of the given password."""
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if plain_password matches the stored bcrypt hash.

    COBOL equivalent: IF SEC-USR-PWD = WS-PASSWD
    Both sides are already uppercased by the Pydantic validator.
    """
    return _pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: str, user_type: str) -> str:
    """Create a signed JWT with user_id and user_type claims.

    Maps to COSGN00C setting CDEMO-USER-ID and CDEMO-USER-TYPE in the COMMAREA
    before XCTLing to the target menu program.
    """
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict = {
        "sub": user_id,
        "user_type": user_type,
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> TokenPayload:
    """Decode and verify a JWT; raise ValueError on any failure.

    Raises:
        ValueError: token is expired, tampered, or structurally invalid.
    """
    try:
        raw = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return TokenPayload(sub=raw["sub"], user_type=raw["user_type"])
    except (JWTError, KeyError) as exc:
        raise ValueError(_JWT_DECODE_ERROR) from exc


def is_token_expired(token: str) -> bool:
    """Return True if the token's exp claim is in the past."""
    try:
        decode_access_token(token)
        return False
    except ValueError:
        return True
