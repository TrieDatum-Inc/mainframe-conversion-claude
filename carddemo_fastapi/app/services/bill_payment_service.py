"""Bill payment service ported from COBIL00C.cbl.

COBIL00C: Process bill payments by reading the account balance,
          creating a payment transaction, and updating the account balance.
          Uses a two-step confirmation flow (confirm='N' shows balance,
          confirm='Y' processes payment).
"""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.card_xref import CardXref
from app.models.transaction import Transaction
from app.exceptions import RecordNotFoundError, ValidationError


def process_bill_payment(
    db: Session,
    acct_id: int,
    confirm: str = "N",
) -> dict:
    """Process a bill payment, ported from COBIL00C.

    Flow:
    1. Read account by acct_id
    2. Validate balance > 0
    3. Confirmation step
    4. On confirm='Y': create payment transaction, update balance

    Returns:
        dict with message, balance info, and optional tran_id.

    Raises:
        RecordNotFoundError: If account or card xref not found.
        ValidationError: If balance <= 0 or invalid confirmation value.
    """
    # 1. Read account
    account = (
        db.query(Account)
        .filter(Account.acct_id == acct_id)
        .first()
    )

    if not account:
        raise RecordNotFoundError("Account ID NOT found")

    # 2. Check balance
    if account.acct_curr_bal is None or account.acct_curr_bal <= Decimal("0"):
        raise ValidationError("You have nothing to pay")

    # 3. Validate confirmation value
    confirm_upper = confirm.upper() if confirm else ""
    if confirm_upper not in ("Y", "N"):
        raise ValidationError("Invalid value. Valid values are (Y/N)")

    # If not confirmed, return balance preview
    if confirm_upper != "Y":
        return {
            "message": "Confirm to make a bill payment",
            "previous_balance": account.acct_curr_bal,
            "acct_id": acct_id,
        }

    # 4. Process payment (confirm == 'Y')

    # a. Read card_xref by acct_id (CXACAIX alternate index)
    xref = (
        db.query(CardXref)
        .filter(CardXref.xref_acct_id == acct_id)
        .first()
    )
    if not xref:
        raise RecordNotFoundError("Account ID NOT found")

    # b. Generate new tran_id: MAX(tran_id) + 1, zero-padded to 16 chars
    max_tran_id = db.query(func.max(Transaction.tran_id)).scalar()
    if max_tran_id:
        numeric_part = int(max_tran_id[3:])  # remove "TRN"
        new_id_int = numeric_part + 1
    else:
        new_id_int = 1

    new_tran_id = f"TRN{str(new_id_int).zfill(13)}"

    # Save old balance for response
    old_balance = account.acct_curr_bal
    payment_amt = account.acct_curr_bal

    # Current timestamp
    now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H.%M.%S.%f")

    # c. Create payment transaction
    payment_txn = Transaction(
        tran_id=new_tran_id,
        tran_type_cd="02",
        tran_cat_cd=2,
        tran_source="POS TERM",
        tran_desc="BILL PAYMENT - ONLINE",
        tran_amt=payment_amt,
        tran_merchant_id=999999999,
        tran_merchant_name="BILL PAYMENT",
        tran_merchant_city="N/A",
        tran_merchant_zip="N/A",
        tran_card_num=xref.xref_card_num,
        tran_orig_ts=now_ts,
        tran_proc_ts=now_ts,
    )
    db.add(payment_txn)

    # d. Update account balance
    new_balance = account.acct_curr_bal - payment_amt
    account.acct_curr_bal = new_balance

    # e. Commit both in same database transaction
    db.commit()

    # f. Return result
    return {
        "message": f"Payment successful. Your Transaction ID is {new_tran_id}.",
        "tran_id": new_tran_id,
        "previous_balance": old_balance,
        "new_balance": new_balance,
    }
