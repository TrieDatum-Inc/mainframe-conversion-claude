"""
Pydantic schemas for Authentication endpoints.
Maps COSGN00C sign-on logic to REST API request/response.

COSGN00C business rules preserved:
  BR-SGN-001: User ID and password are mandatory
  BR-SGN-002: User ID converted to upper-case before validation
  BR-SGN-004: User type 'A' = Admin, 'U' = Regular User
  BR-SGN-006: PF3 -> logout (handled by token expiry)
"""

from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    """
    Maps COSGN0AI BMS map input fields:
      USERIDI X(8) -> user_id
      PASSWDI X(8) -> password

    BR-SGN-001: Both fields mandatory
    BR-SGN-002: user_id is upper-cased before VSAM key lookup
    """
    user_id: str = Field(
        ...,
        min_length=1,
        max_length=8,
        description="User ID (1-8 chars, upper-cased per BR-SGN-002)",
        examples=["ADMIN001"],
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=8,
        description="Password (1-8 chars per USRSEC SEC-USR-PWD PIC X(08))",
        examples=["PASS1234"],
    )

    @field_validator("user_id")
    @classmethod
    def uppercase_user_id(cls, v: str) -> str:
        """BR-SGN-002: User ID converted to upper-case."""
        return v.strip().upper()


class TokenResponse(BaseModel):
    """JWT token response returned on successful login."""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    user_type: str = Field(description="'A'=Admin, 'U'=Regular User")
    first_name: str
    last_name: str


class UserContext(BaseModel):
    """
    Represents the CARDDEMO-COMMAREA user context fields:
      CDEMO-USER-ID      PIC X(08)
      CDEMO-USER-TYPE    PIC X(01) ('A'=Admin, 'U'=User)
    """
    user_id: str
    user_type: str
    first_name: str
    last_name: str
