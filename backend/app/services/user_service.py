"""
User service — COUSR00C/01C/02C/03C business logic (admin-only).

COBOL programs: COUSR00C (list), COUSR01C (add), COUSR02C (update), COUSR03C (delete).
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.errors import DuplicateResourceError, NotFoundError
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    UserCreateRequest,
    UserListResponse,
    UserResponse,
    UserUpdateRequest,
)
from app.utils.security import hash_password


async def list_users(
    db: AsyncSession,
    page: int,
    page_size: int,
    user_id_filter: str | None,
) -> UserListResponse:
    """COUSR00C POPULATE-USER-DATA."""
    repo = UserRepository(db)
    users, total = await repo.list_paginated(page, page_size, user_id_filter)
    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in users],
        page=page,
        page_size=page_size,
        total_count=total,
        has_next=page * page_size < total,
        has_previous=page > 1,
    )


async def get_user(user_id: str, db: AsyncSession) -> UserResponse:
    """COUSR02C READ-USER-SEC-FILE."""
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if user is None:
        raise NotFoundError("User", user_id)
    return UserResponse.model_validate(user)


async def create_user(request: UserCreateRequest, db: AsyncSession) -> UserResponse:
    """COUSR01C WRITE-USER-SEC-FILE."""
    repo = UserRepository(db)
    user = User(
        user_id=request.user_id.upper(),
        first_name=request.first_name,
        last_name=request.last_name,
        password_hash=hash_password(request.password),
        user_type=request.user_type,
    )
    try:
        created = await repo.create(user)
    except IntegrityError:
        raise DuplicateResourceError("User", request.user_id)
    return UserResponse.model_validate(created)


async def update_user(
    user_id: str,
    request: UserUpdateRequest,
    db: AsyncSession,
) -> UserResponse:
    """COUSR02C UPDATE-USER-SEC-FILE."""
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if user is None:
        raise NotFoundError("User", user_id)

    user.first_name = request.first_name
    user.last_name = request.last_name
    user.user_type = request.user_type
    if request.password:
        user.password_hash = hash_password(request.password)

    updated = await repo.update(user)
    return UserResponse.model_validate(updated)


async def delete_user(user_id: str, db: AsyncSession) -> None:
    """COUSR03C DELETE-USER-SEC-FILE."""
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if user is None:
        raise NotFoundError("User", user_id)
    await repo.delete(user)
