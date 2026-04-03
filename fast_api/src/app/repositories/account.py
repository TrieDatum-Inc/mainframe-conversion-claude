"""Account data access repository.

Maps CBTRN02C 1500-B-LOOKUP-ACCT, 2800-UPDATE-ACCOUNT-REC
and CBACT04C 1100-GET-ACCT-DATA, 1050-UPDATE-ACCOUNT.
"""

from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account


class AccountRepository:
    """Data access for accounts table."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, acct_id: str) -> Account | None:
        """Random READ by account ID. Maps CBTRN02C 1500-B-LOOKUP-ACCT."""
        result = await self.db.execute(
            select(Account).where(Account.acct_id == acct_id)
        )
        return result.scalar_one_or_none()

    async def update_balance_after_posting(
        self,
        acct_id: str,
        tran_amt: Decimal,
    ) -> bool:
        """Update account balance fields after posting a transaction.

        Maps CBTRN02C 2800-UPDATE-ACCOUNT-REC:
          ADD DALYTRAN-AMT TO ACCT-CURR-BAL
          IF DALYTRAN-AMT >= 0 -> ADD to ACCT-CURR-CYC-CREDIT
          ELSE -> ADD to ACCT-CURR-CYC-DEBIT
        """
        account = await self.get_by_id(acct_id)
        if not account:
            return False

        account.acct_curr_bal = (account.acct_curr_bal or Decimal("0")) + tran_amt

        if tran_amt >= Decimal("0"):
            account.acct_curr_cyc_credit = (
                account.acct_curr_cyc_credit or Decimal("0")
            ) + tran_amt
        else:
            account.acct_curr_cyc_debit = (
                account.acct_curr_cyc_debit or Decimal("0")
            ) + tran_amt

        await self.db.flush()
        return True

    async def update_balance_after_interest(
        self,
        acct_id: str,
        total_interest: Decimal,
    ) -> bool:
        """Update account after interest calculation.

        Maps CBACT04C 1050-UPDATE-ACCOUNT:
          ADD WS-TOTAL-INT TO ACCT-CURR-BAL
          MOVE 0 TO ACCT-CURR-CYC-CREDIT
          MOVE 0 TO ACCT-CURR-CYC-DEBIT
        """
        account = await self.get_by_id(acct_id)
        if not account:
            return False

        account.acct_curr_bal = (account.acct_curr_bal or Decimal("0")) + total_interest
        account.acct_curr_cyc_credit = Decimal("0")
        account.acct_curr_cyc_debit = Decimal("0")

        await self.db.flush()
        return True

    async def get_all(self) -> list[Account]:
        """Sequential read of all accounts. Maps CBEXPORT 3000-EXPORT-ACCOUNTS."""
        result = await self.db.execute(select(Account).order_by(Account.acct_id))
        return list(result.scalars().all())
