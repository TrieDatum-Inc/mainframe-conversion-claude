"""
CBACT04C Transformations - Interest Calculator

COBOL Program : CBACT04C.cbl
Function      : Reads transaction-category-balance records sequentially
                (ordered by account).  For each category balance, looks up
                the interest rate from DISCGRP-FILE (falling back to DEFAULT
                group when no specific entry exists), computes monthly
                interest = (balance * rate) / 1200, and writes an interest
                transaction.  When the account changes, it updates the
                account record: adds total interest to current balance and
                zeros cycle credit/debit.

COBOL Paragraph -> PySpark Function Mapping
-------------------------------------------
1000-TCATBALF-GET-NEXT     -> (SparkSession read of transaction_category_balance)
1050-UPDATE-ACCOUNT        -> build_account_interest_updates()
1100-GET-ACCT-DATA         -> (join with accounts)
1110-GET-XREF-DATA         -> (join with card_xref)
1200-GET-INTEREST-RATE     -> resolve_interest_rates()
  1200-A-GET-DEFAULT-INT-RATE -> (fallback handled inside resolve_interest_rates)
1300-COMPUTE-INTEREST      -> compute_monthly_interest()
1300-B-WRITE-TX            -> build_interest_transactions()
1400-COMPUTE-FEES          -> (stub - not implemented in COBOL, not implemented here)
"""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import DecimalType, StringType

from carddemo_batch.config.columns import (
    COL_ACCT_CURR_BAL,
    COL_ACCT_CURR_CYC_CREDIT,
    COL_ACCT_CURR_CYC_DEBIT,
    COL_ACCT_GROUP_ID,
    COL_ACCT_ID,
    COL_DEFAULT_INT_RATE,
    COL_DEF_CAT_CD,
    COL_DEF_TYPE_CD,
    COL_DIS_ACCT_GROUP_ID,
    COL_DIS_INT_RATE,
    COL_DIS_TRAN_CAT_CD,
    COL_DIS_TRAN_TYPE_CD,
    COL_MONTHLY_INTEREST,
    COL_RESET_CYCLE_BALANCES,
    COL_SPECIFIC_INT_RATE,
    COL_TOTAL_INTEREST,
    COL_TRANCAT_ACCT_ID,
    COL_TRANCAT_CD,
    COL_TRANCAT_TYPE_CD,
    COL_TRAN_AMT,
    COL_TRAN_CARD_NUM,
    COL_TRAN_CAT_BAL,
    COL_TRAN_CAT_CD,
    COL_TRAN_DESC,
    COL_TRAN_ID,
    COL_TRAN_MERCHANT_CITY,
    COL_TRAN_MERCHANT_ID,
    COL_TRAN_MERCHANT_NAME,
    COL_TRAN_MERCHANT_ZIP,
    COL_TRAN_ORIG_TS,
    COL_TRAN_PROC_TS,
    COL_TRAN_SOURCE,
    COL_TRAN_TYPE_CD,
    COL_XREF_ACCT_ID,
    COL_XREF_CARD_NUM,
)
from carddemo_batch.config.settings import (
    INTEREST_DEFAULT_GROUP,
    INTEREST_DIVISOR,
    INTEREST_TRAN_CAT_CD,
    INTEREST_TRAN_SOURCE,
    INTEREST_TRAN_TYPE_CD,
)


def _join_tcatbal_to_account_xref(
    tcatbal_df: DataFrame,
    account_df: DataFrame,
    xref_df: DataFrame,
) -> DataFrame:
    """
    COBOL: 1100-GET-ACCT-DATA + 1110-GET-XREF-DATA
    Joins tcatbal to account master and card_xref to obtain acct_group_id
    and xref_card_num needed for rate lookup and transaction writing.
    """
    with_acct = tcatbal_df.join(
        account_df.select(
            F.col(COL_ACCT_ID),
            F.col(COL_ACCT_GROUP_ID),
            F.col(COL_ACCT_CURR_BAL),
            F.col(COL_ACCT_CURR_CYC_CREDIT),
            F.col(COL_ACCT_CURR_CYC_DEBIT),
        ),
        on=tcatbal_df[COL_TRANCAT_ACCT_ID].cast(StringType()) == account_df[COL_ACCT_ID],
        how="inner",
    )
    return with_acct.join(
        xref_df.select(F.col(COL_XREF_ACCT_ID), F.col(COL_XREF_CARD_NUM)),
        on=with_acct[COL_TRANCAT_ACCT_ID] == xref_df[COL_XREF_ACCT_ID],
        how="left",
    )


def _lookup_specific_interest_rate(
    enriched_df: DataFrame, discgrp_df: DataFrame
) -> DataFrame:
    """
    COBOL: 1200-GET-INTEREST-RATE (specific acct_group_id lookup).
    Adds specific_int_rate column; NULL when no matching group entry.
    """
    return enriched_df.join(
        discgrp_df.select(
            F.col(COL_DIS_ACCT_GROUP_ID),
            F.col(COL_DIS_TRAN_TYPE_CD),
            F.col(COL_DIS_TRAN_CAT_CD),
            F.col(COL_DIS_INT_RATE).alias(COL_SPECIFIC_INT_RATE),
        ),
        on=[
            F.trim(enriched_df[COL_ACCT_GROUP_ID]) == F.trim(discgrp_df[COL_DIS_ACCT_GROUP_ID]),
            enriched_df[COL_TRANCAT_TYPE_CD] == discgrp_df[COL_DIS_TRAN_TYPE_CD],
            enriched_df[COL_TRANCAT_CD] == discgrp_df[COL_DIS_TRAN_CAT_CD],
        ],
        how="left",
    )


def _lookup_default_interest_rate(
    specific_df: DataFrame, discgrp_df: DataFrame
) -> DataFrame:
    """
    COBOL: 1200-A-GET-DEFAULT-INT-RATE (fallback when status=23).
    Adds default_int_rate column from the DEFAULT group entry.
    """
    default_discgrp = discgrp_df.filter(
        F.trim(F.col(COL_DIS_ACCT_GROUP_ID)) == F.lit(INTEREST_DEFAULT_GROUP)
    ).select(
        F.col(COL_DIS_TRAN_TYPE_CD).alias(COL_DEF_TYPE_CD),
        F.col(COL_DIS_TRAN_CAT_CD).alias(COL_DEF_CAT_CD),
        F.col(COL_DIS_INT_RATE).alias(COL_DEFAULT_INT_RATE),
    )
    return specific_df.join(
        default_discgrp,
        on=[
            specific_df[COL_TRANCAT_TYPE_CD] == default_discgrp[COL_DEF_TYPE_CD],
            specific_df[COL_TRANCAT_CD] == default_discgrp[COL_DEF_CAT_CD],
        ],
        how="left",
    )


def resolve_interest_rates(
    tcatbal_df: DataFrame,
    account_df: DataFrame,
    xref_df: DataFrame,
    discgrp_df: DataFrame,
) -> DataFrame:
    """
    COBOL: 1100-GET-ACCT-DATA, 1110-GET-XREF-DATA, 1200-GET-INTEREST-RATE,
           1200-A-GET-DEFAULT-INT-RATE

    Enriches tcatbal records with account/xref data and resolves the interest
    rate: uses the specific disclosure group entry, falling back to DEFAULT
    when no specific entry exists (COBOL FILE STATUS 23).

    Returns enriched DataFrame with columns:
      trancat_acct_id, trancat_type_cd, trancat_cd, tran_cat_bal,
      dis_int_rate, xref_card_num, acct_group_id, acct_curr_bal,
      acct_curr_cyc_credit, acct_curr_cyc_debit
    """
    with_refs = _join_tcatbal_to_account_xref(tcatbal_df, account_df, xref_df)
    with_specific = _lookup_specific_interest_rate(with_refs, discgrp_df)
    with_default = _lookup_default_interest_rate(with_specific, discgrp_df)

    resolved = with_default.withColumn(
        COL_DIS_INT_RATE,
        F.when(
            F.col(COL_SPECIFIC_INT_RATE).isNotNull(), F.col(COL_SPECIFIC_INT_RATE)
        ).otherwise(F.col(COL_DEFAULT_INT_RATE)),
    )
    return resolved.select(
        COL_TRANCAT_ACCT_ID,
        COL_TRANCAT_TYPE_CD,
        COL_TRANCAT_CD,
        COL_TRAN_CAT_BAL,
        COL_DIS_INT_RATE,
        COL_XREF_CARD_NUM,
        COL_ACCT_GROUP_ID,
        COL_ACCT_CURR_BAL,
        COL_ACCT_CURR_CYC_CREDIT,
        COL_ACCT_CURR_CYC_DEBIT,
    )


def compute_monthly_interest(enriched_df: DataFrame) -> DataFrame:
    """
    COBOL: 1300-COMPUTE-INTEREST
    COMPUTE WS-MONTHLY-INT = (TRAN-CAT-BAL * DIS-INT-RATE) / 1200

    Only processes rows where dis_int_rate != 0 (COBOL: IF DIS-INT-RATE NOT = 0).

    Returns DataFrame with monthly_interest column added, filtered to non-zero rates.
    """
    non_zero = enriched_df.filter(
        F.col(COL_DIS_INT_RATE).isNotNull() & (F.col(COL_DIS_INT_RATE) != 0)
    )

    return non_zero.withColumn(
        COL_MONTHLY_INTEREST,
        (F.col(COL_TRAN_CAT_BAL) * F.col(COL_DIS_INT_RATE) / F.lit(INTEREST_DIVISOR)).cast(
            DecimalType(11, 2)
        ),
    )


def _add_interest_tran_id(interest_df: DataFrame, parm_date: str) -> DataFrame:
    """
    COBOL: STRING PARM-DATE WS-TRANID-SUFFIX INTO TRAN-ID
    Assigns a unique transaction ID per row using parm_date + zero-padded sequence.
    """
    with_seq = interest_df.withColumn(
        "_row_num", F.monotonically_increasing_id() + 1
    )
    return with_seq.withColumn(
        COL_TRAN_ID,
        F.concat(
            F.lit(parm_date),
            F.lpad(F.col("_row_num").cast(StringType()), 6, "0"),
        ),
    )


def _add_interest_tran_fields(df: DataFrame, proc_ts: str) -> DataFrame:
    """
    COBOL: 1300-B-WRITE-TX field assignments (type, cat, source, desc, merchant, timestamps).
    """
    return (
        df.withColumn(COL_TRAN_TYPE_CD, F.lit(INTEREST_TRAN_TYPE_CD))
        .withColumn(COL_TRAN_CAT_CD, F.lit(INTEREST_TRAN_CAT_CD))
        .withColumn(COL_TRAN_SOURCE, F.lit(INTEREST_TRAN_SOURCE))
        .withColumn(
            COL_TRAN_DESC,
            F.concat(F.lit("Int. for a/c "), F.col(COL_TRANCAT_ACCT_ID).cast(StringType())),
        )
        .withColumn(COL_TRAN_AMT, F.col(COL_MONTHLY_INTEREST).cast(DecimalType(11, 2)))
        .withColumn(COL_TRAN_MERCHANT_ID, F.lit(0).cast("long"))
        .withColumn(COL_TRAN_MERCHANT_NAME, F.lit(""))
        .withColumn(COL_TRAN_MERCHANT_CITY, F.lit(""))
        .withColumn(COL_TRAN_MERCHANT_ZIP, F.lit(""))
        .withColumn(COL_TRAN_CARD_NUM, F.col(COL_XREF_CARD_NUM))
        .withColumn(COL_TRAN_ORIG_TS, F.lit(proc_ts))
        .withColumn(COL_TRAN_PROC_TS, F.lit(proc_ts))
    )


def build_interest_transactions(
    interest_df: DataFrame,
    parm_date: str,
    proc_ts: str,
) -> DataFrame:
    """
    COBOL: 1300-B-WRITE-TX
    Builds synthetic interest charge transaction records.

    TRAN-ID = PARM-DATE || WS-TRANID-SUFFIX (incrementing counter)
    All field assignments mirror the COBOL paragraph exactly.
    """
    with_id = _add_interest_tran_id(interest_df, parm_date)
    with_fields = _add_interest_tran_fields(with_id, proc_ts)
    return with_fields.select(
        COL_TRAN_ID, COL_TRAN_TYPE_CD, COL_TRAN_CAT_CD, COL_TRAN_SOURCE,
        COL_TRAN_DESC, COL_TRAN_AMT, COL_TRAN_MERCHANT_ID, COL_TRAN_MERCHANT_NAME,
        COL_TRAN_MERCHANT_CITY, COL_TRAN_MERCHANT_ZIP, COL_TRAN_CARD_NUM,
        COL_TRAN_ORIG_TS, COL_TRAN_PROC_TS,
    )


def build_account_interest_updates(interest_df: DataFrame) -> DataFrame:
    """
    COBOL: 1050-UPDATE-ACCOUNT
    Aggregates total interest per account (WS-TOTAL-INT) and produces the
    account update deltas:
      - curr_bal += total_interest
      - acct_curr_cyc_credit = 0
      - acct_curr_cyc_debit  = 0

    COBOL resets cycle credit/debit to 0 unconditionally as part of
    end-of-cycle processing. We represent this as explicit zero values
    so the caller can apply them via a MERGE.

    Returns (trancat_acct_id, total_interest, set_cyc_credit_zero, set_cyc_debit_zero).
    """
    return interest_df.groupBy(COL_TRANCAT_ACCT_ID).agg(
        F.sum(COL_MONTHLY_INTEREST).cast(DecimalType(11, 2)).alias(COL_TOTAL_INTEREST),
        F.lit(True).alias(COL_RESET_CYCLE_BALANCES),
    )
