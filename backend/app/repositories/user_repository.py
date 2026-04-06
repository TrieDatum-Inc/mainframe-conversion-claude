"""
User repository — all database operations for the `users` table.

COBOL origin: Maps CICS FILE CONTROL commands against USRSEC VSAM KSDS.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Data access object for the `users` table."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id: str) -> User | None:
        """EXEC CICS READ DATASET(USRSEC) RIDFLD(WS-USER-ID)."""
        result = await self.db.execute(select(User).where(User.user_id == user_id))
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        """EXEC CICS WRITE DATASET(USRSEC)."""
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update(self, user: User) -> User:
        """EXEC CICS REWRITE DATASET(USRSEC)."""
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        """EXEC CICS DELETE DATASET(USRSEC)."""
        await self.db.delete(user)
        await self.db.flush()

    async def list_paginated(
        self,
        page: int,
        page_size: int,
        user_id_filter: str | None = None,
    ) -> tuple[list[User], int]:
        """EXEC CICS STARTBR/READNEXT — paginated user list."""
        query = select(User)
        if user_id_filter:
            query = query.where(User.user_id.ilike(f"{user_id_filter}%"))
        query = query.order_by(User.user_id)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()

        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total
