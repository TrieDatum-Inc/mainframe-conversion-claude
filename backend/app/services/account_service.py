"""
Account service — business logic for COACTVWC (view) and COACTUPC (update).

COBOL programs: COACTVWC, COACTUPC
VSAM datasets: ACCTDAT, CUSTDAT (via account_customer_xref join)

Key functions:
  view_account()   → COACTVWC: reads ACCTDAT + CUSTDAT + CARDXREF
  update_account() → COACTUPC: validates and rewrites ACCTDAT + CUSTDAT

Cognitive complexity kept under 15 per function by extracting helpers.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.errors import NoChangesDetectedError, NotFoundError, OptimisticLockError
from app.repositories.account_repository import AccountRepository
from app.repositories.customer_repository import CustomerRepository
from app.schemas.account import (
    AccountUpdateRequest,
    AccountViewResponse,
    CustomerDetailResponse,
    CustomerUpdateRequest,
)
from app.models.account import Account
from app.models.customer import Customer


# =============================================================================
# Helpers
# =============================================================================

def _mask_ssn(ssn: str | None) -> str:
    """
    Mask SSN for display — always returns ***-**-XXXX format.

    COBOL origin: SSN was stored as PIC 9(09); displayed in CACTVWA as
    masked for security. Backend enforces masking in ALL responses.
    """
    if not ssn:
        return "***-**-****"
    parts = ssn.replace("-", "")
    if len(parts) < 4:
        return "***-**-****"
    return f"***-**-{parts[-4:]}"


def _format_date(d) -> str | None:
    """Convert date to ISO string or None."""
    if d is None:
        return None
    if hasattr(d, "isoformat"):
        return d.isoformat()
    return str(d)


def _build_customer_response(customer: Customer) -> CustomerDetailResponse:
    """
    Build CustomerDetailResponse from ORM model.
    Masks SSN — never returns plain text.
    Maps CVCUS01Y copybook fields to CACTVWA display fields.
    """
    return CustomerDetailResponse(
        customer_id=customer.customer_id,
        first_name=customer.first_name,
        middle_name=customer.middle_name,
        last_name=customer.last_name,
        ssn_masked=_mask_ssn(customer.ssn),
        date_of_birth=_format_date(customer.date_of_birth),
        fico_score=customer.fico_score,
        primary_card_holder=customer.primary_card_holder or "N",
        address_line_1=customer.address_line_1,
        address_line_2=customer.address_line_2,
        address_line_3=customer.address_line_3,
        city=None,  # city stored in address_line_3 in original COBOL data
        state_code=customer.state_code,
        zip_code=customer.zip_code,
        country_code=customer.country_code,
        phone_1=customer.phone_1,
        phone_2=customer.phone_2,
        government_id_ref=customer.government_id_ref,
        eft_account_id=customer.eft_account_id,
    )


def _build_account_response(
    account: Account, customer: Customer
) -> AccountViewResponse:
    """
    Build AccountViewResponse from account + customer ORM models.
    Maps all CACTVWA ASKIP display fields.
    """
    return AccountViewResponse(
        account_id=account.account_id,
        active_status=account.active_status,
        credit_limit=Decimal(str(account.credit_limit)),
        cash_credit_limit=Decimal(str(account.cash_credit_limit)),
        current_balance=Decimal(str(account.current_balance)),
        curr_cycle_credit=Decimal(str(account.curr_cycle_credit)),
        curr_cycle_debit=Decimal(str(account.curr_cycle_debit)),
        open_date=_format_date(account.open_date),
        expiration_date=_format_date(account.expiration_date),
        reissue_date=_format_date(account.reissue_date),
        group_id=account.group_id,
        updated_at=account.updated_at.isoformat(),
        customer=_build_customer_response(customer),
    )


# =============================================================================
# View account — COACTVWC
# =============================================================================

async def view_account(account_id: int, db: AsyncSession) -> AccountViewResponse:
    """
    Fetch account + customer details.

    COACTVWC flow (three data source join):
      1. READ ACCTDAT RIDFLD(ACCT-ID) → get account record
      2. STARTBR CARDAIX → READ CUSTDAT RIDFLD(XREF-CUST-ID) → get customer
      3. Build display response

    Raises NotFoundError if account or customer not found.
    """
    account_repo = AccountRepository(db)
    customer_repo = CustomerRepository(db)

    account = await account_repo.get_by_id(account_id)
    if account is None:
        raise NotFoundError("Account", str(account_id))

    customer = await customer_repo.get_by_account_id(account_id)
    if customer is None:
        raise NotFoundError("Customer for account", str(account_id))

    return _build_account_response(account, customer)


# =============================================================================
# Update account — COACTUPC
# =============================================================================

def _apply_account_changes(account: Account, req: AccountUpdateRequest) -> bool:
    """
    Apply account field updates and return True if any field changed.

    COACTUPC: WS-DATACHANGED-FLAG — set to 'Y' when any field differs.
    """
    changed = False

    def _set(field: str, value) -> None:
        nonlocal changed
        if value is not None and getattr(account, field) != value:
            setattr(account, field, value)
            changed = True

    _set("active_status", req.active_status)
    _set("credit_limit", req.credit_limit)
    _set("cash_credit_limit", req.cash_credit_limit)
    _set("group_id", req.group_id)

    # Date fields — convert string to date if provided
    if req.open_date:
        from datetime import date as date_type
        try:
            new_date = date_type.fromisoformat(req.open_date)
            if account.open_date != new_date:
                account.open_date = new_date
                changed = True
        except ValueError:
            pass

    if req.expiration_date:
        from datetime import date as date_type
        try:
            new_date = date_type.fromisoformat(req.expiration_date)
            if account.expiration_date != new_date:
                account.expiration_date = new_date
                changed = True
        except ValueError:
            pass

    if req.reissue_date:
        from datetime import date as date_type
        try:
            new_date = date_type.fromisoformat(req.reissue_date)
            if account.reissue_date != new_date:
                account.reissue_date = new_date
                changed = True
        except ValueError:
            pass

    return changed


def _build_new_ssn(cust_req: CustomerUpdateRequest, existing_ssn: str | None) -> str | None:
    """
    Build updated SSN from request parts, or return existing SSN if no new parts.

    COACTUPC: SSN stored as NNN-NN-NNNN in CUSTDAT.
    """
    if cust_req.ssn_part1 and cust_req.ssn_part2 and cust_req.ssn_part3:
        return f"{cust_req.ssn_part1}-{cust_req.ssn_part2}-{cust_req.ssn_part3}"
    return existing_ssn


def _apply_customer_changes(customer: Customer, cust_req: CustomerUpdateRequest) -> bool:
    """
    Apply customer field updates and return True if any field changed.

    COACTUPC: Customer fields validated and rewritten to CUSTDAT.
    """
    changed = False

    def _set(field: str, value) -> None:
        nonlocal changed
        if value is not None and getattr(customer, field) != value:
            setattr(customer, field, value)
            changed = True

    _set("first_name", cust_req.first_name)
    _set("middle_name", cust_req.middle_name)
    _set("last_name", cust_req.last_name)
    _set("address_line_1", cust_req.address_line_1)
    _set("address_line_2", cust_req.address_line_2)
    _set("address_line_3", cust_req.address_line_3)
    _set("state_code", cust_req.state_code)
    _set("country_code", cust_req.country_code)
    _set("zip_code", cust_req.zip_code)
    _set("phone_1", cust_req.phone_1)
    _set("phone_2", cust_req.phone_2)
    _set("government_id_ref", cust_req.government_id_ref)
    _set("eft_account_id", cust_req.eft_account_id)
    _set("primary_card_holder", cust_req.primary_card_holder)
    _set("fico_score", cust_req.fico_score)

    # SSN
    new_ssn = _build_new_ssn(cust_req, customer.ssn)
    if new_ssn and new_ssn != customer.ssn:
        customer.ssn = new_ssn
        changed = True

    # Date of birth
    if cust_req.date_of_birth:
        from datetime import date as date_type
        try:
            new_dob = date_type.fromisoformat(cust_req.date_of_birth)
            if customer.date_of_birth != new_dob:
                customer.date_of_birth = new_dob
                changed = True
        except ValueError:
            pass

    return changed


async def update_account(
    account_id: int,
    request: AccountUpdateRequest,
    db: AsyncSession,
) -> AccountViewResponse:
    """
    Update account and customer fields.

    COACTUPC flow:
      1. READ ACCTDAT RIDFLD(ACCT-ID) → verify account exists
      2. READ CUSTDAT via CARDXREF AIX → verify customer exists
      3. Validate all fields (SSN, FICO, cash limit, etc.)
      4. Detect changes (WS-DATACHANGED-FLAG)
      5. REWRITE ACCTDAT if account changed
      6. REWRITE CUSTDAT if customer changed
      7. Return updated view

    Raises:
      NotFoundError — account or customer not found
      NoChangesDetectedError — no fields changed (COACTUPC WS-DATACHANGED-FLAG='N')
    """
    account_repo = AccountRepository(db)
    customer_repo = CustomerRepository(db)

    account = await account_repo.get_by_id(account_id)
    if account is None:
        raise NotFoundError("Account", str(account_id))

    customer = await customer_repo.get_by_account_id(account_id)
    if customer is None:
        raise NotFoundError("Customer for account", str(account_id))

    account_changed = _apply_account_changes(account, request)
    customer_changed = _apply_customer_changes(customer, request.customer)

    if not account_changed and not customer_changed:
        raise NoChangesDetectedError("account")

    if account_changed:
        await account_repo.update(account)
    if customer_changed:
        await customer_repo.update(customer)

    return _build_account_response(account, customer)
