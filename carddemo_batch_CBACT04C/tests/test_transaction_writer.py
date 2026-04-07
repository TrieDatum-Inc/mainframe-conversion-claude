"""
Unit tests for transaction_writer.py

Covers COBOL paragraph 1300-B-WRITE-TX:
  - TRAN-ID construction (run_date prefix + 6-digit suffix)
  - All hardcoded transaction field values
  - XREF join for TRAN-CARD-NUM (including missing XREF case)
  - TRAN-ID uniqueness assertion
  - DB2-format timestamp in TRAN-ORIG-TS / TRAN-PROC-TS
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
    ArrayType,
)

from src.transaction_writer import (
    assert_tran_id_uniqueness,
    build_interest_transactions,
)
from src.constants import (
    INTEREST_TRAN_CAT_CD,
    INTEREST_TRAN_DESC_PREFIX,
    INTEREST_TRAN_MERCHANT_ID,
    INTEREST_TRAN_SOURCE,
    INTEREST_TRAN_TYPE_CD,
    TRAN_ID_DATE_CHARS,
    TRAN_ID_SUFFIX_DIGITS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ACCOUNT_INTEREST_SCHEMA = StructType([
    StructField("acct_id", LongType()),
    StructField("acct_group_id", StringType()),
    StructField("total_interest", DecimalType(11, 2)),
    StructField("category_detail", ArrayType(
        StructType([
            StructField("tran_type_cd", StringType()),
            StructField("tran_cat_cd", IntegerType()),
            StructField("tran_cat_bal", DecimalType(11, 2)),
            StructField("effective_int_rate", DecimalType(7, 4)),
            StructField("rate_source", StringType()),
            StructField("monthly_interest", DecimalType(11, 2)),
        ])
    )),
])

XREF_SCHEMA = StructType([
    StructField("acct_id", LongType()),
    StructField("card_num", StringType()),
])


def make_account_interest(spark, rows):
    return spark.createDataFrame(rows, ACCOUNT_INTEREST_SCHEMA)


def make_xref(spark, rows):
    return spark.createDataFrame(rows, XREF_SCHEMA)


# ---------------------------------------------------------------------------
# TRAN-ID construction
# ---------------------------------------------------------------------------

class TestTranIdConstruction:
    """Tests for TRAN-ID = PARM-DATE (YYYYMMDD) + WS-TRANID-SUFFIX (6 digits)."""

    def test_tran_id_format(self, spark):
        """
        TRAN-ID must start with run_date without dashes (8 chars) followed by 6-digit suffix.
        Replaces: TRAN-ID = PARM-DATE + WS-TRANID-SUFFIX (paragraph 1300-B-WRITE-TX)
        """
        acct_df = make_account_interest(spark, [
            Row(acct_id=1, acct_group_id="G1", total_interest=Decimal("10.00"),
                category_detail=[]),
        ])
        xref_df = make_xref(spark, [
            Row(acct_id=1, card_num="4111111111111111"),
        ])

        result = build_interest_transactions(
            acct_df, xref_df, "2026-04-07", "run-001"
        ).collect()

        assert len(result) == 1
        tran_id = result[0]["tran_id"]
        assert tran_id.startswith("20260407"), (
            f"TRAN-ID '{tran_id}' should start with YYYYMMDD='20260407'"
        )
        assert len(tran_id) == TRAN_ID_DATE_CHARS + TRAN_ID_SUFFIX_DIGITS, (
            f"TRAN-ID length should be {TRAN_ID_DATE_CHARS + TRAN_ID_SUFFIX_DIGITS}"
        )

    def test_tran_id_unique_across_accounts(self, spark):
        """
        Multiple accounts must get unique TRAN-IDs.
        Replaces: ADD 1 TO WS-TRANID-SUFFIX before each WRITE.
        """
        acct_df = make_account_interest(spark, [
            Row(acct_id=1, acct_group_id="G1", total_interest=Decimal("10.00"), category_detail=[]),
            Row(acct_id=2, acct_group_id="G1", total_interest=Decimal("20.00"), category_detail=[]),
            Row(acct_id=3, acct_group_id="G2", total_interest=Decimal("5.00"), category_detail=[]),
        ])
        xref_df = make_xref(spark, [
            Row(acct_id=1, card_num="4111111111111111"),
            Row(acct_id=2, card_num="4222222222222222"),
            Row(acct_id=3, card_num="4333333333333333"),
        ])

        result = build_interest_transactions(acct_df, xref_df, "2026-04-07", "run-002")
        tran_ids = [r["tran_id"] for r in result.collect()]
        assert len(tran_ids) == len(set(tran_ids)), "All TRAN-IDs must be unique"

    def test_invalid_run_date_raises(self, spark):
        """run_date in wrong format must raise ValueError."""
        acct_df = make_account_interest(spark, [
            Row(acct_id=1, acct_group_id="G1", total_interest=Decimal("10.00"), category_detail=[]),
        ])
        xref_df = make_xref(spark, [Row(acct_id=1, card_num="4111111111111111")])

        with pytest.raises(ValueError):
            build_interest_transactions(acct_df, xref_df, "07-04-2026", "run-003")


# ---------------------------------------------------------------------------
# Hardcoded transaction field values
# ---------------------------------------------------------------------------

class TestTransactionFieldValues:
    """Tests that hardcoded COBOL 1300-B-WRITE-TX field values are preserved."""

    def _build(self, spark, acct_id=1, total_interest=Decimal("25.00"),
               run_date="2026-04-07", card_num="4111111111111111"):
        acct_df = make_account_interest(spark, [
            Row(acct_id=acct_id, acct_group_id="G1", total_interest=total_interest,
                category_detail=[]),
        ])
        xref_df = make_xref(spark, [Row(acct_id=acct_id, card_num=card_num)])
        return build_interest_transactions(acct_df, xref_df, run_date, "run-test").collect()[0]

    def test_tran_type_cd(self, spark):
        """TRAN-TYPE-CD must be '01'."""
        row = self._build(spark)
        assert row["tran_type_cd"] == INTEREST_TRAN_TYPE_CD == "01"

    def test_tran_cat_cd(self, spark):
        """TRAN-CAT-CD must be 5 (integer)."""
        row = self._build(spark)
        assert row["tran_cat_cd"] == INTEREST_TRAN_CAT_CD == 5

    def test_tran_source(self, spark):
        """TRAN-SOURCE must be 'System'."""
        row = self._build(spark)
        assert row["tran_source"] == INTEREST_TRAN_SOURCE == "System"

    def test_tran_merchant_id_zero(self, spark):
        """TRAN-MERCHANT-ID must be 0."""
        row = self._build(spark)
        assert row["tran_merchant_id"] == INTEREST_TRAN_MERCHANT_ID == 0

    def test_tran_merchant_fields_empty(self, spark):
        """TRAN-MERCHANT-NAME, CITY, ZIP must be empty strings (COBOL SPACES)."""
        row = self._build(spark)
        assert row["tran_merchant_name"] == ""
        assert row["tran_merchant_city"] == ""
        assert row["tran_merchant_zip"] == ""

    def test_tran_desc_format(self, spark):
        """
        TRAN-DESC = 'Int. for a/c ' + zero-padded 11-digit account ID.
        Example: acct_id=12345 → 'Int. for a/c 00000012345'
        """
        row = self._build(spark, acct_id=12345)
        expected_desc = f"{INTEREST_TRAN_DESC_PREFIX}{'12345'.zfill(11)}"
        assert row["tran_desc"] == expected_desc

    def test_tran_amt_equals_total_interest(self, spark):
        """TRAN-AMT = WS-TOTAL-INT (account-level sum)."""
        row = self._build(spark, total_interest=Decimal("99.99"))
        assert row["tran_amt"] == Decimal("99.99")

    def test_tran_card_num_from_xref(self, spark):
        """TRAN-CARD-NUM = card_num from XREF lookup."""
        row = self._build(spark, card_num="5555555555554444")
        assert row["tran_card_num"] == "5555555555554444"

    def test_tran_card_num_null_when_xref_missing(self, spark):
        """
        TRAN-CARD-NUM = NULL when XREF not found.
        Replaces: COBOL INVALID KEY on 1110-GET-XREF-DATA — continue with spaces.
        """
        acct_df = make_account_interest(spark, [
            Row(acct_id=9999, acct_group_id="G1", total_interest=Decimal("10.00"),
                category_detail=[]),
        ])
        xref_df = make_xref(spark, [])  # empty XREF
        result = build_interest_transactions(acct_df, xref_df, "2026-04-07", "run-x").collect()
        assert result[0]["tran_card_num"] is None

    def test_tran_orig_ts_db2_format(self, spark):
        """
        TRAN-ORIG-TS and TRAN-PROC-TS must be 26-char DB2-format strings.
        Format: YYYY-MM-DD-HH.MM.SS.mmm0000
        Replaces: PERFORM Z-GET-DB2-FORMAT-TIMESTAMP
        """
        row = self._build(spark)
        orig_ts = row["tran_orig_ts"]
        proc_ts = row["tran_proc_ts"]

        assert orig_ts == proc_ts, "TRAN-ORIG-TS and TRAN-PROC-TS must be identical"
        assert len(orig_ts) == 26, f"DB2 timestamp must be 26 chars, got {len(orig_ts)}"
        # Pattern: YYYY-MM-DD-HH.MM.SS.mmm0000
        import re
        pattern = r"^\d{4}-\d{2}-\d{2}-\d{2}\.\d{2}\.\d{2}\.\d{7}$"
        assert re.match(pattern, orig_ts), (
            f"TRAN-ORIG-TS '{orig_ts}' does not match DB2 format YYYY-MM-DD-HH.MM.SS.mmm0000"
        )


# ---------------------------------------------------------------------------
# TRAN-ID uniqueness assertion
# ---------------------------------------------------------------------------

class TestAssertTranIdUniqueness:
    """Tests for the post-write data quality check."""

    def test_unique_ids_pass(self, spark):
        """No duplicates → assertion passes silently."""
        schema = StructType([StructField("tran_id", StringType())])
        df = spark.createDataFrame([
            Row(tran_id="202604070000001"),
            Row(tran_id="202604070000002"),
            Row(tran_id="202604070000003"),
        ], schema)
        assert_tran_id_uniqueness(df)  # should not raise

    def test_duplicate_ids_raise(self, spark):
        """Duplicate TRAN-ID → AssertionError raised."""
        schema = StructType([StructField("tran_id", StringType())])
        df = spark.createDataFrame([
            Row(tran_id="202604070000001"),
            Row(tran_id="202604070000001"),  # duplicate
        ], schema)
        with pytest.raises(AssertionError, match="TRAN-ID uniqueness violated"):
            assert_tran_id_uniqueness(df)
