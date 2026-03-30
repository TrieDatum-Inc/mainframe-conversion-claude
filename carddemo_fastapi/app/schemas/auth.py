"""Authentication schemas matching COBOL CSUSR01Y.cpy and COMMAREA user fields.

- LoginRequest: maps to SEC-USR-ID (PIC X(08)) and SEC-USR-PWD (PIC X(08))
- LoginResponse: maps to CDEMO-USER-ID, CDEMO-USER-TYPE from COCOM01Y.cpy
- UserContext: extracted from JWT, replaces COMMAREA user fields at runtime
"""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Login request matching SEC-USR-ID and SEC-USR-PWD from CSUSR01Y.cpy."""

    user_id: str = Field(..., max_length=8, description="User ID (SEC-USR-ID PIC X(08))")
    password: str = Field(..., max_length=8, description="Password (SEC-USR-PWD PIC X(08))")


class LoginResponse(BaseModel):
    """Login response carrying JWT token and user context from COMMAREA."""

    token: str = Field(..., description="JWT bearer token")
    user_id: str = Field(..., description="Authenticated user ID (CDEMO-USER-ID)")
    user_type: str = Field(
        ...,
        description="User type: 'A' (admin) or 'U' (regular) (CDEMO-USER-TYPE)",
    )


class UserContext(BaseModel):
    """User context extracted from JWT, replaces COMMAREA user fields.

    Maps to CDEMO-USER-ID PIC X(08) and CDEMO-USER-TYPE PIC X(01)
    with 88-level values CDEMO-USRTYP-ADMIN='A' and CDEMO-USRTYP-USER='U'.
    """

    user_id: str = Field(..., description="User ID from JWT (CDEMO-USER-ID)")
    user_type: str = Field(
        ...,
        description="User type from JWT: 'A' (admin) or 'U' (regular) (CDEMO-USER-TYPE)",
    )
