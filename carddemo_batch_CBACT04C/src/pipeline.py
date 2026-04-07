"""
CBACT04C — Interest Calculation Pipeline (Main Entry Point)

Migrates COBOL batch program CBACT04C from z/OS to Databricks PySpark.

Source program: app/cbl/CBACT04C.cbl
JCL job:        INTCALC.jcl
Databricks job: cbact04c_interest_calc

High-level flow (mirrors COBOL PROCEDURE DIVISION):
  1. Read and sort TCATBALF driving file      (1000-TCATBALF-GET-NEXT loop)
  2. Join interest rates from DISCGRP         (1200-GET-INTEREST-RATE + 1200-A fallback)
  3. Compute monthly interest per category    (1300-COMPUTE-INTEREST)
  4. Aggregate total interest per account     (1050-UPDATE-ACCOUNT accumulation)
  5. Generate interest transaction records    (1300-B-WRITE-TX)
  6. Write transactions to silver.transaction (WRITE TRANSACT-FILE)
  7. Update account balances in silver.account (REWRITE ACCOUNT-FILE)
  8. Append audit rows to gold.interest_charges (SYSOUT equivalent)
  9. Validate data quality                    (post-run assertions)
 10. Write pipeline metrics                   (SYSOUT stats equivalent)

Paragraph stubs NOT implemented (matching COBOL behaviour):
  1400-COMPUTE-FEES — EXIT only in COBOL; fees not implemented.

Usage (Databricks notebook or job):
    %run ./pipeline    # notebook mode
    or invoked directly as a Python script by the Databricks job runner.

Parameters (replaces JCL PARM):
    run_date — YYYY-MM-DD string (e.g. "2026-04-07")
               Used as PARM-DATE prefix in generated TRAN-IDs.
"""

import sys
import traceback
from datetime import datetime, timezone

from pyspark.sql import SparkSession

from .account_updater import (
    assert_balance_integrity,
    update_account_balances,
    write_gold_interest_charges,
)
from .constants import DATABRICKS_JOB_NAME, SOURCE_PROGRAM
from .interest_calc import (
    aggregate_account_interest,
    compute_monthly_interest,
    join_interest_rates,
    read_account,
    read_disclosure_group,
    read_tran_cat_balance,
)
from .transaction_writer import (
    assert_tran_id_uniqueness,
    build_interest_transactions,
    read_card_xref,
    write_interest_transactions,
)
from .timestamp_utils import get_db2_format_timestamp


def get_run_date(spark: SparkSession) -> str:
    """
    Retrieve run_date from Databricks widget or environment.

    Replaces JCL: PARM='2026-04-07' passed to EXTERNAL-PARMS linkage section.
    Databricks widget name: run_date (configured in job parameters).

    Args:
        spark: Active SparkSession.

    Returns:
        YYYY-MM-DD string.

    Raises:
        ValueError: If run_date is empty or invalid.
    """
    try:
        # dbutils is injected by Databricks runtime
        dbutils = spark._jvm.com.databricks.dbutils  # type: ignore[attr-defined]
        run_date = dbutils.widgets.get("run_date")
    except Exception:
        # Fallback for local/test execution: check sys.argv or use today's date
        if len(sys.argv) > 1:
            run_date = sys.argv[1]
        else:
            run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    run_date = run_date.strip()
    if not run_date:
        raise ValueError(
            "run_date parameter is required (replaces JCL PARM-DATE). "
            "Provide via Databricks widget or as first CLI argument."
        )

    # Basic format validation
    try:
        datetime.strptime(run_date, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(
            f"run_date '{run_date}' is not a valid YYYY-MM-DD date: {exc}"
        ) from exc

    return run_date


def write_pipeline_metrics(
    spark: SparkSession,
    pipeline_run_id: str,
    run_date: str,
    tcatbal_rows: int,
    accounts_processed: int,
    accounts_not_found: int,
    transactions_written: int,
    gold_rows: int,
    status: str,
    error_message: str = "",
) -> None:
    """
    Append run statistics to migration_ctrl.pipeline_metrics.

    Replaces COBOL DISPLAY statements that printed counts and status to SYSOUT.
    """
    from pyspark.sql import Row

    metrics_row = Row(
        pipeline_name=DATABRICKS_JOB_NAME,
        source_program=SOURCE_PROGRAM,
        pipeline_run_id=pipeline_run_id,
        run_date=run_date,
        tcatbal_rows_read=tcatbal_rows,
        accounts_processed=accounts_processed,
        accounts_not_found=accounts_not_found,
        transactions_written=transactions_written,
        gold_rows_appended=gold_rows,
        status=status,
        error_message=error_message,
        run_ts=get_db2_format_timestamp(),
    )

    metrics_df = spark.createDataFrame([metrics_row])
    metrics_df.write.format("delta").mode("append").saveAsTable(
        "carddemo.migration_ctrl.pipeline_metrics"
    )


def run_pipeline(spark: SparkSession, run_date: str, pipeline_run_id: str) -> int:
    """
    Execute the full CBACT04C interest calculation pipeline.

    Args:
        spark: Active SparkSession.
        run_date: YYYY-MM-DD processing date (from JCL PARM-DATE).
        pipeline_run_id: Unique run identifier (from Databricks job context).

    Returns:
        Return code: 0 = success, non-zero = failure.
    """
    tcatbal_rows = 0
    accounts_processed = 0
    accounts_not_found = 0
    transactions_written = 0
    gold_rows = 0

    try:
        print(f"[{SOURCE_PROGRAM}] Starting interest calculation pipeline. run_date={run_date}")

        # -----------------------------------------------------------------------
        # Step 1: Read driving file (replaces OPEN + 1000-TCATBALF-GET-NEXT loop)
        # -----------------------------------------------------------------------
        tcatbal_df = read_tran_cat_balance(spark)
        tcatbal_rows = tcatbal_df.count()
        print(f"[{SOURCE_PROGRAM}] TCATBALF records read: {tcatbal_rows}")

        if tcatbal_rows == 0:
            print(f"[{SOURCE_PROGRAM}] WARNING: No TCATBALF records found. Pipeline exits cleanly.")
            write_pipeline_metrics(
                spark, pipeline_run_id, run_date,
                tcatbal_rows=0, accounts_processed=0, accounts_not_found=0,
                transactions_written=0, gold_rows=0, status="SUCCESS_NO_DATA",
            )
            return 0

        # -----------------------------------------------------------------------
        # Step 2: Load reference tables for joining
        # -----------------------------------------------------------------------
        acct_df = read_account(spark)
        discgrp_df = read_disclosure_group(spark)

        # -----------------------------------------------------------------------
        # Step 3: Join interest rates (1200-GET-INTEREST-RATE + 1200-A fallback)
        # -----------------------------------------------------------------------
        tcatbal_with_rate_df = join_interest_rates(tcatbal_df, acct_df, discgrp_df)

        # Log categories with no rate at all (warning, not abend)
        no_rate_count = tcatbal_with_rate_df.filter(
            tcatbal_with_rate_df["effective_int_rate"].isNull()
        ).count()
        if no_rate_count > 0:
            print(
                f"[{SOURCE_PROGRAM}] WARNING: {no_rate_count} TCATBALF rows have no rate "
                f"(neither primary group nor DEFAULT). These categories will be skipped."
            )

        # -----------------------------------------------------------------------
        # Step 4: Compute monthly interest (1300-COMPUTE-INTEREST, BR-1, BR-3)
        # -----------------------------------------------------------------------
        interest_df = compute_monthly_interest(tcatbal_with_rate_df)

        # -----------------------------------------------------------------------
        # Step 5: Aggregate to account level (1050-UPDATE-ACCOUNT accumulation)
        # -----------------------------------------------------------------------
        account_interest_df = aggregate_account_interest(interest_df)
        accounts_with_interest = account_interest_df.count()
        print(f"[{SOURCE_PROGRAM}] Accounts with non-zero interest: {accounts_with_interest}")

        if accounts_with_interest == 0:
            print(f"[{SOURCE_PROGRAM}] No interest charges to post. Pipeline exits cleanly.")
            write_pipeline_metrics(
                spark, pipeline_run_id, run_date,
                tcatbal_rows=tcatbal_rows, accounts_processed=0, accounts_not_found=0,
                transactions_written=0, gold_rows=0, status="SUCCESS_NO_INTEREST",
            )
            return 0

        # -----------------------------------------------------------------------
        # Step 6: Build interest transaction records (1300-B-WRITE-TX)
        # -----------------------------------------------------------------------
        xref_df = read_card_xref(spark)
        transactions_df = build_interest_transactions(
            account_interest_df, xref_df, run_date, pipeline_run_id
        )

        # Log missing XREF (warning, not abend — matches COBOL INVALID KEY handling)
        missing_xref = transactions_df.filter(
            transactions_df["tran_card_num"].isNull()
        ).count()
        if missing_xref > 0:
            print(
                f"[{SOURCE_PROGRAM}] WARNING: {missing_xref} account(s) have no XREF record. "
                f"tran_card_num will be NULL for those transactions."
            )

        # -----------------------------------------------------------------------
        # Step 7: Data quality check — TRAN-ID uniqueness
        # -----------------------------------------------------------------------
        assert_tran_id_uniqueness(transactions_df)

        # -----------------------------------------------------------------------
        # Step 8: Write interest transactions (WRITE TRANSACT-FILE)
        # -----------------------------------------------------------------------
        transactions_written = write_interest_transactions(spark, transactions_df)
        print(f"[{SOURCE_PROGRAM}] Interest transactions written: {transactions_written}")

        # -----------------------------------------------------------------------
        # Step 9: Update account balances (REWRITE ACCOUNT-FILE)
        # -----------------------------------------------------------------------
        accounts_processed, accounts_not_found = update_account_balances(
            spark, account_interest_df
        )
        print(
            f"[{SOURCE_PROGRAM}] Accounts updated: {accounts_processed}, "
            f"not found: {accounts_not_found}"
        )
        if accounts_not_found > 0:
            print(
                f"[{SOURCE_PROGRAM}] WARNING: {accounts_not_found} account(s) in TCATBALF "
                f"have no matching record in silver.account."
            )

        # -----------------------------------------------------------------------
        # Step 10: Data quality check — balance integrity
        # -----------------------------------------------------------------------
        assert_balance_integrity(account_interest_df, transactions_df)

        # -----------------------------------------------------------------------
        # Step 11: Append gold audit rows
        # -----------------------------------------------------------------------
        gold_rows = write_gold_interest_charges(
            spark,
            interest_df,
            account_interest_df,
            transactions_df,
            run_date,
            pipeline_run_id,
        )
        print(f"[{SOURCE_PROGRAM}] Gold interest_charges rows appended: {gold_rows}")

        # -----------------------------------------------------------------------
        # Step 12: Write pipeline metrics (SYSOUT stats)
        # -----------------------------------------------------------------------
        write_pipeline_metrics(
            spark,
            pipeline_run_id=pipeline_run_id,
            run_date=run_date,
            tcatbal_rows=tcatbal_rows,
            accounts_processed=accounts_processed,
            accounts_not_found=accounts_not_found,
            transactions_written=transactions_written,
            gold_rows=gold_rows,
            status="SUCCESS",
        )

        print(f"[{SOURCE_PROGRAM}] Pipeline completed successfully.")
        return 0

    except Exception as exc:  # noqa: BLE001
        error_msg = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
        print(f"[{SOURCE_PROGRAM}] PIPELINE FAILED: {error_msg}", file=sys.stderr)

        try:
            write_pipeline_metrics(
                spark,
                pipeline_run_id=pipeline_run_id,
                run_date=run_date,
                tcatbal_rows=tcatbal_rows,
                accounts_processed=accounts_processed,
                accounts_not_found=accounts_not_found,
                transactions_written=transactions_written,
                gold_rows=gold_rows,
                status="FAILED",
                error_message=error_msg[:2000],  # truncate for storage
            )
        except Exception:  # noqa: BLE001
            pass  # Do not mask original exception with metrics write failure

        raise


def main() -> None:
    """
    Entry point for Databricks job execution.

    Databricks invokes this via the Python script task type.
    Return code is communicated via dbutils.notebook.exit() for workflow conditional tasks.
    """
    spark = SparkSession.builder.appName(DATABRICKS_JOB_NAME).getOrCreate()

    # Retrieve pipeline run ID from Databricks runtime context
    try:
        pipeline_run_id = spark.conf.get("spark.databricks.job.runId", "local-run")
    except Exception:
        pipeline_run_id = "local-run"

    run_date = get_run_date(spark)
    return_code = run_pipeline(spark, run_date, pipeline_run_id)

    # Communicate return code to Databricks Workflow for conditional task routing
    # Replaces JCL RETURN-CODE / COND parameter handling
    try:
        dbutils = spark._jvm.com.databricks.dbutils  # type: ignore[attr-defined]
        dbutils.notebook.exit(str(return_code))
    except Exception:
        sys.exit(return_code)


if __name__ == "__main__":
    main()
