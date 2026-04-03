"""Unit tests for MenuService — maps COMEN01C and COADM01C business rules."""
import pytest

from app.schemas.auth import NavigateRequest, UserInfo
from app.services.menu_service import MenuNavigationError, MenuService


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def menu_service() -> MenuService:
    return MenuService()


@pytest.fixture
def admin_user() -> UserInfo:
    return UserInfo(
        user_id="ADMIN001", first_name="System", last_name="Admin", user_type="A"
    )


@pytest.fixture
def regular_user() -> UserInfo:
    return UserInfo(
        user_id="USER0001", first_name="John", last_name="Doe", user_type="U"
    )


# ============================================================
# Main Menu — BR-003 (COMEN01C): Option validation
# ============================================================

class TestMainMenuOptionValidation:
    """COMEN01C BR-003: Option must be numeric, non-zero, in range 1-11."""

    def test_option_zero_rejected_by_pydantic_schema(self):
        """BR-003: Option 0 is invalid — Pydantic schema enforces ge=1."""
        with pytest.raises(Exception):
            NavigateRequest(option=0)

    def test_option_12_rejected(self, menu_service, regular_user):
        """Option 12 exceeds CDEMO-MENU-OPT-COUNT = 11."""
        # Pydantic schema rejects >11 at schema level
        with pytest.raises(Exception):
            NavigateRequest(option=12)

    def test_valid_option_1_accepted(self, menu_service, regular_user):
        """Option 1 (Account View) must be valid for regular user."""
        result = menu_service.navigate_main_menu(
            NavigateRequest(option=1), regular_user
        )
        assert result.option_selected == 1
        assert result.program_name == "COACTVWC"

    def test_valid_option_11_returns_not_installed(self, menu_service, regular_user):
        """Option 11 (COPAUS0C) is the authorization extension — not installed by default."""
        with pytest.raises(MenuNavigationError) as exc_info:
            menu_service.navigate_main_menu(
                NavigateRequest(option=11), regular_user
            )
        assert "not installed" in exc_info.value.message


# ============================================================
# Main Menu — BR-004 (COMEN01C): Admin-only option access control
# ============================================================

class TestMainMenuAccessControl:
    """COMEN01C BR-004: Regular users blocked from Admin-only options."""

    def test_regular_user_can_select_user_options(self, menu_service, regular_user):
        """Regular user (type='U') can select options with required_type='U'."""
        for opt in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
            result = menu_service.navigate_main_menu(
                NavigateRequest(option=opt), regular_user
            )
            assert result.option_selected == opt

    def test_regular_user_blocked_from_admin_only(self, menu_service, regular_user):
        """Regular user cannot access Admin-only option."""
        # Temporarily patch an option to admin-only to test the guard
        # In current data all main menu options are 'U' type, so we test the guard directly
        from app.services import menu_service as ms_module
        original = ms_module._MAIN_MENU_OPTIONS[0]
        ms_module._MAIN_MENU_OPTIONS[0] = (
            1, "Admin Only Option", "SOMEPRG0", "A", "/some-route"
        )
        try:
            with pytest.raises(MenuNavigationError) as exc_info:
                menu_service.navigate_main_menu(
                    NavigateRequest(option=1), regular_user
                )
            assert "Admin Only" in exc_info.value.message
        finally:
            ms_module._MAIN_MENU_OPTIONS[0] = original

    def test_admin_user_can_select_any_main_menu_option(self, menu_service, admin_user):
        """Admin user (type='A') can select any main menu option including admin-only."""
        result = menu_service.navigate_main_menu(
            NavigateRequest(option=1), admin_user
        )
        assert result.option_selected == 1


# ============================================================
# Main Menu — BR-005 (COMEN01C): COPAUS0C extension check
# ============================================================

class TestMainMenuCopaus0cCheck:
    """COMEN01C BR-005: COPAUS0C requires authorization extension to be installed."""

    def test_option_11_returns_not_installed_message(self, menu_service, regular_user):
        """Option 11 (COPAUS0C) should raise error with 'not installed' message."""
        with pytest.raises(MenuNavigationError) as exc_info:
            menu_service.navigate_main_menu(
                NavigateRequest(option=11), regular_user
            )
        assert exc_info.value.message == "This option is not installed ..."

    def test_option_11_message_type_is_info(self, menu_service, regular_user):
        """Not-installed message should be 'info' type (GREEN in COBOL)."""
        with pytest.raises(MenuNavigationError) as exc_info:
            menu_service.navigate_main_menu(
                NavigateRequest(option=11), regular_user
            )
        assert exc_info.value.message_type == "info"


# ============================================================
# Main Menu — get_main_menu display
# ============================================================

class TestGetMainMenu:
    """COMEN01C BUILD-MENU-OPTIONS and POPULATE-HEADER-INFO."""

    def test_returns_11_options(self, menu_service, regular_user):
        """Main menu must have exactly 11 options (CDEMO-MENU-OPT-COUNT = 11)."""
        result = menu_service.get_main_menu(regular_user)
        assert len(result.options) == 11

    def test_transaction_id_is_cm00(self, menu_service, regular_user):
        """TRNNAMEO must be 'CM00' for COMEN01C."""
        result = menu_service.get_main_menu(regular_user)
        assert result.transaction_id == "CM00"

    def test_program_name_is_comen01c(self, menu_service, regular_user):
        """PGMNAMEO must be 'COMEN01C'."""
        result = menu_service.get_main_menu(regular_user)
        assert result.program_name == "COMEN01C"

    def test_menu_type_is_main(self, menu_service, regular_user):
        result = menu_service.get_main_menu(regular_user)
        assert result.menu_type == "main"

    def test_option_numbers_are_1_through_11(self, menu_service, regular_user):
        """Option numbers must be sequential 1-11 (CDEMO-MENU-OPT-NUM)."""
        result = menu_service.get_main_menu(regular_user)
        numbers = [opt.option_number for opt in result.options]
        assert numbers == list(range(1, 12))

    def test_option_11_marked_unavailable(self, menu_service, regular_user):
        """COPAUS0C (option 11) should be marked as unavailable."""
        result = menu_service.get_main_menu(regular_user)
        opt11 = result.options[10]
        assert opt11.program_name == "COPAUS0C"
        assert opt11.is_available is False

    def test_option_1_name_matches_cobol_data(self, menu_service, regular_user):
        """Option 1 must have name 'Account View' from COMEN02Y."""
        result = menu_service.get_main_menu(regular_user)
        assert result.options[0].name == "Account View"


# ============================================================
# Admin Menu — BR-003 (COADM01C): Option validation
# ============================================================

class TestAdminMenuOptionValidation:
    """COADM01C BR-003: Valid range 1-6 (CDEMO-ADMIN-OPT-COUNT = 6)."""

    def test_option_7_rejected(self, menu_service, admin_user):
        """Option 7 exceeds CDEMO-ADMIN-OPT-COUNT = 6."""
        with pytest.raises(MenuNavigationError) as exc_info:
            menu_service.navigate_admin_menu(
                NavigateRequest(option=7), admin_user
            )
        assert "valid option" in exc_info.value.message

    def test_valid_option_1_accepted(self, menu_service, admin_user):
        """Option 1 (User List) is valid for admin user."""
        result = menu_service.navigate_admin_menu(
            NavigateRequest(option=1), admin_user
        )
        assert result.option_selected == 1
        assert result.program_name == "COUSR00C"

    def test_valid_options_1_through_6(self, menu_service, admin_user):
        """All options 1-6 must be valid for admin users."""
        for opt in range(1, 7):
            result = menu_service.navigate_admin_menu(
                NavigateRequest(option=opt), admin_user
            )
            assert result.option_selected == opt


# ============================================================
# Admin Menu — get_admin_menu display
# ============================================================

class TestGetAdminMenu:
    """COADM01C BUILD-MENU-OPTIONS and POPULATE-HEADER-INFO."""

    def test_returns_6_options(self, menu_service, admin_user):
        """Admin menu must have exactly 6 options (CDEMO-ADMIN-OPT-COUNT = 6)."""
        result = menu_service.get_admin_menu(admin_user)
        assert len(result.options) == 6

    def test_transaction_id_is_ca00(self, menu_service, admin_user):
        """TRNNAMEO must be 'CA00' for COADM01C."""
        result = menu_service.get_admin_menu(admin_user)
        assert result.transaction_id == "CA00"

    def test_program_name_is_coadm01c(self, menu_service, admin_user):
        """PGMNAMEO must be 'COADM01C'."""
        result = menu_service.get_admin_menu(admin_user)
        assert result.program_name == "COADM01C"

    def test_menu_type_is_admin(self, menu_service, admin_user):
        result = menu_service.get_admin_menu(admin_user)
        assert result.menu_type == "admin"

    def test_option_1_is_user_list(self, menu_service, admin_user):
        """Option 1 must be 'User List (Security)' from COADM02Y."""
        result = menu_service.get_admin_menu(admin_user)
        assert result.options[0].name == "User List (Security)"
        assert result.options[0].program_name == "COUSR00C"

    def test_option_5_is_transaction_type_list(self, menu_service, admin_user):
        """Option 5 is COTRTLIC (DB2 extension, added in v2.0)."""
        result = menu_service.get_admin_menu(admin_user)
        assert result.options[4].program_name == "COTRTLIC"

    def test_all_options_require_admin_type(self, menu_service, admin_user):
        """All admin menu options should have required_user_type='A' (BR-009)."""
        result = menu_service.get_admin_menu(admin_user)
        for opt in result.options:
            assert opt.required_user_type == "A"


# ============================================================
# Admin Menu — BR-004 (COADM01C): DUMMY option handling
# ============================================================

class TestAdminMenuDummyOptions:
    """COADM01C BR-004: DUMMY programs → 'not installed' message (not 'coming soon')."""

    def test_dummy_option_raises_not_installed(self, menu_service, admin_user):
        """DUMMY program in admin menu should show 'not installed' (not 'coming soon')."""
        from app.services import menu_service as ms_module
        original = ms_module._ADMIN_MENU_OPTIONS[0]
        ms_module._ADMIN_MENU_OPTIONS[0] = (
            1, "Dummy Option", "DUMMY000", "/dummy"
        )
        try:
            with pytest.raises(MenuNavigationError) as exc_info:
                menu_service.navigate_admin_menu(
                    NavigateRequest(option=1), admin_user
                )
            assert "not installed" in exc_info.value.message
        finally:
            ms_module._ADMIN_MENU_OPTIONS[0] = original


# ============================================================
# Security test: User model properties
# ============================================================

class TestUserModel:
    """Test User model helper properties."""

    def test_admin_user_is_admin_property(self):
        from app.models.user import User
        user = User(user_id="A1", first_name="A", last_name="B",
                    password="x", user_type="A")
        assert user.is_admin is True
        assert user.is_regular_user is False

    def test_regular_user_is_regular_property(self):
        from app.models.user import User
        user = User(user_id="U1", first_name="A", last_name="B",
                    password="x", user_type="U")
        assert user.is_admin is False
        assert user.is_regular_user is True
