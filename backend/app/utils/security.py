"""
Security utilities: JWT creation/verification and bcrypt password hashing.

COBOL origin: Replaces COSGN00C password authentication and CICS session management.

Key improvements over legacy system:
1. bcrypt replaces plain-text SEC-USR-PWD X(8) comparison (timing-safe)
2. JWT replaces indefinite CICS session (bounded 1-hour TTL)
3. get_current_user dependency replaces EIBCALEN=0 check for unauthenticated entry
4. require_admin replaces CDEMO-USRTYP-ADMIN 88-level condition check
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db

# Password hashing context — bcrypt with configurable work factor
# COBOL equivalent: plain-text comparison `IF SEC-USR-PWD = WS-USER-PWD`
# Modern: constant-time bcrypt verification prevents timing attacks
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.bcrypt_rounds,
)

# JWT bearer scheme for FastAPI dependency injection
security_scheme = HTTPBearer(auto_error=False)


def hash_password(plain_password: str) -> str:
    """
    Hash a plain-text password using bcrypt.

    COBOL origin: Replaces SEC-USR-PWD X(8) plain-text storage in USRSEC VSAM.
    The COBOL system stored and compared passwords as raw bytes:
        IF CDEMO-SIGNON-PASSWD = SEC-USR-PWD (COSGN00C line ~290)
    This is replaced by a one-way bcrypt hash. Password is never recoverable.
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against its bcrypt hash.

    COBOL origin: Replaces byte-by-byte plain-text comparison in COSGN00C.
    Uses constant-time comparison to prevent timing side-channel attacks.
    bcrypt internally handles salt extraction from the hash string.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, user_type: str) -> str:
    """
    Create a signed JWT access token.

    COBOL origin: Replaces CARDDEMO-COMMAREA population in COSGN00C PROCESS-ENTER-KEY:
        MOVE CDEMO-USER-ID    → JWT claim 'sub'
        MOVE CDEMO-USER-TYPE  → JWT claim 'user_type'
        EXEC CICS RETURN TRANSID COMMAREA → token carries state across stateless HTTP

    JWT payload:
        sub: user_id (CDEMO-USER-ID)
        user_type: 'A' or 'U' (CDEMO-USER-TYPE / CDEMO-USRTYP-ADMIN)
        exp: now + JWT_EXPIRE_MINUTES (replaces indefinite CICS session)
        iat: issued-at timestamp
        iss: issuer identifier
        jti: unique token ID (enables revocation / logout deny-list)
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.jwt_expire_minutes)

    payload = {
        "sub": subject,
        "user_type": user_type,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "iss": "carddemo-api",
        "jti": str(uuid4()),
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.

    Raises ValueError if the token is invalid or expired.
    Used by get_current_user to extract user claims.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    FastAPI dependency: validate JWT and return the authenticated User model.

    COBOL origin: Replaces EIBCALEN=0 check in every CICS program's MAIN-PARA:
        IF EIBCALEN = 0: EXEC CICS XCTL PROGRAM('COSGN00C')
    In COBOL, EIBCALEN=0 means no COMMAREA — unauthenticated entry.
    This dependency raises HTTP 401 for any request without a valid JWT.

    Must be imported lazily to avoid circular import with user_repository.
    """
    from app.repositories.user_repository import UserRepository

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error_code": "INVALID_TOKEN",
            "message": "Could not validate credentials",
        },
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    try:
        payload = decode_token(credentials.credentials)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except ValueError:
        raise credentials_exception

    # Validate user still exists in database
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if user is None:
        raise credentials_exception

    return user


async def require_admin(
    current_user=Depends(get_current_user),
):
    """
    FastAPI dependency: require the current user to have admin role ('A').

    COBOL origin: Replaces CDEMO-USRTYP-ADMIN 88-level condition check used
    to gate access to admin screens (COADM01C and its sub-programs):
        IF CDEMO-USRTYP-ADMIN: proceed
        ELSE: send error / XCTL back to signon

    All user management endpoints (COUSR00C/01C/02C/03C) and transaction type
    endpoints (COTRTLIC/COTRTUPC) require this dependency.
    """
    if current_user.user_type != "A":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "ADMIN_REQUIRED",
                "message": "This function requires administrator privileges",
            },
        )
    return current_user
