"""
Data access layer for the `users` table.

COBOL origin: Replaces all CICS file I/O commands against the USRSEC VSAM KSDS:
  EXEC CICS STARTBR / READNEXT / READPREV / ENDBR  → list_all (paginated)
  EXEC CICS READ DATASET(USRSEC)                    → get_by_id
  EXEC CICS WRITE DATASET(USRSEC)                   → create
  EXEC CICS REWRITE DATASET(USRSEC)                 → update
  EXEC CICS DELETE DATASET(USRSEC)                  → delete

All methods are async; callers must pass an active AsyncSession.
No business logic lives here — only raw DB operations.
"""

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """
    Encapsulates all database operations for the User entity.

    COBOL origin: Replaces CICS file control for USRSEC KSDS.
    One method per CICS command type; complexity kept low (<15) per function.
    """

    async def get_by_id(self, db: AsyncSession, user_id: str) -> Optional[User]:
        """
        Fetch a single user by primary key.

        COBOL origin: COUSR02C/COUSR03C READ-USER-SEC-FILE:
          EXEC CICS READ DATASET(USRSEC) INTO(SEC-USER-DATA) RIDFLD(SEC-USR-ID)
          IF RESP = NORMAL  → return record
          IF RESP = NOTFND  → return None (caller raises UserNotFoundError)
        """
        result = await db.execute(select(User).where(User.user_id == user_id))
        return result.scalar_one_or_none()

    async def exists(self, db: AsyncSession, user_id: str) -> bool:
        """
        Check whether a user_id already exists in the table.

        COBOL origin: COUSR01C WRITE-USER-SEC-FILE checks RESP=DUPKEY/DUPREC
        after EXEC CICS WRITE. This pre-flight check avoids the insert attempt
        and returns a structured 409 before hitting the DB constraint.
        """
        result = await db.execute(
            select(func.count()).select_from(User).where(User.user_id == user_id)
        )
        count: int = result.scalar_one()
        return count > 0

    async def list_all(
        self,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 10,
        user_id_filter: Optional[str] = None,
    ) -> tuple[list[User], int]:
        """
        Paginated browse of users, ordered by user_id ascending.

        COBOL origin: COUSR00C POPULATE-USER-DATA:
          EXEC CICS STARTBR FILE(USRSEC) RIDFLD(WS-USR-ID-SRCH)
          EXEC CICS READNEXT (up to 10 rows)
          One look-ahead READNEXT sets CDEMO-CU00-NEXT-PAGE-FLG

        If user_id_filter is provided:
          WHERE user_id >= filter ORDER BY user_id ASC  (replaces STARTBR at filter key)
        Else:
          ORDER BY user_id ASC  (replaces STARTBR with LOW-VALUES)

        Returns (rows_for_this_page, total_matching_count).
        """
        base_query = select(User).order_by(User.user_id.asc())
        count_query = select(func.count()).select_from(User)

        if user_id_filter:
            base_query = base_query.where(User.user_id >= user_id_filter)
            count_query = count_query.where(User.user_id >= user_id_filter)

        # Total count (replaces look-ahead READNEXT + CDEMO-CU00-NEXT-PAGE-FLG)
        total_result = await db.execute(count_query)
        total_count: int = total_result.scalar_one()

        # Paginated rows
        offset = (page - 1) * page_size
        paged_query = base_query.offset(offset).limit(page_size)
        result = await db.execute(paged_query)
        rows = list(result.scalars().all())

        return rows, total_count

    async def create(self, db: AsyncSession, user: User) -> User:
        """
        Insert a new user record.

        COBOL origin: COUSR01C WRITE-USER-SEC-FILE:
          EXEC CICS WRITE DATASET(USRSEC) FROM(SEC-USER-DATA) RIDFLD(SEC-USR-ID)
          RESP=NORMAL → success; RESP=DUPKEY/DUPREC → caller handles as 409
        """
        db.add(user)
        await db.flush()  # Send INSERT; let SQLAlchemy detect constraint violations
        await db.refresh(user)
        return user

    async def update(self, db: AsyncSession, user: User) -> User:
        """
        Persist changes to an existing user record.

        COBOL origin: COUSR02C UPDATE-USER-SEC-FILE:
          EXEC CICS REWRITE DATASET(USRSEC) FROM(SEC-USER-DATA)
          (Only called when USR-MODIFIED-YES — at least one field changed)
        """
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user

    async def delete(self, db: AsyncSession, user: User) -> None:
        """
        Delete a user record.

        COBOL origin: COUSR03C DELETE-USER-SEC-FILE:
          EXEC CICS DELETE DATASET(USRSEC)
          (Requires prior READ UPDATE to acquire exclusive lock)
        """
        await db.delete(user)
        await db.flush()
