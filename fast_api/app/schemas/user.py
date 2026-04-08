"""
Pydantic schemas for user management (COUSR00C, COUSR01C, COUSR02C, COUSR03C).

Maps BMS map COUSR00/COUSR01/COUSR02/COUSR03 to request/response schemas.

COUSR00C: list users (STARTBR/READNEXT USRSEC)
  → GET /api/v1/admin/users

COUSR01C: add user (EXEC CICS WRITE FILE(USRSEC))
  → POST /api/v1/admin/users

COUSR02C: update user (EXEC CICS REWRITE FILE(USRSEC))
  → PUT /api/v1/admin/users/{user_id}

COUSR03C: delete user (EXEC CICS DELETE FILE(USRSEC))
  → DELETE /api/v1/admin/users/{user_id}
"""
from pydantic import BaseModel, Field, field_validator

from app.models.user import USER_TYPE_ADMIN, USER_TYPE_REGULAR
from app.utils.cobol_compat import cobol_upper, pad_user_id


class UserBase(BaseModel):
    """Shared user fields."""

    first_name: str | None = Field(None, max_length=20, description="SEC-USR-FNAME PIC X(20)")
    last_name: str | None = Field(None, max_length=20, description="SEC-USR-LNAME PIC X(20)")
    user_type: str | None = Field(None, max_length=1, description="SEC-USR-TYPE PIC X(01): A=admin, U=regular")

    @field_validator("user_type")
    @classmethod
    def validate_user_type(cls, v: str | None) -> str | None:
        """COUSR01C/02C: user type must be 'A' or 'U'."""
        if v is not None and v not in (USER_TYPE_ADMIN, USER_TYPE_REGULAR):
            raise ValueError(f"user_type must be '{USER_TYPE_ADMIN}' (admin) or '{USER_TYPE_REGULAR}' (regular)")
        return v


class UserResponse(UserBase):
    """
    User response — maps to COUSR00 BMS map row display.

    Password hash is never returned in responses.
    """

    user_id: str = Field(..., description="SEC-USR-ID PIC X(08)")
    is_admin: bool = Field(..., description="Derived from user_type == 'A'")

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """
    Paginated user list — maps to COUSR00 BMS map (10 rows per screen).

    Keyset pagination mirrors STARTBR/READNEXT on USRSEC:
      next_cursor = last user_id on page.
    """

    items: list[UserResponse]
    total: int
    next_cursor: str | None = Field(None, description="Keyset cursor: last user_id on this page")
    prev_cursor: str | None = Field(None, description="Keyset cursor: first user_id on this page")


class UserCreateRequest(UserBase):
    """
    Create user request — maps to COUSR01C BMS map RECEIVE MAP.

    Business rules (COUSR01C):
      - user_id is 8 chars max, uppercased, space-padded in COBOL
      - password is 8 chars max (PIC X(08)) — stored as bcrypt hash
      - Duplicate user_id → DuplicateRecordError (CICS DUPREC → HTTP 409)
    """

    user_id: str = Field(
        ..., min_length=1, max_length=8, description="SEC-USR-ID PIC X(08) — uppercased, space-padded"
    )
    password: str = Field(
        ..., min_length=1, max_length=8, description="SEC-USR-PWD PIC X(08) — stored as bcrypt hash"
    )
    user_type: str = Field(
        USER_TYPE_REGULAR, max_length=1, description="SEC-USR-TYPE: A=admin, U=regular"
    )

    @field_validator("user_id")
    @classmethod
    def normalize_user_id(cls, v: str) -> str:
        """
        COUSR01C: user ID is uppercased and space-padded to 8 chars.
        COSGN00C: FUNCTION UPPER-CASE(USERIDI OF COSGN0AI) TO WS-USER-ID
        """
        return pad_user_id(v)


class UserUpdateRequest(UserBase):
    """
    Update user request — maps to COUSR02C BMS map RECEIVE MAP.

    Password update is optional; if provided, bcrypt hashed before storing.
    user_id cannot be changed (it is the VSAM key).
    """

    password: str | None = Field(
        None, min_length=1, max_length=8, description="New password (optional) — stored as bcrypt hash"
    )
