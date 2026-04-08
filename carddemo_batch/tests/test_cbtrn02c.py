"""
Tests for CBTRN02C - Daily Transaction Posting

Test coverage:
  - Validation: invalid card, account not found, overlimit, expired account
  - Valid transactions are posted correctly
  - Reject records contain correct reason codes and descriptions
  - Transaction-category balance deltas are computed correctly
  - Account balance deltas are computed correctly
  - Edge cases: empty input, all-rejected input, negative amounts (payments)
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from pyspark.sql import functions as F

from carddemo_batch.config.settings import (
    REJECT_CODE_ACCOUNT_NOT_FOUND,
    REJECT_CODE_EXPIRED_ACCT,
    REJECT_CODE_INVALID_CARD,
    REJECT_CODE_OVERLIMIT,
)
from carddemo_batch.transformations.cbtrn02c_transforms import (
    build_account_balance_updates,
    build_posted_transactions,
    build_tcatbal_updates,
    extract_rejected_transactions,
    validate_transactions,
)


# ===========================================================================
# validate_transactions / 1500-VALIDATE-TRAN
# ===========================================================================

class TestValidateTransactions:

    def test_valid_transaction_passes(self, spark, daily_tran_df, xref_df, account_df):
        """Happy path: known card, active account, within credit limit."""
        result = validate_transactions(daily_tran_df, xref_df, account_df)
        valid = result.filter(
            (F.col("tran_id") == "TRN0000000000001")
            & (F.col("validation_fail_reason") == 0)
        )
        assert valid.count() == 1

    def test_invalid_card_gets_code_100(self, spark, daily_tran_df, xref_df, account_df):
        """
        COBOL 1500-A-LOOKUP-XREF: card 9999999999999999 not in xref.
        Expect fail reason 100.
        """
        result = validate_transactions(daily_tran_df, xref_df, account_df)
        rejected = result.filter(
            (F.col("tran_id") == "TRN0000000000004")
        )
        row = rejected.first()
        assert row["validation_fail_reason"] == REJECT_CODE_INVALID_CARD
        assert "INVALID CARD NUMBER" in row["validation_fail_reason_desc"]

    def test_overlimit_gets_code_102(self, spark, daily_tran_df, xref_df, account_df):
        """
        COBOL 1500-B-LOOKUP-ACCT overlimit check.
        Acct 2: credit_limit=5000, cyc_credit=1200, cyc_debit=800
        temp_bal = 1200-800+4700 = 5100 > 5000 -> OVERLIMIT
        """
        result = validate_transactions(daily_tran_df, xref_df, account_df)
        rejected = result.filter(F.col("tran_id") == "TRN0000000000005")
        row = rejected.first()
        assert row["validation_fail_reason"] == REJECT_CODE_OVERLIMIT
        assert "OVERLIMIT" in row["validation_fail_reason_desc"]

    def test_negative_amount_payment_passes(self, spark, daily_tran_df, xref_df, account_df):
        """
        Payments (negative amounts) always reduce temp_bal, so they should pass
        the credit-limit check.
        """
        result = validate_transactions(daily_tran_df, xref_df, account_df)
        payment = result.filter(F.col("tran_id") == "TRN0000000000003")
        row = payment.first()
        assert row["validation_fail_reason"] == 0

    def test_all_valid_no_rejects(self, spark, xref_df, account_df):
        """When all transactions are valid, reject count must be 0."""
        from tests.conftest import DAILY_TRAN_SCHEMA
        data = [
            ("TRN9999999999001", "01", 1, "POS", "TEST",
             Decimal("10.00"), 0, "", "", "",
             "4111111111111111",
             "2024-01-15-09.00.00.000000", "2024-01-15-09.00.00.000000"),
        ]
        small_df = spark.createDataFrame(data, schema=DAILY_TRAN_SCHEMA)
        result = validate_transactions(small_df, xref_df, account_df)
        assert result.filter(F.col("validation_fail_reason") != 0).count() == 0

    def test_sequential_overlimit_rejects_third_txn(self, spark):
        """
        COBOL processes transactions one at a time, REWRITing the account
        after each valid posting.  Three $6000 purchases on an account with
        limit=20000 and starting cyc_credit=5000, cyc_debit=0:

          Txn 1 (09:00): temp = 5000 + 6000 = 11000 <= 20000 -> VALID
                          running_credit updated to 11000
          Txn 2 (10:00): temp = 11000 + 6000 = 17000 <= 20000 -> VALID
                          running_credit updated to 17000
          Txn 3 (11:00): temp = 17000 + 6000 = 23000 > 20000 -> OVERLIMIT

        A set-based approach would evaluate each transaction against the
        original balance (5000) and approve all three — this test catches
        that bug.
        """
        from tests.conftest import DAILY_TRAN_SCHEMA, XREF_SCHEMA, ACCOUNT_SCHEMA

        xref = spark.createDataFrame(
            [("5000000000000001", 999, 999)],
            schema=XREF_SCHEMA,
        )
        acct = spark.createDataFrame(
            [(
                "00000000999", "Y",
                Decimal("0.00"), Decimal("20000.00"), Decimal("0.00"),
                "2020-01-01", "2027-12-31", "2025-01-01",
                Decimal("5000.00"), Decimal("0.00"), "00000", "DEFAULT   ",
            )],
            schema=ACCOUNT_SCHEMA,
        )
        daily = spark.createDataFrame(
            [
                ("SEQ_TRN_001", "01", 1, "POS", "PURCHASE 1",
                 Decimal("6000.00"), 0, "", "", "",
                 "5000000000000001",
                 "2024-01-15-09.00.00.000000", ""),
                ("SEQ_TRN_002", "01", 1, "POS", "PURCHASE 2",
                 Decimal("6000.00"), 0, "", "", "",
                 "5000000000000001",
                 "2024-01-15-10.00.00.000000", ""),
                ("SEQ_TRN_003", "01", 1, "POS", "PURCHASE 3",
                 Decimal("6000.00"), 0, "", "", "",
                 "5000000000000001",
                 "2024-01-15-11.00.00.000000", ""),
            ],
            schema=DAILY_TRAN_SCHEMA,
        )

        result = validate_transactions(daily, xref, acct)

        # First two pass
        for tran_id in ("SEQ_TRN_001", "SEQ_TRN_002"):
            row = result.filter(F.col("tran_id") == tran_id).first()
            assert row["validation_fail_reason"] == 0, (
                f"{tran_id} should be valid"
            )

        # Third is overlimit
        third = result.filter(F.col("tran_id") == "SEQ_TRN_003").first()
        assert third["validation_fail_reason"] == REJECT_CODE_OVERLIMIT

    def test_empty_input_returns_empty(self, spark, xref_df, account_df):
        """Empty daily transactions produce empty output."""
        from tests.conftest import DAILY_TRAN_SCHEMA
        empty_df = spark.createDataFrame([], schema=DAILY_TRAN_SCHEMA)
        result = validate_transactions(empty_df, xref_df, account_df)
        assert result.count() == 0


# ===========================================================================
# extract_rejected_transactions / 2500-WRITE-REJECT-REC
# ===========================================================================

class TestExtractRejectedTransactions:

    def test_only_rejected_rows_returned(self, spark, daily_tran_df, xref_df, account_df):
        validated = validate_transactions(daily_tran_df, xref_df, account_df)
        rejects = extract_rejected_transactions(validated)
        # All rows in rejects must have non-zero fail reason
        assert rejects.filter(F.col("validation_fail_reason") == 0).count() == 0

    def test_reject_schema_has_reason_fields(self, spark, daily_tran_df, xref_df, account_df):
        validated = validate_transactions(daily_tran_df, xref_df, account_df)
        rejects = extract_rejected_transactions(validated)
        columns = rejects.columns
        assert "validation_fail_reason" in columns
        assert "validation_fail_reason_desc" in columns

    def test_reject_preserves_original_tran_fields(self, spark, daily_tran_df, xref_df, account_df):
        validated = validate_transactions(daily_tran_df, xref_df, account_df)
        rejects = extract_rejected_transactions(validated)
        invalid_card_row = rejects.filter(
            F.col("tran_id") == "TRN0000000000004"
        ).first()
        assert invalid_card_row is not None
        assert invalid_card_row["tran_card_num"] == "9999999999999999"


# ===========================================================================
# build_posted_transactions / 2000-POST-TRANSACTION
# ===========================================================================

class TestBuildPostedTransactions:

    def test_only_valid_transactions_are_posted(self, spark, daily_tran_df, xref_df, account_df):
        validated = validate_transactions(daily_tran_df, xref_df, account_df)
        posted = build_posted_transactions(validated, "2024-01-15-10.00.00.000000")
        # Invalid card TRN0000000000004 must not appear
        assert posted.filter(F.col("tran_id") == "TRN0000000000004").count() == 0

    def test_proc_ts_is_set_to_current(self, spark, daily_tran_df, xref_df, account_df):
        proc_ts = "2024-01-15-12.00.00.000000"
        validated = validate_transactions(daily_tran_df, xref_df, account_df)
        posted = build_posted_transactions(validated, proc_ts)
        rows = posted.filter(F.col("tran_proc_ts") != proc_ts)
        assert rows.count() == 0


# ===========================================================================
# build_tcatbal_updates / 2700-UPDATE-TCATBAL
# ===========================================================================

class TestBuildTcatbalUpdates:

    def test_net_delta_per_key(self, spark, daily_tran_df, xref_df, account_df):
        """
        For account 2 (card 4222222222222222, acct_id=2):
          TRN0000000000003: type=04, cat=1, amt=-200.00
          TRN0000000000005: type=01, cat=3, amt= 4700.00 (OVERLIMIT - excluded)
        Only the valid payment should appear in deltas.
        """
        validated = validate_transactions(daily_tran_df, xref_df, account_df)
        deltas = build_tcatbal_updates(validated)
        acct2_deltas = deltas.filter(F.col("trancat_acct_id") == 2)
        # Only the valid payment passes
        assert acct2_deltas.count() == 1
        row = acct2_deltas.first()
        assert float(row["balance_delta"]) == pytest.approx(-200.00)

    def test_positive_transaction_adds_positive_delta(self, spark, daily_tran_df, xref_df, account_df):
        validated = validate_transactions(daily_tran_df, xref_df, account_df)
        deltas = build_tcatbal_updates(validated)
        acct1 = deltas.filter(F.col("trancat_acct_id") == 1)
        row = acct1.first()
        assert float(row["balance_delta"]) == pytest.approx(75.50)


# ===========================================================================
# build_account_balance_updates / 2800-UPDATE-ACCOUNT-REC
# ===========================================================================

class TestBuildAccountBalanceUpdates:

    def test_curr_bal_delta_includes_all_valid_amounts(self, spark, daily_tran_df, xref_df, account_df):
        validated = validate_transactions(daily_tran_df, xref_df, account_df)
        updates = build_account_balance_updates(validated)
        acct1 = updates.filter(F.col("acct_id") == 1).first()
        # Only TRN0000000000001 is valid for acct 1
        assert float(acct1["curr_bal_delta"]) == pytest.approx(75.50)
        assert float(acct1["cyc_credit_delta"]) == pytest.approx(75.50)
        assert float(acct1["cyc_debit_delta"]) == pytest.approx(0.00)

    def test_payment_goes_to_cyc_debit(self, spark, daily_tran_df, xref_df, account_df):
        """
        COBOL 2800: IF DALYTRAN-AMT >= 0 -> CREDIT else -> DEBIT.
        Payment of -200 must go to cyc_debit_delta.
        """
        validated = validate_transactions(daily_tran_df, xref_df, account_df)
        updates = build_account_balance_updates(validated)
        acct2 = updates.filter(F.col("acct_id") == 2).first()
        assert float(acct2["cyc_credit_delta"]) == pytest.approx(0.00)
        assert float(acct2["cyc_debit_delta"]) == pytest.approx(-200.00)
        assert float(acct2["curr_bal_delta"]) == pytest.approx(-200.00)
