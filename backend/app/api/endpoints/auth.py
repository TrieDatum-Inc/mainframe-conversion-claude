"""
Authentication API endpoints — COSGN00C (Transaction: CC00).

POST /api/v1/auth/login   — COSGN00C PROCESS-ENTER-KEY
POST /api/v1/auth/logout  — COSGN00C PF3 path
GET  /api/v1/auth/me      — no COBOL equivalent
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser, get_current_user
from app.database import get_db
from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.common import MessageResponse
from app.services.auth_service import login as auth_login

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)) -> LoginResponse:
    """Authenticate user — replaces COSGN00C PROCESS-ENTER-KEY."""
    return await auth_login(request.user_id, request.password, db)


@router.post("/logout", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def logout(current_user: CurrentUser = Depends(get_current_user)) -> MessageResponse:
    """Sign out — replaces COSGN00C PF3 / EXEC CICS RETURN."""
    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=dict)
async def me(current_user: CurrentUser = Depends(get_current_user)) -> dict:
    """Return current user context from JWT claims."""
    return {"user_id": current_user.user_id, "user_type": current_user.user_type}
