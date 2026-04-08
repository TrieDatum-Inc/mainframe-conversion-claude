"""
Pydantic schemas for authentication (COSGN00C).

Maps COSGN0A BMS map fields to request/response:
  USERIDI (PIC X(08)) → LoginRequest.user_id
  PASSWDI (PIC X(08)) → LoginRequest.password
  CDEMO-USER-ID + CDEMO-USER-TYPE → JWT token claims
"""
from pydantic import BaseModel, Field, field_validator

from app.utils.cobol_compat import cobol_upper


class LoginRequest(BaseModel):
    """
    Sign-on request — maps to COSGN0A BMS map RECEIVE.

    COSGN00C validation rules:
      - user_id must not be spaces/empty (WHEN USERIDI = SPACES)
      - password must not be spaces/empty (WHEN PASSWDI = SPACES)
      - user_id is uppercased before lookup (FUNCTION UPPER-CASE)
    """

    user_id: str = Field(
        ...,
        min_length=1,
        max_length=8,
        description="SEC-USR-ID PIC X(08) — uppercased before USRSEC lookup",
        examples=["ADMIN"],
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=8,
        description="SEC-USR-PWD PIC X(08) — compared against stored hash",
        examples=["Admin123"],
    )

    @field_validator("user_id")
    @classmethod
    def uppercase_user_id(cls, v: str) -> str:
        """
        COSGN00C PROCESS-ENTER-KEY:
          MOVE FUNCTION UPPER-CASE(USERIDI OF COSGN0AI) TO WS-USER-ID
        """
        return cobol_upper(v).strip()

    @field_validator("password")
    @classmethod
    def password_not_spaces(cls, v: str) -> str:
        """COSGN00C: WHEN PASSWDI OF COSGN0AI = SPACES → error."""
        if not v or not v.strip():
            raise ValueError("Please enter Password ...")
        return v


class TokenResponse(BaseModel):
    """
    JWT token response — replaces CICS COMMAREA (COCOM01Y) session state.

    JWT claims encode:
      sub  → CDEMO-USER-ID (PIC X(08))
      role → CDEMO-USER-TYPE (PIC X(01): 'A'=admin, 'U'=user)
    """

    access_token: str = Field(..., description="JWT bearer token")
    token_type: str = Field(default="bearer", description="Always 'bearer'")
    user_id: str = Field(..., description="Authenticated user ID (CDEMO-USER-ID)")
    user_type: str = Field(..., description="User type: 'A'=admin, 'U'=regular (CDEMO-USER-TYPE)")
    first_name: str | None = Field(None, description="SEC-USR-FNAME")
    last_name: str | None = Field(None, description="SEC-USR-LNAME")


class TokenData(BaseModel):
    """JWT payload claims — extracted from token in dependencies."""

    sub: str  # user_id
    role: str  # user_type ('A' or 'U')
