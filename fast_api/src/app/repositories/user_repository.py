"""User repository — replaces EXEC CICS READ DATASET('USRSEC') operations.

COBOL equivalent:
  READ-USER-SEC-FILE paragraph in COSGN00C (lines 209-257)
  EXEC CICS READ DATASET('USRSEC') INTO(SEC-USER-DATA) RIDFLD(WS-USER-ID)

RESP code mapping:
  DFHRESP(NORMAL) = 0  → record found (SELECT returns a row)
  DFHRESP(NOTFND) = 13 → user not found (SELECT returns None)
  OTHER                → unexpected error (exception raised)
"""
import logging

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

logger = logging.getLogger(__name__)


class UserRepository:
    """Data access layer for the users table (USRSEC VSAM equivalent)."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, user_id: str) -> User | None:
        """Fetch user by primary key — maps CICS READ RIDFLD(WS-USER-ID).

        COBOL BR-003: caller must uppercase user_id before calling this method.
        Returns None when RESP = DFHRESP(NOTFND) (code 13).
        """
        result = await self._db.execute(
            select(User).where(User.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        """Insert a new user record — maps COUSR01C EXEC CICS WRITE."""
        self._db.add(user)
        await self._db.flush()
        await self._db.refresh(user)
        logger.info("Created user: %s (type=%s)", user.user_id, user.user_type)
        return user

    async def update_password(self, user_id: str, hashed_password: str) -> bool:
        """Update user password — maps COUSR02C EXEC CICS REWRITE."""
        result = await self._db.execute(
            update(User)
            .where(User.user_id == user_id)
            .values(password=hashed_password)
            .returning(User.user_id)
        )
        updated = result.scalar_one_or_none()
        return updated is not None

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[User]:
        """Browse all users — maps COUSR00C EXEC CICS STARTBR / READNEXT pattern."""
        result = await self._db.execute(
            select(User).order_by(User.user_id).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def delete(self, user_id: str) -> bool:
        """Delete a user record — maps COUSR03C EXEC CICS DELETE."""
        user = await self.get_by_id(user_id)
        if user is None:
            return False
        await self._db.delete(user)
        logger.info("Deleted user: %s", user_id)
        return True
