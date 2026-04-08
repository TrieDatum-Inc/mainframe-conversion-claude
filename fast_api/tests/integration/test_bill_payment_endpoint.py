"""
Integration tests for POST /api/v1/accounts/{id}/payments (COBIL00C / CB00).

Tests verify HTTP-level behavior for the account-centric payment path:
  1. 201 Created for valid payment
  2. Balance reduced by payment amount (ACCT-CURR-BAL = ACCT-CURR-BAL - TRAN-AMT)
  3. Transaction record created with TRAN-TYPE-CD = '02'
  4. 404 when account not found
  5. 422 when payment amount exceeds balance
  6. 401/403 for auth failures

Source: COBIL00C PROCESS-PAYMENT paragraph.
"""
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.models.account import Account
from app.models.card import Card
from app.models.transaction import TransactionType


class TestBillPaymentAccountPath:
    """Integration tests for COBIL00C bill payment via account-centric path."""

    @pytest.mark.asyncio
    async def test_payment_returns_201(
        self,
        client: AsyncClient,
        auth_token: str,
        account: Account,
        card: Card,
        tran_type: TransactionType,
    ) -> None:
        """
        COBIL00C PROCESS-PAYMENT: WRITE FILE('TRANSACT') succeeds → 201 Created.
        """
        response = await client.post(
            "/api/v1/accounts/1/payments",
            json={"payment_amount": "50.00"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_payment_creates_transaction_record(
        self,
        client: AsyncClient,
        auth_token: str,
        account: Account,
        card: Card,
        tran_type: TransactionType,
    ) -> None:
        """
        COBIL00C: EXEC CICS WRITE FILE('TRANSACT') FROM(TRAN-RECORD).
        Response body must contain a transaction ID.
        """
        response = await client.post(
            "/api/v1/accounts/1/payments",
            json={"payment_amount": "50.00"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        data = response.json()
        assert "tran_id" in data
        assert data["tran_id"] is not None

    @pytest.mark.asyncio
    async def test_payment_transaction_type_cd_is_02(
        self,
        client: AsyncClient,
        auth_token: str,
        account: Account,
        card: Card,
        tran_type: TransactionType,
    ) -> None:
        """
        COBIL00C: MOVE '02' TO TRAN-TYPE-CD
        Payment transactions must have type_cd = '02'.
        """
        response = await client.post(
            "/api/v1/accounts/1/payments",
            json={"payment_amount": "50.00"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        data = response.json()
        assert data["type_cd"] == "02"

    @pytest.mark.asyncio
    async def test_payment_reduces_account_balance(
        self,
        client: AsyncClient,
        auth_token: str,
        account: Account,
        card: Card,
        tran_type: TransactionType,
    ) -> None:
        """
        COBIL00C: COMPUTE ACCT-CURR-BAL = ACCT-CURR-BAL - TRAN-AMT
        Account balance must decrease by payment amount after successful payment.
        """
        # Get initial balance
        acct_before = await client.get(
            "/api/v1/accounts/1",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        initial_balance = Decimal(str(acct_before.json()["curr_bal"]))

        payment_amount = Decimal("50.00")
        await client.post(
            "/api/v1/accounts/1/payments",
            json={"payment_amount": str(payment_amount)},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        # Verify balance reduced
        acct_after = await client.get(
            "/api/v1/accounts/1",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        new_balance = Decimal(str(acct_after.json()["curr_bal"]))
        expected_balance = initial_balance - payment_amount
        assert new_balance == expected_balance

    @pytest.mark.asyncio
    async def test_payment_for_nonexistent_account_returns_404(
        self,
        client: AsyncClient,
        auth_token: str,
    ) -> None:
        """
        COBIL00C READ-ACCTDAT-FILE: DFHRESP(NOTFND) → 'Account ID NOT found...' → HTTP 404.
        """
        response = await client.post(
            "/api/v1/accounts/99999/payments",
            json={"payment_amount": "50.00"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_payment_exceeds_balance_returns_422(
        self,
        client: AsyncClient,
        auth_token: str,
        account: Account,
        card: Card,
        tran_type: TransactionType,
    ) -> None:
        """
        COBIL00C: payment_amount > ACCT-CURR-BAL → validation error → 422.
        (Account balance is $194.00; attempt to pay $999.00)
        """
        response = await client.post(
            "/api/v1/accounts/1/payments",
            json={"payment_amount": "999.00"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_payment_zero_amount_returns_422(
        self,
        client: AsyncClient,
        auth_token: str,
        account: Account,
        card: Card,
        tran_type: TransactionType,
    ) -> None:
        """
        COBIL00C: payment_amount must be positive (BillPaymentRequest gt=0 constraint).
        """
        response = await client.post(
            "/api/v1/accounts/1/payments",
            json={"payment_amount": "0.00"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_payment_negative_amount_returns_422(
        self,
        client: AsyncClient,
        auth_token: str,
        account: Account,
        card: Card,
        tran_type: TransactionType,
    ) -> None:
        """payment_amount must be positive — negative amounts rejected."""
        response = await client.post(
            "/api/v1/accounts/1/payments",
            json={"payment_amount": "-10.00"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_payment_unauthenticated_returns_401(
        self, client: AsyncClient, account: Account
    ) -> None:
        """No JWT token → 401."""
        response = await client.post(
            "/api/v1/accounts/1/payments",
            json={"payment_amount": "50.00"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_payment_acct_id_in_url_matches_payment_target(
        self,
        client: AsyncClient,
        auth_token: str,
        account: Account,
        card: Card,
        tran_type: TransactionType,
    ) -> None:
        """
        Account-centric path: acct_id in URL is the payment target.
        Transaction acct_id in response must match the path acct_id.
        """
        response = await client.post(
            "/api/v1/accounts/1/payments",
            json={"payment_amount": "50.00"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        data = response.json()
        assert data["acct_id"] == 1
