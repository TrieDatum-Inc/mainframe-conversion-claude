"""
CBTRN02C Transformations - Daily Transaction Posting

COBOL Program : CBTRN02C.cbl
Function      : Post records from the daily transaction file into the
                transaction master, update account balances, and maintain
                the transaction-category-balance index.

COBOL Paragraph -> PySpark Function Mapping
-------------------------------------------
1500-VALIDATE-TRAN           -> validate_transactions()
  1500-A-LOOKUP-XREF         -> _flag_invalid_cards()
  1500-B-LOOKUP-ACCT         -> _flag_account_errors() (window-based sequential check)
2000-POST-TRANSACTION        -> build_posted_transactions()
2700-UPDATE-TCATBAL          -> build_tcatbal_updates()
  2700-A-CREATE-TCATBAL-REC  -> (handled inside build_tcatbal_updates via MERGE logic)
  2700-B-UPDATE-TCATBAL-REC  -> (handled inside build_tcatbal_updates via MERGE logic)
2800-UPDATE-ACCOUNT-REC      -> build_account_balance_updates()
2500-WRITE-REJECT-REC        -> extract_rejected_transactions()
"""

from __future__ import annotations

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F
from pyspark.sql.types import DecimalType, StringType

from carddemo_batch.config.columns import (
    COL_ACCT_CREDIT_LIMIT,
    COL_ACCT_CURR_BAL,
    COL_ACCT_CURR_CYC_CREDIT,
    COL_ACCT_CURR_CYC_DEBIT,
    COL_ACCT_EXPIRATION_DATE,
    COL_ACCT_GROUP_ID,
    COL_ACCT_ID,
    COL_BALANCE_DELTA,
    COL_CURR_BAL_DELTA,
    COL_CYC_CREDIT_DELTA,
    COL_CYC_DEBIT_DELTA,
    COL_TRANCAT_ACCT_ID,
    COL_TRANCAT_CD,
    COL_TRANCAT_TYPE_CD,
    COL_TRAN_AMT,
    COL_TRAN_CARD_NUM,
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
    COL_VALIDATION_FAIL_REASON,
    COL_VALIDATION_FAIL_REASON_DESC,
    COL_XREF_ACCT_ID,
    COL_XREF_CARD_NUM,
    COL_XREF_CUST_ID,
)
from carddemo_batch.config.settings import (
    REJECT_CODE_ACCOUNT_NOT_FOUND,
    REJECT_CODE_EXPIRED_ACCT,
    REJECT_CODE_INVALID_CARD,
    REJECT_CODE_OVERLIMIT,
    REJECT_DESCRIPTIONS,
)


# ---------------------------------------------------------------------------
# Column constants - local aliases for brevity
# ---------------------------------------------------------------------------
_FAIL_REASON = COL_VALIDATION_FAIL_REASON
_FAIL_DESC = COL_VALIDATION_FAIL_REASON_DESC


def _flag_invalid_cards(
    daily_df: DataFrame,
    xref_df: DataFrame,
) -> DataFrame:
    """
    COBOL: 1500-A-LOOKUP-XREF
    Mark transactions whose card number has no entry in card_xref.
    Failure code 100 = INVALID CARD NUMBER FOUND.

    Returns daily_df with added columns:
      xref_cust_id, xref_acct_id,
      validation_fail_reason (updated to 100 when card missing),
      validation_fail_reason_desc.
    """
    joined = daily_df.join(
        xref_df.select(
            F.col(COL_XREF_CARD_NUM),
            F.col(COL_XREF_CUST_ID),
            F.col(COL_XREF_ACCT_ID),
        ),
        on=daily_df[COL_TRAN_CARD_NUM] == xref_df[COL_XREF_CARD_NUM],
        how="left",
    )

    card_missing = F.col(COL_XREF_CARD_NUM).isNull()

    return joined.withColumn(
        _FAIL_REASON,
        F.when(card_missing, F.lit(REJECT_CODE_INVALID_CARD)).otherwise(
            F.lit(0)
        ),
    ).withColumn(
        _FAIL_DESC,
        F.when(card_missing, F.lit(REJECT_DESCRIPTIONS[REJECT_CODE_INVALID_CARD])).otherwise(
            F.lit("")
        ),
    )


def _join_account_master(flagged_df: DataFrame, account_df: DataFrame) -> DataFrame:
    """Join validated card records to the account master (left join preserves unmatched)."""
    return flagged_df.join(
        account_df.select(
            F.col(COL_ACCT_ID),
            F.col(COL_ACCT_CREDIT_LIMIT),
            F.col(COL_ACCT_EXPIRATION_DATE),
            F.col(COL_ACCT_CURR_CYC_CREDIT),
            F.col(COL_ACCT_CURR_CYC_DEBIT),
            F.col(COL_ACCT_CURR_BAL),
            F.col(COL_ACCT_GROUP_ID),
        ),
        on=F.lpad(flagged_df[COL_XREF_ACCT_ID].cast(StringType()), 11, "0") == account_df[COL_ACCT_ID],
        how="left",
    )


def _flag_account_errors(
    flagged_df: DataFrame,
    account_df: DataFrame,
) -> DataFrame:
    """
    COBOL: 1500-B-LOOKUP-ACCT
    For cards that passed xref lookup, check:
      - Account exists  (code 101) — set-based, independent of ordering
      - Overlimit        (code 102) — sequential per account via window
      - Account expired  (code 103) — per-row check

    The overlimit check must be sequential because COBOL REWRITEs the
    account balance after each valid posting (2800-UPDATE-ACCOUNT-REC).
    COBOL tracks credits and debits separately:
      IF DALYTRAN-AMT >= 0  ADD to ACCT-CURR-CYC-CREDIT
      ELSE                  ADD to ACCT-CURR-CYC-DEBIT
    Then checks: (credit + prior_credits) - (debit + prior_debits) + amt.

    A window function with separate cumulative credit/debit sums over
    preceding rows replicates this sequential balance accumulation.
    """
    card_valid = F.col(_FAIL_REASON) == F.lit(0)
    with_acct = _join_account_master(flagged_df, account_df)

    # 101 — account not found (independent of ordering)
    acct_missing = card_valid & F.col(COL_ACCT_ID).isNull()
    # Update _FAIL_DESC before _FAIL_REASON — see note in the 102/103 block below.
    with_101 = with_acct.withColumn(
        _FAIL_DESC,
        F.when(
            acct_missing,
            F.lit(REJECT_DESCRIPTIONS[REJECT_CODE_ACCOUNT_NOT_FOUND]),
        ).otherwise(F.col(_FAIL_DESC)),
    ).withColumn(
        _FAIL_REASON,
        F.when(acct_missing, F.lit(REJECT_CODE_ACCOUNT_NOT_FOUND))
        .otherwise(F.col(_FAIL_REASON)),
    )

    # Window over preceding rows per account (excludes current row)
    w = Window.partitionBy(COL_XREF_ACCT_ID).orderBy(
        COL_TRAN_ORIG_TS, COL_TRAN_ID,
    ).rowsBetween(Window.unboundedPreceding, -1)

    # COBOL tracks credits (>=0) and debits (<0) separately in the
    # account record.  Replicate with two conditional cumulative sums.
    prior_credits = F.coalesce(
        F.sum(F.when(F.col(COL_TRAN_AMT) >= 0, F.col(COL_TRAN_AMT))
              .otherwise(0)).over(w),
        F.lit(0),
    )
    prior_debits = F.coalesce(
        F.sum(F.when(F.col(COL_TRAN_AMT) < 0, F.col(COL_TRAN_AMT))
              .otherwise(0)).over(w),
        F.lit(0),
    )

    # COBOL formula: (CYC_CREDIT + prior_credits) - (CYC_DEBIT + prior_debits) + AMT
    running_bal = (
        (F.col(COL_ACCT_CURR_CYC_CREDIT) + prior_credits)
        - (F.col(COL_ACCT_CURR_CYC_DEBIT) + prior_debits)
        + F.col(COL_TRAN_AMT)
    )

    not_yet_rejected = F.col(_FAIL_REASON) == F.lit(0)
    overlimit = not_yet_rejected & (F.col(COL_ACCT_CREDIT_LIMIT) < running_bal)
    expired = not_yet_rejected & (
        F.col(COL_ACCT_EXPIRATION_DATE) < F.col(COL_TRAN_ORIG_TS).substr(1, 10)
    )

    # COBOL evaluates 102 first then 103; if both true, 103 overwrites 102.
    # Update _FAIL_DESC BEFORE _FAIL_REASON: the `expired`/`overlimit` predicates
    # reference F.col(_FAIL_REASON), which Spark resolves lazily by name. If we
    # mutated _FAIL_REASON first, the second withColumn would re-evaluate those
    # predicates against the already-updated reason and `not_yet_rejected` would
    # collapse to false, silently leaving _FAIL_DESC empty.
    return with_101.withColumn(
        _FAIL_DESC,
        F.when(expired, F.lit(REJECT_DESCRIPTIONS[REJECT_CODE_EXPIRED_ACCT]))
        .when(overlimit, F.lit(REJECT_DESCRIPTIONS[REJECT_CODE_OVERLIMIT]))
        .otherwise(F.col(_FAIL_DESC)),
    ).withColumn(
        _FAIL_REASON,
        F.when(expired, F.lit(REJECT_CODE_EXPIRED_ACCT))
        .when(overlimit, F.lit(REJECT_CODE_OVERLIMIT))
        .otherwise(F.col(_FAIL_REASON)),
    )


def validate_transactions(
    daily_df: DataFrame,
    xref_df: DataFrame,
    account_df: DataFrame,
) -> DataFrame:
    """
    COBOL: 1500-VALIDATE-TRAN (calls 1500-A then 1500-B)
    Adds validation_fail_reason and validation_fail_reason_desc to every row.
    Rows with fail_reason=0 are valid; all others are rejected.

    Also enriches every row with xref_acct_id, xref_cust_id, and account
    master fields needed for downstream posting steps.
    """
    after_xref = _flag_invalid_cards(daily_df, xref_df)
    return _flag_account_errors(after_xref, account_df)


def extract_rejected_transactions(validated_df: DataFrame) -> DataFrame:
    """
    COBOL: 2500-WRITE-REJECT-REC
    Isolate rows where validation failed.  Returns a DataFrame shaped to
    match daily_reject_transactions schema.
    """
    return validated_df.filter(F.col(_FAIL_REASON) != 0).select(
        COL_TRAN_ID,
        COL_TRAN_TYPE_CD,
        COL_TRAN_CAT_CD,
        COL_TRAN_SOURCE,
        COL_TRAN_DESC,
        COL_TRAN_AMT,
        COL_TRAN_MERCHANT_ID,
        COL_TRAN_MERCHANT_NAME,
        COL_TRAN_MERCHANT_CITY,
        COL_TRAN_MERCHANT_ZIP,
        COL_TRAN_CARD_NUM,
        COL_TRAN_ORIG_TS,
        COL_TRAN_PROC_TS,
        _FAIL_REASON,
        _FAIL_DESC,
    )


def build_posted_transactions(
    validated_df: DataFrame,
    proc_ts: str,
) -> DataFrame:
    """
    COBOL: 2000-POST-TRANSACTION
    Build the TRAN-RECORD to be written to the transaction master.
    Only valid (fail_reason=0) rows are included.

    The COBOL program copies all DALYTRAN fields into TRAN-RECORD fields
    and sets TRAN-PROC-TS to the current timestamp.
    """
    return (
        validated_df.filter(F.col(_FAIL_REASON) == 0)
        .withColumn(COL_TRAN_PROC_TS, F.lit(proc_ts))
        .select(
            COL_TRAN_ID,
            COL_TRAN_TYPE_CD,
            COL_TRAN_CAT_CD,
            COL_TRAN_SOURCE,
            COL_TRAN_DESC,
            COL_TRAN_AMT,
            COL_TRAN_MERCHANT_ID,
            COL_TRAN_MERCHANT_NAME,
            COL_TRAN_MERCHANT_CITY,
            COL_TRAN_MERCHANT_ZIP,
            COL_TRAN_CARD_NUM,
            COL_TRAN_ORIG_TS,
            COL_TRAN_PROC_TS,
        )
    )


def build_tcatbal_updates(validated_df: DataFrame) -> DataFrame:
    """
    COBOL: 2700-UPDATE-TCATBAL, 2700-A-CREATE-TCATBAL-REC, 2700-B-UPDATE-TCATBAL-REC
    Compute the net balance change per (acct_id, type_cd, cat_cd) key.

    The COBOL program does a VSAM read-with-key; if status=23 (not found) it
    creates a new record; otherwise it adds to the existing balance.

    In Spark we compute the delta per key and use a MERGE statement to
    upsert into the Delta table (caller performs the MERGE).

    Returns a DataFrame with (trancat_acct_id, trancat_type_cd, trancat_cd,
    balance_delta) representing the net change to apply.
    """
    valid = validated_df.filter(F.col(_FAIL_REASON) == 0)

    return (
        valid.groupBy(
            F.col(COL_XREF_ACCT_ID).alias(COL_TRANCAT_ACCT_ID),
            F.col(COL_TRAN_TYPE_CD).alias(COL_TRANCAT_TYPE_CD),
            F.col(COL_TRAN_CAT_CD).alias(COL_TRANCAT_CD),
        )
        .agg(F.sum(COL_TRAN_AMT).cast(DecimalType(11, 2)).alias(COL_BALANCE_DELTA))
    )


def build_account_balance_updates(validated_df: DataFrame) -> DataFrame:
    """
    COBOL: 2800-UPDATE-ACCOUNT-REC
    Compute per-account balance updates.

    COBOL logic:
      ADD DALYTRAN-AMT TO ACCT-CURR-BAL
      IF DALYTRAN-AMT >= 0:
        ADD DALYTRAN-AMT TO ACCT-CURR-CYC-CREDIT
      ELSE:
        ADD DALYTRAN-AMT TO ACCT-CURR-CYC-DEBIT

    We aggregate all valid transactions per account to get the net deltas.
    Returns (acct_id, curr_bal_delta, cyc_credit_delta, cyc_debit_delta).
    """
    valid = validated_df.filter(F.col(_FAIL_REASON) == 0)

    return (
        valid.groupBy(F.col(COL_XREF_ACCT_ID).alias(COL_ACCT_ID))
        .agg(
            F.sum(COL_TRAN_AMT).cast(DecimalType(12, 2)).alias(COL_CURR_BAL_DELTA),
            F.sum(
                F.when(F.col(COL_TRAN_AMT) >= 0, F.col(COL_TRAN_AMT)).otherwise(F.lit(0))
            ).cast(DecimalType(12, 2)).alias(COL_CYC_CREDIT_DELTA),
            F.sum(
                F.when(F.col(COL_TRAN_AMT) < 0, F.col(COL_TRAN_AMT)).otherwise(F.lit(0))
            ).cast(DecimalType(12, 2)).alias(COL_CYC_DEBIT_DELTA),
        )
    )
