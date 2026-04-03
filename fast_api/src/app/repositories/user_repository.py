"""User repository — data access layer for the users table.

All database I/O is here.  No business logic.

VSAM→SQL operation mapping:
    STARTBR/READNEXT (COUSR00C)  → paginated SELECT ORDER BY user_id
    EXEC CICS READ  (COUSR02C/03C)→ SELECT WHERE user_id = :id
    EXEC CICS WRITE (COUSR01C)   → INSERT
    EXEC CICS REWRITE(COUSR02C)  → UPDATE
    EXEC CICS DELETE (COUSR03C)  → DELETE
"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Data access operations for the users table."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: str) -> User | None:
        """Fetch a single user by primary key.

        Maps to EXEC CICS READ DATASET('USRSEC') RIDFLD(SEC-USR-ID).
        Returns None instead of raising NOTFND — callers handle 404.
        """
        result = await self._session.execute(
            select(User).where(User.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_paginated(
        self,
        page: int,
        page_size: int,
        search_user_id: str | None = None,
    ) -> tuple[list[User], int]:
        """Paginated user browse in user_id order.

        Maps to COUSR00C PROCESS-PAGE-FORWARD/BACKWARD (STARTBR/READNEXT).
        COUSR00C displays 10 rows per page and tracks first/last user_id
        for bidirectional navigation.  Here we use SQL OFFSET/LIMIT with
        ORDER BY user_id (equivalent to VSAM KSDS sequential key order).

        Args:
            page: 1-based page number.
            page_size: Number of records per page (default 10 from COUSR00C).
            search_user_id: Optional prefix filter; maps to USRIDINI search field.
                When blank in COUSR00C, browse starts from LOW-VALUES (all records).

        Returns:
            Tuple of (user_list, total_count).
        """
        base_query = select(User).order_by(User.user_id)

        if search_user_id:
            # COUSR00C: non-blank USRIDINI positions browse at that key
            base_query = base_query.where(
                User.user_id >= search_user_id
            )

        # Total count for pagination metadata
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self._session.execute(count_query)
        total_count = total_result.scalar_one()

        # Paginated fetch
        offset = (page - 1) * page_size
        paginated_query = base_query.offset(offset).limit(page_size)
        result = await self._session.execute(paginated_query)
        users = list(result.scalars().all())

        return users, total_count

    async def create(self, user: User) -> User:
        """Insert a new user record.

        Maps to EXEC CICS WRITE DATASET('USRSEC') (COUSR01C WRITE-USER-SEC-FILE).
        Raises IntegrityError on duplicate key — caller maps to HTTP 409.
        """
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def update(self, user: User) -> User:
        """Persist changes to an existing user record.

        Maps to EXEC CICS REWRITE DATASET('USRSEC') (COUSR02C UPDATE-USER-SEC-FILE).
        The user object must already be tracked by the session (from a prior get_by_id).
        """
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        """Delete a user record.

        Maps to EXEC CICS DELETE DATASET('USRSEC') (COUSR03C DELETE-USER-SEC-FILE).
        The user object must already be tracked by the session.
        """
        await self._session.delete(user)
        await self._session.flush()

    async def exists(self, user_id: str) -> bool:
        """Check if a user_id exists without fetching the full record."""
        result = await self._session.execute(
            select(func.count()).where(User.user_id == user_id)
        )
        return result.scalar_one() > 0
