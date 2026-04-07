"""
pytest fixtures for the CardDemo backend test suite.

Uses SQLite in-memory for fast tests (no external PostgreSQL required).
"""

import os

# Set required env vars before any app module is imported.
# JWT_SECRET_KEY has no default in config.py (security requirement) so tests
# must provide a deterministic test-only secret here.
os.environ.setdefault("JWT_SECRET_KEY", "carddemo-test-secret-not-for-production")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.account import Account
from app.models.account_customer_xref import AccountCustomerXref
from app.models.card_xref import CardXref
from app.models.credit_card import CreditCard
from app.models.customer import Customer
from app.models.user import User
from app.utils.security import create_access_token, hash_password

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def engine():
    """Create a test SQLite engine with the full application schema."""
    test_engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield test_engine
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest.fixture
async def db_session(engine):
    """Provide a test database session with rollback isolation."""
    TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session):
    """Async test client with database dependency override."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> User:
    user = User(
        user_id="ADMIN001",
        first_name="System",
        last_name="Admin",
        password_hash=hash_password("Admin1234"),
        user_type="A",
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def regular_user(db_session: AsyncSession) -> User:
    user = User(
        user_id="USER0001",
        first_name="Alice",
        last_name="Johnson",
        password_hash=hash_password("User1234"),
        user_type="U",
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
def admin_token(admin_user: User) -> str:
    return create_access_token(admin_user.user_id, admin_user.user_type)


@pytest.fixture
def user_token(regular_user: User) -> str:
    return create_access_token(regular_user.user_id, regular_user.user_type)


@pytest.fixture
def admin_headers(admin_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def user_headers(user_token: str) -> dict:
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
async def sample_account(db_session: AsyncSession) -> Account:
    account = Account(
        account_id=100001,
        active_status="Y",
        credit_limit=50000.00,
        cash_credit_limit=10000.00,
        current_balance=1500.00,
        curr_cycle_credit=0.00,
        curr_cycle_debit=500.00,
        group_id="A000000000",
    )
    db_session.add(account)
    await db_session.flush()
    await db_session.refresh(account)
    return account


@pytest.fixture
async def sample_customer(db_session: AsyncSession) -> Customer:
    customer = Customer(
        customer_id=200001,
        first_name="John",
        last_name="Doe",
        ssn="123-45-6789",
        fico_score=720,
        primary_card_holder="Y",
        state_code="CA",
        country_code="USA",
    )
    db_session.add(customer)
    await db_session.flush()
    await db_session.refresh(customer)
    return customer


@pytest.fixture
async def sample_account_customer_xref(
    db_session: AsyncSession,
    sample_account: Account,
    sample_customer: Customer,
) -> AccountCustomerXref:
    xref = AccountCustomerXref(
        account_id=sample_account.account_id,
        customer_id=sample_customer.customer_id,
    )
    db_session.add(xref)
    await db_session.flush()
    return xref


@pytest.fixture
async def sample_card(
    db_session: AsyncSession,
    sample_account: Account,
    sample_customer: Customer,
) -> CreditCard:
    from datetime import date
    card = CreditCard(
        card_number="4185540994448062",
        account_id=sample_account.account_id,
        customer_id=sample_customer.customer_id,
        card_embossed_name="JOHN DOE",
        expiration_date=date(2026, 12, 31),
        expiration_day=31,
        active_status="Y",
    )
    db_session.add(card)
    await db_session.flush()
    await db_session.refresh(card)
    return card
