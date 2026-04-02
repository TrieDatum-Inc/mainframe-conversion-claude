"""
User repository — data access layer.

Replaces VSAM KSDS EXEC CICS operations on USRSEC file (CSUSR01Y).
Primary key: SEC-USR-ID PIC X(08) (user ID, upper-cased).

COUSR00C: STARTBR/READNEXT/READPREV (paginated browse, 10 rows/page)
COUSR01C: WRITE (new user)
COUSR02C: REWRITE (update user)
COUSR03C: DELETE (delete user)
COSGN00C: READ by user ID (authentication)
"""

from typing import List, Optional, Tuple

from sqlalchemy import asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateKeyError, ResourceNotFoundError
from app.infrastructure.orm.user_orm import UserORM


class UserRepository:
    """USRSEC VSAM KSDS operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, usr_id: str) -> UserORM:
        """
        Read user by primary key.
        Equivalent to: EXEC CICS READ DATASET('USRSEC') RIDFLD(usr_id)
        COSGN00C uses this for authentication.
        Raises ResourceNotFoundError (RESP=NOTFND -> 'User not found. Try again ...').
        """
        stmt = select(UserORM).where(UserORM.usr_id == usr_id.upper())
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            raise ResourceNotFoundError("User", usr_id)
        return user

    async def get_by_id_or_none(self, usr_id: str) -> Optional[UserORM]:
        """Read user; return None if not found."""
        stmt = select(UserORM).where(UserORM.usr_id == usr_id.upper())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_paginated_forward(
        self,
        page_size: int,
        start_usr_id: Optional[str] = None,
    ) -> Tuple[List[UserORM], bool]:
        """
        Forward-paginated user list.
        Equivalent to COUSR00C STARTBR/READNEXT on USRSEC.
        Returns (records, has_next_page).
        """
        conditions = []
        if start_usr_id:
            conditions.append(UserORM.usr_id >= start_usr_id.upper())

        from sqlalchemy import and_
        stmt = (
            select(UserORM)
            .where(and_(*conditions) if conditions else True)
            .order_by(asc(UserORM.usr_id))
            .limit(page_size + 1)
        )
        result = await self.db.execute(stmt)
        rows = list(result.scalars().all())
        has_next = len(rows) > page_size
        return rows[:page_size], has_next

    async def list_paginated_backward(
        self,
        page_size: int,
        end_usr_id: str,
    ) -> Tuple[List[UserORM], bool]:
        """
        Backward-paginated user list.
        Equivalent to COUSR00C READPREV on USRSEC.
        Returns (records in forward order, has_previous_page).
        """
        from sqlalchemy import and_
        stmt = (
            select(UserORM)
            .where(UserORM.usr_id <= end_usr_id.upper())
            .order_by(desc(UserORM.usr_id))
            .limit(page_size + 1)
        )
        result = await self.db.execute(stmt)
        rows = list(result.scalars().all())
        has_prev = len(rows) > page_size
        return list(reversed(rows[:page_size])), has_prev

    async def create(self, user: UserORM) -> UserORM:
        """
        Write new user.
        Equivalent to: EXEC CICS WRITE DATASET('USRSEC')
        COUSR01C: writes after validating all 5 required fields.
        Raises DuplicateKeyError if user ID already exists.
        """
        existing = await self.get_by_id_or_none(user.usr_id)
        if existing is not None:
            raise DuplicateKeyError("User", user.usr_id)
        self.db.add(user)
        await self.db.flush()
        return user

    async def update(self, user: UserORM) -> UserORM:
        """
        Update user record.
        Equivalent to: EXEC CICS REWRITE DATASET('USRSEC')
        COUSR02C: updates first name, last name, password, user type.
        User ID (key) cannot be changed.
        """
        await self.db.flush()
        return user

    async def delete(self, usr_id: str) -> None:
        """
        Delete user.
        Equivalent to: EXEC CICS DELETE DATASET('USRSEC') RIDFLD(usr_id)
        COUSR03C: deletes after confirmation step.
        """
        user = await self.get_by_id(usr_id)
        await self.db.delete(user)
        await self.db.flush()
