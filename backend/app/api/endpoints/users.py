"""
User Management API endpoints — COUSR00C/01C/02C/03C (admin-only).

GET    /api/v1/users              → COUSR00C (list)
GET    /api/v1/users/{user_id}    → COUSR02C (get)
POST   /api/v1/users              → COUSR01C (create)
PUT    /api/v1/users/{user_id}    → COUSR02C (update)
DELETE /api/v1/users/{user_id}    → COUSR03C (delete)
"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser, require_admin
from app.database import get_db
from app.schemas.common import MessageResponse
from app.schemas.user import UserCreateRequest, UserListResponse, UserResponse, UserUpdateRequest
from app.services import user_service

router = APIRouter(prefix="/users", tags=["User Management"])

DbDep = Annotated[AsyncSession, Depends(get_db)]
AdminDep = Annotated[CurrentUser, Depends(require_admin)]


@router.get("")
async def list_users(
    db: DbDep,
    _: AdminDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
    user_id_filter: Annotated[Optional[str], Query()] = None,
) -> UserListResponse:
    """COUSR00C POPULATE-USER-DATA (paginated browse)."""
    return await user_service.list_users(db, page, page_size, user_id_filter)


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    db: DbDep,
    _: AdminDep,
) -> UserResponse:
    """COUSR02C READ-USER-SEC-FILE."""
    return await user_service.get_user(user_id, db)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(
    request: UserCreateRequest,
    db: DbDep,
    _: AdminDep,
) -> UserResponse:
    """COUSR01C WRITE-USER-SEC-FILE."""
    return await user_service.create_user(request, db)


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    request: UserUpdateRequest,
    db: DbDep,
    _: AdminDep,
) -> UserResponse:
    """COUSR02C UPDATE-USER-SEC-FILE."""
    return await user_service.update_user(user_id, request, db)


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    db: DbDep,
    _: AdminDep,
) -> MessageResponse:
    """COUSR03C DELETE-USER-SEC-FILE."""
    await user_service.delete_user(user_id, db)
    return MessageResponse(message=f"User {user_id} deleted successfully")
