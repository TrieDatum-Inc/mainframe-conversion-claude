"""
Tests for account_repository.py and customer_repository.py.

Validates VSAM KSDS operation equivalents:
  AccountRepository.get_by_id  <- EXEC CICS READ DATASET('ACCTDAT')
  AccountRepository.update     <- EXEC CICS REWRITE DATASET('ACCTDAT')
  AccountRepository.create     <- EXEC CICS WRITE DATASET('ACCTDAT')
  AccountRepository.get_xref_by_account_id <- EXEC CICS READ DATASET('CXACAIX')
  CustomerRepository.get_by_id <- EXEC CICS READ DATASET('CUSTDAT')
"""

from decimal import Decimal

import pytest

from app.core.exceptions import ResourceNotFoundError
from app.infrastructure.orm.account_orm import AccountORM
from app.infrastructure.orm.customer_orm import CustomerORM
from app.infrastructure.repositories.account_repository import (
    AccountRepository,
    CustomerRepository,
)


class TestAccountRepository:
    @pytest.mark.asyncio
    async def test_get_by_id_returns_account(self, seeded_db):
        repo = AccountRepository(seeded_db)
        account = await repo.get_by_id(10000000001)
        assert account.acct_id == 10000000001
        assert account.active_status == "Y"
        assert account.credit_limit == Decimal("5000.00")

    @pytest.mark.asyncio
    async def test_get_by_id_raises_not_found(self, seeded_db):
        """Maps CICS RESP=NOTFND."""
        repo = AccountRepository(seeded_db)
        with pytest.raises(ResourceNotFoundError) as exc_info:
            await repo.get_by_id(99999999999)
        assert "Account" in str(exc_info.value.resource_type)

    @pytest.mark.asyncio
    async def test_get_by_id_or_none_returns_none_when_missing(self, seeded_db):
        repo = AccountRepository(seeded_db)
        result = await repo.get_by_id_or_none(99999999999)
        assert result is None

    @pytest.mark.asyncio
    async def test_update_persists_changes(self, seeded_db):
        """Maps CICS REWRITE DATASET('ACCTDAT')."""
        repo = AccountRepository(seeded_db)
        account = await repo.get_by_id(10000000001)
        account.curr_bal = Decimal("-2000.00")
        await repo.update(account)

        # Verify in same session
        updated = await repo.get_by_id(10000000001)
        assert updated.curr_bal == Decimal("-2000.00")

    @pytest.mark.asyncio
    async def test_create_stores_account(self, seeded_db):
        """Maps CICS WRITE DATASET('ACCTDAT')."""
        from datetime import date
        repo = AccountRepository(seeded_db)
        new_acct = AccountORM(
            acct_id=10000000099,
            active_status="Y",
            curr_bal=Decimal("0.00"),
            credit_limit=Decimal("2000.00"),
            cash_credit_limit=Decimal("500.00"),
            open_date=date(2024, 1, 1),
        )
        created = await repo.create(new_acct)
        assert created.acct_id == 10000000099

        fetched = await repo.get_by_id(10000000099)
        assert fetched.credit_limit == Decimal("2000.00")

    @pytest.mark.asyncio
    async def test_get_xref_by_account_id_returns_xref(self, seeded_db):
        """Maps EXEC CICS READ DATASET('CXACAIX') RIDFLD(acct_id)."""
        repo = AccountRepository(seeded_db)
        xref = await repo.get_xref_by_account_id(10000000001)
        assert xref is not None
        assert xref.card_num == "4111111111111001"
        assert xref.cust_id == 100000001
        assert xref.acct_id == 10000000001

    @pytest.mark.asyncio
    async def test_get_xref_returns_none_when_missing(self, seeded_db):
        repo = AccountRepository(seeded_db)
        xref = await repo.get_xref_by_account_id(99999999999)
        assert xref is None

    @pytest.mark.asyncio
    async def test_inactive_account_retrievable(self, seeded_db):
        """Inactive account (status='N') can still be read."""
        repo = AccountRepository(seeded_db)
        account = await repo.get_by_id(10000000003)
        assert account.active_status == "N"


class TestCustomerRepository:
    @pytest.mark.asyncio
    async def test_get_by_id_returns_customer(self, seeded_db):
        repo = CustomerRepository(seeded_db)
        customer = await repo.get_by_id(100000001)
        assert customer.cust_id == 100000001
        assert customer.first_name == "John"
        assert customer.last_name == "Doe"

    @pytest.mark.asyncio
    async def test_get_by_id_raises_not_found(self, seeded_db):
        repo = CustomerRepository(seeded_db)
        with pytest.raises(ResourceNotFoundError):
            await repo.get_by_id(999999999)

    @pytest.mark.asyncio
    async def test_get_by_id_or_none_returns_none(self, seeded_db):
        repo = CustomerRepository(seeded_db)
        result = await repo.get_by_id_or_none(999999999)
        assert result is None

    @pytest.mark.asyncio
    async def test_update_persists_customer_changes(self, seeded_db):
        repo = CustomerRepository(seeded_db)
        customer = await repo.get_by_id(100000001)
        customer.first_name = "Jonathan"
        await repo.update(customer)

        updated = await repo.get_by_id(100000001)
        assert updated.first_name == "Jonathan"

    @pytest.mark.asyncio
    async def test_customer_fico_score_at_max_boundary(self, seeded_db):
        """FICO score boundary: max is 850."""
        repo = CustomerRepository(seeded_db)
        customer = await repo.get_by_id(100000002)
        assert customer.fico_score == 850

    @pytest.mark.asyncio
    async def test_customer_fico_score_at_min_boundary(self, seeded_db):
        """FICO score boundary: min is 300."""
        repo = CustomerRepository(seeded_db)
        customer = await repo.get_by_id(100000003)
        assert customer.fico_score == 300
