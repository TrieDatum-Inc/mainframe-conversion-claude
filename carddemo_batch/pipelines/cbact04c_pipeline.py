"""
CBACT04C Pipeline - Interest Calculator

COBOL Program : CBACT04C.cbl
Type          : Batch - reads TCATBAL-FILE (transaction-category-balance)
                sequentially, computes monthly interest per category,
                writes interest transactions to TRANSACT-FILE, and updates
                ACCOUNT-FILE balances.

Accepts an optional run_date parameter (maps to COBOL PARM-DATE from
LINKAGE SECTION / JCL PARM).

Execution:
    spark-submit pipelines/cbact04c_pipeline.py --run-date 2024-01-15

    Or in a Databricks notebook:
        from carddemo_batch.pipelines.cbact04c_pipeline import run
        run(spark, run_date="2024-01-15")

COBOL Main Flow Mapping
-----------------------
PROCEDURE DIVISION USING EXTERNAL-PARMS
  PERFORM 0000-TCATBALF-OPEN    -> spark.read.table(TBL_TRAN_CAT_BAL) [sequential]
  PERFORM 0100-XREFFILE-OPEN    -> spark.read.table(TBL_CARD_XREF)
  PERFORM 0200-DISCGRP-OPEN     -> spark.read.table(TBL_DISCLOSURE_GROUPS)
  PERFORM 0300-ACCTFILE-OPEN    -> spark.read.table(TBL_ACCOUNTS) [I-O]
  PERFORM 0400-TRANFILE-OPEN    -> (output) TBL_INTEREST_TRANSACTIONS
  PERFORM 1000-TCATBALF-GET-NEXT -> (loop over tcatbal DataFrame)
  PERFORM 1050-UPDATE-ACCOUNT   -> _merge_account_interest_updates()
  PERFORM 1100-GET-ACCT-DATA    -> (join inside resolve_interest_rates)
  PERFORM 1110-GET-XREF-DATA    -> (join inside resolve_interest_rates)
  PERFORM 1200-GET-INTEREST-RATE -> resolve_interest_rates()
  PERFORM 1300-COMPUTE-INTEREST  -> compute_monthly_interest()
  PERFORM 1300-B-WRITE-TX       -> build_interest_transactions()

Sequential processing note:
  COBOL processes TCATBAL records in ACCT-ID order (indexed file, sequential
  access).  It maintains WS-LAST-ACCT-NUM to detect account boundaries and
  calls 1050-UPDATE-ACCOUNT when the account changes.  In Spark we process
  ALL records in a single pass and then aggregate per account, which produces
  identical results.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from pyspark.sql import SparkSession

from carddemo_batch.config.columns import (
    COL_ACCT_CURR_BAL,
    COL_ACCT_CURR_CYC_CREDIT,
    COL_ACCT_CURR_CYC_DEBIT,
    COL_ACCT_ID,
    COL_TOTAL_INTEREST,
    COL_TRANCAT_ACCT_ID,
)
from carddemo_batch.config.settings import (
    TBL_ACCOUNTS,
    TBL_CARD_XREF,
    TBL_DISCLOSURE_GROUPS,
    TBL_INTEREST_TRANSACTIONS,
    TBL_TRAN_CAT_BAL,
)
from carddemo_batch.transformations.cbact04c_transforms import (
    build_account_interest_updates,
    build_interest_transactions,
    compute_monthly_interest,
    resolve_interest_rates,
)
from carddemo_batch.validators.common import (
    PipelineAbendError,
    assert_table_not_empty,
    log_processing_summary,
)

logger = logging.getLogger(__name__)
PROGRAM_NAME = "CBACT04C"


def _get_proc_ts() -> str:
    """COBOL: Z-GET-DB2-FORMAT-TIMESTAMP"""
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%d-%H.%M.%S.") + f"{now.microsecond:06d}"


def  _merge_account_interest_updates(spark: SparkSession, interest_updates_df) -> None:
    """
    COBOL: 1050-UPDATE-ACCOUNT
    REWRITE FD-ACCTFILE-REC:
      ADD WS-TOTAL-INT TO ACCT-CURR-BAL
      MOVE 0 TO ACCT-CURR-CYC-CREDIT
      MOVE 0 TO ACCT-CURR-CYC-DEBIT
    """
    interest_updates_df.createOrReplaceTempView("_cbact04c_interest_updates")
    spark.sql(f"""
        MERGE INTO {TBL_ACCOUNTS} AS target
        USING _cbact04c_interest_updates AS source
        ON target.{COL_ACCT_ID} = CAST(source.{COL_TRANCAT_ACCT_ID} AS STRING)
        WHEN MATCHED THEN
            UPDATE SET
                target.{COL_ACCT_CURR_BAL}        = target.{COL_ACCT_CURR_BAL} + source.{COL_TOTAL_INTEREST},
                target.{COL_ACCT_CURR_CYC_CREDIT} = 0,
                target.{COL_ACCT_CURR_CYC_DEBIT}  = 0
    """)


def _compute_and_write_interest(
    spark: SparkSession,
    tcatbal_df, account_df, xref_df, discgrp_df,
    run_date: str, proc_ts: str,
) -> tuple:
    """
    COBOL: 1200/1300 paragraphs.
    Resolves rates, computes interest, writes transactions, returns (interest_df, count).
    """
    enriched_df = resolve_interest_rates(tcatbal_df, account_df, xref_df, discgrp_df)
    interest_df = compute_monthly_interest(enriched_df)
    interest_df.cache()
    interest_tran_df = build_interest_transactions(interest_df, run_date, proc_ts)
    interest_tran_df.write.format("delta").mode("append").saveAsTable(TBL_INTEREST_TRANSACTIONS)
    tran_written = interest_tran_df.count()
    return interest_df, tran_written


def run(spark: SparkSession, run_date: str | None = None) -> int:
    """
    Main pipeline entry point.
    run_date: YYYY-MM-DD (maps to COBOL PARM-DATE). Defaults to today.
    Returns the count of interest transactions written.
    """
    logger.info("START OF EXECUTION OF PROGRAM %s", PROGRAM_NAME)

    if run_date is None:
        run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    proc_ts = _get_proc_ts()

    tcatbal_df = spark.read.table(TBL_TRAN_CAT_BAL)
    xref_df = spark.read.table(TBL_CARD_XREF)
    account_df = spark.read.table(TBL_ACCOUNTS)
    discgrp_df = spark.read.table(TBL_DISCLOSURE_GROUPS)
    assert_table_not_empty(tcatbal_df, TBL_TRAN_CAT_BAL, PROGRAM_NAME)

    record_count = tcatbal_df.count()
    logger.info("[%s] Records read from tcatbal: %d", PROGRAM_NAME, record_count)

    interest_df, tran_written = _compute_and_write_interest(
        spark, tcatbal_df, account_df, xref_df, discgrp_df, run_date, proc_ts
    )
    _merge_account_interest_updates(spark, build_account_interest_updates(interest_df))
    interest_df.unpersist()

    log_processing_summary(PROGRAM_NAME, records_read=record_count, records_written=tran_written)
    logger.info("END OF EXECUTION OF PROGRAM %s", PROGRAM_NAME)
    return tran_written


if __name__ == "__main__":
    import argparse
    from pyspark.sql import SparkSession as _SparkSession

    parser = argparse.ArgumentParser(description="CBACT04C - Interest Calculator")
    parser.add_argument("--run-date", dest="run_date", default=None,
                        help="Processing date YYYY-MM-DD (default: today)")
    args = parser.parse_args()

    _spark = _SparkSession.builder.appName(PROGRAM_NAME).getOrCreate()
    run(_spark, run_date=args.run_date)
