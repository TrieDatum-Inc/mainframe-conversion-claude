"""
Pydantic schemas for Transaction endpoints.

COBOL origin: COTRN00C (list/browse), COTRN01C (detail view), COTRN02C (add).

Key design decisions vs. COBOL:
  - TransactionCreateRequest uses account_id XOR card_number (COTRN02C mutual exclusivity)
  - confirm='Y' gate preserved from COTRN02C CONFIRMI field
  - amount != 0 validation from COTRN02C VALIDATE-INPUT-FIELDS
  - processed_date >= original_date from COTRN02C date validation via CSUTLDTC
  - transaction_id is NOT in TransactionCreateRequest — generated server-side via sequence
    (fixes COTRN02C STARTBR/READPREV race condition)
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


class TransactionListItem(BaseModel):
    """
    Single row in the paginated transaction list.

    COBOL origin: COTRN00C POPULATE-TRAN-DATA — fills 10 screen rows:
      TRNID1O–TRNID10O   → transaction_id
      TRNDT1O–TRNDT10O   → original_date (extracted from TRAN-ORIG-TS)
      TRNAM1O–TRNAM10O   → description (TRAN-DESC)
      TRNAM1O–TRNAM10O   → amount (TRAN-AMT, from COTRN00C map)
    """

    transaction_id: str
    original_date: Optional[date] = None
    description: Optional[str] = None
    amount: Decimal

    model_config = {"from_attributes": True}


class TransactionDetailResponse(BaseModel):
    """
    Full transaction detail.

    COBOL origin: COTRN01C POPULATE-TRAN-FIELDS — maps all TRAN-RECORD fields
    to COTRN1AO output fields. Also used as the response body for POST /transactions.

    Notable fix: COTRN01C issued READ UPDATE (exclusive lock) for this display-only
    operation. The modern API uses a plain SELECT — no lock acquired.
    """

    transaction_id: str = Field(description="TRNIDO output field")
    card_number: str = Field(description="TRNCARDO output field")
    transaction_type_code: str = Field(description="TRNTPO output field")
    transaction_category_code: Optional[str] = Field(None, description="TCATCD")
    transaction_source: Optional[str] = Field(None, description="TRNSRC")
    description: Optional[str] = Field(None, description="TDESC / TRNDESCO")
    amount: Decimal = Field(description="TRNAMO / TRNAMT output field")
    original_date: Optional[date] = Field(None, description="TRNORIGO — TRAN-ORIG-TS date part")
    processed_date: Optional[date] = Field(None, description="TRNPROCO — TRAN-PROC-TS date part")
    merchant_id: Optional[str] = Field(None, description="MID / TRNMRCHO")
    merchant_name: Optional[str] = Field(None, description="MNAME / TRNMRCO")
    merchant_city: Optional[str] = Field(None, description="MCITY / TRNMRCCDO")
    merchant_zip: Optional[str] = Field(None, description="MZIP / TRNMRCZIPO")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    """
    Paginated transaction list response.

    COBOL origin: COTRN00C — 10 rows per page (POPULATE-TRAN-DATA loop limit).
    Pagination anchors CDEMO-CT00-TRNID-FIRST and CDEMO-CT00-TRNID-LAST (commarea fields)
    replaced by standard page/page_size/total_count.
    """

    items: list[TransactionListItem]
    page: int
    page_size: int
    total_count: int
    has_next: bool
    has_previous: bool
    first_item_key: Optional[str] = None
    last_item_key: Optional[str] = None

    model_config = {"from_attributes": True}


class TransactionCreateRequest(BaseModel):
    """
    Request body for POST /api/v1/transactions.

    COBOL origin: COTRN02C screen fields (COTRN2AI input map):
      ACCTIDOI  → account_id  (mutually exclusive with card_number)
      CARDINPI  → card_number (mutually exclusive with account_id)
      TRNTYPEI  → transaction_type_code
      TRNCATI   → transaction_category_code
      TRNSRCI   → transaction_source
      TRNDESI   → description
      TRNAMI    → amount (format: ±NNNNNNNN.NN)
      TRNORIGI  → original_date (YYYYMMDD validated via CSUTLDTC equivalent)
      TRNPROCI  → processed_date (YYYYMMDD; must be >= original_date)
      TRNMRCHI  → merchant_id (9-digit numeric)
      TRNMRCNMI → merchant_name
      TRNMRCCTI → merchant_city
      TRNMRCZPI → merchant_zip
      CONFIRMI  → confirm ('Y' required to insert — COTRN02C ADD-TRANSACTION gate)

    Key COTRN02C business rules encoded as validators:
      1. account_id XOR card_number required (COTRN02C: both blank = error)
      2. amount != 0 (COTRN02C VALIDATE-INPUT-FIELDS)
      3. processed_date >= original_date (COTRN02C date validation)
      4. confirm must be 'Y' (COTRN02C CONFIRMI check)
    """

    account_id: Optional[int] = Field(
        None,
        description="ACTIDIN / ACCTIDOI — 11-digit account ID. Mutually exclusive with card_number.",
    )
    card_number: Optional[str] = Field(
        None,
        min_length=16,
        max_length=16,
        description="CARDINPI — 16-char card number. Mutually exclusive with account_id.",
    )
    transaction_type_code: str = Field(
        ...,
        min_length=1,
        max_length=2,
        description="TRNTYPEI — must exist in transaction_types table.",
    )
    transaction_category_code: Optional[str] = Field(
        None,
        max_length=4,
        description="TRNCATI — 4-digit numeric category.",
    )
    transaction_source: Optional[str] = Field(
        None,
        max_length=10,
        description="TRNSRCI — source code (e.g. 'POS TERM').",
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=60,
        description="TRNDESI — transaction description; must not be blank.",
    )
    amount: Decimal = Field(
        ...,
        description="TRNAMI — signed amount; format ±NNNNNNNN.NN; must not be zero.",
    )
    original_date: date = Field(
        ...,
        description="TRNORIGI — YYYYMMDD in COBOL; ISO date here. Validated by CSUTLDTC equivalent.",
    )
    processed_date: date = Field(
        ...,
        description="TRNPROCI — must be >= original_date. Validated by CSUTLDTC equivalent.",
    )
    merchant_id: str = Field(
        ...,
        min_length=1,
        max_length=9,
        description="TRNMRCHI — 9-digit merchant ID.",
    )
    merchant_name: str = Field(
        ...,
        min_length=1,
        max_length=30,
        description="TRNMRCNMI — merchant name.",
    )
    merchant_city: Optional[str] = Field(
        None,
        max_length=25,
        description="TRNMRCCTI — merchant city.",
    )
    merchant_zip: Optional[str] = Field(
        None,
        max_length=10,
        description="TRNMRCZPI — merchant ZIP code.",
    )
    confirm: Literal["Y"] = Field(
        ...,
        description=(
            "CONFIRMI — must be 'Y' to insert record. "
            "Replicates COTRN02C CONFIRMI gate before ADD-TRANSACTION."
        ),
    )

    @model_validator(mode="after")
    def validate_business_rules(self) -> "TransactionCreateRequest":
        """
        Validate COTRN02C business rules that span multiple fields.

        COBOL origin: COTRN02C VALIDATE-INPUT-FIELDS + ADD-TRANSACTION entry checks.
        """
        # COTRN02C: Card number blank AND account ID blank → error
        if not self.account_id and not self.card_number:
            raise ValueError(
                "Either account_id or card_number must be provided (COTRN02C: both blank check)"
            )

        # COTRN02C: amount must not be zero
        if self.amount == 0:
            raise ValueError("Amount must not be zero (COTRN02C: TRNAMI zero check)")

        # COTRN02C: processed date must be >= original date (CSUTLDTC date order validation)
        if self.processed_date < self.original_date:
            raise ValueError(
                "processed_date must be >= original_date (COTRN02C: CSUTLDTC date validation)"
            )

        return self
