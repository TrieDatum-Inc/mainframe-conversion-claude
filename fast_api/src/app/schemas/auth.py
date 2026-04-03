"""Pydantic schemas for authentication and menu navigation.

Maps COBOL BMS screen fields and COMMAREA fields to REST API contracts:
- COSGN0AI USERIDI/PASSWDI fields → LoginRequest
- CARDDEMO-COMMAREA fields → TokenPayload
- COMEN02Y / COADM02Y menu option tables → MenuOption / MenuResponse
"""
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    """Login credentials — maps COSGN0AI USERIDI and PASSWDI fields.

    COBOL BR-001: user_id is required (not spaces / LOW-VALUES).
    COBOL BR-002: password is required (not spaces / LOW-VALUES).
    COBOL BR-003: Both are uppercased before authentication.
    COBOL constraint: both fields are PIC X(08) — max 8 characters.
    """

    user_id: str = Field(
        ...,
        min_length=1,
        max_length=8,
        description="User ID (COSGN0AI USERIDI, PIC X(08)). Case-insensitive — uppercased before lookup.",
        examples=["USER0001"],
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=8,
        description="Password (COSGN0AI PASSWDI, PIC X(08), dark field on BMS screen). Case-insensitive — uppercased before verify.",
        examples=["USER0001"],
    )

    @field_validator("user_id", "password", mode="before")
    @classmethod
    def strip_and_validate_not_blank(cls, value: str) -> str:
        """Reject blank/whitespace-only values — mirrors COBOL SPACES check."""
        if not isinstance(value, str):
            raise ValueError("Must be a string")
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field cannot be blank")
        return stripped


class UserInfo(BaseModel):
    """Authenticated user data — subset of CARDDEMO-COMMAREA fields."""

    user_id: str = Field(description="CDEMO-USER-ID PIC X(08)")
    first_name: str
    last_name: str
    user_type: str = Field(description="CDEMO-USER-TYPE: A=Admin, U=Regular")

    model_config = {"from_attributes": True}


class TokenPayload(BaseModel):
    """JWT token claims — replaces CARDDEMO-COMMAREA session state.

    COMMAREA field mapping:
      CDEMO-USER-ID    → sub
      CDEMO-USER-TYPE  → user_type
      CDEMO-FROM-TRANID → from_tranid (set on each navigation)
    """

    sub: str = Field(description="User ID — CDEMO-USER-ID")
    user_type: str = Field(description="User role — CDEMO-USER-TYPE (A or U)")
    first_name: str
    last_name: str
    exp: int | None = None


class LoginResponse(BaseModel):
    """Successful login response.

    Equivalent to COSGN00C READ-USER-SEC-FILE success path:
    - Sets COMMAREA routing fields
    - Determines destination menu based on user_type
    """

    access_token: str = Field(description="JWT bearer token")
    token_type: str = Field(default="bearer")
    user: UserInfo
    redirect_to: str = Field(
        description="Route target based on user type: /admin-menu (type=A) or /main-menu (type=U)"
    )
    server_time: datetime = Field(description="Current server timestamp — replaces POPULATE-HEADER-INFO")


class MenuOption(BaseModel):
    """Single menu option — maps COMEN02Y / COADM02Y OCCURS table entry.

    COBOL fields:
      CDEMO-MENU-OPT-NUM      → option_number
      CDEMO-MENU-OPT-NAME     → name
      CDEMO-MENU-OPT-PGMNAME  → program_name
      CDEMO-MENU-OPT-USRTYPE  → required_user_type
    """

    option_number: int = Field(description="CDEMO-MENU-OPT-NUM PIC 9(02)")
    name: str = Field(description="CDEMO-MENU-OPT-NAME PIC X(35)")
    program_name: str = Field(description="CDEMO-MENU-OPT-PGMNAME PIC X(08)")
    route: str = Field(description="Modern frontend route equivalent")
    required_user_type: str = Field(
        description="CDEMO-MENU-OPT-USRTYPE: U=Regular A=Admin"
    )
    is_available: bool = Field(
        default=True,
        description="False when program begins with DUMMY or extension not installed — BR-005/BR-006",
    )
    availability_message: str | None = Field(
        default=None,
        description="Message when not available — 'coming soon' or 'not installed'",
    )


class MenuResponse(BaseModel):
    """Menu screen data — replaces SEND-MENU-SCREEN in COMEN01C / COADM01C.

    Includes header info (replaces POPULATE-HEADER-INFO) and the option list
    (replaces BUILD-MENU-OPTIONS).
    """

    menu_type: str = Field(description="'main' or 'admin'")
    title: str = Field(description="Menu title (Main Menu / Admin Menu)")
    user: UserInfo
    options: list[MenuOption]
    server_time: datetime
    transaction_id: str = Field(description="TRNNAMEO — CM00 or CA00")
    program_name: str = Field(description="PGMNAMEO — COMEN01C or COADM01C")


class NavigateRequest(BaseModel):
    """Option selection request — maps COMEN1AI / COADM1AI OPTIONI field.

    COBOL OPTIONI is PIC X(02) with NUM attribute and JUSTIFY=(RIGHT,ZERO).
    Values 1-11 for main menu, 1-6 for admin menu.
    Zero and out-of-range are rejected (BR-003).
    """

    option: int = Field(
        ...,
        ge=1,
        le=11,
        description="Selected option number (1-11 for main, 1-6 for admin)",
    )


class NavigateResponse(BaseModel):
    """Navigation result — replaces XCTL dispatch in PROCESS-ENTER-KEY."""

    option_selected: int
    program_name: str = Field(description="Target COBOL program equivalent")
    route: str = Field(description="Modern frontend route to navigate to")
    message: str | None = None
    message_type: str | None = Field(
        default=None,
        description="'error' (RED), 'info' (GREEN), 'success' — mirrors DFHRED/DFHGREEN",
    )
