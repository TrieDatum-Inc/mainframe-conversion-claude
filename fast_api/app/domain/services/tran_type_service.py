"""
Transaction Type service — business logic layer.

Maps COTRTLIC (list/select) and COTRTUPC (add/update/delete) programs.
These programs use DB2 directly (CARDDEMO.TRANSACTION_TYPE table).

COTRTLIC: cursor-based paginated list (7 rows/page), bidirectional
COTRTUPC: full CRUD with delete confirmation (action code 'D')
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.infrastructure.orm.transaction_orm import TransactionTypeORM
from app.infrastructure.repositories.transaction_repository import TransactionTypeRepository
from app.schemas.tran_type_schemas import (
    TransactionTypeCreateRequest,
    TransactionTypeListResponse,
    TransactionTypeUpdateRequest,
    TransactionTypeView,
)


async def list_transaction_types(
    db: AsyncSession,
    page_size: int = 7,
    start_type_cd: Optional[str] = None,
    type_cd_filter: Optional[str] = None,
    desc_filter: Optional[str] = None,
) -> TransactionTypeListResponse:
    """
    Paginated transaction type list (COTRTLIC).
    DB2 cursor: C-TR-TYPE-FORWARD / C-TR-TYPE-BACKWARD.
    7 rows per page per COTRTLIC WS-MAX-SCREEN-LINES.
    """
    repo = TransactionTypeRepository(db)
    rows, has_next = await repo.list_paginated(
        page_size=page_size,
        start_type_cd=start_type_cd,
        type_cd_filter=type_cd_filter,
        desc_filter=desc_filter,
    )

    from app.schemas.tran_type_schemas import TransactionTypeListItem
    items = [TransactionTypeListItem.model_validate(r) for r in rows]

    return TransactionTypeListResponse(
        items=items,
        page=1,
        has_next_page=has_next,
        first_type_cd=rows[0].tran_type_cd if rows else None,
        last_type_cd=rows[-1].tran_type_cd if rows else None,
        type_cd_filter=type_cd_filter,
        desc_filter=desc_filter,
    )


async def get_transaction_type(
    tran_type_cd: str,
    db: AsyncSession,
) -> TransactionTypeView:
    """Get a single transaction type record."""
    repo = TransactionTypeRepository(db)
    ttype = await repo.get_by_code(tran_type_cd)
    return TransactionTypeView.model_validate(ttype)


async def create_transaction_type(
    req: TransactionTypeCreateRequest,
    db: AsyncSession,
) -> TransactionTypeView:
    """
    Create transaction type (COTRTUPC INSERT).
    DB2: EXEC SQL INSERT INTO CARDDEMO.TRANSACTION_TYPE VALUES (:type_cd, :type_desc)
    """
    repo = TransactionTypeRepository(db)
    ttype = TransactionTypeORM(
        tran_type_cd=req.tran_type_cd.upper(),
        tran_type_desc=req.tran_type_desc,
    )
    created = await repo.create(ttype)
    return TransactionTypeView.model_validate(created)


async def update_transaction_type(
    tran_type_cd: str,
    req: TransactionTypeUpdateRequest,
    db: AsyncSession,
) -> TransactionTypeView:
    """
    Update transaction type description (COTRTUPC UPDATE).
    DB2: EXEC SQL UPDATE CARDDEMO.TRANSACTION_TYPE SET TYPE_DESC = :desc WHERE TYPE_CD = :cd
    """
    repo = TransactionTypeRepository(db)
    ttype = await repo.get_by_code(tran_type_cd)
    ttype.tran_type_desc = req.tran_type_desc
    updated = await repo.update(ttype)
    return TransactionTypeView.model_validate(updated)


async def delete_transaction_type(
    tran_type_cd: str,
    db: AsyncSession,
) -> dict:
    """
    Delete transaction type (COTRTLIC/COTRTUPC DELETE).
    DB2: EXEC SQL DELETE FROM CARDDEMO.TRANSACTION_TYPE WHERE TYPE_CD = :cd
    COTRTUPC: action code 'D' triggers delete with confirmation.
    """
    repo = TransactionTypeRepository(db)
    await repo.delete(tran_type_cd)
    return {
        "message": f"Transaction type '{tran_type_cd}' deleted successfully.",
        "tran_type_cd": tran_type_cd,
    }
