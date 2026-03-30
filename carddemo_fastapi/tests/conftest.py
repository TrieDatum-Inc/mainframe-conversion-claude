"""Shared pytest fixtures for the CardDemo FastAPI test suite.

Provides an in-memory SQLite database, a test HTTP client wired to
that database, JWT helper tokens for admin and regular users, and
seed data covering all domain entities.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.models import (
    Account,
    Card,
    CardXref,
    Customer,
    PendingAuthDetail,
    PendingAuthSummary,
    Transaction,
    TransactionType,
    User,
)


# ---------------------------------------------------------------------------
# Database engine & session
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def engine():
    """Create an in-memory SQLite engine for test isolation."""
    _engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return _engine


@pytest.fixture(scope="function")
def db_session(engine):
    """Create all tables, yield a session, and rollback after each test."""
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        Base.metadata.drop_all(bind=engine)


# ---------------------------------------------------------------------------
# FastAPI TestClient with overridden DB dependency
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def client(db_session):
    """Return a TestClient whose get_db dependency yields the test session."""

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# JWT tokens and Authorization headers
# ---------------------------------------------------------------------------

def _make_token(user_id: str, user_type: str) -> str:
    """Create a JWT token matching the app's auth_service logic."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=60)
    payload = {
        "user_id": user_id,
        "user_type": user_type,
        "exp": expire,
    }
    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


@pytest.fixture(scope="function")
def admin_token():
    """JWT for an admin user (admin1, type A)."""
    return _make_token("admin1", "A")


@pytest.fixture(scope="function")
def admin_headers(admin_token):
    """Authorization header dict for admin requests."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="function")
def user_token():
    """JWT for a regular user (user001, type U)."""
    return _make_token("user001", "U")


@pytest.fixture(scope="function")
def user_headers(user_token):
    """Authorization header dict for regular-user requests."""
    return {"Authorization": f"Bearer {user_token}"}


# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def seed_data(db_session):
    """Populate the test database with representative data across all tables.

    Inserts:
    - 2 customers (id=1 and 2)
    - 2 accounts  (id=10000000001 and 20000000002)
    - 3 cards
    - 3 card_xref records
    - 3 users     (admin1/A, user001/U, user002/U)
    - 2 transaction_types (01=Purchase, 02=Payment)
    - 3 transactions
    - 1 pending_auth_summary (acct=10000000001)
    - 1 pending_auth_detail
    """
    # -- Customers --
    cust1 = Customer(
        cust_id=1,
        cust_first_name="John",
        cust_middle_name="M",
        cust_last_name="Doe",
        cust_addr_line_1="123 Main St",
        cust_addr_line_2="Apt 4",
        cust_addr_line_3="",
        cust_addr_state_cd="NY",
        cust_addr_country_cd="US",
        cust_addr_zip="10001",
        cust_phone_num_1="2125551234",
        cust_phone_num_2="2125555678",
        cust_ssn=123456789,
        cust_govt_issued_id="DL123456",
        cust_dob_yyyymmdd="1985-01-15",
        cust_eft_account_id="EFT00001",
        cust_pri_card_holder_ind="Y",
        cust_fico_credit_score=750,
    )
    cust2 = Customer(
        cust_id=2,
        cust_first_name="Jane",
        cust_middle_name="A",
        cust_last_name="Smith",
        cust_addr_line_1="456 Oak Ave",
        cust_addr_line_2="",
        cust_addr_line_3="",
        cust_addr_state_cd="CA",
        cust_addr_country_cd="US",
        cust_addr_zip="90210",
        cust_phone_num_1="3105551234",
        cust_phone_num_2="",
        cust_ssn=987654321,
        cust_govt_issued_id="DL654321",
        cust_dob_yyyymmdd="1990-06-20",
        cust_eft_account_id="EFT00002",
        cust_pri_card_holder_ind="Y",
        cust_fico_credit_score=800,
    )
    db_session.add_all([cust1, cust2])

    # -- Accounts --
    acct1 = Account(
        acct_id=10000000001,
        acct_active_status="Y",
        acct_curr_bal=Decimal("1500.00"),
        acct_credit_limit=Decimal("5000.00"),
        acct_cash_credit_limit=Decimal("1000.00"),
        acct_open_date="2020-01-01",
        acct_expiration_date="2025-12-31",
        acct_reissue_date="2023-01-01",
        acct_curr_cyc_credit=Decimal("200.00"),
        acct_curr_cyc_debit=Decimal("100.00"),
        acct_addr_zip="10001",
        acct_group_id="GRP001",
    )
    acct2 = Account(
        acct_id=20000000002,
        acct_active_status="Y",
        acct_curr_bal=Decimal("3000.00"),
        acct_credit_limit=Decimal("10000.00"),
        acct_cash_credit_limit=Decimal("2000.00"),
        acct_open_date="2019-06-15",
        acct_expiration_date="2026-06-15",
        acct_reissue_date="2022-06-15",
        acct_curr_cyc_credit=Decimal("500.00"),
        acct_curr_cyc_debit=Decimal("250.00"),
        acct_addr_zip="90210",
        acct_group_id="GRP002",
    )
    db_session.add_all([acct1, acct2])

    # -- Cards --
    card1 = Card(
        card_num="4111111111111111",
        card_acct_id=10000000001,
        card_cvv_cd=123,
        card_embossed_name="JOHN M DOE",
        card_expiration_date="2025-12-01",
        card_active_status="Y",
    )
    card2 = Card(
        card_num="4222222222222222",
        card_acct_id=10000000001,
        card_cvv_cd=456,
        card_embossed_name="JOHN DOE SECONDARY",
        card_expiration_date="2025-06-01",
        card_active_status="Y",
    )
    card3 = Card(
        card_num="5333333333333333",
        card_acct_id=20000000002,
        card_cvv_cd=789,
        card_embossed_name="JANE A SMITH",
        card_expiration_date="2026-06-01",
        card_active_status="Y",
    )
    db_session.add_all([card1, card2, card3])

    # -- Card cross-references --
    xref1 = CardXref(
        xref_card_num="4111111111111111",
        xref_cust_id=1,
        xref_acct_id=10000000001,
    )
    xref2 = CardXref(
        xref_card_num="4222222222222222",
        xref_cust_id=1,
        xref_acct_id=10000000001,
    )
    xref3 = CardXref(
        xref_card_num="5333333333333333",
        xref_cust_id=2,
        xref_acct_id=20000000002,
    )
    db_session.add_all([xref1, xref2, xref3])

    # -- Users --
    usr_admin = User(
        usr_id="ADMIN1",
        usr_fname="Admin",
        usr_lname="One",
        usr_pwd="ADMIN123",
        usr_type="A",
    )
    usr1 = User(
        usr_id="USER001",
        usr_fname="Regular",
        usr_lname="User",
        usr_pwd="USER0001",
        usr_type="U",
    )
    usr2 = User(
        usr_id="USER002",
        usr_fname="Another",
        usr_lname="User",
        usr_pwd="USER0002",
        usr_type="U",
    )
    db_session.add_all([usr_admin, usr1, usr2])

    # -- Transaction types --
    tt1 = TransactionType(tran_type="01", tran_type_desc="Purchase")
    tt2 = TransactionType(tran_type="02", tran_type_desc="Payment")
    db_session.add_all([tt1, tt2])

    # -- Transactions --
    txn1 = Transaction(
        tran_id="0000000000000001",
        tran_type_cd="01",
        tran_cat_cd=1,
        tran_source="POS TERM",
        tran_desc="GROCERY PURCHASE",
        tran_amt=Decimal("50.00"),
        tran_merchant_id=100001,
        tran_merchant_name="SUPER MART",
        tran_merchant_city="NEW YORK",
        tran_merchant_zip="10001",
        tran_card_num="4111111111111111",
        tran_orig_ts="2023-10-01-10.30.00.000000",
        tran_proc_ts="2023-10-01-10.30.01.000000",
    )
    txn2 = Transaction(
        tran_id="0000000000000002",
        tran_type_cd="01",
        tran_cat_cd=1,
        tran_source="ONLINE",
        tran_desc="ELECTRONICS PURCHASE",
        tran_amt=Decimal("250.00"),
        tran_merchant_id=100002,
        tran_merchant_name="TECH STORE",
        tran_merchant_city="SAN FRANCISCO",
        tran_merchant_zip="94102",
        tran_card_num="4111111111111111",
        tran_orig_ts="2023-10-02-14.00.00.000000",
        tran_proc_ts="2023-10-02-14.00.01.000000",
    )
    txn3 = Transaction(
        tran_id="0000000000000003",
        tran_type_cd="02",
        tran_cat_cd=2,
        tran_source="POS TERM",
        tran_desc="BILL PAYMENT",
        tran_amt=Decimal("100.00"),
        tran_merchant_id=999999999,
        tran_merchant_name="BILL PAYMENT",
        tran_merchant_city="N/A",
        tran_merchant_zip="N/A",
        tran_card_num="5333333333333333",
        tran_orig_ts="2023-10-03-09.00.00.000000",
        tran_proc_ts="2023-10-03-09.00.01.000000",
    )
    db_session.add_all([txn1, txn2, txn3])

    # -- Pending authorization summary --
    pa_summary = PendingAuthSummary(
        pa_acct_id=10000000001,
        pa_cust_id=1,
        pa_auth_status="A",
        pa_account_status_1="OK",
        pa_account_status_2="OK",
        pa_account_status_3="OK",
        pa_account_status_4="OK",
        pa_account_status_5="OK",
        pa_credit_limit=Decimal("5000.00"),
        pa_cash_limit=Decimal("1000.00"),
        pa_credit_balance=Decimal("3500.00"),
        pa_cash_balance=Decimal("800.00"),
        pa_approved_auth_cnt=5,
        pa_declined_auth_cnt=1,
        pa_approved_auth_amt=Decimal("2500.00"),
        pa_declined_auth_amt=Decimal("500.00"),
    )
    db_session.add(pa_summary)

    # -- Pending authorization detail --
    pa_detail = PendingAuthDetail(
        pa_acct_id=10000000001,
        pa_auth_date="231001",
        pa_auth_time="103000",
        pa_card_num="4111111111111111",
        pa_auth_type="0100",
        pa_card_expiry_date="2025-12-01",
        pa_message_type="0100",
        pa_message_source="POS",
        pa_auth_id_code="ABC123",
        pa_auth_resp_code="00",
        pa_auth_resp_reason="APPROVED",
        pa_processing_code="003",
        pa_transaction_amt=Decimal("50.00"),
        pa_approved_amt=Decimal("50.00"),
        pa_merchant_category_code="5411",
        pa_acqr_country_code="840",
        pa_pos_entry_mode="051",
        pa_merchant_id="MID000000000001",
        pa_merchant_name="SUPER MART",
        pa_merchant_city="NEW YORK",
        pa_merchant_state="NY",
        pa_merchant_zip="10001",
        pa_transaction_id="TXN000000000001",
        pa_match_status="M",
        pa_auth_fraud="",
        pa_fraud_rpt_date="",
    )
    db_session.add(pa_detail)

    db_session.commit()

    return db_session
