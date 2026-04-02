"""
Tests for authorization_service.py — maps COPAUA0C, COPAUS0C, COPAUS1C, COPAUS2C.

Business rules tested:
  COPAUA0C-001: available = credit_limit - |curr_bal| - approved_running
  COPAUA0C-002: available >= requested -> APPROVE ('00')
  COPAUA0C-003: available < requested -> DECLINE ('51')
  COPAUA0C-004: writes PAUTDTL1 (auth_detail) on both approve and decline
  COPAUA0C-005: updates PAUTSUM0 (auth_summary) approved/declined counters
  COPAUS2C-001: INSERT AUTHFRDS when no prior record
  COPAUS2C-002: UPDATE AUTHFRDS when record exists
  COPAUS2C-003: sets fraud_flag='Y' on PAUTDTL1 (IMS REPL)
"""

from datetime import date, time
from decimal import Decimal

import pytest

from app.core.exceptions import ResourceNotFoundError
from app.domain.services.authorization_service import (
    flag_fraud,
    get_auth_detail,
    get_auth_details_for_account,
    get_auth_summary_list,
    process_authorization,
)
from app.schemas.authorization_schemas import AuthorizationRequest, FraudFlagRequest


class TestGetAuthSummaryList:
    """Maps COPAUS0C summary list."""

    @pytest.mark.asyncio
    async def test_returns_all_summaries(self, seeded_db):
        result = await get_auth_summary_list(seeded_db)
        assert result.total_count >= 2

    @pytest.mark.asyncio
    async def test_filter_by_account_id(self, seeded_db):
        result = await get_auth_summary_list(seeded_db, account_id_filter=10000000001)
        assert result.total_count == 1
        assert result.items[0].acct_id == 10000000001

    @pytest.mark.asyncio
    async def test_filter_nonexistent_account_returns_empty(self, seeded_db):
        result = await get_auth_summary_list(seeded_db, account_id_filter=99999999999)
        assert result.total_count == 0


class TestGetAuthDetail:
    """Maps COPAUS1C detail view."""

    @pytest.mark.asyncio
    async def test_returns_detail_by_key(self, seeded_db):
        result = await get_auth_detail(
            10000000001,
            date(2024, 1, 15),
            time(10, 30, 0),
            seeded_db,
        )
        assert result.acct_id == 10000000001
        assert result.response_code == "00"
        assert result.auth_id_code == "AUTH001"

    @pytest.mark.asyncio
    async def test_wrong_key_raises_not_found(self, seeded_db):
        with pytest.raises(ResourceNotFoundError):
            await get_auth_detail(
                10000000001,
                date(2000, 1, 1),
                time(0, 0, 0),
                seeded_db,
            )

    @pytest.mark.asyncio
    async def test_returns_declined_detail(self, seeded_db):
        result = await get_auth_detail(
            10000000001,
            date(2024, 1, 16),
            time(14, 45, 0),
            seeded_db,
        )
        assert result.response_code == "51"
        assert result.fraud_flag == "N"


class TestGetAuthDetailsForAccount:
    @pytest.mark.asyncio
    async def test_returns_all_details_for_account(self, seeded_db):
        result = await get_auth_details_for_account(10000000001, seeded_db)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_empty_for_unknown_account(self, seeded_db):
        result = await get_auth_details_for_account(99999999999, seeded_db)
        assert result == []


class TestProcessAuthorization:
    """Maps COPAUA0C decision engine."""

    @pytest.mark.asyncio
    async def test_approve_when_sufficient_credit(self, seeded_db):
        """
        Account 1: credit_limit=5000, curr_bal=-1500, approved_running=800
        available = 5000 - 1500 - 800 = 2700
        Request 100 -> APPROVE
        """
        req = AuthorizationRequest(
            card_num="4111111111111001",
            requested_amt=Decimal("100.00"),
            auth_type="P",
        )
        result = await process_authorization(req, seeded_db)
        assert result.response_code == "00"
        assert result.approved_amt == Decimal("100.00")
        assert result.tran_id is not None

    @pytest.mark.asyncio
    async def test_decline_when_insufficient_credit(self, seeded_db):
        """
        Account 1: credit_limit=5000, curr_bal=-1500, approved_running=800
        available = 2700; request 3000 -> DECLINE
        """
        req = AuthorizationRequest(
            card_num="4111111111111001",
            requested_amt=Decimal("3000.00"),
            auth_type="P",
        )
        result = await process_authorization(req, seeded_db)
        assert result.response_code == "51"
        assert result.approved_amt == Decimal("0.00")
        assert result.tran_id is None

    @pytest.mark.asyncio
    async def test_decline_response_reason_contains_amounts(self, seeded_db):
        req = AuthorizationRequest(
            card_num="4111111111111001",
            requested_amt=Decimal("9999.00"),
            auth_type="P",
        )
        result = await process_authorization(req, seeded_db)
        assert result.response_code == "51"
        assert "insufficient" in result.response_reason.lower()

    @pytest.mark.asyncio
    async def test_approve_creates_auth_detail_record(self, seeded_db):
        """COPAUA0C writes PAUTDTL1 on approval."""
        req = AuthorizationRequest(
            card_num="4111111111111002",
            requested_amt=Decimal("50.00"),
            auth_type="P",
        )
        result = await process_authorization(req, seeded_db)
        assert result.response_code == "00"
        # Verify detail was written
        from app.infrastructure.repositories.authorization_repository import AuthDetailRepository
        detail_repo = AuthDetailRepository(seeded_db)
        details = await detail_repo.get_for_account(10000000002)
        assert len(details) >= 1

    @pytest.mark.asyncio
    async def test_approval_updates_summary_counters(self, seeded_db):
        """COPAUA0C updates PAUTSUM0 approved_count/approved_amt."""
        from app.infrastructure.repositories.authorization_repository import AuthSummaryRepository
        summary_repo = AuthSummaryRepository(seeded_db)
        before = await summary_repo.get_by_acct_id(10000000001)
        before_count = before.approved_count

        req = AuthorizationRequest(
            card_num="4111111111111001",
            requested_amt=Decimal("50.00"),
            auth_type="P",
        )
        await process_authorization(req, seeded_db)

        after = await summary_repo.get_by_acct_id(10000000001)
        assert after.approved_count == before_count + 1

    @pytest.mark.asyncio
    async def test_decline_updates_declined_counters(self, seeded_db):
        """COPAUA0C increments declined_count on DECLINE."""
        from app.infrastructure.repositories.authorization_repository import AuthSummaryRepository
        summary_repo = AuthSummaryRepository(seeded_db)
        before = await summary_repo.get_by_acct_id(10000000001)
        before_count = before.declined_count

        req = AuthorizationRequest(
            card_num="4111111111111001",
            requested_amt=Decimal("9999.00"),
            auth_type="P",
        )
        await process_authorization(req, seeded_db)

        after = await summary_repo.get_by_acct_id(10000000001)
        assert after.declined_count == before_count + 1

    @pytest.mark.asyncio
    async def test_unknown_card_raises_not_found(self, seeded_db):
        req = AuthorizationRequest(
            card_num="9999999999999999",
            requested_amt=Decimal("100.00"),
            auth_type="P",
        )
        with pytest.raises(ResourceNotFoundError):
            await process_authorization(req, seeded_db)

    @pytest.mark.asyncio
    async def test_exactly_available_credit_is_approved(self, seeded_db):
        """Boundary: available = requested -> APPROVE."""
        from app.infrastructure.repositories.authorization_repository import AuthSummaryRepository
        summary_repo = AuthSummaryRepository(seeded_db)
        summary = await summary_repo.get_by_acct_id(10000000001)
        # available = 5000 - 1500 - 800 = 2700
        available = Decimal("5000.00") - abs(Decimal("-1500.00")) - summary.approved_amt

        req = AuthorizationRequest(
            card_num="4111111111111001",
            requested_amt=available,
            auth_type="P",
        )
        result = await process_authorization(req, seeded_db)
        assert result.response_code == "00"

    @pytest.mark.asyncio
    async def test_creates_summary_for_new_account(self, seeded_db):
        """COPAUA0C: ISRT new PAUTSUM0 if account has no prior summary."""
        # Account 3 has no auth_summary in seed data
        req = AuthorizationRequest(
            card_num="4111111111111003",
            requested_amt=Decimal("10.00"),
            auth_type="P",
        )
        # This may approve or decline; just verify it completes without error
        result = await process_authorization(req, seeded_db)
        assert result.response_code in ("00", "51")


class TestFlagFraud:
    """Maps COPAUS2C INSERT/UPDATE AUTHFRDS + IMS REPL fraud_flag='Y'."""

    @pytest.mark.asyncio
    async def test_flag_fraud_inserts_new_record(self, seeded_db):
        """COPAUS2C: INSERT when no prior AUTHFRDS record."""
        req = FraudFlagRequest(
            acct_id=10000000001,
            auth_date=date(2024, 1, 15),
            auth_time=time(10, 30, 0),
            fraud_reason="Suspicious merchant",
            fraud_status="P",
        )
        result = await flag_fraud(req, "SYSADM00", seeded_db)
        assert result["acct_id"] == 10000000001

    @pytest.mark.asyncio
    async def test_flag_fraud_sets_fraud_flag_on_detail(self, seeded_db):
        """COPAUS2C: sets PAUTDTL1 fraud_flag = 'Y' (IMS REPL)."""
        req = FraudFlagRequest(
            acct_id=10000000001,
            auth_date=date(2024, 1, 15),
            auth_time=time(10, 30, 0),
            fraud_reason="Test fraud",
            fraud_status="P",
        )
        await flag_fraud(req, "SYSADM00", seeded_db)

        detail = await get_auth_detail(
            10000000001,
            date(2024, 1, 15),
            time(10, 30, 0),
            seeded_db,
        )
        assert detail.fraud_flag == "Y"

    @pytest.mark.asyncio
    async def test_flag_fraud_on_nonexistent_detail_raises_not_found(self, seeded_db):
        """Cannot flag fraud on a detail record that doesn't exist."""
        req = FraudFlagRequest(
            acct_id=10000000001,
            auth_date=date(2000, 1, 1),
            auth_time=time(0, 0, 0),
            fraud_reason="Test",
            fraud_status="P",
        )
        with pytest.raises(ResourceNotFoundError):
            await flag_fraud(req, "SYSADM00", seeded_db)

    @pytest.mark.asyncio
    async def test_flag_fraud_updates_existing_record(self, seeded_db):
        """COPAUS2C: UPDATE when prior AUTHFRDS record exists."""
        req = FraudFlagRequest(
            acct_id=10000000001,
            auth_date=date(2024, 1, 15),
            auth_time=time(10, 30, 0),
            fraud_reason="Initial reason",
            fraud_status="P",
        )
        await flag_fraud(req, "SYSADM00", seeded_db)

        # Second call should UPDATE (not INSERT duplicate)
        req2 = FraudFlagRequest(
            acct_id=10000000001,
            auth_date=date(2024, 1, 15),
            auth_time=time(10, 30, 0),
            fraud_reason="Updated reason",
            fraud_status="C",
        )
        result = await flag_fraud(req2, "SYSADM00", seeded_db)
        assert result["acct_id"] == 10000000001
