"""
Authentication Pydantic schemas.

COBOL origin: Maps COSGN0A BMS map input fields (USERIDI, PASSWDI) and
CARDDEMO-COMMAREA fields (CDEMO-USER-ID, CDEMO-USER-TYPE, CDEMO-USER-FNAME, etc.)
to typed request/response models.

Security improvement: password max_length extended from 8 (COBOL PIC X(8)) to 72
(bcrypt limit). Legacy 8-char passwords remain valid.
"""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """
    Login request body.

    Maps BMS map COSGN0A input fields:
    - USERIDI (USERID field, 8 chars, UNPROT) → user_id
    - PASSWDI (PASSWD field, 8 chars, DRK UNPROT) → password

    COBOL validation in PROCESS-ENTER-KEY paragraph:
        IF WS-USER-ID = SPACES → 'Please enter your user id...'
    Replicated here as min_length=1.
    """

    user_id: str = Field(
        ...,
        min_length=1,
        max_length=8,
        description="USERIDI field from COSGN0A map — USRSEC VSAM key (SEC-USR-ID PIC X(8))",
        examples=["ADMIN001"],
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=72,  # bcrypt limit; original COBOL: 8 chars
        description=(
            "PASSWDI field from COSGN0A map — DRK field (masked); "
            "replaces plain-text SEC-USR-PWD X(8) comparison"
        ),
        examples=["password"],
    )


class LoginResponse(BaseModel):
    """
    Successful login response.

    Maps CARDDEMO-COMMAREA fields populated by COSGN00C PROCESS-ENTER-KEY:
    - CDEMO-USER-ID → user_id
    - CDEMO-USER-TYPE → user_type ('A' or 'U')
    - CDEMO-USER-FNAME → first_name
    - CDEMO-USER-LNAME → last_name

    The redirect_to field replaces CICS XCTL logic:
    - SEC-USR-TYPE='A' → XCTL to COADM01C → redirect_to='/admin/menu'
    - SEC-USR-TYPE!='A' → XCTL to COMEN01C → redirect_to='/menu'
    """

    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600  # seconds; replaces indefinite CICS task lifetime
    user_id: str
    user_type: str  # 'A' (Admin) or 'U' (User) — from CDEMO-USER-TYPE
    first_name: str
    last_name: str
    redirect_to: str  # '/admin/menu' for type='A', '/menu' for type='U'


class TokenPayload(BaseModel):
    """
    JWT token payload claims.

    Maps CARDDEMO-COMMAREA session fields that COBOL programs passed via XCTL/RETURN:
    - sub (CDEMO-USER-ID): authenticated user ID
    - user_type (CDEMO-USER-TYPE): role for RBAC decisions

    COBOL used EIBCALEN=0 check to detect unauthenticated entry (no COMMAREA).
    The modern equivalent is absence of a valid JWT → 401 Unauthorized.
    """

    sub: str  # user_id — CDEMO-USER-ID X(8)
    user_type: str  # 'A' or 'U' — CDEMO-USER-TYPE X(1) / CDEMO-USRTYP-ADMIN 88-level
    exp: int  # token expiry Unix timestamp
    iat: int  # issued-at Unix timestamp
    iss: str = "carddemo-api"  # issuer
    jti: str = ""  # JWT ID for token revocation (logout deny-list)
