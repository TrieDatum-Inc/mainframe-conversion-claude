"""
Authentication API endpoints.

COBOL origin: COSGN00C (Transaction CC00) — the CardDemo application entry point.

Endpoints:
    POST /api/v1/auth/login   → PROCESS-ENTER-KEY paragraph (user authentication)
    POST /api/v1/auth/logout  → RETURN-TO-PREV-SCREEN paragraph (PF3 exit / session end)

The router is thin — no business logic lives here. All logic delegates to AuthService.
"""

import ipaddress

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth_service import AuthService
from app.utils.security import decode_access_token

# Refactoring note (security review finding #1):
# Import the shared Limiter instance from app.utils.rate_limit so that the
# same object is registered on app.state (in main.py) AND used by the
# @limiter.limit() decorator below. A locally constructed second Limiter
# instance would not share state with app.state.limiter, silently defeating
# the rate limit. The shared module pattern prevents this mistake.
from app.utils.rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["Authentication"])
security_scheme = HTTPBearer()

# ---------------------------------------------------------------------------
# Trusted proxy networks for X-Forwarded-For validation.
# Refactoring note (security review finding #2):
# X-Forwarded-For is only trusted when the direct TCP connection originates
# from a private/loopback address (i.e., a reverse proxy we control).
# Any client can forge this header; accepting it unconditionally allows
# per-IP rate limiting to be bypassed by cycling through arbitrary IPs.
# ---------------------------------------------------------------------------
_TRUSTED_PROXY_NETS = [
    ipaddress.ip_network("127.0.0.0/8"),    # loopback
    ipaddress.ip_network("10.0.0.0/8"),     # RFC 1918
    ipaddress.ip_network("172.16.0.0/12"),  # RFC 1918
    ipaddress.ip_network("192.168.0.0/16"), # RFC 1918
    ipaddress.ip_network("::1/128"),        # IPv6 loopback
]


def _get_client_ip(request: Request) -> str:
    """
    Extract the real client IP for audit logging and rate limiting.

    Only trusts X-Forwarded-For when the direct TCP connection arrives from
    a known trusted proxy (private/loopback range). Falls back to the
    direct connection IP for all other cases.
    """
    client_host = request.client.host if request.client else None
    if client_host:
        try:
            addr = ipaddress.ip_address(client_host)
            is_trusted_proxy = any(addr in net for net in _TRUSTED_PROXY_NETS)
            if is_trusted_proxy:
                xff = request.headers.get("X-Forwarded-For")
                if xff:
                    return xff.split(",")[0].strip()
        except ValueError:
            pass
    return client_host or "unknown"


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
@limiter.limit("5/minute")
async def login(
    request: Request,
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """
    Authenticate user credentials and issue a JWT access token.

    COBOL origin: COSGN00C PROCESS-ENTER-KEY (lines 118-183).
    Rate limited to 5 requests/minute per IP to prevent brute-force attacks.

    Refactoring note (security review finding #1):
    The @limiter.limit("5/minute") decorator is now applied using the shared
    Limiter instance from app.utils.rate_limit. The request parameter is
    required by slowapi to resolve the limiter from request.app.state.limiter.
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
