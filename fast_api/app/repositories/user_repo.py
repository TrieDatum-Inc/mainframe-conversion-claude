"""
User repository — data access layer for USRSEC VSAM file operations.

All EXEC CICS file operations on USRSEC map to methods here:
  EXEC CICS READ   FILE(USRSEC) RIDFLD(key)  → get_by_id()
  EXEC CICS WRITE  FILE(USRSEC)              → create()
  EXEC CICS REWRITE FILE(USRSEC)             → update()
  EXEC CICS DELETE FILE(USRSEC)              → delete()
  EXEC CICS STARTBR/READNEXT FILE(USRSEC)    → list_paginated()

Source programs: COSGN00C, COUSR00C, COUSR01C, COUSR02C, COUSR03C
"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.utils.cobol_compat import pad_user_id
from app.utils.error_handlers import DuplicateRecordError, RecordNotFoundError


class UserRepository:
    """Data access object for the `users` table (USRSEC VSAM)."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, user_id: str) -> User:
        """
        EXEC CICS READ FILE('USRSEC') INTO(SEC-USER-DATA) RIDFLD(WS-USER-ID)

        COSGN00C READ-USER-SEC-FILE paragraph.
        RESP=13 (NOTFND) → RecordNotFoundError.

        Args:
            user_id: SEC-USR-ID value (will be normalized to 8-char uppercase).

        Returns:
            User ORM instance.

        Raises:
            RecordNotFoundError: User not found (CICS RESP=13 NOTFND).
        """
        normalized = pad_user_id(user_id)
        user = await self._db.get(User, normalized)
        if user is None:
            raise RecordNotFoundError(f"User not found. Try again ... (id={user_id!r})")
        return user

    async def get_by_id_or_none(self, user_id: str) -> User | None:
        """Get user without raising on not-found."""
        normalized = pad_user_id(user_id)
        return await self._db.get(User, normalized)

    async def create(self, user: User) -> User:
        """
        EXEC CICS WRITE FILE('USRSEC') FROM(SEC-USER-DATA)

        COUSR01C add-user paragraph.
        RESP=14 (DUPREC) → DuplicateRecordError.
        """
        existing = await self.get_by_id_or_none(user.user_id)
        if existing is not None:
            raise DuplicateRecordError(f"User ID {user.user_id!r} already exists (DUPREC)")
        self._db.add(user)
        await self._db.flush()
        return user

    async def update(self, user: User) -> User:
        """
        EXEC CICS REWRITE FILE('USRSEC') FROM(SEC-USER-DATA)

        COUSR02C update-user paragraph.
        Record must exist (read-then-rewrite pattern in COBOL).
        """
        merged = await self._db.merge(user)
        await self._db.flush()
        return merged

    async def delete(self, user_id: str) -> None:
        """
        EXEC CICS DELETE FILE('USRSEC') RIDFLD(WS-USER-ID)

        COUSR03C: reads record first, then deletes.
        RESP=13 (NOTFND) → RecordNotFoundError.
        """
        user = await self.get_by_id(user_id)
        await self._db.delete(user)
        await self._db.flush()

    async def list_paginated(
        self,
        cursor: str | None = None,
        limit: int = 10,
        direction: str = "forward",
    ) -> tuple[list[User], int, bool]:
        """
        EXEC CICS STARTBR/READNEXT FILE('USRSEC') — keyset pagination.

        COUSR00C browses USRSEC sequentially (by user ID, PIC X(08) ascending).
        CDEMO-CU00-USRID-FIRST tracks the first key on each page.

        Args:
            cursor: Last user_id from previous page (CDEMO-CU00-USRID-LAST).
                    None means start from beginning (STARTBR from first record).
            limit: Page size (COUSR00C: 10 rows per screen).

        Returns:
            Tuple of (user list, total count).
        """
        count_stmt = select(func.count(User.user_id))
        total = (await self._db.execute(count_stmt)).scalar_one()

        stmt = select(User)
        if direction == "backward":
            stmt = stmt.order_by(User.user_id.desc())
            if cursor:
                stmt = stmt.where(User.user_id < pad_user_id(cursor))
        else:
            stmt = stmt.order_by(User.user_id)
            if cursor:
                stmt = stmt.where(User.user_id > pad_user_id(cursor))
        # Fetch limit+1 to detect whether more rows exist beyond this page
        stmt = stmt.limit(limit + 1)

        result = await self._db.execute(stmt)
        users = list(result.scalars().all())
        has_more = len(users) > limit
        users = users[:limit]
        if direction == "backward":
            users = list(reversed(users))
        return users, total, has_more
