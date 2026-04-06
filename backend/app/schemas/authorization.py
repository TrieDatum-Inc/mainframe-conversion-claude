"""
Pydantic schemas for the Authorization module.

Maps BMS screen fields from COPAU00 (COPAU0A map) and COPAU01 (COPAU1A map)
to API request/response DTOs.

COPAUS0C → AuthSummaryResponse, AuthListItem, AuthListResponse
COPAUS1C → AuthDetailResponse (POPULATE-DETAIL-SCREEN paragraph)
COPAUS2C → FraudToggleRequest, FraudToggleResponse
"""
from datetime import date, datetime, time
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Decline reason codes — replaces COPAUS1C WS-DECLINE-REASON-TABLE
# Used in AuthDetailResponse.decline_reason field (AUTHRSNO BMS field)
# SEARCH ALL on DECL-CODE indexed by WS-DECL-RSN-IDX
# ---------------------------------------------------------------------------
DECLINE_REASON_TABLE: dict[str, str] = {
    "00": "APPROVED",
    "3100": "INVALID CARD",
    "4100": "INSUFFICNT FUND",
    "4200": "CARD NOT ACTIVE",
    "4300": "ACCOUNT CLOSED",
    "4400": "EXCED DAILY LMT",
    "5100": "CARD FRAUD",
    "5200": "MERCHANT FRAUD",
    "5300": "LOST CARD",
    "9000": "UNKNOWN",
}


def resolve_decline_reason(response_code: str) -> str:
    """
    Replaces COPAUS1C SEARCH ALL WS-DECLINE-REASON-TAB on DECL-CODE.
    Returns code-description pair like '4100-INSUFFICNT FUND'.
    If not found (COBOL AT END): returns '9999-ERROR'.
    """
    desc = DECLINE_REASON_TABLE.get(response_code.strip(), None)
    if desc is None:
        return "9999-ERROR"
    return f"{response_code.strip()}-{desc}"


def format_fraud_status_display(fraud_status: str) -> str:
    """
    Replaces COPAUS1C POPULATE-AUTH-DETAILS fraud display logic (lines 344-350).
    PA-FRAUD-CONFIRMED → 'FRAUD'
    PA-FRAUD-REMOVED → 'REMOVED'
    No flag → '' (empty, displayed as '-' in COBOL)
    """
    if fraud_status == "F":
        return "FRAUD"
    if fraud_status == "R":
        return "REMOVED"
    return ""


def mask_card_number(card_number: str) -> str:
    """
    PCI-DSS compliant card number masking for list displays.
    Shows only last 4 digits: ************1234
    """
    stripped = card_number.strip()
    if len(stripped) >= 4:
        return "*" * (len(stripped) - 4) + stripped[-4:]
    return stripped


# ---------------------------------------------------------------------------
# Summary schemas — COPAUS0C / COPAU00 (COPAU0A map)
# ---------------------------------------------------------------------------


class AuthSummaryResponse(BaseModel):
    """
    Maps COPAU00 account/customer summary section fields (rows 6-12).
    Source: IMS PAUTSUM0 root segment (CIPAUSMY copybook).
    Fields map to BMS output fields: CREDLIMO, CASHLIMO, APPRAMTO,
    CREDBALO, CASHBALO, DECLAMTO, APPRCNTO, DECLCNTO.
    """

    account_id: int = Field(description="PA-ACCT-ID — COPAU00 ACCTID field")
    credit_limit: Decimal = Field(description="PA-CREDIT-LIMIT — CREDLIMO")
    cash_limit: Decimal = Field(description="PA-CASH-LIMIT — CASHLIMO")
    credit_balance: Decimal = Field(description="PA-CREDIT-BALANCE — CREDBALO")
    cash_balance: Decimal = Field(description="PA-CASH-BALANCE — CASHBALO")
    approved_auth_count: int = Field(description="PA-APPROVED-AUTH-CNT — APPRCNTO")
    declined_auth_count: int = Field(description="PA-DECLINED-AUTH-CNT — DECLCNTO")
    approved_auth_amount: Decimal = Field(description="PA-APPROVED-AUTH-AMT — APPRAMTO")
    declined_auth_amount: Decimal = Field(description="PA-DECLINED-AUTH-AMT — DECLAMTO")

    model_config = {"from_attributes": True}


class AuthListItem(BaseModel):
    """
    Maps one authorization list row (5 rows per page) from COPAU00.
    Fields: TRNIDnn, PDATEnn, PTIMEnn, PTYPEnn, PAPRVnn, PSTATnn, PAMTnnn.
    COPAUS0C POPULATE-AUTH-LIST paragraph (lines 525-605).
    """

    auth_id: int
    transaction_id: str = Field(description="PA-TRANSACTION-ID — TRNIDnn")
    card_number_masked: str = Field(description="Card number last 4 for display")
    auth_date: date = Field(description="PA-AUTH-ORIG-DATE formatted MM/DD/YY — PDATEnn")
    auth_time: time = Field(description="PA-AUTH-ORIG-TIME formatted HH:MM:SS — PTIMEnn")
    auth_type: Optional[str] = Field(None, description="PA-AUTH-TYPE — PTYPEnn")
    approval_status: str = Field(
        description="'A'=Approved (resp='00'), 'D'=Declined — PAPRVnn"
    )
    match_status: str = Field(description="PA-MATCH-STATUS P/D/E/M — PSTATnn")
    amount: Decimal = Field(description="PA-TRANSACTION-AMT formatted — PAMTnnn")
    fraud_status: str = Field(description="N/F/R raw fraud status")
    fraud_status_display: str = Field(description="FRAUD/REMOVED/empty string")

    model_config = {"from_attributes": True}


class AuthListResponse(BaseModel):
    """
    Paginated list response for GET /api/v1/authorizations.
    Replaces COPAUS0C IMS browse (GU summary + GNP detail, 5 per page).
    page_size default 5 maps to COPAUS0C screen row count.
    CDEMO-CPVS-NEXT-PAGE-FLG → has_next.
    """

    summary: AuthSummaryResponse
    items: list[AuthListItem]
    page: int
    page_size: int
    total_count: int
    has_next: bool = Field(description="CDEMO-CPVS-NEXT-PAGE-FLG 'Y'/'N'")
    has_previous: bool


# ---------------------------------------------------------------------------
# Detail schema — COPAUS1C / COPAU01 (COPAU1A map)
# ---------------------------------------------------------------------------


class AuthDetailResponse(BaseModel):
    """
    Full authorization detail view — all COPAU1A map fields.
    COPAUS1C POPULATE-AUTH-DETAILS paragraph (lines 291-357).
    All fields are ASKIP (read-only) on COPAU01 screen.
    AUTHMTCO and AUTHFRDO displayed in RED.
    """

    auth_id: int
    account_id: int

    # CARDNUMO — PA-CARD-NUM (shown masked in list, full in detail per spec)
    card_number: str = Field(description="CARDNUMO — PA-CARD-NUM (masked)")
    card_number_masked: str = Field(description="Last 4 only for display")

    # AUTHDTO — PA-AUTH-ORIG-DATE formatted MM/DD/YY
    auth_date: date
    # AUTHTMO — PA-AUTH-ORIG-TIME formatted HH:MM:SS
    auth_time: time

    # AUTHRSPO — PA-AUTH-RESP-CODE; 'A' (00=approved) or 'D' (declined)
    auth_response_code: str
    approval_status: str = Field(description="'A' if resp='00', 'D' otherwise — AUTHRSPO")

    # AUTHRSNO — DECL-CODE + '-' + DECL-DESC from SEARCH ALL
    decline_reason: str = Field(description="AUTHRSNO from WS-DECLINE-REASON-TABLE")

    # AUTHCDO — PA-PROCESSING-CODE (auth code)
    auth_code: Optional[str] = None

    # AUTHAMTO — PA-TRANSACTION-AMT
    amount: Decimal

    # POSEMDO — PA-POS-ENTRY-MODE
    pos_entry_mode: Optional[str] = None

    # AUTHSRCO — PA-MESSAGE-SOURCE
    auth_source: Optional[str] = None

    # MCCCDO — PA-MERCHANT-CATAGORY-CODE
    mcc_code: Optional[str] = None

    # CRDEXPO — PA-CARD-EXPIRY-DATE
    card_expiry: Optional[str] = None

    # AUTHTYPO — PA-AUTH-TYPE
    auth_type: Optional[str] = None

    # TRNIDO — PA-TRANSACTION-ID
    transaction_id: str

    # AUTHMTCO — PA-MATCH-STATUS (shown in RED on COPAU01)
    match_status: str = Field(description="P/D/E/M — AUTHMTCO (RED text)")

    # AUTHFRDO — 'FRAUD'/'REMOVED'/'' (shown in RED on COPAU01)
    # Raw: N/F/R; Display: FRAUD/REMOVED/empty
    fraud_status: str = Field(description="Raw N/F/R")
    fraud_status_display: str = Field(description="FRAUD/REMOVED/'' — AUTHFRDO (RED text)")

    # Merchant details (row 19 and 21 of COPAU01, below row 17 separator)
    merchant_name: Optional[str] = None  # MERNAMEO
    merchant_id: Optional[str] = None  # MERIDO
    merchant_city: Optional[str] = None  # MERCITYO
    merchant_state: Optional[str] = None  # MERSTO
    merchant_zip: Optional[str] = None  # MERZIPO

    processed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Fraud toggle schemas — COPAUS1C PF5 → COPAUS2C LINK
# ---------------------------------------------------------------------------


class FraudToggleRequest(BaseModel):
    """
    Request body for PUT /api/v1/authorizations/detail/{auth_id}/fraud.
    Maps COPAUS1C PF5 action → COPAUS2C LINK COMMAREA WS-FRD-ACTION.
    Spec: toggle cycles N→F→R→F→R... (3-state cycle per COPAUS1C MARK-AUTH-FRAUD).
    current_fraud_status sent from client to validate client/server state sync.
    """

    current_fraud_status: str = Field(
        ...,
        description=(
            "Current fraud status known by client (N/F/R). "
            "Prevents double-toggle on page refresh."
        ),
    )

    @field_validator("current_fraud_status")
    @classmethod
    def validate_fraud_status(cls, v: str) -> str:
        """Replaces COPAUS1C: IF PA-FRAUD-CONFIRMED / ELSE set PA-FRAUD-CONFIRMED."""
        if v not in ("N", "F", "R"):
            raise ValueError("current_fraud_status must be N, F, or R")
        return v


class FraudToggleResponse(BaseModel):
    """
    Response for fraud toggle action.
    Returns updated state equivalent to COPAUS1C POPULATE-AUTH-DETAILS after MARK-AUTH-FRAUD.
    """

    auth_id: int
    previous_fraud_status: str
    new_fraud_status: str = Field(description="New value: F (if was N or R) or R (if was F)")
    fraud_status_display: str = Field(description="FRAUD/REMOVED/''")
    fraud_report_date: Optional[datetime] = None
    message: str = Field(description="WS-FRD-ACT-MSG: 'ADD SUCCESS' or 'UPDT SUCCESS'")


# ---------------------------------------------------------------------------
# Fraud log response schema
# ---------------------------------------------------------------------------


class AuthFraudLogResponse(BaseModel):
    """Maps DB2 CARDDEMO.AUTHFRDS row to API response."""

    log_id: int
    auth_id: int
    transaction_id: str
    card_number_masked: str
    account_id: int
    fraud_flag: str
    fraud_flag_display: str
    fraud_report_date: datetime
    auth_response_code: Optional[str] = None
    auth_amount: Optional[Decimal] = None
    merchant_name: Optional[str] = None
    merchant_id: Optional[str] = None
    logged_at: datetime

    model_config = {"from_attributes": True}
