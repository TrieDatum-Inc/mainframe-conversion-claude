"""
Pydantic schemas for Transaction Type Management (DB2 CARDDEMO.TRANSACTION_TYPE).

Maps COTRTLIC (list/select) and COTRTUPC (add/update/delete) programs.

COTRTLIC: paginated list (7 rows), forward/backward cursor-based paging
COTRTUPC: add, update, delete operations on TRANSACTION_TYPE table
"""

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class TransactionTypeBase(BaseModel):
    """Transaction type fields from DB2 TRANSACTION_TYPE table."""
    tran_type_cd: str = Field(
        ...,
        min_length=1,
        max_length=2,
        description="Transaction type code (2-char) - TRAN-TYPE PIC X(02)",
    )
    tran_type_desc: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Transaction type description - TRAN-TYPE-DESC PIC X(50)",
    )

    @field_validator("tran_type_cd")
    @classmethod
    def uppercase_type_cd(cls, v: str) -> str:
        return v.strip().upper()


class TransactionTypeView(TransactionTypeBase):
    """Read-only transaction type view."""
    model_config = {"from_attributes": True}


class TransactionTypeListItem(BaseModel):
    """
    Single row in COTRTLIC transaction type list.
    COTRTLI BMS map shows type code and description per row.
    """
    tran_type_cd: str = Field(..., max_length=2)
    tran_type_desc: str = Field(..., max_length=50)

    model_config = {"from_attributes": True}


class TransactionTypeListResponse(BaseModel):
    """
    Paginated transaction type list (COTRTLIC).
    Uses DB2 cursor-based paging (C-TR-TYPE-FORWARD / C-TR-TYPE-BACKWARD).
    7 rows per page.
    """
    items: List[TransactionTypeListItem]
    page: int = Field(default=1, ge=1)
    has_next_page: bool = False
    first_type_cd: Optional[str] = None
    last_type_cd: Optional[str] = None
    type_cd_filter: Optional[str] = None
    desc_filter: Optional[str] = None


class TransactionTypeCreateRequest(TransactionTypeBase):
    """
    Create transaction type (COTRTUPC INSERT).
    Admin-only operation.
    """
    pass


class TransactionTypeUpdateRequest(BaseModel):
    """
    Update transaction type description (COTRTUPC UPDATE).
    Only description can be changed; type code is the key.
    """
    tran_type_desc: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="New transaction type description",
    )


class TransactionCategoryView(BaseModel):
    """Transaction category view (CARDDEMO.TRANSACTION_CATEGORY)."""
    tran_type_cd: str = Field(..., max_length=2)
    tran_cat_cd: int
    tran_cat_desc: str = Field(..., max_length=50)

    model_config = {"from_attributes": True}
