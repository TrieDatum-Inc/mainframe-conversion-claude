"""
CBSTM03A/CBSTM03B Transformations - Account Statement Generation (CSV only)

COBOL Programs : CBSTM03A.CBL (main) + CBSTM03B.CBL (file I/O subroutine)
Function       : Produce per-card account statements from transaction data.
                 CBSTM03A drives the logic; CBSTM03B is an I/O dispatcher
                 subroutine that opens/reads four VSAM files.

Key COBOL structures:
  WS-TRNX-TABLE  OCCURS 51 TIMES -> holds up to 51 cards
    WS-TRAN-TBL  OCCURS 10 TIMES -> up to 10 transactions per card
  CR-CNT / TR-CNT / CR-JMP / TR-JMP -> loop counters

COBOL Paragraph -> PySpark Function Mapping
-------------------------------------------
1000-XREFFILE-GET-NEXT   -> (SparkSession read of card_xref, sequential)
2000-CUSTFILE-GET        -> (join with customers by xref_cust_id)
3000-ACCTFILE-GET        -> (join with accounts by xref_acct_id)
4000-TRNXFILE-GET        -> match_transactions_to_cards()
5000-CREATE-STATEMENT    -> build_statement_header()
6000-WRITE-TRANS         -> build_statement_detail_rows()

CBSTM03B paragraphs are fully absorbed into the joins above; the subroutine
only handled file open/read/close dispatch.
"""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import DecimalType

from carddemo_batch.config.columns import (
    COL_ACCT_CURR_BAL,
    COL_ACCT_ID,
    COL_CUST_ADDR_COUNTRY_CD,
    COL_CUST_ADDR_FULL,
    COL_CUST_ADDR_LINE_1,
    COL_CUST_ADDR_LINE_2,
    COL_CUST_ADDR_LINE_3,
    COL_CUST_ADDR_STATE_CD,
    COL_CUST_ADDR_ZIP,
    COL_CUST_FICO_CREDIT_SCORE,
    COL_CUST_FIRST_NAME,
    COL_CUST_FULL_NAME,
    COL_CUST_ID,
    COL_CUST_LAST_NAME,
    COL_CUST_MIDDLE_NAME,
    COL_FICO_SCORE,
    COL_TOTAL_EXP,
    COL_TRNX_AMT,
    COL_TRNX_CARD_NUM,
    COL_TRNX_DESC,
    COL_TRNX_ID,
    COL_XREF_ACCT_ID,
    COL_XREF_CARD_NUM,
    COL_XREF_CUST_ID,
)


def enrich_xref_with_customer_account(
    xref_df: DataFrame,
    customer_df: DataFrame,
    account_df: DataFrame,
) -> DataFrame:
    """
    COBOL: 2000-CUSTFILE-GET, 3000-ACCTFILE-GET
    Join card_xref with customer and account master to get all fields
    needed for statement header generation.

    CBSTM03B performs random reads by customer_id and account_id;
    we replicate this with inner joins.
    """
    with_cust = xref_df.join(
        customer_df,
        on=xref_df[COL_XREF_CUST_ID] == customer_df[COL_CUST_ID],
        how="inner",
    )

    with_acct = with_cust.join(
        account_df,
        on=with_cust[COL_XREF_ACCT_ID].cast("string") == account_df[COL_ACCT_ID],
        how="inner",
    )

    return with_acct.select(
        xref_df[COL_XREF_CARD_NUM],
        xref_df[COL_XREF_CUST_ID],
        xref_df[COL_XREF_ACCT_ID],
        customer_df[COL_CUST_FIRST_NAME],
        customer_df[COL_CUST_MIDDLE_NAME],
        customer_df[COL_CUST_LAST_NAME],
        customer_df[COL_CUST_ADDR_LINE_1],
        customer_df[COL_CUST_ADDR_LINE_2],
        customer_df[COL_CUST_ADDR_LINE_3],
        customer_df[COL_CUST_ADDR_STATE_CD],
        customer_df[COL_CUST_ADDR_COUNTRY_CD],
        customer_df[COL_CUST_ADDR_ZIP],
        customer_df[COL_CUST_FICO_CREDIT_SCORE],
        account_df[COL_ACCT_ID],
        account_df[COL_ACCT_CURR_BAL],
    )


def build_customer_full_name(enriched_df: DataFrame) -> DataFrame:
    """
    COBOL: 5000-CREATE-STATEMENT (STRING with DELIMITED BY ' ' trimming)
    Build the full customer name by trimming each component and joining
    with a single space - matches COBOL STRING ... DELIMITED BY ' ' semantics.

    COBOL: STRING CUST-FIRST-NAME DELIMITED BY ' '
                  ' ' DELIMITED BY SIZE
                  CUST-MIDDLE-NAME DELIMITED BY ' '
                  ' ' DELIMITED BY SIZE
                  CUST-LAST-NAME DELIMITED BY ' '
    This takes the first 'word' (up to first space) from each name field.
    We replicate by trimming trailing spaces, which is functionally equivalent
    for non-embedded-space names.
    """
    return enriched_df.withColumn(
        COL_CUST_FULL_NAME,
        F.trim(
            F.concat_ws(
                " ",
                F.rtrim(F.col(COL_CUST_FIRST_NAME)),
                F.rtrim(F.col(COL_CUST_MIDDLE_NAME)),
                F.rtrim(F.col(COL_CUST_LAST_NAME)),
            )
        ),
    ).withColumn(
        COL_CUST_ADDR_FULL,
        F.trim(
            F.concat_ws(
                " ",
                F.rtrim(F.col(COL_CUST_ADDR_LINE_3)),
                F.rtrim(F.col(COL_CUST_ADDR_STATE_CD)),
                F.rtrim(F.col(COL_CUST_ADDR_COUNTRY_CD)),
                F.rtrim(F.col(COL_CUST_ADDR_ZIP)),
            )
        ),
    )


def match_transactions_to_cards(
    enriched_df: DataFrame,
    trnx_df: DataFrame,
) -> DataFrame:
    """
    COBOL: 4000-TRNXFILE-GET
    Match transactions from the TRNX-FILE (keyed by card+tran_id) against
    the card_xref-driven loop.

    COBOL uses a 2-dimensional in-memory table (WS-TRNX-TABLE: 51 cards x 10
    transactions) loaded from the TRNX-FILE.  The outer loop iterates cards in
    order and the inner loop iterates transactions per card.

    In Spark we simply join on card number - the result is equivalent since
    all data is in Delta tables.  We also compute the running total per card
    (WS-TOTAL-AMT accumulator).
    """
    joined = enriched_df.join(
        trnx_df,
        on=enriched_df[COL_XREF_CARD_NUM] == trnx_df[COL_TRNX_CARD_NUM],
        how="left",
    )

    total_by_card = (
        trnx_df.groupBy(COL_TRNX_CARD_NUM)
        .agg(
            F.sum(COL_TRNX_AMT).cast(DecimalType(11, 2)).alias(COL_TOTAL_EXP)
        )
    )

    with_total = joined.join(
        total_by_card,
        on=joined[COL_XREF_CARD_NUM] == total_by_card[COL_TRNX_CARD_NUM],
        how="left",
    )

    return with_total.withColumn(
        COL_TOTAL_EXP,
        F.coalesce(F.col(COL_TOTAL_EXP), F.lit(0).cast(DecimalType(11, 2))),
    )


def build_statement_rows(
    enriched_df: DataFrame,
    trnx_df: DataFrame,
) -> DataFrame:
    """
    COBOL: 5000-CREATE-STATEMENT + 6000-WRITE-TRANS
    Produce one output row per transaction, carrying the account/customer
    header fields alongside each transaction detail.

    Output shape matches carddemo.account_statements schema.
    """
    named = build_customer_full_name(enriched_df)
    with_trnx = match_transactions_to_cards(named, trnx_df)

    return with_trnx.select(
        F.col(COL_ACCT_ID).alias(COL_ACCT_ID),
        F.col(COL_CUST_FULL_NAME),
        F.col(COL_CUST_ADDR_LINE_1),
        F.col(COL_CUST_ADDR_LINE_2),
        F.col(COL_CUST_ADDR_FULL),
        F.col(COL_ACCT_CURR_BAL).cast(DecimalType(12, 2)).alias(COL_ACCT_CURR_BAL),
        F.col(COL_CUST_FICO_CREDIT_SCORE).alias(COL_FICO_SCORE),
        F.col(COL_TRNX_CARD_NUM),
        F.col(COL_TRNX_ID),
        F.col(COL_TRNX_DESC),
        F.col(COL_TRNX_AMT).cast(DecimalType(11, 2)),
        F.col(COL_TOTAL_EXP).cast(DecimalType(11, 2)),
    )
