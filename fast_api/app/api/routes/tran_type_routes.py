"""
Transaction Type routes (Admin Only, DB2 TRANSACTION_TYPE table).
Maps COTRTLIC (CTLI) and COTRTUPC programs.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_admin
from app.core.exceptions import DuplicateKeyError, ResourceNotFoundError
from app.domain.services.tran_type_service import (
    create_transaction_type,
    delete_transaction_type,
    get_transaction_type,
    list_transaction_types,
    update_transaction_type,
)
from app.infrastructure.database import get_db
from app.schemas.auth_schemas import UserContext
from app.schemas.tran_type_schemas import (
    TransactionTypeCreateRequest,
    TransactionTypeListResponse,
    TransactionTypeUpdateRequest,
    TransactionTypeView,
)

router = APIRouter(
    prefix="/transaction-types",
    tags=["Transaction Types (COTRTLIC/COTRTUPC, Admin Only)"],
)


@router.get(
    "",
    response_model=TransactionTypeListResponse,
    status_code=status.HTTP_200_OK,
    summary="List transaction types (COTRTLIC - CTLI, Admin Only)",
    description="""
    Paginated transaction type list. Admin only.
    7 rows per page (COTRTLIC WS-MAX-SCREEN-LINES).

    COTRTLIC uses DB2 forward/backward cursors:
    - C-TR-TYPE-FORWARD: SELECT WHERE type_cd >= :start ORDER BY type_cd ASC
    - C-TR-TYPE-BACKWARD: SELECT WHERE type_cd <= :end ORDER BY type_cd DESC
    """,
)
async def list_tran_types(
    start_type_cd: Optional[str] = Query(None, max_length=2),
    type_cd_filter: Optional[str] = Query(None, max_length=2),
    desc_filter: Optional[str] = Query(None, max_length=50),
    page_size: int = Query(7, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_admin),
) -> TransactionTypeListResponse:
    return await list_transaction_types(
        db=db,
        page_size=page_size,
        start_type_cd=start_type_cd,
        type_cd_filter=type_cd_filter,
        desc_filter=desc_filter,
    )


@router.get(
    "/{tran_type_cd}",
    response_model=TransactionTypeView,
    status_code=status.HTTP_200_OK,
    summary="Get transaction type (Admin Only)",
)
async def get_tran_type(
    tran_type_cd: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_admin),
) -> TransactionTypeView:
    try:
        return await get_transaction_type(tran_type_cd, db)
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "CDERR013", "message": exc.message},
        )


@router.post(
    "",
    response_model=TransactionTypeView,
    status_code=status.HTTP_201_CREATED,
    summary="Create transaction type (COTRTUPC INSERT, Admin Only)",
    description="DB2: INSERT INTO CARDDEMO.TRANSACTION_TYPE",
)
async def create_tran_type(
    request: TransactionTypeCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_admin),
) -> TransactionTypeView:
    try:
        return await create_transaction_type(request, db)
    except DuplicateKeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "CDERR070", "message": exc.message},
        )


@router.put(
    "/{tran_type_cd}",
    response_model=TransactionTypeView,
    status_code=status.HTTP_200_OK,
    summary="Update transaction type (COTRTUPC UPDATE, Admin Only)",
    description="DB2: UPDATE CARDDEMO.TRANSACTION_TYPE SET TYPE_DESC = :desc WHERE TYPE_CD = :cd",
)
async def update_tran_type(
    tran_type_cd: str,
    request: TransactionTypeUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_admin),
) -> TransactionTypeView:
    try:
        return await update_transaction_type(tran_type_cd, request, db)
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "CDERR013", "message": exc.message},
        )


@router.delete(
    "/{tran_type_cd}",
    status_code=status.HTTP_200_OK,
    summary="Delete transaction type (COTRTLIC/COTRTUPC DELETE, Admin Only)",
    description="DB2: DELETE FROM CARDDEMO.TRANSACTION_TYPE WHERE TYPE_CD = :cd",
)
async def delete_tran_type(
    tran_type_cd: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_admin),
) -> dict:
    try:
        return await delete_transaction_type(tran_type_cd, db)
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "CDERR013", "message": exc.message},
        )
