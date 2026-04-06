"""
Account repository — ACCTDAT VSAM KSDS operations.

COBOL origin: Replaces EXEC CICS READ/REWRITE DATASET('ACCTDAT').
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account


class AccountRepository:
    """
    Data access object for the `accounts` table.

    CICS DATASET(ACCTDAT) commands → SQLAlchemy async queries.
    RESP=NOTFND → returns None.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, account_id: int) -> Account | None:
        """
        EXEC CICS READ DATASET('ACCTDAT') INTO(ACCOUNT-RECORD)
               RIDFLD(ACCT-ID)
               RESP(WS-RESP) RESP2(WS-RESP2).
        """
        result = await self.db.execute(
            select(Account).where(Account.account_id == account_id)
        )
        return result.scalar_one_or_none()

    async def update(self, account: Account) -> Account:
        """
        EXEC CICS REWRITE DATASET('ACCTDAT') FROM(ACCOUNT-RECORD).
        SQLAlchemy tracks dirty fields; flush sends the UPDATE.
        """
        await self.db.flush()
        await self.db.refresh(account)
        return account
