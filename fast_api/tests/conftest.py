"""
Pytest configuration and fixtures for CardDemo API tests.

Uses an in-process async SQLite database (via aiosqlite) for unit/integration tests
to avoid requiring a live PostgreSQL instance in CI.

Fixtures mirror CICS test data:
  - 3 accounts (from acctdata.txt)
  - 3 customers (from custdata.txt)
  - 3 cards (from carddata.txt)
  - 2 users (ADMIN + USER0001)
  - 5 transactions (from dailytran.txt)
"""
import asyncio
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.account import Account
from app.models.authorization import AuthDetail, AuthFraudRecord, AuthSummary  # noqa: F401 — registers tables with Base
from app.models.card import Card, CardXref
from app.models.customer import Customer
from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.services.auth_service import AuthService

# -------------------------------------------------------------------------
# In-memory SQLite engine for tests (no external DB required)
# -------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="session")
async def setup_db() -> AsyncGenerator[None, None]:
    """Create all tables once per test session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db(setup_db) -> AsyncGenerator[AsyncSession, None]:
    """Provide a clean database session for each test with rollback."""
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an HTTP test client with overridden DB dependency."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# -------------------------------------------------------------------------
# Test data fixtures — mirror seed_data.sql
# -------------------------------------------------------------------------

@pytest_asyncio.fixture
async def tran_type(db: AsyncSession) -> TransactionType:
    """Seed transaction type '01' = Purchase."""
    tt = TransactionType(type_cd="01", description="Purchase")
    db.add(tt)
    tt2 = TransactionType(type_cd="02", description="Payment")
    db.add(tt2)
    await db.flush()
    return tt


@pytest_asyncio.fixture
async def account(db: AsyncSession) -> Account:
    """Seed account ID=1 (from acctdata.txt row 1)."""
    acct = Account(
        acct_id=1,
        active_status="Y",
        curr_bal=194.00,
        credit_limit=2020.00,
        cash_credit_limit=1020.00,
        open_date="2014-11-20",
        expiration_date="2025-05-20",
        reissue_date="2025-05-20",
        curr_cycle_credit=0.00,
        curr_cycle_debit=0.00,
        addr_zip=None,
        group_id="A000000000",
    )
    db.add(acct)
    await db.flush()
    return acct


@pytest_asyncio.fixture
async def account2(db: AsyncSession) -> Account:
    """Seed account ID=2."""
    acct = Account(
        acct_id=2,
        active_status="Y",
        curr_bal=158.00,
        credit_limit=6130.00,
        cash_credit_limit=5448.00,
        open_date="2013-06-19",
        expiration_date="2024-08-11",
        reissue_date="2024-08-11",
        curr_cycle_credit=0.00,
        curr_cycle_debit=0.00,
        group_id="A000000000",
    )
    db.add(acct)
    await db.flush()
    return acct


@pytest_asyncio.fixture
async def customer(db: AsyncSession) -> Customer:
    """Seed customer ID=1 (Immanuel Kessler from custdata.txt)."""
    cust = Customer(
        cust_id=1,
        first_name="Immanuel",
        middle_name="Madeline",
        last_name="Kessler",
        addr_line_1="618 Deshaun Route",
        addr_line_2="Apt. 802",
        addr_line_3="Altenwerthshire",
        addr_state_cd="NC",
        addr_country_cd="USA",
        addr_zip="12546",
        phone_num_1="(908)119-8310",
        phone_num_2="(373)693-8684",
        ssn=20973888,
        dob="1961-06-08",
        pri_card_holder_ind="Y",
        fico_credit_score=300,
    )
    db.add(cust)
    await db.flush()
    return cust


@pytest_asyncio.fixture
async def card(db: AsyncSession, account: Account, customer: Customer) -> Card:
    """Seed card for account 1."""
    c = Card(
        card_num="0100000011111111",
        acct_id=1,
        cvv_cd=123,
        embossed_name="Immanuel Kessler",
        expiration_date="2025-11-01",
        active_status="Y",
    )
    db.add(c)
    xref = CardXref(card_num="0100000011111111", cust_id=1, acct_id=1)
    db.add(xref)
    await db.flush()
    return c


@pytest_asyncio.fixture
async def inactive_card(db: AsyncSession, account: Account, customer: Customer) -> Card:
    """Seed inactive card."""
    c = Card(
        card_num="9999999999999999",
        acct_id=1,
        cvv_cd=999,
        embossed_name="Test Inactive",
        expiration_date="2020-01-01",
        active_status="N",
    )
    db.add(c)
    xref = CardXref(card_num="9999999999999999", cust_id=1, acct_id=1)
    db.add(xref)
    await db.flush()
    return c


@pytest_asyncio.fixture
async def admin_user(db: AsyncSession) -> User:
    """Seed admin user — mirrors COSGN00C USRSEC record."""
    user = User(
        user_id="ADMIN",  # SEC-USR-ID PIC X(08) — normalized (stripped for SQLite compat)
        first_name="System",
        last_name="Admin",
        password_hash=AuthService.hash_password("Admin123"),
        user_type="A",  # SEC-USR-TYPE 'A' = admin (CDEMO-USRTYP-ADMIN)
    )
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def regular_user(db: AsyncSession) -> User:
    """Seed regular user."""
    user = User(
        user_id="USER0001",
        first_name="John",
        last_name="Doe",
        password_hash=AuthService.hash_password("Admin123"),
        user_type="U",
    )
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def transaction(db: AsyncSession, account: Account, card: Card, tran_type: TransactionType) -> Transaction:
    """Seed transaction for account 1."""
    txn = Transaction(
        tran_id="TEST000000000001",  # exactly 16 chars
        type_cd="01",
        cat_cd=1,
        source="POS TERM",
        description="Test purchase",
        amount=125.50,
        merchant_id=100000001,
        merchant_name="Test Store",
        merchant_city="New York",
        merchant_zip="10001",
        card_num="0100000011111111",
        acct_id=1,
        orig_ts="2022-06-11 10:00:00.000000",
        proc_ts="2022-06-11 10:00:00.000000",
    )
    db.add(txn)
    await db.flush()
    return txn


@pytest_asyncio.fixture
async def auth_summary(db: AsyncSession, account: Account) -> AuthSummary:
    """
    Seed PAUTSUM0 IMS root segment equivalent for account 1.
    Mirrors AuthSummary (CIPAUSMY.cpy fields).
    """
    from decimal import Decimal
    summary = AuthSummary(
        acct_id=1,
        cust_id=1,
        credit_limit=Decimal("2020.00"),
        cash_limit=Decimal("1020.00"),
        credit_balance=Decimal("194.00"),
        cash_balance=Decimal("0.00"),
        approved_auth_cnt=2,
        declined_auth_cnt=1,
        approved_auth_amt=Decimal("350.00"),
        declined_auth_amt=Decimal("100.00"),
    )
    db.add(summary)
    await db.flush()
    return summary


@pytest_asyncio.fixture
async def auth_detail(db: AsyncSession, auth_summary: AuthSummary, card: Card) -> AuthDetail:
    """
    Seed PAUTDTL1 IMS child segment equivalent.
    Mirrors AuthDetail (CIPAUDTY.cpy fields).
    """
    from decimal import Decimal
    detail = AuthDetail(
        acct_id=1,
        auth_date_9c=99500,  # 99999 - 00499
        auth_time_9c=999000000,  # 999999999 - 999999
        auth_orig_date="260331",
        auth_orig_time="143022",
        card_num="0100000011111111",
        auth_type="PUR ",
        card_expiry_date="1125",
        message_type="0100  ",
        message_source="POS   ",
        auth_id_code="143022",
        auth_resp_code="00",
        auth_resp_reason="0000",
        processing_code=0,
        transaction_amt=Decimal("150.00"),
        approved_amt=Decimal("150.00"),
        merchant_category_code="5411",
        acqr_country_code="840",
        pos_entry_mode=5,
        merchant_id="WALMART0001    ",
        merchant_name="WALMART SUPERCENTER   ",
        merchant_city="BENTONVILLE  ",
        merchant_state="AR",
        merchant_zip="727160001",
        transaction_id="TXN202603310001",
        match_status="P",
        auth_fraud=None,
        fraud_rpt_date=None,
    )
    db.add(detail)
    await db.flush()
    return detail


@pytest_asyncio.fixture
async def auth_token(client: AsyncClient, admin_user: User) -> str:
    """Get JWT token for admin user."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"user_id": "ADMIN", "password": "Admin123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def user_token(client: AsyncClient, regular_user: User) -> str:
    """Get JWT token for regular user."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"user_id": "USER0001", "password": "Admin123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]
