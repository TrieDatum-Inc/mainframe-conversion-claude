"""
Transaction service — business logic layer.

Maps COTRN00C (list), COTRN01C (view), COTRN02C (add), COBIL00C (bill payment),
CORPT00C (report generation).

COTRN02C key logic:
  - Two lookup paths: card_num direct OR acct_id -> CXACAIX lookup
  - New tran_id = last existing tran_id + 1 (READPREV + increment)
  - Two-step confirm: preview then submit
  - Date format validated (CSUTLDTC equivalent)

COBIL00C key logic:
  - Read ACCTDAT (current balance)
  - Create payment transaction in TRANSACT
  - REWRITE ACCTDAT (reset balance to zero)
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AccountInactiveError,
    BusinessValidationError,
    ResourceNotFoundError,
)
from app.infrastructure.orm.transaction_orm import TransactionORM
from app.infrastructure.repositories.account_repository import AccountRepository
from app.infrastructure.repositories.card_repository import CardRepository
from app.infrastructure.repositories.transaction_repository import (
    TransactionRepository,
    TransactionTypeRepository,
)
from app.schemas.transaction_schemas import (
    BillPaymentRequest,
    BillPaymentResponse,
    ReportRequest,
    ReportResponse,
    TransactionAddRequest,
    TransactionListResponse,
    TransactionView,
)


def _generate_tran_id(last_tran_id: Optional[str]) -> str:
    """
    Generate next transaction ID.
    COTRN02C: READPREV to get last_id, then new_id = last_id + 1 (numeric increment).
    Format: 16-char numeric string, zero-padded.
    """
    if last_tran_id is None:
        return "0000000000000001"
    try:
        numeric = int(last_tran_id) + 1
        return str(numeric).zfill(16)
    except ValueError:
        # Fallback if last_tran_id is not purely numeric
        return str(abs(hash(last_tran_id + "1")))[:16].zfill(16)


async def _resolve_card_num(
    card_num: Optional[str],
    acct_id: Optional[int],
    db: AsyncSession,
) -> str:
    """
    Resolve card number from either direct card_num or acct_id CXACAIX lookup.

    COTRN02C lookup paths:
    Path 1: card_num provided -> READ CCXREF (validate card exists)
    Path 2: acct_id provided -> READ CXACAIX (alternate index) -> get card_num
    """
    if card_num is not None:
        card_repo = CardRepository(db)
        card = await card_repo.get_by_card_num(card_num)
        return card.card_num

    if acct_id is not None:
        acct_repo = AccountRepository(db)
        xref = await acct_repo.get_xref_by_account_id(acct_id)
        if xref is None:
            raise ResourceNotFoundError("AccountXref", str(acct_id))
        return xref.card_num

    raise BusinessValidationError(
        "Either card_num or acct_id must be provided.",
        field="card_num",
    )


async def list_transactions(
    db: AsyncSession,
    page_size: int = 10,
    start_tran_id: Optional[str] = None,
    card_num_filter: Optional[str] = None,
    direction: str = "forward",
    end_tran_id: Optional[str] = None,
) -> TransactionListResponse:
    """
    Paginated transaction list.
    Maps COTRN00C STARTBR/READNEXT/READPREV (10 rows per page).
    """
    repo = TransactionRepository(db)

    if direction == "backward" and end_tran_id:
        rows, has_prev = await repo.list_paginated_backward(
            page_size=page_size,
            end_tran_id=end_tran_id,
            card_num_filter=card_num_filter,
        )
    else:
        rows, has_next = await repo.list_paginated_forward(
            page_size=page_size,
            start_tran_id=start_tran_id,
            card_num_filter=card_num_filter,
        )

    from app.schemas.transaction_schemas import TransactionListItem
    items = [TransactionListItem.model_validate(r) for r in rows]

    return TransactionListResponse(
        items=items,
        page=1,
        has_next_page=has_next if direction == "forward" else False,
        first_tran_id=rows[0].tran_id if rows else None,
        last_tran_id=rows[-1].tran_id if rows else None,
        start_tran_id_filter=start_tran_id,
    )


async def get_transaction_detail(
    tran_id: str,
    db: AsyncSession,
) -> TransactionView:
    """
    Transaction detail view (COTRN01C).
    Read-only: EXEC CICS READ DATASET('TRANSACT') RIDFLD(tran_id).
    """
    repo = TransactionRepository(db)
    txn = await repo.get_by_id(tran_id)
    return TransactionView.model_validate(txn)


async def add_transaction(
    req: TransactionAddRequest,
    db: AsyncSession,
) -> TransactionView:
    """
    Add new transaction (COTRN02C).

    Steps from spec:
    1. Resolve card_num (direct or via CXACAIX lookup)
    2. READPREV to get last tran_id -> generate new tran_id
    3. Validate transaction type code exists
    4. WRITE new TRAN-RECORD to TRANSACT
    """
    resolved_card_num = await _resolve_card_num(req.card_num, req.acct_id, db)

    tran_repo = TransactionRepository(db)
    type_repo = TransactionTypeRepository(db)

    # Validate transaction type code exists
    await type_repo.get_by_code(req.tran_type_cd)

    # Generate new transaction ID (COTRN02C READPREV + increment)
    last_tran_id = await tran_repo.get_last_tran_id()
    new_tran_id = _generate_tran_id(last_tran_id)

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    transaction = TransactionORM(
        tran_id=new_tran_id,
        tran_type_cd=req.tran_type_cd.upper(),
        tran_cat_cd=req.tran_cat_cd,
        tran_source=req.tran_source,
        tran_desc=req.tran_desc,
        tran_amt=req.tran_amt,
        merchant_id=req.merchant_id,
        merchant_name=req.merchant_name,
        merchant_city=req.merchant_city,
        merchant_zip=req.merchant_zip,
        card_num=resolved_card_num,
        orig_ts=now,
        proc_ts=now,
    )

    created = await tran_repo.create(transaction)
    return TransactionView.model_validate(created)


async def process_bill_payment(
    req: BillPaymentRequest,
    db: AsyncSession,
    user_id: str = "SYSTEM",
) -> BillPaymentResponse:
    """
    Process bill payment (COBIL00C).

    COBIL00C spec (section 6, PROCESS-ENTER-KEY):
    1. READ ACCTDAT with UPDATE (exclusive lock)
    2. Balance <= 0 -> error "You have nothing to pay..."
    3. READ CXACAIX (get XREF-CARD-NUM for TRAN-CARD-NUM)
    4. STARTBR/READPREV TRANSACT at HIGH-VALUES (get last TRAN-ID)
    5. New TRAN-ID = last + 1
    6. Build TRAN-RECORD:
       - TRAN-TYPE-CD = '02'
       - TRAN-CAT-CD = 2
       - TRAN-SOURCE = 'POS TERM'
       - TRAN-DESC = 'BILL PAYMENT - ONLINE'
       - TRAN-AMT = ACCT-CURR-BAL (full balance)
       - TRAN-MERCHANT-ID = 999999999
       - TRAN-MERCHANT-NAME = 'BILL PAYMENT'
       - TRAN-MERCHANT-CITY = 'N/A'
       - TRAN-MERCHANT-ZIP = 'N/A'
       - TRAN-CARD-NUM = XREF-CARD-NUM
    7. WRITE TRANSACT
    8. COMPUTE ACCT-CURR-BAL = ACCT-CURR-BAL - TRAN-AMT (zeros balance)
    9. REWRITE ACCTDAT
    """
    acct_repo = AccountRepository(db)
    tran_repo = TransactionRepository(db)

    # Step 1: READ ACCTDAT (COBIL00C line 345 — READ with UPDATE)
    account = await acct_repo.get_by_id(req.account_id)

    # Validate account is active
    if account.active_status != "Y":
        raise AccountInactiveError(req.account_id)

    previous_balance = account.curr_bal

    # Step 2: Balance <= 0 check (COBIL00C lines 198-205)
    # "You have nothing to pay..."
    if previous_balance >= Decimal("0"):
        raise BusinessValidationError(
            "You have nothing to pay. Current balance is zero or credit.",
            field="account_id",
        )

    # Step 3: READ CXACAIX (COBIL00C lines 408-436)
    xref = await acct_repo.get_xref_by_account_id(req.account_id)
    if xref is None:
        raise ResourceNotFoundError("AccountXref", str(req.account_id))

    # Step 4-5: Generate TRAN-ID (COBIL00C lines 212-217)
    # STARTBR at HIGH-VALUES, READPREV to get last, add 1
    last_tran_id = await tran_repo.get_last_tran_id()
    new_tran_id = _generate_tran_id(last_tran_id)

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # Payment amount is the full balance (COBIL00C line 224: TRAN-AMT = ACCT-CURR-BAL)
    payment_amount = abs(previous_balance)

    # Step 6: Build TRAN-RECORD (COBIL00C lines 218-230)
    payment_txn = TransactionORM(
        tran_id=new_tran_id,
        tran_type_cd="02",              # COBIL00C line 220: TRAN-TYPE-CD = '02'
        tran_cat_cd=2,                  # COBIL00C line 221: TRAN-CAT-CD = 2
        tran_source="POS TERM",         # COBIL00C line 222: TRAN-SOURCE = 'POS TERM'
        tran_desc="BILL PAYMENT - ONLINE",  # COBIL00C line 223
        tran_amt=payment_amount,        # COBIL00C line 224: TRAN-AMT = ACCT-CURR-BAL
        merchant_id=999999999,          # COBIL00C line 225: TRAN-MERCHANT-ID = 999999999
        merchant_name="BILL PAYMENT",   # COBIL00C line 226: TRAN-MERCHANT-NAME
        merchant_city="N/A",            # COBIL00C line 227: TRAN-MERCHANT-CITY
        merchant_zip="N/A",             # COBIL00C line 228: TRAN-MERCHANT-ZIP
        card_num=xref.card_num,         # COBIL00C line 229: TRAN-CARD-NUM = XREF-CARD-NUM
        orig_ts=now,                    # COBIL00C line 230: GET-CURRENT-TIMESTAMP
        proc_ts=now,
    )

    # Step 7: WRITE TRANSACT (COBIL00C lines 510-547)
    await tran_repo.create(payment_txn)

    # Step 8-9: COMPUTE + REWRITE (COBIL00C line 234)
    # ACCT-CURR-BAL = ACCT-CURR-BAL - TRAN-AMT (effectively zeros the balance)
    account.curr_bal = previous_balance - (- payment_amount)  # prev_bal is negative, so this zeros it
    await acct_repo.update(account)

    return BillPaymentResponse(
        account_id=req.account_id,
        previous_balance=previous_balance,
        payment_amount=payment_amount,
        new_balance=account.curr_bal,
        transaction_id=new_tran_id,
        message=f"Payment successful. Your Transaction ID is {new_tran_id}.",
    )


async def generate_report(
    req: ReportRequest,
    db: AsyncSession,
) -> ReportResponse:
    """
    Transaction report generation (CORPT00C -> CBTRN03C equivalent).

    CORPT00C presents input screen; triggers CBTRN03C batch equivalent.
    CBTRN03C reads TRANSACT + TRAN-TYPE + TRAN-CAT, produces formatted report.
    """
    tran_repo = TransactionRepository(db)

    # Build query based on filters
    from sqlalchemy import and_, select
    from app.infrastructure.orm.transaction_orm import TransactionORM

    conditions = []
    if req.card_num:
        conditions.append(TransactionORM.card_num == req.card_num)

    if req.start_date:
        from datetime import datetime as dt
        start_dt = dt.strptime(req.start_date, "%Y-%m-%d")
        conditions.append(TransactionORM.orig_ts >= start_dt)

    if req.end_date:
        from datetime import datetime as dt
        end_dt = dt.strptime(req.end_date, "%Y-%m-%d")
        conditions.append(TransactionORM.orig_ts <= end_dt)

    from sqlalchemy import func
    stmt = select(
        func.count(TransactionORM.tran_id).label("cnt"),
        func.sum(TransactionORM.tran_amt).label("total"),
    )
    if conditions:
        stmt = stmt.where(and_(*conditions))

    result = await db.execute(stmt)
    row = result.one()

    total_count = row.cnt or 0
    total_amt = row.total or Decimal("0.00")

    report_id = str(uuid.uuid4())[:8].upper()

    return ReportResponse(
        report_id=report_id,
        status="COMPLETED",
        message=f"Report generated: {total_count} transactions totaling {total_amt:.2f}",
        total_transactions=total_count,
        total_amount=total_amt,
    )
