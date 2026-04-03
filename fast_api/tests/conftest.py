"""Test configuration and fixtures using SQLite in-memory database."""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.database import Base, get_db
from app.main import app
from app.models.account import Account
from app.models.card import Card

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def engine():
    _engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield _engine
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(engine):
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def create_account(session: AsyncSession, acct_id: str = "00000000001") -> Account:
    account = Account(acct_id=acct_id, acct_active_status="Y", acct_curr_bal=1000.00, acct_credit_limit=5000.00, acct_cash_credit_limit=1000.00)
    session.add(account)
    await session.flush()
    return account


async def create_card(session: AsyncSession, card_num: str = "4111111111110001", acct_id: str = "00000000001", cvv: str = "123", name: str = "ALICE JOHNSON", status: str = "Y", exp_date=None) -> Card:
    from datetime import date
    card = Card(card_num=card_num, card_acct_id=acct_id, card_cvv_cd=cvv, card_embossed_name=name, card_expiration_date=exp_date or date(2026, 3, 15), card_active_status=status)
    session.add(card)
    await session.flush()
    return card
