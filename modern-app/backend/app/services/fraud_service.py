"""
Fraud management service.

Preserves the COBOL COPAUS2C fraud mark/remove logic:
- 'mark' action  → INSERT INTO AUTHFRDS (new fraud record)
- 'remove' action → UPDATE AUTHFRDS SET AUTH_FRAUD='R', FRAUD_RPT_DATE=today

COBOL COPAUS2C time reversal formula (not needed in Python — we store actual timestamps):
  WS-AUTH-TIME = 999999999 - PA-AUTH-TIME-9C
This was needed to un-encode the IMS 9-complement timestamp. Here we store real dates.

Return status mapping:
  WS-FRD-UPDT-SUCCESS ('S') → success=True
  WS-FRD-UPDT-FAILED  ('F') → success=False
"""

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.authorization import AuthorizationDetail, AuthorizationSummary
from app.models.fraud import FraudRecord
from app.schemas.fraud import FraudActionRequest, FraudActionResponse

FRAUD_FLAG_CONFIRMED = "F"
FRAUD_FLAG_REMOVED = "R"


class FraudService:
    """
    Business logic for fraud flag management.

    Wraps COPAUS2C DB2 INSERT/UPDATE operations.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def toggle_fraud(
        self, detail_id: int, request: FraudActionRequest
    ) -> FraudActionResponse:
        """
        Mark or remove a fraud flag on an authorization detail.

        COBOL COPAUS2C logic:
        - action='mark'   → INSERT INTO AUTHFRDS with AUTH_FRAUD='F'
        - action='remove' → UPDATE AUTHFRDS SET AUTH_FRAUD='R', FRAUD_RPT_DATE=today

        Returns FraudActionResponse with success status and current state.
        """
        detail = await self._require_detail(detail_id)
        summary = await self._require_summary(detail.summary_id)

        fraud_flag = FRAUD_FLAG_CONFIRMED if request.action == "mark" else FRAUD_FLAG_REMOVED
        today = date.today()

        existing_fraud = await self._find_existing_fraud_record(detail)

        if existing_fraud is None:
            return await self._create_fraud_record(
                detail, summary, fraud_flag, today
            )

        return await self._update_fraud_record(existing_fraud, detail, fraud_flag, today)

    async def _create_fraud_record(
        self,
        detail: AuthorizationDetail,
        summary: AuthorizationSummary,
        fraud_flag: str,
        report_date: date,
    ) -> FraudActionResponse:
        """
        INSERT new fraud record.

        COBOL COPAUS2C: INSERT INTO AUTHFRDS — called when no existing record.
        """
        auth_timestamp = datetime.combine(detail.auth_date, detail.auth_time)

        fraud_record = FraudRecord(
            card_number=detail.card_number,
            auth_timestamp=auth_timestamp,
            fraud_flag=fraud_flag,
            fraud_report_date=report_date,
            match_status=detail.match_status,
            account_id=summary.account_id,
            customer_id=summary.customer_id,
            auth_detail_id=detail.id,
        )
        self.db.add(fraud_record)

        detail.fraud_status = fraud_flag
        detail.fraud_report_date = report_date

        await self.db.flush()

        action_label = "marked as fraud" if fraud_flag == FRAUD_FLAG_CONFIRMED else "fraud removed"
        return FraudActionResponse(
            success=True,
            action=fraud_flag,
            fraud_flag=fraud_flag,
            fraud_report_date=report_date,
            message=f"Authorization {detail.transaction_id} has been {action_label}",
        )

    async def _update_fraud_record(
        self,
        fraud_record: FraudRecord,
        detail: AuthorizationDetail,
        fraud_flag: str,
        report_date: date,
    ) -> FraudActionResponse:
        """
        UPDATE existing fraud record.

        COBOL COPAUS2C: UPDATE AUTHFRDS SET AUTH_FRAUD=?, FRAUD_RPT_DATE=?
        """
        fraud_record.fraud_flag = fraud_flag
        fraud_record.fraud_report_date = report_date

        detail.fraud_status = fraud_flag
        detail.fraud_report_date = report_date

        await self.db.flush()

        action_label = "marked as fraud" if fraud_flag == FRAUD_FLAG_CONFIRMED else "fraud removed"
        return FraudActionResponse(
            success=True,
            action=fraud_flag,
            fraud_flag=fraud_flag,
            fraud_report_date=report_date,
            message=f"Authorization {detail.transaction_id} has been {action_label}",
        )

    async def _find_existing_fraud_record(
        self, detail: AuthorizationDetail
    ) -> FraudRecord | None:
        """Look up existing fraud record by (card_number, auth_timestamp)."""
        auth_timestamp = datetime.combine(detail.auth_date, detail.auth_time)
        stmt = select(FraudRecord).where(
            FraudRecord.card_number == detail.card_number,
            FraudRecord.auth_timestamp == auth_timestamp,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _require_detail(self, detail_id: int) -> AuthorizationDetail:
        """Fetch authorization detail or raise 404."""
        stmt = select(AuthorizationDetail).where(AuthorizationDetail.id == detail_id)
        result = await self.db.execute(stmt)
        detail = result.scalar_one_or_none()

        if detail is None:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=404,
                detail=f"Authorization detail {detail_id} not found",
            )
        return detail

    async def _require_summary(self, summary_id: int) -> AuthorizationSummary:
        """Fetch authorization summary or raise 404."""
        stmt = select(AuthorizationSummary).where(
            AuthorizationSummary.id == summary_id
        )
        result = await self.db.execute(stmt)
        summary = result.scalar_one_or_none()

        if summary is None:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=404, detail=f"Authorization summary {summary_id} not found"
            )
        return summary
