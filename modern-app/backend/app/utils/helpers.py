"""Shared helper utilities for the transaction module."""

from datetime import datetime


def format_transaction_id(raw_id: int) -> str:
    """Zero-pad a transaction ID integer to 16 characters.

    COBOL TRAN-ID is X(16), and the auto-generation uses max+1 on a
    zero-padded numeric string. This function reproduces that format.

    Example:
        format_transaction_id(42) == '0000000000000042'
    """
    return str(raw_id).zfill(16)


def format_date_for_display(dt: datetime) -> str:
    """Format a datetime as MM/DD/YY for list display.

    Mirrors the COBOL date parsing of TRAN-ORIG-TS (26-char timestamp)
    into the 8-char TDATE display field on COTRN00C.
    """
    return dt.strftime("%m/%d/%y")


def format_date_iso(dt: datetime) -> str:
    """Return the date portion as YYYY-MM-DD."""
    return dt.strftime("%Y-%m-%d")
