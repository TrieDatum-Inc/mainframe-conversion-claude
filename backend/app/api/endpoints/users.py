"""
User Management API endpoints — COUSR00C/01C/02C/03C (admin-only).

GET    /api/v1/users              → COUSR00C (list)
GET    /api/v1/users/{user_id}    → COUSR02C (get)
POST   /api/v1/users              → COUSR01C (create)
PUT    /api/v1/users/{user_id}    → COUSR02C (update)
DELETE /api/v1/users/{user_id}    → COUSR03C (delete)
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser, require_admin
from app.database import get_db
from app.schemas.common import MessageResponse
from app.schemas.user import UserCreateRequest, UserListResponse, UserResponse, UserUpdateRequest
from app.services import user_service

router = APIRouter(prefix="/users", tags=["User Management"])


@router.get("", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    user_id_filter: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_admin),
) -> UserListResponse:
    """COUSR00C POPULATE-USER-DATA (paginated browse)."""
    return await user_service.list_users(db, page, page_size, user_id_filter)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_admin),
) -> UserResponse:
    """COUSR02C READ-USER-SEC-FILE."""
    return await user_service.get_user(user_id, db)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: UserCreateRequest,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_admin),
) -> UserResponse:
    """COUSR01C WRITE-USER-SEC-FILE."""
    return await user_service.create_user(request, db)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    request: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_admin),
) -> UserResponse:
    """COUSR02C UPDATE-USER-SEC-FILE."""
    return await user_service.update_user(user_id, request, db)


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_admin),
) -> MessageResponse:
    """COUSR03C DELETE-USER-SEC-FILE."""
    await user_service.delete_user(user_id, db)
    return MessageResponse(message=f"User {user_id} deleted successfully")
