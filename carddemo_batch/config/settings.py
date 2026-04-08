"""
CardDemo Batch Pipeline - Central configuration.

All table names, schema identifiers, and pipeline-wide constants live here.
Nothing in the business logic modules should hard-code strings that belong here.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Catalog / database
# ---------------------------------------------------------------------------
CATALOG: str = "main"
DATABASE: str = "carddemo"


def table(name: str) -> str:
    """Return a fully-qualified Delta table path."""
    return f"{CATALOG}.{DATABASE}.{name}"


# ---------------------------------------------------------------------------
# Table names (mirrors setup_tables.sql)
# ---------------------------------------------------------------------------
TBL_DAILY_TRANSACTIONS: str = table("daily_transactions")
TBL_TRANSACTIONS: str = table("transactions")
TBL_ACCOUNTS: str = table("accounts")
TBL_CARD_XREF: str = table("card_xref")
TBL_TRAN_CAT_BAL: str = table("transaction_category_balance")
TBL_DISCLOSURE_GROUPS: str = table("disclosure_groups")
TBL_TRAN_TYPES: str = table("transaction_types")
TBL_TRAN_CATEGORIES: str = table("transaction_categories")
TBL_CUSTOMERS: str = table("customers")
TBL_TRANSACTIONS_BY_CARD: str = table("transactions_by_card")
TBL_DAILY_REJECTS: str = table("daily_reject_transactions")
TBL_INTEREST_TRANSACTIONS: str = table("interest_transactions")
TBL_TRANSACTION_REPORT: str = table("transaction_report")
TBL_ACCOUNT_STATEMENTS: str = table("account_statements")

# ---------------------------------------------------------------------------
# CBTRN02C validation reason codes
# Mirrors WS-VALIDATION-FAIL-REASON values in CBTRN02C.cbl
# ---------------------------------------------------------------------------
REJECT_CODE_INVALID_CARD: int = 100     # "INVALID CARD NUMBER FOUND"
REJECT_CODE_ACCOUNT_NOT_FOUND: int = 101  # "ACCOUNT RECORD NOT FOUND"
REJECT_CODE_OVERLIMIT: int = 102        # "OVERLIMIT TRANSACTION"
REJECT_CODE_EXPIRED_ACCT: int = 103     # "TRANSACTION RECEIVED AFTER ACCT EXPIRATION"
REJECT_CODE_ACCT_REWRITE_FAIL: int = 109  # "ACCOUNT RECORD NOT FOUND" on rewrite

REJECT_DESCRIPTIONS: dict[int, str] = {
    REJECT_CODE_INVALID_CARD: "INVALID CARD NUMBER FOUND",
    REJECT_CODE_ACCOUNT_NOT_FOUND: "ACCOUNT RECORD NOT FOUND",
    REJECT_CODE_OVERLIMIT: "OVERLIMIT TRANSACTION",
    REJECT_CODE_EXPIRED_ACCT: "TRANSACTION RECEIVED AFTER ACCT EXPIRATION",
    REJECT_CODE_ACCT_REWRITE_FAIL: "ACCOUNT RECORD NOT FOUND",
}

# ---------------------------------------------------------------------------
# CBACT04C interest constants
# Mirrors hard-coded values in paragraphs 1300-B-WRITE-TX
# ---------------------------------------------------------------------------
INTEREST_TRAN_TYPE_CD: str = "01"
INTEREST_TRAN_CAT_CD: int = 5
INTEREST_TRAN_SOURCE: str = "System"
INTEREST_DIVISOR: int = 1200   # monthly rate = annual_rate / 1200

# Fallback group used when DISCGRP lookup misses (status 23)
INTEREST_DEFAULT_GROUP: str = "DEFAULT"

# ---------------------------------------------------------------------------
# CBTRN03C report pagination
# Mirrors WS-PAGE-SIZE PIC 9(03) COMP-3 VALUE 20
# ---------------------------------------------------------------------------
REPORT_PAGE_SIZE: int = 20
