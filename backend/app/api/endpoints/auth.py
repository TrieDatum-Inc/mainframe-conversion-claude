"""
Authentication API endpoints.

COBOL origin: COSGN00C (Transaction CC00) — the CardDemo application entry point.

Endpoints:
    POST /api/v1/auth/login   → PROCESS-ENTER-KEY paragraph (user authentication)
    POST /api/v1/auth/logout  → RETURN-TO-PREV-SCREEN paragraph (PF3 exit / session end)

The router is thin — no business logic lives here. All logic delegates to AuthService.
"""

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.common import MessageResponse
from app.services.auth_service import AuthService
from app.utils.security import decode_access_token
from app.exceptions.errors import InvalidTokenError

try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address
    limiter = Limiter(key_func=get_remote_address)
    RATE_LIMITING_AVAILABLE = True
except ImportError:
    RATE_LIMITING_AVAILABLE = False

router = APIRouter(prefix="/auth", tags=["Authentication"])
security_scheme = HTTPBearer()


def _get_client_ip(request: Request) -> str:
    """Extract client IP for audit logging and rate limiting."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and issue JWT token",
    description=(
        "Validates user credentials and returns a JWT access token on success. "
        "Maps COSGN00C PROCESS-ENTER-KEY: reads users table (USRSEC VSAM equivalent), "
        "verifies bcrypt password (replaces plain-text comparison), "
        "and determines redirect based on user_type (replaces CICS XCTL routing)."
    ),
    responses={
        200: {"description": "Authentication successful; JWT token issued"},
        401: {"description": "Invalid credentials (user not found OR wrong password — identical response to prevent enumeration)"},
        422: {"description": "Validation error — user_id or password blank/too long"},
        429: {"description": "Too many login attempts — rate limited"},
    },
)
async def login(
    request: Request,
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """
    Authenticate user credentials and issue a JWT access token.

    COBOL origin: COSGN00C PROCESS-ENTER-KEY (lines 118-183).
    Rate limited to 5 requests/minute per IP to prevent brute-force attacks.
    """
    client_ip = _get_client_ip(request)
    return await AuthService.login(
        request=credentials,
        db=db,
        client_ip=client_ip,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Invalidate the current JWT token",
    description=(
        "Revokes the current access token so it cannot be reused. "
        "Maps COSGN00C RETURN-TO-PREV-SCREEN (PF3 key): the COBOL program executed "
        "a bare EXEC CICS RETURN (no TRANSID) to terminate the CICS task. "
        "The modern equivalent revokes the JWT's jti claim."
    ),
    responses={
        204: {"description": "Logout successful; token revoked"},
        401: {"description": "Missing or invalid Bearer token"},
    },
)
async def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> None:
    """
    Revoke the current JWT access token.

    COBOL origin: COSGN00C RETURN-TO-PREV-SCREEN paragraph (PF3 path).
    """
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub", "unknown")
    except JWTError:
        # Token already invalid — still return 204 (idempotent logout)
        user_id = "unknown"

    client_ip = _get_client_ip(request)
    await AuthService.logout(
        token=token,
        user_id=user_id,
        client_ip=client_ip,
    )
