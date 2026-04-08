"""
Pydantic schemas for admin menu metadata (COADM01C — CICS transaction CA00).

Source program: app/cbl/COADM01C.cbl
BMS map: COADM01 / COADM1A

COADM01C function:
    Displays the admin navigation menu with up to 10 menu options.
    Each option maps to a CICS program via EXEC CICS XCTL.
    Menu items are built from CDEMO-ADMIN-OPT-* arrays (COPY COADM02Y).

Copybook: COADM02Y defines:
    01 CARDDEMO-ADMIN-OPTS.
       05 CDEMO-ADMIN-OPT-COUNT          PIC 9(02)  VALUE 8.
       05 CDEMO-ADMIN-OPT-PGMNAME OCCURS 10 TIMES  PIC X(08).
       05 CDEMO-ADMIN-OPT-TRANID  OCCURS 10 TIMES  PIC X(04).
       05 CDEMO-ADMIN-OPT-NUM     OCCURS 10 TIMES  PIC 9(02).
       05 CDEMO-ADMIN-OPT-NAME    OCCURS 10 TIMES  PIC X(35).

Endpoint mapping:
    GET /api/v1/admin/menu
        → COADM01C BUILD-MENU-OPTIONS paragraph
        → Returns static admin menu metadata (no DB required)

Business rules preserved:
    1. Admin menu has exactly 8 active options (CDEMO-ADMIN-OPT-COUNT = 8)
    2. Options numbered 1-10, text formatted as '{num}. {name}'
       (COADM01C BUILD-MENU-OPTIONS: STRING CDEMO-ADMIN-OPT-NUM CDEMO-ADMIN-OPT-NAME)
    3. Options pointing to 'DUMMY' programs are not installed
       (COADM01C: IF CDEMO-ADMIN-OPT-PGMNAME(WS-OPTION)(1:5) NOT = 'DUMMY')
    4. Option selection must be numeric and within 1..CDEMO-ADMIN-OPT-COUNT
       (COADM01C PROCESS-ENTER-KEY validation)
"""
from pydantic import BaseModel, Field


class AdminMenuItem(BaseModel):
    """
    Single admin menu option.

    Maps to COADM01C BUILD-MENU-OPTIONS one iteration:
      CDEMO-ADMIN-OPT-NUM(I)      → option_number
      CDEMO-ADMIN-OPT-NAME(I)     → name
      CDEMO-ADMIN-OPT-PGMNAME(I)  → program_name
      CDEMO-ADMIN-OPT-TRANID(I)   → transaction_id
      WS-ADMIN-OPT-TXT            → display_text (formatted label)
    """

    option_number: int = Field(..., ge=1, le=10, description="CDEMO-ADMIN-OPT-NUM(I) PIC 9(02)")
    name: str = Field(..., description="CDEMO-ADMIN-OPT-NAME(I) PIC X(35)")
    display_text: str = Field(
        ...,
        description="COADM01C STRING result: '{num}. {name}' (OPTN001O..OPTN010O)",
    )
    program_name: str = Field(..., description="CDEMO-ADMIN-OPT-PGMNAME(I) PIC X(08)")
    transaction_id: str = Field(..., description="CDEMO-ADMIN-OPT-TRANID(I) PIC X(04)")
    rest_endpoint: str = Field(..., description="Equivalent REST endpoint path (modernized mapping)")
    is_installed: bool = Field(
        ...,
        description=(
            "COADM01C: True if CDEMO-ADMIN-OPT-PGMNAME(1:5) != 'DUMMY'. "
            "Uninstalled options show 'This option is not installed ...' message."
        ),
    )


class AdminMenuResponse(BaseModel):
    """
    Admin menu response — maps to COADM01C SEND-MENU-SCREEN output.

    COADM01C SEND-MENU-SCREEN:
      PERFORM BUILD-MENU-OPTIONS
      EXEC CICS SEND MAP('COADM1A') MAPSET('COADM01') FROM(COADM1AO) ERASE

    Response includes all options that BUILD-MENU-OPTIONS iterates through
    (WS-IDX = 1 to CDEMO-ADMIN-OPT-COUNT).
    """

    transaction_id: str = Field(
        default="CA00",
        description="WS-TRANID PIC X(04) = 'CA00' — CICS transaction ID for COADM01C",
    )
    program_name: str = Field(
        default="COADM01C",
        description="WS-PGMNAME PIC X(08) — source CICS program",
    )
    menu_title: str = Field(
        default="Credit Card Demo - Admin Functions Menu",
        description="CCDA-TITLE01 / CCDA-TITLE02 (COPY COTTL01Y)",
    )
    option_count: int = Field(
        default=8,
        description="CDEMO-ADMIN-OPT-COUNT PIC 9(02) = 8",
    )
    menu_items: list[AdminMenuItem] = Field(
        ...,
        description="All menu options (COADM01C BUILD-MENU-OPTIONS: WS-IDX = 1 to CDEMO-ADMIN-OPT-COUNT)",
    )
