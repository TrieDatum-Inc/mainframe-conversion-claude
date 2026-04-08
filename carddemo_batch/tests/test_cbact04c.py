"""
Tests for CBACT04C - Interest Calculator

Test coverage:
  - Interest rate resolution: specific group, fallback to DEFAULT
  - Zero-rate categories are excluded (COBOL: IF DIS-INT-RATE NOT = 0)
  - Monthly interest computation: (bal * rate) / 1200
  - Interest transaction building: correct fields, type/cat codes, description
  - Account update aggregation: total interest per account, cycle reset
  - Edge cases: no matching disclosure group, multiple categories per account
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from pyspark.sql import functions as F
from pyspark.sql.types import DecimalType, IntegerType, LongType, StringType, StructField, StructType

from carddemo_batch.config.settings import (
    INTEREST_DEFAULT_GROUP,
    INTEREST_DIVISOR,
    INTEREST_TRAN_CAT_CD,
    INTEREST_TRAN_SOURCE,
    INTEREST_TRAN_TYPE_CD,
)
from carddemo_batch.transformations.cbact04c_transforms import (
    build_account_interest_updates,
    build_interest_transactions,
    compute_monthly_interest,
    resolve_interest_rates,
)


# ===========================================================================
# resolve_interest_rates / 1200-GET-INTEREST-RATE
# ===========================================================================

class TestResolveInterestRates:

    def test_specific_group_rate_used_when_available(
        self, spark, tcatbal_df, account_df, xref_df, discgrp_df
    ):
        """
        Account 1 is in GOLD group.
        GOLD/01/1 has rate 14.99 vs DEFAULT/01/1 rate 18.00.
        Specific rate should win.
        """
        result = resolve_interest_rates(tcatbal_df, account_df, xref_df, discgrp_df)
        acct1_cat1 = result.filter(
            (F.col("trancat_acct_id") == 1)
            & (F.col("trancat_type_cd") == "01")
            & (F.col("trancat_cd") == 1)
        ).first()
        assert acct1_cat1 is not None
        assert float(acct1_cat1["dis_int_rate"]) == pytest.approx(14.99)

    def test_default_fallback_when_group_not_found(self, spark, tcatbal_df, account_df, xref_df, discgrp_df):
        """
        Account 2 is in DEFAULT group.
        For type 02 cat 1 - not in GOLD, should get DEFAULT rate 24.00.
        """
        result = resolve_interest_rates(tcatbal_df, account_df, xref_df, discgrp_df)
        acct2_cash = result.filter(
            (F.col("trancat_acct_id") == 2)
            & (F.col("trancat_type_cd") == "02")
            & (F.col("trancat_cd") == 1)
        ).first()
        assert acct2_cash is not None
        assert float(acct2_cash["dis_int_rate"]) == pytest.approx(24.00)

    def test_xref_card_num_populated(self, spark, tcatbal_df, account_df, xref_df, discgrp_df):
        """xref_card_num must be populated for use in 1300-B-WRITE-TX."""
        result = resolve_interest_rates(tcatbal_df, account_df, xref_df, discgrp_df)
        acct1 = result.filter(F.col("trancat_acct_id") == 1).first()
        assert acct1["xref_card_num"] is not None
        assert len(acct1["xref_card_num"]) == 16


# ===========================================================================
# compute_monthly_interest / 1300-COMPUTE-INTEREST
# ===========================================================================

class TestComputeMonthlyInterest:

    def test_formula_matches_cobol(self, spark, tcatbal_df, account_df, xref_df, discgrp_df):
        """
        COBOL: WS-MONTHLY-INT = (TRAN-CAT-BAL * DIS-INT-RATE) / 1200
        For acct 1, cat 1: bal=850.00, rate=14.99 (GOLD)
        Expected = (850 * 14.99) / 1200 = 12741.50 / 1200 = 10.618... ~ 10.62
        """
        enriched = resolve_interest_rates(tcatbal_df, account_df, xref_df, discgrp_df)
        result = compute_monthly_interest(enriched)
        acct1_cat1 = result.filter(
            (F.col("trancat_acct_id") == 1) & (F.col("trancat_cd") == 1)
        ).first()
        expected = round(float(850 * 14.99) / 1200, 2)
        assert float(acct1_cat1["monthly_interest"]) == pytest.approx(expected, abs=0.01)

    def test_zero_rate_rows_excluded(self, spark, tcatbal_df, account_df, xref_df, discgrp_df, spark_fixture=None):
        """
        COBOL: IF DIS-INT-RATE NOT = 0 PERFORM 1300-COMPUTE-INTEREST
        Categories with zero rate must be excluded.
        """
        # Add a zero-rate disclosure group entry
        from tests.conftest import DISCGRP_SCHEMA
        zero_rate_data = [("ZERO      ", "01", 1, Decimal("0.00"))]
        zero_df = spark.createDataFrame(zero_rate_data, schema=DISCGRP_SCHEMA)

        from tests.conftest import TCATBAL_SCHEMA
        zero_bal_data = [(99, "01", 1, Decimal("5000.00"))]
        zero_bal_df = spark.createDataFrame(zero_bal_data, schema=TCATBAL_SCHEMA)

        from tests.conftest import ACCOUNT_SCHEMA, XREF_SCHEMA
        zero_acct = spark.createDataFrame(
            [("00000000099", "Y", Decimal("0"), Decimal("10000"), Decimal("2000"),
              "2020-01-01", "2030-01-01", "2025-01-01",
              Decimal("0"), Decimal("0"), "99999", "ZERO      ")],
            schema=ACCOUNT_SCHEMA,
        )
        zero_xref = spark.createDataFrame(
            [("9999999999999999", 999, 99)], schema=XREF_SCHEMA
        )

        enriched = resolve_interest_rates(zero_bal_df, zero_acct, zero_xref, zero_df)
        result = compute_monthly_interest(enriched)
        assert result.count() == 0

    def test_all_valid_rates_produce_rows(self, spark, tcatbal_df, account_df, xref_df, discgrp_df):
        enriched = resolve_interest_rates(tcatbal_df, account_df, xref_df, discgrp_df)
        result = compute_monthly_interest(enriched)
        # All 4 tcatbal rows have non-zero rates
        assert result.count() == 4


# ===========================================================================
# build_interest_transactions / 1300-B-WRITE-TX
# ===========================================================================

class TestBuildInterestTransactions:

    def _get_interest_df(self, spark, tcatbal_df, account_df, xref_df, discgrp_df):
        enriched = resolve_interest_rates(tcatbal_df, account_df, xref_df, discgrp_df)
        return compute_monthly_interest(enriched)

    def test_tran_type_cd_is_01(self, spark, tcatbal_df, account_df, xref_df, discgrp_df):
        interest_df = self._get_interest_df(spark, tcatbal_df, account_df, xref_df, discgrp_df)
        result = build_interest_transactions(interest_df, "2024-01-15", "2024-01-15-12.00.00.000000")
        types = result.select("tran_type_cd").distinct().collect()
        assert len(types) == 1
        assert types[0]["tran_type_cd"] == INTEREST_TRAN_TYPE_CD

    def test_tran_cat_cd_is_05(self, spark, tcatbal_df, account_df, xref_df, discgrp_df):
        interest_df = self._get_interest_df(spark, tcatbal_df, account_df, xref_df, discgrp_df)
        result = build_interest_transactions(interest_df, "2024-01-15", "2024-01-15-12.00.00.000000")
        cats = result.select("tran_cat_cd").distinct().collect()
        assert cats[0]["tran_cat_cd"] == INTEREST_TRAN_CAT_CD

    def test_tran_source_is_system(self, spark, tcatbal_df, account_df, xref_df, discgrp_df):
        interest_df = self._get_interest_df(spark, tcatbal_df, account_df, xref_df, discgrp_df)
        result = build_interest_transactions(interest_df, "2024-01-15", "2024-01-15-12.00.00.000000")
        assert result.filter(F.col("tran_source") != INTEREST_TRAN_SOURCE).count() == 0

    def test_tran_desc_contains_acct_id(self, spark, tcatbal_df, account_df, xref_df, discgrp_df):
        """
        COBOL: STRING 'Int. for a/c ' ACCT-ID INTO TRAN-DESC
        """
        interest_df = self._get_interest_df(spark, tcatbal_df, account_df, xref_df, discgrp_df)
        result = build_interest_transactions(interest_df, "2024-01-15", "2024-01-15-12.00.00.000000")
        descs = result.select("tran_desc").collect()
        for row in descs:
            assert row["tran_desc"].startswith("Int. for a/c ")

    def test_tran_id_starts_with_parm_date(self, spark, tcatbal_df, account_df, xref_df, discgrp_df):
        """
        COBOL: STRING PARM-DATE WS-TRANID-SUFFIX INTO TRAN-ID
        """
        parm_date = "2024-01-15"
        interest_df = self._get_interest_df(spark, tcatbal_df, account_df, xref_df, discgrp_df)
        result = build_interest_transactions(interest_df, parm_date, "2024-01-15-12.00.00.000000")
        ids = result.select("tran_id").collect()
        for row in ids:
            assert row["tran_id"].startswith(parm_date)


# ===========================================================================
# build_account_interest_updates / 1050-UPDATE-ACCOUNT
# ===========================================================================

class TestBuildAccountInterestUpdates:

    def test_total_interest_aggregated_per_account(self, spark, tcatbal_df, account_df, xref_df, discgrp_df):
        """
        COBOL: ADD WS-MONTHLY-INT TO WS-TOTAL-INT (per account boundary)
        """
        enriched = resolve_interest_rates(tcatbal_df, account_df, xref_df, discgrp_df)
        interest_df = compute_monthly_interest(enriched)
        updates = build_account_interest_updates(interest_df)

        # Account 1 has two categories (type 01 cat 1 and cat 2)
        acct1 = updates.filter(F.col("trancat_acct_id") == 1).first()
        assert acct1 is not None
        # Total interest must be > 0
        assert float(acct1["total_interest"]) > 0

    def test_reset_cycle_balances_flag_set(self, spark, tcatbal_df, account_df, xref_df, discgrp_df):
        """
        COBOL: MOVE 0 TO ACCT-CURR-CYC-CREDIT / ACCT-CURR-CYC-DEBIT
        """
        enriched = resolve_interest_rates(tcatbal_df, account_df, xref_df, discgrp_df)
        interest_df = compute_monthly_interest(enriched)
        updates = build_account_interest_updates(interest_df)
        assert updates.filter(F.col("reset_cycle_balances") == True).count() == updates.count()
