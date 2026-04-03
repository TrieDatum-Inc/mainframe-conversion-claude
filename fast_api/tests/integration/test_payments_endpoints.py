"""Integration tests for bill payment endpoints — COBIL00C (CB00) equivalent.

Uses httpx.AsyncClient with the FastAPI app directly.
DB calls are mocked via dependency overrides and repository patching.

Tests cover the two-phase payment flow:
  Phase 1: GET /payments/balance/{acct_id} — account lookup
  Phase 2: POST /payments/{acct_id} — payment processing (CONFIRM=Y)
"""
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.main import app
from app.middleware.auth_middleware import get_current_user_info
from app.models.account import Account
from app.models.card_cross_reference import CardCrossReference
from app.models.transaction import Transaction
from app.repositories.account_repository import AccountRepository
from app.repositories.card_cross_reference_repository import CardCrossReferenceRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.auth import UserInfo


def _make_valid_user() -> UserInfo:
    return UserInfo(
        user_id="USER0001",
        first_name="John",
        last_name="Doe",
        user_type="U",
    )


def _mock_auth_dependency():
    async def override():
        return _make_valid_user()
    return override


def _make_account(
    acct_id: int = 10000000001,
    curr_bal: Decimal = Decimal("1250.75"),
    active_status: str = "Y",
) -> Account:
    return Account(
        acct_id=acct_id,
        active_status=active_status,
        curr_bal=curr_bal,
        credit_limit=Decimal("10000.00"),
        cash_credit_limit=Decimal("2000.00"),
        curr_cycle_credit=Decimal("0.00"),
        curr_cycle_debit=curr_bal,
    )


def _make_xref(
    card_num: str = "4111111111111001",
    acct_id: int = 10000000001,
) -> CardCrossReference:
    return CardCrossReference(
        card_num=card_num,
        acct_id=acct_id,
        cust_id=100000001,
    )


def _make_transaction(
    tran_id: str = "0000000000000006",
    amount: Decimal = Decimal("1250.75"),
) -> Transaction:
    return Transaction(
        tran_id=tran_id,
        tran_type_cd="02",
        tran_cat_cd=2,
        source="POS TERM",
        description="BILL PAYMENT - ONLINE",
        amount=amount,
        card_num="4111111111111001",
        orig_timestamp=datetime.now(tz=timezone.utc),
        proc_timestamp=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
async def client():
    """AsyncClient with auth dependency bypassed."""
    app.dependency_overrides[get_current_user_info] = _mock_auth_dependency()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
    app.dependency_overrides.clear()


# ============================================================
# GET /payments/balance/{acct_id} — Phase 1: balance lookup
# ============================================================

class TestGetBalanceEndpoint:
    """Integration tests for Phase 1 balance lookup."""

    async def test_get_balance_existing_account_returns_200(self, client: AsyncClient):
        """Phase 1: Returns 200 with balance for existing account."""
        account = _make_account(curr_bal=Decimal("1250.75"))

        with patch.object(AccountRepository, "get_by_id", return_value=account):
            app.dependency_overrides[get_db] = lambda: MagicMock()
            response = await client.get("/payments/balance/10000000001")
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 200
        data = response.json()
        assert data["acct_id"] == "10000000001"
        assert float(data["curr_bal"]) == pytest.approx(1250.75)

    async def test_get_balance_account_not_found_returns_404(self, client: AsyncClient):
        """Phase 1: Returns 404 when account not found."""
        with patch.object(AccountRepository, "get_by_id", return_value=None):
            app.dependency_overrides[get_db] = lambda: MagicMock()
            response = await client.get("/payments/balance/99999999999")
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 404
        data = response.json()
        assert "NOT found" in data["detail"]

    async def test_get_balance_zero_balance_shows_info_message(self, client: AsyncClient):
        """BR-003: Zero balance returns info message, not error (still 200)."""
        account = _make_account(curr_bal=Decimal("0.00"))

        with patch.object(AccountRepository, "get_by_id", return_value=account):
            app.dependency_overrides[get_db] = lambda: MagicMock()
            response = await client.get("/payments/balance/10000000004")
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 200
        data = response.json()
        assert float(data["curr_bal"]) == 0.0
        assert data["message"] is not None
        assert data["message_type"] == "info"

    async def test_get_balance_positive_balance_no_message(self, client: AsyncClient):
        """Positive balance has no warning message."""
        account = _make_account(curr_bal=Decimal("500.00"))

        with patch.object(AccountRepository, "get_by_id", return_value=account):
            app.dependency_overrides[get_db] = lambda: MagicMock()
            response = await client.get("/payments/balance/10000000001")
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 200
        data = response.json()
        assert data["message"] is None

    async def test_get_balance_unauthenticated_returns_401(self):
        """Unauthenticated request returns 401."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as c:
            response = await c.get("/payments/balance/10000000001")
        assert response.status_code == 401


# ============================================================
# POST /payments/{acct_id} — Phase 2: payment processing
# ============================================================

class TestProcessPaymentEndpoint:
    """Integration tests for Phase 2 payment processing (CONFIRM=Y)."""

    async def test_successful_payment_returns_201(self, client: AsyncClient):
        """Phase 2: Full payment returns 201 with transaction ID and zero balance."""
        account = _make_account(curr_bal=Decimal("1250.75"))
        xref = _make_xref()
        tran = _make_transaction("0000000000000006", amount=Decimal("1250.75"))
        zeroed_account = _make_account(curr_bal=Decimal("0.00"))

        with (
            patch.object(AccountRepository, "get_by_id", return_value=account),
            patch.object(CardCrossReferenceRepository, "get_by_acct_id", return_value=xref),
            patch.object(TransactionRepository, "generate_next_tran_id", return_value="0000000000000006"),
            patch.object(TransactionRepository, "create", return_value=tran),
            patch.object(AccountRepository, "zero_balance", return_value=zeroed_account),
        ):
            app.dependency_overrides[get_db] = lambda: MagicMock()
            response = await client.post("/payments/10000000001")
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 201
        data = response.json()
        assert data["tran_id"] == "0000000000000006"
        assert float(data["payment_amount"]) == pytest.approx(1250.75)
        assert float(data["new_balance"]) == 0.0
        assert data["message_type"] == "success"
        assert "Payment successful" in data["message"]
        assert "0000000000000006" in data["message"]

    async def test_payment_account_not_found_returns_404(self, client: AsyncClient):
        """Returns 404 when account not found."""
        with patch.object(AccountRepository, "get_by_id", return_value=None):
            app.dependency_overrides[get_db] = lambda: MagicMock()
            response = await client.post("/payments/99999999999")
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 404

    async def test_payment_zero_balance_returns_422(self, client: AsyncClient):
        """BR-003: Returns 422 when account has zero balance."""
        account = _make_account(curr_bal=Decimal("0.00"))

        with patch.object(AccountRepository, "get_by_id", return_value=account):
            app.dependency_overrides[get_db] = lambda: MagicMock()
            response = await client.post("/payments/10000000004")
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 422
        data = response.json()
        assert "nothing to pay" in data["detail"].lower()

    async def test_payment_negative_balance_returns_422(self, client: AsyncClient):
        """BR-003: Returns 422 when account has negative balance."""
        account = _make_account(curr_bal=Decimal("-50.00"))

        with patch.object(AccountRepository, "get_by_id", return_value=account):
            app.dependency_overrides[get_db] = lambda: MagicMock()
            response = await client.post("/payments/10000000001")
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 422

    async def test_payment_xref_not_found_returns_404(self, client: AsyncClient):
        """Returns 404 when card cross-reference not found."""
        account = _make_account(curr_bal=Decimal("500.00"))

        with (
            patch.object(AccountRepository, "get_by_id", return_value=account),
            patch.object(CardCrossReferenceRepository, "get_by_acct_id", return_value=None),
        ):
            app.dependency_overrides[get_db] = lambda: MagicMock()
            response = await client.post("/payments/10000000001")
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 404

    async def test_payment_unauthenticated_returns_401(self):
        """Unauthenticated request returns 401."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as c:
            response = await c.post("/payments/10000000001")
        assert response.status_code == 401

    async def test_payment_returns_acct_id_in_response(self, client: AsyncClient):
        """Response includes the account ID."""
        account = _make_account(curr_bal=Decimal("300.00"))
        xref = _make_xref()
        tran = _make_transaction("0000000000000010", amount=Decimal("300.00"))
        zeroed = _make_account(curr_bal=Decimal("0.00"))

        with (
            patch.object(AccountRepository, "get_by_id", return_value=account),
            patch.object(CardCrossReferenceRepository, "get_by_acct_id", return_value=xref),
            patch.object(TransactionRepository, "generate_next_tran_id", return_value="0000000000000010"),
            patch.object(TransactionRepository, "create", return_value=tran),
            patch.object(AccountRepository, "zero_balance", return_value=zeroed),
        ):
            app.dependency_overrides[get_db] = lambda: MagicMock()
            response = await client.post("/payments/10000000001")
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 201
        data = response.json()
        assert data["acct_id"] == "10000000001"
