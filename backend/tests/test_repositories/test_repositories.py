"""
Integration tests for repository classes.

Uses the shared in-memory SQLite engine from conftest.py.
Covers: UserRepository, CustomerRepository, CardXrefRepository,
        AccountRepository, CreditCardRepository.
"""

import pytest
from datetime import date, datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.account_customer_xref import AccountCustomerXref
from app.models.card_xref import CardXref
from app.models.credit_card import CreditCard
from app.models.customer import Customer
from app.models.user import User
from app.repositories.account_repository import AccountRepository
from app.repositories.card_xref_repository import CardXrefRepository
from app.repositories.credit_card_repository import CreditCardRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.user_repository import UserRepository
from app.utils.security import hash_password


# =============================================================================
# UserRepository
# =============================================================================

class TestUserRepository:
    @pytest.mark.asyncio
    async def test_get_by_id_returns_user_when_exists(self, db_session: AsyncSession, admin_user: User):
        repo = UserRepository(db_session)
        found = await repo.get_by_id(admin_user.user_id)
        assert found is not None
        assert found.user_id == admin_user.user_id

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_missing(self, db_session: AsyncSession):
        repo = UserRepository(db_session)
        found = await repo.get_by_id("NOTEXIST")
        assert found is None

    @pytest.mark.asyncio
    async def test_create_persists_user(self, db_session: AsyncSession):
        repo = UserRepository(db_session)
        user = User(
            user_id="NEWU0001",
            first_name="New",
            last_name="User",
            password_hash=hash_password("TempPass"),
            user_type="U",
        )
        created = await repo.create(user)
        assert created.user_id == "NEWU0001"
        assert created.created_at is not None

    @pytest.mark.asyncio
    async def test_update_persists_changes(self, db_session: AsyncSession, regular_user: User):
        repo = UserRepository(db_session)
        regular_user.last_name = "Changed"
        updated = await repo.update(regular_user)
        assert updated.last_name == "Changed"

    @pytest.mark.asyncio
    async def test_delete_removes_user(self, db_session: AsyncSession):
        repo = UserRepository(db_session)
        user = User(
            user_id="DELME001",
            first_name="Del",
            last_name="Me",
            password_hash=hash_password("pass"),
            user_type="U",
        )
        db_session.add(user)
        await db_session.flush()

        await repo.delete(user)
        found = await repo.get_by_id("DELME001")
        assert found is None

    @pytest.mark.asyncio
    async def test_list_paginated_returns_all_users(
        self, db_session: AsyncSession, admin_user: User, regular_user: User
    ):
        repo = UserRepository(db_session)
        users, total = await repo.list_paginated(page=1, page_size=100)
        assert total >= 2
        user_ids = {u.user_id for u in users}
        assert admin_user.user_id in user_ids
        assert regular_user.user_id in user_ids

    @pytest.mark.asyncio
    async def test_list_paginated_with_filter(
        self, db_session: AsyncSession, admin_user: User, regular_user: User
    ):
        repo = UserRepository(db_session)
        users, _ = await repo.list_paginated(
            page=1, page_size=100, user_id_filter="ADMIN"
        )
        ids = [u.user_id for u in users]
        assert admin_user.user_id in ids
        assert regular_user.user_id not in ids

    @pytest.mark.asyncio
    async def test_list_paginated_respects_page_size(
        self, db_session: AsyncSession, admin_user: User, regular_user: User
    ):
        repo = UserRepository(db_session)
        users, total = await repo.list_paginated(page=1, page_size=1)
        assert len(users) == 1
        assert total >= 2

    @pytest.mark.asyncio
    async def test_list_paginated_page_offset(
        self, db_session: AsyncSession, admin_user: User, regular_user: User
    ):
        repo = UserRepository(db_session)
        page1_users, _ = await repo.list_paginated(page=1, page_size=1)
        page2_users, _ = await repo.list_paginated(page=2, page_size=1)
        assert page1_users[0].user_id != page2_users[0].user_id


# =============================================================================
# CustomerRepository
# =============================================================================

class TestCustomerRepository:
    @pytest.mark.asyncio
    async def test_get_by_id_returns_customer(
        self, db_session: AsyncSession, sample_customer: Customer
    ):
        repo = CustomerRepository(db_session)
        found = await repo.get_by_id(sample_customer.customer_id)
        assert found is not None
        assert found.customer_id == sample_customer.customer_id

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_missing(self, db_session: AsyncSession):
        repo = CustomerRepository(db_session)
        found = await repo.get_by_id(999999)
        assert found is None

    @pytest.mark.asyncio
    async def test_get_by_account_id_returns_linked_customer(
        self,
        db_session: AsyncSession,
        sample_account: Account,
        sample_customer: Customer,
        sample_account_customer_xref: AccountCustomerXref,
    ):
        repo = CustomerRepository(db_session)
        found = await repo.get_by_account_id(sample_account.account_id)
        assert found is not None
        assert found.customer_id == sample_customer.customer_id

    @pytest.mark.asyncio
    async def test_get_by_account_id_returns_none_when_no_xref(
        self, db_session: AsyncSession
    ):
        """No xref entry → returns None (no customer linked to this account)."""
        repo = CustomerRepository(db_session)
        found = await repo.get_by_account_id(999888)
        assert found is None

    @pytest.mark.asyncio
    async def test_update_persists_changes(
        self,
        db_session: AsyncSession,
        sample_customer: Customer,
    ):
        repo = CustomerRepository(db_session)
        sample_customer.first_name = "Jane"
        updated = await repo.update(sample_customer)
        assert updated.first_name == "Jane"


# =============================================================================
# AccountRepository
# =============================================================================

class TestAccountRepository:
    @pytest.mark.asyncio
    async def test_get_by_id_returns_account(
        self, db_session: AsyncSession, sample_account: Account
    ):
        repo = AccountRepository(db_session)
        found = await repo.get_by_id(sample_account.account_id)
        assert found is not None
        assert found.account_id == sample_account.account_id

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_missing(self, db_session: AsyncSession):
        repo = AccountRepository(db_session)
        found = await repo.get_by_id(999999)
        assert found is None

    @pytest.mark.asyncio
    async def test_update_persists_changes(
        self, db_session: AsyncSession, sample_account: Account
    ):
        repo = AccountRepository(db_session)
        sample_account.active_status = "N"
        updated = await repo.update(sample_account)
        assert updated.active_status == "N"


# =============================================================================
# CreditCardRepository
# =============================================================================

class TestCreditCardRepository:
    @pytest.mark.asyncio
    async def test_get_by_number_returns_card(
        self, db_session: AsyncSession, sample_card: CreditCard
    ):
        repo = CreditCardRepository(db_session)
        found = await repo.get_by_number(sample_card.card_number)
        assert found is not None
        assert found.card_number == sample_card.card_number

    @pytest.mark.asyncio
    async def test_get_by_number_returns_none_when_missing(self, db_session: AsyncSession):
        repo = CreditCardRepository(db_session)
        found = await repo.get_by_number("9999999999999999")
        assert found is None

    @pytest.mark.asyncio
    async def test_list_by_filters_returns_all_cards(
        self, db_session: AsyncSession, sample_card: CreditCard
    ):
        repo = CreditCardRepository(db_session)
        cards, total = await repo.list_by_filters(page=1, page_size=100)
        assert total >= 1
        numbers = [c.card_number for c in cards]
        assert sample_card.card_number in numbers

    @pytest.mark.asyncio
    async def test_list_by_filters_account_id_filter(
        self, db_session: AsyncSession, sample_card: CreditCard
    ):
        repo = CreditCardRepository(db_session)
        cards, total = await repo.list_by_filters(
            page=1, page_size=100, account_id=sample_card.account_id
        )
        assert total >= 1
        for c in cards:
            assert c.account_id == sample_card.account_id

    @pytest.mark.asyncio
    async def test_list_by_filters_account_id_no_match(self, db_session: AsyncSession):
        repo = CreditCardRepository(db_session)
        cards, total = await repo.list_by_filters(
            page=1, page_size=100, account_id=999999
        )
        assert total == 0
        assert cards == []

    @pytest.mark.asyncio
    async def test_list_by_filters_card_number_prefix(
        self, db_session: AsyncSession, sample_card: CreditCard
    ):
        repo = CreditCardRepository(db_session)
        prefix = sample_card.card_number[:6]
        _, total = await repo.list_by_filters(
            page=1, page_size=100, card_number_prefix=prefix
        )
        assert total >= 1

    @pytest.mark.asyncio
    async def test_list_by_filters_respects_page_size(
        self, db_session: AsyncSession, sample_account: Account, sample_customer: Customer
    ):
        """Insert 3 cards and verify page_size=2 limits results."""
        for i in range(3):
            card = CreditCard(
                card_number=f"400000000000000{i}",
                account_id=sample_account.account_id,
                customer_id=sample_customer.customer_id,
                card_embossed_name="TEST USER",
                expiration_date=date(2028, 1, 31),
                expiration_day=31,
                active_status="Y",
            )
            db_session.add(card)
        await db_session.flush()

        repo = CreditCardRepository(db_session)
        cards, _ = await repo.list_by_filters(
            page=1, page_size=2, account_id=sample_account.account_id
        )
        assert len(cards) <= 2

    @pytest.mark.asyncio
    async def test_update_persists_changes(
        self, db_session: AsyncSession, sample_card: CreditCard
    ):
        repo = CreditCardRepository(db_session)
        sample_card.card_embossed_name = "JANE DOE"
        updated = await repo.update(sample_card)
        assert updated.card_embossed_name == "JANE DOE"


# =============================================================================
# CardXrefRepository
# =============================================================================

class TestCardXrefRepository:
    @pytest.fixture
    async def sample_xref(
        self,
        db_session: AsyncSession,
        sample_account: Account,
        sample_card: CreditCard,
    ) -> CardXref:
        xref = CardXref(
            card_number=sample_card.card_number,
            account_id=sample_account.account_id,
            customer_id=sample_card.customer_id,
        )
        db_session.add(xref)
        await db_session.flush()
        return xref

    @pytest.mark.asyncio
    async def test_get_by_card_returns_xref(
        self,
        db_session: AsyncSession,
        sample_xref: CardXref,
        sample_card: CreditCard,
    ):
        repo = CardXrefRepository(db_session)
        found = await repo.get_by_card(sample_card.card_number)
        assert found is not None
        assert found.card_number == sample_card.card_number

    @pytest.mark.asyncio
    async def test_get_by_card_returns_none_when_missing(self, db_session: AsyncSession):
        repo = CardXrefRepository(db_session)
        found = await repo.get_by_card("0000000000000000")
        assert found is None

    @pytest.mark.asyncio
    async def test_get_cards_by_account_returns_all_xrefs(
        self,
        db_session: AsyncSession,
        sample_xref: CardXref,
        sample_account: Account,
    ):
        repo = CardXrefRepository(db_session)
        xrefs = await repo.get_cards_by_account(sample_account.account_id)
        assert len(xrefs) >= 1
        assert all(x.account_id == sample_account.account_id for x in xrefs)

    @pytest.mark.asyncio
    async def test_get_cards_by_account_returns_empty_list_when_no_match(
        self, db_session: AsyncSession
    ):
        repo = CardXrefRepository(db_session)
        xrefs = await repo.get_cards_by_account(999999)
        assert xrefs == []
