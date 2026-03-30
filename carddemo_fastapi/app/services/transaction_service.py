"""Transaction management service ported from COTRN00C, COTRN01C, COTRN02C.

COTRN00C: Browse/list transactions with optional tran_id filter.
          BMS page size = 10.
COTRN01C: View a single transaction by tran_id.
COTRN02C: Add a new transaction with full validation flow, confirmation
          step, and auto-generated tran_id.
"""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.card_xref import CardXref
from app.models.transaction import Transaction
from app.exceptions import RecordNotFoundError, ValidationError
from app.services.validation import validate_not_empty


def list_transactions(
    db: Session,
    tran_id_filter: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> dict:
    """Paginated transaction list, ported from COTRN00C.

    If tran_id_filter provided, filters WHERE tran_id >= filter.
    Page size 10 matches the BMS screen layout.

    Returns:
        PaginatedResponse-compatible dict.

    Raises:
        ValidationError: If tran_id_filter is not numeric.
    """
    query = db.query(Transaction)

    if tran_id_filter is not None:
        clean = tran_id_filter.strip()
        if clean and not clean.isdigit():
            raise ValidationError(
                "Tran ID must be Numeric", field="tran_id"
            )
        if clean:
            query = query.filter(Transaction.tran_id >= clean)

    total_count = query.count()

    offset = (page - 1) * page_size
    transactions = (
        query.order_by(Transaction.tran_id)
        .offset(offset)
        .limit(page_size)
        .all()
    )

    has_next_page = (offset + page_size) < total_count

    return {
        "items": [
            {
                "tran_id": t.tran_id,
                "tran_card_num": t.tran_card_num,
                "tran_amt": t.tran_amt,
                "tran_orig_ts": t.tran_orig_ts,
                "tran_type_cd": t.tran_type_cd,
            }
            for t in transactions
        ],
        "page": page,
        "page_size": page_size,
        "total_count": total_count,
        "has_next_page": has_next_page,
    }


def get_transaction(db: Session, tran_id: str) -> dict:
    """Get a single transaction, ported from COTRN01C.

    Returns:
        dict with all transaction fields.

    Raises:
        ValidationError: If tran_id is blank.
        RecordNotFoundError: If transaction not found.
    """
    if not tran_id or tran_id.strip() == "":
        raise ValidationError(
            "Tran ID can NOT be empty", field="tran_id"
        )

    txn = (
        db.query(Transaction)
        .filter(Transaction.tran_id == tran_id.strip())
        .first()
    )

    if not txn:
        raise RecordNotFoundError("Transaction not found")

    return {
        "tran_id": txn.tran_id,
        "tran_type_cd": txn.tran_type_cd,
        "tran_cat_cd": txn.tran_cat_cd,
        "tran_source": txn.tran_source,
        "tran_desc": txn.tran_desc,
        "tran_amt": txn.tran_amt,
        "tran_merchant_id": txn.tran_merchant_id,
        "tran_merchant_name": txn.tran_merchant_name,
        "tran_merchant_city": txn.tran_merchant_city,
        "tran_merchant_zip": txn.tran_merchant_zip,
        "tran_card_num": txn.tran_card_num,
        "tran_orig_ts": txn.tran_orig_ts,
        "tran_proc_ts": txn.tran_proc_ts,
    }


def add_transaction(
    db: Session,
    card_num: str | None = None,
    acct_id: int | None = None,
    tran_type_cd: str = "",
    tran_cat_cd: int = 0,
    tran_source: str = "",
    tran_desc: str = "",
    tran_amt: Decimal = Decimal("0"),
    merchant_id: int = 0,
    merchant_name: str = "",
    merchant_city: str = "",
    merchant_zip: str = "",
    confirm: str = "N",
) -> dict:
    """Add a new transaction, ported from COTRN02C.

    Validation flow:
    1. Either card_num or acct_id must be provided
    2. Look up cross-reference to resolve the other identifier
    3. Validate account exists
    4. Check all mandatory fields
    5. Confirmation step (confirm='Y' to commit)
    6. Generate tran_id from MAX + 1, zero-padded to 16 chars

    Returns:
        dict with message (confirmation prompt or success).

    Raises:
        ValidationError: If validation fails.
        RecordNotFoundError: If referenced account/card not found.
    """
    # 1. Either card_num or acct_id must be provided
    if not card_num and not acct_id:
        raise ValidationError(
            "Account or Card Number must be entered",
            field="card_num",
        )

    resolved_card_num = card_num
    resolved_acct_id = acct_id

    # 2. Resolve identifiers via card_xref
    if acct_id and not card_num:
        # Validate acct_id is numeric
        if not str(acct_id).strip().isdigit():
            raise ValidationError(
                "Account ID must be Numeric", field="acct_id"
            )
        xref = (
            db.query(CardXref)
            .filter(CardXref.xref_acct_id == acct_id)
            .first()
        )
        if not xref:
            raise RecordNotFoundError("Account or Card Number not found")
        resolved_card_num = xref.xref_card_num

    if card_num and not acct_id:
        # Validate 16-digit numeric
        clean_card = card_num.strip()
        if not clean_card.isdigit():
            raise ValidationError(
                "Card number must be Numeric", field="card_num"
            )
        if len(clean_card) != 16:
            raise ValidationError(
                "Card number if supplied must be 16 digit",
                field="card_num",
            )
        xref = (
            db.query(CardXref)
            .filter(CardXref.xref_card_num == clean_card)
            .first()
        )
        if not xref:
            raise RecordNotFoundError("Account or Card Number not found")
        resolved_acct_id = xref.xref_acct_id

    # 3. Validate account exists
    account = (
        db.query(Account)
        .filter(Account.acct_id == resolved_acct_id)
        .first()
    )
    if not account:
        raise RecordNotFoundError("Account not found")

    # 4. Validate all mandatory fields
    mandatory = {
        "tran_type_cd": ("Transaction Type Code", tran_type_cd),
        "tran_source": ("Transaction Source", tran_source),
        "tran_desc": ("Transaction Description", tran_desc),
        "tran_amt": ("Transaction Amount", str(tran_amt)),
        "merchant_name": ("Merchant Name", merchant_name),
        "merchant_city": ("Merchant City", merchant_city),
        "merchant_zip": ("Merchant Zip", merchant_zip),
    }
    for field, (label, value) in mandatory.items():
        is_valid, err = validate_not_empty(str(value), label)
        if not is_valid:
            raise ValidationError(err, field=field)

    # Validate amount is not zero
    if tran_amt == Decimal("0"):
        raise ValidationError(
            "Transaction Amount can NOT be empty", field="tran_amt"
        )

    # 5. Confirmation step
    if confirm.upper() != "Y":
        return {"message": "Confirm to add this transaction"}

    # 6. Generate tran_id: MAX(tran_id) + 1, zero-padded to 16 chars
    max_tran_id = db.query(func.max(Transaction.tran_id)).scalar()
    if max_tran_id:
        numeric_part = int(max_tran_id[3:])  # remove "TRN"
        new_id_int = numeric_part + 1
    else:
        new_id_int = 1

    new_tran_id = f"TRN{str(new_id_int).zfill(13)}"

    # Current timestamp for orig_ts and proc_ts
    now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H.%M.%S.%f")

    new_txn = Transaction(
        tran_id=new_tran_id,
        tran_type_cd=tran_type_cd,
        tran_cat_cd=tran_cat_cd,
        tran_source=tran_source,
        tran_desc=tran_desc,
        tran_amt=tran_amt,
        tran_merchant_id=merchant_id,
        tran_merchant_name=merchant_name,
        tran_merchant_city=merchant_city,
        tran_merchant_zip=merchant_zip,
        tran_card_num=resolved_card_num,
        tran_orig_ts=now_ts,
        tran_proc_ts=now_ts,
    )

    db.add(new_txn)
    db.commit()
    db.refresh(new_txn)

    return {
        "message": "Changes committed to database",
        "tran_id": new_tran_id,
    }
