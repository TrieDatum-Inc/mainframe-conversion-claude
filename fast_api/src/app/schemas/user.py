"""Pydantic request/response schemas for the User Administration module.

Validation rules mirror COBOL field constraints exactly, with COBOL bugs fixed:
  - COUSR01C PROCESS-ENTER-KEY: all fields mandatory (enforced here via Field(...))
  - user_type: COBOL only checked NOT SPACES — here we enforce Literal['A', 'U']
  - password: COBOL stored plaintext PIC X(08) — max 8 chars input, stored as bcrypt
  - user_id: PIC X(08) → max 8 chars
  - first_name / last_name: PIC X(20) → max 20 chars
"""
import re
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Shared field type aliases
# ---------------------------------------------------------------------------

# PIC X(08) — VSAM KSDS key; COUSR01C USERIDI
UserId = Annotated[
    str,
    Field(
        min_length=1,
        max_length=8,
        description="User ID (max 8 characters — maps to PIC X(08) SEC-USR-ID)",
        examples=["admin001"],
    ),
]

# PIC X(20) — SEC-USR-FNAME / SEC-USR-LNAME
NameField = Annotated[
    str,
    Field(
        min_length=1,
        max_length=20,
        description="Name field (max 20 characters — maps to PIC X(20))",
    ),
]

# PIC X(08) in COBOL but we accept plaintext, hash server-side
PasswordField = Annotated[
    str,
    Field(
        min_length=1,
        max_length=72,  # bcrypt processes max 72 bytes of input
        description="Password (plaintext input, stored as bcrypt hash)",
    ),
]

# PIC X(01) — 'A'=Admin, 'U'=User
# COBOL bug fix: COUSR01C only validated NOT SPACES; we enforce the set strictly
UserType = Annotated[
    Literal["A", "U"],
    Field(description="User type: 'A'=Admin, 'U'=Regular user"),
]


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class UserCreate(BaseModel):
    """Request body for POST /api/users (COUSR01C — Add User).

    Validation order mirrors COUSR01C PROCESS-ENTER-KEY validation sequence:
    1. first_name — 'First Name can NOT be empty...'
    2. last_name  — 'Last Name can NOT be empty...'
    3. user_id    — 'User ID can NOT be empty...'
    4. password   — 'Password can NOT be empty...'
    5. user_type  — 'User Type can NOT be empty...' + must be A or U (bug fix)
    """

    first_name: NameField
    last_name: NameField
    user_id: UserId
    password: PasswordField
    user_type: UserType

    @field_validator("user_id")
    @classmethod
    def user_id_no_spaces(cls, v: str) -> str:
        """User IDs should not contain spaces (VSAM key constraint)."""
        if " " in v:
            raise ValueError("User ID must not contain spaces")
        return v.strip()

    @field_validator("first_name", "last_name")
    @classmethod
    def name_not_whitespace_only(cls, v: str) -> str:
        """Strip trailing whitespace (COBOL PIC X fields are space-padded)."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Field cannot be blank or whitespace only")
        return stripped


class UserUpdate(BaseModel):
    """Request body for PUT /api/users/{user_id} (COUSR02C — Update User).

    All editable fields are required (COUSR02C UPDATE-USER-INFO validation).
    User ID is NOT in this schema — it comes from the path parameter and
    is the VSAM key; it cannot be changed (mirrors COUSR02C design: user_id
    is not in the change-detection loop).

    COUSR02C change-detection: REWRITE only issued when at least one field
    differs from the stored record.  This is enforced in the service layer.
    """

    first_name: NameField
    last_name: NameField
    password: PasswordField
    user_type: UserType

    @field_validator("first_name", "last_name")
    @classmethod
    def name_not_whitespace_only(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Field cannot be blank or whitespace only")
        return stripped


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class UserResponse(BaseModel):
    """Full user record response (password field excluded — never returned)."""

    model_config = {"from_attributes": True}

    user_id: str
    first_name: str
    last_name: str
    user_type: str
    created_at: datetime
    updated_at: datetime


class UserListItem(BaseModel):
    """Single row in the user list (maps to COUSR0A BMS row fields).

    Corresponds to one row: USRID, FNAME, LNAME, UTYPE columns.
    """

    model_config = {"from_attributes": True}

    user_id: str
    first_name: str
    last_name: str
    user_type: str


class UserListResponse(BaseModel):
    """Paginated user list response (maps to COUSR00C PROCESS-PAGE-FORWARD).

    COUSR00C displays 10 rows per page (WS-IDX 1–10).
    CDEMO-CU00-NEXT-PAGE-FLG maps to has_next_page.
    CDEMO-CU00-PAGE-NUM maps to page.
    """

    users: list[UserListItem]
    page: int = Field(ge=1, description="Current page number (1-based)")
    page_size: int = Field(ge=1, le=100, description="Number of records per page")
    total_count: int = Field(ge=0, description="Total number of matching records")
    has_next_page: bool = Field(
        description="True when more pages exist (CDEMO-CU00-NEXT-PAGE-FLG='Y')"
    )
    has_prev_page: bool = Field(
        description="True when previous pages exist (page > 1)"
    )
