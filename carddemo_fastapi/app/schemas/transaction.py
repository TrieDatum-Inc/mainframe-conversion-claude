"""Transaction schemas matching COBOL CVTRA05Y.cpy and COTRN00C/COTRN01C/COTRN02C screens.

- TransactionListItem: list columns from COTRN00C screen
- TransactionDetail: full detail from COTRN01C output
- TransactionCreate: new transaction input from COTRN02C
"""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class TransactionListItem(BaseModel):
    """Transaction list item matching COTRN00C screen columns.

    Subset of CVTRA05Y.cpy TRAN-RECORD (RECLN 350).
    """

    tran_id: str = Field(..., max_length=16, description="Transaction ID (TRAN-ID PIC X(16))")
    tran_card_num: str = Field(
        ..., max_length=16, description="Card number (TRAN-CARD-NUM PIC X(16))"
    )
    tran_amt: Decimal = Field(
        ..., description="Transaction amount (TRAN-AMT PIC S9(09)V99)"
    )
    tran_orig_ts: str = Field(
        ..., max_length=26, description="Origination timestamp (TRAN-ORIG-TS PIC X(26))"
    )
    tran_type_cd: str = Field(
        ..., max_length=2, description="Transaction type code (TRAN-TYPE-CD PIC X(02))"
    )


class TransactionDetail(BaseModel):
    """Full transaction detail matching COTRN01C output.

    All fields from CVTRA05Y.cpy TRAN-RECORD (RECLN 350).
    """

    tran_id: str = Field(..., max_length=16, description="Transaction ID (TRAN-ID PIC X(16))")
    tran_type_cd: str = Field(
        ..., max_length=2, description="Transaction type code (TRAN-TYPE-CD PIC X(02))"
    )
    tran_cat_cd: int = Field(
        ..., description="Transaction category code (TRAN-CAT-CD PIC 9(04))"
    )
    tran_source: str = Field(
        ..., max_length=10, description="Transaction source (TRAN-SOURCE PIC X(10))"
    )
    tran_desc: str = Field(
        ..., max_length=100, description="Description (TRAN-DESC PIC X(100))"
    )
    tran_amt: Decimal = Field(
        ..., description="Transaction amount (TRAN-AMT PIC S9(09)V99)"
    )
    tran_merchant_id: int = Field(
        ..., description="Merchant ID (TRAN-MERCHANT-ID PIC 9(09))"
    )
    tran_merchant_name: str = Field(
        ..., max_length=50, description="Merchant name (TRAN-MERCHANT-NAME PIC X(50))"
    )
    tran_merchant_city: str = Field(
        ..., max_length=50, description="Merchant city (TRAN-MERCHANT-CITY PIC X(50))"
    )
    tran_merchant_zip: str = Field(
        ..., max_length=10, description="Merchant ZIP (TRAN-MERCHANT-ZIP PIC X(10))"
    )
    tran_card_num: str = Field(
        ..., max_length=16, description="Card number (TRAN-CARD-NUM PIC X(16))"
    )
    tran_orig_ts: str = Field(
        ..., max_length=26, description="Origination timestamp (TRAN-ORIG-TS PIC X(26))"
    )
    tran_proc_ts: str = Field(
        ..., max_length=26, description="Processing timestamp (TRAN-PROC-TS PIC X(26))"
    )


class TransactionCreate(BaseModel):
    """New transaction input matching COTRN02C screen.

    Requires at least one of card_num or acct_id to identify the account.
    """

    card_num: Optional[str] = Field(
        None, max_length=16, description="Card number (at least one of card_num or acct_id required)"
    )
    acct_id: Optional[int] = Field(
        None, description="Account ID (at least one of card_num or acct_id required)"
    )
    tran_type_cd: str = Field(
        ..., max_length=2, description="Transaction type code (TRAN-TYPE-CD PIC X(02))"
    )
    tran_cat_cd: int = Field(
        ..., description="Transaction category code (TRAN-CAT-CD PIC 9(04))"
    )
    tran_source: str = Field(
        ..., max_length=10, description="Transaction source (TRAN-SOURCE PIC X(10))"
    )
    tran_desc: str = Field(
        ..., max_length=100, description="Description (TRAN-DESC PIC X(100))"
    )
    tran_amt: Decimal = Field(
        ..., description="Transaction amount (TRAN-AMT PIC S9(09)V99)"
    )
    tran_merchant_id: int = Field(
        ..., description="Merchant ID (TRAN-MERCHANT-ID PIC 9(09))"
    )
    tran_merchant_name: str = Field(
        ..., max_length=50, description="Merchant name (TRAN-MERCHANT-NAME PIC X(50))"
    )
    tran_merchant_city: str = Field(
        ..., max_length=50, description="Merchant city (TRAN-MERCHANT-CITY PIC X(50))"
    )
    tran_merchant_zip: str = Field(
        ..., max_length=10, description="Merchant ZIP (TRAN-MERCHANT-ZIP PIC X(10))"
    )
    confirm: str = Field(
        default="N",
        max_length=1,
        description="Confirmation flag: 'Y' to confirm, 'N' to preview (matches COTRN02C pattern)",
    )

    @model_validator(mode="after")
    def require_card_or_account(self) -> "TransactionCreate":
        """At least one of card_num or acct_id must be provided."""
        if not self.card_num and self.acct_id is None:
            raise ValueError("At least one of card_num or acct_id is required")
        return self
