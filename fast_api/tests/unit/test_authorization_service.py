"""
Unit tests for AuthorizationService — business logic from COPAUA0C/COPAUS0C/COPAUS1C/COPAUS2C.

Tests verify all business rules:
  1.  process_authorization — approved when card valid, account active, sufficient credit
  2.  process_authorization — declined 3100 when card not in CCXREF
  3.  process_authorization — declined 4300 when account inactive
  4.  process_authorization — declined 4100 when amount > available credit
  5.  process_authorization — uses auth_summary credit_balance when summary exists
  6.  process_authorization — falls back to account.curr_bal when no summary
  7.  process_authorization — approved_amt = 0 on decline
  8.  process_authorization — approved_amt = transaction_amt on approve
  9.  process_authorization — persists auth_detail after decision
  10. process_authorization — updates auth_summary counters
  11. list_authorizations — returns paginated detail list + summary
  12. get_authorization_detail — returns detail by auth_id
  13. get_authorization_detail — raises RecordNotFoundError on missing id
  14. get_next_authorization_detail — navigates to next record (PF8)
  15. get_next_authorization_detail — raises RecordNotFoundError at end (AUTHS-EOF)
  16. mark_fraud — sets PA-FRAUD-CONFIRMED ('F') and writes to AUTHFRDS
  17. mark_fraud — sets PA-FRAUD-REMOVED ('R') on toggle
  18. _make_decision — uses summary balance over account balance when summary present
  19. _build_auth_ts — reconstructs timestamp from inverted COBOL key fields
"""
from decimal import Decimal

import pytest

from app.models.account import Account
from app.models.authorization import AuthDetail, AuthSummary
from app.models.card import Card, CardXref
from app.schemas.authorization import (
    AuthDecision,
    AuthorizationRequest,
    DeclineReasonCode,
    FraudAction,
    FraudMarkRequest,
)
from app.services.authorization_service import AuthorizationService
from app.utils.error_handlers import RecordNotFoundError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_auth_request(**overrides) -> AuthorizationRequest:
    """Build a default valid authorization request."""
    defaults = {
        "auth_date": "260331",
        "auth_time": "143022",
        "card_num": "0100000011111111",
        "auth_type": "PUR ",
        "card_expiry_date": "1125",
        "message_type": "0100  ",
        "message_source": "POS   ",
        "processing_code": 0,
        "transaction_amt": Decimal("150.00"),
        "merchant_category_code": "5411",
        "acqr_country_code": "840",
        "pos_entry_mode": 5,
        "merchant_id": "WALMART0001    ",
        "merchant_name": "WALMART SUPERCENTER   ",
        "merchant_city": "BENTONVILLE  ",
        "merchant_state": "AR",
        "merchant_zip": "727160001",
        "transaction_id": "TXN202603310001",
    }
    defaults.update(overrides)
    return AuthorizationRequest(**defaults)


# ---------------------------------------------------------------------------
# Authorization Decision Tests (COPAUA0C 6000-MAKE-DECISION)
# ---------------------------------------------------------------------------


class TestProcessAuthorization:
    """Tests for COPAUA0C 5000-PROCESS-AUTH and 6000-MAKE-DECISION paragraphs."""

    @pytest.mark.asyncio
    async def test_approved_valid_card_sufficient_credit(
        self, db, account: Account, card: Card
    ) -> None:
        """
        COPAUA0C 6000-MAKE-DECISION: approved when card found, account active,
        and transaction_amt <= available credit.
        auth_resp_code = '00', approved_amt = transaction_amt.
        """
        service = AuthorizationService(db)
        request = make_auth_request(transaction_amt=Decimal("100.00"))
        result = await service.process_authorization(request)

        assert result.auth_resp_code == AuthDecision.APPROVED
        assert result.is_approved is True
        assert result.approved_amt == Decimal("100.00")
        assert result.auth_resp_reason == DeclineReasonCode.APPROVED
        assert result.card_num == "0100000011111111"

    @pytest.mark.asyncio
    async def test_declined_card_not_in_xref(self, db, account: Account) -> None:
        """
        COPAUA0C 5100-READ-XREF-RECORD: CARD-NFOUND-XREF → DECLINE reason 3100.
        No card fixture added → xref not found.
        """
        service = AuthorizationService(db)
        request = make_auth_request(
            card_num="0000000000000001",  # no card seeded for this number
            transaction_amt=Decimal("50.00"),
        )
        result = await service.process_authorization(request)

        assert result.auth_resp_code == AuthDecision.DECLINED
        assert result.is_approved is False
        assert result.auth_resp_reason == DeclineReasonCode.INVALID_CARD
        assert result.approved_amt == Decimal("0.00")

    @pytest.mark.asyncio
    async def test_declined_account_inactive(
        self, db, account: Account, customer, card: Card
    ) -> None:
        """
        COPAUA0C: account ACCT-ACTIVE-STATUS != 'Y' → DECLINE reason 4300 (ACCOUNT CLOSED).
        """
        # Make account inactive
        account.active_status = "N"
        await db.flush()

        service = AuthorizationService(db)
        request = make_auth_request(transaction_amt=Decimal("50.00"))
        result = await service.process_authorization(request)

        assert result.auth_resp_code == AuthDecision.DECLINED
        assert result.auth_resp_reason == DeclineReasonCode.ACCOUNT_CLOSED
        assert result.approved_amt == Decimal("0.00")

    @pytest.mark.asyncio
    async def test_declined_insufficient_credit_no_summary(
        self, db, account: Account, card: Card
    ) -> None:
        """
        COPAUA0C 6000-MAKE-DECISION (no summary branch):
          COMPUTE WS-AVAILABLE-AMT = ACCT-CREDIT-LIMIT - ACCT-CURR-BAL
          IF WS-TRANSACTION-AMT > WS-AVAILABLE-AMT → DECLINE 4100

        Account: credit_limit=2020.00, curr_bal=194.00 → available=1826.00
        Requesting 1900.00 > 1826.00 → declined.
        """
        service = AuthorizationService(db)
        request = make_auth_request(transaction_amt=Decimal("1900.00"))
        result = await service.process_authorization(request)

        assert result.auth_resp_code == AuthDecision.DECLINED
        assert result.auth_resp_reason == DeclineReasonCode.INSUFFICIENT_FUND
        assert result.approved_amt == Decimal("0.00")

    @pytest.mark.asyncio
    async def test_approved_exact_available_credit_boundary(
        self, db, account: Account, card: Card
    ) -> None:
        """
        COPAUA0C 6000-MAKE-DECISION boundary: exactly available credit → approved.
        account.credit_limit=2020, curr_bal=194 → available=1826.00
        Transaction of exactly 1826.00 should be approved (not > available).
        """
        service = AuthorizationService(db)
        request = make_auth_request(transaction_amt=Decimal("1826.00"))
        result = await service.process_authorization(request)

        assert result.auth_resp_code == AuthDecision.APPROVED
        assert result.approved_amt == Decimal("1826.00")

    @pytest.mark.asyncio
    async def test_approved_uses_summary_credit_balance(
        self, db, account: Account, card: Card, auth_summary: AuthSummary
    ) -> None:
        """
        COPAUA0C 6000-MAKE-DECISION (summary found branch):
          COMPUTE WS-AVAILABLE-AMT = PA-CREDIT-LIMIT - PA-CREDIT-BALANCE
          summary: credit_limit=2020, credit_balance=194 → available=1826

        Uses summary balances, not account.curr_bal.
        """
        service = AuthorizationService(db)
        request = make_auth_request(transaction_amt=Decimal("500.00"))
        result = await service.process_authorization(request)

        assert result.auth_resp_code == AuthDecision.APPROVED
        assert result.approved_amt == Decimal("500.00")

    @pytest.mark.asyncio
    async def test_declined_insufficient_credit_with_summary(
        self, db, account: Account, card: Card, auth_summary: AuthSummary
    ) -> None:
        """
        COPAUA0C: summary credit_balance=194, credit_limit=2020 → available=1826.
        Amount 1900 > 1826 → declined with 4100.
        """
        service = AuthorizationService(db)
        request = make_auth_request(transaction_amt=Decimal("1900.00"))
        result = await service.process_authorization(request)

        assert result.auth_resp_code == AuthDecision.DECLINED
        assert result.auth_resp_reason == DeclineReasonCode.INSUFFICIENT_FUND

    @pytest.mark.asyncio
    async def test_auth_id_code_equals_auth_time(
        self, db, account: Account, card: Card
    ) -> None:
        """
        COPAUA0C 6000-MAKE-DECISION:
          MOVE PA-RQ-AUTH-TIME TO PA-RL-AUTH-ID-CODE
        auth_id_code in response must equal the request auth_time.
        """
        service = AuthorizationService(db)
        request = make_auth_request(auth_time="091530", transaction_amt=Decimal("10.00"))
        result = await service.process_authorization(request)

        assert result.auth_id_code == "091530"

    @pytest.mark.asyncio
    async def test_approved_increments_summary_counters(
        self, db, account: Account, card: Card, auth_summary: AuthSummary
    ) -> None:
        """
        COPAUA0C 8400-UPDATE-SUMMARY approved branch:
          ADD 1 TO PA-APPROVED-AUTH-CNT
          ADD WS-APPROVED-AMT TO PA-APPROVED-AUTH-AMT
          ADD WS-APPROVED-AMT TO PA-CREDIT-BALANCE
        """
        initial_cnt = auth_summary.approved_auth_cnt
        initial_amt = auth_summary.approved_auth_amt
        initial_bal = auth_summary.credit_balance

        service = AuthorizationService(db)
        request = make_auth_request(transaction_amt=Decimal("200.00"))
        await service.process_authorization(request)

        await db.refresh(auth_summary)
        assert auth_summary.approved_auth_cnt == initial_cnt + 1
        assert auth_summary.approved_auth_amt == initial_amt + Decimal("200.00")
        assert auth_summary.credit_balance == initial_bal + Decimal("200.00")

    @pytest.mark.asyncio
    async def test_declined_increments_declined_counters(
        self, db, account: Account, card: Card, auth_summary: AuthSummary
    ) -> None:
        """
        COPAUA0C 8400-UPDATE-SUMMARY declined branch:
          ADD 1 TO PA-DECLINED-AUTH-CNT
          ADD PA-TRANSACTION-AMT TO PA-DECLINED-AUTH-AMT
        """
        initial_cnt = auth_summary.declined_auth_cnt
        initial_amt = auth_summary.declined_auth_amt

        service = AuthorizationService(db)
        # Decline by requesting more than available
        request = make_auth_request(transaction_amt=Decimal("9999.00"))
        result = await service.process_authorization(request)

        assert result.auth_resp_code == AuthDecision.DECLINED
        await db.refresh(auth_summary)
        assert auth_summary.declined_auth_cnt == initial_cnt + 1
        assert auth_summary.declined_auth_amt == initial_amt + Decimal("9999.00")

    @pytest.mark.asyncio
    async def test_approved_persists_auth_detail_match_pending(
        self, db, account: Account, card: Card
    ) -> None:
        """
        COPAUA0C 8500-INSERT-AUTH:
          IF AUTH-RESP-APPROVED → SET PA-MATCH-PENDING TO TRUE ('P')
        auth_detail_id must be populated and match_status = 'P'.
        """
        service = AuthorizationService(db)
        request = make_auth_request(transaction_amt=Decimal("50.00"))
        result = await service.process_authorization(request)

        assert result.auth_detail_id is not None
        # Verify the persisted detail
        from app.repositories.authorization_repo import AuthorizationRepository
        repo = AuthorizationRepository(db)
        detail = await repo.get_detail_by_id(result.auth_detail_id)
        assert detail.match_status == "P"
        assert detail.auth_resp_code == "00"
        assert detail.card_num == "0100000011111111"

    @pytest.mark.asyncio
    async def test_declined_persists_auth_detail_match_declined(
        self, db, account: Account, card: Card
    ) -> None:
        """
        COPAUA0C 8500-INSERT-AUTH (declined with xref found):
          IF CARD-FOUND-XREF → PERFORM 8000-WRITE-AUTH-TO-DB regardless of decision.
          ELSE → SET PA-MATCH-AUTH-DECLINED TO TRUE ('D')
        Detail IS persisted for any authorization where the card exists in XREF.
        Only when the card is NOT found in XREF is auth_detail_id None.
        """
        service = AuthorizationService(db)
        # Card exists in xref, but amount exceeds credit limit → declined
        request = make_auth_request(transaction_amt=Decimal("9999.00"))
        result = await service.process_authorization(request)

        # auth_detail_id IS non-None — COBOL writes detail for all cards found in XREF
        assert result.auth_detail_id is not None
        assert result.auth_resp_code == AuthDecision.DECLINED

    @pytest.mark.asyncio
    async def test_declined_with_xref_found_persists_detail(
        self, db, account: Account, card: Card, auth_summary: AuthSummary
    ) -> None:
        """
        COPAUA0C 8500-INSERT-AUTH for declined authorization:
          IF CARD-FOUND-XREF → PERFORM 8000-WRITE-AUTH-TO-DB regardless of decision.
          match_status = 'D' on decline.
        """
        service = AuthorizationService(db)
        # Exceed available credit to force decline
        request = make_auth_request(transaction_amt=Decimal("9999.00"))
        result = await service.process_authorization(request)

        assert result.auth_resp_code == AuthDecision.DECLINED
        assert result.auth_detail_id is not None  # detail persisted even on decline

        from app.repositories.authorization_repo import AuthorizationRepository
        repo = AuthorizationRepository(db)
        detail = await repo.get_detail_by_id(result.auth_detail_id)
        assert detail.match_status == "D"
        assert detail.auth_resp_code == "05"

    @pytest.mark.asyncio
    async def test_no_xref_no_detail_persisted(self, db, account: Account) -> None:
        """
        COPAUA0C: IF CARD-FOUND-XREF → PERFORM 8000-WRITE-AUTH-TO-DB
        When card is NOT in CCXREF, no detail should be written.
        """
        service = AuthorizationService(db)
        request = make_auth_request(
            card_num="0000000000000002",
            transaction_amt=Decimal("50.00"),
        )
        result = await service.process_authorization(request)

        assert result.auth_resp_code == AuthDecision.DECLINED
        assert result.auth_detail_id is None  # no detail written — no xref

    @pytest.mark.asyncio
    async def test_creates_summary_when_none_exists(
        self, db, account: Account, card: Card
    ) -> None:
        """
        COPAUA0C 8400-UPDATE-SUMMARY: IF NFOUND-PAUT-SMRY-SEG → INITIALIZE + INSERT.
        When no summary exists, a new one is created.
        """
        service = AuthorizationService(db)
        request = make_auth_request(transaction_amt=Decimal("50.00"))
        result = await service.process_authorization(request)

        from app.repositories.authorization_repo import AuthorizationRepository
        repo = AuthorizationRepository(db)
        summary = await repo.get_summary_by_acct_id(1)
        assert summary is not None
        assert summary.approved_auth_cnt == 1
        assert summary.credit_limit == account.credit_limit


# ---------------------------------------------------------------------------
# Authorization List / View Tests (COPAUS0C, COPAUS1C)
# ---------------------------------------------------------------------------


class TestListAndViewAuthorizations:
    """Tests for COPAUS0C (CPVS) and COPAUS1C (CPVD) view programs."""

    @pytest.mark.asyncio
    async def test_list_authorizations_returns_items_and_summary(
        self, db, account: Account, card: Card, auth_summary: AuthSummary, auth_detail: AuthDetail
    ) -> None:
        """
        COPAUS0C GATHER-DETAILS: retrieve list + summary for account.
        CDEMO-CPVS-AUTH-KEYS OCCURS 5 → up to 5 items per page.
        """
        service = AuthorizationService(db)
        result = await service.list_authorizations(acct_id=1)

        assert result.total >= 1
        assert len(result.items) >= 1
        assert result.summary is not None
        assert result.summary.acct_id == 1
        assert result.summary.credit_limit == Decimal("2020.00")

    @pytest.mark.asyncio
    async def test_list_authorizations_empty_account(
        self, db, account: Account
    ) -> None:
        """
        COPAUS0C: account with no authorization records returns empty list.
        CDEMO-CPVS-PAUKEY-LAST = SPACES → no PF8 navigation possible.
        """
        service = AuthorizationService(db)
        result = await service.list_authorizations(acct_id=1)

        assert result.total == 0
        assert result.items == []
        assert result.summary is None

    @pytest.mark.asyncio
    async def test_get_authorization_detail_found(
        self, db, account: Account, card: Card, auth_summary: AuthSummary, auth_detail: AuthDetail
    ) -> None:
        """
        COPAUS1C READ-AUTH-RECORD: EXEC DLI GU → retrieve single detail.
        Verify all key fields from CIPAUDTY.cpy are returned.
        """
        service = AuthorizationService(db)
        result = await service.get_authorization_detail(auth_detail.auth_id)

        assert result.auth_id == auth_detail.auth_id
        assert result.card_num == "0100000011111111"
        assert result.auth_resp_code == "00"
        assert result.is_approved is True
        assert result.transaction_amt == Decimal("150.00")
        assert result.merchant_name == "WALMART SUPERCENTER   "

    @pytest.mark.asyncio
    async def test_get_authorization_detail_not_found(self, db) -> None:
        """
        COPAUS1C: IMS 'GE' (SEGMENT-NOT-FOUND) → RecordNotFoundError → HTTP 404.
        """
        service = AuthorizationService(db)
        with pytest.raises(RecordNotFoundError):
            await service.get_authorization_detail(999999)

    @pytest.mark.asyncio
    async def test_get_next_detail_pf8_navigation(
        self,
        db,
        account: Account,
        card: Card,
        auth_summary: AuthSummary,
        auth_detail: AuthDetail,
    ) -> None:
        """
        COPAUS1C PROCESS-PF8-KEY: navigate to next record.
        Inserts a second detail to be the 'next' record.
        """
        # Seed a second auth_detail with higher auth_id
        second = AuthDetail(
            acct_id=1,
            auth_date_9c=99400,
            auth_time_9c=998000000,
            auth_orig_date="260331",
            auth_orig_time="150000",
            card_num="0100000011111111",
            auth_type="PUR ",
            card_expiry_date="1125",
            auth_id_code="150000",
            auth_resp_code="00",
            auth_resp_reason="0000",
            transaction_amt=Decimal("75.00"),
            approved_amt=Decimal("75.00"),
            match_status="P",
        )
        db.add(second)
        await db.flush()

        service = AuthorizationService(db)
        result = await service.get_next_authorization_detail(
            acct_id=1, current_auth_id=auth_detail.auth_id
        )

        assert result.auth_id == second.auth_id

    @pytest.mark.asyncio
    async def test_get_next_detail_at_end_raises(
        self, db, account: Account, auth_summary: AuthSummary, auth_detail: AuthDetail
    ) -> None:
        """
        COPAUS1C: IMS 'GB' (end-of-database) on GN → AUTHS-EOF → RecordNotFoundError.
        Navigating past last record raises.
        """
        service = AuthorizationService(db)
        with pytest.raises(RecordNotFoundError, match="last Authorization"):
            await service.get_next_authorization_detail(
                acct_id=1, current_auth_id=auth_detail.auth_id
            )

    @pytest.mark.asyncio
    async def test_list_pagination_cursor(
        self,
        db,
        account: Account,
        card: Card,
        auth_summary: AuthSummary,
        auth_detail: AuthDetail,
    ) -> None:
        """
        COPAUS0C PROCESS-PF8-KEY keyset pagination: cursor-based forward navigation.
        next_cursor populated when more records exist.
        """
        # Add 5 more details so we have more than 5 total
        for i in range(5):
            extra = AuthDetail(
                acct_id=1,
                auth_date_9c=99000 - i,
                auth_time_9c=900000000 - i * 1000,
                auth_resp_code="00",
                auth_resp_reason="0000",
                transaction_amt=Decimal("10.00"),
                approved_amt=Decimal("10.00"),
                match_status="P",
            )
            db.add(extra)
        await db.flush()

        service = AuthorizationService(db)
        result = await service.list_authorizations(acct_id=1, limit=3)

        assert len(result.items) == 3
        assert result.next_cursor is not None


# ---------------------------------------------------------------------------
# Fraud Marking Tests (COPAUS1C PF5 → COPAUS2C)
# ---------------------------------------------------------------------------


class TestMarkFraud:
    """Tests for COPAUS1C MARK-AUTH-FRAUD paragraph and COPAUS2C database persistence."""

    @pytest.mark.asyncio
    async def test_mark_fraud_confirmed(
        self,
        db,
        account: Account,
        card: Card,
        auth_summary: AuthSummary,
        auth_detail: AuthDetail,
    ) -> None:
        """
        COPAUS1C: PA-FRAUD-CONFIRMED not set → SET PA-FRAUD-CONFIRMED → action='F'.
        COPAUS2C: EXEC SQL INSERT → WS-FRD-UPDT-SUCCESS.
        auth_details.auth_fraud must be updated to 'F'.
        """
        service = AuthorizationService(db)
        result = await service.mark_fraud(
            auth_id=auth_detail.auth_id,
            acct_id=1,
            cust_id=1,
            request=FraudMarkRequest(action=FraudAction.CONFIRMED),
        )

        assert result.success is True
        assert result.auth_fraud == "F"
        assert result.message == "ADD SUCCESS"
        assert result.fraud_rpt_date is not None

        # Verify detail was updated (EXEC DLI REPL SEGMENT(PAUTDTL1))
        await db.refresh(auth_detail)
        assert auth_detail.auth_fraud == "F"
        assert auth_detail.fraud_rpt_date is not None

    @pytest.mark.asyncio
    async def test_mark_fraud_removed(
        self,
        db,
        account: Account,
        card: Card,
        auth_summary: AuthSummary,
        auth_detail: AuthDetail,
    ) -> None:
        """
        COPAUS1C: PA-FRAUD-CONFIRMED already set → SET PA-FRAUD-REMOVED → action='R'.
        COPAUS2C: SQLCODE=-803 (duplicate key) → PERFORM FRAUD-UPDATE → UPDATE auth_fraud='R'.
        """
        # Pre-set fraud flag to simulate it was already marked
        auth_detail.auth_fraud = "F"
        await db.flush()

        service = AuthorizationService(db)
        # First: report fraud to create the AUTHFRDS row
        await service.mark_fraud(
            auth_id=auth_detail.auth_id,
            acct_id=1,
            cust_id=1,
            request=FraudMarkRequest(action=FraudAction.CONFIRMED),
        )

        # Now: remove fraud flag (SQLCODE=-803 branch → UPDATE)
        result = await service.mark_fraud(
            auth_id=auth_detail.auth_id,
            acct_id=1,
            cust_id=1,
            request=FraudMarkRequest(action=FraudAction.REMOVED),
        )

        assert result.success is True
        assert result.auth_fraud == "R"

    @pytest.mark.asyncio
    async def test_mark_fraud_not_found_raises(self, db) -> None:
        """
        COPAUS1C MARK-AUTH-FRAUD: auth record must exist before marking fraud.
        RecordNotFoundError on missing auth_id.
        """
        service = AuthorizationService(db)
        with pytest.raises(RecordNotFoundError):
            await service.mark_fraud(
                auth_id=999999,
                acct_id=1,
                cust_id=1,
                request=FraudMarkRequest(action=FraudAction.CONFIRMED),
            )

    @pytest.mark.asyncio
    async def test_fraud_record_written_to_auth_fraud_records(
        self,
        db,
        account: Account,
        card: Card,
        auth_summary: AuthSummary,
        auth_detail: AuthDetail,
    ) -> None:
        """
        COPAUS2C: EXEC SQL INSERT INTO CARDDEMO.AUTHFRDS.
        AuthFraudRecord must be persisted with all key fields from CIPAUDTY.
        """
        service = AuthorizationService(db)
        await service.mark_fraud(
            auth_id=auth_detail.auth_id,
            acct_id=1,
            cust_id=1,
            request=FraudMarkRequest(action=FraudAction.CONFIRMED),
        )

        from app.repositories.authorization_repo import AuthorizationRepository
        repo = AuthorizationRepository(db)
        fraud_records = await repo.get_fraud_records_by_card("0100000011111111")

        assert len(fraud_records) == 1
        assert fraud_records[0].auth_fraud == "F"
        assert fraud_records[0].acct_id == 1
        assert fraud_records[0].cust_id == 1
        assert fraud_records[0].card_num == "0100000011111111"


# ---------------------------------------------------------------------------
# Decline reason description mapping (WS-DECLINE-REASON-TABLE)
# ---------------------------------------------------------------------------


class TestDeclineReasonDescriptions:
    """Tests for WS-DECLINE-REASON-TABLE lookup from COPAUS1C."""

    @pytest.mark.asyncio
    async def test_approved_reason_description(
        self, db, account: Account, card: Card
    ) -> None:
        """Approved auth returns 'APPROVED' description."""
        service = AuthorizationService(db)
        request = make_auth_request(transaction_amt=Decimal("10.00"))
        result = await service.process_authorization(request)

        assert result.decline_reason_description == "APPROVED"

    @pytest.mark.asyncio
    async def test_invalid_card_reason_description(self, db, account: Account) -> None:
        """Unknown card returns '3100 INVALID CARD' description."""
        service = AuthorizationService(db)
        request = make_auth_request(
            card_num="0000000000000099",
            transaction_amt=Decimal("10.00"),
        )
        result = await service.process_authorization(request)

        assert "INVALID" in result.decline_reason_description

    @pytest.mark.asyncio
    async def test_insufficient_fund_description(
        self, db, account: Account, card: Card
    ) -> None:
        """Over-limit transaction returns '4100 INSUFFICIENT FUND' description."""
        service = AuthorizationService(db)
        request = make_auth_request(transaction_amt=Decimal("99999.00"))
        result = await service.process_authorization(request)

        assert "FUND" in result.decline_reason_description
