"""
Pydantic request/response schemas for the User Management module.

COBOL origin: COUSR00C, COUSR01C, COUSR02C, COUSR03C — USRSEC VSAM KSDS
              BMS maps: COUSR0A, COUSR1A, COUSR2A, COUSR3A

Schema→COBOL field mapping:
  UserCreateRequest → COUSR1AI (input map): FNAMEI, LNAMEI, USERIDI, PASSWDI, USRTYPEI
  UserUpdateRequest → COUSR2AI (input map): FNAMEI, LNAMEI, PASSWDI, USRTYPEI
  UserResponse      → COUSR0AO (output): USRID, FNAME, LNAME, UTYPE (password NEVER returned)
  UserListResponse  → COUSR00C pagination envelope + up to 10 rows

Security rule: password_hash is NEVER included in any response schema.
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class UserBase(BaseModel):
    """
    Shared editable fields common to create and update operations.

    COBOL origin: SEC-USR-FNAME, SEC-USR-LNAME, SEC-USR-TYPE from CSUSR01Y.
    """

    first_name: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="SEC-USR-FNAME X(20) — must be non-blank (COUSR01C: FNAMEI blank check)",
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="SEC-USR-LNAME X(20) — must be non-blank (COUSR01C: LNAMEI blank check)",
    )
    user_type: Literal["A", "U"] = Field(
        ...,
        description="SEC-USR-TYPE X(01): 'A'=Admin, 'U'=Regular. COUSR01C: USRTYPEI blank/invalid check",
    )

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_and_validate_not_blank(cls, value: str) -> str:
        """
        Trim whitespace and reject blank strings.

        COBOL origin: COUSR01C PROCESS-ENTER-KEY validates:
            IF FNAMEI = SPACES OR LOW-VALUES → ERR-FLG-ON; 'First Name can NOT be empty...'
            IF LNAMEI = SPACES OR LOW-VALUES → ERR-FLG-ON; 'Last Name can NOT be empty...'
        """
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field cannot be blank or whitespace only")
        return stripped


class UserCreateRequest(UserBase):
    """
    Request body for POST /api/v1/users (create new user).

    COBOL origin: COUSR01C PROCESS-ENTER-KEY → WRITE-USER-SEC-FILE.
    All five fields required; validation order: first_name → last_name → user_id → password → user_type.
    """

    user_id: str = Field(
        ...,
        min_length=1,
        max_length=8,
        pattern=r"^[A-Za-z0-9]{1,8}$",
        description="SEC-USR-ID X(08) — VSAM primary key; 1-8 alphanumeric chars",
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=72,
        description="SEC-USR-PWD (was plain text X(8) in VSAM; now bcrypt-hashed before storage)",
    )

    @field_validator("user_id")
    @classmethod
    def validate_user_id_not_blank(cls, value: str) -> str:
        """
        COBOL origin: COUSR01C: IF USERIDI = SPACES OR LOW-VALUES → 'User ID can NOT be empty...'
        """
        stripped = value.strip()
        if not stripped:
            raise ValueError("User ID cannot be blank")
        return stripped

    @field_validator("password")
    @classmethod
    def validate_password_not_blank(cls, value: str) -> str:
        """
        COBOL origin: COUSR01C: IF PASSWDI = SPACES OR LOW-VALUES → 'Password can NOT be empty...'
        """
        if not value.strip():
            raise ValueError("Password cannot be blank")
        return value


class UserUpdateRequest(BaseModel):
    """
    Request body for PUT /api/v1/users/{user_id} (update existing user).

    COBOL origin: COUSR02C UPDATE-USER-INFO paragraph.
    Password is optional — blank/absent means no password change.
    user_id is taken from the path, not the request body (cannot be changed).
    """

    first_name: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="SEC-USR-FNAME — must be non-blank",
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="SEC-USR-LNAME — must be non-blank",
    )
    password: Optional[str] = Field(
        None,
        min_length=1,
        max_length=72,
        description=(
            "New password — optional. If omitted or None, password is unchanged. "
            "COBOL origin: COUSR02C field-level change detection for PASSWDI"
        ),
    )
    user_type: Literal["A", "U"] = Field(
        ...,
        description="SEC-USR-TYPE: 'A'=Admin, 'U'=Regular",
    )

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_and_validate_not_blank(cls, value: str) -> str:
        """
        COBOL origin: COUSR02C UPDATE-USER-INFO:
            IF FNAMEI = SPACES → 'First Name can NOT be empty...'
            IF LNAMEI = SPACES → 'Last Name can NOT be empty...'
        """
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field cannot be blank or whitespace only")
        return stripped


class UserResponse(UserBase):
    """
    Response schema for a single user — password NEVER returned.

    COBOL origin: Output fields from COUSR0AO, COUSR2AO, COUSR3AO maps.
    SEC-USR-PWD is intentionally excluded from this schema.
    """

    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """
    Paginated list response for GET /api/v1/users.

    COBOL origin: COUSR00C POPULATE-USER-DATA:
      - Up to 10 rows per page (COUSR00C fills USRID1O–USRID10O)
      - Pagination state from CDEMO-CU00-INFO fields
      - CDEMO-CU00-NEXT-PAGE-FLG → has_next
      - CDEMO-CU00-USRID-FIRST / LAST → first_item_key / last_item_key
    """

    items: list[UserResponse]
    page: int
    page_size: int
    total_count: int
    has_next: bool
    has_previous: bool
    first_item_key: Optional[str] = None
    last_item_key: Optional[str] = None
