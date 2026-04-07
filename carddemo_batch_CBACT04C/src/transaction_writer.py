"""
Interest transaction record construction and writing for CBACT04C.

Replaces COBOL paragraphs:
  1110-GET-XREF-DATA    — random READ of XREF-FILE by alternate key FD-XREF-ACCT-ID
  1300-B-WRITE-TX       — build TRAN-RECORD and WRITE to TRANSACT-FILE
  Z-GET-DB2-FORMAT-TIMESTAMP — DB2-format timestamp for TRAN-ORIG-TS / TRAN-PROC-TS

The TRANSACT output is written via Delta MERGE (idempotent on re-run).
One interest transaction record is generated per account (not per category).
"""

from datetime import datetime, timezone

from delta.tables import DeltaTable
from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F
from pyspark.sql.types import DecimalType, IntegerType, LongType, StringType

from .constants import (
    INTEREST_TRAN_CAT_CD,
    INTEREST_TRAN_DESC_PREFIX,
    INTEREST_TRAN_MERCHANT_CITY,
    INTEREST_TRAN_MERCHANT_ID,
    INTEREST_TRAN_MERCHANT_NAME,
    INTEREST_TRAN_MERCHANT_ZIP,
    INTEREST_TRAN_SOURCE,
    INTEREST_TRAN_TYPE_CD,
    TRAN_ID_DATE_CHARS,
    TRAN_ID_SUFFIX_DIGITS,
)
from .timestamp_utils import get_db2_format_timestamp


def _build_tran_id_col(run_date_compact: str, suffix_digits: int) -> "F.Column":
    """
    Build the TRAN-ID column expression.

    Replaces: TRAN-ID = PARM-DATE (8 chars) + WS-TRANID-SUFFIX (6-digit zero-padded counter).
    Uses row_number() over acct_id ordering so the suffix is compact (1-N) and deterministic.
    """
    seq_window = Window.orderBy("acct_id")
    return F.concat(
        F.lit(run_date_compact),
        F.lpad(F.row_number().over(seq_window).cast(StringType()), suffix_digits, "0"),
    )


def _build_tran_desc_col() -> "F.Column":
    """
    Build the TRAN-DESC column expression.

    Replicates COBOL: TRAN-DESC = 'Int. for a/c ' || ZERO-PADDED(ACCT-ID, 11)
    """
    return F.concat(
        F.lit(INTEREST_TRAN_DESC_PREFIX),
        F.lpad(F.col("acct_id").cast(StringType()), 11, "0"),
    )


def read_card_xref(spark: SparkSession) -> DataFrame:
    """
    Read card cross-reference table for card number lookup.

    Replaces COBOL paragraph 1110-GET-XREF-DATA:
      READ XREF-FILE by alternate key FD-XREF-ACCT-ID

    Returns:
        DataFrame with columns: acct_id, card_num
    """
    return (
        spark.read.format("delta")
        .table("carddemo.silver.card_xref")
        .select("acct_id", "card_num")
    )


def build_interest_transactions(
    account_interest_df: DataFrame,
    xref_df: DataFrame,
    run_date: str,
    pipeline_run_id: str,
) -> DataFrame:
    """
    Build TRAN-RECORD rows for each account with non-zero interest.

    Replaces COBOL paragraph 1300-B-WRITE-TX which constructs each field:
      TRAN-ID        = PARM-DATE (8 chars YYYYMMDD) + WS-TRANID-SUFFIX (6-digit counter)
      TRAN-TYPE-CD   = '01'
      TRAN-CAT-CD    = 05
      TRAN-SOURCE    = 'System'
      TRAN-DESC      = 'Int. for a/c ' + zero-padded 11-digit ACCT-ID
      TRAN-AMT       = WS-TOTAL-INT (account-level sum of category interests)
      TRAN-MERCHANT-ID = 0
      TRAN-CARD-NUM  = from XREF lookup (NULL if account not in XREF)
      TRAN-ORIG-TS   = DB2-format current timestamp
      TRAN-PROC-TS   = same as TRAN-ORIG-TS

    TRAN-ID uniqueness: run_date prefix (8 chars, no dashes) + monotonically_increasing_id
    as a zero-padded 6-digit suffix. Final TRAN-ID is 14 chars stored in X(16) field.

    Args:
        account_interest_df: Output of aggregate_account_interest() — one row per account.
        xref_df: Card cross-reference (acct_id, card_num).
        run_date: YYYY-MM-DD string from Databricks widget (replaces JCL PARM-DATE).
        pipeline_run_id: Databricks run ID for metadata columns.

    Returns:
        DataFrame ready to MERGE into carddemo.silver.transaction.
    """
    # Build DB2-format timestamp for TRAN-ORIG-TS and TRAN-PROC-TS
    # Replaces: PERFORM Z-GET-DB2-FORMAT-TIMESTAMP
    current_ts_str = get_db2_format_timestamp(datetime.now(timezone.utc))

    # run_date YYYY-MM-DD → YYYYMMDD (8 chars, no dashes) for TRAN-ID prefix
    # Replaces: PARM-DATE usage in 1300-B-WRITE-TX
    run_date_compact = run_date.replace("-", "")  # e.g. "20260407"
    if len(run_date_compact) != TRAN_ID_DATE_CHARS:
        raise ValueError(
            f"run_date '{run_date}' produces unexpected compact form '{run_date_compact}'"
        )

    # Join with XREF to get card_num per account.
    # Replaces: 1110-GET-XREF-DATA — READ XREF-FILE by FD-XREF-ACCT-ID
    # COBOL: on INVALID KEY → DISPLAY warning and continue (tran_card_num stays as spaces)
    with_xref = account_interest_df.join(xref_df, on="acct_id", how="left")

    # Build all TRAN-RECORD fields in a single withColumns call.
    # row_number() over Window.orderBy("acct_id") produces a compact 1-N TRAN-ID suffix,
    # guaranteed to fit within TRAN_ID_SUFFIX_DIGITS (6) for any realistic batch size.
    # monotonically_increasing_id() was rejected because it encodes partition offsets
    # into the high bits of a 64-bit integer — values like 8589934592 exceed 6 digits
    # on multi-partition DataFrames and cause assert_tran_id_uniqueness to fail when
    # lpad silently truncates the string, producing collisions.
    return (
        with_xref
        .withColumns({
            "tran_id": _build_tran_id_col(run_date_compact, TRAN_ID_SUFFIX_DIGITS),
            "tran_type_cd": F.lit(INTEREST_TRAN_TYPE_CD),
            "tran_cat_cd": F.lit(INTEREST_TRAN_CAT_CD).cast(IntegerType()),
            "tran_source": F.lit(INTEREST_TRAN_SOURCE),
            "tran_desc": _build_tran_desc_col(),
            "tran_amt": F.col("total_interest").cast(DecimalType(11, 2)),
            "tran_merchant_id": F.lit(INTEREST_TRAN_MERCHANT_ID).cast(LongType()),
            "tran_merchant_name": F.lit(INTEREST_TRAN_MERCHANT_NAME),
            "tran_merchant_city": F.lit(INTEREST_TRAN_MERCHANT_CITY),
            "tran_merchant_zip": F.lit(INTEREST_TRAN_MERCHANT_ZIP),
            # NULL if XREF not found — matches COBOL INVALID KEY behaviour
            "tran_card_num": F.col("card_num"),
            "tran_orig_ts": F.lit(current_ts_str),
            "tran_proc_ts": F.lit(current_ts_str),
            "_silver_pipeline_run_id": F.lit(pipeline_run_id),
            "_silver_load_ts": F.current_timestamp(),
        })
        .drop("category_detail", "acct_group_id", "total_interest", "card_num")
    )


def write_interest_transactions(
    spark: SparkSession,
    transactions_df: DataFrame,
) -> int:
    """
    Write interest transaction records to carddemo.silver.transaction via Delta MERGE.

    Replaces COBOL: WRITE TRAN-RECORD TO TRANSACT-FILE (paragraph 1300-B-WRITE-TX).

    Uses MERGE to ensure idempotency on re-run:
      - WHEN MATCHED → no-op (do not overwrite existing transactions with same TRAN-ID)
      - WHEN NOT MATCHED → INSERT all columns

    COBOL used sequential OUTPUT mode (always writes new records). The MERGE guards
    against duplicate inserts on pipeline re-runs without altering existing records.

    Args:
        spark: Active SparkSession.
        transactions_df: DataFrame of new interest transaction records.

    Returns:
        Count of records inserted.
    """
    target = DeltaTable.forName(spark, "carddemo.silver.transaction")

    (
        target.alias("target")
        .merge(
            transactions_df.alias("source"),
            condition="target.tran_id = source.tran_id",
        )
        .whenNotMatchedInsertAll()
        .execute()
    )

    # Return count of rows in the source to report as processed count
    return transactions_df.count()


def assert_tran_id_uniqueness(transactions_df: DataFrame) -> None:
    """
    Data quality check: assert all generated TRAN-IDs are unique within this run.

    Specification section 4.8 requirement:
      'All generated TRAN-IDs must be unique within the run (assert no duplicates post-write)'

    Args:
        transactions_df: DataFrame of generated interest transactions.

    Raises:
        AssertionError: If any TRAN-ID appears more than once.
    """
    total = transactions_df.count()
    distinct = transactions_df.select("tran_id").distinct().count()
    if total != distinct:
        duplicates = (
            transactions_df.groupBy("tran_id")
            .count()
            .filter(F.col("count") > 1)
            .collect()
        )
        raise AssertionError(
            f"TRAN-ID uniqueness violated: {total - distinct} duplicate(s) found. "
            f"Duplicate tran_ids: {[r['tran_id'] for r in duplicates]}"
        )
