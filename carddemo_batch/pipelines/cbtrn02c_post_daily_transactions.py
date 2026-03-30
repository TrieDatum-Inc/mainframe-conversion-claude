#!/usr/bin/env python3
# ============================================================================
# CBTRN02C - Post Daily Transactions
# ============================================================================
# Migrated from: CBTRN02C.CBL (COBOL Batch Program)
# Function:      Read the daily transaction file, validate each transaction,
#                post valid ones to the transaction file, update account
#                balances and category balances, and write rejects.
#
# COBOL Sequential Processing Note:
#   The original COBOL processes transactions one at a time, sequentially.
#   Each transaction's account update (balance changes) affects the overlimit
#   validation of subsequent transactions for the SAME account. This pipeline
#   replicates that sequential dependency using window functions with running
#   cumulative sums ordered by the original timestamp.
#
# Input:   carddemo.daily_transactions   (DALYTRAN DD - sequential)
# Lookup:  carddemo.card_xref            (XREFFILE DD - VSAM KSDS)
#          carddemo.accounts             (ACCTFILE DD - VSAM KSDS)
# Output:  carddemo.transactions         (TRANFILE DD - VSAM KSDS)
#          carddemo.daily_transaction_rejects (DALYREJS DD - sequential)
# Update:  carddemo.accounts             (balance updates)
#          carddemo.transaction_category_balances (TCATBALF DD - VSAM KSDS)
#
# Usage:
#   Databricks notebook : Run all cells (schema defaults to 'carddemo')
#   spark-submit        : spark-submit --packages io.delta:delta-spark_2.12:3.1.0 \
#                           cbtrn02c_post_daily_transactions.py --schema carddemo
# ============================================================================

import argparse
import sys

from pyspark.sql import SparkSession
import pyspark.sql.functions as F
from pyspark.sql.window import Window
from datetime import datetime


# ---------------------------------------------------------------------------
# Runtime detection: Databricks vs standalone spark-submit
# ---------------------------------------------------------------------------
def is_databricks():
    """Return True when running inside a Databricks notebook."""
    try:
        # dbutils is injected by Databricks runtime
        _ = dbutils  # noqa: F821
        return True
    except NameError:
        return False


def get_spark(schema):
    """Build or retrieve SparkSession with Delta Lake support."""
    if is_databricks():
        spark = SparkSession.builder.getOrCreate()
    else:
        spark = (
            SparkSession.builder
            .appName("CBTRN02C_PostDailyTransactions")
            .config("spark.sql.extensions",
                    "io.delta.sql.DeltaSparkSessionExtension")
            .config("spark.sql.catalog.spark_catalog",
                    "org.apache.spark.sql.delta.catalog.DeltaCatalog")
            .getOrCreate()
        )
    spark.sql(f"USE {schema}")
    return spark


def parse_args():
    """Parse CLI arguments (ignored silently inside Databricks)."""
    parser = argparse.ArgumentParser(
        description="CBTRN02C - Post Daily Transactions")
    parser.add_argument("--schema", default="carddemo",
                        help="Catalog schema / database name (default: carddemo)")
    # Parse only known args so Databricks/spark-submit extra flags don't fail
    args, _ = parser.parse_known_args()
    return args


# ============================================================================
# Main pipeline logic
# ============================================================================
def run(spark):
    print("=" * 70)
    print("START OF EXECUTION OF PROGRAM CBTRN02C (PySpark)")
    print("=" * 70)

    # ------------------------------------------------------------------
    # Step 1: Read all source tables
    # ------------------------------------------------------------------
    df_daily_raw = spark.table("daily_transactions")
    df_xref = spark.table("card_xref")
    df_accounts = spark.table("accounts")
    df_tcatbal = spark.table("transaction_category_balances")

    total_input_count = df_daily_raw.count()
    print(f"Total daily transactions in input: {total_input_count}")

    # ------------------------------------------------------------------
    # Step 1a: IDEMPOTENCY GUARD — skip already-processed transactions
    #   If the job is re-run with the same input data, transactions that
    #   were already posted (exist in `transactions` by tran_id) or
    #   already rejected (exist in `daily_transaction_rejects` by
    #   dalytran_id) must be excluded so that balances are not doubled
    #   and duplicate rows are not created.
    # ------------------------------------------------------------------
    df_existing_posted = spark.table("transactions").select(
        F.col("tran_id").alias("_posted_id")
    )
    df_existing_rejects = spark.table("daily_transaction_rejects").select(
        F.col("dalytran_id").alias("_reject_id")
    ).distinct()

    df_daily = (
        df_daily_raw
        .join(df_existing_posted,
              df_daily_raw.dalytran_id == df_existing_posted._posted_id,
              "left_anti")
        .join(df_existing_rejects,
              df_daily_raw.dalytran_id == df_existing_rejects._reject_id,
              "left_anti")
    )

    total_count = df_daily.count()
    skipped_count = total_input_count - total_count
    if skipped_count > 0:
        print(f"Skipped {skipped_count} already-processed transactions "
              "(idempotency guard)")
    print(f"New daily transactions to process: {total_count}")

    if total_count == 0:
        print("Nothing to process — all input transactions were already "
              "posted or rejected in a prior run.")
        print("=" * 70)
        print("RETURN CODE: 0 (SUCCESS — idempotent no-op)")
        print("=" * 70)
        return 0

    # ------------------------------------------------------------------
    # Step 2: Validation - Card number lookup (COBOL: 1500-A-LOOKUP-XREF)
    #   Join daily transactions with card_xref on card number.
    #   If no match -> reject code 100: "INVALID CARD NUMBER FOUND"
    # ------------------------------------------------------------------
    df_with_xref = df_daily.join(
        df_xref,
        df_daily.dalytran_card_num == df_xref.xref_card_num,
        "left"
    )

    df_invalid_card = df_with_xref.filter(F.col("xref_card_num").isNull())
    df_valid_card = df_with_xref.filter(F.col("xref_card_num").isNotNull())

    # ------------------------------------------------------------------
    # Step 3: Validation - Account lookup (COBOL: 1500-B-LOOKUP-ACCT)
    #   Join with accounts on xref_acct_id.
    #   If no match -> reject code 101: "ACCOUNT RECORD NOT FOUND"
    # ------------------------------------------------------------------
    df_with_acct = df_valid_card.join(
        df_accounts,
        df_valid_card.xref_acct_id == df_accounts.acct_id,
        "left"
    )

    df_no_account = df_with_acct.filter(F.col("acct_id").isNull())
    df_has_account = df_with_acct.filter(F.col("acct_id").isNotNull())

    # ------------------------------------------------------------------
    # Step 4: Validation - Overlimit & Expiration checks
    #   (COBOL: 1500-B-LOOKUP-ACCT continuation)
    #
    #   CRITICAL: The COBOL processes sequentially. Each posted transaction
    #   updates ACCT-CURR-CYC-CREDIT or ACCT-CURR-CYC-DEBIT, which affects
    #   the overlimit check for the NEXT transaction on the same account.
    #   We replicate this using a running cumulative sum window.
    #
    #   Overlimit (102):  temp_bal = cyc_credit - cyc_debit + running_amt
    #                     IF credit_limit < temp_bal THEN reject
    #   Expiration (103): IF expiraion_date < tran_date THEN reject
    #   Priority: code 103 overwrites 102 (matches COBOL behaviour).
    # ------------------------------------------------------------------
    window_acct = (
        Window.partitionBy("acct_id")
        .orderBy("dalytran_orig_ts")
        .rowsBetween(Window.unboundedPreceding, Window.currentRow)
    )

    df_ordered = df_has_account.withColumn(
        "running_amt_sum",
        F.sum("dalytran_amt").over(window_acct)
    )

    df_validated = (
        df_ordered
        .withColumn(
            "ws_temp_bal",
            F.col("acct_curr_cyc_credit") - F.col("acct_curr_cyc_debit")
            + F.col("running_amt_sum"))
        .withColumn(
            "is_overlimit",
            F.when(F.col("acct_credit_limit") < F.col("ws_temp_bal"), True)
            .otherwise(False))
        .withColumn(
            "is_expired",
            F.when(
                F.col("acct_expiraion_date")
                < F.substring("dalytran_orig_ts", 1, 10), True)
            .otherwise(False))
        .withColumn(
            "reject_reason_code",
            F.when(F.col("is_expired"), 103)
            .when(F.col("is_overlimit"), 102)
            .otherwise(0))
        .withColumn(
            "reject_reason_desc",
            F.when(F.col("reject_reason_code") == 103,
                   F.lit("TRANSACTION RECEIVED AFTER ACCT EXPIRATION"))
            .when(F.col("reject_reason_code") == 102,
                  F.lit("OVERLIMIT TRANSACTION"))
            .otherwise(F.lit("")))
    )

    df_valid_transactions = df_validated.filter(
        F.col("reject_reason_code") == 0)
    df_validation_rejects = df_validated.filter(
        F.col("reject_reason_code") != 0)

    # ------------------------------------------------------------------
    # Step 5: Build all reject records
    #   invalid card (100) + no account (101) + validation fails (102/103)
    # ------------------------------------------------------------------
    reject_cols = [
        "dalytran_id", "dalytran_type_cd", "dalytran_cat_cd",
        "dalytran_source", "dalytran_desc", "dalytran_amt",
        "dalytran_merchant_id", "dalytran_merchant_name",
        "dalytran_merchant_city", "dalytran_merchant_zip",
        "dalytran_card_num", "dalytran_orig_ts", "dalytran_proc_ts",
        "reject_reason_code", "reject_reason_desc"
    ]

    df_rejects_100 = (
        df_invalid_card
        .withColumn("reject_reason_code", F.lit(100))
        .withColumn("reject_reason_desc",
                    F.lit("INVALID CARD NUMBER FOUND"))
        .select(reject_cols)
    )

    df_rejects_101 = (
        df_no_account
        .withColumn("reject_reason_code", F.lit(101))
        .withColumn("reject_reason_desc",
                    F.lit("ACCOUNT RECORD NOT FOUND"))
        .select(reject_cols)
    )

    df_rejects_102_103 = df_validation_rejects.select(reject_cols)

    df_all_rejects = (
        df_rejects_100
        .unionByName(df_rejects_101)
        .unionByName(df_rejects_102_103)
    )

    reject_count = df_all_rejects.count()
    print(f"Rejected transactions: {reject_count}")

    # ------------------------------------------------------------------
    # Step 6: Write rejects to daily_transaction_rejects table
    #   (COBOL: 2500-WRITE-REJECT-REC)
    #   Uses MERGE to prevent duplicates on re-run (idempotent).
    #   Match on dalytran_id + reject_reason_code (a transaction can
    #   only have one reject reason per run).
    # ------------------------------------------------------------------
    if reject_count > 0:
        df_all_rejects.createOrReplaceTempView("new_rejects")
        spark.sql("""
            MERGE INTO daily_transaction_rejects AS target
            USING new_rejects AS source
            ON  target.dalytran_id          = source.dalytran_id
            AND target.reject_reason_code   = source.reject_reason_code
            WHEN NOT MATCHED THEN
                INSERT *
        """)
        print(f"Wrote {reject_count} reject records to "
              "daily_transaction_rejects (MERGE/idempotent)")

    # ------------------------------------------------------------------
    # Step 7: Build posted transaction records
    #   (COBOL: 2000-POST-TRANSACTION -> field mapping + timestamp)
    # ------------------------------------------------------------------
    proc_ts = datetime.now().strftime("%Y-%m-%d-%H.%M.%S.") + "000000"

    df_posted = df_valid_transactions.select(
        F.col("dalytran_id").alias("tran_id"),
        F.col("dalytran_type_cd").alias("tran_type_cd"),
        F.col("dalytran_cat_cd").alias("tran_cat_cd"),
        F.col("dalytran_source").alias("tran_source"),
        F.col("dalytran_desc").alias("tran_desc"),
        F.col("dalytran_amt").alias("tran_amt"),
        F.col("dalytran_merchant_id").alias("tran_merchant_id"),
        F.col("dalytran_merchant_name").alias("tran_merchant_name"),
        F.col("dalytran_merchant_city").alias("tran_merchant_city"),
        F.col("dalytran_merchant_zip").alias("tran_merchant_zip"),
        F.col("dalytran_card_num").alias("tran_card_num"),
        F.col("dalytran_orig_ts").alias("tran_orig_ts"),
        F.lit(proc_ts).alias("tran_proc_ts")
    )

    posted_count = df_posted.count()
    print(f"Valid transactions to post: {posted_count}")

    # ------------------------------------------------------------------
    # Step 8: Write posted transactions to transactions table
    #   (COBOL: 2900-WRITE-TRANSACTION-FILE)
    #   Uses MERGE on tran_id (PK) to prevent duplicates on re-run.
    #   Combined with the Step 1a early filter this is a belt-and-
    #   suspenders safety net.
    # ------------------------------------------------------------------
    if posted_count > 0:
        df_posted.createOrReplaceTempView("new_transactions")
        spark.sql("""
            MERGE INTO transactions AS target
            USING new_transactions AS source
            ON target.tran_id = source.tran_id
            WHEN NOT MATCHED THEN
                INSERT *
        """)
        print(f"Wrote {posted_count} posted transactions to transactions "
              "(MERGE/idempotent)")

    # ------------------------------------------------------------------
    # Step 9: Update transaction category balances (TCATBAL)
    #   (COBOL: 2700-UPDATE-TCATBAL)
    #   Upsert: if exists (acct_id, type_cd, cat_cd) -> add amount
    #           if not -> create record with amount
    # ------------------------------------------------------------------
    df_catbal_updates = df_valid_transactions.groupBy(
        F.col("xref_acct_id").alias("trancat_acct_id"),
        F.col("dalytran_type_cd").alias("trancat_type_cd"),
        F.col("dalytran_cat_cd").alias("trancat_cd")
    ).agg(
        F.sum("dalytran_amt").alias("delta_amt")
    )

    df_catbal_updates.createOrReplaceTempView("catbal_updates")

    spark.sql("""
        MERGE INTO transaction_category_balances AS target
        USING catbal_updates AS source
        ON  target.trancat_acct_id = source.trancat_acct_id
        AND target.trancat_type_cd = source.trancat_type_cd
        AND target.trancat_cd      = source.trancat_cd
        WHEN MATCHED THEN
            UPDATE SET tran_cat_bal = target.tran_cat_bal + source.delta_amt
        WHEN NOT MATCHED THEN
            INSERT (trancat_acct_id, trancat_type_cd, trancat_cd, tran_cat_bal)
            VALUES (source.trancat_acct_id, source.trancat_type_cd,
                    source.trancat_cd, source.delta_amt)
    """)

    print("Updated transaction_category_balances (MERGE/upsert)")

    # ------------------------------------------------------------------
    # Step 10: Update account balances
    #   (COBOL: 2800-UPDATE-ACCOUNT-REC)
    #
    #   ACCT-CURR-BAL += DALYTRAN-AMT            (always)
    #   IF DALYTRAN-AMT >= 0  -> CYC-CREDIT +=
    #   ELSE                  -> CYC-DEBIT  +=
    # ------------------------------------------------------------------
    df_acct_updates = df_valid_transactions.groupBy(
        F.col("xref_acct_id").alias("upd_acct_id")
    ).agg(
        F.sum("dalytran_amt").alias("total_amt"),
        F.sum(F.when(F.col("dalytran_amt") >= 0, F.col("dalytran_amt"))
              .otherwise(0)).alias("total_credit"),
        F.sum(F.when(F.col("dalytran_amt") < 0, F.col("dalytran_amt"))
              .otherwise(0)).alias("total_debit")
    )

    df_acct_updates.createOrReplaceTempView("acct_updates")

    spark.sql("""
        MERGE INTO accounts AS target
        USING acct_updates AS source
        ON target.acct_id = source.upd_acct_id
        WHEN MATCHED THEN
            UPDATE SET
                acct_curr_bal       = target.acct_curr_bal       + source.total_amt,
                acct_curr_cyc_credit = target.acct_curr_cyc_credit + source.total_credit,
                acct_curr_cyc_debit  = target.acct_curr_cyc_debit  + source.total_debit
    """)

    print("Updated account balances (MERGE)")

    # ------------------------------------------------------------------
    # Final Summary (COBOL: DISPLAY counters at end)
    # ------------------------------------------------------------------
    print("=" * 70)
    print(f"TRANSACTIONS READ    : {total_count}")
    print(f"TRANSACTIONS POSTED  : {posted_count}")
    print(f"TRANSACTIONS REJECTED: {reject_count}")

    rc = 4 if reject_count > 0 else 0
    print(f"RETURN CODE: {rc}"
          f"{' (WARNING - some transactions rejected)' if rc else ' (SUCCESS)'}")
    print("=" * 70)
    print("END OF EXECUTION OF PROGRAM CBTRN02C (PySpark)")
    print("=" * 70)

    return rc


# ============================================================================
# Entry point
# ============================================================================
if __name__ == "__main__":
    args = parse_args()
    spark = get_spark(args.schema)
    rc = run(spark)
    spark.stop()
    sys.exit(rc)
