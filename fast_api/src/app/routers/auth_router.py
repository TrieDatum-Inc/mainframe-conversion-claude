"""Authentication router — REST API equivalent of COSGN00C (Transaction CC00).

Endpoints:
  POST /auth/login   → COSGN00C PROCESS-ENTER-KEY + READ-USER-SEC-FILE
  POST /auth/logout  → COSGN00C PF3 (SEND-PLAIN-TEXT + RETURN with no TRANSID)
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import get_current_user_info
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, LoginResponse, UserInfo
from app.services.auth_service import AuthenticationError, AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication (COSGN00C)"])


def _get_auth_service(db: Annotated[AsyncSession, Depends(get_db)]) -> AuthService:
    return AuthService(UserRepository(db))


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="User login (COSGN00C / Transaction CC00)",
    description=(
        "Authenticates user against the users table (USRSEC VSAM equivalent). "
        "Both user_id and password are uppercased before comparison (BR-003). "
        "Returns a JWT token and the redirect destination based on user type (BR-006): "
        "/admin-menu for type='A', /main-menu for type='U'."
    ),
    responses={
        200: {"description": "Login successful — JWT token issued"},
        401: {"description": "Invalid credentials (user not found or wrong password)"},
        422: {"description": "Validation error (blank user_id or password — BR-001/BR-002)"},
    },
)
async def login(
    request: LoginRequest,
    auth_service: Annotated[AuthService, Depends(_get_auth_service)],
) -> LoginResponse:
    """Login endpoint.

    Equivalent to COSGN00C PROCESS-ENTER-KEY + READ-USER-SEC-FILE.
    Schema validation already enforces BR-001 (user_id required) and
    BR-002 (password required) before this handler runs.
    """
    try:
        return await auth_service.authenticate(request)
    except AuthenticationError as exc:
        # Map COBOL error messages to 401 responses
        # BR-004: "User not found" (RESP=13)
        # BR-005: "Wrong Password"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
        ) from exc


@router.post(
    "/logout",
    summary="User logout (COSGN00C PF3 / SEND-PLAIN-TEXT)",
    description=(
        "Ends the user session. Equivalent to pressing PF3 on the signon screen: "
        "COSGN00C BR-007: sends 'Thank you for using CardDemo application...' "
        "and issues CICS RETURN with no TRANSID. "
        "Client must discard the JWT token."
    ),
    responses={
        200: {"description": "Logout successful"},
        401: {"description": "Not authenticated"},
    },
)
async def logout(
    current_user: Annotated[UserInfo, Depends(get_current_user_info)],
) -> dict[str, str]:
    """Logout endpoint — equivalent to COSGN00C PF3 handler.

    COBOL: MOVE CCDA-MSG-THANK-YOU TO WS-MESSAGE
           PERFORM SEND-PLAIN-TEXT
    Server-side JWT invalidation would require a token blacklist;
    this implementation relies on client-side token deletion (stateless JWT).
    """
    logger.info("User %s logged out", current_user.user_id)
    return {
        "message": "Thank you for using CardDemo application...",
        "user_id": current_user.user_id,
    }


@router.get(
    "/me",
    response_model=UserInfo,
    summary="Get current authenticated user info",
    description="Returns the current user's info from JWT claims (COMMAREA equivalent).",
)
async def get_me(
    current_user: Annotated[UserInfo, Depends(get_current_user_info)],
) -> UserInfo:
    """Return current user info from JWT token claims."""
    return current_user
