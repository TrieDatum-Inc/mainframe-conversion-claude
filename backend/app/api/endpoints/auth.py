"""
Authentication API endpoints — COSGN00C (Transaction: CC00).

POST /api/v1/auth/login   — COSGN00C PROCESS-ENTER-KEY
POST /api/v1/auth/logout  — COSGN00C PF3 path
GET  /api/v1/auth/me      — no COBOL equivalent
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser, get_current_user
from app.database import get_db
from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.common import MessageResponse
from app.services.auth_service import login as auth_login

router = APIRouter(prefix="/auth", tags=["Authentication"])

DbDep = Annotated[AsyncSession, Depends(get_db)]
AuthDep = Annotated[CurrentUser, Depends(get_current_user)]


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(request: LoginRequest, db: DbDep) -> LoginResponse:
    """Authenticate user — replaces COSGN00C PROCESS-ENTER-KEY."""
    return await auth_login(request.user_id, request.password, db)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(current_user: AuthDep) -> MessageResponse:
    """Sign out — replaces COSGN00C PF3 / EXEC CICS RETURN."""
    return MessageResponse(message="Logged out successfully")


@router.get("/me")
async def me(current_user: AuthDep) -> dict:
    """Return current user context from JWT claims."""
    return {"user_id": current_user.user_id, "user_type": current_user.user_type}
