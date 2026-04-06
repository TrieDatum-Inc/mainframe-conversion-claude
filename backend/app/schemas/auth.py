"""
Auth schemas — login request/response.

COBOL origin: COSGN00C PROCESS-ENTER-KEY → CARDDEMO-COMMAREA.
"""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """
    Login request — maps COSGN0A BMS map input fields.
    USERIDI PIC X(8), PASSWDI PIC X(8).
    """
    user_id: str = Field(..., min_length=1, max_length=8)
    password: str = Field(..., min_length=1, max_length=8)


class LoginResponse(BaseModel):
    """
    Login response — maps CARDDEMO-COMMAREA fields from COSGN00C.
    JWT token replaces CICS session/COMMAREA state.
    """
    access_token: str
    token_type: str = "bearer"
    expires_in: int          # seconds
    user_id: str
    user_type: str           # 'A' or 'U'
    first_name: str
    last_name: str
    redirect_to: str         # '/admin/menu' or '/menu'
