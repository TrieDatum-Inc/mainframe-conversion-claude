"""Transaction router porting COBOL programs COTRN00C, COTRN01C, and COTRN02C.

COTRN00C lists transactions with STARTBR/READNEXT pagination over the
TRANSACT VSAM file (CVTRA05Y.cpy), with optional transaction ID filter.

COTRN01C displays full transaction detail for a selected transaction.

COTRN02C handles new transaction entry with a two-step confirm flow
(preview then confirm with flag 'Y').

This router replaces all three screens with REST endpoints.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.transaction import (
    TransactionCreate,
    TransactionDetail,
    TransactionListItem,
)
from app.services import transaction_service

router = APIRouter(tags=["transactions"])


@router.get("/", response_model=PaginatedResponse[TransactionListItem])
def list_transactions(
    tran_id_filter: Optional[str] = Query(None, description="Filter by transaction ID prefix"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> PaginatedResponse[TransactionListItem]:
    """List transactions with optional filter and pagination.

    Ports COBOL program COTRN00C which uses STARTBR/READNEXT to browse
    the TRANSACT VSAM KSDS file with page-size of 10 records per screen.
    """
    return transaction_service.list_transactions(
        db, tran_id_filter=tran_id_filter, page=page, page_size=page_size
    )


@router.get("/{tran_id}", response_model=TransactionDetail)
def get_transaction(
    tran_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> TransactionDetail:
    """Retrieve full detail for a specific transaction.

    Ports COBOL program COTRN01C which reads the TRANSACT VSAM file
    by transaction ID and displays all transaction fields.
    """
    return transaction_service.get_transaction(db, tran_id)


@router.post("/", response_model=MessageResponse)
def add_transaction(
    body: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> MessageResponse:
    """Create a new transaction.

    Ports COBOL program COTRN02C which handles the two-step add flow:
    first preview (confirm='N'), then confirm (confirm='Y'). The service
    validates card/account, generates a transaction ID, and writes to
    the TRANSACT VSAM file.
    """
    return transaction_service.add_transaction(
        db,
        card_num=body.card_num,
        acct_id=body.acct_id,
        tran_type_cd=body.tran_type_cd,
        tran_cat_cd=body.tran_cat_cd,
        tran_source=body.tran_source,
        tran_desc=body.tran_desc,
        tran_amt=body.tran_amt,
        merchant_id=body.tran_merchant_id,
        merchant_name=body.tran_merchant_name,
        merchant_city=body.tran_merchant_city,
        merchant_zip=body.tran_merchant_zip,
        confirm=body.confirm,
    )
