"""
pytest fixtures for the CardDemo backend test suite.

Provides:
- In-memory SQLite async engine for fast unit tests (no external DB required)
- TestClient for integration tests
- Pre-built User fixtures (admin and regular)
- Auth token fixtures for protected endpoint tests
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.transaction_type import TransactionType
from app.models.user import User
from app.utils.security import create_access_token, hash_password

# Use SQLite in-memory for tests — fast, no external dependency
# asyncpg is not used in tests to avoid PostgreSQL requirement
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop_policy():
    """Use default event loop policy for pytest-asyncio."""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture
async def engine():
    """Create a test SQLite engine with the application schema."""
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
    """Provide a test database session with transaction rollback isolation."""
    TestSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session):
    """
    Async test client with database dependency override.

    Replaces the production AsyncSession with the test session,
    ensuring tests don't touch the production database.
    """

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create and persist a test admin user."""
    user = User(
        user_id="ADMIN001",
        first_name="System",
        last_name="Administrator",
        password_hash=hash_password("Admin1234"),
        user_type="A",
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def regular_user(db_session: AsyncSession) -> User:
    """Create and persist a test regular user."""
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
    """Generate a valid JWT token for the admin user."""
    return create_access_token(
        subject=admin_user.user_id,
        user_type=admin_user.user_type,
    )


@pytest.fixture
def regular_token(regular_user: User) -> str:
    """Generate a valid JWT token for the regular user."""
    return create_access_token(
        subject=regular_user.user_id,
        user_type=regular_user.user_type,
    )


@pytest.fixture
def admin_auth_headers(admin_token: str) -> dict:
    """Authorization header dict for admin user requests."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def user_auth_headers(regular_token: str) -> dict:
    """Authorization header dict for regular user requests."""
    return {"Authorization": f"Bearer {regular_token}"}


# =============================================================================
# Transaction Type fixtures — COTRTLIC / COTRTUPC
# =============================================================================


@pytest.fixture
async def sample_transaction_type(db_session: AsyncSession) -> TransactionType:
    """
    Create and persist a single test transaction type.

    COBOL: CARDDEMO.TRANSACTION_TYPE row with TR_TYPE='01', TR_DESCRIPTION='Purchase'.
    """
    tt = TransactionType(type_code="01", description="Purchase")
    db_session.add(tt)
    await db_session.flush()
    await db_session.refresh(tt)
    return tt


@pytest.fixture
async def multiple_transaction_types(db_session: AsyncSession) -> list[TransactionType]:
    """
    Create and persist 10 transaction types for pagination / list tests.

    COBOL: Simulates the 7-row display page from COTRTLIC (WS-MAX-SCREEN-LINES=7).
    More than 7 rows ensures pagination logic is exercised.
    """
    types = [
        TransactionType(type_code=f"{i:02d}", description=f"Type {i:02d} Description")
        for i in range(1, 11)
    ]
    for tt in types:
        db_session.add(tt)
    await db_session.flush()
    for tt in types:
        await db_session.refresh(tt)
    return types
