"""
Tests for transaction_repository.py.

Validates VSAM KSDS + DB2 operation equivalents:
  TransactionRepository.get_by_id           <- READ TRANSACT RIDFLD(tran_id)
  TransactionRepository.get_last_tran_id    <- STARTBR/READPREV TRANSACT
  TransactionRepository.list_paginated_forward  <- STARTBR/READNEXT
  TransactionRepository.create              <- WRITE TRANSACT
  TranCatBalRepository.get                  <- READ TRAN-CAT-BAL-FILE
  TranCatBalRepository.upsert               <- REWRITE or WRITE TRAN-CAT-BAL-FILE
  DisclosureGroupRepository.get             <- READ DISCGRP-FILE
  TransactionTypeRepository.get_by_code     <- SELECT FROM TRANSACTION_TYPE
"""

from decimal import Decimal

import pytest

from app.core.exceptions import ResourceNotFoundError
from app.infrastructure.orm.transaction_orm import TransactionORM
from app.infrastructure.repositories.transaction_repository import (
    DisclosureGroupRepository,
    TranCatBalRepository,
    TransactionRepository,
    TransactionTypeRepository,
)


class TestTransactionRepository:
    @pytest.mark.asyncio
    async def test_get_by_id_returns_transaction(self, seeded_db):
        repo = TransactionRepository(seeded_db)
        txn = await repo.get_by_id("0000000000000001")
        assert txn.tran_id == "0000000000000001"
        assert txn.tran_amt == Decimal("75.50")
        assert txn.tran_type_cd == "DB"

    @pytest.mark.asyncio
    async def test_get_by_id_raises_not_found(self, seeded_db):
        repo = TransactionRepository(seeded_db)
        with pytest.raises(ResourceNotFoundError):
            await repo.get_by_id("9999999999999999")

    @pytest.mark.asyncio
    async def test_get_last_tran_id_returns_highest_id(self, seeded_db):
        """COTRN02C: READPREV to get last tran_id for new-ID generation."""
        repo = TransactionRepository(seeded_db)
        last_id = await repo.get_last_tran_id()
        # Seed data has tran_ids ending in 0001-0004
        assert last_id == "0000000000000004"

    @pytest.mark.asyncio
    async def test_get_last_tran_id_returns_none_when_empty(self, db_session):
        """When no transactions exist, returns None."""
        repo = TransactionRepository(db_session)
        last_id = await repo.get_last_tran_id()
        assert last_id is None

    @pytest.mark.asyncio
    async def test_list_paginated_forward_returns_items(self, seeded_db):
        """STARTBR/READNEXT equivalent."""
        repo = TransactionRepository(seeded_db)
        rows, has_next = await repo.list_paginated_forward(page_size=10)
        assert len(rows) == 4  # All seed transactions
        assert has_next is False

    @pytest.mark.asyncio
    async def test_list_paginated_forward_limits_results(self, seeded_db):
        repo = TransactionRepository(seeded_db)
        rows, has_next = await repo.list_paginated_forward(page_size=2)
        assert len(rows) == 2
        assert has_next is True

    @pytest.mark.asyncio
    async def test_list_paginated_forward_filter_by_card(self, seeded_db):
        repo = TransactionRepository(seeded_db)
        rows, _ = await repo.list_paginated_forward(
            page_size=10,
            card_num_filter="4111111111111001",
        )
        # 3 transactions for card 001 in seed
        assert all(r.card_num == "4111111111111001" for r in rows)

    @pytest.mark.asyncio
    async def test_create_stores_transaction(self, seeded_db):
        """WRITE TRANSACT."""
        repo = TransactionRepository(seeded_db)
        new_txn = TransactionORM(
            tran_id="0000000000000099",
            tran_type_cd="DB",
            tran_cat_cd=1,
            tran_source="TEST",
            tran_desc="Test transaction",
            tran_amt=Decimal("99.99"),
            card_num="4111111111111001",
        )
        created = await repo.create(new_txn)
        assert created.tran_id == "0000000000000099"

        fetched = await repo.get_by_id("0000000000000099")
        assert fetched.tran_amt == Decimal("99.99")


class TestTranCatBalRepository:
    @pytest.mark.asyncio
    async def test_get_returns_balance(self, seeded_db):
        repo = TranCatBalRepository(seeded_db)
        tcb = await repo.get(10000000001, "DB", 1)
        assert tcb is not None
        assert tcb.tran_cat_bal == Decimal("500.00")

    @pytest.mark.asyncio
    async def test_get_returns_none_when_missing(self, seeded_db):
        repo = TranCatBalRepository(seeded_db)
        tcb = await repo.get(99999999999, "DB", 1)
        assert tcb is None

    @pytest.mark.asyncio
    async def test_get_all_for_account(self, seeded_db):
        repo = TranCatBalRepository(seeded_db)
        records = await repo.get_all_for_account(10000000001)
        # Account 1 has 2 tran_cat_bal records in seed
        assert len(records) == 2

    @pytest.mark.asyncio
    async def test_upsert_creates_new_record(self, seeded_db):
        """WRITE TRAN-CAT-BAL-FILE when record doesn't exist."""
        from app.infrastructure.orm.transaction_orm import TranCatBalORM
        repo = TranCatBalRepository(seeded_db)
        new_tcb = TranCatBalORM(
            acct_id=10000000001,
            tran_type_cd="IN",
            tran_cat_cd=1,
            tran_cat_bal=Decimal("25.00"),
        )
        await repo.upsert(new_tcb)
        fetched = await repo.get(10000000001, "IN", 1)
        assert fetched is not None
        assert fetched.tran_cat_bal == Decimal("25.00")

    @pytest.mark.asyncio
    async def test_get_all_sequential_returns_all_records(self, seeded_db):
        """CBACT04C reads TCATBAL-FILE sequentially."""
        repo = TranCatBalRepository(seeded_db)
        all_records = await repo.get_all_sequential()
        assert len(all_records) == 3  # seed has 3 records


class TestDisclosureGroupRepository:
    @pytest.mark.asyncio
    async def test_get_returns_interest_rate(self, seeded_db):
        """READ DISCGRP-FILE by composite key."""
        repo = DisclosureGroupRepository(seeded_db)
        dg = await repo.get("GRP001", "DB", 1)
        assert dg is not None
        assert dg.int_rate == Decimal("18.99")

    @pytest.mark.asyncio
    async def test_get_returns_none_when_missing(self, seeded_db):
        repo = DisclosureGroupRepository(seeded_db)
        dg = await repo.get("NONEXIST", "DB", 1)
        assert dg is None

    @pytest.mark.asyncio
    async def test_different_groups_have_different_rates(self, seeded_db):
        repo = DisclosureGroupRepository(seeded_db)
        grp1 = await repo.get("GRP001", "DB", 9)
        grp2 = await repo.get("GRP002", "DB", 1)
        assert grp1.int_rate == Decimal("24.99")
        assert grp2.int_rate == Decimal("29.99")


class TestTransactionTypeRepository:
    @pytest.mark.asyncio
    async def test_get_by_code_returns_type(self, seeded_db):
        repo = TransactionTypeRepository(seeded_db)
        tt = await repo.get_by_code("DB")
        assert tt.tran_type_cd == "DB"
        assert tt.tran_type_desc == "Debit - Purchase"

    @pytest.mark.asyncio
    async def test_get_by_code_raises_not_found(self, seeded_db):
        repo = TransactionTypeRepository(seeded_db)
        with pytest.raises(ResourceNotFoundError):
            await repo.get_by_code("ZZ")

    @pytest.mark.asyncio
    async def test_list_paginated_returns_types(self, seeded_db):
        repo = TransactionTypeRepository(seeded_db)
        items, has_next = await repo.list_paginated(page_size=10)
        assert len(items) == 5  # 5 seed transaction types

    @pytest.mark.asyncio
    async def test_list_paginated_respects_page_size(self, seeded_db):
        repo = TransactionTypeRepository(seeded_db)
        items, has_next = await repo.list_paginated(page_size=2)
        assert len(items) == 2
        assert has_next is True

    @pytest.mark.asyncio
    async def test_create_new_type(self, seeded_db):
        from app.infrastructure.orm.transaction_orm import TransactionTypeORM
        repo = TransactionTypeRepository(seeded_db)
        new_type = TransactionTypeORM(tran_type_cd="TS", tran_type_desc="Test Type")
        created = await repo.create(new_type)
        assert created.tran_type_cd == "TS"

        fetched = await repo.get_by_code("TS")
        assert fetched.tran_type_desc == "Test Type"

    @pytest.mark.asyncio
    async def test_delete_type(self, seeded_db):
        repo = TransactionTypeRepository(seeded_db)
        # Create a disposable type first
        from app.infrastructure.orm.transaction_orm import TransactionTypeORM
        new_type = TransactionTypeORM(tran_type_cd="TD", tran_type_desc="Delete Me")
        await repo.create(new_type)

        await repo.delete("TD")

        with pytest.raises(ResourceNotFoundError):
            await repo.get_by_code("TD")
