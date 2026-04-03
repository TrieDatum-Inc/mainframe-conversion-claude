"""Menu service — business logic from COMEN01C (Main Menu) and COADM01C (Admin Menu).

Maps COBOL paragraphs:
  BUILD-MENU-OPTIONS     → get_main_menu() / get_admin_menu()
  PROCESS-ENTER-KEY      → navigate()
  RETURN-TO-SIGNON-SCREEN (PF3) → logout handled in auth router

COMEN02Y menu option table (compiled into COBOL load module) is represented here
as Python constants — same data, same option numbers, same program names.

COADM02Y admin option table likewise represented as Python constants.

Business rules preserved:
  BR-003 (COMEN01C): Option must be numeric, non-zero, in range 1-11 for main menu
  BR-003 (COADM01C): Option must be in range 1-6 for admin menu
  BR-004 (COMEN01C): Regular users cannot select Admin-only options
  BR-005 (COMEN01C): COPAUS0C special availability check (authorization extension)
  BR-006 (COMEN01C): DUMMY programs show "coming soon" in GREEN
  BR-004 (COADM01C): DUMMY programs treated as "not installed" in GREEN
  BR-005 (COADM01C): PGMIDERR — non-existent programs show "not installed" in GREEN
  BR-009 (COADM01C): No per-option access control in admin menu
"""
import logging
from datetime import UTC, datetime

from app.schemas.auth import (
    MenuOption,
    MenuResponse,
    NavigateRequest,
    NavigateResponse,
    UserInfo,
)

logger = logging.getLogger(__name__)

# ============================================================
# COMEN02Y data — Main Menu Options (CARDDEMO-MAIN-MENU-OPTIONS)
# CDEMO-MENU-OPT-COUNT = 11
# Each entry: (num, name, program, user_type, route)
# ============================================================
_MAIN_MENU_OPTIONS: list[tuple[int, str, str, str, str]] = [
    (1,  "Account View",               "COACTVWC", "U", "/account/view"),
    (2,  "Account Update",             "COACTUPC", "U", "/account/update"),
    (3,  "Credit Card List",           "COCRDLIC",  "U", "/cards/list"),
    (4,  "Credit Card View",           "COCRDSLC",  "U", "/cards/view"),
    (5,  "Credit Card Update",         "COCRDUPC",  "U", "/cards/update"),
    (6,  "Transaction List",           "COTRN00C", "U", "/transactions/list"),
    (7,  "Transaction View",           "COTRN01C", "U", "/transactions/view"),
    (8,  "Transaction Add",            "COTRN02C", "U", "/transactions/add"),
    (9,  "Transaction Reports",        "CORPT00C", "U", "/reports"),
    (10, "Bill Payment",               "COBIL00C", "U", "/billing/payment"),
    (11, "Pending Authorization View", "COPAUS0C",  "U", "/authorization/pending"),
]

# ============================================================
# COADM02Y data — Admin Menu Options (CARDDEMO-ADMIN-MENU-OPTIONS)
# CDEMO-ADMIN-OPT-COUNT = 6
# Admin menu has no user_type discriminator per option (BR-009 COADM01C)
# ============================================================
_ADMIN_MENU_OPTIONS: list[tuple[int, str, str, str]] = [
    (1, "User List (Security)",              "COUSR00C",  "/admin/users/list"),
    (2, "User Add (Security)",               "COUSR01C",  "/admin/users/add"),
    (3, "User Update (Security)",            "COUSR02C",  "/admin/users/update"),
    (4, "User Delete (Security)",            "COUSR03C",  "/admin/users/delete"),
    (5, "Transaction Type List/Update (Db2)", "COTRTLIC", "/admin/transaction-types"),
    (6, "Transaction Type Maintenance (Db2)", "COTRTUPC", "/admin/transaction-types/edit"),
]

# Programs that require special availability checks (CICS INQUIRE equivalent)
# COMEN01C BR-005: COPAUS0C requires authorization extension to be installed
_EXTENSION_PROGRAMS = {"COPAUS0C", "COTRTLIC", "COTRTUPC"}

# Programs not yet implemented (start with 'DUMMY') — BR-006 COMEN01C
# No DUMMY entries in current data, but the check is preserved per spec
_COMING_SOON_MSG = "This option ... is coming soon ..."
_NOT_INSTALLED_MSG = "This option is not installed ..."


class MenuNavigationError(Exception):
    """Raised when navigation fails — invalid option or access denied."""

    def __init__(self, message: str, message_type: str = "error") -> None:
        super().__init__(message)
        self.message = message
        self.message_type = message_type


class MenuService:
    """Business logic for main menu (COMEN01C) and admin menu (COADM01C)."""

    def get_main_menu(self, user: UserInfo) -> MenuResponse:
        """Build main menu response — maps COMEN01C SEND-MENU-SCREEN + BUILD-MENU-OPTIONS.

        BR-004: Admin-only options are marked but visible (enforcement at navigation).
        BR-005: COPAUS0C availability is checked here to pre-mark the option.
        BR-006: DUMMY programs are marked as coming soon.
        """
        options = [
            self._build_main_option(entry) for entry in _MAIN_MENU_OPTIONS
        ]
        return MenuResponse(
            menu_type="main",
            title="Main Menu",
            user=user,
            options=options,
            server_time=datetime.now(UTC),
            transaction_id="CM00",
            program_name="COMEN01C",
        )

    def get_admin_menu(self, user: UserInfo) -> MenuResponse:
        """Build admin menu response — maps COADM01C SEND-MENU-SCREEN + BUILD-MENU-OPTIONS.

        BR-009: No per-option user type check in admin menu.
        Admin access is already validated by the route guard (user_type='A' check).
        """
        options = [
            self._build_admin_option(entry) for entry in _ADMIN_MENU_OPTIONS
        ]
        return MenuResponse(
            menu_type="admin",
            title="Admin Menu",
            user=user,
            options=options,
            server_time=datetime.now(UTC),
            transaction_id="CA00",
            program_name="COADM01C",
        )

    def navigate_main_menu(
        self, request: NavigateRequest, user: UserInfo
    ) -> NavigateResponse:
        """Process main menu option selection — maps COMEN01C PROCESS-ENTER-KEY.

        BR-003 (COMEN01C): Valid range 1-11; zero and >11 rejected.
        BR-004 (COMEN01C): Regular users blocked from Admin-only options.
        BR-005 (COMEN01C): COPAUS0C special availability check.
        BR-006 (COMEN01C): DUMMY options return "coming soon".
        """
        self._validate_main_option(request.option)

        entry = _MAIN_MENU_OPTIONS[request.option - 1]
        opt_num, name, program, required_type, route = entry

        # BR-004: Access control check for admin-only options
        if required_type == "A" and user.user_type == "U":
            raise MenuNavigationError("No access - Admin Only option... ")

        # BR-006: DUMMY programs show "coming soon"
        if program.startswith("DUMMY"):
            raise MenuNavigationError(_COMING_SOON_MSG, message_type="info")

        # BR-005: Extension program availability check (replaces CICS INQUIRE)
        if program in _EXTENSION_PROGRAMS:
            msg = self._check_extension_availability(program)
            if msg:
                raise MenuNavigationError(msg, message_type="info")

        return NavigateResponse(
            option_selected=opt_num,
            program_name=program,
            route=route,
        )

    def navigate_admin_menu(
        self, request: NavigateRequest, user: UserInfo
    ) -> NavigateResponse:
        """Process admin menu option selection — maps COADM01C PROCESS-ENTER-KEY.

        BR-003 (COADM01C): Valid range 1-6.
        BR-004 (COADM01C): DUMMY options treated as "not installed".
        BR-005 (COADM01C): Missing programs handled gracefully (PGMIDERR equivalent).
        BR-009 (COADM01C): No per-option user type check.
        """
        self._validate_admin_option(request.option)

        entry = _ADMIN_MENU_OPTIONS[request.option - 1]
        opt_num, name, program, route = entry

        # BR-004 COADM01C: DUMMY programs treated as "not installed" (no separate message)
        if program.startswith("DUMMY"):
            raise MenuNavigationError(_NOT_INSTALLED_MSG, message_type="info")

        # BR-005 COADM01C: Extension program check (PGMIDERR equivalent)
        if program in _EXTENSION_PROGRAMS:
            msg = self._check_extension_availability(program)
            if msg:
                raise MenuNavigationError(msg, message_type="info")

        return NavigateResponse(
            option_selected=opt_num,
            program_name=program,
            route=route,
        )

    def _validate_main_option(self, option: int) -> None:
        """Validate option range for main menu — maps COMEN01C PROCESS-ENTER-KEY validation.

        COBOL: IF WS-OPTION IS NOT NUMERIC OR WS-OPTION > CDEMO-MENU-OPT-COUNT OR WS-OPTION = ZEROS
        """
        if option < 1 or option > len(_MAIN_MENU_OPTIONS):
            raise MenuNavigationError(
                "Please enter a valid option number..."
            )

    def _validate_admin_option(self, option: int) -> None:
        """Validate option range for admin menu — maps COADM01C PROCESS-ENTER-KEY validation.

        COBOL: IF WS-OPTION IS NOT NUMERIC OR WS-OPTION > CDEMO-ADMIN-OPT-COUNT OR WS-OPTION = ZEROS
        """
        if option < 1 or option > len(_ADMIN_MENU_OPTIONS):
            raise MenuNavigationError(
                "Please enter a valid option number..."
            )

    def _check_extension_availability(self, program: str) -> str | None:
        """Check if an extension program is available — replaces EXEC CICS INQUIRE PROGRAM.

        COMEN01C BR-005: COPAUS0C requires the authorization extension.
        COADM01C BR-005: COTRTLIC/COTRTUPC require the transaction type extension.

        In the modern stack, extension availability is determined by checking
        if the corresponding API endpoints exist (feature flags or deployment checks).
        Currently returns None (available) for all programs; can be extended
        with actual feature flag checks.

        Returns error message string if unavailable, None if available.
        """
        # TODO: Implement actual feature flag check for extension programs
        # For now, COPAUS0C is treated as not installed (authorization extension not deployed)
        # COTRTLIC/COTRTUPC are treated as available (transaction type extension deployed)
        if program == "COPAUS0C":
            return _NOT_INSTALLED_MSG
        return None

    def _build_main_option(
        self, entry: tuple[int, str, str, str, str]
    ) -> MenuOption:
        """Build a MenuOption from a COMEN02Y table entry."""
        opt_num, name, program, required_type, route = entry
        is_dummy = program.startswith("DUMMY")
        is_extension = program in _EXTENSION_PROGRAMS

        is_available = True
        availability_message = None

        if is_dummy:
            is_available = False
            availability_message = _COMING_SOON_MSG
        elif is_extension and program == "COPAUS0C":
            is_available = False
            availability_message = _NOT_INSTALLED_MSG

        return MenuOption(
            option_number=opt_num,
            name=name,
            program_name=program,
            route=route,
            required_user_type=required_type,
            is_available=is_available,
            availability_message=availability_message,
        )

    def _build_admin_option(
        self, entry: tuple[int, str, str, str]
    ) -> MenuOption:
        """Build a MenuOption from a COADM02Y table entry."""
        opt_num, name, program, route = entry
        is_dummy = program.startswith("DUMMY")

        is_available = not is_dummy
        availability_message = _NOT_INSTALLED_MSG if is_dummy else None

        return MenuOption(
            option_number=opt_num,
            name=name,
            program_name=program,
            route=route,
            required_user_type="A",  # All admin menu options require admin
            is_available=is_available,
            availability_message=availability_message,
        )
