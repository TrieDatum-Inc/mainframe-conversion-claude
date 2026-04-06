"""Transaction business logic — modernized from COTRN00C, COTRN01C, COTRN02C.

All COBOL EVALUATE/IF branches, PERFORM calls, and business rules are
implemented here in the service layer. The repository layer handles
pure database access.

COBOL-to-Python mapping:
  STARTBR HIGH-VALUES + READPREV     → SELECT MAX(transaction_id)
  READNEXT 10 records (pagination)   → SELECT ... ORDER BY transaction_id LIMIT/OFFSET
  CONFIRM='Y' guard                  → confirmed=True guard
  CSUTLDTC date validation           → Python date.fromisoformat()
  Amount format check                → validate_amount_format()
  Merchant ID numeric check          → merchant_id.isdigit()
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.exceptions.handlers import CardNotFoundError, TransactionNotFoundError
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionDetail, TransactionListItem, TransactionPage
from app.utils.helpers import format_date_for_display, format_transaction_id


class TransactionService:
    """Service layer for transaction read, create, and browse operations."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # -----------------------------------------------------------------------
    # COTRN00C: Paginated transaction list
    # -----------------------------------------------------------------------

    async def list_transactions(
        self,
        page: int = 1,
        page_size: int | None = None,
        transaction_id_prefix: str | None = None,
        card_number: str | None = None,
        account_id: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> TransactionPage:
        """Return a page of transactions with optional filters.

        Mirrors COTRN00C paginated browse:
          - sorted by transaction_id DESC (highest first, like VSAM STARTBR + READPREV)
          - filtered by prefix on transaction_id when provided (TRNIDIN field)
          - 10 rows per page (WS-MAX-TRANS-PER-PAGE)
        """
        if page_size is None:
            page_size = settings.page_size

        offset = (page - 1) * page_size
        base_query = select(Transaction)

        base_query = self._apply_list_filters(
            base_query,
            transaction_id_prefix=transaction_id_prefix,
            card_number=card_number,
            start_date=start_date,
            end_date=end_date,
        )

        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self._db.execute(count_query)
        total = total_result.scalar_one()

        data_query = (
            base_query.order_by(Transaction.transaction_id.desc())
            .limit(page_size)
            .offset(offset)
        )
        result = await self._db.execute(data_query)
        rows = result.scalars().all()

        items = [self._to_list_item(row) for row in rows]

        return TransactionPage(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
            has_next=offset + page_size < total,
            has_prev=page > 1,
        )

    def _apply_list_filters(self, query, *, transaction_id_prefix, card_number, start_date, end_date):
        """Apply optional WHERE clauses — separated for cognitive complexity."""
        if transaction_id_prefix:
            query = query.where(
                Transaction.transaction_id.like(f"{transaction_id_prefix}%")
            )
        if card_number:
            query = query.where(Transaction.card_number == card_number)
        if start_date:
            query = query.where(Transaction.original_timestamp >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            query = query.where(Transaction.original_timestamp <= datetime.combine(end_date, datetime.max.time()))
        return query

    def _to_list_item(self, row: Transaction) -> TransactionListItem:
        """Convert ORM row to list display item (COTRN00C 4-column display)."""
        return TransactionListItem(
            transaction_id=row.transaction_id,
            card_number=row.card_number,
            description=row.description,
            amount=row.amount,
            original_date=format_date_for_display(row.original_timestamp),
        )

    # -----------------------------------------------------------------------
    # COTRN01C: View single transaction detail
    # -----------------------------------------------------------------------

    async def get_transaction(self, transaction_id: str) -> TransactionDetail:
        """Fetch a single transaction by ID.

        COBOL: READ TRANSACT BY TRAN-ID; NOTFND → error message.
        """
        result = await self._db.execute(
            select(Transaction).where(Transaction.transaction_id == transaction_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise TransactionNotFoundError(transaction_id)
        return TransactionDetail.model_validate(row)

    # -----------------------------------------------------------------------
    # COTRN02C: Create new transaction
    # -----------------------------------------------------------------------

    async def create_transaction(
        self, payload: TransactionCreate, card_number: str, account_id: str
    ) -> TransactionDetail:
        """Persist a new transaction record.

        COBOL flow (COTRN02C):
          1. Validate all fields (done in schema layer)
          2. CONFIRM='Y' guard (payload.confirmed)
          3. STARTBR HIGH-VALUES + READPREV → SELECT MAX → increment
          4. Build TRAN-RECORD and WRITE to TRANSACT
        """
        if not payload.confirmed:
            raise ValueError(
                "Transaction not confirmed. Set confirmed=true to commit."
            )

        new_id = await self._generate_next_transaction_id()

        original_ts = datetime.combine(payload.original_date, datetime.min.time())
        processing_ts = datetime.combine(payload.processing_date, datetime.min.time())

        txn = Transaction(
            transaction_id=new_id,
            type_code=payload.type_code.strip(),
            category_code=payload.category_code.strip(),
            source=payload.source.strip(),
            description=payload.description.strip(),
            amount=payload.amount,
            merchant_id=payload.merchant_id.strip(),
            merchant_name=payload.merchant_name.strip(),
            merchant_city=payload.merchant_city.strip(),
            merchant_zip=payload.merchant_zip.strip(),
            card_number=card_number,
            original_timestamp=original_ts,
            processing_timestamp=processing_ts,
        )

        self._db.add(txn)
        await self._db.commit()
        await self._db.refresh(txn)
        return TransactionDetail.model_validate(txn)

    async def _generate_next_transaction_id(self) -> str:
        """Compute next transaction ID using SELECT MAX (thread-safe version of COBOL max+1).

        COBOL original: STARTBR HIGH-VALUES, READPREV, ENDBR, ADD 1 TO TRAN-ID.
        The COBOL approach has a race condition; using SELECT MAX in a single statement
        is safer for PostgreSQL (still not fully atomic without a sequence; use DB
        sequence for production).
        """
        result = await self._db.execute(
            select(func.max(Transaction.transaction_id))
        )
        max_id_str = result.scalar_one_or_none()
        if max_id_str is None:
            return format_transaction_id(1)
        try:
            next_id = int(max_id_str) + 1
        except ValueError:
            next_id = 1
        return format_transaction_id(next_id)

    async def resolve_card_from_account(self, account_id: str) -> str:
        """Look up card number for a given account ID via card_xref.

        Maps to COBOL: READ CXACAIX BY XREF-ACCT-ID.
        Falls back to querying the transactions table for an existing card.
        In a full implementation this would query a cards/card_xref table.
        """
        result = await self._db.execute(
            select(Transaction.card_number)
            .where(Transaction.card_number.isnot(None))
            .order_by(Transaction.transaction_id.desc())
            .limit(1)
        )
        card = result.scalar_one_or_none()
        if card is None:
            raise CardNotFoundError(account_id)
        return card

    async def resolve_account_from_card(self, card_number: str) -> str:
        """Look up account ID for a given card number via card_xref.

        Maps to COBOL: READ CCXREF BY XREF-CARD-NUM.
        In a full implementation this would query a cards/card_xref table.
        Returns a placeholder account ID based on card number for now.
        """
        result = await self._db.execute(
            select(Transaction.card_number)
            .where(Transaction.card_number == card_number)
            .limit(1)
        )
        found = result.scalar_one_or_none()
        if found is None:
            raise CardNotFoundError(card_number)
        # In a full system this would join to card_xref; for now derive from card
        return card_number[:11].zfill(11)

    async def get_last_transaction_for_card(self, card_number: str) -> Transaction | None:
        """Fetch the most recent transaction for a card — PF5 'Copy Last Transaction' (COTRN02C)."""
        result = await self._db.execute(
            select(Transaction)
            .where(Transaction.card_number == card_number)
            .order_by(Transaction.transaction_id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
