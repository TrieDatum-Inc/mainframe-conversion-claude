"""
Pydantic schemas for Transaction endpoints.

Maps COTRN00C (list), COTRN01C (detail view), COTRN02C (add) screen fields.
Also includes schemas for COBIL00C (bill payment) and CORPT00C (report generation).

COTRN02C business rules:
  - Transaction ID: auto-generated (READPREV to find last key + 1)
  - Card num: looked up from CDEMO-CT02-TRN-SELECTED or entered directly
  - Account/card cross-reference validated via CXACAIX
  - Confirmation step (Y/N) prevents accidental submission
  - Date format validated via CSUTLDTC external call
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class TransactionBase(BaseModel):
    """Core transaction fields from CVTRA05Y copybook."""
    tran_type_cd: str = Field(
        ...,
        min_length=1,
        max_length=2,
        description="Transaction type code - TRAN-TYPE-CD PIC X(02)",
    )
    tran_cat_cd: int = Field(
        ...,
        ge=0,
        le=9999,
        description="Transaction category code - TRAN-CAT-CD PIC 9(04)",
    )
    tran_source: Optional[str] = Field(
        default=None,
        max_length=10,
        description="Source system - TRAN-SOURCE PIC X(10)",
    )
    tran_desc: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Description - TRAN-DESC PIC X(100)",
    )
    tran_amt: Decimal = Field(
        ...,
        description="Transaction amount - TRAN-AMT PIC S9(09)V99",
    )
    merchant_id: Optional[int] = Field(
        default=None,
        ge=0,
        le=999999999,
        description="Merchant ID - TRAN-MERCHANT-ID PIC 9(09)",
    )
    merchant_name: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Merchant name - TRAN-MERCHANT-NAME PIC X(50)",
    )
    merchant_city: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Merchant city - TRAN-MERCHANT-CITY PIC X(50)",
    )
    merchant_zip: Optional[str] = Field(
        default=None,
        max_length=10,
        description="Merchant ZIP - TRAN-MERCHANT-ZIP PIC X(10)",
    )


class TransactionView(TransactionBase):
    """
    Full transaction detail (COTRN01C).
    Displays all fields of a single transaction record.
    """
    tran_id: str = Field(
        ...,
        max_length=16,
        description="Transaction ID - TRAN-ID PIC X(16)",
    )
    card_num: str = Field(
        ...,
        max_length=16,
        description="Card number - TRAN-CARD-NUM PIC X(16)",
    )
    orig_ts: Optional[datetime] = Field(
        default=None,
        description="Original timestamp - TRAN-ORIG-TS PIC X(26)",
    )
    proc_ts: Optional[datetime] = Field(
        default=None,
        description="Processing timestamp - TRAN-PROC-TS PIC X(26)",
    )

    model_config = {"from_attributes": True}


class TransactionListItem(BaseModel):
    """
    Single row in COTRN00C transaction list screen.
    Shows 10 rows per page with TRNID selector.
    """
    tran_id: str = Field(..., max_length=16)
    tran_type_cd: str = Field(..., max_length=2)
    tran_cat_cd: int
    tran_amt: Decimal
    card_num: str = Field(..., max_length=16)
    orig_ts: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    """
    Paginated transaction list (COTRN00C).
    COTRN00C state: CDEMO-CT00-PAGE-NUM, CDEMO-CT00-NEXT-PAGE-FLG
    """
    items: List[TransactionListItem]
    page: int = Field(default=1, ge=1)
    has_next_page: bool = False
    first_tran_id: Optional[str] = None
    last_tran_id: Optional[str] = None
    start_tran_id_filter: Optional[str] = None


class TransactionAddRequest(TransactionBase):
    """
    Add new transaction (COTRN02C).

    COTRN02C logic:
    1. Card number or account ID provided
    2. CXACAIX lookup validates card/account relationship
    3. READPREV to find last tran_id; new ID = last + 1
    4. Two-step confirm: POST returns preview, PUT confirms
    """
    card_num: Optional[str] = Field(
        default=None,
        max_length=16,
        description="Card number - TRAN-CARD-NUM PIC X(16)",
    )
    acct_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="Account ID - used for CXACAIX lookup if card_num not provided",
    )

    @field_validator("tran_type_cd")
    @classmethod
    def validate_tran_type(cls, v: str) -> str:
        return v.strip().upper()


class BillPaymentRequest(BaseModel):
    """
    Bill payment request (COBIL00C).

    COBIL00C spec: payment is always full balance.
    1. Accept account_id only
    2. Read ACCTDAT to get current balance (ACCT-CURR-BAL)
    3. Balance must be > 0 ("You have nothing to pay...")
    4. On confirm: TRAN-AMT = ACCT-CURR-BAL (full balance)
    5. WRITE TRANSACT (payment record with type '02', cat 2)
    6. REWRITE ACCTDAT: ACCT-CURR-BAL = ACCT-CURR-BAL - TRAN-AMT (zeros it)
    """
    account_id: int = Field(
        ...,
        gt=0,
        description="Account to pay - maps to ACCTDAT read by COBIL00C",
    )


class BillPaymentResponse(BaseModel):
    """Response after successful bill payment."""
    account_id: int
    previous_balance: Decimal
    payment_amount: Decimal
    new_balance: Decimal
    transaction_id: str
    message: str = "Payment successful."


class ReportRequest(BaseModel):
    """
    Report generation request (CORPT00C).
    Maps CRPT00AI BMS map fields to REST parameters.
    CORPT00C -> triggers batch CBTRN03C equivalent.
    """
    start_date: Optional[str] = Field(
        default=None,
        description="Report start date YYYY-MM-DD",
    )
    end_date: Optional[str] = Field(
        default=None,
        description="Report end date YYYY-MM-DD",
    )
    account_id: Optional[int] = Field(
        default=None,
        description="Filter by account ID (optional)",
    )
    card_num: Optional[str] = Field(
        default=None,
        max_length=16,
        description="Filter by card number (optional)",
    )
    confirm: bool = Field(
        default=False,
        description="Two-step confirm: POST to preview, POST with confirm=true to generate",
    )


class ReportResponse(BaseModel):
    """Report generation response."""
    report_id: str
    status: str
    message: str
    total_transactions: int = 0
    total_amount: Decimal = Decimal("0.00")
