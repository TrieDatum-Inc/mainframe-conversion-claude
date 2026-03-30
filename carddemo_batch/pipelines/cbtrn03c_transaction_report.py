#!/usr/bin/env python3
# ============================================================================
# CBTRN03C - Transaction Detail Report
# ============================================================================
# Migrated from: CBTRN03C.CBL (COBOL Batch Program)
# Function:      Generate a transaction detail report filtered by date range.
#                Enriches transactions with account ID (via card XREF),
#                transaction type descriptions, and category descriptions.
#                Produces page totals (every 20 lines), account totals
#                (on card number change), and a grand total.
#
# Output:        CSV report file (replaces COBOL 133-byte fixed-width TRANREPT)
#
# COBOL Processing Flow:
#   1. Read date parameters (start_date, end_date) from DATEPARM file
#   2. Open TRANFILE (sequential), CARDXREF, TRANTYPE, TRANCATG, REPTFILE
#   3. For each transaction record (sequential read):
#      a. Filter by date range: TRAN-PROC-TS(1:10) between start/end dates
#      b. On card number change -> write account totals
#      c. Lookup XREF by card number -> get account ID
#      d. Lookup transaction type description
#      e. Lookup transaction category description
#      f. Write detail line with formatted amount
#      g. Every 20 lines -> write page totals and re-print headers
#   4. At EOF: write final page totals + grand totals
#
# Input:   carddemo.transactions          (TRANFILE DD - sequential)
#          carddemo.card_xref             (CARDXREF DD - random read)
#          carddemo.transaction_types     (TRANTYPE DD - random read)
#          carddemo.transaction_categories (TRANCATG DD - random read)
# Params:  start_date, end_date           (DATEPARM DD)
# Output:  CSV report file
#
# Usage:
#   Databricks notebook : Set widgets start_date/end_date, then run all cells
#   spark-submit        : spark-submit --packages io.delta:delta-spark_2.12:3.1.0 \
#                           cbtrn03c_transaction_report.py \
#                           --schema carddemo --start-date 2025-03-01 \
#                           --end-date 2025-03-31 --output ./output/report
# ============================================================================

import argparse
import sys

from pyspark.sql import SparkSession
import pyspark.sql.functions as F
from pyspark.sql.window import Window
from decimal import Decimal


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
            .appName("CBTRN03C_TransactionReport")
            .config("spark.sql.extensions",
                    "io.delta.sql.DeltaSparkSessionExtension")
            .config("spark.sql.catalog.spark_catalog",
                    "org.apache.spark.sql.delta.catalog.DeltaCatalog")
            .getOrCreate()
        )
    spark.sql(f"USE {schema}")
    return spark


def resolve_dates(cli_start, cli_end):
    """Resolve date range: CLI args > Databricks widgets > defaults."""
    start = cli_start
    end = cli_end
    if is_databricks():
        try:
            if not start:
                start = dbutils.widgets.get("start_date")  # noqa: F821
            if not end:
                end = dbutils.widgets.get("end_date")  # noqa: F821
        except Exception:
            pass
    return start or "2025-03-01", end or "2025-03-31"


def resolve_output(cli_value):
    if cli_value:
        return cli_value
    return "/tmp/carddemo/transaction_report"


def parse_args():
    parser = argparse.ArgumentParser(
        description="CBTRN03C - Transaction Detail Report (CSV)")
    parser.add_argument("--schema", default="carddemo",
                        help="Catalog schema / database name")
    parser.add_argument("--start-date", default=None,
                        help="Report start date YYYY-MM-DD")
    parser.add_argument("--end-date", default=None,
                        help="Report end date YYYY-MM-DD")
    parser.add_argument("--output", default=None,
                        help="Output path for CSV files")
    args, _ = parser.parse_known_args()
    return args


# ============================================================================
# Main pipeline logic
# ============================================================================
def run(spark, start_date, end_date, output_path):
    print("=" * 70)
    print("START OF EXECUTION OF PROGRAM CBTRN03C (PySpark)")
    print(f"Date Range: {start_date} to {end_date}")
    print("=" * 70)

    # ------------------------------------------------------------------
    # Step 1: Read source tables
    # ------------------------------------------------------------------
    df_transactions = spark.table("transactions")
    df_xref = spark.table("card_xref")
    df_tran_types = spark.table("transaction_types")
    df_tran_cats = spark.table("transaction_categories")

    # ------------------------------------------------------------------
    # Step 2: Filter transactions by date range
    #   (COBOL: TRAN-PROC-TS(1:10) >= WS-START-DATE
    #       AND TRAN-PROC-TS(1:10) <= WS-END-DATE)
    # ------------------------------------------------------------------
    df_filtered = df_transactions.filter(
        (F.substring("tran_proc_ts", 1, 10) >= start_date) &
        (F.substring("tran_proc_ts", 1, 10) <= end_date)
    )

    filtered_count = df_filtered.count()
    print(f"Transactions in date range: {filtered_count}")

    # ------------------------------------------------------------------
    # Step 3: Enrich with card cross-reference (get account ID)
    #   (COBOL: 1500-A-LOOKUP-XREF)
    # ------------------------------------------------------------------
    df_with_xref = df_filtered.join(
        df_xref.select("xref_card_num", "xref_acct_id"),
        df_filtered.tran_card_num == df_xref.xref_card_num,
        "left"
    )

    # ------------------------------------------------------------------
    # Step 4: Enrich with transaction type description
    # ------------------------------------------------------------------
    df_with_type = df_with_xref.join(
        df_tran_types,
        df_with_xref.tran_type_cd == df_tran_types.tran_type,
        "left"
    )

    # ------------------------------------------------------------------
    # Step 5: Enrich with transaction category description
    # ------------------------------------------------------------------
    df_enriched = df_with_type.alias("t").join(
        df_tran_cats.alias("c"),
        (F.col("t.tran_type_cd") == F.col("c.tran_type_cd")) &
        (F.col("t.tran_cat_cd") == F.col("c.tran_cat_cd")),
        "left"
    )

    # ------------------------------------------------------------------
    # Step 6: Build report detail records
    #   (COBOL: 1120-WRITE-DETAIL - TRANSACTION-DETAIL-REPORT layout)
    # ------------------------------------------------------------------
    df_report_detail = df_enriched.select(
        F.col("t.tran_id").alias("transaction_id"),
        F.coalesce(F.col("t.xref_acct_id").cast("string"), F.lit("")).alias("account_id"),
        F.col("t.tran_card_num").alias("card_number"),
        F.col("t.tran_type_cd").alias("type_code"),
        F.coalesce(F.col("t.tran_type_desc"), F.lit("")).alias("type_description"),
        F.col("t.tran_cat_cd").alias("category_code"),
        F.coalesce(F.col("c.tran_cat_type_desc"), F.lit("")).alias("category_description"),
        F.col("t.tran_source").alias("source"),
        F.col("t.tran_amt").alias("amount"),
        F.col("t.tran_proc_ts").alias("process_timestamp")
    ).orderBy("card_number", "transaction_id")

    # ------------------------------------------------------------------
    # Step 7: Compute account totals, page totals, and grand total
    #   (COBOL: 1110-WRITE-PAGE-TOTALS, 1120-WRITE-ACCOUNT-TOTALS,
    #           1110-WRITE-GRAND-TOTALS)
    # ------------------------------------------------------------------

    # Account totals (control break on card number change)
    df_account_totals = (
        df_report_detail
        .groupBy("card_number", "account_id")
        .agg(
            F.sum("amount").alias("account_total"),
            F.count("*").alias("transaction_count"))
        .orderBy("card_number")
    )

    # Grand total
    grand_total_row = df_report_detail.agg(
        F.sum("amount").alias("grand_total"),
        F.count("*").alias("total_transactions")
    ).collect()[0]

    grand_total = (grand_total_row["grand_total"]
                   if grand_total_row["grand_total"]
                   else Decimal("0.00"))
    total_transactions = grand_total_row["total_transactions"]

    # Page totals (every 20 rows, matching COBOL WS-PAGE-SIZE = 20)
    w_page = Window.orderBy("card_number", "transaction_id")
    df_with_page = (
        df_report_detail
        .withColumn("row_num", F.row_number().over(w_page))
        .withColumn("page_number", F.ceil(F.col("row_num") / F.lit(20)))
    )

    df_page_totals = (
        df_with_page
        .groupBy("page_number")
        .agg(
            F.sum("amount").alias("page_total"),
            F.count("*").alias("page_rows"))
        .orderBy("page_number")
    )

    # ------------------------------------------------------------------
    # Step 8: Write CSV report output
    #   (COBOL: WRITE FD-REPTFILE-REC)
    # ------------------------------------------------------------------
    df_report_detail.coalesce(1).write.format("csv") \
        .option("header", "true") \
        .mode("overwrite") \
        .save(f"{output_path}/detail")

    df_account_totals.coalesce(1).write.format("csv") \
        .option("header", "true") \
        .mode("overwrite") \
        .save(f"{output_path}/account_totals")

    df_page_totals.coalesce(1).write.format("csv") \
        .option("header", "true") \
        .mode("overwrite") \
        .save(f"{output_path}/page_totals")

    print(f"Report CSV files written to: {output_path}/")

    # ------------------------------------------------------------------
    # Step 9: Display report output
    #   (COBOL: report header from CVTRA07Y - REPORT-NAME-HEADER)
    # ------------------------------------------------------------------
    print("\n" + "=" * 133)
    print(f"{'DALYREPT':<38}{'Daily Transaction Report':<41}"
          f"{'Date Range: '}{start_date} to {end_date}")
    print("=" * 133)

    print(f"{'Transaction ID':<17}{'Account ID':<12}"
          f"{'Transaction Type':<19}{'Tran Category':<35}"
          f"{'Tran Source':<14} {'Amount':>16}")
    print("-" * 133)

    df_report_detail.show(50, truncate=False)

    print("\nAccount Totals:")
    df_account_totals.show(truncate=False)

    print("\nPage Totals:")
    df_page_totals.show(truncate=False)

    print(f"\n{'Grand Total':<11}{'.' * 86} {grand_total:>+15,.2f}")

    print("\n" + "=" * 70)
    print(f"TRANSACTIONS IN RANGE : {total_transactions}")
    print(f"GRAND TOTAL           : {grand_total:+,.2f}")
    print("=" * 70)
    print("END OF EXECUTION OF PROGRAM CBTRN03C (PySpark)")
    print("=" * 70)


# ============================================================================
# Entry point
# ============================================================================
if __name__ == "__main__":
    args = parse_args()
    spark = get_spark(args.schema)
    start_date, end_date = resolve_dates(args.start_date, args.end_date)
    output_path = resolve_output(args.output)
    run(spark, start_date, end_date, output_path)
    spark.stop()
