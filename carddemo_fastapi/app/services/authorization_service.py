"""Authorization and fraud management service ported from COPAUA0C,
COPAUS0C, COPAUS1C, COPAUS2C.

COPAUS0C: Browse pending authorization summaries, paginated by
          pa_acct_id.  Page size = 5.
COPAUS1C / COPAUA0C: View authorization detail for a single account
          including all pending auth detail records with response code
          mapping ('00' -> 'Approved', others -> 'Declined').
COPAUS2C: Mark or remove fraud flags on authorization records.
"""

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.auth_fraud import AuthFraud
from app.models.card_xref import CardXref
from app.models.pending_auth_detail import PendingAuthDetail
from app.models.pending_auth_summary import PendingAuthSummary
from app.exceptions import RecordNotFoundError, ValidationError


def list_auth_summary(
    db: Session,
    page: int = 1,
    page_size: int = 5,
) -> dict:
    """Paginated pending authorization summary list, ported from COPAUS0C.

    Orders by pa_acct_id to match VSAM key ordering.  Page size 5
    matches the BMS screen layout.

    Returns:
        PaginatedResponse-compatible dict.
    """
    total_count = db.query(PendingAuthSummary).count()

    offset = (page - 1) * page_size
    summaries = (
        db.query(PendingAuthSummary)
        .order_by(PendingAuthSummary.pa_acct_id)
        .offset(offset)
        .limit(page_size)
        .all()
    )

    has_next_page = (offset + page_size) < total_count

    return {
        "items": [
            {
                "pa_acct_id": s.pa_acct_id,
                "pa_cust_id": s.pa_cust_id,
                "pa_auth_status": s.pa_auth_status,
                "pa_account_status_1": s.pa_account_status_1,
                "pa_account_status_2": s.pa_account_status_2,
                "pa_account_status_3": s.pa_account_status_3,
                "pa_account_status_4": s.pa_account_status_4,
                "pa_account_status_5": s.pa_account_status_5,
                "pa_credit_limit": s.pa_credit_limit,
                "pa_cash_limit": s.pa_cash_limit,
                "pa_credit_balance": s.pa_credit_balance,
                "pa_cash_balance": s.pa_cash_balance,
                "pa_approved_auth_cnt": s.pa_approved_auth_cnt,
                "pa_declined_auth_cnt": s.pa_declined_auth_cnt,
                "pa_approved_auth_amt": s.pa_approved_auth_amt,
                "pa_declined_auth_amt": s.pa_declined_auth_amt,
            }
            for s in summaries
        ],
        "page": page,
        "page_size": page_size,
        "total_count": total_count,
        "has_next_page": has_next_page,
    }


def get_auth_detail(db: Session, acct_id: int) -> dict:
    """Get authorization detail for an account, ported from COPAUS1C / COPAUA0C.

    Reads the pending_auth_summary record and all associated
    pending_auth_details.  Maps auth_resp_code '00' to 'Approved',
    all others to 'Declined'.

    Returns:
        dict with summary fields and a details list.

    Raises:
        RecordNotFoundError: If summary record not found.
    """
    summary = (
        db.query(PendingAuthSummary)
        .filter(PendingAuthSummary.pa_acct_id == acct_id)
        .first()
    )

    if not summary:
        raise RecordNotFoundError("Authorization summary not found for account")

    details = (
        db.query(PendingAuthDetail)
        .filter(PendingAuthDetail.pa_acct_id == acct_id)
        .all()
    )

    detail_list = []
    for d in details:
        # Map auth_resp_code: '00' -> Approved, others -> Declined
        auth_status = (
            "Approved" if d.pa_auth_resp_code == "00" else "Declined"
        )

        detail_list.append(
            {
                "id": d.id,
                "pa_acct_id": d.pa_acct_id,
                "pa_auth_date": d.pa_auth_date,
                "pa_auth_time": d.pa_auth_time,
                "pa_card_num": d.pa_card_num,
                "pa_auth_type": d.pa_auth_type,
                "pa_card_expiry_date": d.pa_card_expiry_date,
                "pa_message_type": d.pa_message_type,
                "pa_message_source": d.pa_message_source,
                "pa_auth_id_code": d.pa_auth_id_code,
                "pa_auth_resp_code": d.pa_auth_resp_code,
                "pa_auth_resp_reason": d.pa_auth_resp_reason,
                "pa_processing_code": d.pa_processing_code,
                "pa_transaction_amt": d.pa_transaction_amt,
                "pa_approved_amt": d.pa_approved_amt,
                "pa_merchant_category_code": d.pa_merchant_category_code,
                "pa_acqr_country_code": d.pa_acqr_country_code,
                "pa_pos_entry_mode": d.pa_pos_entry_mode,
                "pa_merchant_id": d.pa_merchant_id,
                "pa_merchant_name": d.pa_merchant_name,
                "pa_merchant_city": d.pa_merchant_city,
                "pa_merchant_state": d.pa_merchant_state,
                "pa_merchant_zip": d.pa_merchant_zip,
                "pa_transaction_id": d.pa_transaction_id,
                "pa_match_status": d.pa_match_status,
                "pa_auth_fraud": d.pa_auth_fraud,
                "pa_fraud_rpt_date": d.pa_fraud_rpt_date,
                "auth_status": auth_status,
            }
        )

    return {
        "summary": {
            "pa_acct_id": summary.pa_acct_id,
            "pa_cust_id": summary.pa_cust_id,
            "pa_auth_status": summary.pa_auth_status,
            "pa_credit_limit": summary.pa_credit_limit,
            "pa_cash_limit": summary.pa_cash_limit,
            "pa_credit_balance": summary.pa_credit_balance,
            "pa_cash_balance": summary.pa_cash_balance,
            "pa_approved_auth_cnt": summary.pa_approved_auth_cnt,
            "pa_declined_auth_cnt": summary.pa_declined_auth_cnt,
            "pa_approved_auth_amt": summary.pa_approved_auth_amt,
            "pa_declined_auth_amt": summary.pa_declined_auth_amt,
        },
        "details": detail_list,
    }


def mark_fraud(
    db: Session,
    card_num: str,
    auth_ts,
    acct_id: int,
    cust_id: int,
    action: str,
) -> dict:
    """Mark or remove fraud flag on an authorization record, ported from COPAUS2C.

    Actions:
    - 'F': Report fraud -- INSERT or UPDATE auth_fraud with flag 'F'
    - 'R': Remove fraud -- UPDATE auth_fraud flag to 'R' with report date

    Returns:
        dict with status and message.

    Raises:
        ValidationError: If action is not 'F' or 'R'.
    """
    action_upper = action.upper() if action else ""

    if action_upper not in ("F", "R"):
        raise ValidationError(
            "Action must be F (Report Fraud) or R (Remove Fraud)"
        )

    try:
        if action_upper == "F":
            # Try to find existing record
            existing = (
                db.query(AuthFraud)
                .filter(
                    AuthFraud.card_num == card_num,
                    AuthFraud.auth_ts == auth_ts,
                )
                .first()
            )

            if existing:
                # UPDATE existing record with fraud flag
                existing.auth_fraud_flag = "F"
                existing.acct_id = acct_id
                existing.cust_id = cust_id
            else:
                # INSERT new fraud record
                new_fraud = AuthFraud(
                    card_num=card_num,
                    auth_ts=auth_ts,
                    auth_fraud_flag="F",
                    acct_id=acct_id,
                    cust_id=cust_id,
                )
                db.add(new_fraud)

            db.commit()
            return {"status": "success", "message": "AUTH MARKED FRAUD"}

        elif action_upper == "R":
            # UPDATE auth_fraud flag to 'R' and set fraud_rpt_date
            existing = (
                db.query(AuthFraud)
                .filter(
                    AuthFraud.card_num == card_num,
                    AuthFraud.auth_ts == auth_ts,
                )
                .first()
            )

            if not existing:
                raise RecordNotFoundError(
                    "Authorization fraud record not found"
                )

            existing.auth_fraud_flag = "R"
            existing.fraud_rpt_date = date.today()

            db.commit()
            return {"status": "success", "message": "AUTH FRAUD REMOVED"}

    except (RecordNotFoundError, ValidationError):
        raise
    except Exception:
        db.rollback()
        return {"status": "failed", "message": "Fraud update failed"}


def process_authorization(
    db: Session,
    card_num: str,
    auth_type: str,
    card_expiry_date: str,
    transaction_amt: Decimal,
    merchant_category_code: str | None = None,
    acqr_country_code: str | None = None,
    pos_entry_mode: int | None = None,
    merchant_id: str | None = None,
    merchant_name: str | None = None,
    merchant_city: str | None = None,
    merchant_state: str | None = None,
    merchant_zip: str | None = None,
) -> dict:
    """Process an authorization decision, ported from COPAUA0C.

    Performs card/account/summary lookups, makes an approve/decline
    credit decision, writes the result to pending_auth_summary and
    pending_auth_detail, and returns a structured response.

    Returns:
        dict matching AuthDecisionResponse schema.
    """
    transaction_amt = Decimal(str(transaction_amt))

    # --- Generate IDs (replaces MQ-provided fields) ---
    max_txn_id = db.query(func.max(PendingAuthDetail.pa_transaction_id)).scalar()
    if max_txn_id:
        # Extract numeric suffix (handles both "TXN000000000001" and "000000000000001")
        numeric_part = "".join(c for c in max_txn_id if c.isdigit())
        new_id_int = int(numeric_part) + 1 if numeric_part else 1
    else:
        new_id_int = 1
    transaction_id = str(new_id_int).zfill(15)

    now = datetime.now(timezone.utc)
    auth_date = now.strftime("%y%m%d")
    auth_time = now.strftime("%H%M%S")
    auth_id_code = auth_time  # COBOL: MOVE PA-RQ-AUTH-TIME TO PA-RL-AUTH-ID-CODE

    # Helper to build a decline response without DB writes
    def _decline_response(reason: str) -> dict:
        return {
            "card_num": card_num,
            "transaction_id": transaction_id,
            "auth_id_code": auth_id_code,
            "auth_resp_code": "05",
            "auth_resp_reason": reason,
            "approved_amt": Decimal("0"),
        }

    # --- §5100: XREF lookup ---
    xref = db.query(CardXref).filter(CardXref.xref_card_num == card_num).first()
    if not xref:
        return _decline_response("3100")

    # --- §5200: Account lookup ---
    account = db.query(Account).filter(Account.acct_id == xref.xref_acct_id).first()
    if not account:
        return _decline_response("3100")

    # --- §5500: Pending auth summary lookup ---
    summary = (
        db.query(PendingAuthSummary)
        .filter(PendingAuthSummary.pa_acct_id == xref.xref_acct_id)
        .first()
    )
    summary_found = summary is not None

    # --- §6000: Make decision ---
    approve = True
    decline_reason = "0000"

    if summary_found:
        available_amt = summary.pa_credit_limit - summary.pa_credit_balance
        if transaction_amt > available_amt:
            approve = False
            decline_reason = "4100"
    else:
        available_amt = account.acct_credit_limit - account.acct_curr_bal
        if transaction_amt > available_amt:
            approve = False
            decline_reason = "4100"

    if approve:
        resp_code = "00"
        approved_amt = transaction_amt
    else:
        resp_code = "05"
        approved_amt = Decimal("0")

    # --- §8400/§8500: Write auth to DB ---
    try:
        # Update or insert summary
        if not summary_found:
            summary = PendingAuthSummary(
                pa_acct_id=xref.xref_acct_id,
                pa_cust_id=xref.xref_cust_id,
                pa_auth_status="A",
                pa_credit_limit=account.acct_credit_limit,
                pa_cash_limit=account.acct_cash_credit_limit,
                pa_credit_balance=Decimal("0"),
                pa_cash_balance=Decimal("0"),
                pa_approved_auth_cnt=0,
                pa_declined_auth_cnt=0,
                pa_approved_auth_amt=Decimal("0"),
                pa_declined_auth_amt=Decimal("0"),
            )
            db.add(summary)

        # Sync limits from account master
        summary.pa_credit_limit = account.acct_credit_limit
        summary.pa_cash_limit = account.acct_cash_credit_limit

        if approve:
            summary.pa_approved_auth_cnt = (summary.pa_approved_auth_cnt or 0) + 1
            summary.pa_approved_auth_amt = (
                (summary.pa_approved_auth_amt or Decimal("0")) + approved_amt
            )
            summary.pa_credit_balance = (
                (summary.pa_credit_balance or Decimal("0")) + approved_amt
            )
            summary.pa_cash_balance = Decimal("0")
        else:
            summary.pa_declined_auth_cnt = (summary.pa_declined_auth_cnt or 0) + 1
            summary.pa_declined_auth_amt = (
                (summary.pa_declined_auth_amt or Decimal("0")) + transaction_amt
            )

        # Insert detail record
        detail = PendingAuthDetail(
            pa_acct_id=xref.xref_acct_id,
            pa_auth_date=auth_date,
            pa_auth_time=auth_time,
            pa_card_num=card_num,
            pa_auth_type=auth_type,
            pa_card_expiry_date=card_expiry_date,
            pa_message_type="0100",
            pa_message_source="API",
            pa_auth_id_code=auth_id_code,
            pa_auth_resp_code=resp_code,
            pa_auth_resp_reason=decline_reason,
            pa_processing_code=3,
            pa_transaction_amt=transaction_amt,
            pa_approved_amt=approved_amt,
            pa_merchant_category_code=merchant_category_code or "",
            pa_acqr_country_code=acqr_country_code or "",
            pa_pos_entry_mode=pos_entry_mode,
            pa_merchant_id=merchant_id or "",
            pa_merchant_name=merchant_name or "",
            pa_merchant_city=merchant_city or "",
            pa_merchant_state=merchant_state or "",
            pa_merchant_zip=merchant_zip or "",
            pa_transaction_id=transaction_id,
            pa_match_status="P" if approve else "D",
            pa_auth_fraud="",
            pa_fraud_rpt_date="",
        )
        db.add(detail)
        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "card_num": card_num,
        "transaction_id": transaction_id,
        "auth_id_code": auth_id_code,
        "auth_resp_code": resp_code,
        "auth_resp_reason": decline_reason,
        "approved_amt": approved_amt,
    }
