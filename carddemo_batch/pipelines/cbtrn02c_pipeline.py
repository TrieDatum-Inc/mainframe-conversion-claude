"""
CBTRN02C Pipeline - Daily Transaction Posting

COBOL Program : CBTRN02C.cbl
Type          : Batch - reads sequential DALYTRAN file, writes to
                VSAM TRANSACT-FILE, updates ACCOUNT-FILE and TCATBAL-FILE,
                writes rejects to DALYREJS-FILE.

Execution:
    spark-submit pipelines/cbtrn02c_pipeline.py

    Or in a Databricks notebook:
        from carddemo_batch.pipelines.cbtrn02c_pipeline import run
        run(spark)

COBOL Main Flow Mapping
-----------------------
PROCEDURE DIVISION
  PERFORM 0000-DALYTRAN-OPEN     -> spark.read.table(TBL_DAILY_TRANSACTIONS)
  PERFORM 0100-TRANFILE-OPEN     -> (output) TBL_TRANSACTIONS
  PERFORM 0200-XREFFILE-OPEN     -> spark.read.table(TBL_CARD_XREF)
  PERFORM 0300-DALYREJS-OPEN     -> (output) TBL_DAILY_REJECTS
  PERFORM 0400-ACCTFILE-OPEN     -> spark.read.table(TBL_ACCOUNTS) [I-O]
  PERFORM 0500-TCATBALF-OPEN     -> spark.read.table(TBL_TRAN_CAT_BAL) [I-O]
  PERFORM 1000-DALYTRAN-GET-NEXT -> (loop over DataFrame rows)
  PERFORM 1500-VALIDATE-TRAN     -> validate_transactions()
  PERFORM 2000-POST-TRANSACTION  -> build_posted_transactions()
  PERFORM 2700-UPDATE-TCATBAL    -> build_tcatbal_updates() + MERGE
  PERFORM 2800-UPDATE-ACCOUNT    -> build_account_balance_updates() + MERGE
  PERFORM 2500-WRITE-REJECT-REC  -> extract_rejected_transactions()

Return-code behaviour (COBOL: IF WS-REJECT-COUNT > 0 MOVE 4 TO RETURN-CODE):
  The run() function returns the reject count.  Callers should treat > 0
  as a warning condition (RC=4 equivalent).
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
    COL_BALANCE_DELTA,
    COL_CURR_BAL_DELTA,
    COL_CYC_CREDIT_DELTA,
    COL_CYC_DEBIT_DELTA,
    COL_TRANCAT_ACCT_ID,
    COL_TRANCAT_CD,
    COL_TRANCAT_TYPE_CD,
    COL_TRAN_CAT_BAL,
    COL_TRAN_ID,
)
from carddemo_batch.config.settings import (
    TBL_ACCOUNTS,
    TBL_CARD_XREF,
    TBL_DAILY_REJECTS,
    TBL_DAILY_TRANSACTIONS,
    TBL_TRAN_CAT_BAL,
    TBL_TRANSACTIONS,
)
from carddemo_batch.transformations.cbtrn02c_transforms import (
    build_account_balance_updates,
    build_posted_transactions,
    build_tcatbal_updates,
    extract_rejected_transactions,
    validate_transactions,
)
from carddemo_batch.validators.common import (
    PipelineAbendError,
    assert_table_not_empty,
    log_processing_summary,
    validate_no_duplicate_tran_ids,
)

logger = logging.getLogger(__name__)
PROGRAM_NAME = "CBTRN02C"


def _get_proc_ts() -> str:
    """
    COBOL: Z-GET-DB2-FORMAT-TIMESTAMP
    Returns current UTC time in DB2 timestamp format: YYYY-MM-DD-HH.MM.SS.NNNNNN
    """
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%d-%H.%M.%S.") + f"{now.microsecond:06d}"


def _filter_already_processed(daily_df, spark: SparkSession):
    """
    Idempotency guard: remove transactions whose tran_id already exists
    in the transactions or daily_rejects tables.  On a clean re-run with
    the same input, this ensures deltas are not double-applied and rows
    are not duplicated.
    """
    existing_posted = spark.read.table(TBL_TRANSACTIONS).select(COL_TRAN_ID)
    existing_rejected = spark.read.table(TBL_DAILY_REJECTS).select(COL_TRAN_ID)
    return daily_df.join(
        existing_posted.union(existing_rejected),
        on=COL_TRAN_ID,
        how="left_anti",
    )


def _merge_tcatbal_updates(spark: SparkSession, deltas_df) -> None:
    """
    COBOL: 2700-A-CREATE-TCATBAL-REC / 2700-B-UPDATE-TCATBAL-REC
    Uses Delta MERGE to upsert transaction-category-balance records.
    When key exists: ADD delta to existing balance.
    When key missing: INSERT new record with the delta as the initial balance.
    """
    deltas_df.createOrReplaceTempView("_cbtrn02c_tcatbal_deltas")
    spark.sql(f"""
        MERGE INTO {TBL_TRAN_CAT_BAL} AS target
        USING _cbtrn02c_tcatbal_deltas AS source
        ON  target.{COL_TRANCAT_ACCT_ID}  = source.{COL_TRANCAT_ACCT_ID}
        AND target.{COL_TRANCAT_TYPE_CD}  = source.{COL_TRANCAT_TYPE_CD}
        AND target.{COL_TRANCAT_CD}       = source.{COL_TRANCAT_CD}
        WHEN MATCHED THEN
            UPDATE SET target.{COL_TRAN_CAT_BAL} =
                target.{COL_TRAN_CAT_BAL} + source.{COL_BALANCE_DELTA}
        WHEN NOT MATCHED THEN
            INSERT ({COL_TRANCAT_ACCT_ID}, {COL_TRANCAT_TYPE_CD}, {COL_TRANCAT_CD}, {COL_TRAN_CAT_BAL})
            VALUES (source.{COL_TRANCAT_ACCT_ID}, source.{COL_TRANCAT_TYPE_CD},
                    source.{COL_TRANCAT_CD}, source.{COL_BALANCE_DELTA})
    """)


def _merge_account_updates(spark: SparkSession, account_deltas_df) -> None:
    """
    COBOL: 2800-UPDATE-ACCOUNT-REC (REWRITE FD-ACCTFILE-REC)
    Delta MERGE to update account current balance and cycle accumulators.
    """
    account_deltas_df.createOrReplaceTempView("_cbtrn02c_acct_deltas")
    spark.sql(f"""
        MERGE INTO {TBL_ACCOUNTS} AS target
        USING _cbtrn02c_acct_deltas AS source
        ON target.{COL_ACCT_ID} = CAST(source.{COL_ACCT_ID} AS STRING)
        WHEN MATCHED THEN
            UPDATE SET
                target.{COL_ACCT_CURR_BAL}        = target.{COL_ACCT_CURR_BAL} + source.{COL_CURR_BAL_DELTA},
                target.{COL_ACCT_CURR_CYC_CREDIT} = target.{COL_ACCT_CURR_CYC_CREDIT} + source.{COL_CYC_CREDIT_DELTA},
                target.{COL_ACCT_CURR_CYC_DEBIT}  = target.{COL_ACCT_CURR_CYC_DEBIT} + source.{COL_CYC_DEBIT_DELTA}
    """)


def _write_rejects(validated_df, spark: SparkSession) -> int:
    """
    COBOL: 2500-WRITE-REJECT-REC
    Writes rejected transactions; returns reject count.
    """
    rejects_df = extract_rejected_transactions(validated_df)
    reject_count = rejects_df.count()
    if reject_count > 0:
        rejects_df.createOrReplaceTempView("_cbtrn02c_new_rejects")
        spark.sql(f"""
            MERGE INTO {TBL_DAILY_REJECTS} AS target
            USING _cbtrn02c_new_rejects AS source
            ON target.{COL_TRAN_ID} = source.{COL_TRAN_ID}
            WHEN NOT MATCHED THEN INSERT *
        """)
        logger.warning(
            "[%s] %d transactions rejected - written to %s",
            PROGRAM_NAME, reject_count, TBL_DAILY_REJECTS,
        )
    return reject_count


def _post_and_update(validated_df, spark: SparkSession, proc_ts: str) -> None:
    """
    COBOL: 2000-POST-TRANSACTION, 2700-UPDATE-TCATBAL, 2800-UPDATE-ACCOUNT-REC.
    Posts valid transactions and updates both balance tables.
    """
    posted_df = build_posted_transactions(validated_df, proc_ts)
    validate_no_duplicate_tran_ids(posted_df, PROGRAM_NAME)
    posted_df.createOrReplaceTempView("_cbtrn02c_new_posts")
    spark.sql(f"""
        MERGE INTO {TBL_TRANSACTIONS} AS target
        USING _cbtrn02c_new_posts AS source
        ON target.{COL_TRAN_ID} = source.{COL_TRAN_ID}
        WHEN NOT MATCHED THEN INSERT *
    """)
    _merge_tcatbal_updates(spark, build_tcatbal_updates(validated_df))
    _merge_account_updates(spark, build_account_balance_updates(validated_df))


def run(spark: SparkSession) -> int:
    """
    Main pipeline entry point.
    Returns the reject count (maps to COBOL RETURN-CODE=4 when > 0).
    """
    logger.info("START OF EXECUTION OF PROGRAM %s", PROGRAM_NAME)

    daily_df = spark.read.table(TBL_DAILY_TRANSACTIONS)
    assert_table_not_empty(daily_df, TBL_DAILY_TRANSACTIONS, PROGRAM_NAME)

    # Idempotency: skip transactions already posted or rejected
    daily_df = _filter_already_processed(daily_df, spark)
    if daily_df.head(1) == []:
        logger.info("[%s] All transactions already processed - skipping", PROGRAM_NAME)
        return 0

    xref_df = spark.read.table(TBL_CARD_XREF)
    account_df = spark.read.table(TBL_ACCOUNTS)

    proc_ts = _get_proc_ts()
    validated_df = validate_transactions(daily_df, xref_df, account_df)
    validated_df.cache()

    total_count = validated_df.count()
    logger.info("[%s] Records read: %d", PROGRAM_NAME, total_count)

    reject_count = _write_rejects(validated_df, spark)
    _post_and_update(validated_df, spark, proc_ts)
    validated_df.unpersist()

    log_processing_summary(
        PROGRAM_NAME,
        records_read=total_count,
        records_written=total_count - reject_count,
        records_rejected=reject_count,
    )
    logger.info("END OF EXECUTION OF PROGRAM %s", PROGRAM_NAME)
    return reject_count


if __name__ == "__main__":
    from pyspark.sql import SparkSession as _SparkSession

    _spark = _SparkSession.builder.appName(PROGRAM_NAME).getOrCreate()
    _rc = run(_spark)
    import sys

    sys.exit(4 if _rc > 0 else 0)
