#!/usr/bin/env python3
# ============================================================================
# CBSTM03A + CBSTM03B - Account Statement Generation
# ============================================================================
# Migrated from: CBSTM03A.CBL (main) + CBSTM03B.CBL (file I/O subroutine)
# Function:      Generate account statements from transaction data.
#                For each card in the cross-reference file, look up the
#                customer and account details, then list all transactions
#                for that card with a total.
#
# Output:        CSV file (plain text statement - replaces COBOL STMT-FILE)
#                HTML output is NOT generated per requirements.
#
# COBOL Processing Flow (CBSTM03A):
#   1. Open all files via CBSTM03B subroutine calls
#   2. Read ALL transactions into a 2D in-memory table (51 cards x 10 trans)
#      grouped by card number
#   3. Sequentially read XREF file (card cross-reference)
#   4. For each XREF record:
#      a. Look up customer by XREF-CUST-ID
#      b. Look up account by XREF-ACCT-ID
#      c. Write statement header (name, address, account details)
#      d. Match transactions from the in-memory table for this card
#      e. Write each transaction line
#      f. Write total line
#   5. Close all files
#
# Input:   carddemo.transactions (TRNXFILE)
#          carddemo.card_xref    (XREFFILE)
#          carddemo.customers    (CUSTFILE)
#          carddemo.accounts     (ACCTFILE)
# Output:  CSV statement file written to output path
#
# Usage:
#   Databricks notebook : Run all cells (output to /tmp/carddemo/statements)
#   spark-submit        : spark-submit --packages io.delta:delta-spark_2.12:3.1.0 \
#                           cbstm03_account_statements.py \
#                           --schema carddemo --output ./output/statements
# ============================================================================

import argparse
import sys

from pyspark.sql import SparkSession
import pyspark.sql.functions as F
from pyspark.sql.window import Window


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
            .appName("CBSTM03_AccountStatements")
            .config("spark.sql.extensions",
                    "io.delta.sql.DeltaSparkSessionExtension")
            .config("spark.sql.catalog.spark_catalog",
                    "org.apache.spark.sql.delta.catalog.DeltaCatalog")
            .getOrCreate()
        )
    spark.sql(f"USE {schema}")
    return spark


def resolve_output(cli_value):
    """Resolve output path: CLI arg > Databricks default."""
    if cli_value:
        return cli_value
    return "/tmp/carddemo/statements"


def parse_args():
    parser = argparse.ArgumentParser(
        description="CBSTM03 - Account Statement Generation (CSV)")
    parser.add_argument("--schema", default="carddemo",
                        help="Catalog schema / database name")
    parser.add_argument("--output", default=None,
                        help="Output path for CSV files "
                             "(default: /tmp/carddemo/statements)")
    args, _ = parser.parse_known_args()
    return args


# ============================================================================
# Main pipeline logic
# ============================================================================
def run(spark, output_path):
    print("=" * 70)
    print("START OF EXECUTION OF PROGRAM CBSTM03A/B (PySpark)")
    print("=" * 70)

    # ------------------------------------------------------------------
    # Step 1: Read all source tables
    #   (COBOL CBSTM03B: opens TRNXFILE, XREFFILE, CUSTFILE, ACCTFILE)
    # ------------------------------------------------------------------
    df_transactions = spark.table("transactions")
    df_xref = spark.table("card_xref")
    df_customers = spark.table("customers")
    df_accounts = spark.table("accounts")

    # ------------------------------------------------------------------
    # Step 2: Join XREF with Customer and Account data
    #   (COBOL: 2000-CUSTFILE-GET and 3000-ACCTFILE-GET)
    # ------------------------------------------------------------------
    df_xref_enriched = (
        df_xref
        .join(df_customers,
              df_xref.xref_cust_id == df_customers.cust_id,
              "inner")
        .join(df_accounts,
              df_xref.xref_acct_id == df_accounts.acct_id,
              "inner")
    )

    # ------------------------------------------------------------------
    # Step 3: Match transactions to cards
    #   (COBOL: 4000-TRNXFILE-GET - searches in-memory table by card)
    # ------------------------------------------------------------------
    df_stmt_data = df_xref_enriched.join(
        df_transactions,
        df_xref_enriched.xref_card_num == df_transactions.tran_card_num,
        "left"
    )

    # ------------------------------------------------------------------
    # Step 4: Build the statement CSV output
    #   (COBOL: 5000-CREATE-STATEMENT + 6000-WRITE-TRANS)
    # ------------------------------------------------------------------

    # Customer full name
    df_stmt = df_stmt_data.withColumn(
        "customer_name",
        F.trim(F.concat_ws(" ",
                           F.trim(F.col("cust_first_name")),
                           F.trim(F.col("cust_middle_name")),
                           F.trim(F.col("cust_last_name"))))
    ).withColumn(
        "address_line_3",
        F.trim(F.concat_ws(" ",
                           F.trim(F.col("cust_addr_line_3")),
                           F.trim(F.col("cust_addr_state_cd")),
                           F.trim(F.col("cust_addr_country_cd")),
                           F.trim(F.col("cust_addr_zip"))))
    )

    # Per-card total
    w_card_total = Window.partitionBy("xref_card_num")
    df_stmt = df_stmt.withColumn(
        "card_total_amt",
        F.sum("tran_amt").over(w_card_total)
    )

    # Final column selection
    df_output = df_stmt.select(
        F.col("xref_card_num").alias("card_number"),
        F.col("acct_id").alias("account_id"),
        F.col("customer_name"),
        F.trim(F.col("cust_addr_line_1")).alias("address_line_1"),
        F.trim(F.col("cust_addr_line_2")).alias("address_line_2"),
        F.col("address_line_3"),
        F.col("acct_curr_bal").alias("current_balance"),
        F.col("cust_fico_credit_score").alias("fico_score"),
        F.col("tran_id").alias("transaction_id"),
        F.col("tran_desc").alias("transaction_description"),
        F.col("tran_amt").alias("transaction_amount"),
        F.col("card_total_amt").alias("total_expenditure")
    ).orderBy("xref_card_num", "tran_id")

    # ------------------------------------------------------------------
    # Step 5: Write CSV output
    #   (COBOL: WRITE FD-STMTFILE-REC)
    # ------------------------------------------------------------------
    row_count = df_output.count()
    print(f"Statement rows generated: {row_count}")

    df_output.coalesce(1).write.format("csv") \
        .option("header", "true") \
        .mode("overwrite") \
        .save(output_path)

    print(f"Statement CSV written to: {output_path}")

    # ------------------------------------------------------------------
    # Step 6: Display sample output
    # ------------------------------------------------------------------
    print("\nSample Statement Data:")
    df_output.show(20, truncate=False)

    # Summary statistics per card
    df_summary = df_output.groupBy(
        "card_number", "account_id", "customer_name"
    ).agg(
        F.count("transaction_id").alias("transaction_count"),
        F.first("total_expenditure").alias("total_expenditure")
    )

    print("\nStatement Summary by Card:")
    df_summary.orderBy("card_number").show(truncate=False)

    print("=" * 70)
    print("END OF EXECUTION OF PROGRAM CBSTM03A/B (PySpark)")
    print("=" * 70)


# ============================================================================
# Entry point
# ============================================================================
if __name__ == "__main__":
    args = parse_args()
    spark = get_spark(args.schema)
    output_path = resolve_output(args.output)
    run(spark, output_path)
    spark.stop()
