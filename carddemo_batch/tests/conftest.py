"""
Shared pytest fixtures for CardDemo batch pipeline tests.

Provides:
  - spark: SparkSession fixture (session-scoped for performance)
  - Sample DataFrames matching each Delta table schema
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    DecimalType,
    IntegerType,
    LongType,
    StringType,
    StructField,
    StructType,
)


# ---------------------------------------------------------------------------
# SparkSession
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def spark() -> SparkSession:
    """Session-scoped SparkSession for all tests."""
    session = (
        SparkSession.builder
        .master("local[2]")
        .appName("carddemo_batch_tests")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
        .getOrCreate()
    )
    session.sparkContext.setLogLevel("ERROR")
    return session


# ---------------------------------------------------------------------------
# Schema definitions (mirrors copybook layouts exactly)
# ---------------------------------------------------------------------------

DAILY_TRAN_SCHEMA = StructType([
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

ACCOUNT_SCHEMA = StructType([
    StructField("acct_id", StringType(), False),
    StructField("acct_active_status", StringType(), False),
    StructField("acct_curr_bal", DecimalType(12, 2), False),
    StructField("acct_credit_limit", DecimalType(12, 2), False),
    StructField("acct_cash_credit_limit", DecimalType(12, 2), False),
    StructField("acct_open_date", StringType(), False),
    StructField("acct_expiration_date", StringType(), False),
    StructField("acct_reissue_date", StringType(), False),
    StructField("acct_curr_cyc_credit", DecimalType(12, 2), False),
    StructField("acct_curr_cyc_debit", DecimalType(12, 2), False),
    StructField("acct_addr_zip", StringType(), False),
    StructField("acct_group_id", StringType(), False),
])

XREF_SCHEMA = StructType([
    StructField("xref_card_num", StringType(), False),
    StructField("xref_cust_id", LongType(), False),
    StructField("xref_acct_id", LongType(), False),
])

TCATBAL_SCHEMA = StructType([
    StructField("trancat_acct_id", LongType(), False),
    StructField("trancat_type_cd", StringType(), False),
    StructField("trancat_cd", IntegerType(), False),
    StructField("tran_cat_bal", DecimalType(11, 2), False),
])

DISCGRP_SCHEMA = StructType([
    StructField("dis_acct_group_id", StringType(), False),
    StructField("dis_tran_type_cd", StringType(), False),
    StructField("dis_tran_cat_cd", IntegerType(), False),
    StructField("dis_int_rate", DecimalType(6, 2), False),
])

TRAN_TYPE_SCHEMA = StructType([
    StructField("tran_type", StringType(), False),
    StructField("tran_type_desc", StringType(), False),
])

TRAN_CAT_SCHEMA = StructType([
    StructField("tran_type_cd", StringType(), False),
    StructField("tran_cat_cd", IntegerType(), False),
    StructField("tran_cat_type_desc", StringType(), False),
])

CUSTOMER_SCHEMA = StructType([
    StructField("cust_id", LongType(), False),
    StructField("cust_first_name", StringType(), False),
    StructField("cust_middle_name", StringType(), False),
    StructField("cust_last_name", StringType(), False),
    StructField("cust_addr_line_1", StringType(), False),
    StructField("cust_addr_line_2", StringType(), False),
    StructField("cust_addr_line_3", StringType(), False),
    StructField("cust_addr_state_cd", StringType(), False),
    StructField("cust_addr_country_cd", StringType(), False),
    StructField("cust_addr_zip", StringType(), False),
    StructField("cust_phone_num_1", StringType(), False),
    StructField("cust_phone_num_2", StringType(), False),
    StructField("cust_ssn", LongType(), False),
    StructField("cust_govt_issued_id", StringType(), False),
    StructField("cust_dob_yyyymmdd", StringType(), False),
    StructField("cust_eft_account_id", StringType(), False),
    StructField("cust_pri_card_holder", StringType(), False),
    StructField("cust_fico_credit_score", IntegerType(), False),
])

TRNX_SCHEMA = StructType([
    StructField("trnx_card_num", StringType(), False),
    StructField("trnx_id", StringType(), False),
    StructField("trnx_type_cd", StringType(), False),
    StructField("trnx_cat_cd", IntegerType(), False),
    StructField("trnx_source", StringType(), False),
    StructField("trnx_desc", StringType(), False),
    StructField("trnx_amt", DecimalType(11, 2), False),
    StructField("trnx_merchant_id", LongType(), False),
    StructField("trnx_merchant_name", StringType(), False),
    StructField("trnx_merchant_city", StringType(), False),
    StructField("trnx_merchant_zip", StringType(), False),
    StructField("trnx_orig_ts", StringType(), False),
    StructField("trnx_proc_ts", StringType(), False),
])


# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def xref_df(spark):
    data = [
        ("4111111111111111", 100000001, 1),
        ("4222222222222222", 100000002, 2),
        ("4333333333333333", 100000003, 3),
    ]
    return spark.createDataFrame(data, schema=XREF_SCHEMA)


@pytest.fixture
def account_df(spark):
    data = [
        # acct_id, status, curr_bal, credit_limit, cash_limit,
        # open_date, exp_date, reissue, cyc_credit, cyc_debit, zip, group_id
        ("00000000001", "Y",
         Decimal("1500.00"), Decimal("10000.00"), Decimal("2000.00"),
         "2020-01-15", "2026-01-15", "2024-01-15",
         Decimal("2000.00"), Decimal("500.00"), "98101", "GOLD      "),
        ("00000000002", "Y",
         Decimal("3200.50"), Decimal("5000.00"), Decimal("1000.00"),
         "2019-06-01", "2025-06-01", "2023-06-01",
         Decimal("1200.00"), Decimal("800.00"), "97201", "DEFAULT   "),
        ("00000000003", "Y",
         Decimal("250.00"), Decimal("20000.00"), Decimal("5000.00"),
         "2015-03-20", "2027-03-20", "2025-03-20",
         Decimal("5000.00"), Decimal("0.00"), "94102", "PLATINUM  "),
        # Expired account
        ("00000000004", "Y",
         Decimal("0.00"), Decimal("2000.00"), Decimal("500.00"),
         "2018-01-01", "2022-12-31", "2022-12-31",
         Decimal("0.00"), Decimal("0.00"), "10001", "DEFAULT   "),
    ]
    return spark.createDataFrame(data, schema=ACCOUNT_SCHEMA)


@pytest.fixture
def daily_tran_df(spark):
    data = [
        # Valid purchase
        ("TRN0000000000001", "01", 1, "POS       ", "WHOLE FOODS MARKET",
         Decimal("75.50"), 100000001, "Whole Foods", "Seattle", "98101",
         "4111111111111111",
         "2024-01-15-10.30.00.000000", "2024-01-15-10.30.00.000000"),
        # Valid payment (negative amount)
        ("TRN0000000000003", "04", 1, "ONLINE    ", "PAYMENT",
         Decimal("-200.00"), 0, "", "", "",
         "4222222222222222",
         "2024-01-15-12.00.00.000000", "2024-01-15-12.00.00.000000"),
        # Invalid card (no xref)
        ("TRN0000000000004", "01", 1, "POS       ", "UNKNOWN",
         Decimal("50.00"), 0, "", "", "",
         "9999999999999999",
         "2024-01-15-13.00.00.000000", "2024-01-15-13.00.00.000000"),
        # Overlimit (acct 2: credit_limit=5000, cyc_credit=1200, cyc_debit=800)
        # temp_bal = 1200-800+4500 = 4900 < 5000 -- not actually overlimit
        # Use amount that pushes over: need temp_bal > 5000 -> 1200-800+X > 5000 -> X > 4600
        ("TRN0000000000005", "01", 3, "POS       ", "BIG PURCHASE",
         Decimal("4700.00"), 0, "", "", "",
         "4222222222222222",
         "2024-01-15-14.00.00.000000", "2024-01-15-14.00.00.000000"),
    ]
    return spark.createDataFrame(data, schema=DAILY_TRAN_SCHEMA)


@pytest.fixture
def tcatbal_df(spark):
    data = [
        (1, "01", 1, Decimal("850.00")),
        (1, "01", 2, Decimal("320.00")),
        (2, "01", 1, Decimal("2000.00")),
        (2, "02", 1, Decimal("500.00")),
    ]
    return spark.createDataFrame(data, schema=TCATBAL_SCHEMA)


@pytest.fixture
def discgrp_df(spark):
    data = [
        ("DEFAULT   ", "01", 1, Decimal("18.00")),
        ("DEFAULT   ", "01", 2, Decimal("21.00")),
        ("DEFAULT   ", "02", 1, Decimal("24.00")),
        ("GOLD      ", "01", 1, Decimal("14.99")),
        ("GOLD      ", "01", 2, Decimal("18.00")),
        ("PLATINUM  ", "01", 1, Decimal("12.99")),
    ]
    return spark.createDataFrame(data, schema=DISCGRP_SCHEMA)


@pytest.fixture
def tran_type_df(spark):
    data = [
        ("01", "Purchase"),
        ("02", "Cash Advance"),
        ("04", "Payment"),
    ]
    return spark.createDataFrame(data, schema=TRAN_TYPE_SCHEMA)


@pytest.fixture
def tran_cat_df(spark):
    data = [
        ("01", 1, "Groceries"),
        ("01", 2, "Gas"),
        ("01", 3, "Restaurants"),
        ("04", 1, "Regular Payment"),
    ]
    return spark.createDataFrame(data, schema=TRAN_CAT_SCHEMA)


@pytest.fixture
def customer_df(spark):
    data = [
        (100000001, "John", "A", "Smith",
         "123 Main St", "Apt 4B", "Seattle",
         "WA", "USA", "98101",
         "206-555-1234", "", 123456789, "DL-WA-1234",
         "1975-06-15", "CHK-001", "Y", 750),
        (100000002, "Jane", "M", "Doe",
         "456 Oak Ave", "", "Portland",
         "OR", "USA", "97201",
         "503-555-9876", "", 987654321, "DL-OR-8765",
         "1982-11-23", "SAV-002", "Y", 690),
    ]
    return spark.createDataFrame(data, schema=CUSTOMER_SCHEMA)


@pytest.fixture
def trnx_df(spark):
    data = [
        ("4111111111111111", "TRN0000000000001", "01", 1, "POS",
         "WHOLE FOODS", Decimal("75.50"), 100000001, "Whole Foods", "Seattle", "98101",
         "2024-01-15-10.30.00.000000", "2024-01-15-10.30.00.000000"),
        ("4222222222222222", "TRN0000000000002", "01", 2, "POS",
         "SHELL STATION", Decimal("45.00"), 100000002, "Shell", "Portland", "97201",
         "2024-01-15-11.00.00.000000", "2024-01-15-11.00.00.000000"),
    ]
    return spark.createDataFrame(data, schema=TRNX_SCHEMA)
