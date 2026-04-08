"""
Pydantic schemas for transaction operations (COTRN00C, COTRN01C, COTRN02C).

Maps COTRN00/COTRN01/COTRN02 BMS maps to request/response schemas.

COTRN00C: list/browse transactions
  → GET /api/v1/transactions

COTRN01C: view single transaction detail
  → GET /api/v1/transactions/{tran_id}

COTRN02C: add new transaction
  → POST /api/v1/transactions

Also used by COBIL00C bill payment which writes a new transaction record.
"""
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.utils.cobol_compat import cobol_upper


class TransactionBase(BaseModel):
    """Shared transaction fields."""

    type_cd: str | None = Field(None, max_length=2, description="TRAN-TYPE-CD PIC X(02)")
    cat_cd: int | None = Field(None, ge=0, description="TRAN-CAT-CD PIC 9(04)")
    source: str | None = Field(None, max_length=10, description="TRAN-SOURCE PIC X(10)")
    description: str | None = Field(None, max_length=100, description="TRAN-DESC PIC X(100)")
    amount: Decimal = Field(..., description="TRAN-AMT PIC S9(09)V99 COMP-3")
    merchant_id: int | None = Field(None, description="TRAN-MERCHANT-ID PIC 9(09)")
    merchant_name: str | None = Field(None, max_length=50, description="TRAN-MERCHANT-NAME PIC X(50)")
    merchant_city: str | None = Field(None, max_length=50, description="TRAN-MERCHANT-CITY PIC X(50)")
    merchant_zip: str | None = Field(None, max_length=10, description="TRAN-MERCHANT-ZIP PIC X(10)")
    card_num: str | None = Field(None, max_length=16, description="TRAN-CARD-NUM PIC X(16)")
    orig_ts: str | None = Field(None, max_length=26, description="TRAN-ORIG-TS PIC X(26)")
    proc_ts: str | None = Field(None, max_length=26, description="TRAN-PROC-TS PIC X(26)")


class TransactionResponse(TransactionBase):
    """
    Transaction view response — maps to COTRN01 BMS map SEND MAP output.
    """

    tran_id: str = Field(..., description="TRAN-ID PIC X(16)")
    acct_id: int | None = Field(None, description="Derived account ID from XREF")

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    """
    Paginated transaction list — maps to COTRN00 BMS map (10 rows per screen).

    Keyset pagination mirrors STARTBR/READNEXT on TRANSACT:
      next_cursor = last TRAN-ID on page (use as start key for next STARTBR GTEQ)
    """

    items: list[TransactionResponse]
    total: int
    next_cursor: str | None = Field(None, description="Keyset cursor: last tran_id on this page")
    prev_cursor: str | None = Field(None, description="Keyset cursor: first tran_id on this page")


class TransactionCreateRequest(TransactionBase):
    """
    Create transaction request — maps to COTRN02C RECEIVE MAP.

    Business rules:
      - amount must not be zero (COTRN02C validation)
      - card_num is required — used to look up account via CCXREF
      - tran_id is auto-generated (like COBIL00C WS-TRAN-ID-NUM from ASKTIME)
      - type_cd required for transaction posting
    """

    amount: Decimal = Field(..., description="TRAN-AMT: must not be zero")
    card_num: str = Field(..., min_length=16, max_length=16, description="TRAN-CARD-NUM PIC X(16)")
    type_cd: str = Field(..., min_length=1, max_length=2, description="TRAN-TYPE-CD PIC X(02)")

    @field_validator("amount")
    @classmethod
    def amount_not_zero(cls, v: Decimal) -> Decimal:
        """COTRN02C: transaction amount must not be zero."""
        if v == 0:
            raise ValueError("Transaction amount must not be zero")
        return v


class BillPaymentRequest(BaseModel):
    """
    Bill payment request — maps to COBIL00C BMS map input.

    COBIL00C business rules:
      - payment_amount must be positive and <= current balance
      - Creates new TRANSACT record (EXEC CICS WRITE FILE(TRANSACT))
      - Updates ACCT-CURR-BAL via EXEC CICS REWRITE FILE(ACCTDAT)
      - Looks up card via CXACAIX (browse by account ID)
    """

    account_id: int = Field(..., description="Account to apply payment to")
    payment_amount: Decimal = Field(..., gt=0, description="Payment amount (must be positive)")
    description: str | None = Field("Bill Payment", max_length=100, description="TRAN-DESC")


class AccountPaymentRequest(BaseModel):
    """
    Account-centric bill payment request body — used by POST /api/v1/accounts/{acct_id}/payments.

    The account_id is taken from the URL path parameter, so only the payment
    amount and optional description are required in the request body.

    Equivalent to COBIL00C BMS map COBI0AI input fields:
      PYMTAMTI  PIC X(09) — payment amount entered by operator
      (account ID comes from COMMAREA WS-ACCT-ID, not the map)
    """

    payment_amount: Decimal = Field(..., gt=0, description="Payment amount (must be positive)")
    description: str | None = Field("Bill Payment", max_length=100, description="TRAN-DESC")
