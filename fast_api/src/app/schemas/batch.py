"""Batch operation request/response schemas.

Each schema maps to a COBOL batch program:
- TransactionPostingRequest/Response -> CBTRN02C
- TransactionReportRequest/Response -> CBTRN03C
- InterestCalculationRequest/Response -> CBACT04C
- ExportResponse -> CBEXPORT
- ImportRequest/Response -> CBIMPORT
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.transaction import DailyTransactionInput, RejectRecord, TransactionReportLine


# ============================================================
# CBTRN02C — Daily Transaction Posting
# ============================================================

class TransactionPostingRequest(BaseModel):
    """Request to run CBTRN02C equivalent.

    transactions: list of DALYTRAN records to post.
    If empty, posts all pending transactions (future: from DB staging table).
    """

    transactions: list[DailyTransactionInput] = Field(
        ...,
        description="List of daily transactions to validate and post",
    )


class TransactionPostingResponse(BaseModel):
    """Response from CBTRN02C equivalent.

    has_rejects maps to COBOL return code 4 when WS-REJECT-COUNT > 0.
    """

    job_id: int
    status: str
    transactions_processed: int
    transactions_posted: int
    transactions_rejected: int
    has_rejects: bool
    rejects: list[RejectRecord]
    message: str


# ============================================================
# CBTRN03C — Transaction Report Generator
# ============================================================

class TransactionReportRequest(BaseModel):
    """Request to run CBTRN03C equivalent.

    Date range maps to DATEPARM control file input.
    """

    start_date: date = Field(..., description="Report start date (YYYY-MM-DD), maps to WS-START-DATE")
    end_date: date = Field(..., description="Report end date (YYYY-MM-DD), maps to WS-END-DATE")


class ReportTotals(BaseModel):
    """Report summary totals. Maps page/account/grand totals from CBTRN03C."""

    grand_total: Decimal
    page_count: int
    transaction_count: int


class TransactionReportResponse(BaseModel):
    """Response from CBTRN03C equivalent. Replaces DALYREPT GDG output."""

    job_id: int
    status: str
    start_date: date
    end_date: date
    report_lines: list[TransactionReportLine]
    totals: ReportTotals
    report_text: str  # Formatted 133-char-wide report text (preserves COBOL layout)
    message: str


# ============================================================
# CBACT04C — Interest and Fee Calculator
# ============================================================

class InterestCalculationRequest(BaseModel):
    """Request to run CBACT04C equivalent.

    run_date maps to JCL PARM date used to prefix generated TRAN-IDs.
    """

    run_date: date = Field(
        ...,
        description="Calculation run date (YYYY-MM-DD). Used to prefix interest transaction IDs.",
    )


class InterestTransactionResult(BaseModel):
    """One interest charge created by CBACT04C equivalent."""

    tran_id: str
    acct_id: str
    tran_type_cd: str
    tran_cat_cd: str
    balance: Decimal
    interest_rate: Decimal
    monthly_interest: Decimal
    card_num: str


class AccountInterestSummary(BaseModel):
    """Per-account interest summary."""

    acct_id: str
    total_interest: Decimal
    category_count: int
    transactions_created: list[InterestTransactionResult]


class InterestCalculationResponse(BaseModel):
    """Response from CBACT04C equivalent."""

    job_id: int
    status: str
    run_date: date
    accounts_processed: int
    interest_transactions_created: int
    account_summaries: list[AccountInterestSummary]
    # TODO: fee_calculations_performed when 1400-COMPUTE-FEES is implemented
    message: str


# ============================================================
# CBEXPORT — Data Export
# ============================================================

class CustomerExport(BaseModel):
    """Customer record in export payload. Maps EXPORT-CUSTOMER-DATA / CVCUS01Y."""

    cust_id: str
    cust_first_name: str | None
    cust_middle_name: str | None
    cust_last_name: str | None
    cust_addr_line_1: str | None
    cust_addr_line_2: str | None
    cust_addr_line_3: str | None
    cust_addr_state_cd: str | None
    cust_addr_country_cd: str | None
    cust_addr_zip: str | None
    cust_phone_num_1: str | None
    cust_phone_num_2: str | None
    cust_ssn: str | None
    cust_govt_issued_id: str | None
    cust_dob: date | None
    cust_eft_account_id: str | None
    cust_pri_card_holder_ind: str | None
    cust_fico_credit_score: int | None


class AccountExport(BaseModel):
    """Account record in export payload. Maps EXPORT-ACCOUNT-DATA / CVACT01Y."""

    acct_id: str
    acct_active_status: str
    acct_curr_bal: Decimal
    acct_credit_limit: Decimal
    acct_cash_credit_limit: Decimal
    acct_open_date: date | None
    acct_expiration_date: date | None
    acct_reissue_date: date | None
    acct_curr_cyc_credit: Decimal
    acct_curr_cyc_debit: Decimal
    acct_addr_zip: str | None
    acct_group_id: str | None


class XrefExport(BaseModel):
    """Cross-reference record in export payload. Maps EXPORT-CARD-XREF-DATA / CVACT03Y."""

    xref_card_num: str
    xref_cust_id: str | None
    xref_acct_id: str | None


class TransactionExport(BaseModel):
    """Transaction record in export payload. Maps EXPORT-TRANSACTION-DATA / CVTRA05Y."""

    tran_id: str
    tran_type_cd: str | None
    tran_cat_cd: str | None
    tran_source: str | None
    tran_desc: str | None
    tran_amt: Decimal | None
    tran_merchant_id: str | None
    tran_merchant_name: str | None
    tran_merchant_city: str | None
    tran_merchant_zip: str | None
    tran_card_num: str | None
    tran_orig_ts: datetime | None
    tran_proc_ts: datetime | None


class CardExport(BaseModel):
    """Card record in export payload. Maps EXPORT-CARD-DATA / CVACT02Y."""

    card_num: str
    card_acct_id: str | None
    card_cvv_cd: str | None
    card_embossed_name: str | None
    card_expiration_date: date | None
    card_active_status: str


class ExportPayload(BaseModel):
    """Full export payload. Replaces CBEXPORT 500-byte fixed-width multi-type file."""

    export_timestamp: str  # WS-FORMATTED-TIMESTAMP
    branch_id: str = "0001"
    region_code: str = "NORTH"
    customers: list[CustomerExport]
    accounts: list[AccountExport]
    xrefs: list[XrefExport]
    transactions: list[TransactionExport]
    cards: list[CardExport]
    total_records: int


class ExportResponse(BaseModel):
    """Response from CBEXPORT equivalent."""

    job_id: int
    status: str
    customers_exported: int
    accounts_exported: int
    xrefs_exported: int
    transactions_exported: int
    cards_exported: int
    total_records_exported: int
    payload: ExportPayload
    message: str


# ============================================================
# CBIMPORT — Data Import
# ============================================================

class ImportRequest(BaseModel):
    """Request for CBIMPORT equivalent.

    Accepts the JSON payload produced by CBEXPORT.
    The 3000-VALIDATE-IMPORT stub is implemented here as real validation.
    """

    payload: ExportPayload


class ImportValidationError(BaseModel):
    """Validation error found during import. Replaces CBIMPORT error file record."""

    record_type: str  # C/A/X/T/D
    record_id: str
    field: str
    error: str


class ImportResponse(BaseModel):
    """Response from CBIMPORT equivalent."""

    job_id: int
    status: str
    total_records_read: int
    customers_imported: int
    accounts_imported: int
    xrefs_imported: int
    transactions_imported: int
    cards_imported: int
    validation_errors: list[ImportValidationError]
    error_count: int
    message: str


# ============================================================
# Generic batch job status
# ============================================================

class BatchJobResponse(BaseModel):
    """Generic batch job status response."""

    job_id: int
    job_type: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    records_processed: int
    records_rejected: int
    result_summary: dict[str, Any] | None
    created_at: datetime | None
