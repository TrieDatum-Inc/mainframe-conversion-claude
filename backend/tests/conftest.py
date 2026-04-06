"""
Pytest fixtures for the CardDemo authorization test suite.
Uses in-memory SQLite for unit tests to avoid requiring a live PostgreSQL instance.
Integration tests that need PostgreSQL are marked with @pytest.mark.integration.
"""
from collections.abc import AsyncGenerator
from datetime import date, time, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.authorization import AuthFraudLog, AuthorizationDetail, AuthorizationSummary
from app.utils.security import create_access_token


# ---------------------------------------------------------------------------
# Auth tokens
# ---------------------------------------------------------------------------


@pytest.fixture
def admin_token() -> str:
    """JWT token for admin user (user_type='A')."""
    return create_access_token({"sub": "ADMIN001", "user_type": "A"})


@pytest.fixture
def user_token() -> str:
    """JWT token for regular user (user_type='U')."""
    return create_access_token({"sub": "USER0001", "user_type": "U"})


# ---------------------------------------------------------------------------
# Test data fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_summary() -> AuthorizationSummary:
    """Sample AuthorizationSummary ORM object — maps PAUTSUM0 segment."""
    summary = AuthorizationSummary()
    summary.account_id = 10000000001
    summary.credit_limit = Decimal("10000.00")
    summary.cash_limit = Decimal("2000.00")
    summary.credit_balance = Decimal("3500.00")
    summary.cash_balance = Decimal("500.00")
    summary.approved_auth_count = 12
    summary.declined_auth_count = 2
    summary.approved_auth_amount = Decimal("4200.00")
    summary.declined_auth_amount = Decimal("350.00")
    return summary


@pytest.fixture
def sample_detail() -> AuthorizationDetail:
    """
    Sample AuthorizationDetail ORM object — maps PAUTDTL1 segment.
    fraud_status='N' (initial state, no fraud flag set).
    auth_response_code='00' (approved).
    """
    detail = AuthorizationDetail()
    detail.auth_id = 1
    detail.account_id = 10000000001
    detail.transaction_id = "TXN0000000001"
    detail.card_number = "4111111111111001"
    detail.auth_date = date(2026, 3, 1)
    detail.auth_time = time(10, 25, 33)
    detail.auth_response_code = "00"
    detail.auth_code = "AUTH01"
    detail.transaction_amount = Decimal("125.50")
    detail.pos_entry_mode = "0101"
    detail.auth_source = "POS"
    detail.mcc_code = "5411"
    detail.card_expiry_date = "03/28"
    detail.auth_type = "PURCHASE"
    detail.match_status = "P"
    detail.fraud_status = "N"
    detail.merchant_name = "WHOLE FOODS MARKET"
    detail.merchant_id = "M000000001"
    detail.merchant_city = "SEATTLE"
    detail.merchant_state = "WA"
    detail.merchant_zip = "98101"
    detail.processed_at = datetime(2026, 3, 1, 10, 25, 33, tzinfo=timezone.utc)
    detail.updated_at = datetime(2026, 3, 1, 10, 25, 33, tzinfo=timezone.utc)
    return detail


@pytest.fixture
def sample_detail_fraud_confirmed(sample_detail: AuthorizationDetail) -> AuthorizationDetail:
    """Sample detail with fraud_status='F' (fraud confirmed)."""
    detail = sample_detail
    detail.fraud_status = "F"
    return detail


@pytest.fixture
def sample_detail_fraud_removed(sample_detail: AuthorizationDetail) -> AuthorizationDetail:
    """Sample detail with fraud_status='R' (fraud removed)."""
    detail = sample_detail
    detail.fraud_status = "R"
    return detail


@pytest.fixture
def sample_detail_declined(sample_detail: AuthorizationDetail) -> AuthorizationDetail:
    """Sample detail with declined authorization (auth_response_code != '00')."""
    detail = AuthorizationDetail()
    detail.auth_id = 2
    detail.account_id = 10000000001
    detail.transaction_id = "TXN0000000002"
    detail.card_number = "4111111111111001"
    detail.auth_date = date(2026, 3, 10)
    detail.auth_time = time(9, 45, 22)
    detail.auth_response_code = "4100"
    detail.auth_code = None
    detail.transaction_amount = Decimal("250.00")
    detail.pos_entry_mode = "0101"
    detail.auth_source = "POS"
    detail.mcc_code = "5411"
    detail.card_expiry_date = "03/28"
    detail.auth_type = "PURCHASE"
    detail.match_status = "D"
    detail.fraud_status = "N"
    detail.merchant_name = "WHOLE FOODS MARKET"
    detail.merchant_id = "M000000001"
    detail.merchant_city = "SEATTLE"
    detail.merchant_state = "WA"
    detail.merchant_zip = "98101"
    detail.processed_at = datetime(2026, 3, 10, 9, 45, 22, tzinfo=timezone.utc)
    detail.updated_at = datetime(2026, 3, 10, 9, 45, 22, tzinfo=timezone.utc)
    return detail


@pytest.fixture
def sample_fraud_log(sample_detail: AuthorizationDetail) -> AuthFraudLog:
    """Sample AuthFraudLog entry — maps DB2 CARDDEMO.AUTHFRDS row."""
    log = AuthFraudLog()
    log.log_id = 1
    log.auth_id = sample_detail.auth_id
    log.transaction_id = sample_detail.transaction_id
    log.card_number = sample_detail.card_number
    log.account_id = sample_detail.account_id
    log.fraud_flag = "F"
    log.fraud_report_date = datetime(2026, 3, 20, 12, 0, 0, tzinfo=timezone.utc)
    log.auth_response_code = sample_detail.auth_response_code
    log.auth_amount = sample_detail.transaction_amount
    log.merchant_name = "WHOLE FOODS MARKE"
    log.merchant_id = "M0000000"
    log.logged_at = datetime(2026, 3, 20, 12, 0, 0, tzinfo=timezone.utc)
    return log


# ---------------------------------------------------------------------------
# Mock repository fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_repo() -> MagicMock:
    """Mock AuthorizationRepository with AsyncMock methods."""
    repo = MagicMock()
    repo.get_summary_by_account = AsyncMock()
    repo.list_summaries = AsyncMock()
    repo.list_details_by_account = AsyncMock()
    repo.get_detail_by_id = AsyncMock()
    repo.update_fraud_status = AsyncMock()
    repo.insert_fraud_log = AsyncMock()
    repo.upsert_fraud_log = AsyncMock()
    repo.get_fraud_logs_for_auth = AsyncMock()
    return repo


# ---------------------------------------------------------------------------
# HTTP test client
# ---------------------------------------------------------------------------


@pytest.fixture
def client() -> TestClient:
    """Synchronous test client for FastAPI app."""
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for FastAPI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
