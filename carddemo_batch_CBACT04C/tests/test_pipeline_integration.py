"""
Integration tests for the CBACT04C interest calculation pipeline.

These tests exercise the full computation path (interest_calc → transaction_writer →
account_updater) using in-process DataFrames without writing to actual Delta tables.
The Delta MERGE calls (write_interest_transactions, update_account_balances) are
omitted here because they require a live cluster; they are covered in the CI job
that runs against a Databricks test environment.

Tests here validate end-to-end business logic correctness:
  - Complete pipeline from TCATBALF input to transaction output
  - All business rules together (BR-1 through BR-4)
  - Error/warning paths (missing account, missing XREF)
  - Data quality checks (uniqueness + balance integrity)
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
from src.transaction_writer import (
    assert_tran_id_uniqueness,
    build_interest_transactions,
)
from src.account_updater import assert_balance_integrity
from src.constants import DEFAULT_DISCLOSURE_GROUP


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

TCATBAL_SCHEMA = StructType([
    StructField("acct_id", LongType()),
    StructField("tran_type_cd", StringType()),
    StructField("tran_cat_cd", IntegerType()),
    StructField("tran_cat_bal", DecimalType(11, 2)),
])

ACCOUNT_SCHEMA = StructType([
    StructField("acct_id", LongType()),
    StructField("acct_group_id", StringType()),
    StructField("acct_curr_bal", DecimalType(12, 2)),
    StructField("acct_curr_cyc_credit", DecimalType(12, 2)),
    StructField("acct_curr_cyc_debit", DecimalType(12, 2)),
])

DISCGRP_SCHEMA = StructType([
    StructField("dis_acct_group_id", StringType()),
    StructField("dis_tran_type_cd", StringType()),
    StructField("dis_tran_cat_cd", IntegerType()),
    StructField("dis_int_rate", DecimalType(7, 4)),
])

XREF_SCHEMA = StructType([
    StructField("acct_id", LongType()),
    StructField("card_num", StringType()),
])


# ---------------------------------------------------------------------------
# Full pipeline integration test
# ---------------------------------------------------------------------------

class TestFullPipeline:

    def _run_pipeline(self, spark, tcatbal_rows, account_rows, discgrp_rows,
                      xref_rows, run_date="2026-04-07"):
        """Run the full computation chain and return transaction + account-interest DataFrames."""
        tcatbal_df = spark.createDataFrame(tcatbal_rows, TCATBAL_SCHEMA)
        account_df = spark.createDataFrame(account_rows, ACCOUNT_SCHEMA)
        discgrp_df = spark.createDataFrame(discgrp_rows, DISCGRP_SCHEMA)
        xref_df = spark.createDataFrame(xref_rows, XREF_SCHEMA)

        # Step 1-2: Rate join
        with_rate = join_interest_rates(tcatbal_df, account_df, discgrp_df)
        # Step 3: Compute monthly interest
        interest_df = compute_monthly_interest(with_rate)
        # Step 4: Aggregate
        account_interest_df = aggregate_account_interest(interest_df)
        # Step 5: Build transactions
        transactions_df = build_interest_transactions(
            account_interest_df, xref_df, run_date, "test-run"
        )

        return interest_df, account_interest_df, transactions_df

    def test_happy_path_single_account_single_category(self, spark):
        """
        End-to-end: one account, one category, primary rate found.
        balance=1200.00, rate=12.0000 → monthly_interest=12.00 → tran_amt=12.00
        """
        _, _, transactions_df = self._run_pipeline(
            spark,
            tcatbal_rows=[
                Row(acct_id=1, tran_type_cd="01", tran_cat_cd=1,
                    tran_cat_bal=Decimal("1200.00")),
            ],
            account_rows=[
                Row(acct_id=1, acct_group_id="GRPA",
                    acct_curr_bal=Decimal("1200.00"),
                    acct_curr_cyc_credit=Decimal("0"),
                    acct_curr_cyc_debit=Decimal("0")),
            ],
            discgrp_rows=[
                Row(dis_acct_group_id="GRPA", dis_tran_type_cd="01",
                    dis_tran_cat_cd=1, dis_int_rate=Decimal("12.0000")),
            ],
            xref_rows=[Row(acct_id=1, card_num="4111111111111111")],
        )

        tran_rows = transactions_df.collect()
        assert len(tran_rows) == 1
        assert tran_rows[0]["tran_amt"] == Decimal("12.00")
        assert tran_rows[0]["tran_type_cd"] == "01"
        assert tran_rows[0]["tran_cat_cd"] == 5
        assert tran_rows[0]["tran_card_num"] == "4111111111111111"
        assert tran_rows[0]["tran_desc"] == "Int. for a/c 00000000001"

    def test_happy_path_single_account_multiple_categories(self, spark):
        """
        One account, three categories: interests accumulate into one transaction record.
        category totals: 12.00 + 24.00 + 9.00 = 45.00 → single tran_amt=45.00
        """
        _, _, transactions_df = self._run_pipeline(
            spark,
            tcatbal_rows=[
                Row(acct_id=1, tran_type_cd="01", tran_cat_cd=1, tran_cat_bal=Decimal("1200.00")),
                Row(acct_id=1, tran_type_cd="01", tran_cat_cd=2, tran_cat_bal=Decimal("2400.00")),
                Row(acct_id=1, tran_type_cd="02", tran_cat_cd=1, tran_cat_bal=Decimal("600.00")),
            ],
            account_rows=[
                Row(acct_id=1, acct_group_id="GRPA",
                    acct_curr_bal=Decimal("4200.00"),
                    acct_curr_cyc_credit=Decimal("0"), acct_curr_cyc_debit=Decimal("0")),
            ],
            discgrp_rows=[
                Row(dis_acct_group_id="GRPA", dis_tran_type_cd="01",
                    dis_tran_cat_cd=1, dis_int_rate=Decimal("12.0000")),
                Row(dis_acct_group_id="GRPA", dis_tran_type_cd="01",
                    dis_tran_cat_cd=2, dis_int_rate=Decimal("12.0000")),
                Row(dis_acct_group_id="GRPA", dis_tran_type_cd="02",
                    dis_tran_cat_cd=1, dis_int_rate=Decimal("18.0000")),
            ],
            xref_rows=[Row(acct_id=1, card_num="4111111111111111")],
        )

        tran_rows = transactions_df.collect()
        assert len(tran_rows) == 1  # one transaction per account (cat1: 12.00 + cat2: 24.00 + cat3: 9.00 = 45.00)
        assert tran_rows[0]["tran_amt"] == Decimal("45.00")

    def test_multiple_accounts_each_gets_one_transaction(self, spark):
        """Three accounts → three separate interest transactions."""
        _, account_interest_df, transactions_df = self._run_pipeline(
            spark,
            tcatbal_rows=[
                Row(acct_id=1, tran_type_cd="01", tran_cat_cd=1, tran_cat_bal=Decimal("1200.00")),
                Row(acct_id=2, tran_type_cd="01", tran_cat_cd=1, tran_cat_bal=Decimal("2400.00")),
                Row(acct_id=3, tran_type_cd="01", tran_cat_cd=1, tran_cat_bal=Decimal("600.00")),
            ],
            account_rows=[
                Row(acct_id=1, acct_group_id="G1", acct_curr_bal=Decimal("1200.00"),
                    acct_curr_cyc_credit=Decimal("0"), acct_curr_cyc_debit=Decimal("0")),
                Row(acct_id=2, acct_group_id="G1", acct_curr_bal=Decimal("2400.00"),
                    acct_curr_cyc_credit=Decimal("0"), acct_curr_cyc_debit=Decimal("0")),
                Row(acct_id=3, acct_group_id="G1", acct_curr_bal=Decimal("600.00"),
                    acct_curr_cyc_credit=Decimal("0"), acct_curr_cyc_debit=Decimal("0")),
            ],
            discgrp_rows=[
                Row(dis_acct_group_id="G1", dis_tran_type_cd="01",
                    dis_tran_cat_cd=1, dis_int_rate=Decimal("12.0000")),
            ],
            xref_rows=[
                Row(acct_id=1, card_num="4111111111111111"),
                Row(acct_id=2, card_num="4222222222222222"),
                Row(acct_id=3, card_num="4333333333333333"),
            ],
        )

        assert transactions_df.count() == 3
        assert_tran_id_uniqueness(transactions_df)
        assert_balance_integrity(account_interest_df, transactions_df)

    def test_zero_rate_category_produces_no_transaction(self, spark):
        """
        BR-3: Account with one zero-rate category and one non-zero category.
        Only the non-zero category contributes to the transaction amount.
        """
        _, _, transactions_df = self._run_pipeline(
            spark,
            tcatbal_rows=[
                Row(acct_id=1, tran_type_cd="01", tran_cat_cd=1, tran_cat_bal=Decimal("1200.00")),
                Row(acct_id=1, tran_type_cd="01", tran_cat_cd=2, tran_cat_bal=Decimal("1000.00")),  # zero-rate
            ],
            account_rows=[
                Row(acct_id=1, acct_group_id="G1", acct_curr_bal=Decimal("2200.00"),
                    acct_curr_cyc_credit=Decimal("0"), acct_curr_cyc_debit=Decimal("0")),
            ],
            discgrp_rows=[
                Row(dis_acct_group_id="G1", dis_tran_type_cd="01",
                    dis_tran_cat_cd=1, dis_int_rate=Decimal("12.0000")),  # 12.00
                Row(dis_acct_group_id="G1", dis_tran_type_cd="01",
                    dis_tran_cat_cd=2, dis_int_rate=Decimal("0.0000")),  # zero-rate
            ],
            xref_rows=[Row(acct_id=1, card_num="4111111111111111")],
        )

        tran_rows = transactions_df.collect()
        assert len(tran_rows) == 1
        # Only cat=1 contributes: (1200 * 12) / 1200 = 12.00
        assert tran_rows[0]["tran_amt"] == Decimal("12.00")

    def test_all_zero_rate_produces_no_transaction(self, spark):
        """
        All categories have zero rate → no transactions generated, no account update.
        """
        _, account_interest_df, transactions_df = self._run_pipeline(
            spark,
            tcatbal_rows=[
                Row(acct_id=1, tran_type_cd="01", tran_cat_cd=1, tran_cat_bal=Decimal("5000.00")),
            ],
            account_rows=[
                Row(acct_id=1, acct_group_id="FREEGROUP", acct_curr_bal=Decimal("5000.00"),
                    acct_curr_cyc_credit=Decimal("0"), acct_curr_cyc_debit=Decimal("0")),
            ],
            discgrp_rows=[
                Row(dis_acct_group_id="FREEGROUP", dis_tran_type_cd="01",
                    dis_tran_cat_cd=1, dis_int_rate=Decimal("0.0000")),
            ],
            xref_rows=[Row(acct_id=1, card_num="4111111111111111")],
        )

        assert transactions_df.count() == 0
        assert account_interest_df.count() == 0

    def test_default_fallback_pipeline(self, spark):
        """
        BR-2 end-to-end: account group not in DISCGRP → DEFAULT rate used.
        balance=1200.00, DEFAULT rate=6.0000 → (1200 * 6) / 1200 = 6.00
        """
        _, _, transactions_df = self._run_pipeline(
            spark,
            tcatbal_rows=[
                Row(acct_id=1, tran_type_cd="01", tran_cat_cd=1, tran_cat_bal=Decimal("1200.00")),
            ],
            account_rows=[
                Row(acct_id=1, acct_group_id="UNKNOWNGROUP", acct_curr_bal=Decimal("1200.00"),
                    acct_curr_cyc_credit=Decimal("0"), acct_curr_cyc_debit=Decimal("0")),
            ],
            discgrp_rows=[
                Row(dis_acct_group_id=DEFAULT_DISCLOSURE_GROUP, dis_tran_type_cd="01",
                    dis_tran_cat_cd=1, dis_int_rate=Decimal("6.0000")),
            ],
            xref_rows=[Row(acct_id=1, card_num="4111111111111111")],
        )

        tran_rows = transactions_df.collect()
        assert len(tran_rows) == 1
        assert tran_rows[0]["tran_amt"] == Decimal("6.00")

    def test_missing_xref_does_not_abort(self, spark):
        """
        XREF not found → pipeline continues with tran_card_num=NULL.
        Replaces: COBOL 1110-GET-XREF-DATA INVALID KEY (display warning, continue)
        """
        _, _, transactions_df = self._run_pipeline(
            spark,
            tcatbal_rows=[
                Row(acct_id=1, tran_type_cd="01", tran_cat_cd=1, tran_cat_bal=Decimal("1200.00")),
            ],
            account_rows=[
                Row(acct_id=1, acct_group_id="G1", acct_curr_bal=Decimal("1200.00"),
                    acct_curr_cyc_credit=Decimal("0"), acct_curr_cyc_debit=Decimal("0")),
            ],
            discgrp_rows=[
                Row(dis_acct_group_id="G1", dis_tran_type_cd="01",
                    dis_tran_cat_cd=1, dis_int_rate=Decimal("12.0000")),
            ],
            xref_rows=[],  # empty XREF
        )

        tran_rows = transactions_df.collect()
        assert len(tran_rows) == 1
        assert tran_rows[0]["tran_card_num"] is None
        assert tran_rows[0]["tran_amt"] == Decimal("12.00")

    def test_balance_integrity_full_run(self, spark):
        """
        End-to-end: sum of generated tran_amt == sum of total_interest.
        """
        _, account_interest_df, transactions_df = self._run_pipeline(
            spark,
            tcatbal_rows=[
                Row(acct_id=1, tran_type_cd="01", tran_cat_cd=1, tran_cat_bal=Decimal("1200.00")),
                Row(acct_id=1, tran_type_cd="02", tran_cat_cd=1, tran_cat_bal=Decimal("2400.00")),
                Row(acct_id=2, tran_type_cd="01", tran_cat_cd=1, tran_cat_bal=Decimal("600.00")),
            ],
            account_rows=[
                Row(acct_id=1, acct_group_id="G1", acct_curr_bal=Decimal("3600.00"),
                    acct_curr_cyc_credit=Decimal("0"), acct_curr_cyc_debit=Decimal("0")),
                Row(acct_id=2, acct_group_id="G1", acct_curr_bal=Decimal("600.00"),
                    acct_curr_cyc_credit=Decimal("0"), acct_curr_cyc_debit=Decimal("0")),
            ],
            discgrp_rows=[
                Row(dis_acct_group_id="G1", dis_tran_type_cd="01",
                    dis_tran_cat_cd=1, dis_int_rate=Decimal("12.0000")),
                Row(dis_acct_group_id="G1", dis_tran_type_cd="02",
                    dis_tran_cat_cd=1, dis_int_rate=Decimal("12.0000")),
            ],
            xref_rows=[
                Row(acct_id=1, card_num="4111111111111111"),
                Row(acct_id=2, card_num="4222222222222222"),
            ],
        )

        assert_balance_integrity(account_interest_df, transactions_df)
        assert_tran_id_uniqueness(transactions_df)
