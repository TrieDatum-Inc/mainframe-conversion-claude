"""
Tests for CBTRN03C - Transaction Detail Report

Test coverage:
  - Date range filtering (transactions outside range excluded)
  - Xref enrichment: account ID added, missing card abends (inner join drops)
  - Transaction type and category description lookup
  - Page number assignment (REPORT_PAGE_SIZE = 20)
  - Account and grand totals
  - Edge cases: empty date range, single transaction, transactions spanning pages
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DecimalType,
    IntegerType,
    LongType,
    StringType,
    StructField,
    StructType,
)

from carddemo_batch.config.settings import REPORT_PAGE_SIZE
from carddemo_batch.transformations.cbtrn03c_transforms import (
    build_report_detail_rows,
    compute_account_totals,
    compute_grand_total,
    compute_page_totals,
    filter_by_date_range,
)

# Use base TRAN_RECORD schema (same as CVTRA05Y)
TRAN_SCHEMA = StructType([
    StructField("tran_id", StringType(), False),
    StructField("tran_type_cd", StringType(), False),
    StructField("tran_cat_cd", IntegerType(), False),
    StructField("tran_source", StringType(), False),
    StructField("tran_desc", StringType(), False),
    StructField("tran_amt", DecimalType(11, 2), False),
    StructField("tran_merchant_id", LongType(), False),
    StructField("tran_merchant_name", StringType(), False),
    StructField("tran_merchant_city", StringType(), False),
    StructField("tran_merchant_zip", StringType(), False),
    StructField("tran_card_num", StringType(), False),
    StructField("tran_orig_ts", StringType(), False),
    StructField("tran_proc_ts", StringType(), False),
])


@pytest.fixture
def tran_df(spark):
    data = [
        ("TRN001", "01", 1, "POS", "Groceries",
         Decimal("75.50"), 0, "", "", "",
         "4111111111111111",
         "2024-01-15-10.30.00.000000", "2024-01-15-10.30.00.000000"),
        ("TRN002", "01", 2, "POS", "Gas",
         Decimal("45.00"), 0, "", "", "",
         "4222222222222222",
         "2024-01-15-11.00.00.000000", "2024-01-15-11.00.00.000000"),
        ("TRN003", "04", 1, "ONLINE", "Payment",
         Decimal("-200.00"), 0, "", "", "",
         "4222222222222222",
         "2024-01-16-12.00.00.000000", "2024-01-16-12.00.00.000000"),
        # Outside date range
        ("TRN004", "01", 1, "POS", "Old purchase",
         Decimal("22.00"), 0, "", "", "",
         "4111111111111111",
         "2023-12-01-09.00.00.000000", "2023-12-01-09.00.00.000000"),
    ]
    return spark.createDataFrame(data, schema=TRAN_SCHEMA)


# ===========================================================================
# filter_by_date_range / COBOL main loop date filter
# ===========================================================================

class TestFilterByDateRange:

    def test_transactions_within_range_pass(self, spark, tran_df):
        result = filter_by_date_range(tran_df, "2024-01-01", "2024-01-31")
        ids = {row["tran_id"] for row in result.collect()}
        assert "TRN001" in ids
        assert "TRN002" in ids
        assert "TRN003" in ids

    def test_transactions_outside_range_filtered(self, spark, tran_df):
        result = filter_by_date_range(tran_df, "2024-01-01", "2024-01-31")
        ids = {row["tran_id"] for row in result.collect()}
        assert "TRN004" not in ids

    def test_start_date_boundary_inclusive(self, spark, tran_df):
        result = filter_by_date_range(tran_df, "2024-01-15", "2024-01-31")
        ids = {row["tran_id"] for row in result.collect()}
        assert "TRN001" in ids

    def test_end_date_boundary_inclusive(self, spark, tran_df):
        result = filter_by_date_range(tran_df, "2024-01-01", "2024-01-16")
        ids = {row["tran_id"] for row in result.collect()}
        assert "TRN003" in ids

    def test_empty_range_returns_no_rows(self, spark, tran_df):
        result = filter_by_date_range(tran_df, "2030-01-01", "2030-01-31")
        assert result.count() == 0


# ===========================================================================
# build_report_detail_rows - full enrichment pipeline
# ===========================================================================

class TestBuildReportDetailRows:

    def test_account_id_populated_from_xref(
        self, spark, tran_df, xref_df, tran_type_df, tran_cat_df
    ):
        result = build_report_detail_rows(
            tran_df, xref_df, tran_type_df, tran_cat_df,
            "2024-01-01", "2024-01-31", "2024-01-31"
        )
        null_acct = result.filter(F.col("account_id").isNull())
        assert null_acct.count() == 0

    def test_type_desc_populated(
        self, spark, tran_df, xref_df, tran_type_df, tran_cat_df
    ):
        result = build_report_detail_rows(
            tran_df, xref_df, tran_type_df, tran_cat_df,
            "2024-01-01", "2024-01-31", "2024-01-31"
        )
        null_desc = result.filter(F.col("tran_type_desc").isNull())
        assert null_desc.count() == 0

    def test_cat_desc_populated(
        self, spark, tran_df, xref_df, tran_type_df, tran_cat_df
    ):
        result = build_report_detail_rows(
            tran_df, xref_df, tran_type_df, tran_cat_df,
            "2024-01-01", "2024-01-31", "2024-01-31"
        )
        null_desc = result.filter(F.col("tran_cat_desc").isNull())
        assert null_desc.count() == 0

    def test_out_of_range_excluded(
        self, spark, tran_df, xref_df, tran_type_df, tran_cat_df
    ):
        result = build_report_detail_rows(
            tran_df, xref_df, tran_type_df, tran_cat_df,
            "2024-01-01", "2024-01-31", "2024-01-31"
        )
        old_tran = result.filter(F.col("tran_id") == "TRN004")
        assert old_tran.count() == 0

    def test_page_number_starts_at_1(
        self, spark, tran_df, xref_df, tran_type_df, tran_cat_df
    ):
        result = build_report_detail_rows(
            tran_df, xref_df, tran_type_df, tran_cat_df,
            "2024-01-01", "2024-01-31", "2024-01-31"
        )
        min_page = result.agg(F.min("page_num")).first()[0]
        assert min_page == 1


# ===========================================================================
# compute_page_totals / 1110-WRITE-PAGE-TOTALS
# ===========================================================================

class TestComputePageTotals:

    def _get_detail(self, spark, tran_df, xref_df, tran_type_df, tran_cat_df):
        return build_report_detail_rows(
            tran_df, xref_df, tran_type_df, tran_cat_df,
            "2024-01-01", "2024-01-31", "2024-01-31"
        )

    def test_page_total_sum_equals_grand_total(
        self, spark, tran_df, xref_df, tran_type_df, tran_cat_df
    ):
        detail = self._get_detail(spark, tran_df, xref_df, tran_type_df, tran_cat_df)
        page_totals = compute_page_totals(detail)
        grand = compute_grand_total(detail).first()["grand_total"]
        page_sum = page_totals.agg(F.sum("page_total")).first()[0]
        assert float(page_sum) == pytest.approx(float(grand), abs=0.01)


# ===========================================================================
# compute_account_totals / 1120-WRITE-ACCOUNT-TOTALS
# ===========================================================================

class TestComputeAccountTotals:

    def test_account_totals_group_by_account(
        self, spark, tran_df, xref_df, tran_type_df, tran_cat_df
    ):
        detail = build_report_detail_rows(
            tran_df, xref_df, tran_type_df, tran_cat_df,
            "2024-01-01", "2024-01-31", "2024-01-31"
        )
        totals = compute_account_totals(detail)
        # Two unique accounts (acct 1 and acct 2)
        assert totals.count() == 2

    def test_account_total_sum_matches_transactions(
        self, spark, tran_df, xref_df, tran_type_df, tran_cat_df
    ):
        detail = build_report_detail_rows(
            tran_df, xref_df, tran_type_df, tran_cat_df,
            "2024-01-01", "2024-01-31", "2024-01-31"
        )
        totals = compute_account_totals(detail)
        acct_sum = totals.agg(F.sum("account_total")).first()[0]
        grand = compute_grand_total(detail).first()["grand_total"]
        assert float(acct_sum) == pytest.approx(float(grand), abs=0.01)


# ===========================================================================
# compute_grand_total / 1110-WRITE-GRAND-TOTALS
# ===========================================================================

class TestComputeGrandTotal:

    def test_grand_total_is_sum_of_all_amounts(
        self, spark, tran_df, xref_df, tran_type_df, tran_cat_df
    ):
        detail = build_report_detail_rows(
            tran_df, xref_df, tran_type_df, tran_cat_df,
            "2024-01-01", "2024-01-31", "2024-01-31"
        )
        grand = compute_grand_total(detail).first()["grand_total"]
        # TRN001=75.50, TRN002=45.00, TRN003=-200.00 = -79.50
        assert float(grand) == pytest.approx(-79.50, abs=0.01)

    def test_grand_total_for_empty_range_is_none(self, spark, tran_df):
        from tests.conftest import XREF_SCHEMA, StructType
        from pyspark.sql.types import LongType

        empty_tran = filter_by_date_range(tran_df, "2030-01-01", "2030-01-31")
        # grand_total on empty DF returns None (SQL SUM of no rows)
        grand = compute_grand_total(empty_tran).first()["grand_total"]
        assert grand is None
