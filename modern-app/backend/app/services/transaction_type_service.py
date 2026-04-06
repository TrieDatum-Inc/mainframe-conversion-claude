"""Business logic for the Transaction Type module.

Preserves COBOL business rules from:
  - COTRTLIC  (list, inline delete/update, pagination)
  - COTRTUPC  (add / update single type)
  - COBTUPDT  (batch 'A'/'U'/'D' operations)

All DB2 operations are translated to async SQLAlchemy ORM calls.
Business rules preserved:
  - type_code must be 2-char alphanumeric, non-blank (COTRTUPC validation)
  - description must be non-blank (COTRTUPC validation)
  - Delete cascade: categories are deleted with the parent type
  - Inline update: only saves if value has actually changed (WS-DATACHANGED-FLAG)
  - Duplicate type_code on insert → 409 Conflict (replaces DB2 SQLCODE -803)
"""

import math
import logging

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction_type import TransactionType, TransactionTypeCategory
from app.schemas.transaction_type import (
    CategoryCreate,
    CategoryUpdate,
    InlineSaveRequest,
    InlineSaveResponse,
    PaginatedTransactionTypes,
    TransactionTypeCreate,
    TransactionTypeDetailResponse,
    TransactionTypeResponse,
    TransactionTypeUpdate,
)

logger = logging.getLogger(__name__)

# Mirrors COTRTLIC: 7 rows per page (7+1 BMS rows, 1 protected overflow)
DEFAULT_PAGE_SIZE = 7


# ---------------------------------------------------------------------------
# Transaction Type CRUD
# ---------------------------------------------------------------------------


async def list_transaction_types(
    db: AsyncSession,
    *,
    type_code_filter: str | None = None,
    description_filter: str | None = None,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> PaginatedTransactionTypes:
    """Return a paginated list of transaction types.

    Mirrors COTRTLIC DB2 cursor:
      SELECT TR_TYPE, TR_DESCRIPTION FROM TRANSACTION_TYPE
      WHERE TR_TYPE LIKE :filter AND TR_DESCRIPTION LIKE :filter
      (optional WHERE clauses from TRTYPE / TRDESC screen filters)
    """
    base_query = _build_list_query(type_code_filter, description_filter)

    count_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    rows_result = await db.execute(
        base_query.order_by(TransactionType.type_code).offset(offset).limit(page_size)
    )
    rows = rows_result.scalars().all()

    return PaginatedTransactionTypes(
        items=[TransactionTypeResponse.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, math.ceil(total / page_size)),
    )


def _build_list_query(
    type_code_filter: str | None,
    description_filter: str | None,
):
    """Build the SELECT query with optional LIKE filters."""
    query = select(TransactionType)
    conditions = []
    if type_code_filter:
        conditions.append(
            TransactionType.type_code.ilike(f"%{type_code_filter}%")
        )
    if description_filter:
        conditions.append(
            TransactionType.description.ilike(f"%{description_filter}%")
        )
    if conditions:
        query = query.where(or_(*conditions))
    return query


async def get_transaction_type(
    db: AsyncSession, type_code: str
) -> TransactionTypeDetailResponse:
    """Fetch a single transaction type with its categories.

    Raises ValueError if not found (caller maps to HTTP 404).
    """
    row = await _fetch_type_or_raise(db, type_code)
    return TransactionTypeDetailResponse.model_validate(row)


async def create_transaction_type(
    db: AsyncSession, payload: TransactionTypeCreate
) -> TransactionTypeResponse:
    """Insert a new transaction type (COTRTUPC F6=Add / COBTUPDT 'A' record).

    Raises ValueError on duplicate type_code (DB2 SQLCODE -803 equivalent).
    """
    new_type = TransactionType(
        type_code=payload.type_code,
        description=payload.description,
    )
    db.add(new_type)
    try:
        await db.flush()
        await db.refresh(new_type)
    except IntegrityError as exc:
        await db.rollback()
        logger.warning("Duplicate type_code=%s rejected", payload.type_code)
        raise ValueError(
            f"Transaction type '{payload.type_code}' already exists"
        ) from exc
    return TransactionTypeResponse.model_validate(new_type)


async def update_transaction_type(
    db: AsyncSession, type_code: str, payload: TransactionTypeUpdate
) -> TransactionTypeResponse:
    """Update description for an existing type (COTRTUPC F5=Save / COBTUPDT 'U').

    Mirrors WS-DATACHANGED-FLAG: skip DB write if no change.
    Raises ValueError if type_code not found.
    """
    row = await _fetch_type_or_raise(db, type_code)
    if row.description == payload.description:
        # WS-DATACHANGED-FLAG = 'N' — no-op
        return TransactionTypeResponse.model_validate(row)
    row.description = payload.description
    await db.flush()
    await db.refresh(row)
    return TransactionTypeResponse.model_validate(row)


async def delete_transaction_type(
    db: AsyncSession, type_code: str
) -> None:
    """Delete a transaction type and cascade-delete its categories.

    Mirrors COTRTLIC inline-delete (TRTSEL column) and COBTUPDT 'D'.
    FK is CASCADE DELETE so categories are removed automatically.
    Raises ValueError if type not found.
    """
    row = await _fetch_type_or_raise(db, type_code)
    await db.delete(row)
    await db.flush()


async def save_inline_edits(
    db: AsyncSession, request: InlineSaveRequest
) -> InlineSaveResponse:
    """Batch update descriptions from COTRTLIC F10=Save (7-row inline edit).

    For each update in the request:
      - Skip if type_code not found (non-fatal, recorded in errors)
      - Skip if description unchanged (WS-DATACHANGED-FLAG = 'N')
      - Apply UPDATE otherwise
    """
    saved = 0
    errors: list[str] = []

    for item in request.updates:
        result = await db.execute(
            select(TransactionType).where(
                TransactionType.type_code == item.type_code
            )
        )
        row = result.scalars().first()
        if row is None:
            errors.append(f"Type '{item.type_code}' not found — skipped")
            continue
        if row.description == item.description:
            continue  # WS-DATACHANGED-FLAG = 'N'
        row.description = item.description
        saved += 1

    if saved:
        await db.flush()

    return InlineSaveResponse(saved=saved, errors=errors)


# ---------------------------------------------------------------------------
# Category CRUD
# ---------------------------------------------------------------------------


async def list_categories(
    db: AsyncSession, type_code: str
) -> list:
    """Return all categories for a given type_code.

    Raises ValueError if the parent type does not exist.
    """
    await _fetch_type_or_raise(db, type_code)
    result = await db.execute(
        select(TransactionTypeCategory)
        .where(TransactionTypeCategory.type_code == type_code)
        .order_by(TransactionTypeCategory.category_code)
    )
    return result.scalars().all()


async def create_category(
    db: AsyncSession, type_code: str, payload: CategoryCreate
) -> TransactionTypeCategory:
    """Add a new category to a transaction type.

    Raises ValueError on duplicate (type_code, category_code) or unknown type.
    """
    await _fetch_type_or_raise(db, type_code)
    new_cat = TransactionTypeCategory(
        type_code=type_code,
        category_code=payload.category_code,
        description=payload.description,
    )
    db.add(new_cat)
    try:
        await db.flush()
        await db.refresh(new_cat)
    except IntegrityError as exc:
        await db.rollback()
        raise ValueError(
            f"Category '{payload.category_code}' already exists for type '{type_code}'"
        ) from exc
    return new_cat


async def update_category(
    db: AsyncSession,
    type_code: str,
    category_code: str,
    payload: CategoryUpdate,
) -> TransactionTypeCategory:
    """Update a category's description.

    Raises ValueError if parent type or category not found.
    """
    await _fetch_type_or_raise(db, type_code)
    cat = await _fetch_category_or_raise(db, type_code, category_code)
    if cat.description == payload.description:
        return cat  # no change
    cat.description = payload.description
    await db.flush()
    await db.refresh(cat)
    return cat


async def delete_category(
    db: AsyncSession, type_code: str, category_code: str
) -> None:
    """Delete a single category.

    Raises ValueError if parent type or category not found.
    """
    await _fetch_type_or_raise(db, type_code)
    cat = await _fetch_category_or_raise(db, type_code, category_code)
    await db.delete(cat)
    await db.flush()


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


async def _fetch_type_or_raise(
    db: AsyncSession, type_code: str
) -> TransactionType:
    """Load a TransactionType row or raise ValueError (maps to HTTP 404)."""
    result = await db.execute(
        select(TransactionType).where(TransactionType.type_code == type_code)
    )
    row = result.scalars().first()
    if row is None:
        raise ValueError(f"Transaction type '{type_code}' not found")
    return row


async def _fetch_category_or_raise(
    db: AsyncSession, type_code: str, category_code: str
) -> TransactionTypeCategory:
    """Load a TransactionTypeCategory row or raise ValueError (maps to HTTP 404)."""
    result = await db.execute(
        select(TransactionTypeCategory).where(
            TransactionTypeCategory.type_code == type_code,
            TransactionTypeCategory.category_code == category_code,
        )
    )
    row = result.scalars().first()
    if row is None:
        raise ValueError(
            f"Category '{category_code}' not found for type '{type_code}'"
        )
    return row
