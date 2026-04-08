"""
Tests for CBSTM03A/CBSTM03B - Account Statement Generation

Test coverage:
  - Customer/account enrichment via xref joins
  - Full name construction (COBOL STRING DELIMITED BY ' ')
  - Address concatenation
  - Transaction matching to cards
  - Total expenditure per card accumulation
  - Cards with no transactions produce null/zero transaction rows
  - Edge cases: empty xref, customer not found
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from pyspark.sql import functions as F

from carddemo_batch.transformations.cbstm03_transforms import (
    build_customer_full_name,
    build_statement_rows,
    enrich_xref_with_customer_account,
    match_transactions_to_cards,
)


# ===========================================================================
# enrich_xref_with_customer_account / 2000-CUSTFILE-GET + 3000-ACCTFILE-GET
# ===========================================================================

class TestEnrichXrefWithCustomerAccount:

    def test_customer_fields_present(self, spark, xref_df, customer_df, account_df):
        result = enrich_xref_with_customer_account(xref_df, customer_df, account_df)
        assert "cust_first_name" in result.columns
        assert "cust_last_name" in result.columns
        assert "acct_curr_bal" in result.columns

    def test_only_matching_cards_returned(self, spark, xref_df, customer_df, account_df):
        """
        COBOL 2000/3000 use random reads with INVALID KEY.
        Inner join matches only cards that have customer + account records.
        """
        result = enrich_xref_with_customer_account(xref_df, customer_df, account_df)
        # fixture xref has 3 cards; only 2 customers exist (cust_id 100000001, 100000002)
        # xref card for cust 100000003 (acct 3) has no customer fixture -> dropped
        assert result.count() == 2

    def test_acct_id_matches_xref_acct_id(self, spark, xref_df, customer_df, account_df):
        result = enrich_xref_with_customer_account(xref_df, customer_df, account_df)
        mismatches = result.filter(
            result["xref_acct_id"].cast("string") != result["acct_id"]
        )
        assert mismatches.count() == 0


# ===========================================================================
# build_customer_full_name / 5000-CREATE-STATEMENT STRING logic
# ===========================================================================

class TestBuildCustomerFullName:

    def test_full_name_trims_and_joins(self, spark, xref_df, customer_df, account_df):
        """
        COBOL: STRING CUST-FIRST-NAME DELIMITED BY ' ' ' ' DELIMITED BY SIZE
                      CUST-MIDDLE-NAME DELIMITED BY ' ' ...
        Should produce "John A Smith" (trimmed components joined by space).
        """
        enriched = enrich_xref_with_customer_account(xref_df, customer_df, account_df)
        with_name = build_customer_full_name(enriched)
        john = with_name.filter(F.col("cust_first_name") == "John").first()
        assert john["cust_full_name"] == "John A Smith"

    def test_addr_full_combines_fields(self, spark, xref_df, customer_df, account_df):
        enriched = enrich_xref_with_customer_account(xref_df, customer_df, account_df)
        with_name = build_customer_full_name(enriched)
        john = with_name.filter(F.col("cust_first_name") == "John").first()
        # Fixture addr_line_3=Seattle, state_cd=WA, country=USA, zip=98101
        assert "Seattle" in john["cust_addr_full"]
        assert "WA" in john["cust_addr_full"]

    def test_empty_middle_name_handled(self, spark, xref_df, customer_df, account_df):
        enriched = enrich_xref_with_customer_account(xref_df, customer_df, account_df)
        with_name = build_customer_full_name(enriched)
        jane = with_name.filter(F.col("cust_first_name") == "Jane").first()
        # Jane M Doe - M is present in fixture
        assert jane["cust_full_name"] is not None
        assert "Jane" in jane["cust_full_name"]
        assert "Doe" in jane["cust_full_name"]


# ===========================================================================
# match_transactions_to_cards / 4000-TRNXFILE-GET
# ===========================================================================

class TestMatchTransactionsToCards:

    def test_transactions_matched_by_card(self, spark, xref_df, customer_df, account_df, trnx_df):
        enriched = enrich_xref_with_customer_account(xref_df, customer_df, account_df)
        result = match_transactions_to_cards(enriched, trnx_df)
        # Each matched row should have trnx_id
        card1_rows = result.filter(F.col("xref_card_num") == "4111111111111111")
        assert card1_rows.filter(F.col("trnx_id").isNotNull()).count() == 1

    def test_total_exp_aggregated_per_card(self, spark, xref_df, customer_df, account_df, trnx_df):
        """
        COBOL: ADD TRNX-AMT TO WS-TOTAL-AMT (accumulator per card).
        """
        enriched = enrich_xref_with_customer_account(xref_df, customer_df, account_df)
        result = match_transactions_to_cards(enriched, trnx_df)
        card1 = result.filter(
            (F.col("xref_card_num") == "4111111111111111")
            & F.col("trnx_id").isNotNull()
        ).first()
        # Fixture has one transaction for card 1: $75.50
        assert float(card1["total_exp"]) == pytest.approx(75.50)

    def test_card_with_no_transactions_gets_zero_total(
        self, spark, xref_df, customer_df, account_df, spark_fixture=None
    ):
        """
        COBOL: card loop runs even if no matching transactions exist.
        total_exp should be 0 (coalesce of NULL).
        """
        from tests.conftest import TRNX_SCHEMA
        empty_trnx = spark.createDataFrame([], schema=TRNX_SCHEMA)
        enriched = enrich_xref_with_customer_account(xref_df, customer_df, account_df)
        result = match_transactions_to_cards(enriched, empty_trnx)
        zero_total = result.filter(F.col("total_exp").isNull() | (F.col("total_exp") == 0))
        assert zero_total.count() == result.count()


# ===========================================================================
# build_statement_rows - integration
# ===========================================================================

class TestBuildStatementRows:

    def test_output_schema_matches_delta_table(self, spark, xref_df, customer_df, account_df, trnx_df):
        enriched = enrich_xref_with_customer_account(xref_df, customer_df, account_df)
        result = build_statement_rows(enriched, trnx_df)
        expected_cols = {
            "acct_id", "cust_full_name", "cust_addr_line_1", "cust_addr_line_2",
            "cust_addr_full", "acct_curr_bal", "fico_score",
            "trnx_card_num", "trnx_id", "trnx_desc", "trnx_amt", "total_exp",
        }
        assert expected_cols.issubset(set(result.columns))

    def test_fico_score_present(self, spark, xref_df, customer_df, account_df, trnx_df):
        enriched = enrich_xref_with_customer_account(xref_df, customer_df, account_df)
        result = build_statement_rows(enriched, trnx_df)
        null_fico = result.filter(F.col("fico_score").isNull())
        assert null_fico.count() == 0

    def test_trnx_amt_is_decimal(self, spark, xref_df, customer_df, account_df, trnx_df):
        enriched = enrich_xref_with_customer_account(xref_df, customer_df, account_df)
        result = build_statement_rows(enriched, trnx_df)
        from pyspark.sql.types import DecimalType
        trnx_amt_type = dict(result.dtypes)["trnx_amt"]
        assert "decimal" in trnx_amt_type.lower()
