"""
Authentication API endpoints.

COBOL origin: COSGN00C (Transaction: CC00)
Replaces the BMS SEND/RECEIVE MAP cycle with REST API endpoints.

Endpoints:
    POST /api/v1/auth/login   — replaces COSGN00C PROCESS-ENTER-KEY
    POST /api/v1/auth/logout  — replaces COSGN00C RETURN-TO-PREV-SCREEN (PF3 path)
    GET  /api/v1/auth/me      — returns current user info (no COBOL equivalent)
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.common import MessageResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.utils.security import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Sign on — replaces COSGN00C PROCESS-ENTER-KEY",
    description=(
        "Authenticate with user ID and password. "
        "Replaces USRSEC VSAM READ + plain-text password comparison. "
        "Returns a JWT token and redirect URL based on user type."
    ),
)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """
    COBOL origin: COSGN00C PROCESS-ENTER-KEY paragraph (lines 118-183).

    Original COBOL flow:
        1. MOVE FUNCTION TRIM(USERIDI) TO WS-USER-ID
        2. IF WS-USER-ID = SPACES → error
        3. EXEC CICS READ DATASET(USRSEC) RIDFLD(WS-USER-ID)
        4. IF RESP = NOTFND → 'Invalid User ID or Password'
        5. IF SEC-USR-PWD != WS-USER-PWD → 'Invalid User ID or Password'
        6. IF SEC-USR-TYPE = 'A' → XCTL COADM01C
           ELSE → XCTL COMEN01C

    Modern flow:
        - bcrypt verification replaces plain-text comparison
        - JWT token replaces COMMAREA state passing
        - redirect_to in response replaces CICS XCTL routing
        - Uniform 401 for both not-found and wrong-password (preserves COBOL behavior)
    """
    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo)
    return await auth_service.authenticate_user(request)


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Sign off — replaces COSGN00C RETURN-TO-PREV-SCREEN (PF3)",
    description=(
        "Invalidate the current session. "
        "Replaces COSGN00C PF3 path: display CCDA-MSG-THANK-YOU then bare CICS RETURN."
    ),
)
async def logout(
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    """
    COBOL origin: COSGN00C RETURN-TO-PREV-SCREEN paragraph (lines 188-200).

    Original COBOL:
        MOVE CCDA-MSG-THANK-YOU TO WS-MESSAGE
        PERFORM SEND-SIGNON-SCREEN
        EXEC CICS RETURN (bare — no TRANSID; session ends)

    Modern: returns a thank-you message. Frontend clears the stored JWT token.
    In production with token deny-listing, this endpoint would blacklist the JTI.
    """
    return MessageResponse(
        message=f"Thank you for using CardDemo, {current_user.first_name}. Have a nice day!"
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user info",
    description="Returns the profile of the currently authenticated user.",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    No direct COBOL equivalent.

    The COBOL system embedded user info in the COMMAREA (CDEMO-USER-FNAME,
    CDEMO-USER-LNAME, CDEMO-USER-TYPE). This endpoint provides the same
    information to the frontend via the JWT subject claim.
    """
    return UserResponse.model_validate(current_user)
