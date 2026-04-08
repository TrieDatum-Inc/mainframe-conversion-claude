"""
Unit tests for AdminService — business logic from COADM01C.

Tests verify all business rules:
  1. Menu returns exactly CDEMO-ADMIN-OPT-COUNT (8) active options
  2. Display text formatted as '{num:02d}. {name}' (BUILD-MENU-OPTIONS STRING)
  3. Installed flag: False for 'DUMMY' program names (PGMIDERR-ERR-PARA)
  4. Option validation: numeric, in range 1..8 (PROCESS-ENTER-KEY)
  5. Invalid option → ValueError 'Please enter a valid option number...'
"""
import pytest

from app.services.admin_service import AdminService, _ADMIN_OPT_COUNT


class TestAdminService:
    """Tests for COADM01C business logic."""

    def test_get_admin_menu_returns_correct_option_count(self) -> None:
        """
        COADM01C: CDEMO-ADMIN-OPT-COUNT PIC 9(02) VALUE 8.
        Menu must return exactly 8 active options.
        """
        service = AdminService()
        result = service.get_admin_menu()

        assert result.option_count == _ADMIN_OPT_COUNT
        assert len(result.menu_items) == _ADMIN_OPT_COUNT

    def test_menu_item_display_text_format(self) -> None:
        """
        COADM01C BUILD-MENU-OPTIONS:
          STRING CDEMO-ADMIN-OPT-NUM(WS-IDX) '. ' CDEMO-ADMIN-OPT-NAME(WS-IDX)
            INTO WS-ADMIN-OPT-TXT
        Display text must be '{num:02d}. {name}'.
        """
        service = AdminService()
        result = service.get_admin_menu()

        for item in result.menu_items:
            expected_prefix = f"{item.option_number:02d}. "
            assert item.display_text.startswith(expected_prefix), (
                f"Option {item.option_number} display_text {item.display_text!r} "
                f"must start with {expected_prefix!r}"
            )

    def test_installed_options_have_non_dummy_program_names(self) -> None:
        """
        COADM01C: IF CDEMO-ADMIN-OPT-PGMNAME(WS-OPTION)(1:5) NOT = 'DUMMY'
        Installed options must not have program_name starting with 'DUMMY'.
        """
        service = AdminService()
        result = service.get_admin_menu()

        for item in result.menu_items:
            if item.is_installed:
                assert not item.program_name.upper().startswith("DUMMY"), (
                    f"Installed option {item.option_number} has 'DUMMY' program name"
                )

    def test_dummy_options_flagged_as_not_installed(self) -> None:
        """
        COADM01C PGMIDERR-ERR-PARA: 'This option is not installed ...'
        Options with 'DUMMY' program names must have is_installed=False.
        """
        service = AdminService()
        result = service.get_admin_menu()

        for item in result.menu_items:
            if item.program_name.upper().startswith("DUMMY"):
                assert not item.is_installed

    def test_option_numbers_are_sequential(self) -> None:
        """
        COADM01C: CDEMO-ADMIN-OPT-NUM(I) PIC 9(02)
        Option numbers must be 1..8 in the returned menu.
        """
        service = AdminService()
        result = service.get_admin_menu()

        numbers = [item.option_number for item in result.menu_items]
        assert numbers == list(range(1, _ADMIN_OPT_COUNT + 1))

    def test_transaction_id_is_ca00(self) -> None:
        """
        COADM01C: WS-TRANID PIC X(04) VALUE 'CA00'
        Menu response must include CICS transaction ID CA00.
        """
        service = AdminService()
        result = service.get_admin_menu()

        assert result.transaction_id == "CA00"

    def test_program_name_is_coadm01c(self) -> None:
        """
        COADM01C: WS-PGMNAME PIC X(08) VALUE 'COADM01C'
        Menu response must identify source program.
        """
        service = AdminService()
        result = service.get_admin_menu()

        assert result.program_name == "COADM01C"

    def test_validate_selection_valid_option_returns_item(self) -> None:
        """
        COADM01C PROCESS-ENTER-KEY: valid option returns program details for XCTL.
        """
        service = AdminService()
        item = service.validate_menu_selection(1)  # Option 1 = User Management

        assert item.option_number == 1
        assert item.is_installed

    def test_validate_selection_zero_raises(self) -> None:
        """
        COADM01C PROCESS-ENTER-KEY:
          IF WS-OPTION = ZEROS → 'Please enter a valid option number...'
        """
        service = AdminService()
        with pytest.raises(ValueError, match="valid option"):
            service.validate_menu_selection(0)

    def test_validate_selection_above_max_raises(self) -> None:
        """
        COADM01C PROCESS-ENTER-KEY:
          IF WS-OPTION > CDEMO-ADMIN-OPT-COUNT → 'Please enter a valid option number...'
        """
        service = AdminService()
        with pytest.raises(ValueError, match="valid option"):
            service.validate_menu_selection(_ADMIN_OPT_COUNT + 1)

    def test_validate_selection_all_valid_installed_options(self) -> None:
        """All installed options (1..8 minus DUMMY) must resolve without error."""
        service = AdminService()
        menu = service.get_admin_menu()

        for item in menu.menu_items:
            if item.is_installed:
                resolved = service.validate_menu_selection(item.option_number)
                assert resolved.option_number == item.option_number

    def test_all_installed_items_have_rest_endpoints(self) -> None:
        """Installed options must have a non-empty rest_endpoint (XCTL replacement)."""
        service = AdminService()
        result = service.get_admin_menu()

        for item in result.menu_items:
            if item.is_installed:
                assert item.rest_endpoint, (
                    f"Installed option {item.option_number} missing rest_endpoint"
                )

    def test_all_installed_items_have_transaction_ids(self) -> None:
        """Installed options must have 4-char CICS transaction IDs."""
        service = AdminService()
        result = service.get_admin_menu()

        for item in result.menu_items:
            if item.is_installed:
                assert len(item.transaction_id) == 4, (
                    f"Option {item.option_number} transaction_id {item.transaction_id!r} "
                    "must be 4 chars (PIC X(04))"
                )
