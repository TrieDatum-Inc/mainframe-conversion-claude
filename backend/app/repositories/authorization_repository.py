"""
Authorization data access repository.

Replaces all IMS DLI commands from COPAUS0C/COPAUS1C and DB2 SQL from COPAUS2C.
All database operations are isolated here — services must not call SQLAlchemy directly.

COBOL → Python mapping:
  EXEC DLI GU PAUTSUM0 WHERE(ACCNTID=x) → get_summary_by_account()
  EXEC DLI GNP PAUTDTL1 (5 per page)   → list_details_by_account() paginated
  EXEC DLI GNP PAUTDTL1 WHERE(key=x)   → get_detail_by_id()
  EXEC DLI REPL PAUTDTL1               → update_fraud_status() (part of toggle_fraud_flag)
  EXEC SQL INSERT CARDDEMO.AUTHFRDS     → insert_fraud_log()
  EXEC SQL UPDATE CARDDEMO.AUTHFRDS     → upsert_fraud_log() (on -803 duplicate)
"""
from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.authorization import AuthFraudLog, AuthorizationDetail, AuthorizationSummary


class AuthorizationRepository:
    """
    Repository for all authorization-related database operations.
    Follows the pattern: thin SQL layer, no business logic.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # -------------------------------------------------------------------------
    # Summary operations — replaces EXEC DLI GU PAUTSUM0
    # -------------------------------------------------------------------------

    async def get_summary_by_account(self, account_id: int) -> AuthorizationSummary | None:
        """
        Read authorization summary for a single account.
        Replaces: COPAUS0C EXEC DLI GU PAUTSUM0 WHERE(ACCNTID = WS-CARD-RID-ACCT-ID)
        Returns None if not found (maps to IMS GE/GB status code).
        """
        stmt = select(AuthorizationSummary).where(
            AuthorizationSummary.account_id == account_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_summaries(
        self, page: int, page_size: int
    ) -> tuple[list[AuthorizationSummary], int]:
        """
        Paginated list of all authorization summaries.
        Replaces: sequential browse of IMS PAUTSUM0 root segments.
        Returns (items, total_count).
        """
        offset = (page - 1) * page_size

        count_stmt = select(func.count(AuthorizationSummary.account_id))
        count_result = await self.db.execute(count_stmt)
        total_count = count_result.scalar_one()

        stmt = (
            select(AuthorizationSummary)
            .order_by(AuthorizationSummary.account_id)
            .offset(offset)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        items = list(result.scalars().all())

        return items, total_count

    # -------------------------------------------------------------------------
    # Detail operations — replaces EXEC DLI GNP PAUTDTL1
    # -------------------------------------------------------------------------

    async def list_details_by_account(
        self, account_id: int, page: int, page_size: int
    ) -> tuple[list[AuthorizationDetail], int]:
        """
        Paginated list of authorization detail records for an account.
        Replaces: COPAUS0C EXEC DLI GNP PAUTDTL1 (read up to 5 child segments).
        ORDER BY processed_at DESC replaces IMS inverted timestamp key (999999999 - AUTH-TIME-9C).
        page_size=5 maps to COPAUS0C's WS-IDX 1..5 loop.
        Returns (items, total_count).
        """
        offset = (page - 1) * page_size

        count_stmt = select(func.count(AuthorizationDetail.auth_id)).where(
            AuthorizationDetail.account_id == account_id
        )
        count_result = await self.db.execute(count_stmt)
        total_count = count_result.scalar_one()

        stmt = (
            select(AuthorizationDetail)
            .where(AuthorizationDetail.account_id == account_id)
            .order_by(AuthorizationDetail.processed_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        items = list(result.scalars().all())

        return items, total_count

    async def get_detail_by_id(self, auth_id: int) -> AuthorizationDetail | None:
        """
        Read single authorization detail record by primary key.
        Replaces: COPAUS1C EXEC DLI GNP PAUTDTL1 WHERE(PAUT9CTS = PA-AUTHORIZATION-KEY)
        Returns None if not found (maps to IMS GE status after GNP).
        """
        stmt = select(AuthorizationDetail).where(AuthorizationDetail.auth_id == auth_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # -------------------------------------------------------------------------
    # Fraud flag operations — replaces EXEC DLI REPL + EXEC SQL INSERT/UPDATE
    # -------------------------------------------------------------------------

    async def update_fraud_status(
        self, auth_id: int, new_fraud_status: str
    ) -> AuthorizationDetail | None:
        """
        Update fraud_status on a single authorization detail record.
        Replaces: COPAUS1C EXEC DLI REPL PAUTDTL1 (UPDATE-AUTH-DETAILS paragraph).
        Called only after successful fraud log insert (two-phase atomic operation).
        """
        stmt = (
            update(AuthorizationDetail)
            .where(AuthorizationDetail.auth_id == auth_id)
            .values(fraud_status=new_fraud_status, updated_at=datetime.now(tz=timezone.utc))
            .returning(AuthorizationDetail)
        )
        result = await self.db.execute(stmt)
        row = result.scalar_one_or_none()
        return row

    async def insert_fraud_log(
        self,
        detail: AuthorizationDetail,
        fraud_flag: str,
        report_date: datetime,
    ) -> AuthFraudLog:
        """
        Insert a new fraud log entry.
        Replaces: COPAUS2C EXEC SQL INSERT INTO CARDDEMO.AUTHFRDS (26 columns).
        On IntegrityError (unique constraint on auth_id+fraud_flag='F'):
          caller should use upsert_fraud_log() instead — mirrors COPAUS2C SQLCODE -803 path.
        fraud_flag: 'F'=fraud confirmed, 'R'=fraud removed (WS-FRD-ACTION in COPAUS2C).
        """
        log_entry = AuthFraudLog(
            auth_id=detail.auth_id,
            transaction_id=detail.transaction_id,
            card_number=detail.card_number,
            account_id=detail.account_id,
            fraud_flag=fraud_flag,
            fraud_report_date=report_date,
            auth_response_code=detail.auth_response_code,
            auth_amount=detail.transaction_amount,
            merchant_name=(
                detail.merchant_name[:22] if detail.merchant_name else None
            ),
            merchant_id=(
                detail.merchant_id[:9] if detail.merchant_id else None
            ),
            logged_at=datetime.now(tz=timezone.utc),
        )
        self.db.add(log_entry)
        try:
            await self.db.flush()
        except IntegrityError:
            await self.db.rollback()
            raise
        return log_entry

    async def upsert_fraud_log(
        self,
        detail: AuthorizationDetail,
        fraud_flag: str,
        report_date: datetime,
    ) -> AuthFraudLog:
        """
        Insert or update fraud log entry, handling the unique constraint.
        Replaces: COPAUS2C FRAUD-UPDATE paragraph triggered on SQLCODE -803.
        On duplicate (fraud_flag='F' already exists for this auth_id):
          UPDATE fraud_flag and fraud_report_date only (per COPAUS2C UPDATE statement).
        Returns the final AuthFraudLog record.
        """
        existing = await self._get_fraud_log_for_auth(detail.auth_id, fraud_flag)
        if existing is not None:
            # Replaces COPAUS2C FRAUD-UPDATE paragraph:
            # UPDATE AUTHFRDS SET AUTH_FRAUD=:flag, FRAUD_RPT_DATE=CURRENT DATE WHERE ...
            existing.fraud_flag = fraud_flag
            existing.fraud_report_date = report_date
            existing.logged_at = datetime.now(tz=timezone.utc)
            await self.db.flush()
            return existing
        return await self.insert_fraud_log(detail, fraud_flag, report_date)

    async def _get_fraud_log_for_auth(
        self, auth_id: int, fraud_flag: str
    ) -> AuthFraudLog | None:
        """Find an existing fraud log entry by auth_id and flag."""
        stmt = select(AuthFraudLog).where(
            AuthFraudLog.auth_id == auth_id,
            AuthFraudLog.fraud_flag == fraud_flag,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_fraud_logs_for_auth(self, auth_id: int) -> list[AuthFraudLog]:
        """
        Read all fraud log entries for an authorization.
        Used for audit trail display.
        """
        stmt = (
            select(AuthFraudLog)
            .where(AuthFraudLog.auth_id == auth_id)
            .order_by(AuthFraudLog.logged_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
