"""Test configuration and shared fixtures.

Uses SQLite in-memory for unit tests (no PostgreSQL required).
For integration tests against real DB, set CARDDEMO_DATABASE_URL env var.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.account import Account
from app.models.batch_job import BatchJob, DailyReject
from app.models.card import Card
from app.models.card_cross_reference import CardCrossReference
from app.models.customer import Customer
from app.models.disclosure_group import DisclosureGroup
from app.models.transaction import Transaction
from app.models.transaction_category import TransactionCategory
from app.models.transaction_category_balance import TransactionCategoryBalance
from app.models.transaction_type import TransactionType

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create in-memory SQLite engine for each test."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine):
    """Provide a database session for each test."""
    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    """HTTP test client with database dependency override."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_account(db_session: AsyncSession) -> Account:
    """Active account within credit limit, not expired."""
    from datetime import date
    from decimal import Decimal
    account = Account(
        acct_id="00000000001",
        acct_active_status="Y",
        acct_curr_bal=Decimal("1500.00"),
        acct_credit_limit=Decimal("5000.00"),
        acct_cash_credit_limit=Decimal("1000.00"),
        acct_curr_cyc_credit=Decimal("2500.00"),
        acct_curr_cyc_debit=Decimal("1000.00"),
        acct_addr_zip="90210",
        acct_group_id="GOLD",
        acct_open_date=date(2020, 1, 15),
        acct_expiration_date=date(2027, 12, 31),
        acct_reissue_date=date(2025, 1, 15),
    )
    db_session.add(account)
    await db_session.flush()
    return account


@pytest_asyncio.fixture
async def expired_account(db_session: AsyncSession) -> Account:
    """Account with expiration date in the past."""
    from datetime import date
    from decimal import Decimal
    account = Account(
        acct_id="00000000004",
        acct_active_status="Y",
        acct_curr_bal=Decimal("500.00"),
        acct_credit_limit=Decimal("3000.00"),
        acct_cash_credit_limit=Decimal("500.00"),
        acct_curr_cyc_credit=Decimal("500.00"),
        acct_curr_cyc_debit=Decimal("0.00"),
        acct_addr_zip="33101",
        acct_group_id="GOLD",
        acct_expiration_date=date(2024, 1, 31),
    )
    db_session.add(account)
    await db_session.flush()
    return account


@pytest_asyncio.fixture
async def overlimit_account(db_session: AsyncSession) -> Account:
    """Account near credit limit."""
    from datetime import date
    from decimal import Decimal
    account = Account(
        acct_id="00000000003",
        acct_active_status="Y",
        acct_curr_bal=Decimal("2000.00"),
        acct_credit_limit=Decimal("2500.00"),
        acct_cash_credit_limit=Decimal("500.00"),
        acct_curr_cyc_credit=Decimal("2000.00"),
        acct_curr_cyc_debit=Decimal("0.00"),
        acct_addr_zip="75201",
        acct_group_id="BRONZE",
        acct_expiration_date=date(2028, 3, 31),
    )
    db_session.add(account)
    await db_session.flush()
    return account


@pytest_asyncio.fixture
async def sample_xref(db_session: AsyncSession, sample_account: Account) -> CardCrossReference:
    """Card cross-reference for sample account."""
    xref = CardCrossReference(
        xref_card_num="4111111111111111",
        xref_cust_id="000000001",
        xref_acct_id=sample_account.acct_id,
    )
    db_session.add(xref)
    await db_session.flush()
    return xref


@pytest_asyncio.fixture
async def sample_xref_expired(
    db_session: AsyncSession, expired_account: Account
) -> CardCrossReference:
    """Cross-reference for expired account."""
    xref = CardCrossReference(
        xref_card_num="4444444444444444",
        xref_cust_id="000000004",
        xref_acct_id=expired_account.acct_id,
    )
    db_session.add(xref)
    await db_session.flush()
    return xref


@pytest_asyncio.fixture
async def sample_xref_overlimit(
    db_session: AsyncSession, overlimit_account: Account
) -> CardCrossReference:
    """Cross-reference for overlimit account."""
    xref = CardCrossReference(
        xref_card_num="4333333333333333",
        xref_cust_id="000000003",
        xref_acct_id=overlimit_account.acct_id,
    )
    db_session.add(xref)
    await db_session.flush()
    return xref


@pytest_asyncio.fixture
async def sample_transaction_types(db_session: AsyncSession) -> list[TransactionType]:
    """Sample transaction type reference data."""
    types = [
        TransactionType(tran_type="01", tran_type_desc="Purchase"),
        TransactionType(tran_type="02", tran_type_desc="Refund"),
        TransactionType(tran_type="07", tran_type_desc="Payment"),
    ]
    for t in types:
        db_session.add(t)
    await db_session.flush()
    return types


@pytest_asyncio.fixture
async def sample_transaction_categories(db_session: AsyncSession) -> list[TransactionCategory]:
    """Sample transaction category reference data."""
    cats = [
        TransactionCategory(tran_type="01", tran_cat_cd="0001", tran_cat_desc="Groceries"),
        TransactionCategory(tran_type="01", tran_cat_cd="0002", tran_cat_desc="Restaurants"),
        TransactionCategory(tran_type="07", tran_cat_cd="0001", tran_cat_desc="Online Payment"),
    ]
    for c in cats:
        db_session.add(c)
    await db_session.flush()
    return cats


@pytest_asyncio.fixture
async def sample_disclosure_groups(db_session: AsyncSession) -> list[DisclosureGroup]:
    """Sample interest rate data."""
    from decimal import Decimal
    groups = [
        DisclosureGroup(group_id="GOLD", tran_type_cd="01", tran_cat_cd="0001", interest_rate=Decimal("18.00")),
        DisclosureGroup(group_id="GOLD", tran_type_cd="01", tran_cat_cd="0002", interest_rate=Decimal("18.00")),
        DisclosureGroup(group_id="DEFAULT", tran_type_cd="01", tran_cat_cd="0001", interest_rate=Decimal("24.00")),
        DisclosureGroup(group_id="DEFAULT", tran_type_cd="01", tran_cat_cd="0002", interest_rate=Decimal("24.00")),
        DisclosureGroup(group_id="DEFAULT", tran_type_cd="01", tran_cat_cd="0005", interest_rate=Decimal("0.00")),
    ]
    for g in groups:
        db_session.add(g)
    await db_session.flush()
    return groups


@pytest_asyncio.fixture
async def sample_tcatbal(
    db_session: AsyncSession, sample_account: Account
) -> TransactionCategoryBalance:
    """Sample transaction category balance."""
    from decimal import Decimal
    bal = TransactionCategoryBalance(
        acct_id=sample_account.acct_id,
        tran_type_cd="01",
        tran_cat_cd="0001",
        balance=Decimal("500.00"),
    )
    db_session.add(bal)
    await db_session.flush()
    return bal
