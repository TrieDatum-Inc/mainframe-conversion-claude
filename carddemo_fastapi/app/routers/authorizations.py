"""Authorization router porting COBOL batch programs and DALYTRAN copybook screens.

The authorization subsystem in CardDemo is primarily batch-driven:
- CBACT04C processes daily authorization transactions and fraud detection
- Pending authorization summary/detail records aggregate per-account stats

This router exposes the pending authorization data and fraud-marking
functionality as REST endpoints, replacing the batch report views and
the CICS admin fraud-flagging interface.
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.schemas.authorization import (
    AuthDecisionRequest,
    AuthDecisionResponse,
    AuthSummaryItem,
    MarkFraudRequest,
    MarkFraudResponse,
)
from app.schemas.common import PaginatedResponse
from app.services import authorization_service

router = APIRouter(tags=["authorizations"])


@router.get("/summary", response_model=PaginatedResponse[AuthSummaryItem])
def list_auth_summary(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(5, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> PaginatedResponse[AuthSummaryItem]:
    """List pending authorization summaries with pagination.

    Ports the pending authorization summary view derived from the
    DALYTRAN batch processing. Returns per-account aggregate statistics
    including approved/declined counts and amounts.
    """
    return authorization_service.list_auth_summary(db, page=page, page_size=page_size)


@router.post("/decide", response_model=AuthDecisionResponse)
def process_authorization(
    body: AuthDecisionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> AuthDecisionResponse:
    """Process an authorization decision request.

    Ports COBOL program COPAUA0C which receives authorization requests,
    performs card/account/summary lookups, makes an approve/decline
    credit decision, and writes the result to the pending authorization
    summary and detail records.
    """
    return authorization_service.process_authorization(
        db,
        card_num=body.card_num,
        auth_type=body.auth_type,
        card_expiry_date=body.card_expiry_date,
        transaction_amt=body.transaction_amt,
        merchant_category_code=body.merchant_category_code,
        acqr_country_code=body.acqr_country_code,
        pos_entry_mode=body.pos_entry_mode,
        merchant_id=body.merchant_id,
        merchant_name=body.merchant_name,
        merchant_city=body.merchant_city,
        merchant_state=body.merchant_state,
        merchant_zip=body.merchant_zip,
    )


@router.get("/{acct_id}/detail")
def get_auth_detail(
    acct_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Retrieve authorization detail for a specific account.

    Ports the pending authorization detail view which shows the account
    summary record along with all individual authorization detail records.
    Returns a dict containing 'summary' and 'details' keys.
    """
    return authorization_service.get_auth_detail(db, acct_id)


@router.post("/fraud", response_model=MarkFraudResponse)
def mark_fraud(
    body: MarkFraudRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> MarkFraudResponse:
    """Mark an authorization record as fraudulent.

    Ports the fraud-flagging functionality from COBOL batch program
    CBACT04C. Sets the auth_fraud flag and fraud_rpt_date on the
    specified authorization record. Admin-only access.
    """
    return authorization_service.mark_fraud(
        db,
        card_num=body.card_num,
        auth_ts=body.auth_ts,
        acct_id=body.acct_id,
        cust_id=body.cust_id,
        action=body.action,
    )
