"""
Account repository — data access layer for the `accounts` table.

COBOL origin: Replaces EXEC CICS READ/REWRITE DATASET(ACCTDAT).
  COACTVWC: READ ACCTDAT FILE BY ACCT-ID → get_by_id
  COACTUPC: READ UPDATE ACCTDAT → get_by_id_for_update (with lock)
  COACTUPC: REWRITE ACCTDAT → update
"""

from decimal import Decimal
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account


class AccountRepository:
    """
    Data access operations for the `accounts` table.

    No business logic here — only SQLAlchemy queries.
    All COACTVWC/COACTUPC READ/REWRITE logic is handled at this layer.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, account_id: int) -> Optional[Account]:
        """
        Fetch account by primary key.

        COBOL: EXEC CICS READ DATASET(ACCTDAT) INTO(ACCOUNT-RECORD)
               RIDFLD(WS-ACCT-ID) RESP(WS-RESP)
        Returns None if not found (maps RESP=NOTFND → 404 at service layer).
        """
        stmt = select(Account).where(Account.account_id == account_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update(
        self,
        account_id: int,
        active_status: str,
        current_balance: Decimal,
        credit_limit: Decimal,
        cash_credit_limit: Decimal,
        open_date: object,
        expiration_date: object,
        reissue_date: object,
        curr_cycle_credit: Decimal,
        curr_cycle_debit: Decimal,
        group_id: Optional[str],
    ) -> Optional[Account]:
        """
        Update account fields.

        COBOL: EXEC CICS REWRITE DATASET(ACCTDAT) FROM(ACCOUNT-RECORD)
        Returns the updated Account row or None if not found.
        updated_at is managed by the database trigger (replaces WS-DATACHANGED-FLAG).
        """
        stmt = (
            update(Account)
            .where(Account.account_id == account_id)
            .values(
                active_status=active_status,
                current_balance=current_balance,
                credit_limit=credit_limit,
                cash_credit_limit=cash_credit_limit,
                open_date=open_date,
                expiration_date=expiration_date,
                reissue_date=reissue_date,
                curr_cycle_credit=curr_cycle_credit,
                curr_cycle_debit=curr_cycle_debit,
                group_id=group_id,
            )
            .returning(Account)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
