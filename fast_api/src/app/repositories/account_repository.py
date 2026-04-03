"""Account repository — data access layer for ACCTDAT VSAM equivalent.

Maps CICS file commands from COBIL00C to async SQLAlchemy queries.
"""
import logging
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account

logger = logging.getLogger(__name__)


class AccountRepository:
    """Data access for the accounts table.

    CICS equivalents:
      READ-ACCTDAT-FILE  → get_by_id()
      UPDATE-ACCTDAT-FILE (REWRITE) → zero_balance()
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, acct_id: str) -> Account | None:
        """Fetch account by primary key.

        Maps: EXEC CICS READ DATASET('ACCTDAT') RIDFLD(ACCT-ID) UPDATE
        The UPDATE intent in COBOL acquires exclusive lock for REWRITE.
        In PostgreSQL, row-level locking is handled by the transaction context.
        """
        result = await self._session.execute(
            select(Account).where(Account.acct_id == int(acct_id))
        )
        return result.scalar_one_or_none()

    async def zero_balance(
        self, acct_id: str, payment_amount: Decimal
    ) -> Account | None:
        """Zero the account balance after full payment.

        Maps: EXEC CICS REWRITE DATASET('ACCTDAT')
        COBIL00C lines 233-234:
          ACCT-CURR-BAL = ACCT-CURR-BAL - TRAN-AMT
          (TRAN-AMT equals ACCT-CURR-BAL so result is always 0)

        Also resets cycle credits/debits per spec intent.
        """
        await self._session.execute(
            update(Account)
            .where(Account.acct_id == int(acct_id))
            .values(
                curr_bal=Decimal("0.00"),
                curr_cycle_credit=Decimal("0.00"),
                curr_cycle_debit=Decimal("0.00"),
            )
        )
        return await self.get_by_id(acct_id)
