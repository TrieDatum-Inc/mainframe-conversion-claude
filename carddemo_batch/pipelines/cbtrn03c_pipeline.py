"""
CBTRN03C Pipeline - Transaction Detail Report (CSV output only)

COBOL Program : CBTRN03C.cbl
Type          : Batch - reads posted transactions within a date range,
                enriches with type/category descriptions, and produces a
                formatted report with page/account/grand totals.

NOTE: The COBOL program writes a fixed-width 133-column print file (TRANREPT).
      This pipeline produces CSV output to the transaction_report Delta table
      plus summary tables for page, account, and grand totals.

Accepts start_date and end_date parameters (maps to COBOL WS-DATEPARM-RECORD
read from DATE-PARMS-FILE - "YYYY-MM-DD YYYY-MM-DD").

Execution:
    spark-submit pipelines/cbtrn03c_pipeline.py \
        --start-date 2024-01-01 --end-date 2024-01-31

    Or in a Databricks notebook:
        from carddemo_batch.pipelines.cbtrn03c_pipeline import run
        run(spark, start_date="2024-01-01", end_date="2024-01-31")

COBOL Main Flow Mapping
-----------------------
0550-DATEPARM-READ         -> start_date / end_date arguments
0000-TRANFILE-OPEN         -> spark.read.table(TBL_TRANSACTIONS)
0100-REPTFILE-OPEN         -> (output) TBL_TRANSACTION_REPORT
0200-CARDXREF-OPEN         -> spark.read.table(TBL_CARD_XREF)
0300-TRANTYPE-OPEN         -> spark.read.table(TBL_TRAN_TYPES)
0400-TRANCATG-OPEN         -> spark.read.table(TBL_TRAN_CATEGORIES)
1000-TRANFILE-GET-NEXT     -> (loop over transactions DataFrame)
date filter (inline)       -> filter_by_date_range()
1500-A-LOOKUP-XREF         -> enrich_with_xref()
1500-B-LOOKUP-TRANTYPE     -> enrich_with_tran_type()
1500-C-LOOKUP-TRANCATG     -> enrich_with_tran_category()
1100-WRITE-TRANSACTION-REPORT -> build_report_detail_rows()
1110-WRITE-PAGE-TOTALS     -> compute_page_totals()
1120-WRITE-ACCOUNT-TOTALS  -> compute_account_totals()
1110-WRITE-GRAND-TOTALS    -> compute_grand_total()
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from pyspark.sql import SparkSession

from carddemo_batch.config.columns import COL_GRAND_TOTAL, COL_PAGE_NUM
from carddemo_batch.config.settings import (
    TBL_CARD_XREF,
    TBL_TRAN_CATEGORIES,
    TBL_TRAN_TYPES,
    TBL_TRANSACTION_REPORT,
    TBL_TRANSACTIONS,
)
from carddemo_batch.transformations.cbtrn03c_transforms import (
    build_report_detail_rows,
    compute_account_totals,
    compute_grand_total,
    compute_page_totals,
)
from carddemo_batch.validators.common import (
    assert_table_not_empty,
    log_processing_summary,
    validate_date_format,
)

logger = logging.getLogger(__name__)
PROGRAM_NAME = "CBTRN03C"


def _resolve_date_params(
    start_date: str | None, end_date: str | None
) -> tuple[str, str, str]:
    """
    COBOL: 0550-DATEPARM-READ
    Validates and returns (today, start_date, end_date).
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    start = start_date or today
    end = end_date or today
    validate_date_format(start, "WS-START-DATE", PROGRAM_NAME)
    validate_date_format(end, "WS-END-DATE", PROGRAM_NAME)
    return today, start, end


def _build_and_write_report(
    spark: SparkSession,
    tran_df, xref_df, tran_type_df, tran_cat_df,
    start_date: str, end_date: str, today: str,
) -> tuple:
    """
    COBOL: main loop (1000-GET-NEXT through 1120-WRITE-DETAIL).
    Builds detail rows, writes to Delta, returns (report_df, rows_written).
    """
    report_df = build_report_detail_rows(
        tran_df=tran_df,
        xref_df=xref_df,
        tran_type_df=tran_type_df,
        tran_cat_df=tran_cat_df,
        start_date=start_date,
        end_date=end_date,
        report_date=today,
    )
    report_df.cache()
    rows_written = report_df.count()
    report_df.drop(COL_PAGE_NUM).write.format("delta").mode("overwrite").saveAsTable(
        TBL_TRANSACTION_REPORT
    )
    return report_df, rows_written


def run(
    spark: SparkSession,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    """
    Main pipeline entry point.

    Parameters
    ----------
    start_date : str, optional
        YYYY-MM-DD (maps to WS-START-DATE from DATE-PARMS-FILE).
    end_date : str, optional
        YYYY-MM-DD (maps to WS-END-DATE from DATE-PARMS-FILE).
        Defaults to today's date if not supplied.

    Returns dict: rows_written, account_totals_df, page_totals_df, grand_total.
    """
    logger.info("START OF EXECUTION OF PROGRAM %s", PROGRAM_NAME)
    today, start_date, end_date = _resolve_date_params(start_date, end_date)
    logger.info("[%s] Reporting from %s to %s", PROGRAM_NAME, start_date, end_date)

    tran_df = spark.read.table(TBL_TRANSACTIONS)
    xref_df = spark.read.table(TBL_CARD_XREF)
    tran_type_df = spark.read.table(TBL_TRAN_TYPES)
    tran_cat_df = spark.read.table(TBL_TRAN_CATEGORIES)
    assert_table_not_empty(tran_df, TBL_TRANSACTIONS, PROGRAM_NAME)

    report_df, rows_written = _build_and_write_report(
        spark, tran_df, xref_df, tran_type_df, tran_cat_df,
        start_date, end_date, today,
    )

    page_totals = compute_page_totals(report_df)
    account_totals = compute_account_totals(report_df)
    grand_total_val = compute_grand_total(report_df).first()[COL_GRAND_TOTAL]
    report_df.unpersist()

    logger.info(
        "[%s] GRAND TOTAL: %s", PROGRAM_NAME,
        f"{grand_total_val:,.2f}" if grand_total_val is not None else "0.00",
    )
    log_processing_summary(PROGRAM_NAME, records_read=rows_written, records_written=rows_written)
    logger.info("END OF EXECUTION OF PROGRAM %s", PROGRAM_NAME)

    return {
        "rows_written": rows_written,
        "page_totals_df": page_totals,
        "account_totals_df": account_totals,
        "grand_total": grand_total_val,
    }


if __name__ == "__main__":
    import argparse
    from pyspark.sql import SparkSession as _SparkSession

    parser = argparse.ArgumentParser(description="CBTRN03C - Transaction Detail Report")
    parser.add_argument("--start-date", dest="start_date", required=True,
                        help="Report start date YYYY-MM-DD")
    parser.add_argument("--end-date", dest="end_date", required=True,
                        help="Report end date YYYY-MM-DD")
    args = parser.parse_args()

    _spark = _SparkSession.builder.appName(PROGRAM_NAME).getOrCreate()
    result = run(_spark, start_date=args.start_date, end_date=args.end_date)
    print(f"Grand Total: {result['grand_total']}")
