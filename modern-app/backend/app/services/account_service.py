"""Account service — business logic for account and customer operations.

Migrated from COBOL programs:
  COACTVWC  — READ ACCTDAT, READ CUSTDAT, BROWSE CARDAIX
  COACTUPC  — READ/REWRITE ACCTDAT, READ/REWRITE CUSTDAT (4400-line program)

This service implements:
  - Fetch account detail with linked customer (via card_xref) and cards
  - List/search accounts with pagination
  - Update account and customer fields with full COACTUPC validation
"""

import math
from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.account import Account, Customer
from app.models.card import Card, CardXref
from app.schemas.account import (
    AccountDetailResponse,
    AccountListItem,
    AccountListResponse,
    AccountUpdateRequest,
    CardSummary,
    CustomerResponse,
)


# ---------------------------------------------------------------------------
# List / search
# ---------------------------------------------------------------------------


async def list_accounts(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
    account_id_filter: str | None = None,
) -> AccountListResponse:
    """Return a paginated list of accounts, optionally filtered by account_id.

    Mirrors COCRDLIC/COACTVWC pattern: browse ACCTDAT with optional key filter.
    """
    offset = (page - 1) * page_size
    base_query = select(Account)

    if account_id_filter:
        # COBOL: READ ACCTDAT with EQUAL key — partial match for UX
        base_query = base_query.where(
            Account.account_id.like(f"{account_id_filter}%")
        )

    count_query = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    result = await db.execute(
        base_query.order_by(Account.account_id).offset(offset).limit(page_size)
    )
    accounts = result.scalars().all()

    items = [
        AccountListItem(
            account_id=a.account_id,
            active_status=a.active_status,
            current_balance=a.current_balance,
            credit_limit=a.credit_limit,
            open_date=a.open_date,
        )
        for a in accounts
    ]

    return AccountListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


# ---------------------------------------------------------------------------
# Fetch account detail
# ---------------------------------------------------------------------------


async def get_account_detail(
    db: AsyncSession, account_id: str
) -> AccountDetailResponse | None:
    """Fetch full account detail including linked customer and cards.

    COBOL COACTVWC flow:
      1. READ ACCTDAT by ACCT-ID
      2. READ CXACAIX by XREF-ACCT-ID -> get CUST-ID
      3. READ CUSTDAT by CUST-ID
      4. BROWSE CARDAIX for cards (STARTBR/READNEXT/ENDBR)
    """
    result = await db.execute(
        select(Account)
        .where(Account.account_id == account_id)
        .options(
            selectinload(Account.cards),
            selectinload(Account.card_xrefs).selectinload(CardXref.customer),
        )
    )
    account = result.scalar_one_or_none()
    if account is None:
        return None

    customer_response = _extract_customer(account)
    card_summaries = _build_card_summaries(account.cards)

    return AccountDetailResponse(
        id=account.id,
        account_id=account.account_id,
        active_status=account.active_status,
        current_balance=account.current_balance,
        credit_limit=account.credit_limit,
        cash_credit_limit=account.cash_credit_limit,
        open_date=account.open_date,
        expiration_date=account.expiration_date,
        reissue_date=account.reissue_date,
        current_cycle_credit=account.current_cycle_credit,
        current_cycle_debit=account.current_cycle_debit,
        address_zip=account.address_zip,
        group_id=account.group_id,
        customer=customer_response,
        cards=card_summaries,
        created_at=account.created_at,
        updated_at=account.updated_at,
    )


def _extract_customer(account: Account) -> CustomerResponse | None:
    """Pull customer from first card_xref record (CXACAIX lookup pattern)."""
    if not account.card_xrefs:
        return None
    xref = account.card_xrefs[0]
    cust = xref.customer
    if cust is None:
        return None
    return CustomerResponse(
        id=cust.id,
        customer_id=cust.customer_id,
        first_name=cust.first_name,
        middle_name=cust.middle_name,
        last_name=cust.last_name,
        address_line_1=cust.address_line_1,
        address_line_2=cust.address_line_2,
        address_line_3=cust.address_line_3,
        state_code=cust.state_code,
        country_code=cust.country_code,
        zip_code=cust.zip_code,
        phone_1=cust.phone_1,
        phone_2=cust.phone_2,
        ssn=_mask_ssn(cust.ssn),
        govt_issued_id=cust.govt_issued_id,
        date_of_birth=cust.date_of_birth,
        eft_account_id=cust.eft_account_id,
        primary_card_holder=cust.primary_card_holder,
        fico_score=cust.fico_score,
        created_at=cust.created_at,
        updated_at=cust.updated_at,
    )


def _mask_ssn(ssn: str) -> str:
    """Return SSN in xxx-xx-xxxx display format (digits only stored in DB)."""
    digits = ssn.replace("-", "").strip()
    if len(digits) == 9:
        return f"{digits[:3]}-{digits[3:5]}-{digits[5:]}"
    return ssn


def _build_card_summaries(cards: list[Card]) -> list[CardSummary]:
    """Build card summary list (CARDAIX browse result)."""
    return [
        CardSummary(
            card_number=c.card_number,
            active_status=c.active_status,
            expiration_date=c.expiration_date,
            embossed_name=c.embossed_name,
        )
        for c in cards
    ]


# ---------------------------------------------------------------------------
# Update account + customer (COACTUPC REWRITE logic)
# ---------------------------------------------------------------------------


async def update_account(
    db: AsyncSession,
    account_id: str,
    payload: AccountUpdateRequest,
) -> AccountDetailResponse | None:
    """Update account and optionally the linked customer record.

    COBOL COACTUPC flow:
      PF5 save:
        1. READ ACCTDAT WITH UPDATE
        2. MOVE updated fields to account record
        3. REWRITE ACCTDAT
        4. READ CUSTDAT WITH UPDATE
        5. MOVE updated fields to customer record
        6. REWRITE CUSTDAT

    Validation is handled at schema level (Pydantic) mirroring COACTUPC's
    inline field validation paragraphs.
    """
    result = await db.execute(
        select(Account)
        .where(Account.account_id == account_id)
        .options(
            selectinload(Account.cards),
            selectinload(Account.card_xrefs).selectinload(CardXref.customer),
        )
    )
    account = result.scalar_one_or_none()
    if account is None:
        return None

    _apply_account_updates(account, payload)

    customer = _get_linked_customer(account)
    if customer is not None:
        _apply_customer_updates(customer, payload)

    await db.flush()
    await db.refresh(account)
    return await get_account_detail(db, account_id)


def _apply_account_updates(account: Account, payload: AccountUpdateRequest) -> None:
    """Apply non-None account fields from payload to ORM object.

    COBOL: MOVE WS-FIELD TO ACCT-RECORD-FIELD for each updated field.
    """
    field_map = {
        "active_status": "active_status",
        "credit_limit": "credit_limit",
        "cash_credit_limit": "cash_credit_limit",
        "open_date": "open_date",
        "expiration_date": "expiration_date",
        "reissue_date": "reissue_date",
        "current_cycle_credit": "current_cycle_credit",
        "current_cycle_debit": "current_cycle_debit",
        "group_id": "group_id",
    }
    for schema_field, model_field in field_map.items():
        value = getattr(payload, schema_field, None)
        if value is not None:
            setattr(account, model_field, value)


def _apply_customer_updates(customer: Customer, payload: AccountUpdateRequest) -> None:
    """Apply non-None customer fields from payload to ORM object.

    COBOL COACTUPC: REWRITE CUSTDAT with updated demographics.
    """
    customer_field_map = {
        "first_name": "first_name",
        "middle_name": "middle_name",
        "last_name": "last_name",
        "address_line_1": "address_line_1",
        "address_line_2": "address_line_2",
        "address_line_3": "address_line_3",
        "state_code": "state_code",
        "country_code": "country_code",
        "zip_code": "zip_code",
        "phone_1": "phone_1",
        "phone_2": "phone_2",
        "govt_issued_id": "govt_issued_id",
        "date_of_birth": "date_of_birth",
        "eft_account_id": "eft_account_id",
        "primary_card_holder": "primary_card_holder",
        "fico_score": "fico_score",
    }
    for schema_field, model_field in customer_field_map.items():
        value = getattr(payload, schema_field, None)
        if value is not None:
            setattr(customer, model_field, value)

    # SSN: strip formatting before storing (COBOL stores digits only)
    if payload.ssn is not None:
        customer.ssn = payload.ssn.replace("-", "")


def _get_linked_customer(account: Account) -> Customer | None:
    """Return the primary customer linked via card_xref (CXACAIX lookup)."""
    if not account.card_xrefs:
        return None
    return account.card_xrefs[0].customer
