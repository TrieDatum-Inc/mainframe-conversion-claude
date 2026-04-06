"""
Customer repository — data access layer for the `customers` table.

COBOL origin: Replaces EXEC CICS READ/REWRITE DATASET(CUSTDAT).
  COACTVWC: READ CUSTDAT by CUST-ID (obtained from account-customer xref) → get_by_id
  COACTUPC: REWRITE CUSTDAT → update
"""

from datetime import date
from typing import Optional

from sqlalchemy import join, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account_customer_xref import AccountCustomerXref
from app.models.customer import Customer


class CustomerRepository:
    """
    Data access operations for the `customers` table.

    No business logic here — only SQLAlchemy queries.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, customer_id: int) -> Optional[Customer]:
        """
        Fetch customer by primary key.

        COBOL: EXEC CICS READ DATASET(CUSTDAT) INTO(CUSTOMER-RECORD)
               RIDFLD(WS-CUST-ID)
        """
        stmt = select(Customer).where(Customer.customer_id == customer_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_account_id(self, account_id: int) -> Optional[Customer]:
        """
        Fetch customer linked to an account via account_customer_xref.

        COBOL: COACTVWC reads CARDAIX (alternate index) by account_id to find
        the customer. This join replicates that cross-reference lookup:
          READ CARDAIX → get customer_id → READ CUSTDAT by customer_id.
        """
        stmt = (
            select(Customer)
            .join(
                AccountCustomerXref,
                Customer.customer_id == AccountCustomerXref.customer_id,
            )
            .where(AccountCustomerXref.account_id == account_id)
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update(
        self,
        customer_id: int,
        first_name: str,
        middle_name: Optional[str],
        last_name: str,
        street_address_1: Optional[str],
        street_address_2: Optional[str],
        city: Optional[str],
        state_code: Optional[str],
        zip_code: Optional[str],
        country_code: Optional[str],
        phone_number_1: Optional[str],
        phone_number_2: Optional[str],
        ssn: Optional[str],
        date_of_birth: Optional[date],
        fico_score: Optional[int],
        government_id_ref: Optional[str],
        eft_account_id: Optional[str],
        primary_card_holder_flag: str,
    ) -> Optional[Customer]:
        """
        Update customer fields.

        COBOL: EXEC CICS REWRITE DATASET(CUSTDAT) FROM(CUSTOMER-RECORD)
        Part of the atomic account+customer update in COACTUPC.
        """
        stmt = (
            update(Customer)
            .where(Customer.customer_id == customer_id)
            .values(
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                street_address_1=street_address_1,
                street_address_2=street_address_2,
                city=city,
                state_code=state_code,
                zip_code=zip_code,
                country_code=country_code,
                phone_number_1=phone_number_1,
                phone_number_2=phone_number_2,
                ssn=ssn,
                date_of_birth=date_of_birth,
                fico_score=fico_score,
                government_id_ref=government_id_ref,
                eft_account_id=eft_account_id,
                primary_card_holder_flag=primary_card_holder_flag,
            )
            .returning(Customer)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
