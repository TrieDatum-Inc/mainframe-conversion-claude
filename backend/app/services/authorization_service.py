"""
Authorization business logic service.

This module contains ALL business logic translated from COPAUS0C, COPAUS1C,
and COPAUS2C programs. No database calls are made here — only repository calls.

COBOL program → Python method mapping:
  COPAUS0C GATHER-DETAILS          → list_authorization_summaries()
  COPAUS1C POPULATE-AUTH-DETAILS   → get_authorization_detail()
  COPAUS1C MARK-AUTH-FRAUD         → toggle_fraud_flag()
  COPAUS2C MAIN-PARA               → _process_fraud_toggle()
  COPAUS2C FRAUD-UPDATE            → _handle_duplicate_fraud_log()
"""
from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.models.authorization import AuthFraudLog, AuthorizationDetail, AuthorizationSummary
from app.repositories.authorization_repository import AuthorizationRepository
from app.schemas.authorization import (
    AuthDetailResponse,
    AuthFraudLogResponse,
    AuthListItem,
    AuthListResponse,
    AuthSummaryResponse,
    FraudToggleResponse,
    format_fraud_status_display,
    mask_card_number,
    resolve_decline_reason,
)


class AuthorizationService:
    """
    Authorization business logic — translates COPAUS0C/1C/2C PROCEDURE DIVISION
    paragraphs into Python service methods.
    Rule: no SQLAlchemy calls here; only repository method calls.
    """

    def __init__(self, repo: AuthorizationRepository) -> None:
        self.repo = repo

    # -------------------------------------------------------------------------
    # COPAUS0C: GATHER-DETAILS → list browse pattern
    # -------------------------------------------------------------------------

    async def list_authorization_summaries(
        self, page: int, page_size: int
    ) -> dict:
        """
        Paginated list of all authorization summaries.
        Replaces: COPAUS0C IMS browse pattern (GU root, GNP children, 5 per page).
        page_size=5 default maps to COPAUS0C's 5-row screen.
        Returns dict matching the standard pagination envelope.
        """
        items, total_count = await self.repo.list_summaries(page, page_size)
        has_next = (page * page_size) < total_count
        has_previous = page > 1
        return {
            "items": [self._build_summary_response(s) for s in items],
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "has_next": has_next,
            "has_previous": has_previous,
        }

    async def get_authorization_summary(self, account_id: int) -> AuthSummaryResponse:
        """
        Fetch single account authorization summary.
        Replaces: COPAUS0C EXEC DLI GU PAUTSUM0 WHERE(ACCNTID = WS-CARD-RID-ACCT-ID).
        Raises 404 if not found (maps to IMS GE status code).
        """
        summary = await self.repo.get_summary_by_account(account_id)
        if summary is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "AUTH_SUMMARY_NOT_FOUND",
                    "message": f"Authorization summary for account {account_id} not found",
                    "details": [],
                },
            )
        return self._build_summary_response(summary)

    async def list_details_for_account(
        self, account_id: int, page: int, page_size: int
    ) -> AuthListResponse:
        """
        Paginated authorization detail list for a given account.
        Replaces: COPAUS0C PROCESS-PAGE-FORWARD (GNP loop 1..5 per page).
        Validates account summary exists first (IMS parent GU before GNP children).
        Returns AuthListResponse with summary header + paginated detail items.
        """
        summary = await self.repo.get_summary_by_account(account_id)
        if summary is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "AUTH_SUMMARY_NOT_FOUND",
                    "message": f"No authorization record found for account {account_id}",
                    "details": [],
                },
            )

        details, total_count = await self.repo.list_details_by_account(
            account_id, page, page_size
        )
        has_next = (page * page_size) < total_count
        has_previous = page > 1

        list_items = [self._build_list_item(d) for d in details]

        return AuthListResponse(
            summary=self._build_summary_response(summary),
            items=list_items,
            page=page,
            page_size=page_size,
            total_count=total_count,
            has_next=has_next,
            has_previous=has_previous,
        )

    # -------------------------------------------------------------------------
    # COPAUS1C: POPULATE-AUTH-DETAILS
    # -------------------------------------------------------------------------

    async def get_authorization_detail(self, auth_id: int) -> AuthDetailResponse:
        """
        Fetch full authorization detail record for display.
        Replaces: COPAUS1C PROCESS-ENTER-KEY → READ-AUTH-RECORD → POPULATE-AUTH-DETAILS.
        EXEC DLI GNP PAUTDTL1 WHERE(PAUT9CTS = PA-AUTHORIZATION-KEY).
        Resolves decline_reason via SEARCH ALL on inline table (WS-DECLINE-REASON-TABLE).
        Raises 404 if not found (maps to IMS GE after GNP).
        """
        detail = await self.repo.get_detail_by_id(auth_id)
        if detail is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "AUTH_DETAIL_NOT_FOUND",
                    "message": f"Authorization {auth_id} not found",
                    "details": [],
                },
            )
        return self._build_detail_response(detail)

    # -------------------------------------------------------------------------
    # COPAUS1C: MARK-AUTH-FRAUD → COPAUS2C MAIN-PARA (two-phase commit)
    # -------------------------------------------------------------------------

    async def toggle_fraud_flag(
        self, auth_id: int, current_fraud_status: str
    ) -> FraudToggleResponse:
        """
        Toggle fraud status on an authorization detail record.
        Replaces: COPAUS1C MARK-AUTH-FRAUD paragraph + EXEC CICS LINK COPAUS2C.

        3-state cycle (from COPAUS2C business rules):
          N → F (no fraud → fraud confirmed)
          F → R (fraud confirmed → fraud removed)
          R → F (fraud removed → re-confirmed as fraud)

        Two-phase atomic operation (replaces CICS two-phase commit):
          1. Determine new_fraud_status from current state
          2. Upsert auth_fraud_log (replaces COPAUS2C INSERT + SQLCODE -803 UPDATE)
          3. Update authorization_detail.fraud_status (replaces EXEC DLI REPL PAUTDTL1)
          4. Both ops happen in the same DB transaction (session.commit() in get_db())
          If either fails, SQLAlchemy rolls back (replaces EXEC CICS SYNCPOINT ROLLBACK).

        Raises 404 if authorization not found.
        Raises 409 if client-provided current_fraud_status does not match DB state.
        """
        detail = await self.repo.get_detail_by_id(auth_id)
        if detail is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "AUTH_DETAIL_NOT_FOUND",
                    "message": f"Authorization {auth_id} not found",
                    "details": [],
                },
            )

        self._validate_current_fraud_status(detail, current_fraud_status, auth_id)

        new_fraud_status = self._compute_new_fraud_status(detail.fraud_status)
        fraud_flag = new_fraud_status  # 'F' or 'R' — WS-FRD-ACTION in COPAUS2C
        report_date = datetime.now(tz=timezone.utc)

        # Replaces COPAUS2C INSERT + FRAUD-UPDATE on SQLCODE -803
        log_entry = await self.repo.upsert_fraud_log(detail, fraud_flag, report_date)

        # Replaces COPAUS1C UPDATE-AUTH-DETAILS (EXEC DLI REPL PAUTDTL1)
        updated_detail = await self.repo.update_fraud_status(auth_id, new_fraud_status)
        if updated_detail is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error_code": "FRAUD_UPDATE_FAILED",
                    "message": "Failed to update authorization fraud status",
                    "details": [],
                },
            )

        action_message = self._build_fraud_action_message(new_fraud_status, log_entry)

        return FraudToggleResponse(
            auth_id=auth_id,
            previous_fraud_status=detail.fraud_status,
            new_fraud_status=new_fraud_status,
            fraud_status_display=format_fraud_status_display(new_fraud_status),
            fraud_report_date=report_date,
            message=action_message,
        )

    async def get_fraud_logs(self, auth_id: int) -> list[AuthFraudLogResponse]:
        """
        Retrieve fraud audit log for an authorization.
        Replaces: reading CARDDEMO.AUTHFRDS rows for a given card/timestamp key.
        """
        detail = await self.repo.get_detail_by_id(auth_id)
        if detail is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "AUTH_DETAIL_NOT_FOUND",
                    "message": f"Authorization {auth_id} not found",
                    "details": [],
                },
            )
        logs = await self.repo.get_fraud_logs_for_auth(auth_id)
        return [self._build_fraud_log_response(log) for log in logs]

    # -------------------------------------------------------------------------
    # Private helpers — replaces COBOL MOVE / COMPUTE / field-population logic
    # -------------------------------------------------------------------------

    def _build_summary_response(self, summary: AuthorizationSummary) -> AuthSummaryResponse:
        """Build AuthSummaryResponse from ORM model. Maps CIPAUSMY copybook fields."""
        return AuthSummaryResponse(
            account_id=summary.account_id,
            credit_limit=summary.credit_limit,
            cash_limit=summary.cash_limit,
            credit_balance=summary.credit_balance,
            cash_balance=summary.cash_balance,
            approved_auth_count=summary.approved_auth_count,
            declined_auth_count=summary.declined_auth_count,
            approved_auth_amount=summary.approved_auth_amount,
            declined_auth_amount=summary.declined_auth_amount,
        )

    def _build_list_item(self, detail: AuthorizationDetail) -> AuthListItem:
        """
        Build a single list row item.
        Replaces: COPAUS0C POPULATE-AUTH-LIST paragraph fields.
        WS-AUTH-APRV-STAT = 'A' if resp='00' else 'D' (PAPRVnn field).
        """
        approval_status = "A" if detail.is_approved else "D"
        return AuthListItem(
            auth_id=detail.auth_id,
            transaction_id=detail.transaction_id,
            card_number_masked=mask_card_number(detail.card_number),
            auth_date=detail.auth_date,
            auth_time=detail.auth_time,
            auth_type=detail.auth_type,
            approval_status=approval_status,
            match_status=detail.match_status,
            amount=detail.transaction_amount,
            fraud_status=detail.fraud_status,
            fraud_status_display=format_fraud_status_display(detail.fraud_status),
        )

    def _build_detail_response(self, detail: AuthorizationDetail) -> AuthDetailResponse:
        """
        Build AuthDetailResponse from ORM model.
        Replaces: COPAUS1C POPULATE-AUTH-DETAILS paragraph (lines 291-357).
        Key translations:
          AUTHRSPO: 'A' if resp='00' (DFHGREEN), 'D' otherwise (DFHRED)
          AUTHRSNO: resolve_decline_reason() → SEARCH ALL WS-DECLINE-REASON-TAB
          AUTHFRDO: format_fraud_status_display() → 'FRAUD'/'REMOVED'/''
          Card number: mask for display (PCI-DSS)
        """
        approval_status = "A" if detail.is_approved else "D"
        decline_reason = resolve_decline_reason(detail.auth_response_code)
        fraud_display = format_fraud_status_display(detail.fraud_status)

        return AuthDetailResponse(
            auth_id=detail.auth_id,
            account_id=detail.account_id,
            card_number=detail.card_number.strip(),
            card_number_masked=mask_card_number(detail.card_number),
            auth_date=detail.auth_date,
            auth_time=detail.auth_time,
            auth_response_code=detail.auth_response_code,
            approval_status=approval_status,
            decline_reason=decline_reason,
            auth_code=detail.auth_code,
            amount=detail.transaction_amount,
            pos_entry_mode=detail.pos_entry_mode,
            auth_source=detail.auth_source,
            mcc_code=detail.mcc_code,
            card_expiry=detail.card_expiry_date,
            auth_type=detail.auth_type,
            transaction_id=detail.transaction_id,
            match_status=detail.match_status,
            fraud_status=detail.fraud_status,
            fraud_status_display=fraud_display,
            merchant_name=detail.merchant_name,
            merchant_id=detail.merchant_id,
            merchant_city=detail.merchant_city,
            merchant_state=detail.merchant_state,
            merchant_zip=detail.merchant_zip,
            processed_at=detail.processed_at,
            updated_at=detail.updated_at,
        )

    def _build_fraud_log_response(self, log: AuthFraudLog) -> AuthFraudLogResponse:
        """Build fraud log response DTO."""
        return AuthFraudLogResponse(
            log_id=log.log_id,
            auth_id=log.auth_id,
            transaction_id=log.transaction_id,
            card_number_masked=mask_card_number(log.card_number),
            account_id=log.account_id,
            fraud_flag=log.fraud_flag,
            fraud_flag_display="FRAUD CONFIRMED" if log.fraud_flag == "F" else "FRAUD REMOVED",
            fraud_report_date=log.fraud_report_date,
            auth_response_code=log.auth_response_code,
            auth_amount=log.auth_amount,
            merchant_name=log.merchant_name,
            merchant_id=log.merchant_id,
            logged_at=log.logged_at,
        )

    def _validate_current_fraud_status(
        self,
        detail: AuthorizationDetail,
        client_status: str,
        auth_id: int,
    ) -> None:
        """
        Validate client-provided current_fraud_status matches DB state.
        Prevents double-toggle on stale page refresh.
        Returns without error if valid; raises 409 if mismatch.
        """
        if detail.fraud_status != client_status:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error_code": "FRAUD_STATUS_MISMATCH",
                    "message": (
                        f"Authorization {auth_id} fraud status is '{detail.fraud_status}', "
                        f"but client sent '{client_status}'. Refresh and retry."
                    ),
                    "details": [],
                },
            )

    def _compute_new_fraud_status(self, current: str) -> str:
        """
        Compute new fraud status from current state.
        Replaces: COPAUS1C MARK-AUTH-FRAUD IF/ELSE logic + COPAUS2C WS-FRD-ACTION.
        3-state cycle: N→F, F→R, R→F
        From spec: 'If current fraud_status=N → set to F'
                   'If current fraud_status=F → set to R'
                   'If current fraud_status=R → set to F'
        """
        transitions: dict[str, str] = {"N": "F", "F": "R", "R": "F"}
        return transitions.get(current, "F")

    def _build_fraud_action_message(
        self, new_status: str, log_entry: AuthFraudLog
    ) -> str:
        """
        Build action message for fraud toggle response.
        Replaces: COPAUS2C WS-FRD-ACT-MSG = 'ADD SUCCESS' / 'UPDT SUCCESS'.
        """
        if new_status == "F":
            return "ADD SUCCESS"
        return "UPDT SUCCESS"
