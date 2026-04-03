"""Transaction-related Pydantic schemas.

Field constraints mirror COBOL PIC clauses and business validation rules
from CBTRN02C and CBTRN03C specifications.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class DailyTransactionInput(BaseModel):
    """Input transaction record. Maps DALYTRAN-RECORD (CVTRA06Y, 350 bytes).

    Validation rules mirror CBTRN02C 1500-VALIDATE-TRAN paragraph.
    """

    tran_id: str = Field(..., min_length=1, max_length=16, description="Transaction ID")
    tran_type_cd: str = Field(..., min_length=2, max_length=2, description="Transaction type code")
    tran_cat_cd: str = Field(..., min_length=1, max_length=4, description="Transaction category code")
    tran_source: str = Field(..., min_length=1, max_length=10, description="Source channel")
    tran_desc: str = Field(..., max_length=100, description="Transaction description")
    tran_amt: Decimal = Field(..., description="Transaction amount (negative=debit, positive=credit)")
    tran_merchant_id: str | None = Field(None, max_length=9)
    tran_merchant_name: str | None = Field(None, max_length=50)
    tran_merchant_city: str | None = Field(None, max_length=50)
    tran_merchant_zip: str | None = Field(None, max_length=10)
    tran_card_num: str = Field(..., min_length=16, max_length=16, description="Card number")
    tran_orig_ts: datetime = Field(..., description="Transaction origination timestamp")

    @field_validator("tran_card_num")
    @classmethod
    def validate_card_num(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("Card number must be numeric")
        return v


class RejectRecord(BaseModel):
    """Reject record written to DALYREJS. Maps 430-byte CBTRN02C output.

    reason_code values:
      100 = INVALID CARD NUMBER FOUND (1500-A-LOOKUP-XREF)
      101 = ACCOUNT RECORD NOT FOUND (1500-B-LOOKUP-ACCT INVALID KEY)
      102 = OVERLIMIT TRANSACTION (credit limit check)
      103 = TRANSACTION RECEIVED AFTER ACCT EXPIRATION (expiry check)
    """

    tran_id: str
    card_num: str
    reason_code: str
    reason_desc: str
    original_data: dict


class TransactionDetail(BaseModel):
    """Detail record for transaction report. Maps TRANSACTION-DETAIL-REPORT (CVTRA07Y)."""

    tran_id: str
    account_id: str
    tran_type_cd: str
    tran_type_desc: str  # First 15 chars of 50-char CVTRA03Y description
    tran_cat_cd: str
    tran_cat_desc: str   # First 29 chars of 50-char CVTRA04Y description
    tran_source: str
    tran_amt: Decimal
    tran_proc_ts: datetime


class TransactionReportLine(BaseModel):
    """Report output line with enriched metadata."""

    tran_id: str
    account_id: str
    tran_type_cd: str
    tran_type_desc: str
    tran_cat_cd: str
    tran_cat_desc: str
    tran_source: str
    tran_amt: Decimal
    tran_proc_ts: datetime
    card_num: str
