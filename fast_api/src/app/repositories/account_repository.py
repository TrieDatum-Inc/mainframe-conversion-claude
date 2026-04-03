from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account


class AccountRepository:
    """Data access layer for the accounts table (ACCTDAT VSAM KSDS)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, acct_id: str) -> Account | None:
        result = await self._session.execute(
            select(Account).where(Account.acct_id == acct_id)
        )
        return result.scalar_one_or_none()
