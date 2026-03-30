"""Transaction type router porting COBOL programs COTRN04C and TRNTYPE copybook.

COTRN04C manages the transaction type reference data stored in the TRANTYPF
VSAM KSDS file (TRNTYPE.CPY). The screen provides list, view, add, update,
and delete operations for the two-character type codes and their descriptions.

This router replaces that screen with REST endpoints. List and detail
endpoints require authentication; create, update, and delete require admin.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.transaction_type import (
    TransactionTypeCreate,
    TransactionTypeItem,
    TransactionTypeUpdate,
)
from app.services import transaction_type_service

router = APIRouter(tags=["transaction-types"])


@router.get("/", response_model=PaginatedResponse[TransactionTypeItem])
def list_transaction_types(
    type_filter: Optional[str] = Query(None, description="Filter by type code prefix"),
    desc_filter: Optional[str] = Query(None, description="Filter by description substring"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(7, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> PaginatedResponse[TransactionTypeItem]:
    """List transaction types with optional filters and pagination.

    Ports COBOL program COTRN04C list mode which uses STARTBR/READNEXT
    to browse the TRANTYPF VSAM KSDS file with page-size of 7 records.
    """
    return transaction_type_service.list_transaction_types(
        db,
        type_filter=type_filter,
        desc_filter=desc_filter,
        page=page,
        page_size=page_size,
    )


@router.get("/{type_code}", response_model=TransactionTypeItem)
def get_transaction_type(
    type_code: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> TransactionTypeItem:
    """Retrieve a specific transaction type by code.

    Ports COBOL program COTRN04C detail mode which reads a single record
    from the TRANTYPF VSAM file by type code key.
    """
    result = transaction_type_service.get_transaction_type(db, type_code)
    if result is None:
        from app.exceptions import RecordNotFoundError
        raise RecordNotFoundError("Transaction Type not found")
    return result


@router.post("/", response_model=MessageResponse)
def create_transaction_type(
    body: TransactionTypeCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> MessageResponse:
    """Create a new transaction type.

    Ports COBOL program COTRN04C add mode which writes a new record
    to the TRANTYPF VSAM file. Admin-only access.
    """
    return transaction_type_service.create_transaction_type(db, body.tran_type, body.tran_type_desc)


@router.put("/{type_code}", response_model=MessageResponse)
def update_transaction_type(
    type_code: str,
    body: TransactionTypeUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> MessageResponse:
    """Update an existing transaction type.

    Ports COBOL program COTRN04C update mode which validates and rewrites
    the record in the TRANTYPF VSAM file. Admin-only access.
    """
    return transaction_type_service.update_transaction_type(db, type_code, body.tran_type_desc)


@router.delete("/{type_code}", response_model=MessageResponse)
def delete_transaction_type(
    type_code: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> MessageResponse:
    """Delete a transaction type.

    Ports COBOL program COTRN04C delete mode which removes the record
    from the TRANTYPF VSAM file. Admin-only access.
    """
    return transaction_type_service.delete_transaction_type(db, type_code)
