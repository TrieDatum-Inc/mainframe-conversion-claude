"""
Admin service — business logic from COADM01C (CICS transaction CA00).

Source program: app/cbl/COADM01C.cbl
Function: Admin navigation menu with up to 10 options.

COADM01C paragraph mapping:
  BUILD-MENU-OPTIONS  → get_admin_menu()
  PROCESS-ENTER-KEY   → validate_menu_selection()

Copybook: COADM02Y defines CARDDEMO-ADMIN-OPTS table.
  CDEMO-ADMIN-OPT-COUNT   PIC 9(02) VALUE 8
  CDEMO-ADMIN-OPT-PGMNAME OCCURS 10 PIC X(08)
  CDEMO-ADMIN-OPT-TRANID  OCCURS 10 PIC X(04)
  CDEMO-ADMIN-OPT-NUM     OCCURS 10 PIC 9(02)
  CDEMO-ADMIN-OPT-NAME    OCCURS 10 PIC X(35)

Business rules preserved:
  1. Exactly 8 menu options are active (CDEMO-ADMIN-OPT-COUNT = 8)
     (remaining slots up to 10 are empty or 'DUMMY')
  2. Option text formatted as '{num}. {name}'
     (COADM01C BUILD-MENU-OPTIONS: STRING CDEMO-ADMIN-OPT-NUM '. ' CDEMO-ADMIN-OPT-NAME)
  3. Options with program name starting 'DUMMY' are flagged as not installed
     (COADM01C: IF CDEMO-ADMIN-OPT-PGMNAME(WS-OPTION)(1:5) NOT = 'DUMMY')
  4. Option selection (1..N) must be numeric and within range
     (COADM01C PROCESS-ENTER-KEY:
       IF WS-OPTION IS NOT NUMERIC OR WS-OPTION > CDEMO-ADMIN-OPT-COUNT ...)
"""
from app.schemas.admin import AdminMenuItem, AdminMenuResponse

# ---------------------------------------------------------------------------
# Static menu definition from COADM02Y copybook data
# ---------------------------------------------------------------------------
# Original CICS COBOL COADM02Y values (partially reconstructed from COADM01C):
#   Option 1: COUSR00C (CA00) — User Management
#   Option 2: CORPT00C (CR00) — Report Generation
#   Option 3-8: Additional admin functions (some 'DUMMY' placeholders)
#
# Format per option: (opt_num, name, program_name, trans_id, rest_endpoint)
_ADMIN_MENU_DEFINITION: list[tuple[int, str, str, str, str]] = [
    (1,  "User Management",          "COUSR00C", "CU00", "/api/v1/admin/users"),
    (2,  "Transaction Reports",      "CORPT00C", "CR00", "/api/v1/reports/transactions"),
    (3,  "Transaction Type Maint",   "COTRTLIC", "CTLI", "/api/v1/transaction-types"),
    (4,  "Account View",             "COACTVWC", "CA0V", "/api/v1/accounts"),
    (5,  "Account Update",           "COACTUPC", "CA0U", "/api/v1/accounts/{id}"),
    (6,  "Card List",                "COCRDLIC", "CC0L", "/api/v1/cards"),
    (7,  "Transaction List",         "COTRN00C", "CT00", "/api/v1/transactions"),
    (8,  "Bill Payment",             "COBIL00C", "CB00", "/api/v1/accounts/{id}/payments"),
    (9,  "Credit Card Update",       "DUMMY001", "XXXX", ""),   # CDEMO-ADMIN-OPT-COUNT = 8; unused slots
    (10, "Statement",                "DUMMY002", "XXXX", ""),
]

# CDEMO-ADMIN-OPT-COUNT PIC 9(02) VALUE 8
_ADMIN_OPT_COUNT: int = 8


class AdminService:
    """Business logic for admin menu (COADM01C)."""

    def get_admin_menu(self) -> AdminMenuResponse:
        """
        COADM01C BUILD-MENU-OPTIONS paragraph.

        Builds all menu items by iterating WS-IDX from 1 to CDEMO-ADMIN-OPT-COUNT.
        For each option:
          - Formats display text: STRING CDEMO-ADMIN-OPT-NUM '. ' CDEMO-ADMIN-OPT-NAME
            INTO WS-ADMIN-OPT-TXT
          - Determines if installed: CDEMO-ADMIN-OPT-PGMNAME(I)(1:5) NOT = 'DUMMY'

        Returns:
            AdminMenuResponse with all menu items and metadata.
        """
        items = [self._build_menu_item(opt) for opt in _ADMIN_MENU_DEFINITION]
        active_items = [i for i in items if i.option_number <= _ADMIN_OPT_COUNT]

        return AdminMenuResponse(
            transaction_id="CA00",
            program_name="COADM01C",
            menu_title="Credit Card Demo - Admin Functions Menu",
            option_count=_ADMIN_OPT_COUNT,
            menu_items=active_items,
        )

    def validate_menu_selection(self, option: int) -> AdminMenuItem:
        """
        COADM01C PROCESS-ENTER-KEY paragraph.

        Validates and resolves a menu option selection.

        Business rules:
          1. WS-OPTION must be numeric (already enforced by int type hint)
          2. WS-OPTION > CDEMO-ADMIN-OPT-COUNT OR WS-OPTION = ZEROS → error
             'Please enter a valid option number...'
          3. If program name starts with 'DUMMY':
             'This option is not installed ...'

        Args:
            option: Numeric option selected (OPTIONI OF COADM1AI).

        Returns:
            AdminMenuItem for the selected option.

        Raises:
            ValueError: Invalid option number or uninstalled option.
        """
        if option < 1 or option > _ADMIN_OPT_COUNT:
            raise ValueError(
                f"Please enter a valid option number (1-{_ADMIN_OPT_COUNT})"
            )

        opt_def = _ADMIN_MENU_DEFINITION[option - 1]
        item = self._build_menu_item(opt_def)

        if not item.is_installed:
            raise ValueError(f"This option is not installed (option={option})")

        return item

    @staticmethod
    def _build_menu_item(
        opt: tuple[int, str, str, str, str],
    ) -> AdminMenuItem:
        """
        COADM01C BUILD-MENU-OPTIONS single iteration.

        STRING CDEMO-ADMIN-OPT-NUM(WS-IDX)  DELIMITED BY SIZE
               '. '                         DELIMITED BY SIZE
               CDEMO-ADMIN-OPT-NAME(WS-IDX) DELIMITED BY SIZE
          INTO WS-ADMIN-OPT-TXT

        Args:
            opt: Tuple (opt_num, name, program_name, trans_id, rest_endpoint).

        Returns:
            AdminMenuItem instance.
        """
        opt_num, name, program_name, trans_id, rest_endpoint = opt
        display_text = f"{opt_num:02d}. {name}"
        is_installed = not program_name.upper().startswith("DUMMY")

        return AdminMenuItem(
            option_number=opt_num,
            name=name,
            display_text=display_text,
            program_name=program_name,
            transaction_id=trans_id,
            rest_endpoint=rest_endpoint,
            is_installed=is_installed,
        )
