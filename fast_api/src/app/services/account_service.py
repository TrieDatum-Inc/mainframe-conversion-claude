"""Account service — all business logic lives here.

Maps to COBOL paragraph groups:
  - get_account_view → COACTVWC 9000-READ-ACCT + 1200-SETUP-SCREEN-VARS
  - update_account   → COACTUPC 9600-WRITE-PROCESSING + 9700-CHECK-CHANGE-IN-REC
"""

import logging
from datetime import datetime

from sqlalchemy.exc import OperationalError

from app.repositories.account_repository import AccountRepository, AccountWithRelations
from app.schemas.account import (
    AccountDetailResponse,
    AccountUpdateRequest,
    AccountUpdateResponse,
    AccountViewResponse,
    CardInfo,
    CustomerInfo,
)
from app.utils.exceptions import (
    AccountNotFoundError,
    ConcurrentModificationError,
    CustomerNotFoundError,
    LockAcquisitionError,
)
from app.utils.formatters import format_phone, format_ssn

logger = logging.getLogger(__name__)


class AccountService:
    """Implements COACTVWC and COACTUPC business logic.

    Injected with an AccountRepository; all data access goes through it.
    """

    def __init__(self, repository: AccountRepository) -> None:
        self._repo = repository

    # ------------------------------------------------------------------
    # COACTVWC: Account View (read-only)
    # ------------------------------------------------------------------

    async def get_account_view(self, acct_id: str) -> AccountViewResponse:
        """Read account + linked customer + cards for display.

        Business rules (from COACTVWC spec section 7):
        1. Account ID must exist in accounts table (via cross-reference).
           → If not found: raises AccountNotFoundError.
        2. Customer linked via card_cross_references.xref_cust_id.
           → If customer not found: account data returned with customer=None.
        3. SSN is formatted as XXX-XX-XXXX for display (from 1200-SETUP-SCREEN-VARS).
        """
        acct_id = _normalize_acct_id(acct_id)

        result = await self._repo.get_account_with_relations(acct_id)
        if result is None:
            logger.info("Account %s not found in cross-reference / account master", acct_id)
            raise AccountNotFoundError(
                f"Did not find this account in account master file: {acct_id}"
            )

        return _build_view_response(result)

    # ------------------------------------------------------------------
    # COACTUPC: Account Update
    # ------------------------------------------------------------------

    async def update_account(
        self, acct_id: str, request: AccountUpdateRequest
    ) -> AccountUpdateResponse:
        """Update account + customer records atomically.

        Implements COACTUPC 9600-WRITE-PROCESSING with full optimistic
        concurrency control (9700-CHECK-CHANGE-IN-REC).

        Flow:
        1. Lock account row (EXEC CICS READ FILE('ACCTDAT') UPDATE).
        2. Lock customer row (EXEC CICS READ FILE('CUSTDAT') UPDATE).
        3. Compare locked updated_at with request.updated_at token
           (replaces field-by-field ACUP-OLD-DETAILS comparison in COBOL).
        4. Apply account updates (EXEC CICS REWRITE FILE('ACCTDAT')).
        5. Apply customer updates (EXEC CICS REWRITE FILE('CUSTDAT')).
        6. Commit (EXEC CICS SYNCPOINT).
        On any step 4/5 failure: rollback (EXEC CICS SYNCPOINT ROLLBACK).
        """
        acct_id = _normalize_acct_id(acct_id)

        # --- Step 1: acquire account lock (EXEC CICS READ FILE('ACCTDAT') UPDATE) ---
        try:
            account = await self._repo.get_account_for_update(acct_id)
        except OperationalError:
            logger.warning("Could not acquire lock on account %s", acct_id)
            raise LockAcquisitionError("Could not lock account record for update")

        if account is None:
            raise AccountNotFoundError(
                f"Did not find this account in account master file: {acct_id}"
            )

        # --- Step 2: get customer ID via cross-reference ---
        cust_id = await self._repo.get_customer_id_by_account(acct_id)
        if cust_id is None:
            raise CustomerNotFoundError(
                f"Did not find associated customer in master file for account {acct_id}"
            )

        # --- Step 3: acquire customer lock (EXEC CICS READ FILE('CUSTDAT') UPDATE) ---
        try:
            customer = await self._repo.get_customer_for_update(cust_id)
        except OperationalError:
            logger.warning("Could not acquire lock on customer %s", cust_id)
            raise LockAcquisitionError("Could not lock customer record for update")

        if customer is None:
            raise CustomerNotFoundError(
                f"Did not find associated customer in master file: {cust_id}"
            )

        # --- Step 4: optimistic concurrency check (9700-CHECK-CHANGE-IN-REC) ---
        _check_concurrency(account.updated_at, customer.updated_at, request.updated_at)

        # --- Step 5: build and apply account updates ---
        acct_update_data = _build_account_update(request)
        try:
            await self._repo.update_account(account, acct_update_data)
        except Exception as exc:
            await self._repo.rollback()
            logger.error("Account REWRITE failed for %s: %s", acct_id, exc)
            raise

        # --- Step 6: build and apply customer updates ---
        cust_update_data = _build_customer_update(request)
        try:
            await self._repo.update_customer(customer, cust_update_data)
        except Exception as exc:
            # Replicate EXEC CICS SYNCPOINT ROLLBACK on customer REWRITE failure
            await self._repo.rollback()
            logger.error(
                "Customer REWRITE failed for %s (account %s rolled back): %s",
                cust_id,
                acct_id,
                exc,
            )
            raise

        # --- Step 7: commit ---
        await self._repo.commit()
        await self._repo.rollback()  # refresh session state after commit
        account = await self._repo.get_account_for_update(acct_id)  # re-read for updated_at

        logger.info("Account %s updated successfully (customer %s)", acct_id, cust_id)

        return AccountUpdateResponse(
            message="Changes committed to database",
            acct_id=acct_id,
            updated_at=account.updated_at if account else datetime.now(),
        )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _normalize_acct_id(acct_id: str) -> str:
    """Ensure account ID is zero-padded to 11 digits.

    COBOL uses PIC 9(11) so '1' and '00000000001' are the same key.
    """
    return acct_id.zfill(11)


def _build_view_response(result: AccountWithRelations) -> AccountViewResponse:
    """Map AccountWithRelations to AccountViewResponse.

    Mirrors 1200-SETUP-SCREEN-VARS in COACTVWC — populates every screen
    field from ACCOUNT-RECORD and CUSTOMER-RECORD.
    """
    account = result.account
    customer = result.customer
    cards = result.cards

    customer_info: CustomerInfo | None = None
    if customer:
        customer_info = CustomerInfo(
            cust_id=customer.cust_id,
            cust_first_name=customer.cust_first_name,
            cust_middle_name=customer.cust_middle_name,
            cust_last_name=customer.cust_last_name,
            cust_addr_line_1=customer.cust_addr_line_1,
            cust_addr_line_2=customer.cust_addr_line_2,
            cust_addr_line_3=customer.cust_addr_line_3,
            cust_addr_state_cd=customer.cust_addr_state_cd,
            cust_addr_country_cd=customer.cust_addr_country_cd,
            cust_addr_zip=customer.cust_addr_zip,
            cust_phone_num_1=customer.cust_phone_num_1,
            cust_phone_num_2=customer.cust_phone_num_2,
            ssn_formatted=format_ssn(customer.cust_ssn),
            cust_govt_issued_id=customer.cust_govt_issued_id,
            cust_dob=customer.cust_dob,
            cust_eft_account_id=customer.cust_eft_account_id,
            cust_pri_card_holder_ind=customer.cust_pri_card_holder_ind,
            cust_fico_credit_score=customer.cust_fico_credit_score,
            updated_at=customer.updated_at,
        )

    card_infos = [
        CardInfo(
            card_num=c.card_num,
            card_embossed_name=c.card_embossed_name,
            card_expiration_date=c.card_expiration_date,
            card_active_status=c.card_active_status,
        )
        for c in cards
    ]

    return AccountViewResponse(
        acct_id=account.acct_id,
        acct_active_status=account.acct_active_status,
        acct_curr_bal=account.acct_curr_bal,
        acct_credit_limit=account.acct_credit_limit,
        acct_cash_credit_limit=account.acct_cash_credit_limit,
        acct_open_date=account.acct_open_date,
        acct_expiration_date=account.acct_expiration_date,
        acct_reissue_date=account.acct_reissue_date,
        acct_curr_cyc_credit=account.acct_curr_cyc_credit,
        acct_curr_cyc_debit=account.acct_curr_cyc_debit,
        acct_addr_zip=account.acct_addr_zip,
        acct_group_id=account.acct_group_id,
        updated_at=account.updated_at,
        customer=customer_info,
        cards=card_infos,
    )


def _check_concurrency(
    account_updated_at: datetime,
    customer_updated_at: datetime,
    client_token: datetime,
) -> None:
    """Optimistic concurrency check — replicates 9700-CHECK-CHANGE-IN-REC.

    COBOL compared ACUP-OLD-DETAILS (snapshot taken at fetch time) against
    the freshly locked record field by field. We use updated_at timestamps
    as a proxy: if either record has been modified since the client fetched
    it, reject the update.

    Raises ConcurrentModificationError if the record was changed externally.
    """
    # Strip timezone info for comparison if needed
    acct_ts = account_updated_at.replace(tzinfo=None) if account_updated_at.tzinfo else account_updated_at
    cust_ts = customer_updated_at.replace(tzinfo=None) if customer_updated_at.tzinfo else customer_updated_at
    client_ts = client_token.replace(tzinfo=None) if client_token.tzinfo else client_token

    if acct_ts > client_ts or cust_ts > client_ts:
        raise ConcurrentModificationError(
            "Record changed by some one else. Please review"
        )


def _build_account_update(request: AccountUpdateRequest) -> dict:
    """Extract account fields from the update request.

    Mirrors ACCT-UPDATE-RECORD construction in 9600-WRITE-PROCESSING.
    """
    return {
        "acct_active_status": request.acct_active_status,
        "acct_credit_limit": request.acct_credit_limit,
        "acct_cash_credit_limit": request.acct_cash_credit_limit,
        "acct_curr_bal": request.acct_curr_bal,
        "acct_curr_cyc_credit": request.acct_curr_cyc_credit,
        "acct_curr_cyc_debit": request.acct_curr_cyc_debit,
        "acct_open_date": request.acct_open_date,
        "acct_expiration_date": request.acct_expiration_date,
        "acct_reissue_date": request.acct_reissue_date,
        "acct_group_id": request.acct_group_id,
    }


def _build_customer_update(request: AccountUpdateRequest) -> dict:
    """Extract customer fields from the update request.

    Mirrors CUST-UPDATE-RECORD construction in 9600-WRITE-PROCESSING.
    Phone numbers are formatted as (aaa)bbb-cccc.
    SSN is reconstructed from 3 parts as 9-digit string.
    """
    phone1 = format_phone(request.cust_phone_num_1)
    phone2 = format_phone(request.cust_phone_num_2) if request.cust_phone_num_2 else None

    ssn_str = (
        request.cust_ssn.part1 + request.cust_ssn.part2 + request.cust_ssn.part3
    )

    return {
        "cust_first_name": request.cust_first_name,
        "cust_middle_name": request.cust_middle_name,
        "cust_last_name": request.cust_last_name,
        "cust_addr_line_1": request.cust_addr_line_1,
        "cust_addr_line_2": request.cust_addr_line_2,
        "cust_addr_line_3": request.cust_addr_line_3,
        "cust_addr_state_cd": request.cust_addr_state_cd,
        "cust_addr_country_cd": request.cust_addr_country_cd,
        "cust_addr_zip": request.cust_addr_zip,
        "cust_phone_num_1": phone1,
        "cust_phone_num_2": phone2,
        "cust_ssn": ssn_str,
        "cust_govt_issued_id": request.cust_govt_issued_id,
        "cust_dob": request.cust_dob,
        "cust_eft_account_id": request.cust_eft_account_id,
        "cust_pri_card_holder_ind": request.cust_pri_card_holder_ind,
        "cust_fico_credit_score": request.cust_fico_credit_score,
    }
