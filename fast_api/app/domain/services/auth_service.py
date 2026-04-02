"""
Authentication service.
Maps COSGN00C sign-on program logic to FastAPI JWT auth.

Business rules preserved:
  BR-SGN-001: User ID and password are mandatory
  BR-SGN-002: User ID converted to upper-case
  BR-SGN-003: Password comparison (bcrypt replaces plain-text)
  BR-SGN-004: User type 'A' -> Admin, 'U' -> Regular User
  BR-SGN-005: PGM-CONTEXT = 0 (CDEMO-PGM-ENTER) set on login success
  BR-SGN-006: PF3 -> logout (token expiry handles this)
"""

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthenticationError
from app.infrastructure.repositories.user_repository import UserRepository
from app.schemas.auth_schemas import LoginRequest, TokenResponse


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against stored hash.
    Maps COSGN00C: IF SEC-USR-PWD = WS-USER-PWD (plain text in original).
    """
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(data: dict) -> str:
    """
    Create JWT access token.
    Encodes CARDDEMO-COMMAREA session state:
      CDEMO-USER-ID, CDEMO-USER-TYPE, CDEMO-PGM-CONTEXT=0
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict:
    """Decode and validate JWT token. Raises AuthenticationError if invalid."""
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        return payload
    except JWTError as exc:
        raise AuthenticationError("Invalid or expired token.") from exc


async def authenticate_user(
    request: LoginRequest,
    db: AsyncSession,
) -> TokenResponse:
    """
    Authenticate user — maps COSGN00C READ-USER-SEC-FILE paragraph.

    Steps (from spec section 7.6):
    1. Read USRSEC by WS-USER-ID (upper-cased)
    2. If RESP=NOTFND: error 'User not found. Try again ...'
    3. If found: compare password
    4. If password match: populate COMMAREA and route
    5. If wrong password: error 'Wrong Password. Try again ...'
    """
    repo = UserRepository(db)

    # BR-SGN-002: user_id is already upper-cased by Pydantic validator
    try:
        user = await repo.get_by_id(request.user_id)
    except Exception:
        # Maps COSGN00C RESP=NOTFND handling
        raise AuthenticationError("User not found. Try again ...")

    # BR-SGN-003: Password comparison
    if not verify_password(request.password, user.pwd_hash):
        raise AuthenticationError("Wrong Password. Try again ...")

    # BR-SGN-004: Set user type in token (maps CDEMO-USER-TYPE)
    token_data = {
        "sub": user.usr_id,
        "user_type": user.usr_type,
        "first_name": user.first_name,
        "last_name": user.last_name,
        # BR-SGN-005: CDEMO-PGM-CONTEXT = 0 (first entry)
        "pgm_context": 0,
    }

    access_token = create_access_token(token_data)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.usr_id,
        user_type=user.usr_type,
        first_name=user.first_name,
        last_name=user.last_name,
    )
