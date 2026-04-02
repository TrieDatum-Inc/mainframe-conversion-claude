"""
Authentication routes.
Maps COSGN00C (CC00 transaction) sign-on/sign-off logic.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError
from app.domain.services.auth_service import authenticate_user
from app.infrastructure.database import get_db
from app.schemas.auth_schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentication (COSGN00C)"])


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Sign on (COSGN00C - CC00)",
    description="""
    Authenticates a user against the USRSEC file (SEC-USER-DATA).

    Business rules (from COSGN00C spec):
    - BR-SGN-001: Both user_id and password are mandatory
    - BR-SGN-002: user_id is upper-cased before lookup
    - BR-SGN-003: Password is compared (original: plain-text; API: bcrypt)
    - BR-SGN-004: User type 'A' -> Admin; 'U' -> Regular User

    Error responses:
    - 'User not found. Try again ...' -> 401
    - 'Wrong Password. Try again ...' -> 401
    - 'Unable to verify the User ...' -> 500
    """,
)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    try:
        return await authenticate_user(request, db)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "CDERR401", "message": exc.message},
            headers={"WWW-Authenticate": "Bearer"},
        )
