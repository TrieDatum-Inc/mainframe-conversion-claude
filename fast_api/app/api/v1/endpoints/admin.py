"""
Admin menu endpoint — derived from COADM01C (CICS transaction CA00).

Source program: app/cbl/COADM01C.cbl
BMS map: COADM01 / COADM1A

CICS transaction ID: CA00

Endpoint mapping:
  GET /api/v1/admin/menu → COADM01C BUILD-MENU-OPTIONS + SEND-MENU-SCREEN

COADM01C function:
  Displays admin navigation menu with up to 10 options built from COADM02Y
  copybook (CDEMO-ADMIN-OPT-* arrays). Selecting an option XCTLs to the
  corresponding CICS program.

Modernization approach:
  - EXEC CICS SEND MAP → JSON response body
  - EXEC CICS XCTL PROGRAM(option) → REST endpoint URL in menu item rest_endpoint
  - RECEIVE MAP input → GET query param ?option=N (for navigation hint)
  - CICS PGMIDERR HANDLE → 'is_installed=false' flag in response
    (COADM01C: IF CDEMO-ADMIN-OPT-PGMNAME(WS-OPTION)(1:5) NOT = 'DUMMY')

Admin-only:
  COADM01C guards: IF EIBCALEN = 0 → COSGN00C (not authenticated)
  Enforced here via AdminUser dependency (CDEMO-USRTYP-ADMIN = 'A').
"""
from fastapi import APIRouter

from app.dependencies import AdminUser
from app.schemas.admin import AdminMenuResponse, AdminMenuItem
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["Admin (COADM01C/CA00)"])


@router.get(
    "/menu",
    response_model=AdminMenuResponse,
    summary="Admin menu options (COADM01C / CA00)",
    responses={
        200: {"description": "Admin menu metadata with all installed options"},
        403: {"description": "Admin role required (CDEMO-USRTYP-ADMIN = 'A')"},
    },
)
async def get_admin_menu(
    current_user: AdminUser,
) -> AdminMenuResponse:
    """
    Return admin navigation menu metadata.

    Derived from COADM01C BUILD-MENU-OPTIONS paragraph:

    COBOL:
      PERFORM VARYING WS-IDX FROM 1 BY 1 UNTIL WS-IDX > CDEMO-ADMIN-OPT-COUNT
          STRING CDEMO-ADMIN-OPT-NUM(WS-IDX) '. ' CDEMO-ADMIN-OPT-NAME(WS-IDX)
            INTO WS-ADMIN-OPT-TXT
          EVALUATE WS-IDX
              WHEN 1 MOVE WS-ADMIN-OPT-TXT TO OPTN001O
              ...
          END-EVALUATE
      END-PERFORM

    Returns all 8 active menu options (CDEMO-ADMIN-OPT-COUNT = 8) with:
      - display_text: formatted option label ('{num}. {name}')
      - rest_endpoint: equivalent REST endpoint path
      - is_installed: True unless program name starts with 'DUMMY'
        (COADM01C PGMIDERR-ERR-PARA: 'This option is not installed ...')
    """
    service = AdminService()
    return service.get_admin_menu()


@router.get(
    "/menu/{option}",
    response_model=AdminMenuItem,
    summary="Resolve specific admin menu option (COADM01C PROCESS-ENTER-KEY)",
    responses={
        200: {"description": "Menu option details"},
        403: {"description": "Admin role required"},
        422: {"description": "Invalid option number or option not installed"},
    },
)
async def get_admin_menu_option(
    option: int,
    current_user: AdminUser,
) -> AdminMenuItem:
    """
    Resolve and validate a specific admin menu option.

    Derived from COADM01C PROCESS-ENTER-KEY paragraph:

    COBOL:
      MOVE OPTIONI OF COADM1AI TO WS-OPTION-X
      IF WS-OPTION IS NOT NUMERIC OR WS-OPTION > CDEMO-ADMIN-OPT-COUNT OR WS-OPTION = ZEROS
          MOVE 'Please enter a valid option number...' TO WS-MESSAGE
      IF CDEMO-ADMIN-OPT-PGMNAME(WS-OPTION)(1:5) NOT = 'DUMMY'
          EXEC CICS XCTL PROGRAM(CDEMO-ADMIN-OPT-PGMNAME(WS-OPTION))
      ELSE
          STRING 'This option is not installed ...' INTO WS-MESSAGE

    The REST equivalent returns the option metadata and rest_endpoint
    for the client to navigate to, replacing the XCTL call.

    Args:
        option: Option number 1..CDEMO-ADMIN-OPT-COUNT (8).

    Returns:
        AdminMenuItem with rest_endpoint for client-side navigation.

    Raises:
        HTTP 422: Option out of range or not installed.
    """
    from fastapi import HTTPException

    service = AdminService()
    try:
        return service.validate_menu_selection(option)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
