"""Report generation business logic — modernized from CORPT00C.

COBOL CORPT00C submitted JCL to a TDQ queue to run a batch job (TRANREPT).
The modern equivalent generates the report data in-process using SQL queries,
avoiding the need for batch job submission infrastructure.

COBOL business rules preserved:
  - Monthly: first day of current month to last day of current month
  - Yearly: Jan 1 to Dec 31 of current year
  - Custom: caller-supplied dates; end_date >= start_date (CSUTLDTC validated)
  - CONFIRM='Y' required before report generation
"""

import calendar
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction
from app.schemas.report import ReportRequest, ReportResult, ReportTransactionRow, ReportType


class ReportService:
    """Handles transaction report generation (CORPT00C logic)."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def generate_report(self, request: ReportRequest) -> ReportResult:
        """Generate transaction report for the requested date range.

        COBOL CORPT00C flow:
          1. Determine date range based on report_type
          2. Validate custom dates (CSUTLDTC) → handled in schema
          3. CONFIRM='Y' → generate (handled by router pre-check)
          4. TRANREPT batch job → SQL query returning filtered/sorted rows
        """
        start_date, end_date = self._resolve_date_range(request)
        transactions = await self._fetch_transactions_in_range(start_date, end_date)
        rows = [self._to_report_row(t) for t in transactions]
        total_amount = sum(float(t.amount) for t in transactions)

        return ReportResult(
            report_type=request.report_type,
            start_date=start_date,
            end_date=end_date,
            total_transactions=len(rows),
            total_amount=round(total_amount, 2),
            transactions=rows,
            generated_at=datetime.utcnow().isoformat(),
        )

    def _resolve_date_range(self, request: ReportRequest) -> tuple[date, date]:
        """Compute start/end dates from the report type.

        COBOL CORPT00C:
          Monthly → WS-START-DATE = first day of current month
                    WS-END-DATE   = last day of current month
          Yearly  → Jan 1 to Dec 31
          Custom  → use screen-entered dates
        """
        today = date.today()

        if request.report_type == ReportType.MONTHLY:
            return self._monthly_range(today)
        if request.report_type == ReportType.YEARLY:
            return self._yearly_range(today)
        # Custom — schema already validated both dates present and end >= start
        return request.start_date, request.end_date  # type: ignore[return-value]

    def _monthly_range(self, today: date) -> tuple[date, date]:
        """First and last day of the current calendar month."""
        first_day = today.replace(day=1)
        last_day_num = calendar.monthrange(today.year, today.month)[1]
        last_day = today.replace(day=last_day_num)
        return first_day, last_day

    def _yearly_range(self, today: date) -> tuple[date, date]:
        """Jan 1 to Dec 31 of the current year."""
        return date(today.year, 1, 1), date(today.year, 12, 31)

    async def _fetch_transactions_in_range(
        self, start_date: date, end_date: date
    ) -> list[Transaction]:
        """Query transactions within the date range, sorted by card number.

        Mirrors the TRANREPT procedure:
          Step 2: SORT transactions by card number within date range.
        """
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        result = await self._db.execute(
            select(Transaction)
            .where(Transaction.original_timestamp >= start_dt)
            .where(Transaction.original_timestamp <= end_dt)
            .order_by(Transaction.card_number, Transaction.transaction_id)
        )
        return list(result.scalars().all())

    def _to_report_row(self, txn: Transaction) -> ReportTransactionRow:
        """Convert ORM transaction to report row — mirrors CBTRN03C output fields."""
        return ReportTransactionRow(
            transaction_id=txn.transaction_id,
            card_number=txn.card_number,
            type_code=txn.type_code,
            category_code=txn.category_code,
            description=txn.description,
            amount=float(txn.amount),
            original_date=txn.original_timestamp.strftime("%Y-%m-%d"),
            processing_date=txn.processing_timestamp.strftime("%Y-%m-%d"),
            merchant_name=txn.merchant_name,
            merchant_city=txn.merchant_city,
        )
