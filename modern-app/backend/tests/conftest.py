"""pytest fixtures shared across all test modules."""
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.user import User

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def engine():
    """Create an in-memory SQLite engine for the test session."""
    _engine = create_async_engine(TEST_DB_URL, echo=False)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield _engine
    await _engine.dispose()


@pytest.fixture
async def db_session(engine):
    """Provide a clean transactional session per test (rolled back after)."""
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession):
    """AsyncClient with database dependency overridden to the test session."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Seed an admin user for auth-bypass tests."""
    import bcrypt

    user = User(
        user_id="ADMIN001",
        first_name="Admin",
        last_name="User",
        password_hash=bcrypt.hashpw(b"secret", bcrypt.gensalt()).decode(),
        user_type="A",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def regular_user(db_session: AsyncSession) -> User:
    """Seed a regular (non-admin) user."""
    import bcrypt

    user = User(
        user_id="USER0001",
        first_name="Regular",
        last_name="User",
        password_hash=bcrypt.hashpw(b"secret", bcrypt.gensalt()).decode(),
        user_type="U",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


def make_admin_token(user_id: str = "ADMIN001") -> str:
    """Generate a valid admin JWT for use in test Authorization headers."""
    import jwt

    from app.config import settings

    return jwt.encode(
        {"sub": user_id, "user_type": "A"},
        settings.secret_key,
        algorithm=settings.algorithm,
    )
