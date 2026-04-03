"""Export/import data access repository.

Maps CBEXPORT sequential reads and CBIMPORT sequential writes for all 5 entity types.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.card import Card
from app.models.card_cross_reference import CardCrossReference
from app.models.customer import Customer
from app.models.transaction import Transaction


class ExportImportRepository:
    """Data access for all entities required by CBEXPORT and CBIMPORT."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all_customers(self) -> list[Customer]:
        """Sequential read of customers. Maps CBEXPORT 2000-EXPORT-CUSTOMERS."""
        result = await self.db.execute(
            select(Customer).order_by(Customer.cust_id)
        )
        return list(result.scalars().all())

    async def get_all_accounts(self) -> list[Account]:
        """Sequential read of accounts. Maps CBEXPORT 3000-EXPORT-ACCOUNTS."""
        result = await self.db.execute(
            select(Account).order_by(Account.acct_id)
        )
        return list(result.scalars().all())

    async def get_all_xrefs(self) -> list[CardCrossReference]:
        """Sequential read of xrefs. Maps CBEXPORT 4000-EXPORT-XREFS."""
        result = await self.db.execute(
            select(CardCrossReference).order_by(CardCrossReference.xref_card_num)
        )
        return list(result.scalars().all())

    async def get_all_transactions(self) -> list[Transaction]:
        """Sequential read of transactions. Maps CBEXPORT 5000-EXPORT-TRANSACTIONS."""
        result = await self.db.execute(
            select(Transaction).order_by(Transaction.tran_id)
        )
        return list(result.scalars().all())

    async def get_all_cards(self) -> list[Card]:
        """Sequential read of cards. Maps CBEXPORT 5500-EXPORT-CARDS."""
        result = await self.db.execute(
            select(Card).order_by(Card.card_num)
        )
        return list(result.scalars().all())

    async def upsert_customer(self, customer: Customer) -> Customer:
        """Insert or update a customer. Maps CBIMPORT 2300-PROCESS-CUSTOMER-RECORD."""
        result = await self.db.execute(
            select(Customer).where(Customer.cust_id == customer.cust_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            for attr in [
                "cust_first_name", "cust_middle_name", "cust_last_name",
                "cust_addr_line_1", "cust_addr_line_2", "cust_addr_line_3",
                "cust_addr_state_cd", "cust_addr_country_cd", "cust_addr_zip",
                "cust_phone_num_1", "cust_phone_num_2", "cust_ssn",
                "cust_govt_issued_id", "cust_dob", "cust_eft_account_id",
                "cust_pri_card_holder_ind", "cust_fico_credit_score",
            ]:
                setattr(existing, attr, getattr(customer, attr))
            await self.db.flush()
            return existing
        self.db.add(customer)
        await self.db.flush()
        return customer

    async def upsert_account(self, account: Account) -> Account:
        """Insert or update an account. Maps CBIMPORT 2400-PROCESS-ACCOUNT-RECORD."""
        result = await self.db.execute(
            select(Account).where(Account.acct_id == account.acct_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            for attr in [
                "acct_active_status", "acct_curr_bal", "acct_credit_limit",
                "acct_cash_credit_limit", "acct_open_date", "acct_expiration_date",
                "acct_reissue_date", "acct_curr_cyc_credit", "acct_curr_cyc_debit",
                "acct_addr_zip", "acct_group_id",
            ]:
                setattr(existing, attr, getattr(account, attr))
            await self.db.flush()
            return existing
        self.db.add(account)
        await self.db.flush()
        return account

    async def upsert_xref(self, xref: CardCrossReference) -> CardCrossReference:
        """Insert or update a xref. Maps CBIMPORT 2500-PROCESS-XREF-RECORD."""
        result = await self.db.execute(
            select(CardCrossReference).where(
                CardCrossReference.xref_card_num == xref.xref_card_num
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.xref_cust_id = xref.xref_cust_id
            existing.xref_acct_id = xref.xref_acct_id
            await self.db.flush()
            return existing
        self.db.add(xref)
        await self.db.flush()
        return xref

    async def upsert_transaction(self, transaction: Transaction) -> Transaction:
        """Insert or update a transaction. Maps CBIMPORT 2600-PROCESS-TRAN-RECORD."""
        result = await self.db.execute(
            select(Transaction).where(Transaction.tran_id == transaction.tran_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            for attr in [
                "tran_type_cd", "tran_cat_cd", "tran_source", "tran_desc",
                "tran_amt", "tran_merchant_id", "tran_merchant_name",
                "tran_merchant_city", "tran_merchant_zip", "tran_card_num",
                "tran_orig_ts", "tran_proc_ts",
            ]:
                setattr(existing, attr, getattr(transaction, attr))
            await self.db.flush()
            return existing
        self.db.add(transaction)
        await self.db.flush()
        return transaction

    async def upsert_card(self, card: Card) -> Card:
        """Insert or update a card. Maps CBIMPORT 2650-PROCESS-CARD-RECORD."""
        result = await self.db.execute(
            select(Card).where(Card.card_num == card.card_num)
        )
        existing = result.scalar_one_or_none()
        if existing:
            for attr in [
                "card_acct_id", "card_cvv_cd", "card_embossed_name",
                "card_expiration_date", "card_active_status",
            ]:
                setattr(existing, attr, getattr(card, attr))
            await self.db.flush()
            return existing
        self.db.add(card)
        await self.db.flush()
        return card
