"""
Pydantic request/response schemas for the Transaction Type module.

COBOL origin: COTRTUPC (add/update/delete) and COTRTLIC (list/browse).

Schema mapping to COBOL data structures:
  TransactionTypeCreateRequest  → COTRTUPC TTUP-CREATE-NEW-RECORD state (INSERT path)
  TransactionTypeUpdateRequest  → COTRTUPC TTUP-CHANGES-OK-NOT-CONFIRMED state (UPDATE path)
  TransactionTypeResponse       → DCLTRTYP DCLGEN fields (TR_TYPE + TR_DESCRIPTION)
  TransactionTypeListResponse   → COTRTLIC WS-CA-ALL-ROWS-OUT paginated output

Validation rules (from COTRTUPC 1200-EDIT-MAP-INPUTS):
  - type_code: required, numeric, non-zero (1210-EDIT-TRANTYPE + 1245-EDIT-NUM-REQD)
  - description: required, alphanumeric only, max 50 chars (1230-EDIT-ALPHANUM-REQD)

Optimistic locking (replaces COTRTLIC no-change detection and COTRTUPC 1205-COMPARE-OLD-NEW):
  - TransactionTypeUpdateRequest includes updated_at as the lock version
  - If the server's updated_at differs, the record was changed by another user
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class TransactionTypeCreateRequest(BaseModel):
    """
    Request body for POST /api/v1/transaction-types.

    COBOL origin: COTRTUPC TTUP-CREATE-NEW-RECORD state.
    Maps screen fields TRTYPCD (type code) and TRTYDSC (description) from CTRTUPA.

    Validation mirrors COTRTUPC 1200-EDIT-MAP-INPUTS:
      - 1210-EDIT-TRANTYPE: type code must be numeric and non-zero
      - 1230-EDIT-ALPHANUM-REQD: description must be alphanumeric
    """

    type_code: str = Field(
        ...,
        min_length=1,
        max_length=2,
        pattern=r"^[0-9]{1,2}$",
        description="TR_TYPE: 2-digit numeric code, e.g. '01'. Must be 01-99.",
        examples=["01", "02", "15"],
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r"^[A-Za-z0-9 ]+$",
        description="TR_DESCRIPTION: alphanumeric and spaces only, max 50 chars.",
        examples=["Purchase", "Bill Payment", "Cash Advance"],
    )

    @field_validator("type_code")
    @classmethod
    def validate_nonzero(cls, v: str) -> str:
        """
        COBOL origin: COTRTUPC 1210-EDIT-TRANTYPE non-zero check.
        IF TRANTYPE-NEW = 0 → SET FLG-TRANFILTER-NOT-OK, INPUT-ERROR.
        """
        if int(v) == 0:
            raise ValueError("Transaction type code must not be zero")
        return v

    @field_validator("description")
    @classmethod
    def validate_not_blank(cls, v: str) -> str:
        """
        COBOL origin: COTRTUPC 1230-EDIT-ALPHANUM-REQD required check.
        IF WS-EDIT-INPUT = SPACES → SET FLG-DESCRIPTION-NOT-OK, INPUT-ERROR.
        """
        if not v.strip():
            raise ValueError("Description cannot be blank")
        return v


class TransactionTypeUpdateRequest(BaseModel):
    """
    Request body for PUT /api/v1/transaction-types/{type_code}.

    COBOL origin: COTRTUPC TTUP-CHANGES-OK-NOT-CONFIRMED state (9600-WRITE-PROCESSING UPDATE).
    Only the description is editable — type_code is protected on both list and detail screens.

    Optimistic locking via optimistic_lock_version:
      Replaces COTRTLIC no-change detection (WS-DATACHANGED-FLAG) and
      COTRTUPC 1205-COMPARE-OLD-NEW paragraph. If the updated_at timestamp
      provided does not match the server value, another user has modified the record.
    """

    description: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r"^[A-Za-z0-9 ]+$",
        description="New TR_DESCRIPTION: alphanumeric and spaces only, max 50 chars.",
        examples=["Purchase Transaction", "Bill Payment"],
    )
    optimistic_lock_version: datetime = Field(
        ...,
        description=(
            "updated_at timestamp from GET response. "
            "Replaces COTRTLIC WS-DATACHANGED-FLAG no-change detection. "
            "If this does not match the server's current updated_at, returns 409."
        ),
    )

    @field_validator("description")
    @classmethod
    def validate_not_blank(cls, v: str) -> str:
        """COBOL origin: COTRTUPC 1230-EDIT-ALPHANUM-REQD blank check."""
        if not v.strip():
            raise ValueError("Description cannot be blank")
        return v


class TransactionTypeResponse(BaseModel):
    """
    Response body for all transaction type endpoints.

    COBOL origin: DCLTRTYP DCLGEN fields (DCL-TR-TYPE, DCL-TR-DESCRIPTION).
    Includes audit fields (created_at, updated_at) not in the original DB2 table.
    """

    type_code: str = Field(description="TR_TYPE: 2-digit numeric type code")
    description: str = Field(description="TR_DESCRIPTION: type description")
    created_at: datetime = Field(description="Row creation timestamp")
    updated_at: datetime = Field(
        description="Row last-modified timestamp — used as optimistic lock version"
    )

    model_config = {"from_attributes": True}


class TransactionTypeListResponse(BaseModel):
    """
    Paginated list response for GET /api/v1/transaction-types.

    COBOL origin: COTRTLIC 8000-READ-FORWARD / 8100-READ-BACKWARDS.
    Replaces the 7-row cursor-based paging with standard REST pagination.
    The COBOL program stored page state in COMMAREA; we use page/page_size query params.

    Default page_size=7 matches COTRTLIC WS-MAX-SCREEN-LINES=7.
    """

    items: list[TransactionTypeResponse]
    page: int = Field(description="Current page number (1-based)")
    page_size: int = Field(description="Items per page (default 7, max 7)")
    total_count: int = Field(description="Total matching records for pagination")
    has_next: bool = Field(description="Whether a next page exists (COTRTLIC CA-NEXT-PAGE-EXISTS)")
    has_previous: bool = Field(description="Whether a previous page exists")
    first_item_key: Optional[str] = Field(
        None,
        description="type_code of first item (COTRTLIC WS-CA-FIRST-TR-CODE — backward cursor anchor)",
    )
    last_item_key: Optional[str] = Field(
        None,
        description="type_code of last item (COTRTLIC WS-CA-LAST-TR-CODE — forward cursor anchor)",
    )
