"""
User repository — data access layer for the `users` table.

COBOL origin: Maps to CICS file-control commands against USRSEC VSAM:
    EXEC CICS READ FILE('USRSEC') INTO(CDEMO-USRSEC-REC) RIDFLD(WS-USER-ID) RESP RESP2
    RESP=NORMAL  → user found (get_by_id returns User)
    RESP=NOTFND  → user not found (get_by_id returns None)
    RESP=OTHER   → propagated as exception

No business logic lives here — only SQL queries via SQLAlchemy ORM.
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Data access for the users table."""

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
        """
        Fetch a user by primary key.

        COBOL origin: EXEC CICS READ FILE('USRSEC') RIDFLD(WS-USER-ID)
        Returns None when RESP=NOTFND (13); raises on other errors.
        """
        result = await db.execute(
            select(User).where(User.user_id == user_id)
        )
        return result.scalar_one_or_none()
