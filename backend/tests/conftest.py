"""
pytest fixtures for the CardDemo backend test suite.

Uses an in-memory SQLite database (via aiosqlite) so tests run without
a real PostgreSQL instance. SQLite is structurally compatible for these
unit/integration tests; the Alembic migration is applied programmatically.
"""

import asyncio
import os

# Set DEBUG=True for tests so the SECRET_KEY sentinel validation is not triggered.
# Tests use a deliberately weak key; production deployments must use a real secret.
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("BLACKLIST_BACKEND", "memory")

from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from datetime import date
from decimal import Decimal

from app.database import Base, get_db
from app.main import create_app
from app.models.user import User
from app.models.account import Account
from app.models.customer import Customer
from app.models.account_customer_xref import AccountCustomerXref
from app.utils.rate_limit import limiter
from app.utils.security import hash_password, create_access_token

# Use SQLite in-memory database for tests (no PostgreSQL required)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_tables():
    """Create all tables in the test database once per test session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a test database session, rolling back after each test.

    Uses a nested transaction (savepoint) so that even if test code calls
    session.commit(), the outer transaction is rolled back and the database
    stays clean between tests.
    """
    async with test_engine.connect() as conn:
        trans = await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False)

        # Start a savepoint; session.commit() will release & re-create it
        nested = await conn.begin_nested()

        @event.listens_for(session.sync_session, "after_transaction_end")
        def reopen_nested(session_sync, transaction):
            nonlocal nested
            if not conn.closed and not conn.invalidated and nested.is_active is False:
                nested = conn.sync_connection.begin_nested()

        yield session

        await session.close()
        await trans.rollback()


@pytest_asyncio.fixture
async def seed_users(db_session: AsyncSession) -> list[User]:
    """
    Insert test users into the database.

    Mirrors the USRSEC VSAM test records:
      - ADMIN001: Admin user (SEC-USR-TYPE='A')
      - USER0001: Regular user (SEC-USR-TYPE='U')
    """
    users = [
        User(
            user_id="ADMIN001",
            first_name="John",
            last_name="Admin",
            password_hash=hash_password("Admin01!"),
            user_type="A",
        ),
        User(
            user_id="USER0001",
            first_name="Alice",
            last_name="Smith",
            password_hash=hash_password("User001!"),
            user_type="U",
        ),
    ]
    for user in users:
        db_session.add(user)
    await db_session.commit()
    return users


@pytest_asyncio.fixture
async def seed_accounts(db_session: AsyncSession):
    """
    Insert test Account, Customer, and AccountCustomerXref rows.

    Mirrors representative ACCTDAT + CUSTDAT + CXACAIX test records:
      Account 10000000001 linked to Customer 100001
    """
    account = Account(
        account_id=10000000001,
        active_status="Y",
        current_balance=Decimal("250.00"),
        credit_limit=Decimal("5000.00"),
        cash_credit_limit=Decimal("1000.00"),
        open_date=date(2020, 1, 15),
        expiration_date=date(2026, 1, 15),
        reissue_date=date(2024, 1, 15),
        curr_cycle_credit=Decimal("0.00"),
        curr_cycle_debit=Decimal("250.00"),
        zip_code="62701",
        group_id="GRP001",
    )
    customer = Customer(
        customer_id=100001,
        first_name="Alice",
        middle_name="B",
        last_name="Smith",
        street_address_1="123 Main St",
        city="Springfield",
        state_code="IL",
        zip_code="62701",
        country_code="USA",
        phone_number_1="217-555-1234",
        ssn="123-45-6789",
        date_of_birth=date(1985, 6, 15),
        fico_score=720,
        government_id_ref="DL-IL-123456",
        eft_account_id="EFT0001",
        primary_card_holder_flag="Y",
    )
    xref = AccountCustomerXref(account_id=10000000001, customer_id=100001)
    db_session.add(account)
    db_session.add(customer)
    await db_session.flush()  # ensure FKs are satisfied
    db_session.add(xref)
    await db_session.commit()
    return account, customer, xref


@pytest.fixture
def auth_token() -> str:
    """
    Generate a valid JWT access token for test authentication.

    Maps the JWT that would be issued by POST /api/v1/auth/login for ADMIN001.
    Used as Authorization: Bearer header in account endpoint tests.
    """
    return create_access_token(subject="ADMIN001", user_type="A")


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Yield an HTTPX AsyncClient wired to the FastAPI app
    with the test database session injected.
    """
    app = create_app()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Reset rate limiter state so tests don't interfere with each other
    limiter.reset()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac
