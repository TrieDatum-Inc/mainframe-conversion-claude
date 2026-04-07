"""
Interest calculation logic for CBACT04C.

Replaces COBOL paragraphs:
  1000-TCATBALF-GET-NEXT  — sequential read + sort of driving file
  1200-GET-INTEREST-RATE  — primary rate lookup by (group_id, type_cd, cat_cd)
  1200-A-GET-DEFAULT-INT-RATE — fallback to 'DEFAULT' group when primary not found
  1300-COMPUTE-INTEREST   — monthly_interest = (tran_cat_bal * dis_int_rate) / 1200
  1050-UPDATE-ACCOUNT (accumulation) — groupBy acct_id, sum monthly_interest

Key business rules implemented here:
  BR-1: monthly_interest = (tran_cat_bal * dis_int_rate) / 1200
  BR-2: DEFAULT group fallback (coalesce after double left-join)
  BR-3: Zero-rate bypass — categories with rate=0 or NULL are excluded
  BR-4: Account-level aggregation via groupBy + sum
"""

from decimal import Decimal

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DecimalType, LongType

from .constants import DEFAULT_DISCLOSURE_GROUP, INTEREST_DIVISOR


def read_tran_cat_balance(spark: SparkSession) -> DataFrame:
    """
    Read and sort the TCATBALF driving file from Silver layer.

    Replaces COBOL: OPEN INPUT TCATBAL-FILE + sequential READ loop.
    COBOL assumes TCATBALF is already sorted by TRANCAT-ACCT-ID.
    PySpark enforces this ordering explicitly.

    Returns:
        DataFrame with columns: acct_id, tran_type_cd, tran_cat_cd, tran_cat_bal
    """
    return (
        spark.read.format("delta")
        .table("carddemo.silver.tran_cat_balance")
        .select("acct_id", "tran_type_cd", "tran_cat_cd", "tran_cat_bal")
        .orderBy("acct_id", "tran_type_cd", "tran_cat_cd")
    )


def read_disclosure_group(spark: SparkSession) -> DataFrame:
    """
    Read the DISCGRP interest rate reference table.

    COBOL: OPEN INPUT DISCGRP-FILE (random reads by composite key).
    PySpark: broadcast join candidate — small table, fully fits in memory.

    Returns:
        DataFrame with columns: dis_acct_group_id, dis_tran_type_cd, dis_tran_cat_cd, dis_int_rate
    """
    return spark.read.format("delta").table("carddemo.silver.disclosure_group")


def read_account(spark: SparkSession) -> DataFrame:
    """
    Read account records needed for interest calculation.

    COBOL: OPEN I-O ACCOUNT-FILE (random read by FD-ACCT-ID for acct_group_id).
    PySpark: read all accounts; join to tcatbal on acct_id to get acct_group_id.

    Returns:
        DataFrame with columns: acct_id, acct_group_id (plus balance columns for MERGE step)
    """
    return spark.read.format("delta").table("carddemo.silver.account")


def _build_primary_rate_lookup(discgrp_df: DataFrame) -> DataFrame:
    """
    Extract primary (non-DEFAULT) interest rate rows for broadcast join.

    Returns a DataFrame with aliased columns ready to join against TCATBALF rows
    on (acct_group_id, tran_type_cd, tran_cat_cd).
    """
    return discgrp_df.select(
        F.col("dis_acct_group_id").alias("primary_group_id"),
        F.col("dis_tran_type_cd").alias("primary_type_cd"),
        F.col("dis_tran_cat_cd").alias("primary_cat_cd"),
        F.col("dis_int_rate").alias("primary_int_rate"),
    )


def _build_default_rate_lookup(discgrp_df: DataFrame) -> DataFrame:
    """
    Extract DEFAULT-group interest rate rows for broadcast join.

    Replaces COBOL paragraph 1200-A-GET-DEFAULT-INT-RATE which retries the
    DISCGRP READ with GROUP-ID='DEFAULT' when the primary lookup fails.

    Returns a DataFrame with aliased columns ready to join on (tran_type_cd, tran_cat_cd).
    """
    return (
        discgrp_df
        .filter(F.col("dis_acct_group_id") == DEFAULT_DISCLOSURE_GROUP)
        .select(
            F.col("dis_tran_type_cd").alias("default_type_cd"),
            F.col("dis_tran_cat_cd").alias("default_cat_cd"),
            F.col("dis_int_rate").alias("default_int_rate"),
        )
    )


def _resolve_effective_rate(joined_df: DataFrame) -> DataFrame:
    """
    Coalesce primary and DEFAULT interest rates into a single effective_int_rate column.

    Also adds rate_source to record which disclosure group supplied the rate.
    Drops intermediate join columns produced by the double broadcast join.
    """
    return (
        joined_df
        .withColumn(
            "effective_int_rate",
            F.coalesce(F.col("primary_int_rate"), F.col("default_int_rate")),
        )
        .withColumn(
            "rate_source",
            F.when(F.col("primary_int_rate").isNotNull(), F.col("acct_group_id"))
            .when(F.col("default_int_rate").isNotNull(), F.lit(DEFAULT_DISCLOSURE_GROUP))
            .otherwise(F.lit(None).cast("string")),
        )
        .drop(
            "primary_group_id", "primary_type_cd", "primary_cat_cd",
            "default_type_cd", "default_cat_cd",
        )
    )


def join_interest_rates(
    tcatbal_df: DataFrame,
    acct_df: DataFrame,
    discgrp_df: DataFrame,
) -> DataFrame:
    """
    Join TCATBALF rows with disclosure group interest rates.

    Replicates COBOL paragraphs 1200-GET-INTEREST-RATE and 1200-A-GET-DEFAULT-INT-RATE:
      - Primary lookup: (acct_group_id, tran_type_cd, tran_cat_cd)
      - Fallback: if primary not found (status='23' equivalent = NULL after left join),
        retry with dis_acct_group_id = 'DEFAULT'
      - Effective rate = COALESCE(primary_rate, default_rate)

    Args:
        tcatbal_df: TCATBALF driving file rows.
        acct_df: Account records (for acct_group_id lookup).
        discgrp_df: Disclosure group interest rates.

    Returns:
        DataFrame with effective_int_rate column added; rows without any rate retain NULL.
    """
    # Step 1: Get acct_group_id for each account in the driving file
    # Replaces: 1100-GET-ACCT-DATA — READ ACCOUNT-FILE by FD-ACCT-ID
    tcatbal_with_group = tcatbal_df.join(
        acct_df.select("acct_id", "acct_group_id"),
        on="acct_id",
        how="left",
    )

    # Step 2a: Primary rate lookup
    # Replaces: 1200-GET-INTEREST-RATE — READ DISCGRP by (GROUP-ID + TYPE-CD + CAT-CD)
    primary_rate_df = _build_primary_rate_lookup(discgrp_df)
    joined_primary = tcatbal_with_group.join(
        F.broadcast(primary_rate_df),
        on=(
            (F.col("acct_group_id") == F.col("primary_group_id"))
            & (F.col("tran_type_cd") == F.col("primary_type_cd"))
            & (F.col("tran_cat_cd") == F.col("primary_cat_cd"))
        ),
        how="left",
    )

    # Step 2b: DEFAULT fallback rate lookup
    # Replaces: 1200-A-GET-DEFAULT-INT-RATE — retry with GROUP-ID='DEFAULT'
    default_rate_df = _build_default_rate_lookup(discgrp_df)
    joined_with_default = joined_primary.join(
        F.broadcast(default_rate_df),
        on=(
            (F.col("tran_type_cd") == F.col("default_type_cd"))
            & (F.col("tran_cat_cd") == F.col("default_cat_cd"))
        ),
        how="left",
    )

    # Step 2c: Effective rate = primary if found, else DEFAULT fallback
    # Replaces: COBOL COALESCE logic (primary lookup result or DEFAULT retry)
    return _resolve_effective_rate(joined_with_default)


def _monthly_interest_expr(divisor: int) -> "F.Column":
    """
    Build the BR-1 interest formula as a Spark Column expression.

    Formula: (tran_cat_bal * effective_int_rate) / divisor
    All operands use DecimalType to avoid floating-point rounding errors on financial fields.
    Result is cast to DECIMAL(11,2) to match COBOL S9(9)V99.
    """
    return (
        F.col("tran_cat_bal").cast(DecimalType(11, 2))
        * F.col("effective_int_rate").cast(DecimalType(7, 4))
        / F.lit(Decimal(str(divisor)))
    ).cast(DecimalType(11, 2))


def compute_monthly_interest(tcatbal_with_rate_df: DataFrame) -> DataFrame:
    """
    Compute monthly interest per transaction category row.

    Replaces COBOL paragraph 1300-COMPUTE-INTEREST:
      COMPUTE WS-MONTHLY-INT = (TRAN-CAT-BAL * DIS-INT-RATE) / 1200

    Business rules applied:
      BR-1: Formula: (tran_cat_bal * effective_int_rate) / 1200
      BR-3: Zero-rate bypass — filter out rows where effective_int_rate is NULL or 0

    Uses DecimalType arithmetic exclusively — no floating point for financial fields.

    Args:
        tcatbal_with_rate_df: Output of join_interest_rates().

    Returns:
        DataFrame with monthly_interest column; zero/null-rate rows are excluded.
    """
    # BR-3: Skip zero-rate and NULL-rate categories entirely
    non_zero_rate_df = tcatbal_with_rate_df.filter(
        F.col("effective_int_rate").isNotNull()
        & (F.col("effective_int_rate") != F.lit(Decimal("0")))
    )

    # BR-1: monthly_interest = (tran_cat_bal * dis_int_rate) / 1200
    return non_zero_rate_df.withColumn(
        "monthly_interest",
        _monthly_interest_expr(INTEREST_DIVISOR),
    )


def aggregate_account_interest(interest_df: DataFrame) -> DataFrame:
    """
    Aggregate monthly interest amounts to account level.

    Replaces COBOL paragraph 1050-UPDATE-ACCOUNT (accumulation half):
      ADD WS-MONTHLY-INT TO WS-TOTAL-INT (per account)

    In COBOL, WS-TOTAL-INT accumulates as the sequential file is read row by row,
    reset on each new account. PySpark achieves the identical net result via groupBy.

    Also collects per-category detail for the gold.interest_charges audit table.

    Args:
        interest_df: Output of compute_monthly_interest().

    Returns:
        DataFrame grouped by acct_id with:
          - total_interest: DECIMAL(11,2) — sum of all category interests
          - acct_group_id: STRING — group used for rate lookup
          - category_detail: ARRAY of structs for gold layer
    """
    return interest_df.groupBy("acct_id", "acct_group_id").agg(
        F.sum("monthly_interest").cast(DecimalType(11, 2)).alias("total_interest"),
        F.collect_list(
            F.struct(
                "tran_type_cd",
                "tran_cat_cd",
                "tran_cat_bal",
                "effective_int_rate",
                "rate_source",
                "monthly_interest",
            )
        ).alias("category_detail"),
    )
