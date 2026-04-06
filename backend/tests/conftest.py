"""
Pytest configuration and shared fixtures for CardDemo backend tests.

Provides:
  - In-memory SQLite async session for unit/service tests
  - Pre-built admin and regular user JWT tokens
  - FastAPI TestClient with auth headers
  - Sample User ORM objects for repository tests
  - Sample TransactionType ORM objects for transaction type module tests
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.transaction_type import TransactionType
from app.models.user import User
from app.utils.security import create_access_token, hash_password

# Use in-memory SQLite for tests (schema-compatible with PostgreSQL for basic CRUD)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop_policy():
    """Use the default asyncio event loop policy."""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture
async def db_engine():
    """Create a fresh async engine for each test."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine) -> AsyncSession:
    """Provide a fresh async session for each test, rolling back after."""
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
def admin_token() -> str:
    """JWT token for an admin user (user_type='A')."""
    return create_access_token(user_id="ADMIN001", user_type="A")


@pytest.fixture
def regular_token() -> str:
    """JWT token for a regular user (user_type='U')."""
    return create_access_token(user_id="USER0001", user_type="U")


@pytest.fixture
def admin_headers(admin_token: str) -> dict:
    """Authorization headers for admin requests."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def regular_headers(regular_token: str) -> dict:
    """Authorization headers for regular user requests."""
    return {"Authorization": f"Bearer {regular_token}"}


@pytest.fixture
async def sample_admin_user(db_session: AsyncSession) -> User:
    """Persist a sample admin user and return the ORM object."""
    user = User(
        user_id="ADMIN001",
        first_name="System",
        last_name="Administrator",
        password_hash=hash_password("Admin123!"),
        user_type="A",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def sample_regular_user(db_session: AsyncSession) -> User:
    """Persist a sample regular user and return the ORM object."""
    user = User(
        user_id="USER0001",
        first_name="John",
        last_name="Smith",
        password_hash=hash_password("Test1234!"),
        user_type="U",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def multiple_users(db_session: AsyncSession) -> list[User]:
    """Persist 12 users for pagination tests (exceeds the 10-per-page limit)."""
    users = []
    for i in range(1, 13):
        user = User(
            user_id=f"USER{i:04d}",
            first_name=f"First{i}",
            last_name=f"Last{i}",
            password_hash=hash_password("Test1234!"),
            user_type="U" if i > 2 else "A",
        )
        db_session.add(user)
        users.append(user)
    await db_session.commit()
    for user in users:
        await db_session.refresh(user)
    return users


@pytest.fixture
async def client(db_session: AsyncSession, admin_headers: dict) -> AsyncClient:
    """
    FastAPI test client with admin authorization and overridden DB session.
    Uses ASGITransport for async httpx testing.
    """
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        ac.headers.update(admin_headers)
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def regular_client(db_session: AsyncSession, regular_headers: dict) -> AsyncClient:
    """FastAPI test client with regular user authorization."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        ac.headers.update(regular_headers)
        yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Transaction Type fixtures (COTRTLIC / COTRTUPC module)
# ---------------------------------------------------------------------------


@pytest.fixture
async def sample_transaction_type(db_session: AsyncSession) -> TransactionType:
    """
    Persist a single transaction type for test use.
    Maps to CARDDEMO.TRANSACTION_TYPE record with TR_TYPE='01', TR_DESCRIPTION='Purchase'.
    """
    tt = TransactionType(type_code="01", description="Purchase")
    db_session.add(tt)
    await db_session.commit()
    await db_session.refresh(tt)
    return tt


@pytest.fixture
async def multiple_transaction_types(db_session: AsyncSession) -> list[TransactionType]:
    """
    Persist 10 transaction types for pagination tests.
    Exceeds COTRTLIC WS-MAX-SCREEN-LINES=7 to verify pagination.
    """
    types = [
        TransactionType(type_code="01", description="Purchase"),
        TransactionType(type_code="02", description="Bill Payment"),
        TransactionType(type_code="03", description="Cash Advance"),
        TransactionType(type_code="04", description="Balance Transfer"),
        TransactionType(type_code="05", description="Refund"),
        TransactionType(type_code="06", description="Fee"),
        TransactionType(type_code="07", description="Interest Charge"),
        TransactionType(type_code="08", description="Reward Redemption"),
        TransactionType(type_code="09", description="Dispute Credit"),
        TransactionType(type_code="10", description="Merchant Chargeback"),
    ]
    for t in types:
        db_session.add(t)
    await db_session.commit()
    for t in types:
        await db_session.refresh(t)
    return types
