"""
Test fixtures for authorization module tests.

Uses SQLite in-memory for unit/service tests to avoid requiring PostgreSQL.
"""

from datetime import date, time
from decimal import Decimal
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.models.authorization import AuthorizationDetail, AuthorizationSummary
from app.models.fraud import FraudRecord


@pytest.fixture
def sample_summary() -> AuthorizationSummary:
    """Fixture: active account summary with room for more credit."""
    return AuthorizationSummary(
        id=1,
        account_id="00000000001",
        customer_id="000000001",
        auth_status="A",
        credit_limit=Decimal("10000.00"),
        cash_limit=Decimal("1000.00"),
        credit_balance=Decimal("3000.00"),
        cash_balance=Decimal("300.00"),
        approved_count=5,
        declined_count=1,
        approved_amount=Decimal("4500.00"),
        declined_amount=Decimal("200.00"),
    )


@pytest.fixture
def closed_summary() -> AuthorizationSummary:
    """Fixture: closed account summary."""
    return AuthorizationSummary(
        id=2,
        account_id="00000000004",
        customer_id="000000004",
        auth_status="C",
        credit_limit=Decimal("10000.00"),
        cash_limit=Decimal("1000.00"),
        credit_balance=Decimal("9500.00"),
        cash_balance=Decimal("800.00"),
        approved_count=3,
        declined_count=4,
        approved_amount=Decimal("7500.00"),
        declined_amount=Decimal("6000.00"),
    )


@pytest.fixture
def maxed_summary() -> AuthorizationSummary:
    """Fixture: account at credit limit."""
    return AuthorizationSummary(
        id=3,
        account_id="00000000002",
        customer_id="000000002",
        auth_status="A",
        credit_limit=Decimal("5000.00"),
        cash_limit=Decimal("500.00"),
        credit_balance=Decimal("5000.00"),
        cash_balance=Decimal("500.00"),
        approved_count=10,
        declined_count=2,
        approved_amount=Decimal("5000.00"),
        declined_amount=Decimal("1000.00"),
    )


@pytest.fixture
def sample_detail(sample_summary: AuthorizationSummary) -> AuthorizationDetail:
    """Fixture: a matched authorization detail."""
    return AuthorizationDetail(
        id=1,
        summary_id=1,
        card_number="4111111111111111",
        auth_date=date(2026, 4, 1),
        auth_time=time(10, 23, 45),
        auth_type="SALE",
        card_expiry="12/28",
        message_type="0110",
        auth_response_code="00",
        auth_response_reason="APPROVED",
        auth_code="AUTH01",
        transaction_amount=Decimal("250.00"),
        approved_amount=Decimal("250.00"),
        pos_entry_mode="0101",
        auth_source="TERMINAL",
        mcc_code="5411",
        merchant_name="WHOLE FOODS MARKET",
        merchant_id="WHOL001234567",
        merchant_city="AUSTIN",
        merchant_state="TX",
        merchant_zip="78701",
        transaction_id="TXN000000000001",
        match_status="M",
        fraud_status=None,
        processing_code="000000",
    )


@pytest.fixture
def fraud_detail(sample_summary: AuthorizationSummary) -> AuthorizationDetail:
    """Fixture: a fraud-flagged authorization detail."""
    return AuthorizationDetail(
        id=8,
        summary_id=1,
        card_number="4111111111111111",
        auth_date=date(2026, 4, 4),
        auth_time=time(12, 0, 0),
        auth_type="SALE",
        card_expiry="12/28",
        message_type="0110",
        auth_response_code="51",
        auth_response_reason="CARD FRAUD",
        auth_code="",
        transaction_amount=Decimal("999.00"),
        approved_amount=Decimal("0.00"),
        pos_entry_mode="0101",
        auth_source="TERMINAL",
        mcc_code="5944",
        merchant_name="GOLD MERCHANTS",
        merchant_id="GOLD00000001",
        merchant_city="DALLAS",
        merchant_state="TX",
        merchant_zip="75201",
        transaction_id="TXN000000000008",
        match_status="D",
        fraud_status="F",
        processing_code="000000",
    )
