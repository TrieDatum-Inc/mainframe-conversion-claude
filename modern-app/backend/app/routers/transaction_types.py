"""HTTP routes for the Transaction Type module.

All endpoints require admin authentication (require_admin dependency).

COBOL → REST mapping:
  COTRTLIC cursor browse  -> GET  /api/transaction-types
  COTRTLIC F10=Save       -> POST /api/transaction-types/inline-save
  COTRTLIC inline delete  -> DELETE /api/transaction-types/{type_code}
  COTRTUPC F6=Add         -> POST /api/transaction-types
  COTRTUPC F5=Save        -> PUT  /api/transaction-types/{type_code}
  COBTUPDT 'A'            -> POST /api/transaction-types
  COBTUPDT 'U'            -> PUT  /api/transaction-types/{type_code}
  COBTUPDT 'D'            -> DELETE /api/transaction-types/{type_code}

HTTP status codes:
  200 OK        — successful read/update
  201 Created   — successful insert
  204 No Content — successful delete
  400 Bad Request — validation failure
  404 Not Found  — type_code / category_code not found
  409 Conflict   — duplicate type_code or category_code
  403 Forbidden  — non-admin caller
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import require_admin
from app.schemas.transaction_type import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    InlineSaveRequest,
    InlineSaveResponse,
    PaginatedTransactionTypes,
    TransactionTypeCreate,
    TransactionTypeDetailResponse,
    TransactionTypeResponse,
    TransactionTypeUpdate,
)
from app.services import transaction_type_service as svc

router = APIRouter(
    prefix="/api/transaction-types",
    tags=["Transaction Types"],
)

# ---------------------------------------------------------------------------
# Transaction Type endpoints
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=PaginatedTransactionTypes,
    summary="List transaction types (COTRTLIC)",
)
async def list_transaction_types(
    type_code: str | None = Query(None, max_length=2, description="Filter by type code"),
    description: str | None = Query(None, max_length=50, description="Filter by description"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(7, ge=1, le=100, description="Rows per page (default 7 = COTRTLIC page)"),
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
) -> PaginatedTransactionTypes:
    """Paginated list of transaction types with optional filters.

    Mirrors COTRTLIC DB2 cursor SELECT with optional WHERE on TR_TYPE / TR_DESCRIPTION.
    Default page_size=7 matches the 7-row BMS screen.
    """
    return await svc.list_transaction_types(
        db,
        type_code_filter=type_code,
        description_filter=description,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/inline-save",
    response_model=InlineSaveResponse,
    summary="Batch inline-edit save (COTRTLIC F10=Save)",
)
async def inline_save(
    request: InlineSaveRequest,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
) -> InlineSaveResponse:
    """Save one or more inline-edited descriptions from the list view.

    Mirrors COTRTLIC F10=Save: loops over all 7 rows and applies UPDATE
    only when description has actually changed (WS-DATACHANGED-FLAG).
    """
    return await svc.save_inline_edits(db, request)


@router.get(
    "/{type_code}",
    response_model=TransactionTypeDetailResponse,
    summary="Get single transaction type with categories (COTRTUPC read)",
)
async def get_transaction_type(
    type_code: str,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
) -> TransactionTypeDetailResponse:
    """Fetch a single transaction type and its associated categories."""
    return await _run_or_raise(svc.get_transaction_type(db, type_code.upper()))


@router.post(
    "",
    response_model=TransactionTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create transaction type (COTRTUPC F6=Add / COBTUPDT 'A')",
)
async def create_transaction_type(
    payload: TransactionTypeCreate,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
) -> TransactionTypeResponse:
    """Create a new transaction type.

    Rejects blank or non-alphanumeric type_code (COTRTUPC field validation).
    Returns HTTP 409 if type_code already exists (DB2 SQLCODE -803 equivalent).
    """
    return await _run_or_conflict(svc.create_transaction_type(db, payload))


@router.put(
    "/{type_code}",
    response_model=TransactionTypeResponse,
    summary="Update transaction type description (COTRTUPC F5=Save / COBTUPDT 'U')",
)
async def update_transaction_type(
    type_code: str,
    payload: TransactionTypeUpdate,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
) -> TransactionTypeResponse:
    """Update a transaction type's description.

    No-ops if description is unchanged (WS-DATACHANGED-FLAG = 'N').
    Returns HTTP 404 if type_code does not exist.
    """
    return await _run_or_raise(
        svc.update_transaction_type(db, type_code.upper(), payload)
    )


@router.delete(
    "/{type_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete transaction type (COTRTLIC inline delete / COBTUPDT 'D')",
)
async def delete_transaction_type(
    type_code: str,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
) -> None:
    """Delete a transaction type and cascade-delete all its categories.

    Mirrors COTRTLIC inline-delete (TRTSEL selector) and COBTUPDT 'D' record.
    FK CASCADE ensures categories are removed automatically.
    Returns HTTP 404 if type_code does not exist.
    """
    await _run_or_raise(svc.delete_transaction_type(db, type_code.upper()))


# ---------------------------------------------------------------------------
# Category endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/{type_code}/categories",
    response_model=list[CategoryResponse],
    summary="List categories for a transaction type",
)
async def list_categories(
    type_code: str,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
) -> list[CategoryResponse]:
    """Return all categories for the given transaction type."""
    cats = await _run_or_raise(svc.list_categories(db, type_code.upper()))
    return [CategoryResponse.model_validate(c) for c in cats]


@router.post(
    "/{type_code}/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a category to a transaction type",
)
async def create_category(
    type_code: str,
    payload: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
) -> CategoryResponse:
    """Add a new category to the given transaction type.

    Returns HTTP 404 if type_code not found.
    Returns HTTP 409 if (type_code, category_code) already exists.
    """
    cat = await _run_or_conflict(svc.create_category(db, type_code.upper(), payload))
    return CategoryResponse.model_validate(cat)


@router.put(
    "/{type_code}/categories/{category_code}",
    response_model=CategoryResponse,
    summary="Update a category's description",
)
async def update_category(
    type_code: str,
    category_code: str,
    payload: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
) -> CategoryResponse:
    """Update the description of a specific category."""
    cat = await _run_or_raise(
        svc.update_category(db, type_code.upper(), category_code.upper(), payload)
    )
    return CategoryResponse.model_validate(cat)


@router.delete(
    "/{type_code}/categories/{category_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a category",
)
async def delete_category(
    type_code: str,
    category_code: str,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
) -> None:
    """Delete a specific category from a transaction type."""
    await _run_or_raise(
        svc.delete_category(db, type_code.upper(), category_code.upper())
    )


# ---------------------------------------------------------------------------
# Error-handling helpers
# ---------------------------------------------------------------------------


async def _run_or_raise(coro):
    """Await coro; convert ValueError → HTTP 404."""
    try:
        return await coro
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


async def _run_or_conflict(coro):
    """Await coro; convert ValueError with 'already exists' → HTTP 409, else 404."""
    try:
        return await coro
    except ValueError as exc:
        msg = str(exc)
        if "already exists" in msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=msg
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=msg
        ) from exc
