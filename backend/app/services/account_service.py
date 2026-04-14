"""
Account service — business logic for account view and update operations.

COBOL origin:
  get_account  → COACTVWC MAIN-PARA (CDEMO-PGM-REENTER path)
                   → 9000-READ-ACCT paragraph
  update_account → COACTUPC MAIN-PARA (CDEMO-PGM-REENTER + ENTER/PF5 path)
                   → 2000-PROCESS-INPUTS (validation)
                   → 9000-UPDATE-ACCOUNT (conditional REWRITE)

Key design decisions carried over from COBOL analysis:
  1. SSN is never returned in full. ssn_masked always shows "***-**-XXXX".
     COBOL stored CUST-SSN as plain text EBCDIC; the API corrects this exposure.
  2. WS-DATACHANGED-FLAG logic: update only proceeds if at least one field changed.
     If nothing changed, 422 is returned (maps COACTUPC "no changes" path).
  3. Account and customer are updated in the same DB transaction
     (maps COBOL within-task implicit atomicity — both REWRITEs in one CICS task).
  4. 404 for account not found maps DID-NOT-FIND-ACCT-IN-ACCTDAT error message.
     404 for customer not found maps DID-NOT-FIND-CUST-IN-CUSTDAT.
"""

from decimal import Decimal
from typing import Optional

import structlog
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.customer import Customer
from app.repositories.account_repository import AccountRepository
from app.schemas.account import (
    AccountUpdateRequest,
    AccountViewResponse,
    CustomerDetailResponse,
)

logger = structlog.get_logger(__name__)
audit_log = structlog.get_logger("audit")


def _mask_ssn(ssn: Optional[str]) -> str:
    """
    Mask an SSN for display, showing only the last 4 digits.

    SECURITY: COBOL stored SSN as plain text (CUST-SSN 9(9)).
    The BMS view screen displayed the full SSN (ACSTSSN 12-char field).
    The modern API only exposes the last 4 digits to prevent data leakage.

    Examples:
      "123-45-6789" → "***-**-6789"
      None or malformed → "***-**-****"
    """
    if ssn and len(ssn) == 11 and ssn[3] == "-" and ssn[6] == "-":
        return f"***-**-{ssn[7:]}"
    return "***-**-****"


def _build_customer_response(customer: Customer) -> CustomerDetailResponse:
    """Build a CustomerDetailResponse from the ORM model, with SSN masked."""
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


def _build_account_response(
    account: Account, customer: Customer
) -> AccountViewResponse:
    """Build a full AccountViewResponse from ORM models."""
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
        customer=_build_customer_response(customer),
    )


class AccountService:
    """Business logic for account view and update operations."""

    @staticmethod
    async def get_account(
        db: AsyncSession,
        account_id: int,
        requesting_user_id: str = "unknown",
    ) -> AccountViewResponse:
        """
        Retrieve full account and linked customer details.

        COBOL origin: COACTVWC MAIN-PARA (CDEMO-PGM-REENTER path)
          → 2000-PROCESS-INPUTS: validates ACCTSID non-zero numeric
          → 9000-READ-ACCT:
              EXEC CICS READ DATASET('ACCTDAT') RIDFLD(ACCT-ID)
              EXEC CICS READ DATASET('CXACAIX') RIDFLD(acct_id)  [alternate index]
              EXEC CICS READ DATASET('CUSTDAT') RIDFLD(CUST-ID)

        Business rules (COACTVWC section 9):
          1. account_id > 0 (MUSTFILL + PICIN=99999999999, non-zero check)
          2. Account must exist (RESP=NOTFND → DID-NOT-FIND-ACCT-IN-ACCTDAT)
          3. Customer must be linked via xref (DID-NOT-FIND-CUST-IN-CUSTDAT)
        """
        if account_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error_code": "INVALID_ACCOUNT_ID",
                    "message": "Account number must be a non-zero positive value",
                },
            )

        account = await AccountRepository.get_account_by_id(db, account_id)
        if account is None:
            logger.info(
                "account_not_found",
                account_id=account_id,
                requesting_user_id=requesting_user_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "ACCOUNT_NOT_FOUND",
                    "message": f"Account {account_id} not found",
                },
            )

        customer = await AccountRepository.get_customer_by_account_id(db, account_id)
        if customer is None:
            # SEC-02: Log the internal distinction server-side for diagnostics,
            # but return the same ACCOUNT_NOT_FOUND code as the account-missing
            # path. Returning a distinct CUSTOMER_NOT_FOUND code would let an
            # authenticated caller enumerate which account IDs exist in the system.
            logger.warning(
                "customer_not_found_for_account",
                account_id=account_id,
                requesting_user_id=requesting_user_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "ACCOUNT_NOT_FOUND",
                    "message": f"Account {account_id} not found",
                },
            )

        logger.info(
            "account_view",
            account_id=account_id,
            customer_id=customer.customer_id,
            requesting_user_id=requesting_user_id,
        )
        return _build_account_response(account, customer)

    @staticmethod
    async def update_account(
        db: AsyncSession,
        account_id: int,
        request: AccountUpdateRequest,
        requesting_user_id: str = "unknown",
    ) -> AccountViewResponse:
        """
        Validate and apply account and customer field updates.

        COBOL origin: COACTUPC MAIN-PARA (CDEMO-PGM-REENTER + ENTER/PF5 path)
          → 2000-PROCESS-INPUTS: 15+ field-level validations (done by Pydantic)
          → 9000-UPDATE-ACCOUNT:
              WS-DATACHANGED-FLAG logic: detect changes, skip REWRITE if none
              EXEC CICS READ DATASET('ACCTDAT') UPDATE
              EXEC CICS REWRITE DATASET('ACCTDAT') FROM(ACCT-UPDATE-RECORD)
              EXEC CICS READ DATASET('CUSTDAT') UPDATE
              EXEC CICS REWRITE DATASET('CUSTDAT') FROM(CUST-UPDATE-RECORD)

        Business rules:
          1. Account must exist (404 ACCOUNT_NOT_FOUND)
          2. Customer must be linked (404 CUSTOMER_NOT_FOUND)
          3. customer_id in request must match xref (consistency check)
          4. At least one field must have changed (422 NO_CHANGES_DETECTED)
             Maps COACTUPC WS-DATACHANGED-FLAG='0' path
        """
        # SEC-03: Consistent with get_account — validate account_id > 0 before
        # any DB access. Without this guard a zero/negative ID returns 404 instead
        # of the expected 422 INVALID_ACCOUNT_ID, creating an inconsistency that
        # can confuse clients and obscure input-validation errors.
        if account_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error_code": "INVALID_ACCOUNT_ID",
                    "message": "Account number must be a non-zero positive value",
                },
            )

        account = await AccountRepository.get_account_by_id(db, account_id)
        if account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "ACCOUNT_NOT_FOUND",
                    "message": f"Account {account_id} not found",
                },
            )

        customer = await AccountRepository.get_customer_by_account_id(db, account_id)
        if customer is None:
            # SEC-02: Same normalised error code as account-missing path to prevent
            # enumeration of which account IDs exist in the system.
            logger.warning(
                "customer_not_found_for_account",
                account_id=account_id,
                requesting_user_id=requesting_user_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "ACCOUNT_NOT_FOUND",
                    "message": f"Account {account_id} not found",
                },
            )

        # Verify customer_id in request matches the linked customer
        if request.customer.customer_id != customer.customer_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error_code": "CUSTOMER_ID_MISMATCH",
                    "message": (
                        f"Customer ID {request.customer.customer_id} does not match "
                        f"the customer linked to account {account_id}"
                    ),
                },
            )

        # ------------------------------------------------------------------
        # WS-DATACHANGED-FLAG equivalent:
        # Build dicts of only the fields that actually changed.
        # COBOL origin: COACTUPC 9000-UPDATE-ACCOUNT — only REWRITE if
        # WS-DATACHANGED-FLAG = '1' (any field was modified).
        # ------------------------------------------------------------------
        account_changes: dict = {}
        if account.active_status != request.active_status:
            account_changes["active_status"] = request.active_status
        if account.open_date != request.open_date:
            account_changes["open_date"] = request.open_date
        if account.expiration_date != request.expiration_date:
            account_changes["expiration_date"] = request.expiration_date
        if account.reissue_date != request.reissue_date:
            account_changes["reissue_date"] = request.reissue_date
        if Decimal(str(account.credit_limit)) != request.credit_limit:
            account_changes["credit_limit"] = request.credit_limit
        if Decimal(str(account.cash_credit_limit)) != request.cash_credit_limit:
            account_changes["cash_credit_limit"] = request.cash_credit_limit
        if Decimal(str(account.current_balance)) != request.current_balance:
            account_changes["current_balance"] = request.current_balance
        if Decimal(str(account.curr_cycle_credit)) != request.curr_cycle_credit:
            account_changes["curr_cycle_credit"] = request.curr_cycle_credit
        if Decimal(str(account.curr_cycle_debit)) != request.curr_cycle_debit:
            account_changes["curr_cycle_debit"] = request.curr_cycle_debit
        if account.group_id != request.group_id:
            account_changes["group_id"] = request.group_id

        # Build SSN from parts for comparison/storage
        new_ssn = (
            f"{request.customer.ssn_part1}-"
            f"{request.customer.ssn_part2}-"
            f"{request.customer.ssn_part3}"
        )

        customer_changes: dict = {}
        if customer.first_name != request.customer.first_name:
            customer_changes["first_name"] = request.customer.first_name
        if customer.middle_name != request.customer.middle_name:
            customer_changes["middle_name"] = request.customer.middle_name
        if customer.last_name != request.customer.last_name:
            customer_changes["last_name"] = request.customer.last_name
        if customer.street_address_1 != request.customer.address_line_1:
            customer_changes["street_address_1"] = request.customer.address_line_1
        if customer.street_address_2 != request.customer.address_line_2:
            customer_changes["street_address_2"] = request.customer.address_line_2
        if customer.city != request.customer.city:
            customer_changes["city"] = request.customer.city
        if customer.state_code != request.customer.state_code:
            customer_changes["state_code"] = request.customer.state_code
        if customer.zip_code != request.customer.zip_code:
            customer_changes["zip_code"] = request.customer.zip_code
        if customer.country_code != request.customer.country_code:
            customer_changes["country_code"] = request.customer.country_code
        if customer.phone_number_1 != request.customer.phone_1:
            customer_changes["phone_number_1"] = request.customer.phone_1
        if customer.phone_number_2 != request.customer.phone_2:
            customer_changes["phone_number_2"] = request.customer.phone_2
        if customer.ssn != new_ssn:
            customer_changes["ssn"] = new_ssn
        if customer.date_of_birth != request.customer.date_of_birth:
            customer_changes["date_of_birth"] = request.customer.date_of_birth
        if customer.fico_score != request.customer.fico_score:
            customer_changes["fico_score"] = request.customer.fico_score
        if customer.government_id_ref != request.customer.government_id_ref:
            customer_changes["government_id_ref"] = request.customer.government_id_ref
        if customer.eft_account_id != request.customer.eft_account_id:
            customer_changes["eft_account_id"] = request.customer.eft_account_id
        if customer.primary_card_holder_flag != request.customer.primary_card_holder:
            customer_changes["primary_card_holder_flag"] = request.customer.primary_card_holder

        # WS-DATACHANGED-FLAG='0' path: no changes detected
        if not account_changes and not customer_changes:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error_code": "NO_CHANGES_DETECTED",
                    "message": (
                        "No changes detected. "
                        "Please modify at least one field to update."
                    ),
                },
            )

        await AccountRepository.update_account_and_customer(
            db=db,
            account=account,
            customer=customer,
            account_changes=account_changes,
            customer_changes=customer_changes,
        )

        # Refresh customer after flush (fields may have been updated)
        await db.refresh(customer)

        audit_log.info(
            "ACCOUNT_UPDATE",
            account_id=account_id,
            customer_id=customer.customer_id,
            account_fields_changed=list(account_changes.keys()),
            customer_fields_changed=[
                k for k in customer_changes if k != "ssn"  # never log SSN
            ],
            requesting_user_id=requesting_user_id,
        )

        return _build_account_response(account, customer)
