"""
Transaction routes.
Maps COTRN00C (CT00), COTRN01C (CT01), COTRN02C (CT02),
COBIL00C (CB00), CORPT00C (CR00) programs.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_user
from app.core.exceptions import (
    AccountInactiveError,
    BusinessValidationError,
    DuplicateKeyError,
    ResourceNotFoundError,
)
from app.domain.services.transaction_service import (
    add_transaction,
    generate_report,
    get_transaction_detail,
    list_transactions,
    process_bill_payment,
)
from app.infrastructure.database import get_db
from app.schemas.auth_schemas import UserContext
from app.schemas.transaction_schemas import (
    BillPaymentRequest,
    BillPaymentResponse,
    ReportRequest,
    ReportResponse,
    TransactionAddRequest,
    TransactionListResponse,
    TransactionView,
)

router = APIRouter(prefix="/transactions", tags=["Transactions (COTRN00C/01C/02C)"])
billing_router = APIRouter(prefix="/billing", tags=["Billing (COBIL00C)"])
report_router = APIRouter(prefix="/reports", tags=["Reports (CORPT00C)"])


@router.get(
    "",
    response_model=TransactionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List transactions (COTRN00C - CT00)",
    description="""
    Paginated transaction list. 10 rows per page.

    COTRN00C COMMAREA state:
    - CDEMO-CT00-TRNID-FIRST / CDEMO-CT00-TRNID-LAST (page boundaries)
    - CDEMO-CT00-PAGE-NUM (current page)
    - CDEMO-CT00-NEXT-PAGE-FLG (has more pages)

    PF7=backward, PF8=forward navigation via direction parameter.
    """,
)
async def list_transactions_endpoint(
    start_tran_id: Optional[str] = Query(None, max_length=16),
    end_tran_id: Optional[str] = Query(None, max_length=16),
    card_num: Optional[str] = Query(None, max_length=16),
    direction: str = Query("forward", description="'forward' or 'backward'"),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_user),
) -> TransactionListResponse:
    return await list_transactions(
        db=db,
        page_size=page_size,
        start_tran_id=start_tran_id,
        card_num_filter=card_num,
        direction=direction,
        end_tran_id=end_tran_id,
    )


@router.get(
    "/{tran_id}",
    response_model=TransactionView,
    status_code=status.HTTP_200_OK,
    summary="View transaction (COTRN01C - CT01)",
    description="Read-only transaction detail view.",
)
async def get_transaction(
    tran_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_user),
) -> TransactionView:
    try:
        return await get_transaction_detail(tran_id, db)
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "CDERR013", "message": exc.message},
        )


@router.post(
    "",
    response_model=TransactionView,
    status_code=status.HTTP_201_CREATED,
    summary="Add transaction (COTRN02C - CT02)",
    description="""
    Add a new transaction to the TRANSACT file.

    COTRN02C business logic:
    1. Resolve card_num from card_num or acct_id (via CXACAIX lookup)
    2. Validate transaction type exists in TRANSACTION_TYPE table
    3. Auto-generate tran_id: READPREV last ID + 1
    4. WRITE new TRAN-RECORD to TRANSACT

    Two lookup paths:
    - card_num: direct card lookup (READ CCXREF)
    - acct_id: alternate index lookup (READ CXACAIX)
    """,
)
async def add_transaction_endpoint(
    request: TransactionAddRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_user),
) -> TransactionView:
    try:
        return await add_transaction(request, db)
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "CDERR013", "message": exc.message},
        )
    except BusinessValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error_code": "CDERR422", "message": exc.message},
        )
    except DuplicateKeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "CDERR070", "message": exc.message},
        )


@billing_router.post(
    "/pay",
    response_model=BillPaymentResponse,
    status_code=status.HTTP_200_OK,
    summary="Bill payment (COBIL00C - CB00)",
    description="""
    Process account bill payment.

    COBIL00C flow:
    1. READ ACCTDAT (current balance)
    2. Validate payment amount
    3. WRITE TRANSACT (type='PR', payment record)
    4. REWRITE ACCTDAT (update balance)

    Business rules:
    - Account must be active
    - Payment amount must be positive
    - Payment amount must not exceed current balance
    """,
)
async def pay_bill(
    request: BillPaymentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_user),
) -> BillPaymentResponse:
    try:
        return await process_bill_payment(request, db, current_user.user_id)
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "CDERR013", "message": exc.message},
        )
    except AccountInactiveError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "CDBIZ001", "message": exc.message},
        )
    except BusinessValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error_code": "CDERR422", "message": exc.message},
        )


@report_router.post(
    "/generate",
    response_model=ReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate report (CORPT00C - CR00)",
    description="""
    Transaction report generation (maps CORPT00C + CBTRN03C).

    CORPT00C presents the report parameters screen;
    actual report is generated by CBTRN03C batch equivalent.

    Filters:
    - start_date / end_date: date range
    - account_id: specific account
    - card_num: specific card
    """,
)
async def generate_report_endpoint(
    request: ReportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_user),
) -> ReportResponse:
    return await generate_report(request, db)
