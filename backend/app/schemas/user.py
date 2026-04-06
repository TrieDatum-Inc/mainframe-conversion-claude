"""
User management Pydantic schemas.

COBOL origin: Maps COUSR01C/02C/03C BMS map fields (FNAMEI, LNAMEI, USRIDI,
PASSWDI, USRTYPEI) and CSUSR01Y copybook fields to typed DTOs.

SECURITY: password_hash is NEVER included in any response schema.
This is enforced by design — UserResponse has no password field.
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class UserBase(BaseModel):
    """
    Common user fields shared between create/update/response schemas.

    Maps COUSR01C BMS fields:
    - FNAMEI (20 chars, UNPROT) → first_name
    - LNAMEI (20 chars, UNPROT) → last_name
    - USRTYPEI (1 char, UNPROT) → user_type
    """

    first_name: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="SEC-USR-FNAME PIC X(20) — FNAMEI from COUSR01C",
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="SEC-USR-LNAME PIC X(20) — LNAMEI from COUSR01C",
    )
    user_type: Literal["A", "U"] = Field(
        ...,
        description="SEC-USR-TYPE PIC X(01) — 'A'=Admin, 'U'=User — USRTYPEI from COUSR01C",
    )


class UserCreateRequest(UserBase):
    """
    Create user request — maps COUSR01C PROCESS-ENTER-KEY validation order:
    FNAME → LNAME → USERID → PASSWD → USRTYPE (all 5 fields required).
    """

    user_id: str = Field(
        ...,
        min_length=1,
        max_length=8,
        pattern=r"^[A-Za-z0-9]{1,8}$",
        description="SEC-USR-ID PIC X(08) — USRIDI from COUSR01C",
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=72,
        description="Plaintext password; hashed with bcrypt before storage",
    )


class UserUpdateRequest(BaseModel):
    """
    Update user request — maps COUSR02C UPDATE-USER-INFO editable fields.
    user_id is not editable (VSAM key). password=None means no change.
    """

    first_name: str = Field(..., min_length=1, max_length=20)
    last_name: str = Field(..., min_length=1, max_length=20)
    password: Optional[str] = Field(
        None,
        min_length=1,
        max_length=72,
        description="If omitted or null, password is unchanged",
    )
    user_type: Literal["A", "U"]


class UserResponse(UserBase):
    """
    User response — safe public representation.

    Maps COUSR00C/01C/02C/03C screen display fields.
    SECURITY: password_hash is explicitly excluded from this schema.
    """

    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """
    Paginated user list response.

    Maps COUSR00C POPULATE-USER-DATA output (10-row display with NEXT-PAGE-FLG).
    STARTBR/READNEXT pagination → offset-based SQL with total_count look-ahead.
    """

    items: list[UserResponse]
    page: int
    page_size: int
    total_count: int
    has_next: bool
    has_previous: bool
    first_item_key: Optional[str] = None
    last_item_key: Optional[str] = None
