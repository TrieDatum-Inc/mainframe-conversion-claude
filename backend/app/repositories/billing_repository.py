"""
Data access layer for billing operations.

COBOL origin: COBIL00C — Online Bill Payment program.

Key CICS command replacements:
  READ UPDATE ACCTDAT → SELECT ... FOR UPDATE (pessimistic lock for payment)
  REWRITE ACCTDAT → UPDATE accounts SET current_balance = 0
  READ CXACAIX (AIX) → SELECT from card_account_xref WHERE account_id = ?
  STARTBR/READPREV TRANSACT → replaced by transaction_id_seq (in transaction_repository)
  WRITE TRANSACT → handled by transaction_repository.create()
"""

from decimal import Decimal
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.card_xref import CardAccountXref


class BillingRepository:
    """
    Repository for billing-related database operations.

    COBOL equivalent: COBIL00C READ-ACCTDAT-FILE, UPDATE-ACCTDAT-FILE, READ-CXACAIX-FILE.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_account_balance(self, account_id: int) -> Optional[Account]:
        """
        Get account for balance display (Phase 1: read-only).

        COBOL origin: COBIL00C READ-ACCTDAT-FILE when CONFIRMI=SPACES.
          EXEC CICS READ DATASET('ACCTDAT') INTO(ACCOUNT-RECORD)
                    RIDFLD(ACCT-ID) UPDATE RESP RESP2

        Note: COBIL00C reads with UPDATE lock even for display-only Phase 1.
        The modern API uses plain SELECT for Phase 1 (no lock needed for display).
        Phase 2 (payment) uses SELECT FOR UPDATE for proper pessimistic locking.
        """
        result = await self.db.execute(
            select(Account).where(Account.account_id == account_id)
        )
        return result.scalar_one_or_none()

    async def get_account_for_update(self, account_id: int) -> Optional[Account]:
        """
        Get account with pessimistic lock for payment processing (Phase 2).

        COBOL origin: COBIL00C READ-ACCTDAT-FILE when CONFIRMI='Y'.
          EXEC CICS READ DATASET('ACCTDAT') INTO(ACCOUNT-RECORD)
                    RIDFLD(ACCT-ID) UPDATE RESP RESP2
          → SELECT ... FOR UPDATE (prevents double-payment race condition)

        CICS READ UPDATE prevented other tasks from modifying the account record
        until the task ended. PostgreSQL FOR UPDATE provides equivalent protection.
        """
        result = await self.db.execute(
            select(Account)
            .where(Account.account_id == account_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def get_card_for_account(self, account_id: int) -> Optional[str]:
        """
        Get card number for an account via cross-reference.

        COBOL origin: COBIL00C READ-CXACAIX-FILE:
          EXEC CICS READ DATASET('CXACAIX') INTO(CARD-XREF-RECORD)
                    RIDFLD(XREF-ACCT-ID) KEYLENGTH(11) RESP RESP2
          → CXACAIX is the alternate index on CCXREF keyed by XREF-ACCT-ID
          → Returns XREF-CARD-NUM used as TRAN-CARD-NUM in the payment transaction

        PostgreSQL replaces the VSAM alternate index with a regular index on
        card_account_xref.account_id.
        """
        result = await self.db.execute(
            select(CardAccountXref.card_number)
            .where(CardAccountXref.account_id == account_id)
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def update_account_balance(
        self, account_id: int, new_balance: Decimal
    ) -> bool:
        """
        Update account balance after payment.

        COBOL origin: COBIL00C UPDATE-ACCTDAT-FILE:
          COMPUTE ACCT-CURR-BAL = ACCT-CURR-BAL - TRAN-AMT
          (where TRAN-AMT = original ACCT-CURR-BAL, so result = 0)
          EXEC CICS REWRITE DATASET('ACCTDAT') FROM(ACCOUNT-RECORD) RESP RESP2

        The new_balance will always be 0 for full bill payment (COBIL00C hardcodes
        full balance deduction). Stored as Decimal for precision.
        """
        result = await self.db.execute(
            update(Account)
            .where(Account.account_id == account_id)
            .values(current_balance=new_balance)
            .returning(Account.account_id)
        )
        updated = result.scalar_one_or_none()
        return updated is not None
