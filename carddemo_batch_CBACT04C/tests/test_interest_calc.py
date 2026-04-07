"""
Unit tests for interest_calc.py

Covers COBOL business rules:
  BR-1  Interest formula: monthly_interest = (tran_cat_bal * dis_int_rate) / 1200
  BR-2  DEFAULT group fallback when primary rate not found
  BR-3  Zero-rate bypass: categories with rate=0 or NULL are excluded
  BR-4  Account-level aggregation via groupBy + sum

Each test maps to one or more COBOL paragraphs as documented in the spec.
"""

from decimal import Decimal

import pytest
from pyspark.sql import Row
from pyspark.sql.types import (
    DecimalType,
    IntegerType,
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

from src.interest_calc import (
    aggregate_account_interest,
    compute_monthly_interest,
    join_interest_rates,
)
from src.constants import DEFAULT_DISCLOSURE_GROUP


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

TCATBAL_SCHEMA = StructType([
    StructField("acct_id", LongType(), False),
    StructField("tran_type_cd", StringType(), False),
    StructField("tran_cat_cd", IntegerType(), False),
    StructField("tran_cat_bal", DecimalType(11, 2), False),
    StructField("_silver_load_ts", TimestampType(), True),
    StructField("_silver_pipeline_run_id", StringType(), True),
    StructField("_silver_last_updated_ts", TimestampType(), True),
])

ACCOUNT_SCHEMA = StructType([
    StructField("acct_id", LongType(), False),
    StructField("acct_group_id", StringType(), True),
    StructField("acct_curr_bal", DecimalType(12, 2), True),
    StructField("acct_curr_cyc_credit", DecimalType(12, 2), True),
    StructField("acct_curr_cyc_debit", DecimalType(12, 2), True),
])

DISCGRP_SCHEMA = StructType([
    StructField("dis_acct_group_id", StringType(), False),
    StructField("dis_tran_type_cd", StringType(), False),
    StructField("dis_tran_cat_cd", IntegerType(), False),
    StructField("dis_int_rate", DecimalType(7, 4), False),
])


# ---------------------------------------------------------------------------
# BR-1: Interest formula
# ---------------------------------------------------------------------------

class TestComputeMonthlyInterest:
    """Tests for COBOL paragraph 1300-COMPUTE-INTEREST."""

    def test_basic_formula(self, spark):
        """
        BR-1: monthly_interest = (tran_cat_bal * dis_int_rate) / 1200
        Example: balance=1000.00, rate=12.0000 → (1000 * 12) / 1200 = 10.00
        """
        rows = [Row(
            acct_id=1,
            tran_type_cd="01",
            tran_cat_cd=1,
            tran_cat_bal=Decimal("1000.00"),
            acct_group_id="GROUP1",
            effective_int_rate=Decimal("12.0000"),
            rate_source="GROUP1",
        )]
        schema = StructType([
            StructField("acct_id", LongType()),
            StructField("tran_type_cd", StringType()),
            StructField("tran_cat_cd", IntegerType()),
            StructField("tran_cat_bal", DecimalType(11, 2)),
            StructField("acct_group_id", StringType()),
            StructField("effective_int_rate", DecimalType(7, 4)),
            StructField("rate_source", StringType()),
        ])
        df = spark.createDataFrame(rows, schema)
        result = compute_monthly_interest(df).collect()

        assert len(result) == 1
        assert result[0]["monthly_interest"] == Decimal("10.00")

    def test_high_balance(self, spark):
        """
        BR-1: large balance with 18% annual rate.
        Example: balance=50000.00, rate=18.0000 → (50000 * 18) / 1200 = 750.00
        """
        rows = [Row(
            acct_id=1,
            tran_type_cd="01",
            tran_cat_cd=1,
            tran_cat_bal=Decimal("50000.00"),
            acct_group_id="GROUP1",
            effective_int_rate=Decimal("18.0000"),
            rate_source="GROUP1",
        )]
        schema = StructType([
            StructField("acct_id", LongType()),
            StructField("tran_type_cd", StringType()),
            StructField("tran_cat_cd", IntegerType()),
            StructField("tran_cat_bal", DecimalType(11, 2)),
            StructField("acct_group_id", StringType()),
            StructField("effective_int_rate", DecimalType(7, 4)),
            StructField("rate_source", StringType()),
        ])
        df = spark.createDataFrame(rows, schema)
        result = compute_monthly_interest(df).collect()
        assert result[0]["monthly_interest"] == Decimal("750.00")

    def test_fractional_result_rounded(self, spark):
        """
        BR-1: Result is cast to DECIMAL(11,2) — fractional cents rounded.
        balance=100.00, rate=1.0000 → (100 * 1) / 1200 = 0.08 (rounded from 0.0833...)
        """
        rows = [Row(
            acct_id=1,
            tran_type_cd="01",
            tran_cat_cd=1,
            tran_cat_bal=Decimal("100.00"),
            acct_group_id="G1",
            effective_int_rate=Decimal("1.0000"),
            rate_source="G1",
        )]
        schema = StructType([
            StructField("acct_id", LongType()),
            StructField("tran_type_cd", StringType()),
            StructField("tran_cat_cd", IntegerType()),
            StructField("tran_cat_bal", DecimalType(11, 2)),
            StructField("acct_group_id", StringType()),
            StructField("effective_int_rate", DecimalType(7, 4)),
            StructField("rate_source", StringType()),
        ])
        df = spark.createDataFrame(rows, schema)
        result = compute_monthly_interest(df).collect()
        # DECIMAL(11,2) cast: (100 * 1.0000) / 1200 = 0.08333... → 0.08
        assert result[0]["monthly_interest"] == Decimal("0.08")

    def test_zero_rate_excluded(self, spark):
        """
        BR-3: Zero-rate bypass — rows with effective_int_rate=0 must be excluded.
        Replaces: COBOL 'IF DIS-INT-RATE = 0 NEXT SENTENCE'
        """
        rows = [Row(
            acct_id=1,
            tran_type_cd="01",
            tran_cat_cd=1,
            tran_cat_bal=Decimal("5000.00"),
            acct_group_id="G1",
            effective_int_rate=Decimal("0.0000"),
            rate_source="G1",
        )]
        schema = StructType([
            StructField("acct_id", LongType()),
            StructField("tran_type_cd", StringType()),
            StructField("tran_cat_cd", IntegerType()),
            StructField("tran_cat_bal", DecimalType(11, 2)),
            StructField("acct_group_id", StringType()),
            StructField("effective_int_rate", DecimalType(7, 4)),
            StructField("rate_source", StringType()),
        ])
        df = spark.createDataFrame(rows, schema)
        result = compute_monthly_interest(df).collect()
        assert len(result) == 0, "Zero-rate row should be excluded (BR-3)"

    def test_null_rate_excluded(self, spark):
        """
        BR-3: Rows with NULL effective_int_rate (no group, no DEFAULT) must be excluded.
        """
        rows = [Row(
            acct_id=1,
            tran_type_cd="01",
            tran_cat_cd=1,
            tran_cat_bal=Decimal("5000.00"),
            acct_group_id="UNKNOWN",
            effective_int_rate=None,
            rate_source=None,
        )]
        schema = StructType([
            StructField("acct_id", LongType()),
            StructField("tran_type_cd", StringType()),
            StructField("tran_cat_cd", IntegerType()),
            StructField("tran_cat_bal", DecimalType(11, 2)),
            StructField("acct_group_id", StringType()),
            StructField("effective_int_rate", DecimalType(7, 4)),
            StructField("rate_source", StringType()),
        ])
        df = spark.createDataFrame(rows, schema)
        result = compute_monthly_interest(df).collect()
        assert len(result) == 0, "NULL-rate row should be excluded (BR-3)"

    def test_mixed_rates(self, spark):
        """
        BR-1 + BR-3: Multiple rows; zero-rate row excluded, non-zero rows computed.
        """
        rows = [
            Row(acct_id=1, tran_type_cd="01", tran_cat_cd=1, tran_cat_bal=Decimal("1200.00"),
                acct_group_id="G1", effective_int_rate=Decimal("12.0000"), rate_source="G1"),
            Row(acct_id=1, tran_type_cd="01", tran_cat_cd=2, tran_cat_bal=Decimal("600.00"),
                acct_group_id="G1", effective_int_rate=Decimal("0.0000"), rate_source="G1"),
            Row(acct_id=1, tran_type_cd="02", tran_cat_cd=1, tran_cat_bal=Decimal("2400.00"),
                acct_group_id="G1", effective_int_rate=Decimal("24.0000"), rate_source="G1"),
        ]
        schema = StructType([
            StructField("acct_id", LongType()),
            StructField("tran_type_cd", StringType()),
            StructField("tran_cat_cd", IntegerType()),
            StructField("tran_cat_bal", DecimalType(11, 2)),
            StructField("acct_group_id", StringType()),
            StructField("effective_int_rate", DecimalType(7, 4)),
            StructField("rate_source", StringType()),
        ])
        df = spark.createDataFrame(rows, schema)
        result = compute_monthly_interest(df).orderBy("tran_type_cd", "tran_cat_cd").collect()

        # Only 2 rows (zero-rate excluded)
        assert len(result) == 2
        # acct_id=1, type=01, cat=1: (1200 * 12) / 1200 = 12.00
        assert result[0]["monthly_interest"] == Decimal("12.00")
        # acct_id=1, type=02, cat=1: (2400 * 24) / 1200 = 48.00
        assert result[1]["monthly_interest"] == Decimal("48.00")


# ---------------------------------------------------------------------------
# BR-2: DEFAULT group fallback
# ---------------------------------------------------------------------------

class TestJoinInterestRates:
    """Tests for COBOL paragraphs 1200-GET-INTEREST-RATE and 1200-A-GET-DEFAULT-INT-RATE."""

    def _make_tcatbal(self, spark, rows):
        schema = StructType([
            StructField("acct_id", LongType()),
            StructField("tran_type_cd", StringType()),
            StructField("tran_cat_cd", IntegerType()),
            StructField("tran_cat_bal", DecimalType(11, 2)),
        ])
        return spark.createDataFrame(rows, schema)

    def _make_account(self, spark, rows):
        schema = StructType([
            StructField("acct_id", LongType()),
            StructField("acct_group_id", StringType()),
            StructField("acct_curr_bal", DecimalType(12, 2)),
            StructField("acct_curr_cyc_credit", DecimalType(12, 2)),
            StructField("acct_curr_cyc_debit", DecimalType(12, 2)),
        ])
        return spark.createDataFrame(rows, schema)

    def _make_discgrp(self, spark, rows):
        schema = StructType([
            StructField("dis_acct_group_id", StringType()),
            StructField("dis_tran_type_cd", StringType()),
            StructField("dis_tran_cat_cd", IntegerType()),
            StructField("dis_int_rate", DecimalType(7, 4)),
        ])
        return spark.createDataFrame(rows, schema)

    def test_primary_rate_found(self, spark):
        """
        BR-2a: Primary rate lookup succeeds — account group found in DISCGRP.
        Replaces: 1200-GET-INTEREST-RATE returning status '00'
        """
        tcatbal = self._make_tcatbal(spark, [
            Row(acct_id=1, tran_type_cd="01", tran_cat_cd=1, tran_cat_bal=Decimal("1000.00")),
        ])
        account = self._make_account(spark, [
            Row(acct_id=1, acct_group_id="GROUPABC",
                acct_curr_bal=Decimal("0"), acct_curr_cyc_credit=Decimal("0"), acct_curr_cyc_debit=Decimal("0")),
        ])
        discgrp = self._make_discgrp(spark, [
            Row(dis_acct_group_id="GROUPABC", dis_tran_type_cd="01", dis_tran_cat_cd=1,
                dis_int_rate=Decimal("18.0000")),
        ])

        result = join_interest_rates(tcatbal, account, discgrp).collect()
        assert len(result) == 1
        assert result[0]["effective_int_rate"] == Decimal("18.0000")
        assert result[0]["rate_source"] == "GROUPABC"

    def test_default_fallback_used(self, spark):
        """
        BR-2b: Primary rate not found (status='23' equivalent) — DEFAULT group used.
        Replaces: 1200-GET-INTEREST-RATE → status='23' → 1200-A-GET-DEFAULT-INT-RATE
        """
        tcatbal = self._make_tcatbal(spark, [
            Row(acct_id=2, tran_type_cd="01", tran_cat_cd=1, tran_cat_bal=Decimal("500.00")),
        ])
        account = self._make_account(spark, [
            Row(acct_id=2, acct_group_id="NOGROUP",
                acct_curr_bal=Decimal("0"), acct_curr_cyc_credit=Decimal("0"), acct_curr_cyc_debit=Decimal("0")),
        ])
        discgrp = self._make_discgrp(spark, [
            # No entry for NOGROUP — only DEFAULT
            Row(dis_acct_group_id=DEFAULT_DISCLOSURE_GROUP, dis_tran_type_cd="01",
                dis_tran_cat_cd=1, dis_int_rate=Decimal("15.0000")),
        ])

        result = join_interest_rates(tcatbal, account, discgrp).collect()
        assert len(result) == 1
        assert result[0]["effective_int_rate"] == Decimal("15.0000")
        assert result[0]["rate_source"] == DEFAULT_DISCLOSURE_GROUP

    def test_primary_takes_precedence_over_default(self, spark):
        """
        BR-2: When both primary and DEFAULT exist, primary rate is used.
        coalesce(primary_rate, default_rate) → primary always wins.
        """
        tcatbal = self._make_tcatbal(spark, [
            Row(acct_id=3, tran_type_cd="01", tran_cat_cd=1, tran_cat_bal=Decimal("1000.00")),
        ])
        account = self._make_account(spark, [
            Row(acct_id=3, acct_group_id="GROUPXYZ",
                acct_curr_bal=Decimal("0"), acct_curr_cyc_credit=Decimal("0"), acct_curr_cyc_debit=Decimal("0")),
        ])
        discgrp = self._make_discgrp(spark, [
            Row(dis_acct_group_id="GROUPXYZ", dis_tran_type_cd="01", dis_tran_cat_cd=1,
                dis_int_rate=Decimal("20.0000")),
            Row(dis_acct_group_id=DEFAULT_DISCLOSURE_GROUP, dis_tran_type_cd="01",
                dis_tran_cat_cd=1, dis_int_rate=Decimal("10.0000")),
        ])

        result = join_interest_rates(tcatbal, account, discgrp).collect()
        assert result[0]["effective_int_rate"] == Decimal("20.0000")
        assert result[0]["rate_source"] == "GROUPXYZ"

    def test_no_rate_no_default(self, spark):
        """
        BR-2c: No primary and no DEFAULT → effective_int_rate = NULL (row remains for logging).
        """
        tcatbal = self._make_tcatbal(spark, [
            Row(acct_id=4, tran_type_cd="01", tran_cat_cd=99, tran_cat_bal=Decimal("1000.00")),
        ])
        account = self._make_account(spark, [
            Row(acct_id=4, acct_group_id="GHOST",
                acct_curr_bal=Decimal("0"), acct_curr_cyc_credit=Decimal("0"), acct_curr_cyc_debit=Decimal("0")),
        ])
        discgrp = self._make_discgrp(spark, [
            # Nothing matches type_cd=01, cat_cd=99
            Row(dis_acct_group_id="OTHER", dis_tran_type_cd="02", dis_tran_cat_cd=1,
                dis_int_rate=Decimal("5.0000")),
        ])

        result = join_interest_rates(tcatbal, account, discgrp).collect()
        assert len(result) == 1
        assert result[0]["effective_int_rate"] is None

    def test_account_not_in_silver(self, spark):
        """
        BR-2 error path: Account not found in silver.account → acct_group_id = NULL.
        Rate lookup uses NULL group → no primary match → DEFAULT fallback if exists.
        Replaces: 1100-GET-ACCT-DATA INVALID KEY (log warning, continue)
        """
        tcatbal = self._make_tcatbal(spark, [
            Row(acct_id=999, tran_type_cd="01", tran_cat_cd=1, tran_cat_bal=Decimal("1000.00")),
        ])
        account = self._make_account(spark, [])  # empty — account 999 not found

        discgrp = self._make_discgrp(spark, [
            Row(dis_acct_group_id=DEFAULT_DISCLOSURE_GROUP, dis_tran_type_cd="01",
                dis_tran_cat_cd=1, dis_int_rate=Decimal("12.0000")),
        ])

        result = join_interest_rates(tcatbal, account, discgrp).collect()
        assert len(result) == 1
        # acct_group_id is NULL but DEFAULT fallback should provide a rate
        assert result[0]["effective_int_rate"] == Decimal("12.0000")
        assert result[0]["rate_source"] == DEFAULT_DISCLOSURE_GROUP


# ---------------------------------------------------------------------------
# BR-4: Account-level aggregation
# ---------------------------------------------------------------------------

class TestAggregateAccountInterest:
    """Tests for COBOL 1050-UPDATE-ACCOUNT accumulation logic."""

    def _make_interest_df(self, spark, rows):
        schema = StructType([
            StructField("acct_id", LongType()),
            StructField("tran_type_cd", StringType()),
            StructField("tran_cat_cd", IntegerType()),
            StructField("tran_cat_bal", DecimalType(11, 2)),
            StructField("acct_group_id", StringType()),
            StructField("effective_int_rate", DecimalType(7, 4)),
            StructField("rate_source", StringType()),
            StructField("monthly_interest", DecimalType(11, 2)),
        ])
        return spark.createDataFrame(rows, schema)

    def test_single_category(self, spark):
        """Single category per account: total_interest = monthly_interest."""
        df = self._make_interest_df(spark, [
            Row(acct_id=1, tran_type_cd="01", tran_cat_cd=1,
                tran_cat_bal=Decimal("1000.00"), acct_group_id="G1",
                effective_int_rate=Decimal("12.0"), rate_source="G1",
                monthly_interest=Decimal("10.00")),
        ])
        result = aggregate_account_interest(df).collect()
        assert len(result) == 1
        assert result[0]["total_interest"] == Decimal("10.00")

    def test_multiple_categories_same_account(self, spark):
        """
        BR-4: Multiple categories for same account are summed.
        Replaces: COBOL ADD WS-MONTHLY-INT TO WS-TOTAL-INT (accumulator loop)
        """
        df = self._make_interest_df(spark, [
            Row(acct_id=1, tran_type_cd="01", tran_cat_cd=1,
                tran_cat_bal=Decimal("1200.00"), acct_group_id="G1",
                effective_int_rate=Decimal("12.0"), rate_source="G1",
                monthly_interest=Decimal("12.00")),
            Row(acct_id=1, tran_type_cd="01", tran_cat_cd=2,
                tran_cat_bal=Decimal("2400.00"), acct_group_id="G1",
                effective_int_rate=Decimal("12.0"), rate_source="G1",
                monthly_interest=Decimal("24.00")),
            Row(acct_id=1, tran_type_cd="02", tran_cat_cd=1,
                tran_cat_bal=Decimal("600.00"), acct_group_id="G1",
                effective_int_rate=Decimal("18.0"), rate_source="G1",
                monthly_interest=Decimal("9.00")),
        ])
        result = aggregate_account_interest(df).collect()
        assert len(result) == 1
        assert result[0]["total_interest"] == Decimal("45.00")  # 12 + 24 + 9

    def test_multiple_accounts_independent(self, spark):
        """
        BR-4: Each account accumulates independently.
        Replaces: COBOL WS-TOTAL-INT reset on each new TRANCAT-ACCT-ID change.
        """
        df = self._make_interest_df(spark, [
            Row(acct_id=1, tran_type_cd="01", tran_cat_cd=1,
                tran_cat_bal=Decimal("1000.00"), acct_group_id="G1",
                effective_int_rate=Decimal("12.0"), rate_source="G1",
                monthly_interest=Decimal("10.00")),
            Row(acct_id=2, tran_type_cd="01", tran_cat_cd=1,
                tran_cat_bal=Decimal("2000.00"), acct_group_id="G2",
                effective_int_rate=Decimal("18.0"), rate_source="G2",
                monthly_interest=Decimal("30.00")),
        ])
        result = (
            aggregate_account_interest(df)
            .orderBy("acct_id")
            .collect()
        )
        assert len(result) == 2
        assert result[0]["acct_id"] == 1
        assert result[0]["total_interest"] == Decimal("10.00")
        assert result[1]["acct_id"] == 2
        assert result[1]["total_interest"] == Decimal("30.00")

    def test_category_detail_preserved(self, spark):
        """
        BR-4: category_detail array contains per-category breakdown for gold layer.
        """
        df = self._make_interest_df(spark, [
            Row(acct_id=1, tran_type_cd="01", tran_cat_cd=1,
                tran_cat_bal=Decimal("1000.00"), acct_group_id="G1",
                effective_int_rate=Decimal("12.0"), rate_source="G1",
                monthly_interest=Decimal("10.00")),
            Row(acct_id=1, tran_type_cd="01", tran_cat_cd=2,
                tran_cat_bal=Decimal("500.00"), acct_group_id="G1",
                effective_int_rate=Decimal("12.0"), rate_source="G1",
                monthly_interest=Decimal("5.00")),
        ])
        result = aggregate_account_interest(df).collect()
        assert len(result[0]["category_detail"]) == 2
