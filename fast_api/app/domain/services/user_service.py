"""
User management service — business logic layer.

Maps COUSR00C (list), COUSR01C (add), COUSR02C (update), COUSR03C (delete).

All operations are admin-only (CDEMO-USER-TYPE='A' required).
Business rules from spec:
  COUSR01C: All 5 fields mandatory; user ID must be unique; upper-cased
  COUSR02C: Cannot change user ID; password optional
  COUSR03C: Explicit confirmation required before delete
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessValidationError
from app.domain.services.auth_service import hash_password
from app.infrastructure.orm.user_orm import UserORM
from app.infrastructure.repositories.user_repository import UserRepository
from app.schemas.user_schemas import (
    UserCreateRequest,
    UserListResponse,
    UserUpdateRequest,
    UserView,
)


async def list_users(
    db: AsyncSession,
    page_size: int = 10,
    start_usr_id: Optional[str] = None,
    direction: str = "forward",
    end_usr_id: Optional[str] = None,
) -> UserListResponse:
    """
    Paginated user list (COUSR00C).
    10 rows per page, forward/backward navigation.
    """
    repo = UserRepository(db)

    if direction == "backward" and end_usr_id:
        rows, has_prev = await repo.list_paginated_backward(
            page_size=page_size,
            end_usr_id=end_usr_id,
        )
    else:
        rows, has_next = await repo.list_paginated_forward(
            page_size=page_size,
            start_usr_id=start_usr_id,
        )

    from app.schemas.user_schemas import UserListItem
    items = [UserListItem.model_validate(r) for r in rows]

    return UserListResponse(
        items=items,
        page=1,
        has_next_page=has_next if direction == "forward" else False,
        first_usr_id=rows[0].usr_id if rows else None,
        last_usr_id=rows[-1].usr_id if rows else None,
    )


async def get_user(usr_id: str, db: AsyncSession) -> UserView:
    """Get a single user record for display (COUSR02C pre-display read)."""
    repo = UserRepository(db)
    user = await repo.get_by_id(usr_id)
    return UserView.model_validate(user)


async def create_user(req: UserCreateRequest, db: AsyncSession) -> UserView:
    """
    Create new user (COUSR01C).

    Validations:
    - All 5 fields mandatory (first name, last name, user ID, password, user type)
    - User ID must be unique in USRSEC
    - User ID is upper-cased
    - User type must be 'A' or 'U'
    """
    repo = UserRepository(db)

    user = UserORM(
        usr_id=req.usr_id.upper(),  # BR-SGN-002 consistency
        first_name=req.first_name,
        last_name=req.last_name,
        pwd_hash=hash_password(req.password),
        usr_type=req.usr_type,
    )

    created = await repo.create(user)
    return UserView.model_validate(created)


async def update_user(
    usr_id: str,
    req: UserUpdateRequest,
    db: AsyncSession,
) -> UserView:
    """
    Update user (COUSR02C).
    User ID cannot be changed (it's the VSAM key).
    Password update is optional.
    """
    repo = UserRepository(db)
    user = await repo.get_by_id(usr_id)

    user.first_name = req.first_name
    user.last_name = req.last_name
    user.usr_type = req.usr_type

    if req.password is not None:
        user.pwd_hash = hash_password(req.password)

    updated = await repo.update(user)
    return UserView.model_validate(updated)


async def delete_user(
    usr_id: str,
    confirm: bool,
    db: AsyncSession,
) -> dict:
    """
    Delete user (COUSR03C).
    Requires explicit confirmation (confirm=True).
    COUSR03C uses a two-step confirm pattern.
    """
    if not confirm:
        raise BusinessValidationError(
            "User deletion requires explicit confirmation. Set confirm=true.",
            field="confirm",
        )

    repo = UserRepository(db)
    # Verify user exists before deletion (COUSR03C reads user to display before confirm)
    user = await repo.get_by_id(usr_id)

    await repo.delete(usr_id)

    return {
        "message": f"User '{usr_id}' deleted successfully.",
        "user_id": usr_id,
    }
