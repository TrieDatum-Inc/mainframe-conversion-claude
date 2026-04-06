"""
Customer repository — CUSTDAT VSAM KSDS operations.

COBOL origin: Replaces EXEC CICS READ/REWRITE DATASET('CUSTDAT').
Also provides get_by_account_id which replaces the CARDAIX AIX browse
used by COACTVWC to find the customer linked to an account.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account_customer_xref import AccountCustomerXref
from app.models.customer import Customer


class CustomerRepository:
    """
    Data access object for the `customers` table.

    get_by_account_id() replaces COACTVWC's CARDXREF browse:
      EXEC CICS STARTBR DATASET(CARDAIX) RIDFLD(ACCT-ID)
      EXEC CICS READNEXT → get XREF-CUST-ID
      EXEC CICS READ DATASET(CUSTDAT) RIDFLD(XREF-CUST-ID)
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, customer_id: int) -> Customer | None:
        """
        EXEC CICS READ DATASET('CUSTDAT') INTO(CUSTOMER-RECORD)
               RIDFLD(CUST-ID).
        """
        result = await self.db.execute(
            select(Customer).where(Customer.customer_id == customer_id)
        )
        return result.scalar_one_or_none()

    async def get_by_account_id(self, account_id: int) -> Customer | None:
        """
        Find the customer linked to an account via account_customer_xref.

        COACTVWC original flow:
          1. STARTBR CARDAIX RIDFLD(ACCT-ID) → find XREF-CUST-ID
          2. READ CUSTDAT RIDFLD(XREF-CUST-ID) → load customer

        Replaced by JOIN: account_customer_xref → customers.
        Returns the first linked customer (accounts typically have one).
        """
        result = await self.db.execute(
            select(Customer)
            .join(
                AccountCustomerXref,
                AccountCustomerXref.customer_id == Customer.customer_id,
            )
            .where(AccountCustomerXref.account_id == account_id)
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def update(self, customer: Customer) -> Customer:
        """
        EXEC CICS REWRITE DATASET('CUSTDAT') FROM(CUSTOMER-RECORD).
        """
        await self.db.flush()
        await self.db.refresh(customer)
        return customer
