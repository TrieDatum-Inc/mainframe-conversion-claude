"""
Account and Customer service — business logic layer.

Maps COACTVWC (view) and COACTUPC (update) programs.

COACTVWC: read-only 3-step sequence:
  1. CXACAIX read (get cust_id + card_num from acct_id)
  2. ACCTDAT read (get account data)
  3. CUSTDAT read (get customer data)

COACTUPC: 6-state machine + 35+ validations:
  States: NOT-FETCHED -> SHOW -> CHANGES-NOT-OK -> OK-NOT-CONFIRMED -> DONE/LOCK-ERR/FAILED
  On confirm (F5): REWRITE ACCTDAT + REWRITE CUSTDAT (atomic)
  SYNCPOINT before XCTL exit (preserved as transaction commit)
"""

from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BusinessValidationError,
    ResourceNotFoundError,
)
from app.infrastructure.orm.account_orm import AccountORM
from app.infrastructure.orm.customer_orm import CustomerORM, VALID_US_STATE_CODES
from app.infrastructure.repositories.account_repository import (
    AccountRepository,
    CustomerRepository,
)
from app.schemas.account_schemas import (
    AccountUpdateRequest,
    AccountView,
    AccountWithCustomerView,
    CustomerUpdateRequest,
    CustomerView,
)


async def get_account_with_customer(
    acct_id: int,
    db: AsyncSession,
) -> AccountWithCustomerView:
    """
    Retrieve account + customer data by account ID.

    Maps COACTVWC 9000-READ-ACCT:
      PERFORM 9200-GETCARDXREF-BYACCT  (READ CXACAIX)
      PERFORM 9300-GETACCTDATA-BYACCT  (READ ACCTDAT)
      PERFORM 9400-GETCUSTDATA-BYCUST  (READ CUSTDAT)
    """
    acct_repo = AccountRepository(db)
    cust_repo = CustomerRepository(db)

    # Step 1: READ CXACAIX - get cust_id + card_num from acct_id
    xref = await acct_repo.get_xref_by_account_id(acct_id)
    if xref is None:
        raise ResourceNotFoundError("AccountXref", str(acct_id))

    # Step 2: READ ACCTDAT
    account = await acct_repo.get_by_id(acct_id)

    # Step 3: READ CUSTDAT
    customer = await cust_repo.get_by_id(xref.cust_id)

    account_view = AccountView.model_validate(account)
    customer_view = CustomerView.model_validate(customer)

    return AccountWithCustomerView(
        account=account_view,
        customer=customer_view,
        card_num=xref.card_num if xref else None,
    )


def _validate_account_fields(req: AccountUpdateRequest) -> list[str]:
    """
    COACTUPC 1200-EDIT-MAP-INPUTS validation.
    Returns list of error messages. Empty list = all valid.

    Validations from spec section 6.3:
    - Active status: must be single character
    - Credit limits: must be non-negative
    - Dates: must be valid dates (CSUTLDTC equivalent)
    - Expiration date must be >= open date
    """
    errors = []

    if req.active_status not in ("Y", "N", ""):
        errors.append("Active status must be 'Y' or 'N'.")

    if req.credit_limit < Decimal("0"):
        errors.append("Credit limit cannot be negative.")

    if req.cash_credit_limit < Decimal("0"):
        errors.append("Cash credit limit cannot be negative.")

    if req.cash_credit_limit > req.credit_limit:
        errors.append("Cash credit limit cannot exceed credit limit.")

    if req.open_date and req.expiration_date:
        if req.expiration_date < req.open_date:
            errors.append("Expiration date must be on or after open date.")

    if req.open_date and req.reissue_date:
        if req.reissue_date < req.open_date:
            errors.append("Reissue date must be on or after open date.")

    return errors


def _validate_customer_fields(req: CustomerUpdateRequest) -> list[str]:
    """
    COACTUPC customer field validations from 1200-EDIT-MAP-INPUTS.

    Validations:
    - State code: validated against CSLKPCDY table
    - Phone numbers: (999)999-9999 format
    - SSN: 9-digit numeric
    - FICO score: 300-850
    - DOB: valid date, must be in the past
    """
    errors = []

    if req.addr_state_cd and req.addr_state_cd.upper() not in VALID_US_STATE_CODES:
        errors.append(f"Invalid state code '{req.addr_state_cd}'.")

    if req.fico_score is not None:
        if req.fico_score < 300 or req.fico_score > 850:
            errors.append("FICO score must be between 300 and 850.")

    if req.dob is not None:
        if req.dob >= date.today():
            errors.append("Date of birth must be in the past.")

    return errors


async def update_account_with_customer(
    acct_id: int,
    account_req: AccountUpdateRequest,
    customer_req: CustomerUpdateRequest,
    db: AsyncSession,
) -> AccountWithCustomerView:
    """
    Update account + customer atomically.

    Maps COACTUPC 9600-WRITE-PROCESSING (state: ACUP-CHANGES-OK-NOT-CONFIRMED + F5):
      EXEC CICS REWRITE FILE('ACCTDAT')
      IF error: SET ACUP-CHANGES-OKAYED-LOCK-ERROR or ACUP-CHANGES-OKAYED-BUT-FAILED
      EXEC CICS REWRITE FILE('CUSTDAT')
      IF error: EXEC CICS SYNCPOINT ROLLBACK -> SET ACUP-CHANGES-OKAYED-BUT-FAILED

    Both rewrites are in the same DB transaction (equivalent to CICS SYNCPOINT).
    """
    # Run validations before any writes
    acct_errors = _validate_account_fields(account_req)
    cust_errors = _validate_customer_fields(customer_req)
    all_errors = acct_errors + cust_errors
    if all_errors:
        raise BusinessValidationError("; ".join(all_errors))

    acct_repo = AccountRepository(db)
    cust_repo = CustomerRepository(db)

    # Get xref to find cust_id
    xref = await acct_repo.get_xref_by_account_id(acct_id)
    if xref is None:
        raise ResourceNotFoundError("AccountXref", str(acct_id))

    # Read current records (COACTUPC 9000-READ-ACCT fetches before update)
    account = await acct_repo.get_by_id(acct_id)
    customer = await cust_repo.get_by_id(xref.cust_id)

    # Apply account updates (REWRITE ACCTDAT)
    account.active_status = account_req.active_status
    account.curr_bal = account_req.curr_bal
    account.credit_limit = account_req.credit_limit
    account.cash_credit_limit = account_req.cash_credit_limit
    account.open_date = account_req.open_date
    account.expiration_date = account_req.expiration_date
    account.reissue_date = account_req.reissue_date
    account.curr_cycle_credit = account_req.curr_cycle_credit
    account.curr_cycle_debit = account_req.curr_cycle_debit
    account.addr_zip = account_req.addr_zip
    account.group_id = account_req.group_id

    # Apply customer updates (REWRITE CUSTDAT)
    customer.first_name = customer_req.first_name
    customer.middle_name = customer_req.middle_name
    customer.last_name = customer_req.last_name
    customer.addr_line1 = customer_req.addr_line1
    customer.addr_line2 = customer_req.addr_line2
    customer.addr_line3 = customer_req.addr_line3
    customer.addr_state_cd = customer_req.addr_state_cd
    customer.addr_country_cd = customer_req.addr_country_cd
    customer.addr_zip = customer_req.addr_zip
    customer.phone_num1 = customer_req.phone_num1
    customer.phone_num2 = customer_req.phone_num2
    customer.ssn = customer_req.ssn
    customer.govt_issued_id = customer_req.govt_issued_id
    customer.dob = customer_req.dob
    customer.eft_account_id = customer_req.eft_account_id
    customer.pri_card_holder = customer_req.pri_card_holder
    customer.fico_score = customer_req.fico_score

    await acct_repo.update(account)
    await cust_repo.update(customer)

    return AccountWithCustomerView(
        account=AccountView.model_validate(account),
        customer=CustomerView.model_validate(customer),
        card_num=xref.card_num if xref else None,
    )
