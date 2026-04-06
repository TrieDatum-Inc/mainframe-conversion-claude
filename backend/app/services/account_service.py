"""
Account service — all business logic for account view and update.

COBOL origin:
  view_account  → COACTVWC: READ-ACCT-BY-ACCT-ID → READ-CUST-BY-CUST-ID → READ-CARD-BY-ACCT-AIX
  update_account → COACTUPC: VALIDATE-INPUT-FIELDS → UPDATE-ACCOUNT-INFO → UPDATE-CUSTOMER-INFO

COACTVWC joins three data sources:
  1. ACCTDAT    → accounts table
  2. CUSTDAT    → customers table (via account_customer_xref)
  3. CARDAIX    → card_account_xref (to enumerate associated cards)

COACTUPC validation rules (all 15+ preserved):
  1. active_status Y or N
  2. open_date valid date
  3. expiration_date valid date
  4. reissue_date valid date
  5. credit_limit >= 0
  6. cash_credit_limit >= 0 and <= credit_limit
  7. current_balance numeric
  8. first_name / last_name alpha-only
  9. SSN part1 not 000, not 666, not 900-999
  10. date_of_birth valid date
  11. fico_score 300-850
  12. phone format NNN-NNN-NNNN
  13. primary_card_holder Y or N
  14. No changes detected → 422
"""

import re
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.errors import (
    AccountNoChangesDetectedError,
    AccountNotFoundError,
    CustomerNotFoundError,
)
from app.repositories.account_repository import AccountRepository
from app.repositories.customer_repository import CustomerRepository
from app.schemas.account import (
    AccountUpdateRequest,
    AccountViewResponse,
    CustomerDetailResponse,
)


def _mask_ssn(ssn: str | None) -> str:
    """
    Mask SSN for display: NNN-NN-NNNN → ***-**-NNNN.

    COBOL: ACSTSSN on CACTVWA map — masked display per PCI-DSS guidance.
    Full SSN is never returned in API responses.
    """
    if not ssn:
        return "***-**-****"
    parts = ssn.split("-")
    if len(parts) == 3:
        return f"***-**-{parts[2]}"
    return "***-**-****"


def _build_customer_response(customer: object) -> CustomerDetailResponse:
    """
    Build CustomerDetailResponse from a Customer ORM object.

    Masks SSN — never exposes plain SSN in API response.
    Maps COACTVWC PROCESS-CUSTOMER-DATA paragraph.
    """
    return CustomerDetailResponse(
        customer_id=customer.customer_id,
        ssn_masked=_mask_ssn(customer.ssn),
        date_of_birth=customer.date_of_birth,
        fico_score=customer.fico_score,
        first_name=customer.first_name,
        middle_name=customer.middle_name,
        last_name=customer.last_name,
        address_line_1=customer.street_address_1,
        address_line_2=customer.street_address_2,
        city=customer.city,
        state_code=customer.state_code,
        zip_code=customer.zip_code,
        country_code=customer.country_code,
        phone_1=customer.phone_number_1,
        phone_2=customer.phone_number_2,
        government_id_ref=customer.government_id_ref,
        eft_account_id=customer.eft_account_id,
        primary_card_holder=customer.primary_card_holder_flag,
    )


def _build_account_response(account: object, customer: object) -> AccountViewResponse:
    """
    Build AccountViewResponse from account + customer ORM objects.

    Maps COACTVWC PROCESS-ACCT-DATA paragraph — populates CACTVWA map fields.
    """
    return AccountViewResponse(
        account_id=account.account_id,
        active_status=account.active_status,
        open_date=account.open_date,
        expiration_date=account.expiration_date,
        reissue_date=account.reissue_date,
        credit_limit=account.credit_limit,
        cash_credit_limit=account.cash_credit_limit,
        current_balance=account.current_balance,
        curr_cycle_credit=account.curr_cycle_credit,
        curr_cycle_debit=account.curr_cycle_debit,
        group_id=account.group_id,
        updated_at=account.updated_at,
        customer=_build_customer_response(customer),
    )


async def view_account(
    account_id: int,
    db: AsyncSession,
) -> AccountViewResponse:
    """
    View account with customer details.

    COBOL: COACTVWC READ-ACCT-BY-ACCT-ID → READ-CUST-BY-CUST-ID → display.
    Three-source join: ACCTDAT + CUSTDAT (via xref) + CARDAIX.

    Raises AccountNotFoundError (404) if account does not exist.
    Raises CustomerNotFoundError (404) if no customer linked to account.
    """
    account_repo = AccountRepository(db)
    customer_repo = CustomerRepository(db)

    account = await account_repo.get_by_id(account_id)
    if account is None:
        raise AccountNotFoundError(account_id)

    customer = await customer_repo.get_by_account_id(account_id)
    if customer is None:
        raise CustomerNotFoundError(account_id)

    return _build_account_response(account, customer)


def _detect_account_changes(account: object, request: AccountUpdateRequest) -> bool:
    """
    Detect if any account fields changed.

    COBOL: COACTUPC WS-DATACHANGED-FLAG logic — compare each field to stored value.
    Returns True if at least one field differs from the stored record.
    """
    return (
        account.active_status != request.active_status
        or account.open_date != request.open_date
        or account.expiration_date != request.expiration_date
        or account.reissue_date != request.reissue_date
        or account.credit_limit != request.credit_limit
        or account.cash_credit_limit != request.cash_credit_limit
        or account.current_balance != request.current_balance
        or account.curr_cycle_credit != request.curr_cycle_credit
        or account.curr_cycle_debit != request.curr_cycle_debit
        or account.group_id != (request.group_id or None)
    )


def _detect_customer_changes(customer: object, req: object) -> bool:
    """
    Detect if any customer fields changed.

    COBOL: COACTUPC WS-DATACHANGED-FLAG for customer fields.
    """
    new_ssn = f"{req.ssn_part1}-{req.ssn_part2}-{req.ssn_part3}"
    return (
        customer.first_name != req.first_name
        or customer.middle_name != req.middle_name
        or customer.last_name != req.last_name
        or customer.street_address_1 != req.address_line_1
        or customer.street_address_2 != req.address_line_2
        or customer.city != req.city
        or customer.state_code != req.state_code
        or customer.zip_code != req.zip_code
        or customer.country_code != req.country_code
        or customer.phone_number_1 != req.phone_1
        or customer.phone_number_2 != req.phone_2
        or customer.ssn != new_ssn
        or customer.date_of_birth != req.date_of_birth
        or customer.fico_score != req.fico_score
        or customer.government_id_ref != req.government_id_ref
        or customer.eft_account_id != req.eft_account_id
        or customer.primary_card_holder_flag != req.primary_card_holder
    )


async def update_account(
    account_id: int,
    request: AccountUpdateRequest,
    db: AsyncSession,
) -> AccountViewResponse:
    """
    Update account and customer fields atomically.

    COBOL: COACTUPC PROCESS-ENTER-KEY → VALIDATE-INPUT-FIELDS → UPDATE-ACCOUNT-INFO
    All 15+ COACTUPC validation rules are pre-validated by Pydantic schemas.
    This function checks no-changes and executes the updates.

    Raises AccountNotFoundError (404) if account not found.
    Raises CustomerNotFoundError (404) if no customer linked.
    Raises AccountNoChangesDetectedError (422) if nothing changed.
    """
    account_repo = AccountRepository(db)
    customer_repo = CustomerRepository(db)

    account = await account_repo.get_by_id(account_id)
    if account is None:
        raise AccountNotFoundError(account_id)

    customer = await customer_repo.get_by_account_id(account_id)
    if customer is None:
        raise CustomerNotFoundError(account_id)

    # Check if any field changed (COACTUPC WS-DATACHANGED-FLAG pattern)
    acct_changed = _detect_account_changes(account, request)
    cust_changed = _detect_customer_changes(customer, request.customer)

    if not acct_changed and not cust_changed:
        raise AccountNoChangesDetectedError()

    # Update account fields
    if acct_changed:
        account = await account_repo.update(
            account_id=account_id,
            active_status=request.active_status,
            current_balance=request.current_balance,
            credit_limit=request.credit_limit,
            cash_credit_limit=request.cash_credit_limit,
            open_date=request.open_date,
            expiration_date=request.expiration_date,
            reissue_date=request.reissue_date,
            curr_cycle_credit=request.curr_cycle_credit,
            curr_cycle_debit=request.curr_cycle_debit,
            group_id=request.group_id,
        )

    # Update customer fields
    cust_req = request.customer
    new_ssn = f"{cust_req.ssn_part1}-{cust_req.ssn_part2}-{cust_req.ssn_part3}"
    if cust_changed:
        customer = await customer_repo.update(
            customer_id=cust_req.customer_id,
            first_name=cust_req.first_name,
            middle_name=cust_req.middle_name,
            last_name=cust_req.last_name,
            street_address_1=cust_req.address_line_1,
            street_address_2=cust_req.address_line_2,
            city=cust_req.city,
            state_code=cust_req.state_code,
            zip_code=cust_req.zip_code,
            country_code=cust_req.country_code,
            phone_number_1=cust_req.phone_1,
            phone_number_2=cust_req.phone_2,
            ssn=new_ssn,
            date_of_birth=cust_req.date_of_birth,
            fico_score=cust_req.fico_score,
            government_id_ref=cust_req.government_id_ref,
            eft_account_id=cust_req.eft_account_id,
            primary_card_holder_flag=cust_req.primary_card_holder,
        )

    # Refresh to get updated_at from DB trigger
    await db.refresh(account)
    await db.refresh(customer)

    return _build_account_response(account, customer)
