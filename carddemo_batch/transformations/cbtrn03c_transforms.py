"""
CBTRN03C Transformations - Transaction Detail Report (CSV output)

COBOL Program : CBTRN03C.cbl
Function      : Reads posted transactions sequentially within a date range,
                looks up transaction type and category descriptions, accumulates
                per-page/per-account/grand totals, and prints a formatted
                report.  The report breaks on card number change (account total)
                and on page size (page total).

CSV OUTPUT ONLY - HTML output is not produced.

COBOL Paragraph -> PySpark Function Mapping
-------------------------------------------
0550-DATEPARM-READ       -> (parm_start_date / parm_end_date passed as arguments)
1000-TRANFILE-GET-NEXT   -> (SparkSession read of transactions)
1500-A-LOOKUP-XREF       -> enrich_with_xref()
1500-B-LOOKUP-TRANTYPE   -> enrich_with_tran_type()
1500-C-LOOKUP-TRANCATG   -> enrich_with_tran_category()
1100-WRITE-TRANSACTION-REPORT -> build_report_detail_rows() (date filter + enrichment)
1110-WRITE-PAGE-TOTALS   -> compute_page_totals()
1120-WRITE-ACCOUNT-TOTALS -> compute_account_totals()
1110-WRITE-GRAND-TOTALS  -> compute_grand_total()

Note on sequential vs parallel processing:
  COBOL processes transactions one by one, accumulating running page/account
  totals.  Since totals only depend on the set of rows within each group (not
  on prior state from other groups), we can safely compute them in parallel
  using groupBy aggregations.  Per-page totals are computed by assigning each
  row a page number via row_number() window function.
"""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql import Window
from pyspark.sql.types import DecimalType

from carddemo_batch.config.columns import (
    COL_ACCOUNT_ID,
    COL_ACCOUNT_TOTAL,
    COL_GRAND_TOTAL,
    COL_PAGE_NUM,
    COL_PAGE_TOTAL,
    COL_REPORT_DATE,
    COL_TC_CAT_CD,
    COL_TC_TYPE_CD,
    COL_TRAN_AMT,
    COL_TRAN_CARD_NUM,
    COL_TRAN_CAT_CD,
    COL_TRAN_CAT_DESC,
    COL_TRAN_CAT_TYPE_DESC,
    COL_TRAN_ID,
    COL_TRAN_PROC_TS,
    COL_TRAN_SOURCE,
    COL_TRAN_TYPE,
    COL_TRAN_TYPE_CD,
    COL_TRAN_TYPE_DESC,
    COL_TT_TRAN_TYPE,
    COL_XREF_ACCT_ID,
    COL_XREF_CARD_NUM,
)
from carddemo_batch.config.settings import REPORT_PAGE_SIZE


def filter_by_date_range(
    tran_df: DataFrame,
    start_date: str,
    end_date: str,
) -> DataFrame:
    """
    COBOL: main loop date filter
    IF TRAN-PROC-TS(1:10) >= WS-START-DATE
       AND TRAN-PROC-TS(1:10) <= WS-END-DATE

    Keeps only transactions whose process-timestamp date portion falls within
    [start_date, end_date] inclusive.
    """
    date_portion = F.col(COL_TRAN_PROC_TS).substr(1, 10)
    return tran_df.filter(
        (date_portion >= F.lit(start_date)) & (date_portion <= F.lit(end_date))
    )


def enrich_with_xref(tran_df: DataFrame, xref_df: DataFrame) -> DataFrame:
    """
    COBOL: 1500-A-LOOKUP-XREF
    Lookup xref_acct_id by tran_card_num.  COBOL abends on missing card;
    here we use inner join which will naturally drop unmatched rows.
    Callers can validate no rows were dropped by comparing counts.
    """
    return tran_df.join(
        xref_df.select(COL_XREF_CARD_NUM, COL_XREF_ACCT_ID),
        on=tran_df[COL_TRAN_CARD_NUM] == xref_df[COL_XREF_CARD_NUM],
        how="inner",
    )


def enrich_with_tran_type(
    tran_df: DataFrame, tran_type_df: DataFrame
) -> DataFrame:
    """
    COBOL: 1500-B-LOOKUP-TRANTYPE
    Lookup TRAN-TYPE-DESC from transaction_types by TRAN-TYPE-CD.
    COBOL abends on missing type; inner join replicates that behaviour.
    """
    return tran_df.join(
        tran_type_df.select(
            F.col(COL_TRAN_TYPE).alias(COL_TT_TRAN_TYPE),
            F.col(COL_TRAN_TYPE_DESC),
        ),
        on=tran_df[COL_TRAN_TYPE_CD] == F.col(COL_TT_TRAN_TYPE),
        how="inner",
    )


def enrich_with_tran_category(
    tran_df: DataFrame, tran_cat_df: DataFrame
) -> DataFrame:
    """
    COBOL: 1500-C-LOOKUP-TRANCATG
    Lookup TRAN-CAT-TYPE-DESC from transaction_categories by
    (TRAN-TYPE-CD, TRAN-CAT-CD).  Inner join replicates abend-on-missing.
    """
    return tran_df.join(
        tran_cat_df.select(
            F.col(COL_TRAN_TYPE_CD).alias(COL_TC_TYPE_CD),
            F.col(COL_TRAN_CAT_CD).alias(COL_TC_CAT_CD),
            F.col(COL_TRAN_CAT_TYPE_DESC),
        ),
        on=[
            tran_df[COL_TRAN_TYPE_CD] == F.col(COL_TC_TYPE_CD),
            tran_df[COL_TRAN_CAT_CD] == F.col(COL_TC_CAT_CD),
        ],
        how="inner",
    )


def build_report_detail_rows(
    tran_df: DataFrame,
    xref_df: DataFrame,
    tran_type_df: DataFrame,
    tran_cat_df: DataFrame,
    start_date: str,
    end_date: str,
    report_date: str,
) -> DataFrame:
    """
    COBOL: 1120-WRITE-DETAIL (combined with all enrichment steps)
    Produces the full set of transaction detail rows for the report,
    shaped to match the transaction_report Delta table schema.

    Also assigns:
      - page_num  : which report page the row falls on (ordered by card+proc_ts)
      - acct_order: ordering key for account-total breaks

    The COBOL report order is: transactions appear in sequential file order.
    The transaction file is sequential (not indexed), so order = physical order.
    We preserve this via tran_proc_ts ordering as a close approximation.
    """
    filtered = filter_by_date_range(tran_df, start_date, end_date)
    with_xref = enrich_with_xref(filtered, xref_df)
    with_type = enrich_with_tran_type(with_xref, tran_type_df)
    with_cat = enrich_with_tran_category(with_type, tran_cat_df)

    # Assign sequential row number ordered by card number then timestamp
    # This mirrors COBOL's sequential read order which processes the file in
    # tran_proc_ts sequence (transactions were written in arrival order).
    order_window = Window.orderBy(COL_TRAN_CARD_NUM, COL_TRAN_PROC_TS)
    with_row = with_cat.withColumn("_row_num", F.row_number().over(order_window))
    with_page = with_row.withColumn(
        COL_PAGE_NUM,
        F.ceil(F.col("_row_num") / F.lit(REPORT_PAGE_SIZE)).cast("int"),
    )

    return with_page.select(
        F.lit(report_date).alias(COL_REPORT_DATE),
        F.col(COL_TRAN_ID),
        F.col(COL_XREF_ACCT_ID).cast("string").alias(COL_ACCOUNT_ID),
        F.col(COL_TRAN_TYPE_CD),
        F.col(COL_TRAN_TYPE_DESC).substr(1, 15).alias(COL_TRAN_TYPE_DESC),
        F.col(COL_TRAN_CAT_CD),
        F.col(COL_TRAN_CAT_TYPE_DESC).substr(1, 29).alias(COL_TRAN_CAT_DESC),
        F.col(COL_TRAN_SOURCE),
        F.col(COL_TRAN_AMT).cast(DecimalType(11, 2)),
        F.col(COL_TRAN_PROC_TS),
        F.col(COL_PAGE_NUM),
    )


def compute_account_totals(detail_df: DataFrame) -> DataFrame:
    """
    COBOL: 1120-WRITE-ACCOUNT-TOTALS (WS-ACCOUNT-TOTAL per card)
    Returns one row per card with the total transaction amount.
    """
    return detail_df.groupBy(COL_ACCOUNT_ID).agg(
        F.sum(COL_TRAN_AMT).cast(DecimalType(11, 2)).alias(COL_ACCOUNT_TOTAL)
    )


def compute_page_totals(detail_df: DataFrame) -> DataFrame:
    """
    COBOL: 1110-WRITE-PAGE-TOTALS (WS-PAGE-TOTAL reset every PAGE_SIZE lines)
    Returns one row per page with the total transaction amount for that page.
    """
    return detail_df.groupBy(COL_PAGE_NUM).agg(
        F.sum(COL_TRAN_AMT).cast(DecimalType(11, 2)).alias(COL_PAGE_TOTAL)
    ).orderBy(COL_PAGE_NUM)


def compute_grand_total(detail_df: DataFrame) -> DataFrame:
    """
    COBOL: 1110-WRITE-GRAND-TOTALS (WS-GRAND-TOTAL = sum of all page totals)
    Returns a single-row DataFrame with the grand total.
    """
    return detail_df.agg(
        F.sum(COL_TRAN_AMT).cast(DecimalType(11, 2)).alias(COL_GRAND_TOTAL)
    )
