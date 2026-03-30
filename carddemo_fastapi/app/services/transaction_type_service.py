"""Transaction type management service ported from COTRTLIC and COTRTUPC.

COTRTLIC: Browse/list transaction types with optional filters on
          type code and description.  DB2 cursor pagination.
          BMS page size = 7.
COTRTUPC: CRUD operations on transaction type records including
          create (PF5), update, and delete (PF4) with FK checks
          against transaction_categories.
"""

from sqlalchemy.orm import Session

from app.models.transaction_category import TransactionCategory
from app.models.transaction_type import TransactionType
from app.exceptions import (
    DuplicateRecordError,
    RecordNotFoundError,
    ValidationError,
)


def list_transaction_types(
    db: Session,
    type_filter: str | None = None,
    desc_filter: str | None = None,
    page: int = 1,
    page_size: int = 7,
) -> dict:
    """Paginated transaction type list, ported from COTRTLIC.

    Supports optional filters:
    - type_filter: exact match on tran_type
    - desc_filter: LIKE '%filter%' on tran_type_desc

    Page size 7 matches BMS screen layout.

    Returns:
        PaginatedResponse-compatible dict.
    """
    query = db.query(TransactionType)

    if type_filter:
        query = query.filter(TransactionType.tran_type == type_filter)

    if desc_filter:
        query = query.filter(
            TransactionType.tran_type_desc.ilike(f"%{desc_filter}%")
        )

    total_count = query.count()

    offset = (page - 1) * page_size
    types = (
        query.order_by(TransactionType.tran_type)
        .offset(offset)
        .limit(page_size)
        .all()
    )

    has_next_page = (offset + page_size) < total_count

    return {
        "items": [
            {
                "tran_type": t.tran_type,
                "tran_type_desc": t.tran_type_desc,
            }
            for t in types
        ],
        "page": page,
        "page_size": page_size,
        "total_count": total_count,
        "has_next_page": has_next_page,
    }


def get_transaction_type(db: Session, type_code: str) -> dict:
    """Get a single transaction type, ported from COTRTUPC fetch.

    If not found, returns None to allow the caller to proceed
    with creation logic.

    Returns:
        dict with tran_type and tran_type_desc, or None if not found.
    """
    ttype = (
        db.query(TransactionType)
        .filter(TransactionType.tran_type == type_code)
        .first()
    )

    if not ttype:
        return None

    return {
        "tran_type": ttype.tran_type,
        "tran_type_desc": ttype.tran_type_desc,
    }


def create_transaction_type(
    db: Session,
    type_code: str,
    description: str,
) -> dict:
    """Create a new transaction type, ported from COTRTUPC PF5 create.

    Checks for duplicates before inserting.

    Returns:
        dict with success message.

    Raises:
        DuplicateRecordError: If type_code already exists.
    """
    existing = (
        db.query(TransactionType)
        .filter(TransactionType.tran_type == type_code)
        .first()
    )
    if existing:
        raise DuplicateRecordError("Transaction Type already exists")

    new_type = TransactionType(
        tran_type=type_code,
        tran_type_desc=description,
    )
    db.add(new_type)
    db.commit()
    db.refresh(new_type)

    return {"message": f"Transaction Type {type_code} has been created"}


def update_transaction_type(
    db: Session,
    type_code: str,
    description: str,
) -> dict:
    """Update a transaction type description, ported from COTRTUPC update.

    Includes change detection -- if the description is unchanged,
    raises a validation error.

    Returns:
        dict with success message.

    Raises:
        RecordNotFoundError: If type_code not found.
        ValidationError: If no changes detected.
    """
    ttype = (
        db.query(TransactionType)
        .filter(TransactionType.tran_type == type_code)
        .first()
    )

    if not ttype:
        raise RecordNotFoundError("Transaction Type not found")

    if ttype.tran_type_desc == description:
        raise ValidationError("No changes detected")

    ttype.tran_type_desc = description
    db.commit()
    db.refresh(ttype)

    return {"message": f"Transaction Type {type_code} has been updated"}


def delete_transaction_type(db: Session, type_code: str) -> dict:
    """Delete a transaction type, ported from COTRTUPC PF4 delete.

    Checks for foreign key references in transaction_categories
    before deleting.

    Returns:
        dict with success message.

    Raises:
        RecordNotFoundError: If type_code not found.
        ValidationError: If categories reference this type.
    """
    ttype = (
        db.query(TransactionType)
        .filter(TransactionType.tran_type == type_code)
        .first()
    )

    if not ttype:
        raise RecordNotFoundError("Transaction Type not found")

    # Check FK reference in transaction_categories
    category_count = (
        db.query(TransactionCategory)
        .filter(TransactionCategory.tran_type_cd == type_code)
        .count()
    )
    if category_count > 0:
        raise ValidationError("Cannot delete - categories exist")

    db.delete(ttype)
    db.commit()

    return {"message": f"Transaction Type {type_code} has been deleted"}
