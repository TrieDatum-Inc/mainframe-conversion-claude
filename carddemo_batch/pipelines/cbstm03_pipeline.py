"""
CBSTM03A + CBSTM03B Pipeline - Account Statement Generation (CSV only)

COBOL Programs : CBSTM03A.CBL (main orchestrator) + CBSTM03B.CBL (I/O sub)
Type           : Batch - iterates card_xref sequentially, for each card
                 fetches customer and account data, then prints all
                 matching transactions.  Output: CSV statement rows.

NOTE: HTML output is deliberately not produced. Only CSV Delta table output.

COBOL Design Patterns Translated
---------------------------------
1. ALTER / GO TO state machine (0000-START EVALUATE WS-FL-DD):
   CBSTM03A uses ALTER statements and a state machine via GO TO to drive
   sequential file opens in a specific order:
     TRNXFILE -> XREFFILE -> CUSTFILE -> ACCTFILE -> READTRNX -> mainline
   In PySpark we simply read all tables upfront and join them.

2. CBSTM03B subroutine:
   CBSTM03B is a VSAM file dispatcher called by CBSTM03A via CALL.
   Its four operations (OPEN/READ-sequential/READ-keyed/CLOSE) are fully
   absorbed into Spark reads and joins.

3. WS-TRNX-TABLE 2D array (51 cards x 10 transactions):
   COBOL loads the TRNX-FILE into an in-memory 2D table, then uses nested
   PERFORM loops to match against xref records.  In Spark this becomes a
   standard join on card number.

4. Control Block addressing (PSA/TCB/TIOT):
   CBSTM03A reads z/OS control blocks to display JCL job/step names.
   This has no equivalent in Databricks and is intentionally omitted.

Execution:
    spark-submit pipelines/cbstm03_pipeline.py

    Or in a Databricks notebook:
        from carddemo_batch.pipelines.cbstm03_pipeline import run
        run(spark)
"""

from __future__ import annotations

import logging

from pyspark.sql import SparkSession

from carddemo_batch.config.settings import (
    TBL_ACCOUNT_STATEMENTS,
    TBL_ACCOUNTS,
    TBL_CARD_XREF,
    TBL_CUSTOMERS,
    TBL_TRANSACTIONS_BY_CARD,
)
from carddemo_batch.transformations.cbstm03_transforms import (
    build_statement_rows,
    enrich_xref_with_customer_account,
)
from carddemo_batch.validators.common import (
    assert_table_not_empty,
    log_processing_summary,
)

logger = logging.getLogger(__name__)
PROGRAM_NAME = "CBSTM03A"


def run(spark: SparkSession) -> int:
    """
    Main pipeline entry point.
    Returns the number of statement rows written.

    COBOL: PROCEDURE DIVISION main flow:
      1. Open TRNXFILE via CBSTM03B (ALTER GO TO chain)
      2. Read first TRNX record -> set WS-SAVE-CARD, CR-CNT=1, READTRNX state
      3. 1000-MAINLINE: for each xref record:
           - get customer data (2000-CUSTFILE-GET)
           - get account data  (3000-ACCTFILE-GET)
           - create statement header (5000-CREATE-STATEMENT)
           - match transactions for this card (4000-TRNXFILE-GET)
           - write transaction lines (6000-WRITE-TRANS)
           - write total line
    """
    logger.info("START OF EXECUTION OF PROGRAM %s", PROGRAM_NAME)

    # ------------------------------------------------------------------ #
    # Open files (CBSTM03B operations: O for each DD)
    # ------------------------------------------------------------------ #
    xref_df = spark.read.table(TBL_CARD_XREF)
    customer_df = spark.read.table(TBL_CUSTOMERS)
    account_df = spark.read.table(TBL_ACCOUNTS)
    trnx_df = spark.read.table(TBL_TRANSACTIONS_BY_CARD)

    assert_table_not_empty(xref_df, TBL_CARD_XREF, PROGRAM_NAME)

    xref_count = xref_df.count()
    logger.info("[%s] Cards in xref: %d", PROGRAM_NAME, xref_count)

    # ------------------------------------------------------------------ #
    # Build enriched card/customer/account dataset
    # COBOL: 1000-XREFFILE-GET-NEXT + 2000-CUSTFILE-GET + 3000-ACCTFILE-GET
    # ------------------------------------------------------------------ #
    enriched_df = enrich_xref_with_customer_account(xref_df, customer_df, account_df)

    # ------------------------------------------------------------------ #
    # Build statement rows
    # COBOL: 5000-CREATE-STATEMENT + 4000-TRNXFILE-GET + 6000-WRITE-TRANS
    # ------------------------------------------------------------------ #
    statement_df = build_statement_rows(enriched_df, trnx_df)
    statement_df.write.format("delta").mode("overwrite").saveAsTable(
        TBL_ACCOUNT_STATEMENTS
    )

    rows_written = statement_df.count()

    log_processing_summary(
        PROGRAM_NAME,
        records_read=xref_count,
        records_written=rows_written,
    )
    logger.info("END OF EXECUTION OF PROGRAM %s", PROGRAM_NAME)

    return rows_written


if __name__ == "__main__":
    from pyspark.sql import SparkSession as _SparkSession

    _spark = _SparkSession.builder.appName(PROGRAM_NAME).getOrCreate()
    run(_spark)
