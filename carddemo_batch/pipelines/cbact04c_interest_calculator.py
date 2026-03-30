#!/usr/bin/env python3
# ============================================================================
# CBACT04C - Interest Calculator
# ============================================================================
# Migrated from: CBACT04C.CBL (COBOL Batch Program)
# Function:      Calculate monthly interest for each account based on
#                transaction category balances and disclosure group rates.
#                Write interest transaction records and update account balances.
#
# COBOL Sequential Processing Note:
#   The COBOL reads TCATBAL-FILE sequentially (sorted by account). On each
#   account break, it updates the previous account's balance. The interest
#   calculation is: monthly_interest = (category_balance * annual_rate) / 1200.
#   The total interest across all categories is added to ACCT-CURR-BAL, and
#   ACCT-CURR-CYC-CREDIT and ACCT-CURR-CYC-DEBIT are reset to zero.
#
# Input:   carddemo.transaction_category_balances (TCATBALF DD - sequential)
# Lookup:  carddemo.accounts                     (ACCTFILE DD - VSAM KSDS)
#          carddemo.card_xref                     (XREFFILE DD - VSAM KSDS)
#          carddemo.disclosure_groups             (DISCGRP DD - VSAM KSDS)
# Output:  carddemo.transactions                 (TRANSACT DD - sequential)
# Update:  carddemo.accounts                     (balance updates + cycle reset)
#
# Usage:
#   Databricks notebook : Set widget parm_date, then run all cells
#   spark-submit        : spark-submit --packages io.delta:delta-spark_2.12:3.1.0 \
#                           cbact04c_interest_calculator.py \
#                           --schema carddemo --parm-date 2025-03-08
# ============================================================================

import argparse
import sys

from pyspark.sql import SparkSession
import pyspark.sql.functions as F
from pyspark.sql.window import Window
from datetime import datetime


# ---------------------------------------------------------------------------
# Runtime detection
# ---------------------------------------------------------------------------
def is_databricks():
    """Return True when running inside a Databricks notebook."""
    try:
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
            .appName("CBACT04C_InterestCalculator")
            .config("spark.sql.extensions",
                    "io.delta.sql.DeltaSparkSessionExtension")
            .config("spark.sql.catalog.spark_catalog",
                    "org.apache.spark.sql.delta.catalog.DeltaCatalog")
            .getOrCreate()
        )
    spark.sql(f"USE {schema}")
    return spark


def resolve_parm_date(cli_value):
    """Resolve the processing date: CLI arg > Databricks widget > today."""
    if cli_value:
        return cli_value
    if is_databricks():
        try:
            return dbutils.widgets.get("parm_date")  # noqa: F821
        except Exception:
            pass
    return datetime.now().strftime("%Y-%m-%d")


def parse_args():
    parser = argparse.ArgumentParser(
        description="CBACT04C - Interest Calculator")
    parser.add_argument("--schema", default="carddemo",
                        help="Catalog schema / database name")
    parser.add_argument("--parm-date", default=None,
                        help="Processing date YYYY-MM-DD (default: today)")
    args, _ = parser.parse_known_args()
    return args


# ============================================================================
# Main pipeline logic
# ============================================================================
def run(spark, parm_date):
    print("=" * 70)
    print("START OF EXECUTION OF PROGRAM CBACT04C (PySpark)")
    print(f"Processing Date: {parm_date}")
    print("=" * 70)

    # ------------------------------------------------------------------
    # Step 1: IDEMPOTENCY GUARD — detect prior run for this parm_date
    #
    #   Interest transaction IDs are deterministic:
    #       tran_id = parm_date + 6-digit row suffix
    #   e.g. "2025-03-08000001", "2025-03-08000002", ...
    #
    #   If any transactions whose tran_id starts with this parm_date
    #   already exist, this is a re-run — exit immediately.
    # ------------------------------------------------------------------
    existing_count = (
        spark.table("transactions")
        .filter(F.col("tran_id").startswith(parm_date))
        .count()
    )

    if existing_count > 0:
        print(f"Found {existing_count} interest transactions already posted "
              f"for parm_date={parm_date} (tran_id prefix match).")
        print("Skipping to prevent duplicate posting.")
        print("=" * 70)
        print("RETURN CODE: 0 (SUCCESS — idempotent no-op)")
        print("=" * 70)
        return

    # ------------------------------------------------------------------
    # Step 2: Read source tables
    # ------------------------------------------------------------------
    df_tcatbal = spark.table("transaction_category_balances")
    df_accounts = spark.table("accounts")
    df_xref = spark.table("card_xref")
    df_discgrp = spark.table("disclosure_groups")

    record_count = df_tcatbal.count()
    print(f"Transaction category balance records to process: {record_count}")

    # ------------------------------------------------------------------
    # Step 3: Join TCATBAL with ACCOUNTS to get ACCT-GROUP-ID
    #   (COBOL: 1100-GET-ACCT-DATA - random read by account ID)
    # ------------------------------------------------------------------
    df_with_acct = df_tcatbal.join(
        df_accounts.select("acct_id", "acct_group_id", "acct_curr_bal"),
        df_tcatbal.trancat_acct_id == df_accounts.acct_id,
        "inner"
    )

    # ------------------------------------------------------------------
    # Step 4: Join with CARD_XREF to get card number
    #   (COBOL: 1110-GET-XREF-DATA - read by alternate key)
    #   Pick one card per account (first card number)
    # ------------------------------------------------------------------
    w_xref = Window.partitionBy("xref_acct_id").orderBy("xref_card_num")
    df_xref_dedup = (
        df_xref
        .withColumn("rn", F.row_number().over(w_xref))
        .filter(F.col("rn") == 1)
        .drop("rn")
    )

    df_with_card = (
        df_with_acct.join(
            df_xref_dedup.select(
                F.col("xref_acct_id").alias("xr_acct_id"),
                F.col("xref_card_num")),
            df_with_acct.acct_id == F.col("xr_acct_id"),
            "left")
        .drop("xr_acct_id")
    )

    # ------------------------------------------------------------------
    # Step 5: Interest rate lookup with DEFAULT fallback
    #   (COBOL: 1200-GET-INTEREST-RATE + 1200-A-GET-DEFAULT-INT-RATE)
    #   Primary:  (ACCT-GROUP-ID, TYPE-CD, CAT-CD)
    #   Fallback: ('DEFAULT',     TYPE-CD, CAT-CD)
    # ------------------------------------------------------------------
    df_discgrp_primary = df_discgrp.alias("dg_primary")
    df_with_rate = df_with_card.join(
        df_discgrp_primary,
        (df_with_card.acct_group_id == df_discgrp_primary.dis_acct_group_id) &
        (df_with_card.trancat_type_cd == df_discgrp_primary.dis_tran_type_cd) &
        (df_with_card.trancat_cd == df_discgrp_primary.dis_tran_cat_cd),
        "left"
    )

    df_discgrp_default = (
        df_discgrp
        .filter(F.col("dis_acct_group_id") == "DEFAULT")
        .select(
            F.col("dis_tran_type_cd").alias("def_type_cd"),
            F.col("dis_tran_cat_cd").alias("def_cat_cd"),
            F.col("dis_int_rate").alias("def_int_rate"))
    )

    df_with_fallback = df_with_rate.join(
        df_discgrp_default,
        (df_with_rate.trancat_type_cd == df_discgrp_default.def_type_cd) &
        (df_with_rate.trancat_cd == df_discgrp_default.def_cat_cd),
        "left"
    )

    df_resolved = df_with_fallback.withColumn(
        "effective_int_rate",
        F.coalesce(F.col("dis_int_rate"), F.col("def_int_rate"), F.lit(0))
    )

    # ------------------------------------------------------------------
    # Step 6: Compute monthly interest per category
    #   (COBOL: 1300-COMPUTE-INTEREST)
    #   Formula: monthly_interest = (TRAN-CAT-BAL * DIS-INT-RATE) / 1200
    # ------------------------------------------------------------------
    df_interest = (
        df_resolved
        .filter(F.col("effective_int_rate") != 0)
        .withColumn(
            "monthly_interest",
            (F.col("tran_cat_bal") * F.col("effective_int_rate"))
            / F.lit(1200))
    )

    interest_rows = df_interest.count()
    print(f"Category rows with non-zero interest rate: {interest_rows}")

    # ------------------------------------------------------------------
    # Step 7: Generate interest transaction records
    #   (COBOL: 1300-B-WRITE-TX)
    # ------------------------------------------------------------------
    w_suffix = Window.orderBy(
        "trancat_acct_id", "trancat_type_cd", "trancat_cd")
    proc_ts = datetime.now().strftime("%Y-%m-%d-%H.%M.%S.") + "000000"

    df_tran_records = (
        df_interest
        .withColumn(
            "tran_id_suffix",
            F.lpad(F.row_number().over(w_suffix).cast("string"), 6, "0"))
        .select(
            F.concat(F.lit(parm_date),
                     F.col("tran_id_suffix")).alias("tran_id"),
            F.col("acct_id").alias("_src_acct_id"),
            F.lit("01").alias("tran_type_cd"),
            F.lit(5).alias("tran_cat_cd"),
            F.lit("System").alias("tran_source"),
            F.concat(F.lit("Int. for a/c "),
                     F.col("acct_id").cast("string")).alias("tran_desc"),
            F.col("monthly_interest")
            .cast("decimal(11,2)").alias("tran_amt"),
            F.lit(0).cast("bigint").alias("tran_merchant_id"),
            F.lit("").alias("tran_merchant_name"),
            F.lit("").alias("tran_merchant_city"),
            F.lit("").alias("tran_merchant_zip"),
            F.coalesce(F.col("xref_card_num"),
                       F.lit("")).alias("tran_card_num"),
            F.lit(proc_ts).alias("tran_orig_ts"),
            F.lit(proc_ts).alias("tran_proc_ts"))
    )

    tran_count = df_tran_records.count()
    print(f"Interest transactions generated: {tran_count}")

    if tran_count == 0:
        print("No interest transactions to post.")
        print("=" * 70)
        print("RETURN CODE: 0 (SUCCESS — nothing to post)")
        print("=" * 70)
        return

    # ------------------------------------------------------------------
    # Step 8: Write interest transactions
    #   (COBOL: 1300-B-WRITE-TX)
    #   Safe to INSERT because Step 1 already confirmed no records
    #   exist for this parm_date.
    # ------------------------------------------------------------------
    tran_table_cols = [
        "tran_id", "tran_type_cd", "tran_cat_cd", "tran_source",
        "tran_desc", "tran_amt", "tran_merchant_id", "tran_merchant_name",
        "tran_merchant_city", "tran_merchant_zip", "tran_card_num",
        "tran_orig_ts", "tran_proc_ts"
    ]
    df_tran_records.select(tran_table_cols) \
        .write.format("delta").mode("append") \
        .saveAsTable("transactions")
    print(f"Wrote {tran_count} interest transactions to transactions")

    # ------------------------------------------------------------------
    # Step 9: Update account balances
    #   (COBOL: 1050-UPDATE-ACCOUNT)
    #   ACCT-CURR-BAL += total_interest ; reset cycle credit/debit to 0
    # ------------------------------------------------------------------
    df_acct_interest = df_tran_records.groupBy(
        F.col("_src_acct_id").alias("acct_id")
    ).agg(
        F.sum("tran_amt").alias("total_interest")
    )

    df_acct_interest.createOrReplaceTempView("acct_interest_updates")

    spark.sql("""
        MERGE INTO accounts AS target
        USING acct_interest_updates AS source
        ON target.acct_id = source.acct_id
        WHEN MATCHED THEN
            UPDATE SET
                acct_curr_bal        = target.acct_curr_bal + source.total_interest,
                acct_curr_cyc_credit = 0,
                acct_curr_cyc_debit  = 0
    """)

    print("Updated account balances: added interest, reset cycle "
          "credits/debits")

    # ------------------------------------------------------------------
    # Display summaries
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("INTEREST CALCULATION SUMMARY")
    print("=" * 70)
    df_acct_interest.orderBy("acct_id").show(truncate=False)

    print("INTEREST DETAIL BY CATEGORY:")
    df_interest.select(
        "trancat_acct_id", "trancat_type_cd", "trancat_cd",
        "tran_cat_bal", "effective_int_rate", "monthly_interest"
    ).orderBy(
        "trancat_acct_id", "trancat_type_cd", "trancat_cd"
    ).show(truncate=False)

    # ------------------------------------------------------------------
    # Final counts
    # ------------------------------------------------------------------
    print("=" * 70)
    print(f"CATEGORY RECORDS READ        : {record_count}")
    print(f"INTEREST TRANSACTIONS WRITTEN: {tran_count}")
    print("=" * 70)
    print("END OF EXECUTION OF PROGRAM CBACT04C (PySpark)")
    print("=" * 70)


# ============================================================================
# Entry point
# ============================================================================
if __name__ == "__main__":
    args = parse_args()
    spark = get_spark(args.schema)
    parm_date = resolve_parm_date(args.parm_date)
    run(spark, parm_date)
    spark.stop()
