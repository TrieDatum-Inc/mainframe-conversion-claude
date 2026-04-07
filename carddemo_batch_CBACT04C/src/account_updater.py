"""
Account balance update logic for CBACT04C.

Replaces COBOL paragraph 1050-UPDATE-ACCOUNT (REWRITE half):
  ADD WS-TOTAL-INT TO ACCT-CURR-BAL
  MOVE ZEROS TO ACCT-CURR-CYC-CREDIT
  MOVE ZEROS TO ACCT-CURR-CYC-DEBIT
  REWRITE ACCOUNT-FILE FROM ACCOUNT-RECORD

Uses Delta MERGE for idempotency (safe on re-run):
  WHEN MATCHED → UPDATE acct_curr_bal, zero out cycle amounts
  WHEN NOT MATCHED → do nothing (account not found → log warning, no abend)

Also handles the gold.interest_charges audit table write (append).
"""

from decimal import Decimal

from delta.tables import DeltaTable
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DecimalType, IntegerType


def update_account_balances(
    spark: SparkSession,
    account_interest_df: DataFrame,
) -> tuple[int, int]:
    """
    Apply interest charges to account balances via Delta MERGE.

    Replaces COBOL paragraph 1050-UPDATE-ACCOUNT:
      ACCT-CURR-BAL    += WS-TOTAL-INT
      ACCT-CURR-CYC-CREDIT = 0
      ACCT-CURR-CYC-DEBIT  = 0
      REWRITE ACCOUNT-FILE FROM ACCOUNT-RECORD

    COBOL abends on REWRITE failure. PySpark raises an exception on Delta write failure,
    which causes the Databricks task to fail — equivalent behaviour.

    If an account is not found in Silver (WHEN NOT MATCHED):
      - COBOL: DISPLAY 'ACCOUNT NOT FOUND' + continue (no abend on READ, abend on REWRITE)
      - PySpark: row is silently skipped (WHEN NOT MATCHED → ignored in MERGE).
        Caller should log a warning if accounts_not_found_count > 0.

    Args:
        spark: Active SparkSession.
        account_interest_df: Output of aggregate_account_interest(); columns:
            acct_id (BIGINT), total_interest (DECIMAL(11,2)).

    Returns:
        Tuple (accounts_updated, accounts_not_found).
    """
    target_table = DeltaTable.forName(spark, "carddemo.silver.account")

    # Prepare source with only the columns needed for the MERGE condition and SET clauses
    source_df = account_interest_df.select(
        F.col("acct_id"),
        F.col("total_interest").cast(DecimalType(12, 2)).alias("total_interest"),
    )

    (
        target_table.alias("target")
        .merge(
            source_df.alias("source"),
            condition="target.acct_id = source.acct_id",
        )
        .whenMatchedUpdate(
            set={
                # ACCT-CURR-BAL += WS-TOTAL-INT
                "acct_curr_bal": "CAST(target.acct_curr_bal + source.total_interest AS DECIMAL(12,2))",
                # MOVE ZEROS TO ACCT-CURR-CYC-CREDIT
                "acct_curr_cyc_credit": "CAST(0 AS DECIMAL(12,2))",
                # MOVE ZEROS TO ACCT-CURR-CYC-DEBIT
                "acct_curr_cyc_debit": "CAST(0 AS DECIMAL(12,2))",
                # Silver audit timestamp
                "_silver_last_updated_ts": "CURRENT_TIMESTAMP()",
            }
        )
        .execute()
    )

    # Determine how many accounts were actually in Silver (matched)
    accounts_in_tcatbal = source_df.count()
    accounts_in_silver = (
        spark.read.format("delta")
        .table("carddemo.silver.account")
        .join(source_df.select("acct_id"), on="acct_id", how="inner")
        .count()
    )
    accounts_not_found = accounts_in_tcatbal - accounts_in_silver

    return accounts_in_silver, accounts_not_found


def write_gold_interest_charges(
    spark: SparkSession,
    interest_df: DataFrame,
    account_interest_df: DataFrame,
    transactions_df: DataFrame,
    run_date: str,
    pipeline_run_id: str,
) -> int:
    """
    Append interest charge detail to the gold audit table.

    The gold.interest_charges table is an audit trail with per-category granularity,
    replacing the COBOL DISPLAY statements that printed each processed record to SYSOUT.

    Args:
        spark: Active SparkSession.
        interest_df: Per-category interest rows (from compute_monthly_interest).
        account_interest_df: Account-level aggregated totals.
        transactions_df: Generated TRAN-RECORD rows (for tran_id linkage).
        run_date: YYYY-MM-DD run date string.
        pipeline_run_id: Databricks pipeline run ID.

    Returns:
        Count of rows appended to gold table.
    """
    from pyspark.sql.types import DateType

    # Parse run_date to extract year and month for partition columns
    run_date_col = F.to_date(F.lit(run_date), "yyyy-MM-dd")

    # Join category-level detail with account aggregates and transactions
    tran_id_lookup = transactions_df.select(
        "acct_id",
        "tran_id",
    )

    gold_df = (
        interest_df
        .join(
            account_interest_df.select("acct_id", "total_interest"),
            on="acct_id",
            how="left",
        )
        .join(tran_id_lookup, on="acct_id", how="left")
        .join(
            spark.read.format("delta")
            .table("carddemo.silver.card_xref")
            .select("acct_id", F.col("card_num")),
            on="acct_id",
            how="left",
        )
        .select(
            F.col("tran_id"),
            F.col("acct_id"),
            F.col("card_num"),
            F.col("acct_group_id").alias("dis_acct_group_id"),
            F.lit("01").alias("tran_type_cd"),
            F.lit(5).cast(IntegerType()).alias("tran_cat_cd"),
            F.col("tran_cat_bal").cast(DecimalType(11, 2)).alias("tran_cat_bal_basis"),
            F.col("effective_int_rate").cast(DecimalType(7, 4)).alias("dis_int_rate"),
            F.col("monthly_interest").cast(DecimalType(11, 2)),
            F.col("total_interest").cast(DecimalType(11, 2)),
            F.year(run_date_col).alias("charge_year"),
            F.month(run_date_col).alias("charge_month"),
            run_date_col.alias("run_date"),
            F.current_timestamp().alias("_gold_load_ts"),
            F.lit(pipeline_run_id).alias("_gold_pipeline_run_id"),
        )
    )

    gold_df.write.format("delta").mode("append").saveAsTable("carddemo.gold.interest_charges")

    return gold_df.count()


def assert_balance_integrity(
    account_interest_df: DataFrame,
    transactions_df: DataFrame,
) -> None:
    """
    Data quality check: sum of interest charges must equal sum of balance increments.

    Specification section 4.8 requirement:
      'Sum of interest charges must equal sum of account balance increases'

    Args:
        account_interest_df: Account-level aggregated totals (total_interest per account).
        transactions_df: Generated interest transaction records (tran_amt per record).

    Raises:
        AssertionError: If the two sums do not match.
    """
    from decimal import Decimal

    balance_sum = account_interest_df.agg(
        F.sum("total_interest").cast(DecimalType(12, 2)).alias("total")
    ).collect()[0]["total"] or Decimal("0")

    charge_sum = transactions_df.agg(
        F.sum("tran_amt").cast(DecimalType(12, 2)).alias("total")
    ).collect()[0]["total"] or Decimal("0")

    if balance_sum != charge_sum:
        raise AssertionError(
            f"Balance integrity check failed: "
            f"sum(total_interest)={balance_sum} != sum(tran_amt)={charge_sum}"
        )
