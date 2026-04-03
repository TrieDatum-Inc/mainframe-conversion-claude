"""
Shared pytest fixtures for CardDemo Transaction Processing API tests.
Uses SQLite in-memory database to avoid requiring a running PostgreSQL instance.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models import (  # noqa: F401 — imported for metadata registration
    Account,
    CardCrossReference,
    Transaction,
    TransactionCategory,
    TransactionType,
)

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def engine():
    eng = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture(scope="function")
async def session(engine):
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        yield s


@pytest_asyncio.fixture(scope="function")
async def client(engine):
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async def override_db():
        async with factory() as s:
            yield s

    app.dependency_overrides[get_db] = override_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seed_data(session):
    """Seed minimal test data mirroring seed_data.sql structure."""
    from datetime import datetime, timezone

    session.add_all([
        TransactionType(tran_type="PU", tran_type_desc="Purchase"),
        TransactionType(tran_type="PA", tran_type_desc="Payment"),
    ])
    await session.flush()

    session.add_all([
        TransactionCategory(tran_type="PU", tran_cat_cd="0001", tran_cat_desc="Grocery"),
        TransactionCategory(tran_type="PA", tran_cat_cd="0001", tran_cat_desc="Online Payment"),
    ])
    await session.flush()

    session.add_all([
        Account(acct_id="00000000001", acct_active_status="Y"),
        Account(acct_id="00000000002", acct_active_status="N"),  # inactive
    ])
    await session.flush()

    session.add_all([
        CardCrossReference(
            xref_card_num="4111111111111111",
            xref_cust_id="000000001",
            xref_acct_id="00000000001",
        ),
        CardCrossReference(
            xref_card_num="4222222222222222",
            xref_cust_id="000000002",
            xref_acct_id="00000000002",
        ),
    ])
    await session.flush()

    ts = datetime(2026, 3, 1, 9, 0, 0, tzinfo=timezone.utc)
    transactions = [
        Transaction(
            tran_id=str(i).zfill(16),
            tran_type_cd="PU",
            tran_cat_cd="0001",
            tran_source="ONLINE",
            tran_desc=f"Test transaction {i}",
            tran_amt=-10.00 * i,
            tran_merchant_id=str(i).zfill(9),
            tran_merchant_name=f"Merchant {i}",
            tran_merchant_city="New York",
            tran_merchant_zip="10001",
            tran_card_num="4111111111111111",
            tran_orig_ts=ts,
            tran_proc_ts=ts,
        )
        for i in range(1, 26)  # 25 transactions for pagination testing
    ]
    session.add_all(transactions)
    await session.commit()
