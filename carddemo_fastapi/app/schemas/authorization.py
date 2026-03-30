"""Authorization schemas matching COBOL IMS authorization subsystem copybooks.

- AuthSummaryItem: from CIPAUSMY.cpy pending authorization summary segment
- AuthDetailItem: from CIPAUDTY.cpy pending authorization detail segment
- AuthDecisionRequest: from CCPAURQY.cpy pending authorization request
- AuthDecisionResponse: from CCPAURLY.cpy pending authorization response
- MarkFraudRequest: fraud marking input based on CIPAUDTY.cpy PA-AUTH-FRAUD
- MarkFraudResponse: fraud marking result
"""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class AuthSummaryItem(BaseModel):
    """Pending authorization summary matching CIPAUSMY.cpy segment fields."""

    pa_acct_id: int = Field(..., description="Account ID (PA-ACCT-ID PIC S9(11) COMP-3)")
    pa_cust_id: int = Field(..., description="Customer ID (PA-CUST-ID PIC 9(09))")
    pa_auth_status: str = Field(
        ..., max_length=1, description="Authorization status (PA-AUTH-STATUS PIC X(01))"
    )
    pa_credit_limit: Decimal = Field(
        ..., description="Credit limit (PA-CREDIT-LIMIT PIC S9(09)V99)"
    )
    pa_cash_limit: Decimal = Field(
        ..., description="Cash limit (PA-CASH-LIMIT PIC S9(09)V99)"
    )
    pa_credit_balance: Decimal = Field(
        ..., description="Credit balance (PA-CREDIT-BALANCE PIC S9(09)V99)"
    )
    pa_cash_balance: Decimal = Field(
        ..., description="Cash balance (PA-CASH-BALANCE PIC S9(09)V99)"
    )
    pa_account_status_1: Optional[str] = Field(None, description="Account status 1")
    pa_account_status_2: Optional[str] = Field(None, description="Account status 2")
    pa_account_status_3: Optional[str] = Field(None, description="Account status 3")
    pa_account_status_4: Optional[str] = Field(None, description="Account status 4")
    pa_account_status_5: Optional[str] = Field(None, description="Account status 5")
    pa_approved_auth_cnt: int = Field(
        ..., description="Approved authorization count (PA-APPROVED-AUTH-CNT PIC S9(04))"
    )
    pa_declined_auth_cnt: int = Field(
        ..., description="Declined authorization count (PA-DECLINED-AUTH-CNT PIC S9(04))"
    )
    pa_approved_auth_amt: Optional[Decimal] = Field(
        None, description="Approved authorization amount"
    )
    pa_declined_auth_amt: Optional[Decimal] = Field(
        None, description="Declined authorization amount"
    )


class AuthDetailItem(BaseModel):
    """Pending authorization detail matching CIPAUDTY.cpy segment fields.

    Includes all raw fields plus formatted date/time and human-readable
    approved/declined indicator with decline reason text.
    """

    # --- Key fields ---
    pa_auth_date: str = Field(
        ..., max_length=6, description="Authorization date (PA-AUTH-ORIG-DATE PIC X(06))"
    )
    pa_auth_time: str = Field(
        ..., max_length=6, description="Authorization time (PA-AUTH-ORIG-TIME PIC X(06))"
    )
    pa_card_num: str = Field(
        ..., max_length=16, description="Card number (PA-CARD-NUM PIC X(16))"
    )
    pa_auth_type: str = Field(
        ..., max_length=4, description="Authorization type (PA-AUTH-TYPE PIC X(04))"
    )
    pa_card_expiry_date: str = Field(
        ..., max_length=4, description="Card expiry date (PA-CARD-EXPIRY-DATE PIC X(04))"
    )

    # --- Message fields ---
    pa_message_type: str = Field(
        ..., max_length=6, description="Message type (PA-MESSAGE-TYPE PIC X(06))"
    )
    pa_message_source: str = Field(
        ..., max_length=6, description="Message source (PA-MESSAGE-SOURCE PIC X(06))"
    )

    # --- Response fields ---
    pa_auth_id_code: str = Field(
        ..., max_length=6, description="Authorization ID code (PA-AUTH-ID-CODE PIC X(06))"
    )
    pa_auth_resp_code: str = Field(
        ...,
        max_length=2,
        description="Response code: '00'=approved (PA-AUTH-RESP-CODE PIC X(02))",
    )
    pa_auth_resp_reason: str = Field(
        ..., max_length=4, description="Response reason code (PA-AUTH-RESP-REASON PIC X(04))"
    )

    # --- Transaction fields ---
    pa_processing_code: int = Field(
        ..., description="Processing code (PA-PROCESSING-CODE PIC 9(06))"
    )
    pa_transaction_amt: Decimal = Field(
        ..., description="Transaction amount (PA-TRANSACTION-AMT PIC S9(10)V99)"
    )
    pa_approved_amt: Decimal = Field(
        ..., description="Approved amount (PA-APPROVED-AMT PIC S9(10)V99)"
    )

    # --- Merchant fields ---
    pa_merchant_category_code: str = Field(
        ..., max_length=4, description="Merchant category (PA-MERCHANT-CATAGORY-CODE PIC X(04))"
    )
    pa_acqr_country_code: str = Field(
        ..., max_length=3, description="Acquirer country code (PA-ACQR-COUNTRY-CODE PIC X(03))"
    )
    pa_pos_entry_mode: int = Field(
        ..., description="POS entry mode (PA-POS-ENTRY-MODE PIC 9(02))"
    )
    pa_merchant_id: str = Field(
        ..., max_length=15, description="Merchant ID (PA-MERCHANT-ID PIC X(15))"
    )
    pa_merchant_name: str = Field(
        ..., max_length=22, description="Merchant name (PA-MERCHANT-NAME PIC X(22))"
    )
    pa_merchant_city: str = Field(
        ..., max_length=13, description="Merchant city (PA-MERCHANT-CITY PIC X(13))"
    )
    pa_merchant_state: str = Field(
        ..., max_length=2, description="Merchant state (PA-MERCHANT-STATE PIC X(02))"
    )
    pa_merchant_zip: str = Field(
        ..., max_length=9, description="Merchant ZIP (PA-MERCHANT-ZIP PIC X(09))"
    )

    # --- Status fields ---
    pa_transaction_id: str = Field(
        ..., max_length=15, description="Transaction ID (PA-TRANSACTION-ID PIC X(15))"
    )
    pa_match_status: str = Field(
        ...,
        max_length=1,
        description="Match status: P=pending, D=declined, E=expired, M=matched (PA-MATCH-STATUS)",
    )
    pa_auth_fraud: str = Field(
        ...,
        max_length=1,
        description="Fraud indicator: F=fraud confirmed, R=fraud removed (PA-AUTH-FRAUD)",
    )
    pa_fraud_rpt_date: str = Field(
        ..., max_length=8, description="Fraud report date (PA-FRAUD-RPT-DATE PIC X(08))"
    )

    # --- Formatted / derived fields ---
    formatted_date: Optional[str] = Field(
        None, description="Human-readable formatted date"
    )
    formatted_time: Optional[str] = Field(
        None, description="Human-readable formatted time"
    )
    approved_declined_indicator: Optional[str] = Field(
        None, description="'Approved' or 'Declined' text based on PA-AUTH-RESP-CODE"
    )
    decline_reason_text: Optional[str] = Field(
        None, description="Human-readable decline reason based on PA-AUTH-RESP-REASON"
    )


class AuthDecisionRequest(BaseModel):
    """Authorization decision request matching CCPAURQY.cpy fields.

    Submitted to the authorization service for approval/decline decision.
    """

    card_num: str = Field(
        ..., max_length=16, description="Card number (PA-RQ-CARD-NUM PIC X(16))"
    )
    auth_type: str = Field(
        ..., max_length=4, description="Authorization type (PA-RQ-AUTH-TYPE PIC X(04))"
    )
    card_expiry_date: str = Field(
        ..., max_length=4, description="Card expiry MMYY (PA-RQ-CARD-EXPIRY-DATE PIC X(04))"
    )
    transaction_amt: Decimal = Field(
        ..., description="Transaction amount (PA-RQ-TRANSACTION-AMT PIC +9(10).99)"
    )
    merchant_category_code: Optional[str] = Field(
        None, max_length=4, description="Merchant category (PA-RQ-MERCHANT-CATAGORY-CODE)"
    )
    acqr_country_code: Optional[str] = Field(
        None, max_length=3, description="Acquirer country code (PA-RQ-ACQR-COUNTRY-CODE)"
    )
    pos_entry_mode: Optional[int] = Field(
        None, description="POS entry mode (PA-RQ-POS-ENTRY-MODE PIC 9(02))"
    )
    merchant_id: Optional[str] = Field(
        None, max_length=15, description="Merchant ID (PA-RQ-MERCHANT-ID PIC X(15))"
    )
    merchant_name: Optional[str] = Field(
        None, max_length=22, description="Merchant name (PA-RQ-MERCHANT-NAME PIC X(22))"
    )
    merchant_city: Optional[str] = Field(
        None, max_length=13, description="Merchant city (PA-RQ-MERCHANT-CITY PIC X(13))"
    )
    merchant_state: Optional[str] = Field(
        None, max_length=2, description="Merchant state (PA-RQ-MERCHANT-STATE PIC X(02))"
    )
    merchant_zip: Optional[str] = Field(
        None, max_length=9, description="Merchant ZIP (PA-RQ-MERCHANT-ZIP PIC X(09))"
    )


class AuthDecisionResponse(BaseModel):
    """Authorization decision response matching CCPAURLY.cpy fields."""

    card_num: str = Field(
        ..., max_length=16, description="Card number (PA-RL-CARD-NUM PIC X(16))"
    )
    transaction_id: str = Field(
        ..., max_length=15, description="Transaction ID (PA-RL-TRANSACTION-ID PIC X(15))"
    )
    auth_id_code: str = Field(
        ..., max_length=6, description="Authorization ID code (PA-RL-AUTH-ID-CODE PIC X(06))"
    )
    auth_resp_code: str = Field(
        ...,
        max_length=2,
        description="Response code: '00'=approved (PA-RL-AUTH-RESP-CODE PIC X(02))",
    )
    auth_resp_reason: str = Field(
        ..., max_length=4, description="Response reason (PA-RL-AUTH-RESP-REASON PIC X(04))"
    )
    approved_amt: Decimal = Field(
        ..., description="Approved amount (PA-RL-APPROVED-AMT PIC +9(10).99)"
    )


class MarkFraudRequest(BaseModel):
    """Request to mark or remove fraud on a pending authorization.

    Based on PA-AUTH-FRAUD field in CIPAUDTY.cpy with 88-level values
    PA-FRAUD-CONFIRMED='F' and PA-FRAUD-REMOVED='R'.
    """

    card_num: str = Field(..., max_length=16, description="Card number")
    auth_ts: str = Field(
        ...,
        description="Authorization timestamp in ISO format, identifies the specific auth record",
    )
    acct_id: int = Field(..., description="Account ID")
    cust_id: int = Field(..., description="Customer ID")
    action: str = Field(
        ...,
        max_length=1,
        description="Action: 'F' to report fraud, 'R' to remove fraud flag",
    )


class MarkFraudResponse(BaseModel):
    """Fraud marking result."""

    message: str = Field(..., description="Result message")
    status: str = Field(..., description="Status: 'success' or 'failed'")
