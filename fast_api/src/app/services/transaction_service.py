"""
Transaction Service — business logic layer.

This module contains all business rules from:
- COTRN00C: paginated list logic (PROCESS-PAGE-FORWARD / PROCESS-PAGE-BACKWARD)
- COTRN01C: detail view logic (READ-TRANSACT-FILE, no update locking)
- COTRN02C: add logic (VALIDATE-INPUT-KEY-FIELDS, VALIDATE-INPUT-DATA-FIELDS,
            ADD-TRANSACTION, COPY-LAST-TRAN-DATA)
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction
from app.repositories.account_repository import AccountRepository
from app.repositories.card_xref_repository import CardXrefRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.common import PaginationMeta
from app.schemas.transaction import (
    TransactionCreate,
    TransactionDetail,
    TransactionListItem,
    TransactionListResponse,
    TransactionValidateRequest,
    TransactionValidateResponse,
)
from app.utils.exceptions import (
    AccountInactiveError,
    AccountNotFoundError,
    CardNotFoundError,
    DuplicateTransactionError,
    TransactionNotFoundError,
)
from app.utils.formatters import format_amount, normalize_amount_str


class TransactionService:
    """
    Encapsulates all transaction processing business logic.
    Mirrors the three CICS programs: COTRN00C, COTRN01C, COTRN02C.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._tran_repo = TransactionRepository(session)
        self._xref_repo = CardXrefRepository(session)
        self._acct_repo = AccountRepository(session)

    # ------------------------------------------------------------------
    # COTRN00C: Transaction List (paginated browse)
    # ------------------------------------------------------------------

    async def list_transactions(
        self,
        page: int,
        page_size: int,
        start_tran_id: str | None,
        direction: str,
        anchor_tran_id: str | None,
    ) -> TransactionListResponse:
        """
        Paginated transaction browse.

        Business rules from COTRN00C:
        - Page size is exactly page_size (default 10)
        - Forward: reads from start_tran_id or beginning
        - Backward: reads backwards from anchor and reverses for display
        - One extra record read detects whether next/prev page exists
        - Page number tracked by caller via pagination metadata
        """
        if direction == "backward" and anchor_tran_id:
            return await self._list_page_backward(anchor_tran_id, page, page_size)
        return await self._list_page_forward(start_tran_id, page, page_size)

    async def _list_page_forward(
        self,
        start_tran_id: str | None,
        page: int,
        page_size: int,
    ) -> TransactionListResponse:
        """Mirrors PROCESS-PAGE-FORWARD: STARTBR + READNEXT loop."""
        rows = await self._tran_repo.get_page_forward(start_tran_id, page_size)

        has_next = len(rows) > page_size
        items = rows[:page_size]

        list_items = [_to_list_item(t) for t in items]
        first_id = items[0].tran_id if items else None
        last_id = items[-1].tran_id if items else None

        return TransactionListResponse(
            items=list_items,
            pagination=PaginationMeta(
                page=page,
                page_size=page_size,
                has_next_page=has_next,
                has_prev_page=page > 1,
                first_tran_id=first_id,
                last_tran_id=last_id,
            ),
        )

    async def _list_page_backward(
        self,
        anchor_tran_id: str,
        page: int,
        page_size: int,
    ) -> TransactionListResponse:
        """Mirrors PROCESS-PAGE-BACKWARD: STARTBR + READPREV loop (reversed for display)."""
        rows = await self._tran_repo.get_page_backward(anchor_tran_id, page_size)

        has_prev = len(rows) > page_size
        items = rows[-page_size:] if has_prev else rows  # trim the extra look-behind record

        list_items = [_to_list_item(t) for t in items]
        first_id = items[0].tran_id if items else None
        last_id = items[-1].tran_id if items else None

        return TransactionListResponse(
            items=list_items,
            pagination=PaginationMeta(
                page=page,
                page_size=page_size,
                has_next_page=True,  # we came backwards so there is always a next page
                has_prev_page=has_prev,
                first_tran_id=first_id,
                last_tran_id=last_id,
            ),
        )

    # ------------------------------------------------------------------
    # COTRN01C: Transaction Detail (read-only view)
    # ------------------------------------------------------------------

    async def get_transaction(self, tran_id: str) -> TransactionDetail:
        """
        Read-only detail fetch.
        Mirrors READ-TRANSACT-FILE. The original uses READ WITH UPDATE but never REWRITEs
        — this is a known anomaly; we implement a plain read with no locking.
        """
        tran = await self._tran_repo.get_by_id(tran_id)
        if tran is None:
            raise TransactionNotFoundError(f"Transaction ID NOT found: {tran_id}")
        return TransactionDetail.model_validate(tran)

    # ------------------------------------------------------------------
    # COTRN02C: Validate input (step 1 — before confirmation)
    # ------------------------------------------------------------------

    async def validate_transaction_input(
        self, request: TransactionValidateRequest
    ) -> TransactionValidateResponse:
        """
        Mirrors VALIDATE-INPUT-KEY-FIELDS + VALIDATE-INPUT-DATA-FIELDS.
        Returns resolved card/account info for the confirmation screen.
        """
        card_num, acct_id = await self._resolve_card_and_account(request)
        account = await self._acct_repo.get_by_id(acct_id)
        if account is None:
            raise AccountNotFoundError(f"Account ID NOT found: {acct_id}")
        if account.acct_active_status != "Y":
            raise AccountInactiveError(
                f"Account {acct_id} is not active. Transaction cannot be added."
            )
        normalized = normalize_amount_str(request.tran_amt)
        return TransactionValidateResponse(
            resolved_card_num=card_num,
            resolved_acct_id=acct_id,
            acct_active=True,
            normalized_amt=normalized,
        )

    # ------------------------------------------------------------------
    # COTRN02C: Add transaction (step 2 — after confirmation Y)
    # ------------------------------------------------------------------

    async def add_transaction(self, request: TransactionCreate) -> TransactionDetail:
        """
        Mirrors ADD-TRANSACTION paragraph:
        1. Resolve card/account via cross-reference
        2. Validate account is active
        3. Auto-generate next transaction ID (HIGH-VALUES READPREV + 1)
        4. Write new transaction record
        5. Return created record (success message includes new Tran ID)
        """
        card_num, acct_id = await self._resolve_card_and_account(request)

        account = await self._acct_repo.get_by_id(acct_id)
        if account is None:
            raise AccountNotFoundError(f"Account ID NOT found: {acct_id}")
        if account.acct_active_status != "Y":
            raise AccountInactiveError(
                f"Account {acct_id} is not active. Transaction cannot be added."
            )

        new_tran_id = await self._tran_repo.get_next_sequence_id()
        if await self._tran_repo.exists(new_tran_id):
            raise DuplicateTransactionError(f"Tran ID already exist: {new_tran_id}")

        tran_amt = _parse_amount(request.tran_amt)
        orig_ts = datetime.strptime(request.tran_orig_dt, "%Y-%m-%d")
        proc_ts = datetime.strptime(request.tran_proc_dt, "%Y-%m-%d")

        new_tran = Transaction(
            tran_id=new_tran_id,
            tran_type_cd=request.tran_type_cd.strip().zfill(2),
            tran_cat_cd=request.tran_cat_cd.strip().zfill(4),
            tran_source=request.tran_source.strip(),
            tran_desc=request.tran_desc.strip(),
            tran_amt=tran_amt,
            tran_merchant_id=request.tran_merchant_id.strip().zfill(9),
            tran_merchant_name=request.tran_merchant_name.strip(),
            tran_merchant_city=request.tran_merchant_city.strip(),
            tran_merchant_zip=request.tran_merchant_zip.strip(),
            tran_card_num=card_num,
            tran_orig_ts=orig_ts,
            tran_proc_ts=proc_ts,
        )
        created = await self._tran_repo.create(new_tran)
        await self._session.commit()
        return TransactionDetail.model_validate(created)

    # ------------------------------------------------------------------
    # COTRN02C: Copy last transaction data (PF5 equivalent)
    # ------------------------------------------------------------------

    async def get_last_transaction_data(
        self, card_num: str | None, acct_id: str | None
    ) -> TransactionDetail:
        """
        Mirrors COPY-LAST-TRAN-DATA: validates key fields then reads last record.
        The caller pre-fills data fields from the returned record.
        """
        if not card_num and not acct_id:
            from app.utils.exceptions import ValidationError
            raise ValidationError("Account or Card Number must be entered")

        last = await self._tran_repo.get_last_transaction()
        if last is None:
            from app.utils.exceptions import ValidationError
            raise ValidationError("No existing transactions to copy from")
        return TransactionDetail.model_validate(last)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _resolve_card_and_account(
        self, request: TransactionValidateRequest
    ) -> tuple[str, str]:
        """
        Mirrors VALIDATE-INPUT-KEY-FIELDS — resolves card_num and acct_id
        from whichever identifier the user provided.

        Path 1: acct_id entered → lookup CXACAIX (alternate index) → get card_num
        Path 2: card_num entered → lookup CCXREF (primary) → get acct_id
        """
        if request.acct_id:
            padded_acct = request.acct_id.strip().zfill(11)
            xref = await self._xref_repo.get_by_acct_id(padded_acct)
            if xref is None:
                raise AccountNotFoundError(f"Account ID NOT found: {padded_acct}")
            return xref.xref_card_num, xref.xref_acct_id

        # card_num path
        padded_card = request.card_num.strip().zfill(16)  # type: ignore[union-attr]
        xref = await self._xref_repo.get_by_card_num(padded_card)
        if xref is None:
            raise CardNotFoundError(f"Card Number NOT found: {padded_card}")
        return xref.xref_card_num, xref.xref_acct_id


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _to_list_item(tran: Transaction) -> TransactionListItem:
    return TransactionListItem(
        tran_id=tran.tran_id,
        tran_orig_ts=tran.tran_orig_ts,
        tran_desc=tran.tran_desc,
        tran_amt=tran.tran_amt,
    )


def _parse_amount(amount_str: str) -> Decimal:
    """Convert ±99999999.99 string to Decimal. Mirrors FUNCTION NUMVAL-C."""
    try:
        return Decimal(amount_str.strip())
    except InvalidOperation as exc:
        raise ValueError(f"Invalid amount format: {amount_str}") from exc
