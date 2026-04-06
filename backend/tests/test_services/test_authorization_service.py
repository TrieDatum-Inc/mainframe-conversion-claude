"""
Unit tests for AuthorizationService business logic.
These tests use a mock repository to test business logic in isolation.
Maps to COPAUS0C/COPAUS1C/COPAUS2C PROCEDURE DIVISION paragraphs.
"""
from datetime import date, time, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.authorization import AuthFraudLog, AuthorizationDetail, AuthorizationSummary
from app.schemas.authorization import (
    format_fraud_status_display,
    mask_card_number,
    resolve_decline_reason,
)
from app.services.authorization_service import AuthorizationService


class TestDeclineReasonTable:
    """
    Tests for decline reason lookup.
    Replaces: COPAUS1C SEARCH ALL WS-DECLINE-REASON-TAB (lines 57-73).
    """

    def test_approved_code(self) -> None:
        """'00' → '00-APPROVED' (PA-AUTH-RESP-CODE = '00')."""
        assert resolve_decline_reason("00") == "00-APPROVED"

    def test_insufficient_funds(self) -> None:
        """'4100' → '4100-INSUFFICNT FUND'."""
        assert resolve_decline_reason("4100") == "4100-INSUFFICNT FUND"

    def test_invalid_card(self) -> None:
        """'3100' → '3100-INVALID CARD'."""
        assert resolve_decline_reason("3100") == "3100-INVALID CARD"

    def test_card_not_active(self) -> None:
        """'4200' → '4200-CARD NOT ACTIVE'."""
        assert resolve_decline_reason("4200") == "4200-CARD NOT ACTIVE"

    def test_account_closed(self) -> None:
        """'4300' → '4300-ACCOUNT CLOSED'."""
        assert resolve_decline_reason("4300") == "4300-ACCOUNT CLOSED"

    def test_exceeded_daily_limit(self) -> None:
        """'4400' → '4400-EXCED DAILY LMT'."""
        assert resolve_decline_reason("4400") == "4400-EXCED DAILY LMT"

    def test_card_fraud(self) -> None:
        """'5100' → '5100-CARD FRAUD'."""
        assert resolve_decline_reason("5100") == "5100-CARD FRAUD"

    def test_merchant_fraud(self) -> None:
        """'5200' → '5200-MERCHANT FRAUD'."""
        assert resolve_decline_reason("5200") == "5200-MERCHANT FRAUD"

    def test_lost_card(self) -> None:
        """'5300' → '5300-LOST CARD'."""
        assert resolve_decline_reason("5300") == "5300-LOST CARD"

    def test_unknown(self) -> None:
        """'9000' → '9000-UNKNOWN'."""
        assert resolve_decline_reason("9000") == "9000-UNKNOWN"

    def test_not_found_returns_error(self) -> None:
        """
        Code not in table → '9999-ERROR'.
        Replaces: COPAUS1C SEARCH ALL ... AT END MOVE 9999 TO DECL-CODE.
        """
        assert resolve_decline_reason("9999") == "9999-ERROR"
        assert resolve_decline_reason("1234") == "9999-ERROR"
        assert resolve_decline_reason("") == "9999-ERROR"

    def test_whitespace_stripped(self) -> None:
        """Whitespace in code should be stripped before lookup."""
        assert resolve_decline_reason("00  ") == "00-APPROVED"


class TestFraudStatusDisplay:
    """
    Tests for fraud status display formatting.
    Replaces: COPAUS1C POPULATE-AUTH-DETAILS lines 344-350.
    PA-FRAUD-CONFIRMED → 'FRAUD', PA-FRAUD-REMOVED → 'REMOVED', else ''
    """

    def test_fraud_confirmed_displays_fraud(self) -> None:
        """PA-FRAUD-CONFIRMED='F' → 'FRAUD' (AUTHFRDO field)."""
        assert format_fraud_status_display("F") == "FRAUD"

    def test_fraud_removed_displays_removed(self) -> None:
        """PA-FRAUD-REMOVED='R' → 'REMOVED' (AUTHFRDO field)."""
        assert format_fraud_status_display("R") == "REMOVED"

    def test_no_fraud_displays_empty(self) -> None:
        """No fraud flag → '' (AUTHFRDO = '-' in COBOL, empty in API)."""
        assert format_fraud_status_display("N") == ""

    def test_unknown_status_displays_empty(self) -> None:
        """Unknown status → empty string (defensive)."""
        assert format_fraud_status_display("X") == ""


class TestMaskCardNumber:
    """Tests for PCI-DSS card number masking."""

    def test_full_card_number_masked(self) -> None:
        """16-digit card shows only last 4."""
        assert mask_card_number("4111111111111001") == "************1001"

    def test_short_card_preserved(self) -> None:
        """Short card (< 4 chars) returned as-is."""
        assert mask_card_number("123") == "123"

    def test_padded_card_number(self) -> None:
        """Card number with trailing space padded by CHAR(16)."""
        assert mask_card_number("4111111111111001") == "************1001"


class TestFraudToggleCycle:
    """
    Tests for 3-state fraud toggle cycle.
    Replaces: COPAUS1C MARK-AUTH-FRAUD IF/ELSE + COPAUS2C WS-FRD-ACTION.
    Spec: N→F, F→R, R→F (3-state cycle).
    """

    def setup_method(self) -> None:
        """Set up mock repo for each test."""
        self.mock_repo = MagicMock()
        self.mock_repo.get_detail_by_id = AsyncMock()
        self.mock_repo.update_fraud_status = AsyncMock()
        self.mock_repo.upsert_fraud_log = AsyncMock()
        self.service = AuthorizationService(self.mock_repo)

    @pytest.mark.asyncio
    async def test_n_to_f_transition(
        self, sample_detail: AuthorizationDetail, sample_fraud_log: AuthFraudLog
    ) -> None:
        """N (no fraud) → F (fraud confirmed). WS-FRD-ACTION='F'."""
        sample_detail.fraud_status = "N"
        updated = MagicMock(spec=AuthorizationDetail)
        updated.auth_id = sample_detail.auth_id
        updated.fraud_status = "F"

        self.mock_repo.get_detail_by_id.return_value = sample_detail
        self.mock_repo.upsert_fraud_log.return_value = sample_fraud_log
        self.mock_repo.update_fraud_status.return_value = updated

        result = await self.service.toggle_fraud_flag(
            auth_id=sample_detail.auth_id, current_fraud_status="N"
        )

        assert result.new_fraud_status == "F"
        assert result.previous_fraud_status == "N"
        assert result.fraud_status_display == "FRAUD"
        self.mock_repo.upsert_fraud_log.assert_called_once()
        call_kwargs = self.mock_repo.upsert_fraud_log.call_args
        assert call_kwargs[0][1] == "F"  # fraud_flag argument

    @pytest.mark.asyncio
    async def test_f_to_r_transition(
        self, sample_detail: AuthorizationDetail, sample_fraud_log: AuthFraudLog
    ) -> None:
        """F (fraud confirmed) → R (fraud removed). WS-FRD-ACTION='R'."""
        sample_detail.fraud_status = "F"
        sample_fraud_log.fraud_flag = "R"
        updated = MagicMock(spec=AuthorizationDetail)
        updated.auth_id = sample_detail.auth_id
        updated.fraud_status = "R"

        self.mock_repo.get_detail_by_id.return_value = sample_detail
        self.mock_repo.upsert_fraud_log.return_value = sample_fraud_log
        self.mock_repo.update_fraud_status.return_value = updated

        result = await self.service.toggle_fraud_flag(
            auth_id=sample_detail.auth_id, current_fraud_status="F"
        )

        assert result.new_fraud_status == "R"
        assert result.fraud_status_display == "REMOVED"
        call_kwargs = self.mock_repo.upsert_fraud_log.call_args
        assert call_kwargs[0][1] == "R"

    @pytest.mark.asyncio
    async def test_r_to_f_transition(
        self, sample_detail: AuthorizationDetail, sample_fraud_log: AuthFraudLog
    ) -> None:
        """R (fraud removed) → F (re-confirm fraud). WS-FRD-ACTION='F'."""
        sample_detail.fraud_status = "R"
        updated = MagicMock(spec=AuthorizationDetail)
        updated.auth_id = sample_detail.auth_id
        updated.fraud_status = "F"

        self.mock_repo.get_detail_by_id.return_value = sample_detail
        self.mock_repo.upsert_fraud_log.return_value = sample_fraud_log
        self.mock_repo.update_fraud_status.return_value = updated

        result = await self.service.toggle_fraud_flag(
            auth_id=sample_detail.auth_id, current_fraud_status="R"
        )

        assert result.new_fraud_status == "F"
        assert result.fraud_status_display == "FRAUD"

    @pytest.mark.asyncio
    async def test_not_found_raises_404(self) -> None:
        """
        Authorization not found → 404.
        Replaces: COPAUS1C IMS GNP GE status (segment not found).
        """
        from fastapi import HTTPException

        self.mock_repo.get_detail_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await self.service.toggle_fraud_flag(auth_id=9999, current_fraud_status="N")

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_stale_status_raises_409(
        self, sample_detail: AuthorizationDetail
    ) -> None:
        """
        Client status mismatch → 409 Conflict.
        Prevents double-toggle on page refresh.
        """
        from fastapi import HTTPException

        sample_detail.fraud_status = "N"
        self.mock_repo.get_detail_by_id.return_value = sample_detail

        with pytest.raises(HTTPException) as exc_info:
            await self.service.toggle_fraud_flag(
                auth_id=sample_detail.auth_id, current_fraud_status="F"
            )

        assert exc_info.value.status_code == 409
        assert "FRAUD_STATUS_MISMATCH" in str(exc_info.value.detail)


class TestListDetailForAccount:
    """
    Tests for list_details_for_account service method.
    Replaces: COPAUS0C GATHER-DETAILS + PROCESS-PAGE-FORWARD.
    """

    def setup_method(self) -> None:
        self.mock_repo = MagicMock()
        self.mock_repo.get_summary_by_account = AsyncMock()
        self.mock_repo.list_details_by_account = AsyncMock()
        self.service = AuthorizationService(self.mock_repo)

    @pytest.mark.asyncio
    async def test_returns_summary_with_items(
        self,
        sample_summary: AuthorizationSummary,
        sample_detail: AuthorizationDetail,
    ) -> None:
        """Returns summary header + detail list (COPAUS0C screen layout)."""
        self.mock_repo.get_summary_by_account.return_value = sample_summary
        self.mock_repo.list_details_by_account.return_value = ([sample_detail], 1)

        result = await self.service.list_details_for_account(
            account_id=10000000001, page=1, page_size=5
        )

        assert result.summary.account_id == 10000000001
        assert len(result.items) == 1
        assert result.total_count == 1
        assert result.has_next is False
        assert result.has_previous is False

    @pytest.mark.asyncio
    async def test_paging_has_next_flag(
        self,
        sample_summary: AuthorizationSummary,
        sample_detail: AuthorizationDetail,
    ) -> None:
        """
        has_next=True when more records exist.
        Replaces: COPAUS0C CDEMO-CPVS-NEXT-PAGE-FLG 'Y'.
        """
        self.mock_repo.get_summary_by_account.return_value = sample_summary
        self.mock_repo.list_details_by_account.return_value = ([sample_detail], 10)

        result = await self.service.list_details_for_account(
            account_id=10000000001, page=1, page_size=5
        )

        assert result.has_next is True
        assert result.has_previous is False

    @pytest.mark.asyncio
    async def test_summary_not_found_raises_404(self) -> None:
        """No authorization summary → 404. Replaces IMS GE on GU PAUTSUM0."""
        from fastapi import HTTPException

        self.mock_repo.get_summary_by_account.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await self.service.list_details_for_account(
                account_id=9999, page=1, page_size=5
            )

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_approval_status_a_for_approved(
        self,
        sample_summary: AuthorizationSummary,
        sample_detail: AuthorizationDetail,
    ) -> None:
        """
        auth_response_code='00' → approval_status='A'.
        Replaces: COPAUS0C WS-AUTH-APRV-STAT = 'A' if resp='00'.
        """
        sample_detail.auth_response_code = "00"
        self.mock_repo.get_summary_by_account.return_value = sample_summary
        self.mock_repo.list_details_by_account.return_value = ([sample_detail], 1)

        result = await self.service.list_details_for_account(
            account_id=10000000001, page=1, page_size=5
        )

        assert result.items[0].approval_status == "A"

    @pytest.mark.asyncio
    async def test_approval_status_d_for_declined(
        self,
        sample_summary: AuthorizationSummary,
        sample_detail_declined: AuthorizationDetail,
    ) -> None:
        """
        auth_response_code != '00' → approval_status='D'.
        Replaces: COPAUS0C WS-AUTH-APRV-STAT = 'D' if resp != '00'.
        """
        self.mock_repo.get_summary_by_account.return_value = sample_summary
        self.mock_repo.list_details_by_account.return_value = (
            [sample_detail_declined], 1
        )

        result = await self.service.list_details_for_account(
            account_id=10000000001, page=1, page_size=5
        )

        assert result.items[0].approval_status == "D"


class TestGetAuthorizationDetail:
    """
    Tests for get_authorization_detail service method.
    Replaces: COPAUS1C POPULATE-AUTH-DETAILS paragraph.
    """

    def setup_method(self) -> None:
        self.mock_repo = MagicMock()
        self.mock_repo.get_detail_by_id = AsyncMock()
        self.service = AuthorizationService(self.mock_repo)

    @pytest.mark.asyncio
    async def test_returns_full_detail(
        self, sample_detail: AuthorizationDetail
    ) -> None:
        """Returns all COPAU01 screen fields."""
        self.mock_repo.get_detail_by_id.return_value = sample_detail

        result = await self.service.get_authorization_detail(auth_id=1)

        assert result.auth_id == 1
        assert result.transaction_id == "TXN0000000001"
        assert result.merchant_name == "WHOLE FOODS MARKET"
        assert result.approval_status == "A"
        assert result.decline_reason == "00-APPROVED"

    @pytest.mark.asyncio
    async def test_fraud_status_display_for_confirmed(
        self, sample_detail: AuthorizationDetail
    ) -> None:
        """
        fraud_status='F' → fraud_status_display='FRAUD'.
        Replaces: COPAUS1C IF PA-FRAUD-CONFIRMED → AUTHFRDO = 'FRAUD'.
        """
        sample_detail.fraud_status = "F"
        self.mock_repo.get_detail_by_id.return_value = sample_detail

        result = await self.service.get_authorization_detail(auth_id=1)

        assert result.fraud_status == "F"
        assert result.fraud_status_display == "FRAUD"

    @pytest.mark.asyncio
    async def test_fraud_status_display_for_removed(
        self, sample_detail: AuthorizationDetail
    ) -> None:
        """
        fraud_status='R' → fraud_status_display='REMOVED'.
        Replaces: COPAUS1C IF PA-FRAUD-REMOVED → AUTHFRDO = 'REMOVED'.
        """
        sample_detail.fraud_status = "R"
        self.mock_repo.get_detail_by_id.return_value = sample_detail

        result = await self.service.get_authorization_detail(auth_id=1)

        assert result.fraud_status == "R"
        assert result.fraud_status_display == "REMOVED"

    @pytest.mark.asyncio
    async def test_card_number_masked(
        self, sample_detail: AuthorizationDetail
    ) -> None:
        """Card number masked in response (PCI-DSS)."""
        self.mock_repo.get_detail_by_id.return_value = sample_detail

        result = await self.service.get_authorization_detail(auth_id=1)

        assert result.card_number_masked == "************1001"
        assert "111111111" not in result.card_number_masked

    @pytest.mark.asyncio
    async def test_not_found_raises_404(self) -> None:
        """Not found → 404. Replaces COPAUS1C IMS GNP GE status."""
        from fastapi import HTTPException

        self.mock_repo.get_detail_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await self.service.get_authorization_detail(auth_id=9999)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_declined_transaction(
        self, sample_detail_declined: AuthorizationDetail
    ) -> None:
        """
        Declined authorization: approval_status='D', decline_reason='4100-INSUFFICNT FUND'.
        Replaces: COPAUS1C DFHRED for AUTHRSPO when resp != '00'.
        """
        self.mock_repo.get_detail_by_id.return_value = sample_detail_declined

        result = await self.service.get_authorization_detail(auth_id=2)

        assert result.approval_status == "D"
        assert result.decline_reason == "4100-INSUFFICNT FUND"
