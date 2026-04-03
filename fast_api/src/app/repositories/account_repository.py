"""Account repository — data access layer.

Translates COBOL VSAM file operations to SQLAlchemy queries:
  - EXEC CICS READ DATASET('CXACAIX')  → JOIN card_cross_references
  - EXEC CICS READ DATASET('ACCTDAT')  → SELECT FROM accounts
  - EXEC CICS READ DATASET('CUSTDAT')  → SELECT FROM customers
  - EXEC CICS READ FILE('ACCTDAT') UPDATE → SELECT ... FOR UPDATE NOWAIT
  - EXEC CICS REWRITE FILE('ACCTDAT')  → UPDATE accounts SET ...
"""

from datetime import datetime
from typing import NamedTuple

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.card import Card
from app.models.card_cross_reference import CardCrossReference
from app.models.customer import Customer


class AccountWithRelations(NamedTuple):
    """Container matching the data gathered by COACTVWC 9000-READ-ACCT.

    In COBOL: ACCOUNT-RECORD + CUSTOMER-RECORD + CARD-XREF-RECORD
    were loaded into separate working-storage areas by three separate
    EXEC CICS READ calls. Here we return them in one structured result.
    """

    account: Account
    customer: Customer | None
    cards: list[Card]


class AccountRepository:
    """Data access for accounts, customers, cards and cross-references.

    All methods are async and accept a pre-opened AsyncSession.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_account_with_relations(
        self, acct_id: str
    ) -> AccountWithRelations | None:
        """Fetch account + customer + cards via the cross-reference table.

        Replicates COACTVWC 9000-READ-ACCT:
          9200-GETCARDXREF-BYACCT → JOIN card_cross_references on xref_acct_id
          9300-GETACCTDATA-BYACCT → account row
          9400-GETCUSTDATA-BYCUST → customer row via xref_cust_id
        """
        # Step 1: fetch account (9300-GETACCTDATA-BYACCT)
        account = await self._session.get(Account, acct_id)
        if account is None:
            return None

        # Step 2: get the first cross-reference for this account (9200-GETCARDXREF-BYACCT)
        xref_stmt = (
            select(CardCrossReference)
            .where(CardCrossReference.xref_acct_id == acct_id)
            .limit(1)
        )
        xref_result = await self._session.execute(xref_stmt)
        xref = xref_result.scalar_one_or_none()

        # Step 3: fetch customer via xref (9400-GETCUSTDATA-BYCUST)
        customer: Customer | None = None
        if xref and xref.xref_cust_id:
            customer = await self._session.get(Customer, xref.xref_cust_id)

        # Step 4: fetch all cards linked to this account
        cards_stmt = select(Card).where(Card.card_acct_id == acct_id)
        cards_result = await self._session.execute(cards_stmt)
        cards = list(cards_result.scalars().all())

        return AccountWithRelations(account=account, customer=customer, cards=cards)

    async def get_account_for_update(self, acct_id: str) -> Account | None:
        """Fetch account with a row-level lock.

        Replaces EXEC CICS READ FILE('ACCTDAT') UPDATE which acquired
        an exclusive VSAM enqueue before REWRITE.
        Uses SELECT ... FOR UPDATE NOWAIT so concurrent requests fail fast
        rather than queueing (matching CICS dequeue-on-taskend semantics).
        """
        stmt = (
            select(Account)
            .where(Account.acct_id == acct_id)
            .with_for_update(nowait=True)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_customer_for_update(self, cust_id: str) -> Customer | None:
        """Fetch customer with a row-level lock.

        Replaces EXEC CICS READ FILE('CUSTDAT') UPDATE.
        """
        stmt = (
            select(Customer)
            .where(Customer.cust_id == cust_id)
            .with_for_update(nowait=True)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_customer_id_by_account(self, acct_id: str) -> str | None:
        """Lookup customer ID via card cross-reference.

        Replicates 9200-GETCARDXREF-BYACCT reading CXACAIX alternate index.
        """
        stmt = (
            select(CardCrossReference.xref_cust_id)
            .where(CardCrossReference.xref_acct_id == acct_id)
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_account(
        self,
        account: Account,
        update_data: dict,
    ) -> Account:
        """Apply updates to the account row.

        Replaces EXEC CICS REWRITE FILE('ACCTDAT') FROM(ACCT-UPDATE-RECORD).
        The caller must hold a transaction (get_account_for_update was called).
        """
        for field, value in update_data.items():
            setattr(account, field, value)
        await self._session.flush()
        await self._session.refresh(account)
        return account

    async def update_customer(
        self,
        customer: Customer,
        update_data: dict,
    ) -> Customer:
        """Apply updates to the customer row.

        Replaces EXEC CICS REWRITE FILE('CUSTDAT') FROM(CUST-UPDATE-RECORD).
        """
        for field, value in update_data.items():
            setattr(customer, field, value)
        await self._session.flush()
        await self._session.refresh(customer)
        return customer

    async def commit(self) -> None:
        """Commit the current transaction (EXEC CICS SYNCPOINT)."""
        await self._session.commit()

    async def rollback(self) -> None:
        """Roll back the current transaction (EXEC CICS SYNCPOINT ROLLBACK)."""
        await self._session.rollback()
