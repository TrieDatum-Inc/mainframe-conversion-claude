"""
Pydantic schemas for the authentication module.

COBOL origin: COSGN00C (transaction CC00) / BMS map COSGN0A.
  - LoginRequest  → maps USRIDI (8-char) + PASSWDI (8-char) BMS input fields
  - LoginResponse → replaces CARDDEMO-COMMAREA populated on successful XCTL

Field length notes:
  - user_id: original USRIDI is 8 characters; preserved as max_length=8
  - password: original PASSWDI is 8 characters, but the modern system extends
    the maximum to 72 characters (bcrypt limit) to allow stronger passwords
    for new accounts while remaining backward compatible with legacy 8-char passwords.
"""

from typing import Literal
from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    """
    Credentials submitted via the login form.

    COBOL origin: COSGN0A map input fields USRIDI and PASSWDI.
    """
    user_id: str = Field(
        ...,
        min_length=1,
        max_length=8,
        description="User ID — maps USRIDI field from COSGN0A (8 chars max)",
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=72,
        description="Password — maps PASSWDI field; extended from 8 to 72 chars (bcrypt limit)",
    )

    @field_validator("user_id")
    @classmethod
    def user_id_strip(cls, v: str) -> str:
        """
        Trim trailing whitespace.

        COBOL origin: COSGN00C trims WS-USER-ID with FUNCTION TRIM(USERIDI TRAILING).
        """
        stripped = v.strip()
        if not stripped:
            raise ValueError("User ID cannot be empty after trimming whitespace")
        return stripped


class LoginResponse(BaseModel):
    """
    Successful authentication response.

    COBOL origin: Replaces CARDDEMO-COMMAREA populated in PROCESS-ENTER-KEY
    and passed via CICS XCTL to COADM01C (admin) or COMEN01C (regular user).
    The redirect_to field replaces the XCTL routing decision.
    """
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    user_id: str
    user_type: Literal["A", "U"]
    first_name: str
    last_name: str
    redirect_to: str  # "/admin/menu" for user_type='A'; "/menu" for user_type='U'
