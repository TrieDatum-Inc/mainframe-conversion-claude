"""Pydantic schemas for the Transaction Type module.

Request/response validation mirrors COBOL field constraints:
  - type_code: 2 chars, alphanumeric, non-blank (COTRTLIC / COTRTUPC validation)
  - description: max 50 chars, non-blank
  - category_code: max 4 chars, non-blank
"""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ---------------------------------------------------------------------------
# Constants — mirrors COBOL field lengths
# ---------------------------------------------------------------------------
TYPE_CODE_LENGTH = 2
DESCRIPTION_MAX_LENGTH = 50
CATEGORY_CODE_MAX_LENGTH = 4

_ALPHANUMERIC_RE = re.compile(r"^[A-Za-z0-9]+$")


def _validate_type_code(value: str) -> str:
    """Enforce COBOL rule: TR_TYPE must be 2-char alphanumeric, non-blank."""
    stripped = value.strip()
    if len(stripped) == 0:
        raise ValueError("type_code must not be blank")
    if len(value) != TYPE_CODE_LENGTH:
        raise ValueError(f"type_code must be exactly {TYPE_CODE_LENGTH} characters")
    if not _ALPHANUMERIC_RE.match(value):
        raise ValueError("type_code must be alphanumeric (A-Z, a-z, 0-9)")
    return value.upper()


def _validate_description(value: str) -> str:
    """Enforce COBOL rule: TR_DESCRIPTION must be non-blank, max 50 chars."""
    stripped = value.strip()
    if len(stripped) == 0:
        raise ValueError("description must not be blank")
    if len(value) > DESCRIPTION_MAX_LENGTH:
        raise ValueError(
            f"description must not exceed {DESCRIPTION_MAX_LENGTH} characters"
        )
    return value.strip()


def _validate_category_code(value: str) -> str:
    """Enforce COBOL rule: TR_CAT must be non-blank, max 4 chars."""
    stripped = value.strip()
    if len(stripped) == 0:
        raise ValueError("category_code must not be blank")
    if len(value) > CATEGORY_CODE_MAX_LENGTH:
        raise ValueError(
            f"category_code must not exceed {CATEGORY_CODE_MAX_LENGTH} characters"
        )
    return value.upper().strip()


# ---------------------------------------------------------------------------
# Category schemas
# ---------------------------------------------------------------------------


class CategoryBase(BaseModel):
    """Shared fields for category create/update."""

    category_code: str = Field(
        ...,
        min_length=1,
        max_length=CATEGORY_CODE_MAX_LENGTH,
        description="Up to 4-char category code (TR_CAT)",
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=DESCRIPTION_MAX_LENGTH,
        description="Category description (TR_CAT_DESCRIPTION)",
    )

    @field_validator("category_code")
    @classmethod
    def validate_category_code(cls, v: str) -> str:
        return _validate_category_code(v)

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        return _validate_description(v)


class CategoryCreate(CategoryBase):
    """Schema for creating a new category (POST body)."""


class CategoryUpdate(BaseModel):
    """Schema for updating a category's description (PUT body)."""

    description: str = Field(
        ...,
        min_length=1,
        max_length=DESCRIPTION_MAX_LENGTH,
        description="Updated category description",
    )

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        return _validate_description(v)


class CategoryResponse(CategoryBase):
    """Schema returned from GET / POST / PUT category endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    type_code: str
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Transaction Type schemas
# ---------------------------------------------------------------------------


class TransactionTypeBase(BaseModel):
    """Shared fields for transaction type create/update."""

    description: str = Field(
        ...,
        min_length=1,
        max_length=DESCRIPTION_MAX_LENGTH,
        description="Transaction type description (TR_DESCRIPTION)",
    )

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        return _validate_description(v)


class TransactionTypeCreate(TransactionTypeBase):
    """Schema for creating a new transaction type (POST body)."""

    type_code: str = Field(
        ...,
        min_length=TYPE_CODE_LENGTH,
        max_length=TYPE_CODE_LENGTH,
        description="2-char alphanumeric code (TR_TYPE)",
    )

    @field_validator("type_code")
    @classmethod
    def validate_type_code(cls, v: str) -> str:
        return _validate_type_code(v)


class TransactionTypeUpdate(TransactionTypeBase):
    """Schema for updating a transaction type's description (PUT body)."""


class TransactionTypeResponse(TransactionTypeBase):
    """Schema returned from list/get endpoints — without categories."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    type_code: str
    created_at: datetime
    updated_at: datetime


class TransactionTypeDetailResponse(TransactionTypeResponse):
    """Schema returned from GET /transaction-types/{type_code} — includes categories."""

    categories: list[CategoryResponse] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Inline-edit / batch-save schema (mirrors COTRTLIC F10=Save pattern)
# ---------------------------------------------------------------------------


class InlineUpdate(BaseModel):
    """A single inline description edit for the list-view Save All action."""

    type_code: str = Field(..., min_length=TYPE_CODE_LENGTH, max_length=TYPE_CODE_LENGTH)
    description: str = Field(..., min_length=1, max_length=DESCRIPTION_MAX_LENGTH)

    @field_validator("type_code")
    @classmethod
    def validate_type_code(cls, v: str) -> str:
        return _validate_type_code(v)

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        return _validate_description(v)


class InlineSaveRequest(BaseModel):
    """Batch inline-edit payload — mirrors COTRTLIC F10=Save (7 rows at a time)."""

    updates: list[InlineUpdate] = Field(
        ...,
        min_length=1,
        description="One or more inline description edits",
    )


class InlineSaveResponse(BaseModel):
    """Result of a batch inline-edit save."""

    saved: int = Field(..., description="Number of records successfully updated")
    errors: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Pagination envelope
# ---------------------------------------------------------------------------


class PaginatedTransactionTypes(BaseModel):
    """Paginated list response for GET /transaction-types."""

    items: list[TransactionTypeResponse]
    total: int
    page: int
    page_size: int
    pages: int
