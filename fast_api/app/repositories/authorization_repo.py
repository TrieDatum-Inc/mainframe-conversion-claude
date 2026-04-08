"""
Authorization repository — data access layer for authorization module.

Maps CICS/IMS/DB2 operations to SQLAlchemy:

  COPAUA0C 5100-READ-XREF-RECORD:
    EXEC CICS READ FILE(CCXREF) RIDFLD(XREF-CARD-NUM) → get_xref_by_card_num() [in CardRepository]

  COPAUA0C 5500-READ-AUTH-SUMMRY:
    EXEC DLI GU SEGMENT(PAUTSUM0) WHERE(ACCNTID=PA-ACCT-ID) → get_summary_by_acct_id()

  COPAUA0C 8400-UPDATE-SUMMARY (IMS REPL / ISRT):
    EXEC DLI REPL SEGMENT(PAUTSUM0) → upsert_summary()

  COPAUA0C 8500-INSERT-AUTH (IMS ISRT child):
    EXEC DLI ISRT SEGMENT(PAUTDTL1) → create_detail()

  COPAUS0C GATHER-DETAILS + pagination:
    IMS READNEXT on child segments → list_details_by_acct_id()

  COPAUS1C READ-AUTH-RECORD:
    EXEC DLI GU SEGMENT(PAUTSUM0/PAUTDTL1) → get_detail_by_id()

  COPAUS2C EXEC SQL INSERT INTO AUTHFRDS:
    upsert_fraud_record() — mirrors SQLCODE=-803 → UPDATE logic

Source copybooks:
  CIPAUSMY.cpy — PENDING-AUTH-SUMMARY (IMS root segment)
  CIPAUDTY.cpy — PENDING-AUTH-DETAILS (IMS child segment)
"""
from decimal import Decimal

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.authorization import AuthDetail, AuthFraudRecord, AuthSummary
from app.utils.error_handlers import RecordNotFoundError


class AuthorizationRepository:
    """Data access object for authorization tables."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Auth Summary (replaces IMS PAUTSUM0 root segment)
    # ------------------------------------------------------------------

    async def get_summary_by_acct_id(self, acct_id: int) -> AuthSummary | None:
        """
        COPAUA0C 5500-READ-AUTH-SUMMRY:
          EXEC DLI GU SEGMENT(PAUTSUM0) WHERE (ACCNTID = PA-ACCT-ID)

        Returns None (not raises) — caller checks FOUND-PAUT-SMRY-SEG flag.
        IMS 'GE' (segment not found) → None.
        """
        return await self._db.get(AuthSummary, acct_id)

    async def upsert_summary(self, summary: AuthSummary) -> AuthSummary:
        """
        COPAUA0C 8400-UPDATE-SUMMARY:
          IF FOUND-PAUT-SMRY-SEG:
            EXEC DLI REPL SEGMENT(PAUTSUM0) FROM(PENDING-AUTH-SUMMARY)
          ELSE:
            EXEC DLI ISRT SEGMENT(PAUTSUM0) FROM(PENDING-AUTH-SUMMARY)

        Performs an INSERT ... ON CONFLICT UPDATE (upsert) so the
        FOUND/NFOUND branch is handled transparently.
        """
        existing = await self._db.get(AuthSummary, summary.acct_id)
        if existing is None:
            self._db.add(summary)
        else:
            existing.cust_id = summary.cust_id
            existing.credit_limit = summary.credit_limit
            existing.cash_limit = summary.cash_limit
            existing.credit_balance = summary.credit_balance
            existing.cash_balance = summary.cash_balance
            existing.approved_auth_cnt = summary.approved_auth_cnt
            existing.declined_auth_cnt = summary.declined_auth_cnt
            existing.approved_auth_amt = summary.approved_auth_amt
            existing.declined_auth_amt = summary.declined_auth_amt
        await self._db.flush()
        return existing if existing else summary

    # ------------------------------------------------------------------
    # Auth Detail (replaces IMS PAUTDTL1 child segment)
    # ------------------------------------------------------------------

    async def create_detail(self, detail: AuthDetail) -> AuthDetail:
        """
        COPAUA0C 8500-INSERT-AUTH:
          EXEC DLI ISRT SEGMENT(PAUTDTL1) FROM(PENDING-AUTH-DETAILS)

        Inserts a new authorization detail record.
        """
        self._db.add(detail)
        await self._db.flush()
        return detail

    async def get_detail_by_id(self, auth_id: int) -> AuthDetail:
        """
        COPAUS1C READ-AUTH-RECORD:
          EXEC DLI GU SEGMENT(PAUTSUM0/PAUTDTL1) WHERE key = WS-AUTH-KEY

        Raises RecordNotFoundError if not found (IMS 'GE' status).
        """
        detail = await self._db.get(AuthDetail, auth_id)
        if detail is None:
            raise RecordNotFoundError(f"Authorization detail not found (auth_id={auth_id})")
        return detail

    async def get_next_detail(self, acct_id: int, current_auth_id: int) -> AuthDetail | None:
        """
        COPAUS1C PROCESS-PF8-KEY → READ-NEXT-AUTH-RECORD:
          IMS GN (get next) on child segments — returns next detail after current key.

        Returns None if at end of chain (IMS 'GB' end-of-database).
        """
        stmt = (
            select(AuthDetail)
            .where(AuthDetail.acct_id == acct_id)
            .where(AuthDetail.auth_id > current_auth_id)
            .order_by(AuthDetail.auth_date_9c.asc(), AuthDetail.auth_time_9c.asc())
            .limit(1)
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_details_by_acct_id(
        self,
        acct_id: int,
        cursor: int | None = None,
        limit: int = 5,
    ) -> tuple[list[AuthDetail], int]:
        """
        COPAUS0C PROCESS-PAGE-FORWARD / REPOSITION-AUTHORIZATIONS:
          IMS READNEXT on PAUTDTL1 child segments for an account.

        Keyset pagination on auth_id ascending (mirrors IMS sequential read).
        Returns (page_items, total_count).
        """
        base_where = [AuthDetail.acct_id == acct_id]
        if cursor is not None:
            base_where.append(AuthDetail.auth_id > cursor)

        stmt = (
            select(AuthDetail)
            .where(*base_where)
            .order_by(AuthDetail.auth_date_9c.asc(), AuthDetail.auth_time_9c.asc())
            .limit(limit)
        )
        count_stmt = select(func.count()).select_from(AuthDetail).where(AuthDetail.acct_id == acct_id)

        result = await self._db.execute(stmt)
        count_result = await self._db.execute(count_stmt)
        items = list(result.scalars().all())
        total = count_result.scalar_one()
        return items, total

    async def update_detail_fraud(
        self,
        auth_id: int,
        auth_fraud: str,
        fraud_rpt_date: str,
    ) -> AuthDetail:
        """
        COPAUS1C UPDATE-AUTH-DETAILS paragraph:
          EXEC DLI REPL SEGMENT(PAUTDTL1) — update fraud flag on existing detail.

        Called after EXEC CICS LINK COPAUS2C returns WS-FRD-UPDT-SUCCESS.
        """
        detail = await self.get_detail_by_id(auth_id)
        detail.auth_fraud = auth_fraud
        detail.fraud_rpt_date = fraud_rpt_date
        await self._db.flush()
        return detail

    # ------------------------------------------------------------------
    # Auth Fraud Records (DB2 CARDDEMO.AUTHFRDS — COPAUS2C)
    # ------------------------------------------------------------------

    async def upsert_fraud_record(self, record: AuthFraudRecord) -> AuthFraudRecord:
        """
        COPAUS2C MAIN-PARA + FRAUD-UPDATE paragraph:

          EXEC SQL INSERT INTO CARDDEMO.AUTHFRDS (...)
          IF SQLCODE = 0    → success
          IF SQLCODE = -803 → PERFORM FRAUD-UPDATE (duplicate key → UPDATE)
          ELSE              → error

        The INSERT/UPDATE upsert logic is modeled directly:
          - Try to find existing record by (card_num, auth_ts)
          - INSERT if not found, UPDATE auth_fraud + fraud_rpt_date if found
        """
        existing = await self._db.get(AuthFraudRecord, (record.card_num, record.auth_ts))
        if existing is None:
            self._db.add(record)
            await self._db.flush()
            return record
        # SQLCODE=-803 branch: PERFORM FRAUD-UPDATE
        existing.auth_fraud = record.auth_fraud
        existing.fraud_rpt_date = record.fraud_rpt_date
        await self._db.flush()
        return existing

    async def get_fraud_records_by_card(self, card_num: str) -> list[AuthFraudRecord]:
        """Retrieve all fraud records for a card number."""
        stmt = (
            select(AuthFraudRecord)
            .where(AuthFraudRecord.card_num == card_num)
            .order_by(AuthFraudRecord.auth_ts.desc())
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())
