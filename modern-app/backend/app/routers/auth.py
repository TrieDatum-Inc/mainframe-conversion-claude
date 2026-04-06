"""Authentication router.

Endpoints:
  POST /api/auth/login       — JSON login (primary endpoint for frontend)
  POST /api/auth/login/form  — OAuth2 form-compatible login (for Swagger UI)
  POST /api/auth/logout      — Token invalidation (stateless: client discards token)
  GET  /api/auth/me          — Return current user info from JWT

COBOL → HTTP status code mapping:
  USRSEC NOTFND              -> HTTP 401  ("User not found")
  Password mismatch          -> HTTP 401  ("Invalid credentials")
  Other VSAM errors          -> HTTP 500  ("Unable to verify the user")
  Blank USERID / PASSWD      -> HTTP 422  (Pydantic validation error)
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, LogoutResponse, Token, UserResponse
from app.utils.security import create_access_token, verify_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _fetch_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    """Fetch a User row by user_id; return None if not found."""
    result = await db.execute(select(User).where(User.user_id == user_id))
    return result.scalar_one_or_none()


def _authenticate_user(user: User | None, password: str) -> User:
    """Validate user existence and password; raise HTTP 401 on failure.

    COBOL equivalents:
      - USRSEC READ RESP=NOTFND  -> "User not found"
      - SEC-USR-PWD != WS-PASSWD -> "Wrong Password"
    Both conditions return the same HTTP 401 to avoid user enumeration.
    """
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def _build_login_response(user: User) -> LoginResponse:
    """Build the LoginResponse from a validated User model."""
    token = create_access_token(user_id=user.user_id, user_type=user.user_type)
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """Authenticate a user and return a JWT access token.

    Implements the full COSGN00C authentication flow:
    1. Both fields are uppercased (handled by Pydantic validator).
    2. User record is looked up in the users table (was USRSEC VSAM).
    3. Password is verified with bcrypt (was plain-text compare in COBOL).
    4. JWT is issued carrying user_id and user_type claims
       (was COMMAREA CDEMO-USER-ID / CDEMO-USER-TYPE).
    """
    user = await _fetch_user_by_id(db, credentials.user_id)
    validated_user = _authenticate_user(user, credentials.password)
    logger.info("Successful login for user_id=%s", validated_user.user_id)
    return _build_login_response(validated_user)


@router.post("/login/form", response_model=Token, status_code=status.HTTP_200_OK)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    """OAuth2 form-compatible login for Swagger UI token flow.

    The username field maps to user_id; both are uppercased to match COBOL
    behaviour. Returns a plain Token (no user info) per OAuth2 spec.
    """
    uppercased_id = form_data.username.strip().upper()
    uppercased_pw = form_data.password.strip().upper()

    user = await _fetch_user_by_id(db, uppercased_id)
    validated_user = _authenticate_user(user, uppercased_pw)
    token = create_access_token(
        user_id=validated_user.user_id, user_type=validated_user.user_type
    )
    return Token(access_token=token)


@router.post("/logout", response_model=LogoutResponse, status_code=status.HTTP_200_OK)
async def logout(
    _current_user=Depends(get_current_user),
) -> LogoutResponse:
    """Invalidate the current session.

    The API is stateless (JWT); logout is acknowledged and the client is
    responsible for discarding the token. This maps to COSGN00C PF3:
    EXEC CICS RETURN (no TRANSID) which ends the CICS session.
    """
    return LogoutResponse()


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_me(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Return the authenticated caller's profile.

    Derives user info from the JWT sub claim (user_id) and fetches fresh
    data from the database to ensure accuracy.
    """
    user = await _fetch_user_by_id(db, current_user.sub)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserResponse.model_validate(user)
