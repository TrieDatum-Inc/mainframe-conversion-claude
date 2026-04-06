"""
User repository — all database operations for the `users` table.

COBOL origin: Maps to CICS FILE CONTROL commands against USRSEC VSAM KSDS:
    EXEC CICS READ DATASET(USRSEC) INTO(SEC-USER-DATA) RIDFLD(WS-USER-ID)
    EXEC CICS WRITE DATASET(USRSEC) FROM(SEC-USER-DATA) RIDFLD(SEC-USR-ID)
    EXEC CICS REWRITE DATASET(USRSEC) FROM(SEC-USER-DATA)
    EXEC CICS DELETE DATASET(USRSEC) RIDFLD(WS-USER-ID)
    EXEC CICS STARTBR / READNEXT / READPREV / ENDBR (browse operations)

DESIGN RULE: No business logic in this layer. All logic lives in services/.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """
    Data access object for the `users` table.

    All CICS DATASET(USRSEC) commands are mapped to async SQLAlchemy operations.
    RESP=NOTFND (13) → returns None (caller decides on 404 vs 401 semantics).
    RESP=DUPKEY/DUPREC → IntegrityError raised by SQLAlchemy → caller handles 409.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id: str) -> User | None:
        """
        Fetch a user by primary key.

        COBOL equivalent:
            EXEC CICS READ DATASET(USRSEC) INTO(SEC-USER-DATA) RIDFLD(WS-USER-ID) RESP RESP2
            IF RESP = DFHRESP(NORMAL): use record
            ELSE IF RESP = DFHRESP(NOTFND): return 404/401
        """
        result = await self.db.execute(
            select(User).where(User.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        """
        Insert a new user record.

        COBOL equivalent:
            EXEC CICS WRITE DATASET(USRSEC) FROM(SEC-USER-DATA) RIDFLD(SEC-USR-ID)
            IF RESP = DFHRESP(DUPKEY) or DFHRESP(DUPREC): duplicate user_id

        Raises sqlalchemy.exc.IntegrityError on duplicate user_id.
        Caller (service layer) converts to 409 Conflict.
        """
        self.db.add(user)
        await self.db.flush()  # Execute INSERT; raises IntegrityError on dup
        await self.db.refresh(user)
        return user

    async def update(self, user: User) -> User:
        """
        Persist changes to an existing user record.

        COBOL equivalent:
            EXEC CICS REWRITE DATASET(USRSEC) FROM(SEC-USER-DATA)
        SQLAlchemy tracks dirty fields automatically; flush writes the UPDATE.
        """
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        """
        Delete a user record.

        COBOL equivalent:
            EXEC CICS DELETE DATASET(USRSEC) RIDFLD(WS-USER-ID)
        Caller must fetch the record first (mirrors COUSR03C two-step: READ then DELETE).
        """
        await self.db.delete(user)
        await self.db.flush()

    async def list_users(
        self,
        user_id_filter: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[User], int]:
        """
        Browse users with optional prefix filter and pagination.

        COBOL equivalent (COUSR00C POPULATE-USER-DATA):
            EXEC CICS STARTBR DATASET(USRSEC) RIDFLD(USRIDINI or LOW-VALUES)
            EXEC CICS READNEXT DATASET(USRSEC) INTO(WS-USER-SEC-FILE) RIDFLD(...)
            (repeat up to 10 times for one page)
            EXEC CICS ENDBR DATASET(USRSEC)

        STARTBR with USRIDINI filter → WHERE user_id >= filter ORDER BY user_id ASC
        STARTBR with LOW-VALUES → ORDER BY user_id ASC (full browse from beginning)
        Look-ahead READNEXT for NEXT-PAGE-FLG → COUNT(*) > offset + page_size
        """
        offset = (page - 1) * page_size

        # Build base query
        base_query = select(User)
        if user_id_filter:
            # STARTBR with RIDFLD=USRIDINI → WHERE user_id >= filter
            base_query = base_query.where(User.user_id >= user_id_filter.upper())

        # Count query for pagination metadata (replaces look-ahead READNEXT)
        count_query = select(func.count()).select_from(
            base_query.subquery()
        )
        total_count = (await self.db.execute(count_query)).scalar_one()

        # Paginated data query — READNEXT pattern
        data_query = (
            base_query
            .order_by(User.user_id.asc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.db.execute(data_query)
        users = list(result.scalars().all())

        return users, total_count

    async def exists(self, user_id: str) -> bool:
        """
        Check if a user ID already exists (for duplicate detection).

        COBOL equivalent: EXEC CICS READ DATASET(USRSEC) → check RESP=DUPKEY
        Used by create-user flow before attempting INSERT.
        """
        result = await self.db.execute(
            select(func.count()).select_from(User).where(User.user_id == user_id)
        )
        return (result.scalar_one() or 0) > 0
