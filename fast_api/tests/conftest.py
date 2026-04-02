"""
Test configuration and fixtures for CardDemo FastAPI tests.

Uses an in-memory SQLite database for unit/integration tests.
Mirrors the seed data structure from 002_seed_data.sql.
"""

import asyncio
from datetime import date, time
from decimal import Decimal
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.domain.services.auth_service import hash_password
from app.infrastructure.database import Base, get_db
from app.infrastructure.orm.account_orm import AccountORM
from app.infrastructure.orm.authorization_orm import AuthDetailORM, AuthSummaryORM
from app.infrastructure.orm.card_orm import CardORM, CardXrefORM
from app.infrastructure.orm.customer_orm import CustomerORM
from app.infrastructure.orm.transaction_orm import (
    DisclosureGroupORM,
    TranCatBalORM,
    TransactionCategoryORM,
    TransactionORM,
    TransactionTypeORM,
)
from app.infrastructure.orm.user_orm import UserORM
from app.main import app

# SQLite in-memory async engine for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def engine():
    """Create async engine for tests using SQLite in-memory."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def session_factory(engine):
    """Session factory scoped to test session."""
    factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    return factory


@pytest_asyncio.fixture
async def db_session(session_factory) -> AsyncGenerator[AsyncSession, None]:
    """Per-test async session with automatic rollback."""
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def seeded_db(db_session: AsyncSession) -> AsyncSession:
    """
    Database session pre-populated with test data.
    Mirrors structure of 002_seed_data.sql.
    """
    # ----- Transaction types -----
    tran_types = [
        TransactionTypeORM(tran_type_cd="PR", tran_type_desc="Payment Received"),
        TransactionTypeORM(tran_type_cd="DB", tran_type_desc="Debit - Purchase"),
        TransactionTypeORM(tran_type_cd="CR", tran_type_desc="Credit - Refund"),
        TransactionTypeORM(tran_type_cd="FS", tran_type_desc="Fee - Service"),
        TransactionTypeORM(tran_type_cd="IN", tran_type_desc="Interest Charge"),
    ]
    for t in tran_types:
        db_session.add(t)

    # ----- Transaction categories -----
    tran_cats = [
        TransactionCategoryORM(tran_type_cd="DB", tran_cat_cd=1, tran_cat_desc="Groceries"),
        TransactionCategoryORM(tran_type_cd="DB", tran_cat_cd=2, tran_cat_desc="Gas/Auto"),
        TransactionCategoryORM(tran_type_cd="DB", tran_cat_cd=9, tran_cat_desc="Miscellaneous Purchase"),
        TransactionCategoryORM(tran_type_cd="CR", tran_cat_cd=1, tran_cat_desc="General Refund"),
        TransactionCategoryORM(tran_type_cd="PR", tran_cat_cd=9999, tran_cat_desc="Bill Payment"),
        TransactionCategoryORM(tran_type_cd="IN", tran_cat_cd=1, tran_cat_desc="Purchase Interest"),
        TransactionCategoryORM(tran_type_cd="FS", tran_cat_cd=1, tran_cat_desc="Late Payment Fee"),
    ]
    for c in tran_cats:
        db_session.add(c)

    # ----- Users -----
    users = [
        UserORM(
            usr_id="SYSADM00",
            first_name="System",
            last_name="Admin",
            pwd_hash=hash_password("Admin123"),
            usr_type="A",
        ),
        UserORM(
            usr_id="USER0001",
            first_name="Alice",
            last_name="Smith",
            pwd_hash=hash_password("Pass1234"),
            usr_type="U",
        ),
        UserORM(
            usr_id="USER0002",
            first_name="Bob",
            last_name="Jones",
            pwd_hash=hash_password("Pass5678"),
            usr_type="U",
        ),
    ]
    for u in users:
        db_session.add(u)

    # ----- Customers -----
    customers = [
        CustomerORM(
            cust_id=100000001,
            first_name="John",
            middle_name="A",
            last_name="Doe",
            addr_line1="123 Main St",
            addr_line2="Apt 4B",
            addr_line3="Springfield",
            addr_state_cd="IL",
            addr_country_cd="USA",
            addr_zip="62701",
            phone_num1="(217)555-1234",
            phone_num2=None,
            ssn=123456789,
            dob=date(1985, 6, 15),
            fico_score=720,
            pri_card_holder="Y",
        ),
        CustomerORM(
            cust_id=100000002,
            first_name="Jane",
            middle_name=None,
            last_name="Smith",
            addr_line1="456 Oak Ave",
            addr_line2=None,
            addr_line3="Shelbyville",
            addr_state_cd="TX",
            addr_country_cd="USA",
            addr_zip="75001",
            phone_num1="(214)555-9876",
            phone_num2=None,
            ssn=234567890,
            dob=date(1990, 3, 22),
            fico_score=850,  # max FICO
            pri_card_holder="Y",
        ),
        CustomerORM(
            cust_id=100000003,
            first_name="Bob",
            middle_name=None,
            last_name="Johnson",
            addr_line1="789 Elm St",
            addr_line2=None,
            addr_line3="Capital City",
            addr_state_cd="CA",
            addr_country_cd="USA",
            addr_zip="90001",
            phone_num1="(310)555-4444",
            phone_num2=None,
            ssn=345678901,
            dob=date(1975, 11, 30),
            fico_score=300,  # min FICO
            pri_card_holder="Y",
        ),
    ]
    for c in customers:
        db_session.add(c)

    # ----- Accounts -----
    accounts = [
        AccountORM(
            acct_id=10000000001,
            active_status="Y",
            curr_bal=Decimal("-1500.00"),
            credit_limit=Decimal("5000.00"),
            cash_credit_limit=Decimal("2000.00"),
            open_date=date(2020, 1, 1),
            expiration_date=date(2025, 12, 31),
            reissue_date=None,
            curr_cycle_credit=Decimal("0.00"),
            curr_cycle_debit=Decimal("1500.00"),
            addr_zip="62701",
            group_id="GRP001",
        ),
        AccountORM(
            acct_id=10000000002,
            active_status="Y",
            curr_bal=Decimal("0.00"),
            credit_limit=Decimal("10000.00"),
            cash_credit_limit=Decimal("3000.00"),
            open_date=date(2019, 6, 15),
            expiration_date=date(2026, 6, 30),
            reissue_date=None,
            curr_cycle_credit=Decimal("500.00"),
            curr_cycle_debit=Decimal("200.00"),
            addr_zip="75001",
            group_id="GRP001",
        ),
        AccountORM(
            acct_id=10000000003,
            active_status="N",  # Inactive account
            curr_bal=Decimal("-200.00"),
            credit_limit=Decimal("1000.00"),
            cash_credit_limit=Decimal("500.00"),
            open_date=date(2018, 3, 10),
            expiration_date=date(2023, 3, 31),
            reissue_date=None,
            curr_cycle_credit=Decimal("0.00"),
            curr_cycle_debit=Decimal("200.00"),
            addr_zip="90001",
            group_id="GRP002",
        ),
    ]
    for a in accounts:
        db_session.add(a)

    # ----- Cards -----
    cards = [
        CardORM(
            card_num="4111111111111001",
            acct_id=10000000001,
            cvv_cd=123,
            embossed_name="JOHN A DOE",
            expiration_date=date(2025, 12, 31),
            active_status="Y",
        ),
        CardORM(
            card_num="4111111111111002",
            acct_id=10000000002,
            cvv_cd=456,
            embossed_name="JANE SMITH",
            expiration_date=date(2026, 6, 30),
            active_status="Y",
        ),
        CardORM(
            card_num="4111111111111003",
            acct_id=10000000003,
            cvv_cd=789,
            embossed_name="BOB JOHNSON",
            expiration_date=date(2023, 3, 31),
            active_status="N",
        ),
    ]
    for c in cards:
        db_session.add(c)

    # ----- Card Xref (CXACAIX) -----
    xrefs = [
        CardXrefORM(card_num="4111111111111001", cust_id=100000001, acct_id=10000000001),
        CardXrefORM(card_num="4111111111111002", cust_id=100000002, acct_id=10000000002),
        CardXrefORM(card_num="4111111111111003", cust_id=100000003, acct_id=10000000003),
    ]
    for x in xrefs:
        db_session.add(x)

    # ----- Transactions -----
    transactions = [
        TransactionORM(
            tran_id="0000000000000001",
            tran_type_cd="DB",
            tran_cat_cd=1,
            tran_source="ONLINE",
            tran_desc="Grocery store purchase",
            tran_amt=Decimal("75.50"),
            merchant_id=9001,
            merchant_name="WHOLE FOODS",
            merchant_city="Springfield",
            merchant_zip="62701",
            card_num="4111111111111001",
        ),
        TransactionORM(
            tran_id="0000000000000002",
            tran_type_cd="DB",
            tran_cat_cd=2,
            tran_source="POS",
            tran_desc="Gas station",
            tran_amt=Decimal("45.00"),
            merchant_id=9002,
            merchant_name="SHELL GAS",
            merchant_city="Springfield",
            merchant_zip="62702",
            card_num="4111111111111001",
        ),
        TransactionORM(
            tran_id="0000000000000003",
            tran_type_cd="PR",
            tran_cat_cd=9999,
            tran_source="ONLINE",
            tran_desc="Bill payment",
            tran_amt=Decimal("-100.00"),
            card_num="4111111111111001",
        ),
        TransactionORM(
            tran_id="0000000000000004",
            tran_type_cd="DB",
            tran_cat_cd=9,
            tran_source="ONLINE",
            tran_desc="Online purchase",
            tran_amt=Decimal("250.00"),
            merchant_id=9003,
            merchant_name="AMAZON",
            merchant_city="SEATTLE",
            merchant_zip="98101",
            card_num="4111111111111002",
        ),
    ]
    for t in transactions:
        db_session.add(t)

    # ----- Tran Cat Bal -----
    tran_cat_bals = [
        TranCatBalORM(
            acct_id=10000000001,
            tran_type_cd="DB",
            tran_cat_cd=1,
            tran_cat_bal=Decimal("500.00"),
        ),
        TranCatBalORM(
            acct_id=10000000001,
            tran_type_cd="DB",
            tran_cat_cd=2,
            tran_cat_bal=Decimal("200.00"),
        ),
        TranCatBalORM(
            acct_id=10000000002,
            tran_type_cd="DB",
            tran_cat_cd=9,
            tran_cat_bal=Decimal("750.00"),
        ),
    ]
    for b in tran_cat_bals:
        db_session.add(b)

    # ----- Disclosure Groups (interest rates) -----
    disc_groups = [
        DisclosureGroupORM(acct_group_id="GRP001", tran_type_cd="DB", tran_cat_cd=1, int_rate=Decimal("18.99")),
        DisclosureGroupORM(acct_group_id="GRP001", tran_type_cd="DB", tran_cat_cd=2, int_rate=Decimal("18.99")),
        DisclosureGroupORM(acct_group_id="GRP001", tran_type_cd="DB", tran_cat_cd=9, int_rate=Decimal("24.99")),
        DisclosureGroupORM(acct_group_id="GRP002", tran_type_cd="DB", tran_cat_cd=1, int_rate=Decimal("29.99")),
    ]
    for d in disc_groups:
        db_session.add(d)

    # ----- Auth Summary -----
    auth_summaries = [
        AuthSummaryORM(
            acct_id=10000000001,
            cust_id=100000001,
            auth_status="A",
            credit_limit=Decimal("5000.00"),
            cash_limit=Decimal("2000.00"),
            curr_bal=Decimal("-1500.00"),
            cash_bal=Decimal("0.00"),
            approved_count=2,
            approved_amt=Decimal("800.00"),
            declined_count=1,
            declined_amt=Decimal("200.00"),
        ),
        AuthSummaryORM(
            acct_id=10000000002,
            cust_id=100000002,
            auth_status="A",
            credit_limit=Decimal("10000.00"),
            cash_limit=Decimal("3000.00"),
            curr_bal=Decimal("0.00"),
            cash_bal=Decimal("0.00"),
            approved_count=0,
            approved_amt=Decimal("0.00"),
            declined_count=0,
            declined_amt=Decimal("0.00"),
        ),
    ]
    for s in auth_summaries:
        db_session.add(s)

    # ----- Auth Detail -----
    auth_details = [
        AuthDetailORM(
            auth_date=date(2024, 1, 15),
            auth_time=time(10, 30, 0),
            acct_id=10000000001,
            card_num="4111111111111001",
            tran_id="0000000000000001",
            auth_id_code="AUTH001",
            response_code="00",
            response_reason="Approved",
            approved_amt=Decimal("75.50"),
            auth_type="P",
            match_status="N",
            fraud_flag="N",
        ),
        AuthDetailORM(
            auth_date=date(2024, 1, 16),
            auth_time=time(14, 45, 0),
            acct_id=10000000001,
            card_num="4111111111111001",
            tran_id="0000000000000002",
            auth_id_code="AUTH002",
            response_code="51",
            response_reason="Insufficient funds",
            approved_amt=Decimal("0.00"),
            auth_type="P",
            match_status="N",
            fraud_flag="N",
        ),
    ]
    for d in auth_details:
        db_session.add(d)

    await db_session.flush()
    return db_session


# --------------------------------------------------------------------------
# HTTP client fixtures for route integration tests
# --------------------------------------------------------------------------


@pytest_asyncio.fixture
async def async_client(seeded_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP client with overridden DB dependency pointing to seeded test DB.

    The lifespan in main.py checks PostgreSQL connectivity; we replace it
    with a no-op so tests run without a real PostgreSQL server.
    """
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def _noop_lifespan(_app):
        """No-op lifespan: skip the DB connectivity check for tests."""
        yield

    async def override_get_db():
        yield seeded_db

    app.dependency_overrides[get_db] = override_get_db

    # Temporarily replace lifespan to prevent DB connection attempt
    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = _noop_lifespan

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            yield client
    finally:
        app.router.lifespan_context = original_lifespan
        app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_token(async_client: AsyncClient) -> str:
    """JWT token for admin user SYSADM00."""
    resp = await async_client.post(
        "/auth/login", json={"user_id": "SYSADM00", "password": "Admin123"}
    )
    assert resp.status_code == 200, f"Admin login failed: {resp.text}"
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def user_token(async_client: AsyncClient) -> str:
    """JWT token for regular user USER0001."""
    resp = await async_client.post(
        "/auth/login", json={"user_id": "USER0001", "password": "Pass1234"}
    )
    assert resp.status_code == 200, f"User login failed: {resp.text}"
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def admin_headers(admin_token) -> dict:
    """Authorization headers for admin user."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest_asyncio.fixture
async def user_headers(user_token) -> dict:
    """Authorization headers for regular user."""
    return {"Authorization": f"Bearer {user_token}"}
