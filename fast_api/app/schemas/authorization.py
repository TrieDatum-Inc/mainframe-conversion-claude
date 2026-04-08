"""
Pydantic schemas for the Authorization module.

Source programs:
  COPAUA0C.cbl — Authorization Decision Engine (CICS transaction CP00)
  COPAUS0C.cbl — Authorization Summary View   (CICS transaction CPVS)
  COPAUS1C.cbl — Authorization Detail View    (CICS transaction CPVD)
  COPAUS2C.cbl — Fraud Marking                (EXEC CICS LINK sub-program)

MQ message layout → REST request/response mapping:
  MQ request buffer (W01-GET-BUFFER CSV) → AuthorizationRequest
  MQ reply  buffer  (W02-PUT-BUFFER CSV) → AuthorizationResponse
  PENDING-AUTH-REQUEST  (CCPAURQY.cpy)   → AuthorizationRequest fields
  PENDING-AUTH-RESPONSE (CCPAURLY.cpy)   → AuthorizationResponse fields
  PENDING-AUTH-DETAILS  (CIPAUDTY.cpy)   → AuthDetailResponse

Decline reason codes (WS-DECLINE-REASON-TABLE in COPAUS1C):
  0000 = APPROVED
  3100 = INVALID CARD
  4100 = INSUFFICIENT FUND
  4200 = CARD NOT ACTIVE
  4300 = ACCOUNT CLOSED
  4400 = EXCEEDED DAILY LIMIT
  5100 = CARD FRAUD
  5200 = MERCHANT FRAUD
  5300 = LOST CARD
  9000 = UNKNOWN
"""
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Enums — from 88-level conditions
# ---------------------------------------------------------------------------


class AuthDecision(str, Enum):
    """
    Auth response codes (PA-AUTH-RESP-CODE PIC X(02)).
    88 PA-AUTH-APPROVED VALUE '00'.
    '05' = declined (WS-AUTH-RESP-FLG: AUTH-RESP-DECLINED='D').
    """

    APPROVED = "00"
    DECLINED = "05"


class DeclineReasonCode(str, Enum):
    """
    Auth response reason codes (PA-AUTH-RESP-REASON PIC X(04)).
    Sourced from WS-DECLINE-REASON-TABLE in COPAUS1C.
    """

    APPROVED = "0000"
    INVALID_CARD = "3100"
    INSUFFICIENT_FUND = "4100"
    CARD_NOT_ACTIVE = "4200"
    ACCOUNT_CLOSED = "4300"
    EXCEEDED_DAILY_LIMIT = "4400"
    CARD_FRAUD = "5100"
    MERCHANT_FRAUD = "5200"
    LOST_CARD = "5300"
    UNKNOWN = "9000"


class MatchStatus(str, Enum):
    """
    PA-MATCH-STATUS PIC X(01) — 88-level conditions from CIPAUDTY.cpy.
    """

    PENDING = "P"         # PA-MATCH-PENDING
    DECLINED = "D"        # PA-MATCH-AUTH-DECLINED
    EXPIRED = "E"         # PA-MATCH-PENDING-EXPIRED
    MATCHED = "M"         # PA-MATCHED-WITH-TRAN


class FraudAction(str, Enum):
    """
    PA-AUTH-FRAUD / WS-FRD-ACTION PIC X(01).
    88 PA-FRAUD-CONFIRMED VALUE 'F'.
    88 PA-FRAUD-REMOVED   VALUE 'R'.
    """

    CONFIRMED = "F"
    REMOVED = "R"


# ---------------------------------------------------------------------------
# Authorization Request (replaces MQ W01-GET-BUFFER CSV payload)
# Maps to CCPAURQY.cpy (PENDING-AUTH-REQUEST)
# ---------------------------------------------------------------------------


class AuthorizationRequest(BaseModel):
    """
    Authorization request payload.

    Replaces the comma-delimited MQ message received by COPAUA0C
    (paragraph 2100-EXTRACT-REQUEST-MSG UNSTRING W01-GET-BUFFER).

    Field names match PA-RQ-* fields from CCPAURQY.cpy.
    """

    # PA-RQ-AUTH-DATE PIC X(06) — YYMMDD
    auth_date: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="Authorization date YYMMDD (PA-RQ-AUTH-DATE PIC X(06))",
        examples=["260331"],
    )

    # PA-RQ-AUTH-TIME PIC X(06) — HHMMSS
    auth_time: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="Authorization time HHMMSS (PA-RQ-AUTH-TIME PIC X(06))",
        examples=["143022"],
    )

    # PA-RQ-CARD-NUM PIC X(16)
    card_num: str = Field(
        ...,
        min_length=16,
        max_length=16,
        description="Card number (PA-RQ-CARD-NUM PIC X(16))",
        examples=["4111111111111111"],
    )

    # PA-RQ-AUTH-TYPE PIC X(04)
    auth_type: str = Field(
        ...,
        max_length=4,
        description="Authorization type (PA-RQ-AUTH-TYPE PIC X(04))",
        examples=["PURCH"],
    )

    # PA-RQ-CARD-EXPIRY-DATE PIC X(04) — MMYY
    card_expiry_date: str = Field(
        ...,
        min_length=4,
        max_length=4,
        description="Card expiry date MMYY (PA-RQ-CARD-EXPIRY-DATE PIC X(04))",
        examples=["1225"],
    )

    # PA-RQ-MESSAGE-TYPE PIC X(06)
    message_type: str = Field(
        default="      ",
        max_length=6,
        description="ISO 8583 message type (PA-RQ-MESSAGE-TYPE PIC X(06))",
        examples=["0100  "],
    )

    # PA-RQ-MESSAGE-SOURCE PIC X(06)
    message_source: str = Field(
        default="      ",
        max_length=6,
        description="Message source identifier (PA-RQ-MESSAGE-SOURCE PIC X(06))",
        examples=["POS   "],
    )

    # PA-RQ-PROCESSING-CODE PIC 9(06)
    processing_code: int = Field(
        default=0,
        ge=0,
        le=999999,
        description="Processing code (PA-RQ-PROCESSING-CODE PIC 9(06))",
        examples=[0],
    )

    # PA-RQ-TRANSACTION-AMT PIC +9(10).99 → Decimal
    transaction_amt: Decimal = Field(
        ...,
        description="Transaction amount (PA-RQ-TRANSACTION-AMT PIC +9(10).99)",
        examples=["150.00"],
    )

    # PA-RQ-MERCHANT-CATAGORY-CODE PIC X(04) [sic]
    merchant_category_code: str = Field(
        default="    ",
        max_length=4,
        description="Merchant category code MCC (PA-RQ-MERCHANT-CATAGORY-CODE PIC X(04))",
        examples=["5411"],
    )

    # PA-RQ-ACQR-COUNTRY-CODE PIC X(03)
    acqr_country_code: str = Field(
        default="   ",
        max_length=3,
        description="Acquirer country code (PA-RQ-ACQR-COUNTRY-CODE PIC X(03))",
        examples=["840"],
    )

    # PA-RQ-POS-ENTRY-MODE PIC 9(02)
    pos_entry_mode: int = Field(
        default=0,
        ge=0,
        le=99,
        description="POS entry mode (PA-RQ-POS-ENTRY-MODE PIC 9(02))",
        examples=[5],
    )

    # PA-RQ-MERCHANT-ID PIC X(15)
    merchant_id: str = Field(
        default="               ",
        max_length=15,
        description="Merchant ID (PA-RQ-MERCHANT-ID PIC X(15))",
        examples=["WALMART0001    "],
    )

    # PA-RQ-MERCHANT-NAME PIC X(22)
    merchant_name: str = Field(
        default="                      ",
        max_length=22,
        description="Merchant name (PA-RQ-MERCHANT-NAME PIC X(22))",
        examples=["WALMART SUPERCENTER   "],
    )

    # PA-RQ-MERCHANT-CITY PIC X(13)
    merchant_city: str = Field(
        default="             ",
        max_length=13,
        description="Merchant city (PA-RQ-MERCHANT-CITY PIC X(13))",
        examples=["BENTONVILLE  "],
    )

    # PA-RQ-MERCHANT-STATE PIC X(02)
    merchant_state: str = Field(
        default="  ",
        max_length=2,
        description="Merchant state (PA-RQ-MERCHANT-STATE PIC X(02))",
        examples=["AR"],
    )

    # PA-RQ-MERCHANT-ZIP PIC X(09)
    merchant_zip: str = Field(
        default="         ",
        max_length=9,
        description="Merchant ZIP code (PA-RQ-MERCHANT-ZIP PIC X(09))",
        examples=["727160001"],
    )

    # PA-RQ-TRANSACTION-ID PIC X(15)
    transaction_id: str = Field(
        ...,
        max_length=15,
        description="Transaction ID from acquirer (PA-RQ-TRANSACTION-ID PIC X(15))",
        examples=["TXN202603310001"],
    )

    @field_validator("transaction_amt")
    @classmethod
    def validate_positive_amount(cls, v: Decimal) -> Decimal:
        """COPAUA0C: transaction amount from PA-RQ-TRANSACTION-AMT must be non-negative."""
        if v < Decimal("0"):
            raise ValueError("Transaction amount must be non-negative")
        return v


# ---------------------------------------------------------------------------
# Authorization Response (replaces MQ W02-PUT-BUFFER CSV payload)
# Maps to CCPAURLY.cpy (PENDING-AUTH-RESPONSE)
# ---------------------------------------------------------------------------


class AuthorizationResponse(BaseModel):
    """
    Authorization decision response.

    Replaces the STRING ... INTO W02-PUT-BUFFER built in COPAUA0C
    paragraph 6000-MAKE-DECISION and sent via MQPUT1 in 7100-SEND-RESPONSE.

    Field names match PA-RL-* fields from CCPAURLY.cpy.
    """

    # PA-RL-CARD-NUM PIC X(16)
    card_num: str = Field(..., description="Card number (PA-RL-CARD-NUM PIC X(16))")

    # PA-RL-TRANSACTION-ID PIC X(15)
    transaction_id: str = Field(..., description="Transaction ID (PA-RL-TRANSACTION-ID PIC X(15))")

    # PA-RL-AUTH-ID-CODE PIC X(06) — set to PA-RQ-AUTH-TIME in COPAUA0C
    auth_id_code: str = Field(..., description="Authorization ID code (PA-RL-AUTH-ID-CODE PIC X(06))")

    # PA-RL-AUTH-RESP-CODE PIC X(02) — '00'=approved, '05'=declined
    auth_resp_code: AuthDecision = Field(
        ..., description="Authorization response code (PA-RL-AUTH-RESP-CODE)"
    )

    # PA-RL-AUTH-RESP-REASON PIC X(04)
    auth_resp_reason: DeclineReasonCode = Field(
        ..., description="Decline reason code (PA-RL-AUTH-RESP-REASON)"
    )

    # PA-RL-APPROVED-AMT PIC +9(10).99
    approved_amt: Decimal = Field(
        ..., description="Approved amount — 0.00 if declined (PA-RL-APPROVED-AMT)"
    )

    # Computed fields for API consumers
    is_approved: bool = Field(..., description="True when auth_resp_code='00'")
    decline_reason_description: str | None = Field(
        None, description="Human-readable decline reason from WS-DECLINE-REASON-TABLE"
    )

    # The auth_detail_id is set after the record is persisted (8500-INSERT-AUTH)
    auth_detail_id: int | None = Field(
        None, description="auth_details.auth_id — set after persistence"
    )


# ---------------------------------------------------------------------------
# Summary view (COPAUS0C — CPVS transaction)
# ---------------------------------------------------------------------------


class AuthSummaryResponse(BaseModel):
    """
    Authorization summary for an account.

    Corresponds to PAUTSUM0 IMS segment (CIPAUSMY.cpy),
    displayed by COPAUS0C (CPVS transaction).
    """

    acct_id: int
    cust_id: int | None = None
    auth_status: str | None = None
    credit_limit: Decimal
    cash_limit: Decimal
    credit_balance: Decimal
    cash_balance: Decimal
    available_credit: Decimal = Field(
        ...,
        description="credit_limit - credit_balance (WS-AVAILABLE-AMT in COPAUA0C)",
    )
    approved_auth_cnt: int
    declined_auth_cnt: int
    approved_auth_amt: Decimal
    declined_auth_amt: Decimal

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Detail view (COPAUS0C list rows / COPAUS1C single row)
# ---------------------------------------------------------------------------


class AuthDetailResponse(BaseModel):
    """
    Single authorization detail record.

    Maps to PAUTDTL1 IMS segment (CIPAUDTY.cpy),
    displayed by COPAUS1C (CPVD transaction) and listed by COPAUS0C.
    """

    auth_id: int
    acct_id: int
    auth_date_9c: int | None = None
    auth_time_9c: int | None = None
    auth_orig_date: str | None = None
    auth_orig_time: str | None = None
    card_num: str | None = None
    auth_type: str | None = None
    card_expiry_date: str | None = None
    message_type: str | None = None
    message_source: str | None = None
    auth_id_code: str | None = None
    auth_resp_code: str | None = None
    auth_resp_reason: str | None = None
    processing_code: int | None = None
    transaction_amt: Decimal
    approved_amt: Decimal
    merchant_category_code: str | None = None
    acqr_country_code: str | None = None
    pos_entry_mode: int | None = None
    merchant_id: str | None = None
    merchant_name: str | None = None
    merchant_city: str | None = None
    merchant_state: str | None = None
    merchant_zip: str | None = None
    transaction_id: str | None = None
    match_status: str
    auth_fraud: str | None = None
    fraud_rpt_date: str | None = None

    # Computed
    is_approved: bool = Field(..., description="auth_resp_code == '00'")
    decline_reason_description: str | None = None

    model_config = {"from_attributes": True}


class AuthDetailListResponse(BaseModel):
    """
    Paginated list of authorization detail records (COPAUS0C CPVS screen).

    Keyset pagination mirrors COPAUS0C PF7/PF8 key navigation:
      CDEMO-CPVS-PAUKEY-PREV-PG — previous page cursor
      CDEMO-CPVS-PAUKEY-LAST    — next page cursor
    """

    items: list[AuthDetailResponse]
    total: int
    next_cursor: int | None = Field(None, description="auth_id for next page (PF8)")
    prev_cursor: int | None = Field(None, description="auth_id for prev page (PF7)")
    summary: AuthSummaryResponse | None = None


# ---------------------------------------------------------------------------
# Fraud marking (COPAUS1C PF5 → EXEC CICS LINK COPAUS2C)
# ---------------------------------------------------------------------------


class FraudMarkRequest(BaseModel):
    """
    Fraud marking request — replaces EXEC CICS LINK COPAUS2C COMMAREA.

    COPAUS1C MARK-AUTH-FRAUD paragraph:
      If PA-FRAUD-CONFIRMED → SET PA-FRAUD-REMOVED (toggle off)
      Else                  → SET PA-FRAUD-CONFIRMED (toggle on)
    """

    # WS-FRD-ACTION PIC X(01): 'F'=report fraud, 'R'=remove fraud flag
    action: FraudAction = Field(
        ...,
        description="Fraud action: F=Report fraud, R=Remove fraud flag (WS-FRD-ACTION)",
    )


class FraudMarkResponse(BaseModel):
    """
    Result of fraud marking operation (WS-FRAUD-STATUS-RECORD from COPAUS2C).
    """

    # WS-FRD-UPDATE-STATUS: 'S'=success, 'F'=failed
    success: bool = Field(..., description="True if SQLCODE=0 (WS-FRD-UPDT-SUCCESS)")
    message: str = Field(..., description="WS-FRD-ACT-MSG PIC X(50)")
    auth_fraud: str | None = Field(None, description="Updated fraud flag value")
    fraud_rpt_date: str | None = Field(None, description="PA-FRAUD-RPT-DATE set date")
