"""
Account repository — data access layer for accounts, customers, and xref tables.

COBOL origin: Replaces CICS file-control commands:

  GET by account ID:
    EXEC CICS READ DATASET('ACCTDAT') INTO(ACCOUNT-RECORD) RIDFLD(ACCT-ID) RESP RESP2
    RESP=NORMAL → account found   → get_account_by_id returns Account
    RESP=NOTFND → account missing → get_account_by_id returns None

  GET customer via xref:
    EXEC CICS READ DATASET('CXACAIX') RIDFLD(WS-XREF-RID) KEYLENGTH(11) GTEQ RESP RESP2
    → get CUST-ID from XREF-CUST-ID
    EXEC CICS READ DATASET('CUSTDAT') INTO(CUSTOMER-RECORD) RIDFLD(CUST-ID) RESP RESP2
    → get_customer_by_account_id replaces both steps with a single JOIN

  UPDATE account and customer:
    EXEC CICS READ DATASET('ACCTDAT') UPDATE ... REWRITE ...
    EXEC CICS READ DATASET('CUSTDAT') UPDATE ... REWRITE ...
    → update_account_and_customer performs both updates in one transaction
    WS-DATACHANGED-FLAG logic: only update fields that changed (handled in service)

No business logic lives here — only SQL queries via SQLAlchemy ORM.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.account_customer_xref import AccountCustomerXref
from app.models.customer import Customer


# SEC-04: Allowlists of column names that may be mutated via update_account_and_customer.
# setattr() on a SQLAlchemy mapped object does not raise for arbitrary attribute names,
# so without this guard an unexpected key (e.g. from a future code-path bug) could
# silently set a non-column attribute or interfere with _sa_instance_state.
_ACCOUNT_UPDATABLE_FIELDS: frozenset = frozenset({
    "active_status",
    "open_date",
    "expiration_date",
    "reissue_date",
    "credit_limit",
    "cash_credit_limit",
    "current_balance",
    "curr_cycle_credit",
    "curr_cycle_debit",
    "group_id",
})

_CUSTOMER_UPDATABLE_FIELDS: frozenset = frozenset({
    "first_name",
    "middle_name",
    "last_name",
    "street_address_1",
    "street_address_2",
    "city",
    "state_code",
    "zip_code",
    "country_code",
    "phone_number_1",
    "phone_number_2",
    "ssn",
    "date_of_birth",
    "fico_score",
    "government_id_ref",
    "eft_account_id",
    "primary_card_holder_flag",
})


class AccountRepository:
    """Data access for accounts, customers, and their cross-reference."""

    @staticmethod
    async def get_account_by_id(
        db: AsyncSession, account_id: int
    ) -> Optional[Account]:
        """
        Fetch an account by primary key.

        COBOL origin: EXEC CICS READ DATASET('ACCTDAT') RIDFLD(ACCT-ID)
        Returns None when RESP=NOTFND (13); raises on other errors.
        """
        result = await db.execute(
            select(Account).where(Account.account_id == account_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_customer_by_account_id(
        db: AsyncSession, account_id: int
    ) -> Optional[Customer]:
        """
        Fetch the customer linked to the given account via the xref table.

        COBOL origin: Two-step CICS operation in COACTVWC 9000-READ-ACCT:
          1. EXEC CICS READ DATASET('CXACAIX') RIDFLD(acct_id) → get XREF-CUST-ID
          2. EXEC CICS READ DATASET('CUSTDAT') RIDFLD(XREF-CUST-ID) → get CUSTOMER-RECORD

        Replaced by a single JOIN query:
          SELECT c.* FROM customers c
          JOIN account_customer_xref x ON c.customer_id = x.customer_id
          WHERE x.account_id = :account_id
        Returns None if no xref entry exists (maps DID-NOT-FIND-ACCT-IN-CARDXREF condition).
        """
        result = await db.execute(
            select(Customer)
            .join(
                AccountCustomerXref,
                AccountCustomerXref.customer_id == Customer.customer_id,
            )
            .where(AccountCustomerXref.account_id == account_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_xref_by_account_id(
        db: AsyncSession, account_id: int
    ) -> Optional[AccountCustomerXref]:
        """
        Fetch the xref entry for a given account.

        Used during update to verify the customer_id in the request matches
        the linked customer. Maps COACTUPC implicit assumption that the
        account-to-customer relationship is established before update.
        """
        result = await db.execute(
            select(AccountCustomerXref).where(
                AccountCustomerXref.account_id == account_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_account_and_customer(
        db: AsyncSession,
        account: Account,
        customer: Customer,
        account_changes: dict,
        customer_changes: dict,
    ) -> Account:
        """
        Apply field-level updates to account and customer in one transaction.

        COBOL origin: COACTUPC 9000-UPDATE-ACCOUNT paragraph:
          EXEC CICS READ DATASET('ACCTDAT') UPDATE ...
          (validate WS-DATACHANGED-FLAG)
          EXEC CICS REWRITE DATASET('ACCTDAT') FROM(ACCT-UPDATE-RECORD) ...
          EXEC CICS READ DATASET('CUSTDAT') UPDATE ...
          EXEC CICS REWRITE DATASET('CUSTDAT') FROM(CUST-UPDATE-RECORD) ...

        WS-DATACHANGED-FLAG logic: the caller (AccountService) is responsible
        for providing only the changed fields in account_changes and
        customer_changes. If both dicts are empty, the caller raises 422
        before reaching here.

        Both updates run within the same SQLAlchemy session (transaction),
        matching COBOL's implicit within-task atomicity.
        """
        # SEC-04: Validate field names against allowlists before applying setattr.
        # setattr on a mapped object does not raise for non-column attribute names,
        # so this guard prevents unexpected keys from silently corrupting ORM state.
        for field, value in account_changes.items():
            if field not in _ACCOUNT_UPDATABLE_FIELDS:
                raise ValueError(
                    f"Unexpected account field in update dict: {field!r}. "
                    f"Permitted fields: {sorted(_ACCOUNT_UPDATABLE_FIELDS)}"
                )
            setattr(account, field, value)

        for field, value in customer_changes.items():
            if field not in _CUSTOMER_UPDATABLE_FIELDS:
                raise ValueError(
                    f"Unexpected customer field in update dict: {field!r}. "
                    f"Permitted fields: {sorted(_CUSTOMER_UPDATABLE_FIELDS)}"
                )
            setattr(customer, field, value)

        db.add(account)
        db.add(customer)
        await db.flush()
        await db.refresh(account)
        return account
