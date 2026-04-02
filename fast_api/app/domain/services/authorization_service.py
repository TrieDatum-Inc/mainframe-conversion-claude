"""
Authorization service — business logic layer.

Maps COPAUA0C (decision engine), COPAUS0C (summary list),
COPAUS1C (detail view), COPAUS2C (fraud flag).

COPAUA0C decision logic (preserved exactly from spec):
  1. Resolve card -> XREF -> account + customer
  2. Read account: credit_limit, curr_bal
  3. Read IMS PAUTSUM0: approved_amt (running total of pending auths)
  4. available = credit_limit - curr_bal - approved_amt
  5. IF available >= requested_amt -> APPROVE (response_code='00')
     ELSE -> DECLINE (response_code='51' insufficient funds)
  6. Write new PAUTDTL1 record (IMS ISRT)
  7. Update PAUTSUM0 running totals (IMS REPL or ISRT if new)
  8. CICS SYNCPOINT between each message (each auth is independent transaction)
"""

import uuid
from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError
from app.infrastructure.orm.authorization_orm import (
    AuthDetailORM,
    AuthFraudORM,
    AuthSummaryORM,
)
from app.infrastructure.repositories.account_repository import AccountRepository
from app.infrastructure.repositories.authorization_repository import (
    AuthDetailRepository,
    AuthFraudRepository,
    AuthSummaryRepository,
)
from app.infrastructure.repositories.card_repository import CardRepository
from app.schemas.authorization_schemas import (
    AuthDetailView,
    AuthSummaryListResponse,
    AuthSummaryView,
    AuthorizationRequest,
    AuthorizationResponse,
    FraudFlagRequest,
)


async def get_auth_summary_list(
    db: AsyncSession,
    account_id_filter: Optional[int] = None,
) -> AuthSummaryListResponse:
    """
    Authorization summary list (COPAUS0C).
    COPAU00 map: account ID input, list of pending authorization summaries.
    """
    repo = AuthSummaryRepository(db)
    items = await repo.list_all(account_id_filter=account_id_filter)

    views = [AuthSummaryView.model_validate(i) for i in items]
    return AuthSummaryListResponse(
        items=views,
        account_id_filter=account_id_filter,
        total_count=len(views),
    )


async def get_auth_detail(
    acct_id: int,
    auth_date: date,
    auth_time: time,
    db: AsyncSession,
) -> AuthDetailView:
    """
    Authorization detail view (COPAUS1C).
    COPAU01 map: reads CIPAUDTY segment by composite key.
    """
    repo = AuthDetailRepository(db)
    detail = await repo.get_by_key(auth_date, auth_time, acct_id)
    return AuthDetailView.model_validate(detail)


async def get_auth_details_for_account(
    acct_id: int,
    db: AsyncSession,
) -> list[AuthDetailView]:
    """Get all authorization details for an account (IMS GNP - get next parent)."""
    repo = AuthDetailRepository(db)
    details = await repo.get_for_account(acct_id)
    return [AuthDetailView.model_validate(d) for d in details]


async def flag_fraud(
    req: FraudFlagRequest,
    flagged_by: str,
    db: AsyncSession,
) -> dict:
    """
    Flag authorization as fraudulent (COPAUS2C).

    COPAUS2C:
    1. Check if AUTHFRDS record exists for card+date+time
    2. If not exists: EXEC SQL INSERT INTO CARDDEMO.AUTHFRDS
    3. If exists: EXEC SQL UPDATE CARDDEMO.AUTHFRDS SET ...
    4. Update IMS PAUTDTL1 fraud_flag field (IMS REPL)

    COPAUS1C LINK to COPAUS2C passes card_num + auth_date + auth_time.
    """
    fraud_repo = AuthFraudRepository(db)
    detail_repo = AuthDetailRepository(db)
    summary_repo = AuthSummaryRepository(db)

    # Get summary to find card_num
    summary = await summary_repo.get_by_acct_id(req.acct_id)

    # Get detail record to retrieve card_num
    detail = await detail_repo.get_by_key(req.auth_date, req.auth_time, req.acct_id)
    card_num = detail.card_num or ""

    # Check for existing AUTHFRDS record
    existing_fraud = await fraud_repo.get_by_card_and_date(
        card_num=card_num,
        auth_date=req.auth_date,
        auth_time=req.auth_time,
    )

    if existing_fraud is None:
        # COPAUS2C: INSERT new fraud record
        fraud_record = AuthFraudORM(
            card_num=card_num,
            acct_id=req.acct_id,
            auth_date=req.auth_date,
            auth_time=req.auth_time,
            fraud_reason=req.fraud_reason,
            flagged_by=flagged_by,
            fraud_status=req.fraud_status,
        )
        await fraud_repo.create(fraud_record)
    else:
        # COPAUS2C: UPDATE existing fraud record
        existing_fraud.fraud_reason = req.fraud_reason
        existing_fraud.fraud_status = req.fraud_status
        existing_fraud.flagged_by = flagged_by
        await fraud_repo.update(existing_fraud)

    # Update IMS PAUTDTL1 fraud_flag (IMS REPL)
    await detail_repo.update_fraud_flag(
        auth_date=req.auth_date,
        auth_time=req.auth_time,
        acct_id=req.acct_id,
        fraud_flag="Y",
    )

    return {
        "message": "Authorization flagged as fraudulent.",
        "acct_id": req.acct_id,
        "auth_date": str(req.auth_date),
        "auth_time": str(req.auth_time),
    }


async def process_authorization(
    req: AuthorizationRequest,
    db: AsyncSession,
) -> AuthorizationResponse:
    """
    Process authorization decision (COPAUA0C MQ engine).

    Decision algorithm from spec section COPAUA0C:
    1. Card -> XREF -> account + customer
    2. available = credit_limit - |curr_bal| - approved_amt (running)
    3. available >= requested_amt -> APPROVE ('00')
       else -> DECLINE ('51' = insufficient funds)
    4. Write PAUTDTL1 + update PAUTSUM0

    Note: COPAUA0C processes up to 500 messages per invocation.
    Each authorization is independent (CICS SYNCPOINT after each).
    """
    card_repo = CardRepository(db)
    acct_repo = AccountRepository(db)
    summary_repo = AuthSummaryRepository(db)
    detail_repo = AuthDetailRepository(db)

    # Step 1: Card -> XREF -> account
    card = await card_repo.get_by_card_num(req.card_num)
    xref = await card_repo.get_xref_by_card_num(req.card_num)
    if xref is None:
        raise ResourceNotFoundError("CardXref", req.card_num)

    account = await acct_repo.get_by_id(xref.acct_id)

    # Step 2: Get running approved amounts from PAUTSUM0
    summary = await summary_repo.get_by_acct_id_or_none(xref.acct_id)
    approved_running = summary.approved_amt if summary else Decimal("0.00")

    # Step 3: Decision logic (COPAUA0C core algorithm)
    # available_credit = credit_limit - current_balance - running_pending_approvals
    available_credit = account.credit_limit - abs(account.curr_bal) - approved_running

    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    auth_date = now_utc.date()
    auth_time = now_utc.time()
    auth_id = str(uuid.uuid4())[:10].upper()

    if available_credit >= req.requested_amt:
        # APPROVE
        response_code = "00"
        response_reason = "Approved"
        approved_amt = req.requested_amt
    else:
        # DECLINE (response code '51' = insufficient funds per COPAUA0C spec)
        response_code = "51"
        response_reason = (
            f"Insufficient credit. Available: {available_credit:.2f}, "
            f"Requested: {req.requested_amt:.2f}"
        )
        approved_amt = Decimal("0.00")

    # Generate transaction ID for this authorization
    from app.infrastructure.repositories.transaction_repository import TransactionRepository
    tran_repo = TransactionRepository(db)
    last_tran_id = await tran_repo.get_last_tran_id()
    from app.domain.services.transaction_service import _generate_tran_id
    tran_id = _generate_tran_id(last_tran_id)

    # Step 4a: Write PAUTDTL1 (IMS ISRT)
    detail = AuthDetailORM(
        auth_date=auth_date,
        auth_time=auth_time,
        acct_id=xref.acct_id,
        card_num=req.card_num,
        tran_id=tran_id,
        auth_id_code=auth_id,
        response_code=response_code,
        response_reason=response_reason[:25] if response_reason else None,
        approved_amt=approved_amt,
        auth_type=req.auth_type,
        match_status="N",
        fraud_flag="N",
    )
    await detail_repo.create(detail)

    # Step 4b: Update PAUTSUM0 (IMS REPL or ISRT)
    if summary is None:
        new_summary = AuthSummaryORM(
            acct_id=xref.acct_id,
            cust_id=xref.cust_id,
            credit_limit=account.credit_limit,
            cash_limit=account.cash_credit_limit,
            curr_bal=account.curr_bal,
            cash_bal=Decimal("0.00"),
            approved_count=1 if response_code == "00" else 0,
            approved_amt=approved_amt,
            declined_count=0 if response_code == "00" else 1,
            declined_amt=Decimal("0.00") if response_code == "00" else req.requested_amt,
        )
        await summary_repo.upsert(new_summary)
    else:
        if response_code == "00":
            summary.approved_count += 1
            summary.approved_amt += approved_amt
        else:
            summary.declined_count += 1
            summary.declined_amt += req.requested_amt
        summary.curr_bal = account.curr_bal
        await summary_repo.upsert(summary)

    return AuthorizationResponse(
        card_num=req.card_num,
        auth_id_code=auth_id,
        response_code=response_code,
        response_reason=response_reason,
        approved_amt=approved_amt,
        tran_id=tran_id if response_code == "00" else None,
    )
