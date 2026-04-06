"""Pydantic schemas for the User Administration API.

Mirrors field-level validation rules from COUSR01C (add) and COUSR02C (update):
- All fields required on create (sequential blank checks from spec §6)
- user_id: max 8 chars, uppercase, alphanumeric
- user_type: must be 'A' (Admin) or 'U' (User) — COBOL 88-level conditions
- password: max 8 chars on create; optional on update (only hash if provided)
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Valid user type literals — map directly to COBOL 88-level condition names
UserTypeLiteral = Literal["A", "U"]

# Field length constants from CSUSR01Y copybook
USER_ID_MAX_LEN = 8
FIRST_NAME_MAX_LEN = 20
LAST_NAME_MAX_LEN = 20
PASSWORD_MAX_LEN = 8


class UserBase(BaseModel):
    """Shared fields present in both request and response schemas."""

    first_name: str = Field(
        ...,
        min_length=1,
        max_length=FIRST_NAME_MAX_LEN,
        description="SEC-USR-FNAME X(20)",
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=LAST_NAME_MAX_LEN,
        description="SEC-USR-LNAME X(20)",
    )
    user_type: UserTypeLiteral = Field(
        ...,
        description="A = Admin, U = Regular User (mirrors SEC-USR-TYPE)",
    )

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def strip_and_require(cls, v: object) -> str:
        """Reject blank/whitespace-only strings — mirrors COUSR01C blank checks."""
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Field must not be blank")
        return v.strip()


class UserCreate(UserBase):
    """Request body for POST /api/users — mirrors COUSR01C add flow."""

    user_id: str = Field(
        ...,
        min_length=1,
        max_length=USER_ID_MAX_LEN,
        description="Primary key — SEC-USR-ID X(8), uppercase alphanumeric",
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=PASSWORD_MAX_LEN,
        description="Plain-text password (8 chars max); will be bcrypt-hashed",
    )

    @field_validator("user_id", mode="before")
    @classmethod
    def normalize_user_id(cls, v: object) -> str:
        """Uppercase and strip user_id — mirrors COSGN00C uppercasing behaviour."""
        if not isinstance(v, str) or not v.strip():
            raise ValueError("user_id must not be blank")
        return v.strip().upper()

    @field_validator("password", mode="before")
    @classmethod
    def require_password(cls, v: object) -> str:
        """Password must not be blank on creation."""
        if not isinstance(v, str) or not v.strip():
            raise ValueError("password must not be blank")
        return v


class UserUpdate(BaseModel):
    """Request body for PUT /api/users/{user_id} — mirrors COUSR02C update flow.

    All name/type fields are required (spec §6 Phase 2 re-validates non-empty).
    Password is optional — only supply it to change the password.
    Only issues a DB update when at least one field has changed (COUSR02C business rule).
    """

    first_name: str = Field(
        ...,
        min_length=1,
        max_length=FIRST_NAME_MAX_LEN,
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=LAST_NAME_MAX_LEN,
    )
    user_type: UserTypeLiteral
    password: str | None = Field(
        default=None,
        max_length=PASSWORD_MAX_LEN,
        description="If omitted or null, existing password is unchanged",
    )

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def strip_and_require(cls, v: object) -> str:
        """Reject blank/whitespace-only strings."""
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Field must not be blank")
        return v.strip()

    @field_validator("password", mode="before")
    @classmethod
    def normalize_password(cls, v: object) -> str | None:
        """Treat empty string as no-change (None)."""
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        return v


class UserPublic(BaseModel):
    """Response schema — never exposes password_hash."""

    model_config = ConfigDict(from_attributes=True)

    user_id: str
    first_name: str
    last_name: str
    user_type: str
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    """Paginated list response for GET /api/users."""

    users: list[UserPublic]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserDeleteResponse(BaseModel):
    """Response body for DELETE /api/users/{user_id}."""

    message: str
    user_id: str
