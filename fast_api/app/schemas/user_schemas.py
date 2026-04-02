"""
Pydantic schemas for User Management endpoints.

Maps COUSR00C (list), COUSR01C (add), COUSR02C (update), COUSR03C (delete) programs.

All user management is admin-only (CDEMO-USER-TYPE='A' required).
COUSR00C: paginated list (10 rows per page)
COUSR01C: add new user - validates all 5 required fields
COUSR02C: update existing user - cannot change user ID
COUSR03C: delete user - confirmation step

From COUSR01C validation:
  - First name: mandatory, max 20 chars
  - Last name: mandatory, max 20 chars
  - User ID: mandatory, 1-8 chars, converted to upper-case
  - Password: mandatory, 1-8 chars
  - User type: mandatory, must be 'A' or 'U'
"""

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class UserBase(BaseModel):
    """Shared user fields from CSUSR01Y copybook."""
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="First name - SEC-USR-FNAME PIC X(20)",
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Last name - SEC-USR-LNAME PIC X(20)",
    )
    usr_type: str = Field(
        ...,
        min_length=1,
        max_length=1,
        description="User type: 'A'=Admin, 'U'=Regular - SEC-USR-TYPE PIC X(01)",
    )

    @field_validator("usr_type")
    @classmethod
    def validate_user_type(cls, v: str) -> str:
        """BR-SGN-004: Only 'A' (Admin) and 'U' (User) are valid types."""
        upper = v.strip().upper()
        if upper not in ("A", "U"):
            raise ValueError("User type must be 'A' (Admin) or 'U' (Regular User).")
        return upper


class UserView(UserBase):
    """
    User record view (COUSR00C list row, COUSR02C detail).
    Password is never returned in responses (security improvement over USRSEC plain-text).
    """
    usr_id: str = Field(
        ...,
        min_length=1,
        max_length=8,
        description="User ID - SEC-USR-ID PIC X(08)",
    )

    model_config = {"from_attributes": True}


class UserListItem(BaseModel):
    """
    Single row in COUSR00C user list screen.
    COUSR00C shows: USER-SEL, USER-ID, USER-NAME (first+last), USER-TYPE
    """
    usr_id: str = Field(..., max_length=8)
    first_name: str = Field(..., max_length=20)
    last_name: str = Field(..., max_length=20)
    usr_type: str = Field(..., max_length=1)

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """
    Paginated user list (COUSR00C).
    COUSR00C state: CDEMO-CU00-PAGE-NUM, CDEMO-CU00-NEXT-PAGE-FLG
    10 rows per page.
    """
    items: List[UserListItem]
    page: int = Field(default=1, ge=1)
    has_next_page: bool = False
    first_usr_id: Optional[str] = None
    last_usr_id: Optional[str] = None


class UserCreateRequest(UserBase):
    """
    Create user (COUSR01C).
    All 5 fields are mandatory (validated per COUSR01C business logic).
    User ID is upper-cased before VSAM WRITE (same as COSGN00C login).
    """
    usr_id: str = Field(
        ...,
        min_length=1,
        max_length=8,
        description="User ID (1-8 chars) - SEC-USR-ID PIC X(08)",
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=8,
        description="Password (1-8 chars) - SEC-USR-PWD PIC X(08)",
    )

    @field_validator("usr_id")
    @classmethod
    def uppercase_usr_id(cls, v: str) -> str:
        """Upper-case user ID consistent with COSGN00C UPPER-CASE conversion."""
        return v.strip().upper()


class UserUpdateRequest(UserBase):
    """
    Update user (COUSR02C).
    User ID is the path parameter (not in body).
    Password may be optionally changed.
    """
    password: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=8,
        description="New password (optional) - SEC-USR-PWD PIC X(08)",
    )


class UserDeleteRequest(BaseModel):
    """
    Delete user confirmation (COUSR03C).
    COUSR03C requires explicit confirm=true to prevent accidental deletion.
    """
    confirm: bool = Field(
        default=False,
        description="Must be true to confirm user deletion.",
    )
