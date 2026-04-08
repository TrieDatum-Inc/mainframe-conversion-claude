"""
Account repository — data access layer for ACCTDAT VSAM file operations.

All EXEC CICS file operations on ACCTDAT map to methods here:
  EXEC CICS READ   FILE(ACCTDAT) INTO(ACCOUNT-RECORD) RIDFLD(ACCT-ID) → get_by_id()
  EXEC CICS REWRITE FILE(ACCTDAT) FROM(ACCOUNT-RECORD)               → update()

Source programs: COACTVWC, COACTUPC, COBIL00C, CBTRN01C, CBACT04C

Also reads CUSTDAT and CCXREF for account detail view (COACTVWC join logic).
"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.account import Account
from app.models.card import CardXref
from app.models.customer import Customer
from app.utils.error_handlers import RecordNotFoundError


class AccountRepository:
    """Data access object for the `accounts` table (ACCTDAT VSAM)."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, acct_id: int) -> Account:
        """
        EXEC CICS READ FILE('ACCTDAT') INTO(ACCOUNT-RECORD) RIDFLD(WS-ACCT-ID)

        Used by COACTVWC, COACTUPC, COBIL00C.
        RESP=13 (NOTFND) → RecordNotFoundError.

        Args:
            acct_id: ACCT-ID PIC 9(11) value.

        Returns:
            Account ORM instance.

        Raises:
            RecordNotFoundError: Account not found (CICS RESP=13 NOTFND).
        """
        account = await self._db.get(Account, acct_id)
        if account is None:
            raise RecordNotFoundError(f"Account not found (id={acct_id})")
        return account

    async def get_with_customer(self, acct_id: int) -> tuple[Account, Customer | None]:
        """
        Joined read of ACCTDAT + CCXREF + CUSTDAT.

        COACTVWC reads these three files to build the account view:
          1. READ FILE(ACCTDAT) by ACCT-ID
          2. STARTBR FILE(CXACAIX) — find xref by account
          3. READ FILE(CUSTDAT) by CUST-ID from xref

        Returns:
            Tuple of (Account, Customer or None).
        """
        account = await self.get_by_id(acct_id)

        xref_stmt = (
            select(CardXref)
            .where(CardXref.acct_id == acct_id)
            .limit(1)
        )
        xref_result = await self._db.execute(xref_stmt)
        xref = xref_result.scalar_one_or_none()

        customer = None
        if xref:
            customer = await self._db.get(Customer, xref.cust_id)

        return account, customer

    async def update(self, account: Account) -> Account:
        """
        EXEC CICS REWRITE FILE('ACCTDAT') FROM(ACCOUNT-RECORD)

        COACTUPC and COBIL00C use rewrite after reading the record.
        """
        merged = await self._db.merge(account)
        await self._db.flush()
        return merged
