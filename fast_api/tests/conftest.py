"""Pytest fixtures for unit and integration tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.models.account import Account
from app.models.card import Card
from app.models.customer import Customer
from app.repositories.account_repository import AccountRepository, AccountWithRelations
from app.services.account_service import AccountService

from datetime import date, datetime
from decimal import Decimal


# ---------------------------------------------------------------------------
# Sample data fixtures — mirrors seed_data.sql
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_account() -> Account:
    """A single account object matching seed row 00000000001."""
    acct = Account()
    acct.acct_id = "00000000001"
    acct.acct_active_status = "Y"
    acct.acct_curr_bal = Decimal("1250.75")
    acct.acct_credit_limit = Decimal("10000.00")
    acct.acct_cash_credit_limit = Decimal("2000.00")
    acct.acct_open_date = date(2020, 1, 15)
    acct.acct_expiration_date = date(2026, 1, 31)
    acct.acct_reissue_date = date(2024, 1, 31)
    acct.acct_curr_cyc_credit = Decimal("500.00")
    acct.acct_curr_cyc_debit = Decimal("1750.75")
    acct.acct_addr_zip = "20500"
    acct.acct_group_id = "PREMIUM"
    acct.updated_at = datetime(2024, 1, 1, 12, 0, 0)
    return acct


@pytest.fixture
def sample_customer() -> Customer:
    """A single customer object matching seed row 000000001."""
    cust = Customer()
    cust.cust_id = "000000001"
    cust.cust_first_name = "James"
    cust.cust_middle_name = "Earl"
    cust.cust_last_name = "Carter"
    cust.cust_addr_line_1 = "1600 Pennsylvania Ave NW"
    cust.cust_addr_line_2 = "Suite 100"
    cust.cust_addr_line_3 = None
    cust.cust_addr_state_cd = "DC"
    cust.cust_addr_country_cd = "USA"
    cust.cust_addr_zip = "20500"
    cust.cust_phone_num_1 = "(202)456-1111"
    cust.cust_phone_num_2 = "(202)456-2222"
    cust.cust_ssn = "123456789"
    cust.cust_govt_issued_id = "DL-DC-001234"
    cust.cust_dob = date(1960, 3, 15)
    cust.cust_eft_account_id = "1234567890"
    cust.cust_pri_card_holder_ind = "Y"
    cust.cust_fico_credit_score = 780
    cust.updated_at = datetime(2024, 1, 1, 12, 0, 0)
    return cust


@pytest.fixture
def sample_card() -> Card:
    """A single card object."""
    card = Card()
    card.card_num = "4111111111111001"
    card.card_acct_id = "00000000001"
    card.card_embossed_name = "JAMES E CARTER"
    card.card_expiration_date = date(2026, 1, 31)
    card.card_active_status = "Y"
    return card


@pytest.fixture
def sample_account_with_relations(
    sample_account, sample_customer, sample_card
) -> AccountWithRelations:
    """Complete AccountWithRelations as returned by the repository."""
    return AccountWithRelations(
        account=sample_account,
        customer=sample_customer,
        cards=[sample_card],
    )


# ---------------------------------------------------------------------------
# Mock repository fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_repo() -> AsyncMock:
    """Mock AccountRepository for unit testing the service layer."""
    return AsyncMock(spec=AccountRepository)


@pytest.fixture
def account_service(mock_repo) -> AccountService:
    """AccountService wired to the mock repository."""
    return AccountService(mock_repo)
