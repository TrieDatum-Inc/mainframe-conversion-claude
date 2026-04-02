"""
Account and Customer repository — data access layer.

Replaces VSAM KSDS EXEC CICS READ/REWRITE/WRITE operations on:
  ACCTDAT  (account master)
  CUSTDAT  (customer master)
  CXACAIX  (card xref alternate index lookup by account ID)
"""

from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError
from app.infrastructure.orm.account_orm import AccountORM
from app.infrastructure.orm.card_orm import CardXrefORM
from app.infrastructure.orm.customer_orm import CustomerORM


class AccountRepository:
    """
    Account VSAM KSDS operations.
    Mapped from:
      EXEC CICS READ DATASET('ACCTDAT') RIDFLD(acct-id)
      EXEC CICS REWRITE DATASET('ACCTDAT')
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, acct_id: int) -> AccountORM:
        """
        Read account by primary key.
        Equivalent to: EXEC CICS READ DATASET('ACCTDAT') RIDFLD(acct_id)
        Raises ResourceNotFoundError (maps RESP=NOTFND) if not found.
        """
        stmt = select(AccountORM).where(AccountORM.acct_id == acct_id)
        result = await self.db.execute(stmt)
        account = result.scalar_one_or_none()
        if account is None:
            raise ResourceNotFoundError("Account", str(acct_id))
        return account

    async def get_by_id_or_none(self, acct_id: int) -> Optional[AccountORM]:
        """Read account; return None if not found (does not raise)."""
        stmt = select(AccountORM).where(AccountORM.acct_id == acct_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, account: AccountORM) -> AccountORM:
        """
        Update account record.
        Equivalent to: EXEC CICS REWRITE DATASET('ACCTDAT')
        """
        await self.db.flush()
        return account

    async def create(self, account: AccountORM) -> AccountORM:
        """
        Write new account record.
        Equivalent to: EXEC CICS WRITE DATASET('ACCTDAT')
        """
        self.db.add(account)
        await self.db.flush()
        return account

    async def get_xref_by_account_id(self, acct_id: int) -> Optional[CardXrefORM]:
        """
        Lookup card xref by account ID via alternate index.
        Equivalent to:
          EXEC CICS READ DATASET('CXACAIX') RIDFLD(acct_id) (alternate index lookup)
        Used by COACTVWC, COACTUPC, COBIL00C, COTRN02C.
        Returns the first matching cross-reference record (VSAM AIX returns first hit).
        """
        stmt = (
            select(CardXrefORM)
            .where(CardXrefORM.acct_id == acct_id)
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


class CustomerRepository:
    """
    Customer VSAM KSDS operations.
    Mapped from:
      EXEC CICS READ DATASET('CUSTDAT') RIDFLD(cust_id)
      EXEC CICS REWRITE DATASET('CUSTDAT')
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, cust_id: int) -> CustomerORM:
        """
        Read customer by primary key.
        Raises ResourceNotFoundError if not found.
        """
        stmt = select(CustomerORM).where(CustomerORM.cust_id == cust_id)
        result = await self.db.execute(stmt)
        customer = result.scalar_one_or_none()
        if customer is None:
            raise ResourceNotFoundError("Customer", str(cust_id))
        return customer

    async def get_by_id_or_none(self, cust_id: int) -> Optional[CustomerORM]:
        """Read customer; return None if not found."""
        stmt = select(CustomerORM).where(CustomerORM.cust_id == cust_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, customer: CustomerORM) -> CustomerORM:
        """
        Update customer record.
        Equivalent to: EXEC CICS REWRITE DATASET('CUSTDAT')
        """
        await self.db.flush()
        return customer

    async def create(self, customer: CustomerORM) -> CustomerORM:
        """Write new customer record."""
        self.db.add(customer)
        await self.db.flush()
        return customer
