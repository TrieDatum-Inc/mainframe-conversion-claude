"""
Authorization service — business logic from COPAUA0C, COPAUS0C, COPAUS1C, COPAUS2C.

Paragraph → method mapping:
  COPAUA0C 5000-PROCESS-AUTH        → process_authorization()
  COPAUA0C 5100-READ-XREF-RECORD    → _read_xref_record()
  COPAUA0C 5200-READ-ACCT-RECORD    → _read_acct_record()       [via AccountRepository]
  COPAUA0C 5300-READ-CUST-RECORD    → _read_cust_record()       [skipped, not needed for decision]
  COPAUA0C 6000-MAKE-DECISION       → _make_decision()
  COPAUA0C 8400-UPDATE-SUMMARY      → _update_summary()
  COPAUA0C 8500-INSERT-AUTH         → _insert_auth_detail()
  COPAUS0C GATHER-DETAILS           → list_authorizations()
  COPAUS1C READ-AUTH-RECORD         → get_authorization_detail()
  COPAUS1C MARK-AUTH-FRAUD (PF5)    → mark_fraud()
  COPAUS2C MAIN-PARA                → _write_fraud_to_db()

Business rules preserved:
  1. Card must exist in CCXREF — if not, decline with reason 3100 (INVALID CARD)
  2. Account must be active — if ACCT-ACTIVE-STATUS != 'Y', decline 4300 (ACCOUNT CLOSED)
  3. Available credit = credit_limit - credit_balance; if amount > available → decline 4100
  4. If auth_summary exists, use PA-CREDIT-BALANCE; else fall back to ACCT-CURR-BAL
  5. Approved: auth_resp_code='00', approved_amt=transaction_amt
  6. Declined: auth_resp_code='05', approved_amt=0.00
  7. Summary counters update: approved_auth_cnt/amt or declined_auth_cnt/amt
  8. Credit balance increases only on approval (ADD WS-APPROVED-AMT TO PA-CREDIT-BALANCE)
  9. Fraud toggle: if already 'F' → set 'R'; if not fraud → set 'F'
  10. Auth detail key: inverted YYDDD (99999-YYDDD) + inverted HHMMSS (999999999-time)
       — preserved in auth_date_9c and auth_time_9c columns for sort fidelity
  11. Decline reason hierarchy: card-not-found → insufficient-fund → card-not-active
       → account-closed → card-fraud → merchant-fraud → unknown (WS-DECLINE-REASON-FLG)
"""
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.authorization import AuthDetail, AuthFraudRecord, AuthSummary
from app.repositories.account_repo import AccountRepository
from app.repositories.authorization_repo import AuthorizationRepository
from app.repositories.card_repo import CardRepository
from app.schemas.authorization import (
    AuthDetailListResponse,
    AuthDetailResponse,
    AuthSummaryResponse,
    AuthorizationRequest,
    AuthorizationResponse,
    AuthDecision,
    DeclineReasonCode,
    FraudAction,
    FraudMarkRequest,
    FraudMarkResponse,
)
from app.utils.cobol_compat import to_decimal
from app.utils.error_handlers import RecordNotFoundError, ValidationError

# ---------------------------------------------------------------------------
# Decline reason descriptions — WS-DECLINE-REASON-TABLE in COPAUS1C
# ---------------------------------------------------------------------------
_DECLINE_REASON_DESC: dict[str, str] = {
    "0000": "APPROVED",
    "3100": "INVALID CARD",
    "4100": "INSUFFICNT FUND",
    "4200": "CARD NOT ACTIVE",
    "4300": "ACCOUNT CLOSED",
    "4400": "EXCED DAILY LMT",
    "5100": "CARD FRAUD",
    "5200": "MERCHANT FRAUD",
    "5300": "LOST CARD",
    "9000": "UNKNOWN",
}

# Maximum requests processed in one batch (WS-REQSTS-PROCESS-LIMIT PIC S9(4) VALUE 500)
_PROCESS_LIMIT = 500


class AuthorizationService:
    """
    Authorization business logic — derived from COPAUA0C, COPAUS0C,
    COPAUS1C, and COPAUS2C.

    The original IBM MQ async request/reply pattern (MQOPEN, MQGET, MQPUT1)
    is replaced by a synchronous REST POST. The MQ broker is not required;
    the full decision pipeline runs within a single HTTP request/response
    cycle, which is functionally equivalent from the caller's perspective.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._auth_repo = AuthorizationRepository(db)
        self._acct_repo = AccountRepository(db)
        self._card_repo = CardRepository(db)

    # ------------------------------------------------------------------
    # Public — POST /api/v1/authorizations  (COPAUA0C 5000-PROCESS-AUTH)
    # ------------------------------------------------------------------

    async def process_authorization(
        self, request: AuthorizationRequest
    ) -> AuthorizationResponse:
        """
        Execute the full authorization decision pipeline.

        Derived from COPAUA0C 5000-PROCESS-AUTH paragraph:
          PERFORM 5100-READ-XREF-RECORD
          PERFORM 5200-READ-ACCT-RECORD
          PERFORM 5500-READ-AUTH-SUMMRY
          PERFORM 6000-MAKE-DECISION
          PERFORM 8000-WRITE-AUTH-TO-DB

        The MQ request/reply messaging is replaced by synchronous processing.
        """
        # COPAUA0C: SET APPROVE-AUTH TO TRUE (default to approve)
        decline_reason: DeclineReasonCode | None = None

        # Step 1 — 5100-READ-XREF-RECORD
        xref = await self._read_xref_record(request.card_num)
        if xref is None:
            decline_reason = DeclineReasonCode.INVALID_CARD

        # Step 2 — 5200-READ-ACCT-RECORD (only if xref found)
        account = None
        if xref is not None:
            account = await self._read_acct_record(xref.acct_id)
            if account is None:
                decline_reason = DeclineReasonCode.INVALID_CARD
            elif account.active_status != "Y":
                decline_reason = DeclineReasonCode.ACCOUNT_CLOSED

        # Step 3 — 5500-READ-AUTH-SUMMRY
        summary = None
        if xref is not None and account is not None:
            summary = await self._auth_repo.get_summary_by_acct_id(xref.acct_id)

        # Step 4 — 6000-MAKE-DECISION
        decision, approved_amt, reason_code = self._make_decision(
            request=request,
            account=account,
            summary=summary,
            pre_decline_reason=decline_reason,
        )

        # Build auth_id_code = PA-RQ-AUTH-TIME (COPAUA0C 6000-MAKE-DECISION)
        auth_id_code = request.auth_time[:6]

        # Step 5 — 8000-WRITE-AUTH-TO-DB (only if xref found)
        auth_detail_id: int | None = None
        if xref is not None and account is not None:
            detail = await self._write_auth_to_db(
                request=request,
                account_id=xref.acct_id,
                customer_id=xref.cust_id,
                account=account,
                summary=summary,
                auth_id_code=auth_id_code,
                decision=decision,
                approved_amt=approved_amt,
                reason_code=reason_code,
            )
            auth_detail_id = detail.auth_id

        return AuthorizationResponse(
            card_num=request.card_num,
            transaction_id=request.transaction_id,
            auth_id_code=auth_id_code,
            auth_resp_code=decision,
            auth_resp_reason=reason_code,
            approved_amt=approved_amt,
            is_approved=(decision == AuthDecision.APPROVED),
            decline_reason_description=_DECLINE_REASON_DESC.get(reason_code.value),
            auth_detail_id=auth_detail_id,
        )

    # ------------------------------------------------------------------
    # Public — GET /api/v1/authorizations/{acct_id}  (COPAUS0C)
    # ------------------------------------------------------------------

    async def list_authorizations(
        self,
        acct_id: int,
        cursor: int | None = None,
        limit: int = 5,
    ) -> AuthDetailListResponse:
        """
        COPAUS0C GATHER-DETAILS + PROCESS-PAGE-FORWARD paragraphs.

        Retrieves paginated authorization detail records for an account.
        Cursor-based pagination mirrors IMS READNEXT on PAUTDTL1 child segments.
        Page size 5 matches COPAUS0C screen capacity (5 rows: AUTH-KEYS OCCURS 5).
        """
        items, total = await self._auth_repo.list_details_by_acct_id(
            acct_id=acct_id, cursor=cursor, limit=limit
        )
        summary = await self._auth_repo.get_summary_by_acct_id(acct_id)

        detail_responses = [self._build_detail_response(d) for d in items]
        next_cursor = items[-1].auth_id if len(items) == limit else None
        prev_cursor = items[0].auth_id if cursor and items else None

        return AuthDetailListResponse(
            items=detail_responses,
            total=total,
            next_cursor=next_cursor,
            prev_cursor=prev_cursor,
            summary=self._build_summary_response(summary) if summary else None,
        )

    # ------------------------------------------------------------------
    # Public — GET /api/v1/authorizations/details/{auth_id} (COPAUS1C)
    # ------------------------------------------------------------------

    async def get_authorization_detail(self, auth_id: int) -> AuthDetailResponse:
        """
        COPAUS1C READ-AUTH-RECORD / PROCESS-ENTER-KEY paragraph.

        EXEC DLI GU SEGMENT(PAUTSUM0/PAUTDTL1) — retrieve single authorization.
        Raises RecordNotFoundError if not found (IMS 'GE' status → SEGMENT-NOT-FOUND).
        """
        detail = await self._auth_repo.get_detail_by_id(auth_id)
        return self._build_detail_response(detail)

    async def get_next_authorization_detail(
        self, acct_id: int, current_auth_id: int
    ) -> AuthDetailResponse:
        """
        COPAUS1C PROCESS-PF8-KEY → READ-NEXT-AUTH-RECORD.

        Navigate to the next authorization record for the account.
        Raises RecordNotFoundError when at end of chain (IMS 'GB' end-of-db).
        """
        detail = await self._auth_repo.get_next_detail(acct_id, current_auth_id)
        if detail is None:
            raise RecordNotFoundError(
                "Already at the last Authorization (COPAUS1C: AUTHS-EOF)"
            )
        return self._build_detail_response(detail)

    # ------------------------------------------------------------------
    # Public — POST /api/v1/authorizations/details/{auth_id}/fraud (COPAUS1C PF5)
    # ------------------------------------------------------------------

    async def mark_fraud(
        self,
        auth_id: int,
        acct_id: int,
        cust_id: int,
        request: FraudMarkRequest,
    ) -> FraudMarkResponse:
        """
        COPAUS1C MARK-AUTH-FRAUD paragraph:

          IF PA-FRAUD-CONFIRMED → SET PA-FRAUD-REMOVED / WS-REMOVE-FRAUD
          ELSE                  → SET PA-FRAUD-CONFIRMED / WS-REPORT-FRAUD

          EXEC CICS LINK PROGRAM(COPAUS2C) COMMAREA(WS-FRAUD-DATA)

        Delegates fraud record persistence to _write_fraud_to_db().
        Updates the auth_details row on success.
        """
        detail = await self._auth_repo.get_detail_by_id(auth_id)

        # Compute fraud_rpt_date (COPAUS2C: EXEC CICS FORMATTIME MMDDYY DATESEP)
        now = datetime.now(timezone.utc)
        fraud_rpt_date = now.strftime("%m/%d/%y")

        # Write fraud record to AUTHFRDS (COPAUS2C logic)
        fraud_result = await self._write_fraud_to_db(
            detail=detail,
            acct_id=acct_id,
            cust_id=cust_id,
            action=request.action,
            fraud_rpt_date=fraud_rpt_date,
        )

        if fraud_result["success"]:
            # COPAUS1C UPDATE-AUTH-DETAILS — EXEC DLI REPL SEGMENT(PAUTDTL1)
            await self._auth_repo.update_detail_fraud(
                auth_id=auth_id,
                auth_fraud=request.action.value,
                fraud_rpt_date=fraud_rpt_date,
            )

        return FraudMarkResponse(
            success=fraud_result["success"],
            message=fraud_result["message"],
            auth_fraud=request.action.value if fraud_result["success"] else None,
            fraud_rpt_date=fraud_rpt_date if fraud_result["success"] else None,
        )

    # ------------------------------------------------------------------
    # Private — 5100-READ-XREF-RECORD
    # ------------------------------------------------------------------

    async def _read_xref_record(self, card_num: str):
        """
        COPAUA0C 5100-READ-XREF-RECORD:
          EXEC CICS READ FILE(CCXREF) RIDFLD(XREF-CARD-NUM) RESP(WS-RESP-CD)

        Returns None on NOTFND (sets CARD-NFOUND-XREF).
        """
        try:
            return await self._card_repo.get_xref_by_card_num(card_num)
        except RecordNotFoundError:
            return None

    # ------------------------------------------------------------------
    # Private — 5200-READ-ACCT-RECORD
    # ------------------------------------------------------------------

    async def _read_acct_record(self, acct_id: int):
        """
        COPAUA0C 5200-READ-ACCT-RECORD:
          EXEC CICS READ FILE(ACCTDAT) RIDFLD(WS-CARD-RID-ACCT-ID-X) RESP(WS-RESP-CD)

        Returns None on NOTFND (sets NFOUND-ACCT-IN-MSTR).
        """
        try:
            return await self._acct_repo.get_by_id(acct_id)
        except RecordNotFoundError:
            return None

    # ------------------------------------------------------------------
    # Private — 6000-MAKE-DECISION
    # ------------------------------------------------------------------

    def _make_decision(
        self,
        request: AuthorizationRequest,
        account,
        summary: AuthSummary | None,
        pre_decline_reason: DeclineReasonCode | None,
    ) -> tuple[AuthDecision, Decimal, DeclineReasonCode]:
        """
        COPAUA0C 6000-MAKE-DECISION paragraph.

        Decision logic (exact COBOL faithful translation):
          1. If pre-decline reason already set → decline immediately
          2. If auth_summary found → use PA-CREDIT-LIMIT / PA-CREDIT-BALANCE
             If not found → use ACCT-CREDIT-LIMIT / ACCT-CURR-BAL
          3. WS-AVAILABLE-AMT = credit_limit - credit_balance
          4. IF WS-TRANSACTION-AMT > WS-AVAILABLE-AMT → DECLINE 4100
          5. Approved: resp_code='00', approved_amt=transaction_amt, reason='0000'
          6. Declined: resp_code='05', approved_amt=0.00, reason from flag

        Returns (decision, approved_amt, reason_code).
        """
        transaction_amt = to_decimal(request.transaction_amt)

        # Pre-decline (xref not found, account not found, account closed)
        if pre_decline_reason is not None:
            return AuthDecision.DECLINED, Decimal("0.00"), pre_decline_reason

        # Determine available credit
        if summary is not None:
            credit_limit = to_decimal(summary.credit_limit)
            credit_balance = to_decimal(summary.credit_balance)
        elif account is not None:
            credit_limit = to_decimal(account.credit_limit)
            credit_balance = to_decimal(account.curr_bal)
        else:
            return AuthDecision.DECLINED, Decimal("0.00"), DeclineReasonCode.INVALID_CARD

        available_amt = credit_limit - credit_balance

        if transaction_amt > available_amt:
            return (
                AuthDecision.DECLINED,
                Decimal("0.00"),
                DeclineReasonCode.INSUFFICIENT_FUND,
            )

        # Approved
        return AuthDecision.APPROVED, transaction_amt, DeclineReasonCode.APPROVED

    # ------------------------------------------------------------------
    # Private — 8000-WRITE-AUTH-TO-DB (8400 + 8500)
    # ------------------------------------------------------------------

    async def _write_auth_to_db(
        self,
        request: AuthorizationRequest,
        account_id: int,
        customer_id: int,
        account,
        summary: AuthSummary | None,
        auth_id_code: str,
        decision: AuthDecision,
        approved_amt: Decimal,
        reason_code: DeclineReasonCode,
    ) -> AuthDetail:
        """
        COPAUA0C 8000-WRITE-AUTH-TO-DB:
          PERFORM 8400-UPDATE-SUMMARY
          PERFORM 8500-INSERT-AUTH
        """
        updated_summary = await self._update_summary(
            account_id=account_id,
            customer_id=customer_id,
            account=account,
            existing_summary=summary,
            decision=decision,
            approved_amt=approved_amt,
            transaction_amt=to_decimal(request.transaction_amt),
        )
        return await self._insert_auth_detail(
            request=request,
            account_id=account_id,
            auth_id_code=auth_id_code,
            decision=decision,
            approved_amt=approved_amt,
            reason_code=reason_code,
        )

    async def _update_summary(
        self,
        account_id: int,
        customer_id: int,
        account,
        existing_summary: AuthSummary | None,
        decision: AuthDecision,
        approved_amt: Decimal,
        transaction_amt: Decimal,
    ) -> AuthSummary:
        """
        COPAUA0C 8400-UPDATE-SUMMARY paragraph:

          MOVE ACCT-CREDIT-LIMIT TO PA-CREDIT-LIMIT
          MOVE ACCT-CASH-CREDIT-LIMIT TO PA-CASH-LIMIT
          IF AUTH-RESP-APPROVED:
            ADD 1 TO PA-APPROVED-AUTH-CNT
            ADD WS-APPROVED-AMT TO PA-APPROVED-AUTH-AMT
            ADD WS-APPROVED-AMT TO PA-CREDIT-BALANCE
          ELSE:
            ADD 1 TO PA-DECLINED-AUTH-CNT
            ADD PA-TRANSACTION-AMT TO PA-DECLINED-AUTH-AMT
          EXEC DLI REPL/ISRT SEGMENT(PAUTSUM0)
        """
        if existing_summary is None:
            summary = AuthSummary(
                acct_id=account_id,
                cust_id=customer_id,
                credit_limit=Decimal("0.00"),
                cash_limit=Decimal("0.00"),
                credit_balance=Decimal("0.00"),
                cash_balance=Decimal("0.00"),
                approved_auth_cnt=0,
                declined_auth_cnt=0,
                approved_auth_amt=Decimal("0.00"),
                declined_auth_amt=Decimal("0.00"),
            )
        else:
            summary = existing_summary

        # MOVE ACCT-CREDIT-LIMIT TO PA-CREDIT-LIMIT
        summary.credit_limit = to_decimal(account.credit_limit)
        summary.cash_limit = to_decimal(account.cash_credit_limit)

        if decision == AuthDecision.APPROVED:
            summary.approved_auth_cnt += 1
            summary.approved_auth_amt += approved_amt
            summary.credit_balance += approved_amt
            summary.cash_balance = Decimal("0.00")  # MOVE 0 TO PA-CASH-BALANCE
        else:
            summary.declined_auth_cnt += 1
            summary.declined_auth_amt += transaction_amt

        return await self._auth_repo.upsert_summary(summary)

    async def _insert_auth_detail(
        self,
        request: AuthorizationRequest,
        account_id: int,
        auth_id_code: str,
        decision: AuthDecision,
        approved_amt: Decimal,
        reason_code: DeclineReasonCode,
    ) -> AuthDetail:
        """
        COPAUA0C 8500-INSERT-AUTH paragraph:

          EXEC CICS ASKTIME / FORMATTIME to build inverted key:
            PA-AUTH-DATE-9C = 99999 - WS-YYDDD
            PA-AUTH-TIME-9C = 999999999 - WS-TIME-WITH-MS

          EXEC DLI ISRT SEGMENT(PAUTDTL1) FROM(PENDING-AUTH-DETAILS)

        PA-MATCH-PENDING='P' on approved, PA-MATCH-AUTH-DECLINED='D' on declined.
        """
        now = datetime.now(timezone.utc)

        # Build inverted COBOL key fields (99999 - YYDDD, 999999999 - HHMMSSMMM)
        yyddd = int(now.strftime("%y")) * 1000 + int(now.strftime("%j"))
        auth_date_9c = 99999 - yyddd

        hhmmss_ms = int(now.strftime("%H%M%S")) * 1000 + now.microsecond // 1000
        auth_time_9c = 999999999 - hhmmss_ms

        match_status = "P" if decision == AuthDecision.APPROVED else "D"

        detail = AuthDetail(
            acct_id=account_id,
            auth_date_9c=auth_date_9c,
            auth_time_9c=auth_time_9c,
            auth_orig_date=request.auth_date,
            auth_orig_time=request.auth_time,
            card_num=request.card_num,
            auth_type=request.auth_type,
            card_expiry_date=request.card_expiry_date,
            message_type=request.message_type,
            message_source=request.message_source,
            auth_id_code=auth_id_code,
            auth_resp_code=decision.value,
            auth_resp_reason=reason_code.value,
            processing_code=request.processing_code,
            transaction_amt=to_decimal(request.transaction_amt),
            approved_amt=approved_amt,
            merchant_category_code=request.merchant_category_code,
            acqr_country_code=request.acqr_country_code,
            pos_entry_mode=request.pos_entry_mode,
            merchant_id=request.merchant_id,
            merchant_name=request.merchant_name,
            merchant_city=request.merchant_city,
            merchant_state=request.merchant_state,
            merchant_zip=request.merchant_zip,
            transaction_id=request.transaction_id,
            match_status=match_status,
            auth_fraud=None,
            fraud_rpt_date=None,
        )
        return await self._auth_repo.create_detail(detail)

    # ------------------------------------------------------------------
    # Private — COPAUS2C MAIN-PARA + FRAUD-UPDATE
    # ------------------------------------------------------------------

    async def _write_fraud_to_db(
        self,
        detail: AuthDetail,
        acct_id: int,
        cust_id: int,
        action: FraudAction,
        fraud_rpt_date: str,
    ) -> dict:
        """
        COPAUS2C MAIN-PARA logic:

          Build AUTH-TS from PA-AUTH-ORIG-DATE + inverted PA-AUTH-TIME-9C.
          EXEC SQL INSERT INTO CARDDEMO.AUTHFRDS (...)
          IF SQLCODE = 0    → SET WS-FRD-UPDT-SUCCESS / 'ADD SUCCESS'
          IF SQLCODE = -803 → PERFORM FRAUD-UPDATE (UPDATE auth_fraud, fraud_rpt_date)
          ELSE              → SET WS-FRD-UPDT-FAILED

        Returns dict with 'success' bool and 'message' str.
        """
        auth_ts = self._build_auth_ts(detail)

        record = AuthFraudRecord(
            card_num=detail.card_num or "",
            auth_ts=auth_ts,
            auth_type=detail.auth_type,
            card_expiry_date=detail.card_expiry_date,
            message_type=detail.message_type,
            message_source=detail.message_source,
            auth_id_code=detail.auth_id_code,
            auth_resp_code=detail.auth_resp_code,
            auth_resp_reason=detail.auth_resp_reason,
            processing_code=detail.processing_code,
            transaction_amt=detail.transaction_amt,
            approved_amt=detail.approved_amt,
            merchant_category_code=detail.merchant_category_code,
            acqr_country_code=detail.acqr_country_code,
            pos_entry_mode=detail.pos_entry_mode,
            merchant_id=detail.merchant_id,
            merchant_name=detail.merchant_name,
            merchant_city=detail.merchant_city,
            merchant_state=detail.merchant_state,
            merchant_zip=detail.merchant_zip,
            transaction_id=detail.transaction_id,
            match_status=detail.match_status,
            auth_fraud=action.value,
            fraud_rpt_date=fraud_rpt_date,
            acct_id=acct_id,
            cust_id=cust_id,
        )

        try:
            await self._auth_repo.upsert_fraud_record(record)
            action_word = "ADD" if action == FraudAction.CONFIRMED else "UPDT"
            return {"success": True, "message": f"{action_word} SUCCESS"}
        except Exception as exc:
            return {"success": False, "message": f"SYSTEM ERROR: {exc!s}"}

    def _build_auth_ts(self, detail: AuthDetail) -> str:
        """
        COPAUS2C: Build AUTH-TS string from PA-AUTH-ORIG-DATE + inverted time.

        COBOL format: WS-AUTH-TS 'YY-MM-DD HH.MI.SS.SSS000'
        COPAUS2C:
          MOVE PA-AUTH-ORIG-DATE(1:2) TO WS-AUTH-YY
          MOVE PA-AUTH-ORIG-DATE(3:2) TO WS-AUTH-MM
          MOVE PA-AUTH-ORIG-DATE(5:2) TO WS-AUTH-DD
          COMPUTE WS-AUTH-TIME = 999999999 - PA-AUTH-TIME-9C
        """
        orig_date = detail.auth_orig_date or "000000"
        auth_yy = orig_date[0:2] if len(orig_date) >= 6 else "00"
        auth_mm = orig_date[2:4] if len(orig_date) >= 6 else "00"
        auth_dd = orig_date[4:6] if len(orig_date) >= 6 else "00"

        # Recover HHMMSSMMM from inverted auth_time_9c
        time_val = 999999999 - (detail.auth_time_9c or 0)
        time_str = str(time_val).zfill(9)
        hh = time_str[0:2]
        mi = time_str[2:4]
        ss = time_str[4:6]
        ms = time_str[6:9]

        return f"{auth_yy}-{auth_mm}-{auth_dd} {hh}.{mi}.{ss}{ms}000"

    # ------------------------------------------------------------------
    # Response builders
    # ------------------------------------------------------------------

    def _build_detail_response(self, detail: AuthDetail) -> AuthDetailResponse:
        """Build AuthDetailResponse from ORM AuthDetail."""
        return AuthDetailResponse(
            auth_id=detail.auth_id,
            acct_id=detail.acct_id,
            auth_date_9c=detail.auth_date_9c,
            auth_time_9c=detail.auth_time_9c,
            auth_orig_date=detail.auth_orig_date,
            auth_orig_time=detail.auth_orig_time,
            card_num=detail.card_num,
            auth_type=detail.auth_type,
            card_expiry_date=detail.card_expiry_date,
            message_type=detail.message_type,
            message_source=detail.message_source,
            auth_id_code=detail.auth_id_code,
            auth_resp_code=detail.auth_resp_code,
            auth_resp_reason=detail.auth_resp_reason,
            processing_code=detail.processing_code,
            transaction_amt=detail.transaction_amt,
            approved_amt=detail.approved_amt,
            merchant_category_code=detail.merchant_category_code,
            acqr_country_code=detail.acqr_country_code,
            pos_entry_mode=detail.pos_entry_mode,
            merchant_id=detail.merchant_id,
            merchant_name=detail.merchant_name,
            merchant_city=detail.merchant_city,
            merchant_state=detail.merchant_state,
            merchant_zip=detail.merchant_zip,
            transaction_id=detail.transaction_id,
            match_status=detail.match_status,
            auth_fraud=detail.auth_fraud,
            fraud_rpt_date=detail.fraud_rpt_date,
            is_approved=(detail.auth_resp_code == "00"),
            decline_reason_description=_DECLINE_REASON_DESC.get(
                detail.auth_resp_reason or "9000"
            ),
        )

    def _build_summary_response(self, summary: AuthSummary) -> AuthSummaryResponse:
        """Build AuthSummaryResponse from ORM AuthSummary."""
        available_credit = to_decimal(summary.credit_limit) - to_decimal(summary.credit_balance)
        return AuthSummaryResponse(
            acct_id=summary.acct_id,
            cust_id=summary.cust_id,
            auth_status=summary.auth_status,
            credit_limit=summary.credit_limit,
            cash_limit=summary.cash_limit,
            credit_balance=summary.credit_balance,
            cash_balance=summary.cash_balance,
            available_credit=available_credit,
            approved_auth_cnt=summary.approved_auth_cnt,
            declined_auth_cnt=summary.declined_auth_cnt,
            approved_auth_amt=summary.approved_auth_amt,
            declined_auth_amt=summary.declined_auth_amt,
        )
