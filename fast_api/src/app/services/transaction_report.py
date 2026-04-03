"""Transaction Report Service — CBTRN03C equivalent.

Generates formatted transaction detail report for a date range.

Key changes from COBOL spec:
- ABEND on missing reference data -> log warning and continue (per requirements)
- DATEPARM file -> API request parameters start_date/end_date
- DALYREPT GDG file -> structured JSON response + formatted text
- Page size preserved: 20 lines per page
- Amount formatting preserved from CVTRA07Y layout
"""

import logging
from datetime import date
from decimal import Decimal
from io import StringIO

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.batch_job import BatchJobRepository
from app.repositories.card_cross_reference import CardCrossReferenceRepository
from app.repositories.transaction import TransactionRepository
from app.repositories.transaction_reference import TransactionReferenceRepository
from app.schemas.batch import ReportTotals, TransactionReportResponse
from app.schemas.transaction import TransactionReportLine

logger = logging.getLogger(__name__)

PAGE_SIZE = 20  # WS-PAGE-SIZE = 20 (COMP-3) from CBTRN03C
REPORT_WIDTH = 133  # FD-REPTFILE-REC PIC X(133)
TYPE_DESC_WIDTH = 15  # TRAN-REPORT-TYPE-DESC X(15) — truncated from 50
CAT_DESC_WIDTH = 29  # TRAN-REPORT-CAT-DESC X(29) — truncated from 50


class TransactionReportService:
    """CBTRN03C equivalent: generates transaction detail report."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.tran_repo = TransactionRepository(db)
        self.xref_repo = CardCrossReferenceRepository(db)
        self.ref_repo = TransactionReferenceRepository(db)
        self.job_repo = BatchJobRepository(db)

    async def run(self, start_date: date, end_date: date) -> dict:
        """Generate report for date range.

        Maps CBTRN03C PROCEDURE DIVISION:
          - Reads DATEPARM -> API params
          - Sequential read of TRANSACT with date filter
          - Account break detection
          - Page break every 20 lines
        """
        job = await self.job_repo.create_job("transaction_report")
        await self.db.commit()

        transactions = await self.tran_repo.get_by_date_range(start_date, end_date)

        report_lines, totals, report_text = await self._build_report(
            transactions, start_date, end_date
        )

        await self.job_repo.complete_job(
            job_id=job.job_id,
            records_processed=len(transactions),
            records_rejected=0,
            result_summary={
                "start_date": str(start_date),
                "end_date": str(end_date),
                "transaction_count": len(transactions),
                "grand_total": str(totals.grand_total),
            },
        )
        await self.db.commit()

        return {
            "job_id": job.job_id,
            "status": "completed",
            "start_date": start_date,
            "end_date": end_date,
            "report_lines": report_lines,
            "totals": totals,
            "report_text": report_text,
            "message": (
                f"Report generated: {len(transactions)} transactions, "
                f"grand total {totals.grand_total}"
            ),
        }

    async def _build_report(
        self,
        transactions: list,
        start_date: date,
        end_date: date,
    ) -> tuple[list[TransactionReportLine], ReportTotals, str]:
        """Build report lines and formatted text.

        Implements CBTRN03C main loop with:
        - Account break detection (WS-CURR-CARD-NUM comparison)
        - Page breaks every PAGE_SIZE detail lines
        - Running totals: page, account, grand
        """
        report_lines: list[TransactionReportLine] = []
        output = StringIO()

        grand_total = Decimal("0")
        page_total = Decimal("0")
        account_total = Decimal("0")
        line_counter = 0
        current_card_num = ""
        first_time = True
        page_count = 1

        self._write_headers(output, start_date, end_date)
        line_counter += 4

        for tran in transactions:
            if tran.tran_card_num != current_card_num:
                if not first_time:
                    self._write_account_totals(output, account_total)
                    line_counter += 2
                    account_total = Decimal("0")
                first_time = False
                current_card_num = tran.tran_card_num or ""

                xref = await self.xref_repo.get_by_card_num(current_card_num)
                if xref is None:
                    # COBOL abends here; modern: log warning and use placeholder
                    logger.warning(
                        "Card not found in xref for report: %s — using card num as account",
                        current_card_num,
                    )
                account_id = (xref.xref_acct_id if xref else current_card_num) or current_card_num

            tran_type_desc = await self._get_type_desc(tran.tran_type_cd or "")
            tran_cat_desc = await self._get_cat_desc(
                tran.tran_type_cd or "", tran.tran_cat_cd or ""
            )

            xref = await self.xref_repo.get_by_card_num(tran.tran_card_num or "")
            account_id = (xref.xref_acct_id if xref else tran.tran_card_num) or ""

            if line_counter > 0 and (line_counter % PAGE_SIZE) == 0:
                self._write_page_totals(output, page_total)
                grand_total += page_total
                page_total = Decimal("0")
                page_count += 1
                self._write_headers(output, start_date, end_date)
                line_counter += 4

            tran_amt = Decimal(str(tran.tran_amt or "0"))
            page_total += tran_amt
            account_total += tran_amt

            line = TransactionReportLine(
                tran_id=tran.tran_id,
                account_id=account_id,
                tran_type_cd=tran.tran_type_cd or "",
                tran_type_desc=tran_type_desc[:TYPE_DESC_WIDTH],
                tran_cat_cd=tran.tran_cat_cd or "",
                tran_cat_desc=tran_cat_desc[:CAT_DESC_WIDTH],
                tran_source=tran.tran_source or "",
                tran_amt=tran_amt,
                tran_proc_ts=tran.tran_proc_ts,
                card_num=tran.tran_card_num or "",
            )
            report_lines.append(line)
            self._write_detail_line(output, line)
            line_counter += 1

        # Write final totals
        if not first_time:
            self._write_account_totals(output, account_total)
        grand_total += page_total
        self._write_page_totals(output, page_total)
        self._write_grand_totals(output, grand_total)

        return (
            report_lines,
            ReportTotals(
                grand_total=grand_total,
                page_count=page_count,
                transaction_count=len(transactions),
            ),
            output.getvalue(),
        )

    async def _get_type_desc(self, tran_type_cd: str) -> str:
        """Look up type description. Maps CBTRN03C 1500-B-LOOKUP-TRANTYPE.

        COBOL abends on missing; modern: log warning and return placeholder.
        """
        tran_type = await self.ref_repo.get_type(tran_type_cd)
        if tran_type is None:
            logger.warning("Transaction type not found: %s", tran_type_cd)
            return tran_type_cd
        return tran_type.tran_type_desc or tran_type_cd

    async def _get_cat_desc(self, tran_type_cd: str, tran_cat_cd: str) -> str:
        """Look up category description. Maps CBTRN03C 1500-C-LOOKUP-TRANCATG.

        COBOL abends on missing; modern: log warning and return placeholder.
        """
        category = await self.ref_repo.get_category(tran_type_cd, tran_cat_cd)
        if category is None:
            logger.warning(
                "Transaction category not found: type=%s cat=%s",
                tran_type_cd,
                tran_cat_cd,
            )
            return tran_cat_cd
        return category.tran_cat_desc or tran_cat_cd

    def _write_headers(self, output: StringIO, start_date: date, end_date: date) -> None:
        """Write report header lines. Maps CBTRN03C 1120-WRITE-HEADERS."""
        output.write(
            f"{'DALYREPT':<38}"
            f"{'Daily Transaction Report':<41}"
            f"Date Range: {start_date} to {end_date}\n"
        )
        output.write("\n")
        output.write(
            f"{'Transaction ID':<17}"
            f"{'Account ID':<12}"
            f"{'Type':<4}"
            f"{'Type Desc':<16}"
            f"{'Cat':<5}"
            f"{'Category Desc':<30}"
            f"{'Source':<14}"
            f"{'Amount':>14}\n"
        )
        output.write("-" * REPORT_WIDTH + "\n")

    def _write_detail_line(self, output: StringIO, line: TransactionReportLine) -> None:
        """Write one detail line. Maps CBTRN03C 1120-WRITE-DETAIL.

        Amount format: -ZZZ,ZZZ,ZZZ.ZZ (signed, zero-suppressed with commas).
        """
        amt_str = f"{line.tran_amt:,.2f}"
        output.write(
            f"{line.tran_id:<16} "
            f"{line.account_id:<11} "
            f"{line.tran_type_cd:<2}-"
            f"{line.tran_type_desc[:TYPE_DESC_WIDTH]:<15} "
            f"{line.tran_cat_cd:<4}-"
            f"{line.tran_cat_desc[:CAT_DESC_WIDTH]:<29} "
            f"{line.tran_source:<10}    "
            f"{amt_str:>14}\n"
        )

    def _write_page_totals(self, output: StringIO, page_total: Decimal) -> None:
        """Write page total line. Maps CBTRN03C 1110-WRITE-PAGE-TOTALS."""
        dots = "." * 86
        output.write(f"Page Total{dots}{page_total:+,.2f}\n")
        output.write("-" * REPORT_WIDTH + "\n")

    def _write_account_totals(self, output: StringIO, account_total: Decimal) -> None:
        """Write account total line. Maps CBTRN03C 1120-WRITE-ACCOUNT-TOTALS."""
        dots = "." * 84
        output.write(f"Account Total{dots}{account_total:+,.2f}\n")
        output.write("-" * REPORT_WIDTH + "\n")

    def _write_grand_totals(self, output: StringIO, grand_total: Decimal) -> None:
        """Write grand total line. Maps CBTRN03C 1110-WRITE-GRAND-TOTALS."""
        dots = "." * 86
        output.write(f"Grand Total{dots}{grand_total:+,.2f}\n")
