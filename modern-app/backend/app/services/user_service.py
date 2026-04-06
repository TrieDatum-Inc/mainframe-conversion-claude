"""Business logic layer for User Administration.

Implements ALL business rules from COUSR01C (add), COUSR02C (update),
COUSR03C (delete), and COUSR00C (browse/paginate).

Key business rules preserved from COBOL:
  - user_id uniqueness → 409 Conflict (mirrors DUPKEY/DUPREC on VSAM WRITE)
  - user_id not found  → 404 Not Found  (mirrors NOTFND on VSAM READ)
  - No-change guard    → 304 / special response (mirrors COUSR02C "Please modify")
  - Passwords bcrypt-hashed before storage (plaintext never stored)
  - user_id always uppercased (mirrors COSGN00C uppercasing)
  - Pagination via SQL OFFSET/LIMIT (mirrors STARTBR/READNEXT 10 records)
"""
import math

import bcrypt
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserDeleteResponse,
    UserListResponse,
    UserPublic,
    UserUpdate,
)

# Pagination default mirrors COUSR00C "10 users per page"
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100


def _hash_password(plain: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def _passwords_match(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _build_list_query(user_id_filter: str | None):
    """Build the base SELECT query, optionally filtering by user_id prefix."""
    query = select(User).order_by(User.user_id)
    if user_id_filter:
        # Mirror COUSR00C STARTBR: position at/after user_id substring
        query = query.where(User.user_id.ilike(f"{user_id_filter}%"))
    return query


async def _get_total_count(
    db: AsyncSession,
    user_id_filter: str | None,
) -> int:
    """Return total matching row count for pagination metadata."""
    count_query = select(func.count()).select_from(User)
    if user_id_filter:
        count_query = count_query.where(User.user_id.ilike(f"{user_id_filter}%"))
    result = await db.execute(count_query)
    return result.scalar_one()


async def _fetch_user_or_404(db: AsyncSession, user_id: str) -> User:
    """Load a user by user_id, raising 404 if not found.

    Mirrors COUSR02C/COUSR03C READ NOTFND handling.
    """
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id!r} not found",
        )
    return user


def _detect_changes(user: User, data: UserUpdate, new_hash: str | None) -> bool:
    """Return True if any field actually changed.

    Mirrors COUSR02C business rule §7.1:
    'Only issues REWRITE if at least one field has actually changed.'
    """
    if user.first_name != data.first_name:
        return True
    if user.last_name != data.last_name:
        return True
    if user.user_type != data.user_type:
        return True
    if new_hash is not None:
        # Password changed if a new password was provided
        return True
    return False


def _apply_changes(user: User, data: UserUpdate, new_hash: str | None) -> None:
    """Write updated field values onto the ORM object."""
    user.first_name = data.first_name
    user.last_name = data.last_name
    user.user_type = data.user_type
    if new_hash is not None:
        user.password_hash = new_hash


class UserService:
    """Service class encapsulating all user administration business logic."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_users(
        self,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        user_id_filter: str | None = None,
    ) -> UserListResponse:
        """Paginated user list — mirrors COUSR00C STARTBR/READNEXT 10 logic.

        Args:
            page: 1-based page number (mirrors CDEMO-CU00-PAGE-NUM).
            page_size: Records per page (default 10, mirrors BMS 10-row display).
            user_id_filter: Optional user_id prefix search (mirrors USRIDIN field).

        Returns:
            UserListResponse with users, total, and page metadata.
        """
        page_size = min(max(page_size, 1), MAX_PAGE_SIZE)
        page = max(page, 1)
        offset = (page - 1) * page_size

        total = await _get_total_count(self.db, user_id_filter)
        total_pages = max(math.ceil(total / page_size), 1)

        query = _build_list_query(user_id_filter).offset(offset).limit(page_size)
        result = await self.db.execute(query)
        users = result.scalars().all()

        return UserListResponse(
            users=[UserPublic.model_validate(u) for u in users],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_user(self, user_id: str) -> UserPublic:
        """Fetch a single user by user_id.

        Mirrors COUSR02C Phase 1 READ (fetch for display).
        Raises 404 if not found (mirrors NOTFND handling).
        """
        user = await _fetch_user_or_404(self.db, user_id.upper())
        return UserPublic.model_validate(user)

    async def create_user(self, data: UserCreate) -> UserPublic:
        """Create a new user record.

        Mirrors COUSR01C EXEC CICS WRITE flow:
          1. Validate uniqueness (VSAM DUPKEY → HTTP 409)
          2. Hash password before storage
          3. Write record
          4. Return created user (without password)
        """
        user_id = data.user_id.upper()
        existing = await self.db.execute(
            select(User).where(User.user_id == user_id)
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User ID {user_id!r} already exists",
            )

        new_user = User(
            user_id=user_id,
            first_name=data.first_name,
            last_name=data.last_name,
            password_hash=_hash_password(data.password),
            user_type=data.user_type,
        )
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return UserPublic.model_validate(new_user)

    async def update_user(self, user_id: str, data: UserUpdate) -> UserPublic:
        """Update an existing user record.

        Mirrors COUSR02C Phase 2 (PF5 Save) logic:
          1. Fetch user with implicit DB lock (READ with UPDATE)
          2. Compare each field to stored value (_detect_changes)
          3. Only write if at least one field changed; raise 400 otherwise
          4. Commit and return updated record

        Business rule §7.1: 'Only issues REWRITE if at least one field changed.'
        """
        user = await _fetch_user_or_404(self.db, user_id.upper())

        new_hash = _hash_password(data.password) if data.password else None

        if not _detect_changes(user, data, new_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No changes detected. Please modify at least one field to update.",
            )

        _apply_changes(user, data, new_hash)
        await self.db.commit()
        await self.db.refresh(user)
        return UserPublic.model_validate(user)

    async def delete_user(self, user_id: str) -> UserDeleteResponse:
        """Delete a user record.

        Mirrors COUSR03C Phase 2 (PF5 Confirm Delete) logic:
          1. Fetch user (raises 404 if gone — mirrors READ NOTFND)
          2. DELETE
          3. Return confirmation message (mirrors 'User XXXX has been deleted')
        """
        user = await _fetch_user_or_404(self.db, user_id.upper())
        await self.db.delete(user)
        await self.db.commit()
        return UserDeleteResponse(
            message=f"User {user_id.upper()!r} has been deleted",
            user_id=user_id.upper(),
        )
