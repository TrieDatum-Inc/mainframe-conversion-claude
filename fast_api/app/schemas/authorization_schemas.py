"""
Pydantic schemas for Authorization Subsystem endpoints.

Maps IMS-based authorization programs:
  COPAUS0C: pending auth summary list (IMS CIPAUSMY segments)
  COPAUS1C: pending auth detail view (IMS CIPAUDTY segment)
  COPAUS2C: fraud flag update (DB2 AUTHFRDS INSERT/UPDATE)
  COPAUA0C: MQ-triggered authorization decision engine

COPAUA0C authorization decision logic (preserved):
  1. Resolve card -> account via XREF
  2. Read account master for credit limits
  3. Read IMS PAUTSUM0 for running approved amounts
  4. Compute: available = credit_limit - curr_bal - approved_amt (running)
  5. If available >= requested_amt -> APPROVE (response code '00')
     Else -> DECLINE (response code '51' = insufficient funds)
"""

from datetime import date, time
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class AuthSummaryView(BaseModel):
    """
    Authorization Summary view (COPAUS0C / IMS CIPAUSMY).
    Account-level aggregate of pending authorizations.
    """
    acct_id: int
    cust_id: int
    auth_status: Optional[str] = None
    credit_limit: Decimal
    cash_limit: Decimal
    curr_bal: Decimal
    cash_bal: Decimal
    approved_count: int
    approved_amt: Decimal
    declined_count: int
    declined_amt: Decimal

    model_config = {"from_attributes": True}


class AuthSummaryListResponse(BaseModel):
    """
    Paginated authorization summary list (COPAUS0C).
    COPAU00 BMS map - account ID input, list of authorizations.
    """
    items: List[AuthSummaryView]
    account_id_filter: Optional[int] = None
    total_count: int = 0


class AuthDetailView(BaseModel):
    """
    Authorization Detail view (COPAUS1C / IMS CIPAUDTY).
    Single pending authorization record with fraud flag.
    """
    auth_date: date
    auth_time: time
    acct_id: int
    card_num: Optional[str] = None
    tran_id: Optional[str] = None
    auth_id_code: Optional[str] = None
    response_code: Optional[str] = None
    response_reason: Optional[str] = None
    approved_amt: Decimal
    auth_type: Optional[str] = None
    match_status: Optional[str] = None
    fraud_flag: str = "N"

    model_config = {"from_attributes": True}


class FraudFlagRequest(BaseModel):
    """
    Fraud flag update request (COPAUS2C).
    Operator flags an authorization record as fraudulent.

    COPAUS2C:
    - If no existing AUTHFRDS record: INSERT new fraud record
    - If existing record: UPDATE fraud_flag and reason
    """
    acct_id: int = Field(..., gt=0)
    auth_date: date
    auth_time: time
    fraud_reason: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Reason for fraud flagging",
    )
    fraud_status: str = Field(
        default="P",
        max_length=1,
        description="Fraud status code ('P'=pending, 'C'=confirmed, 'R'=resolved)",
    )


class AuthorizationRequest(BaseModel):
    """
    Authorization decision request (COPAUA0C MQ message equivalent).

    Maps CCPAURQY.cpy MQ request message fields.
    COPAUA0C processes up to 500 messages per invocation.
    """
    card_num: str = Field(
        ...,
        min_length=16,
        max_length=16,
        description="Card number to authorize",
    )
    requested_amt: Decimal = Field(
        ...,
        gt=Decimal("0"),
        description="Amount to authorize",
    )
    auth_type: str = Field(
        default="P",
        max_length=1,
        description="Authorization type",
    )
    merchant_id: Optional[int] = None
    merchant_name: Optional[str] = Field(default=None, max_length=50)


class AuthorizationResponse(BaseModel):
    """
    Authorization decision response (COPAUA0C MQ reply message equivalent).
    Maps CCPAURLY.cpy fields.
    """
    card_num: str
    auth_id_code: str
    response_code: str = Field(
        description="'00'=approved, '51'=insufficient funds, other=declined"
    )
    response_reason: str
    approved_amt: Decimal
    tran_id: Optional[str] = None
