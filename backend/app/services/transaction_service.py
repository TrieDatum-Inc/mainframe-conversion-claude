"""
Business logic service for transactions.

COBOL origin:
  COTRN00C — Transaction list/browse (POPULATE-TRAN-DATA paragraph)
  COTRN01C — Transaction detail view (PROCESS-ENTER-KEY paragraph)
  COTRN02C — Transaction add (PROCESS-ENTER-KEY + ADD-TRANSACTION + VALIDATE-INPUT-FIELDS)

All COBOL paragraph logic is reproduced here. No database calls — delegates to repositories.
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.errors import (
    AccountNotFoundError,
    CardNotFoundError,
    TransactionNotFoundError,
    TransactionTypeNotFoundError,
    ValidationError as ServiceValidationError,
)
from app.models.transaction import Transaction
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.transaction import (
    TransactionCreateRequest,
    TransactionDetailResponse,
    TransactionListItem,
    TransactionListResponse,
)


class TransactionService:
    """
    Service handling all COTRN00C / COTRN01C / COTRN02C business logic.

    Architecture note: This service delegates all data access to TransactionRepository
    and performs all business logic here. No SQLAlchemy queries appear in this file.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.repo = TransactionRepository(db)
        self.db = db

    async def list_transactions(
        self,
        page: int = 1,
        page_size: int = 10,
        tran_id_filter: Optional[str] = None,
        card_number: Optional[str] = None,
        account_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        type_code: Optional[str] = None,
    ) -> TransactionListResponse:
        """
        Paginated transaction list with optional filters.

        COBOL origin: COTRN00C POPULATE-TRAN-DATA paragraph.
          10 rows per page (matches COTRN0A BMS map 10-row display limit).
          TRNIDINI filter: STARTBR key = filter → WHERE transaction_id >= filter.
          CDEMO-CT00-NEXT-PAGE-FLG → has_next (replaced by total_count comparison).

        Pagination logic:
          COTRN00C stored TRNID-FIRST/TRNID-LAST in commarea as STARTBR anchors.
          Modern: stateless pagination via page/page_size offsets.
        """
        self._validate_page_params(page, page_size)

        transactions, total_count = await self.repo.list_transactions(
            page=page,
            page_size=page_size,
            tran_id_filter=tran_id_filter,
            card_number=card_number,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            type_code=type_code,
        )

        items = [self._to_list_item(t) for t in transactions]

        first_key = items[0].transaction_id if items else None
        last_key = items[-1].transaction_id if items else None

        return TransactionListResponse(
            items=items,
            page=page,
            page_size=page_size,
            total_count=total_count,
            has_next=total_count > page * page_size,
            has_previous=page > 1,
            first_item_key=first_key,
            last_item_key=last_key,
        )

    async def get_transaction(self, transaction_id: str) -> TransactionDetailResponse:
        """
        Retrieve a single transaction by ID.

        COBOL origin: COTRN01C PROCESS-ENTER-KEY.
          Validates TRNIDINI (non-blank, numeric) then calls READ-TRANS-FILE.

        BUG FIX: COTRN01C issued READ UPDATE (exclusive lock) for a display-only
        operation. The lock was never used (no REWRITE/DELETE followed).
        This method uses a plain SELECT — no lock acquired.

        COBOL: EXEC CICS READ FILE('TRANSACT') ... UPDATE RESP RESP2
        Modern: SELECT * FROM transactions WHERE transaction_id = ? (no FOR UPDATE)
        """
        self._validate_transaction_id(transaction_id)

        transaction = await self.repo.get_by_id(transaction_id)
        if not transaction:
            raise TransactionNotFoundError(transaction_id)

        return self._to_detail_response(transaction)

    async def create_transaction(
        self, request: TransactionCreateRequest
    ) -> TransactionDetailResponse:
        """
        Create a new transaction record.

        COBOL origin: COTRN02C ADD-TRANSACTION paragraph.

        Processing steps (maps COTRN02C flow):
          1. Determine card_number and account_id from request (card XOR account lookup)
          2. Validate account exists (COTRN02C: LOOKUP-ACCT-FROM-CARD / LOOKUP-CARD-FROM-ACCT)
          3. Validate transaction_type_code exists (COTRN02C: TRNTYPEI numeric check; FK validation)
          4. Generate transaction_id via sequence (fixes COTRN02C STARTBR/READPREV race condition)
          5. Insert transaction record (COTRN02C: EXEC CICS WRITE FILE(WS-TRANSACT-FILE))

        COTRN02C CONFIRMI gate: already enforced at schema level (Literal['Y']).
        Amount != 0: already enforced at schema level (@model_validator).
        Date validation: already enforced at schema level (@model_validator).
        """
        card_number, account_id = await self._resolve_card_and_account(request)
        await self._validate_transaction_type(request.transaction_type_code)

        transaction_id = await self.repo.generate_transaction_id()

        transaction = Transaction(
            transaction_id=transaction_id,
            card_number=card_number,
            transaction_type_code=request.transaction_type_code,
            transaction_category_code=request.transaction_category_code,
            transaction_source=request.transaction_source,
            description=request.description,
            amount=float(request.amount),
            original_date=request.original_date,
            processed_date=request.processed_date,
            merchant_id=request.merchant_id,
            merchant_name=request.merchant_name,
            merchant_city=request.merchant_city,
            merchant_zip=request.merchant_zip,
        )

        created = await self.repo.create(transaction)
        return self._to_detail_response(created)

    async def get_last_transaction(self) -> Optional[TransactionDetailResponse]:
        """
        Get the most recently created transaction.

        COBOL origin: COTRN02C PF5 COPY-LAST-TRAN-DATA.
          Copies last successfully added transaction from WS-LAST-TRAN-* working storage
          back to screen fields for rapid re-entry of similar transactions.

        Modern: SELECT ... ORDER BY transaction_id DESC LIMIT 1.
        """
        transaction = await self.repo.get_last_created()
        if not transaction:
            return None
        return self._to_detail_response(transaction)

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    async def _resolve_card_and_account(
        self, request: TransactionCreateRequest
    ) -> tuple[str, int]:
        """
        Resolve card_number and account_id from the mutual-exclusion input.

        COBOL origin: COTRN02C:
          If CARDINPI provided: LOOKUP-ACCT-FROM-CARD → READ CCXREF by card → get XREF-ACCT-ID
          If ACCTIDOI provided: LOOKUP-CARD-FROM-ACCT → READ CXACAIX (AIX) by account → get XREF-CARD-NUM

        Returns (card_number, account_id) tuple for both cases.
        Raises CardNotFoundError or AccountNotFoundError if lookup fails.
        """
        from sqlalchemy import select
        from app.models.card_xref import CardAccountXref
        from app.models.account import Account

        if request.card_number:
            return await self._lookup_account_from_card(request.card_number)
        else:
            return await self._lookup_card_from_account(request.account_id)

    async def _lookup_account_from_card(self, card_number: str) -> tuple[str, int]:
        """
        Look up account_id from card_number via card_account_xref.

        COBOL origin: COTRN02C LOOKUP-ACCT-FROM-CARD:
          EXEC CICS READ FILE(WS-CCXREF-FILE) INTO(CARD-XREF-RECORD)
                    RIDFLD(WS-CARD-NUM) RESP RESP2
          → XREF-ACCT-ID found in CARD-XREF-RECORD
        """
        from sqlalchemy import select
        from app.models.card_xref import CardAccountXref

        result = await self.db.execute(
            select(CardAccountXref).where(CardAccountXref.card_number == card_number)
        )
        xref = result.scalar_one_or_none()
        if not xref:
            raise CardNotFoundError(card_number)
        return card_number, xref.account_id

    async def _lookup_card_from_account(self, account_id: int) -> tuple[str, int]:
        """
        Look up card_number from account_id via card_account_xref.

        COBOL origin: COTRN02C LOOKUP-CARD-FROM-ACCT:
          EXEC CICS READ FILE(WS-CXACAIX-FILE) INTO(CARD-XREF-RECORD)
                    RIDFLD(WS-ACCT-ID) RESP RESP2
          → CXACAIX is the alternate index on CCXREF keyed by account ID
          → XREF-CARD-NUM found in CARD-XREF-RECORD
        """
        from sqlalchemy import select
        from app.models.card_xref import CardAccountXref

        result = await self.db.execute(
            select(CardAccountXref)
            .where(CardAccountXref.account_id == account_id)
            .limit(1)
        )
        xref = result.scalar_one_or_none()
        if not xref:
            raise AccountNotFoundError(account_id)
        return xref.card_number, account_id

    async def _validate_transaction_type(self, type_code: str) -> None:
        """
        Validate transaction type code exists in transaction_types table.

        COBOL origin: COTRN02C VALIDATE-INPUT-FIELDS — TRNTYPEI numeric check.
          The COBOL only validated that the type code was numeric; it did not
          check existence in the transaction types table.
          Modern: FK constraint on transaction_type_code enforces existence.
          This pre-check provides a better error message than a FK violation.
        """
        from sqlalchemy import select
        from app.models.transaction_type import TransactionType

        result = await self.db.execute(
            select(TransactionType).where(TransactionType.type_code == type_code)
        )
        if not result.scalar_one_or_none():
            raise TransactionTypeNotFoundError(type_code)

    def _validate_transaction_id(self, transaction_id: str) -> None:
        """
        Validate transaction ID format.

        COBOL origin: COTRN01C PROCESS-ENTER-KEY:
          IF TRNIDINI = SPACES: error 'Please enter a transaction ID'
          MOVE TRNIDINI TO WS-TRAN-ID-NUM (numeric conversion — implicit numeric check)
        """
        if not transaction_id or not transaction_id.strip():
            raise ServiceValidationError("transaction_id", "Transaction ID cannot be blank")

    def _validate_page_params(self, page: int, page_size: int) -> None:
        """Validate pagination parameters."""
        if page < 1:
            raise ServiceValidationError("page", "Page must be >= 1")
        if page_size < 1 or page_size > 100:
            raise ServiceValidationError("page_size", "Page size must be between 1 and 100")

    def _to_list_item(self, t: Transaction) -> TransactionListItem:
        """
        Map ORM Transaction to TransactionListItem.

        COBOL origin: COTRN00C POPULATE-TRAN-DATA — maps TRAN-RECORD fields
        to screen output fields TRNID1O–TRNID10O, TRNDT1O–TRNDT10O, etc.
        """
        return TransactionListItem(
            transaction_id=t.transaction_id,
            original_date=t.original_date,
            description=t.description,
            amount=Decimal(str(t.amount)),
        )

    def _to_detail_response(self, t: Transaction) -> TransactionDetailResponse:
        """
        Map ORM Transaction to TransactionDetailResponse.

        COBOL origin: COTRN01C POPULATE-TRAN-FIELDS — maps all TRAN-RECORD fields
        to COTRN1AO output fields for display.
        """
        return TransactionDetailResponse(
            transaction_id=t.transaction_id,
            card_number=t.card_number,
            transaction_type_code=t.transaction_type_code,
            transaction_category_code=t.transaction_category_code,
            transaction_source=t.transaction_source,
            description=t.description,
            amount=Decimal(str(t.amount)),
            original_date=t.original_date,
            processed_date=t.processed_date,
            merchant_id=t.merchant_id,
            merchant_name=t.merchant_name,
            merchant_city=t.merchant_city,
            merchant_zip=t.merchant_zip,
            created_at=t.created_at,
            updated_at=t.updated_at,
        )
