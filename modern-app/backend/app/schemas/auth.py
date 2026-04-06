"""Pydantic schemas for authentication requests and responses.

Business rules preserved from COSGN00C:
- User ID is exactly 8 characters, uppercased before comparison.
- Password is exactly 8 characters, uppercased before comparison.
- user_type is 'A' (Admin) or 'U' (Regular User).
"""

from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    """Payload for POST /api/auth/login.

    Maps to COSGN00C receive-map fields: USERID (8) and PASSWD (8).
    """

    user_id: str = Field(
        min_length=1,
        max_length=8,
        description="CardDemo user ID (up to 8 characters, case-insensitive)",
    )
    password: str = Field(
        min_length=1,
        max_length=8,
        description="CardDemo password (up to 8 characters, case-insensitive)",
    )

    @field_validator("user_id", "password", mode="before")
    @classmethod
    def uppercase_and_strip(cls, value: str) -> str:
        """COBOL rule: both fields are uppercased before comparison."""
        if not isinstance(value, str):
            raise ValueError("Must be a string")
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field must not be blank")
        return stripped.upper()


class Token(BaseModel):
    """JWT bearer token returned on successful login."""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Claims stored inside the JWT.

    Maps to COMMAREA fields set by COSGN00C before XCTL:
    - user_id  -> CDEMO-USER-ID
    - user_type -> CDEMO-USER-TYPE  ('A' | 'U')
    """

    sub: str  # user_id
    user_type: str  # 'A' or 'U'


class UserResponse(BaseModel):
    """Public representation of a CardDemo user."""

    user_id: str
    first_name: str
    last_name: str
    user_type: str

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    """Response body for a successful login."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class LogoutResponse(BaseModel):
    """Acknowledgement for POST /api/auth/logout."""

    message: str = "Successfully logged out"
