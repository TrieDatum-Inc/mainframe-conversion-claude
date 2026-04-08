"""
CardDemo Batch - Common Validators and Error Handlers

Maps to COBOL error-handling patterns:
  - 9999-ABEND-PROGRAM    -> raise PipelineAbendError
  - 9910-DISPLAY-IO-STATUS -> log_io_status()
  - FILE STATUS '00'       -> is_status_ok()
  - FILE STATUS '10'       -> is_status_eof()
  - FILE STATUS '23'       -> is_status_not_found()
"""

from __future__ import annotations

import logging
from typing import Optional

from pyspark.sql import DataFrame

from carddemo_batch.config.columns import COL_TRAN_ID

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# COBOL abend equivalent
# ---------------------------------------------------------------------------

class PipelineAbendError(RuntimeError):
    """
    Raised when the pipeline encounters an unrecoverable error.
    Mirrors the COBOL 9999-ABEND-PROGRAM paragraph which calls CEE3ABD
    with abend code 999.
    """

    def __init__(self, program: str, message: str, cobol_error_code: str = "999") -> None:
        super().__init__(f"[{program}] ABEND-{cobol_error_code}: {message}")
        self.program = program
        self.cobol_error_code = cobol_error_code


# ---------------------------------------------------------------------------
# DataFrame count validation (replaces FILE STATUS checks)
# ---------------------------------------------------------------------------

def assert_table_not_empty(df: DataFrame, table_name: str, program: str) -> None:
    """
    Raise PipelineAbendError if a required input table is empty.
    Mirrors the pattern: OPEN INPUT file -> IF FILE-STATUS != '00' -> ABEND.
    """
    if df.count() == 0:
        raise PipelineAbendError(
            program=program,
            message=f"Required input table '{table_name}' is empty or could not be read.",
            cobol_error_code="12",
        )


def validate_no_duplicate_tran_ids(tran_df: DataFrame, program: str) -> None:
    """
    Validate that transaction IDs are unique before writing to the
    indexed TRANSACT-FILE (VSAM KSDS).  COBOL would get status '22'
    (duplicate key) on WRITE.
    """
    total = tran_df.count()
    distinct = tran_df.select(COL_TRAN_ID).distinct().count()
    if total != distinct:
        raise PipelineAbendError(
            program=program,
            message=(
                f"Duplicate TRAN-IDs detected: {total} records but "
                f"only {distinct} distinct IDs. "
                "VSAM write would fail with FILE STATUS 22."
            ),
            cobol_error_code="22",
        )


def validate_date_format(date_str: Optional[str], field_name: str, program: str) -> None:
    """
    Validate YYYY-MM-DD formatted date parameters.
    Used to validate WS-START-DATE / WS-END-DATE from DATEPARM file.
    """
    import re

    if not date_str:
        raise PipelineAbendError(
            program=program,
            message=f"Required date parameter '{field_name}' is empty.",
            cobol_error_code="12",
        )
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_str):
        raise PipelineAbendError(
            program=program,
            message=(
                f"Date parameter '{field_name}' value '{date_str}' "
                "is not in YYYY-MM-DD format."
            ),
            cobol_error_code="12",
        )


# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------

def log_io_status(program: str, file_name: str, status: str) -> None:
    """
    COBOL: 9910-DISPLAY-IO-STATUS
    Log a file I/O status code in the same format as the COBOL DISPLAY.
    """
    logger.error("[%s] FILE STATUS IS: %s  File: %s", program, status.zfill(4), file_name)


def log_processing_summary(
    program: str,
    records_read: int,
    records_written: int = 0,
    records_rejected: int = 0,
) -> None:
    """
    Mirrors the COBOL end-of-program DISPLAY statements for record counts.
    """
    logger.info(
        "[%s] RECORDS READ: %d  WRITTEN: %d  REJECTED: %d",
        program,
        records_read,
        records_written,
        records_rejected,
    )
    if records_rejected > 0:
        logger.warning(
            "[%s] %d records rejected - review daily_reject_transactions table.",
            program,
            records_rejected,
        )
