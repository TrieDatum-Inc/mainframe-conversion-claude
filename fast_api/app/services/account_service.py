"""
Account service — business logic from COACTVWC and COACTUPC.

Paragraph mapping:
  COACTVWC READ-PROCESSING          → get_account()
  COACTUPC PROCESS-ENTER-KEY        → update_account()
  COACTUPC VALIDATE-INPUT-FIELDS    → _validate_update()
  COACTUPC CHECK-CHANGE-IN-REC      → _apply_changes()

Business rules preserved from COACTUPC:
  1. Only admin users can change group_id (ACCT-GROUP-ID)
  2. active_status must be 'Y' or 'N'
  3. credit_limit >= 0 (implied by PIC S9(10)V99 unsigned)
  4. All monetary fields use Python Decimal for COMP-3 precision
  5. Read-then-rewrite pattern (CICS REWRITE requires prior READ)
"""
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.customer import Customer
from app.repositories.account_repo import AccountRepository
from app.schemas.account import AccountDetailResponse, AccountResponse, AccountUpdateRequest
from app.utils.cobol_compat import cobol_trim
from app.utils.error_handlers import AuthorizationError, ValidationError


class AccountService:
    """
    Account business logic from COACTVWC and COACTUPC.

    All monetary operations use Python Decimal to match COBOL COMP-3 arithmetic.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._repo = AccountRepository(db)

    async def get_account(self, acct_id: int) -> AccountDetailResponse:
        """
        COACTVWC READ-PROCESSING: READ FILE(ACCTDAT) + join CUSTDAT via CCXREF.

        Returns account detail with customer info.
        Raises RecordNotFoundError if account not found (CICS RESP=13).
        """
        account, customer = await self._repo.get_with_customer(acct_id)
        return self._build_detail_response(account, customer)

    async def update_account(
        self,
        acct_id: int,
        request: AccountUpdateRequest,
        is_admin: bool,
    ) -> AccountResponse:
        """
        COACTUPC PROCESS-ENTER-KEY → validate → rewrite.

        Business rules:
          1. Read existing record (CICS READ before REWRITE)
          2. Validate input fields (COACTUPC VALIDATE-INPUT-FIELDS)
          3. Only admin can change group_id
          4. Apply changes (COACTUPC CHECK-CHANGE-IN-REC)
          5. EXEC CICS REWRITE FILE(ACCTDAT)

        Args:
            acct_id: Account ID to update.
            request: Fields to update.
            is_admin: True if requester has CDEMO-USRTYP-ADMIN role.

        Returns:
            Updated AccountResponse.

        Raises:
            AuthorizationError: Non-admin attempts to update group_id.
            ValidationError: Field validation failure.
            RecordNotFoundError: Account not found.
        """
        # COACTUPC: READ FILE(ACCTDAT) before REWRITE (CICS requirement)
        account = await self._repo.get_by_id(acct_id)

        # Validate input fields
        self._validate_update(request, is_admin)

        # Apply changes (COACTUPC CHECK-CHANGE-IN-REC paragraph)
        self._apply_changes(account, request, is_admin)

        # EXEC CICS REWRITE FILE(ACCTDAT) FROM(ACCOUNT-RECORD)
        updated = await self._repo.update(account)
        return self._build_response(updated)

    def _validate_update(self, request: AccountUpdateRequest, is_admin: bool) -> None:
        """
        COACTUPC VALIDATE-INPUT-FIELDS paragraph.

        Business rules:
          - group_id change requires admin role
          - active_status restricted to 'Y'/'N' (88-level conditions)
          - monetary limits must be non-negative
        """
        # COACTUPC: only admin can update ACCT-GROUP-ID
        if request.group_id is not None and not is_admin:
            raise AuthorizationError(
                "Only admin users can update account group ID (COACTUPC business rule)"
            )

        if request.credit_limit is not None and request.credit_limit < 0:
            raise ValidationError("credit_limit must be >= 0")

        if request.cash_credit_limit is not None and request.cash_credit_limit < 0:
            raise ValidationError("cash_credit_limit must be >= 0")

    def _apply_changes(
        self,
        account: Account,
        request: AccountUpdateRequest,
        is_admin: bool,
    ) -> None:
        """
        COACTUPC CHECK-CHANGE-IN-REC paragraph.

        Only updates fields that are explicitly provided (not None).
        Mirrors COBOL MOVE behavior: only changed fields are rewritten.
        """
        if request.active_status is not None:
            account.active_status = request.active_status
        if request.credit_limit is not None:
            account.credit_limit = request.credit_limit
        if request.cash_credit_limit is not None:
            account.cash_credit_limit = request.cash_credit_limit
        if request.open_date is not None:
            account.open_date = request.open_date
        if request.expiration_date is not None:
            account.expiration_date = request.expiration_date
        if request.reissue_date is not None:
            account.reissue_date = request.reissue_date
        if request.curr_cycle_credit is not None:
            account.curr_cycle_credit = request.curr_cycle_credit
        if request.curr_cycle_debit is not None:
            account.curr_cycle_debit = request.curr_cycle_debit
        if request.addr_zip is not None:
            account.addr_zip = request.addr_zip
        # COACTUPC: group_id only settable by admin
        if request.group_id is not None and is_admin:
            account.group_id = request.group_id

    @staticmethod
    def _build_response(account: Account) -> AccountResponse:
        """Build AccountResponse from ORM model."""
        return AccountResponse(
            acct_id=account.acct_id,
            active_status=account.active_status,
            curr_bal=account.curr_bal,
            credit_limit=account.credit_limit,
            cash_credit_limit=account.cash_credit_limit,
            open_date=account.open_date,
            expiration_date=account.expiration_date,
            reissue_date=account.reissue_date,
            curr_cycle_credit=account.curr_cycle_credit,
            curr_cycle_debit=account.curr_cycle_debit,
            addr_zip=account.addr_zip,
            group_id=account.group_id,
        )

    @staticmethod
    def _build_detail_response(
        account: Account, customer: Customer | None
    ) -> AccountDetailResponse:
        """Build AccountDetailResponse including optional customer info."""
        customer_name = None
        customer_id = None
        if customer:
            parts = [
                cobol_trim(customer.first_name),
                cobol_trim(customer.last_name),
            ]
            customer_name = " ".join(p for p in parts if p)
            customer_id = customer.cust_id

        return AccountDetailResponse(
            acct_id=account.acct_id,
            active_status=account.active_status,
            curr_bal=account.curr_bal,
            credit_limit=account.credit_limit,
            cash_credit_limit=account.cash_credit_limit,
            open_date=account.open_date,
            expiration_date=account.expiration_date,
            reissue_date=account.reissue_date,
            curr_cycle_credit=account.curr_cycle_credit,
            curr_cycle_debit=account.curr_cycle_debit,
            addr_zip=account.addr_zip,
            group_id=account.group_id,
            customer_id=customer_id,
            customer_name=customer_name,
        )
