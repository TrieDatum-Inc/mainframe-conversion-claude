"""
Tests for common validators and error handlers.
"""

from __future__ import annotations

import pytest
from pyspark.sql.types import StringType, StructField, StructType

from carddemo_batch.validators.common import (
    PipelineAbendError,
    assert_table_not_empty,
    validate_date_format,
    validate_no_duplicate_tran_ids,
)


class TestPipelineAbendError:

    def test_message_includes_program_name(self):
        err = PipelineAbendError("CBTRN02C", "test error")
        assert "CBTRN02C" in str(err)

    def test_default_error_code_is_999(self):
        err = PipelineAbendError("TEST", "msg")
        assert err.cobol_error_code == "999"

    def test_custom_error_code(self):
        err = PipelineAbendError("TEST", "msg", cobol_error_code="12")
        assert err.cobol_error_code == "12"


class TestAssertTableNotEmpty:

    def test_raises_on_empty_df(self, spark):
        schema = StructType([StructField("id", StringType())])
        empty_df = spark.createDataFrame([], schema)
        with pytest.raises(PipelineAbendError, match="empty"):
            assert_table_not_empty(empty_df, "test_table", "CBTEST")

    def test_passes_on_non_empty_df(self, spark, daily_tran_df):
        # Should not raise
        assert_table_not_empty(daily_tran_df, "daily_transactions", "CBTEST")


class TestValidateNoduplicateTranIds:

    def test_raises_on_duplicates(self, spark):
        from pyspark.sql.types import StructType, StructField, StringType
        schema = StructType([StructField("tran_id", StringType())])
        dupes = spark.createDataFrame([("TRN001",), ("TRN001",)], schema=schema)
        with pytest.raises(PipelineAbendError, match="Duplicate"):
            validate_no_duplicate_tran_ids(dupes, "CBTEST")

    def test_passes_on_unique_ids(self, spark):
        from pyspark.sql.types import StructType, StructField, StringType
        schema = StructType([StructField("tran_id", StringType())])
        unique = spark.createDataFrame([("TRN001",), ("TRN002",)], schema=schema)
        validate_no_duplicate_tran_ids(unique, "CBTEST")


class TestValidateDateFormat:

    def test_valid_date_passes(self):
        validate_date_format("2024-01-15", "WS-START-DATE", "CBTEST")

    def test_invalid_format_raises(self):
        with pytest.raises(PipelineAbendError):
            validate_date_format("01/15/2024", "WS-START-DATE", "CBTEST")

    def test_empty_string_raises(self):
        with pytest.raises(PipelineAbendError, match="empty"):
            validate_date_format("", "WS-START-DATE", "CBTEST")

    def test_none_raises(self):
        with pytest.raises(PipelineAbendError, match="empty"):
            validate_date_format(None, "WS-START-DATE", "CBTEST")

    def test_partial_date_raises(self):
        with pytest.raises(PipelineAbendError):
            validate_date_format("2024-01", "WS-START-DATE", "CBTEST")
