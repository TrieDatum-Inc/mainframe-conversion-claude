"""Account management service ported from COACTVWC and COACTUPC.

COACTVWC: View account details with customer information look-up
          via CARDXREF cross-reference file.
COACTUPC: Update account details with field-level validation including
          date, status, and monetary amount fields.
"""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.card_xref import CardXref
from app.models.customer import Customer
from app.exceptions import RecordNotFoundError, ValidationError
from app.services.validation import (
    validate_date_ccyymmdd,
    validate_signed_decimal,
    validate_yes_no,
)


def get_account_view(db: Session, acct_id: int) -> dict:
    """View account details with associated customer, ported from COACTVWC.

    Flow:
    1. READ ACCTFILE by acct_id
    2. If RESP=13 (not found): raise error
    3. READ CARDXREF by acct_id (CXACAIX alternate index) to get cust_id
    4. READ CUSTFILE by cust_id
    5. Return merged account + customer data

    Returns:
        dict with all account and customer fields.

    Raises:
        RecordNotFoundError: If account not found.
    """
    account = db.query(Account).filter(Account.acct_id == acct_id).first()

    if not account:
        raise RecordNotFoundError(
            "Did not find this account in account master file"
        )

    # Look up customer via card_xref (CXACAIX alternate index)
    xref = (
        db.query(CardXref).filter(CardXref.xref_acct_id == acct_id).first()
    )

    customer_data = {}
    if xref:
        customer = (
            db.query(Customer)
            .filter(Customer.cust_id == xref.xref_cust_id)
            .first()
        )
        if customer:
            customer_data = {
                "cust_id": customer.cust_id,
                "cust_first_name": customer.cust_first_name,
                "cust_middle_name": customer.cust_middle_name,
                "cust_last_name": customer.cust_last_name,
                "cust_addr_line_1": customer.cust_addr_line_1,
                "cust_addr_line_2": customer.cust_addr_line_2,
                "cust_addr_line_3": customer.cust_addr_line_3,
                "cust_addr_state_cd": customer.cust_addr_state_cd,
                "cust_addr_country_cd": customer.cust_addr_country_cd,
                "cust_addr_zip": customer.cust_addr_zip,
                "cust_phone_num_1": customer.cust_phone_num_1,
                "cust_phone_num_2": customer.cust_phone_num_2,
                "cust_ssn": customer.cust_ssn,
                "cust_govt_issued_id": customer.cust_govt_issued_id,
                "cust_dob_yyyymmdd": customer.cust_dob_yyyymmdd,
                "cust_eft_account_id": customer.cust_eft_account_id,
                "cust_pri_card_holder_ind": customer.cust_pri_card_holder_ind,
                "cust_fico_credit_score": customer.cust_fico_credit_score,
            }

    return {
        "acct_id": account.acct_id,
        "acct_active_status": account.acct_active_status,
        "acct_curr_bal": account.acct_curr_bal,
        "acct_credit_limit": account.acct_credit_limit,
        "acct_cash_credit_limit": account.acct_cash_credit_limit,
        "acct_open_date": account.acct_open_date,
        "acct_expiration_date": account.acct_expiration_date,
        "acct_reissue_date": account.acct_reissue_date,
        "acct_curr_cyc_credit": account.acct_curr_cyc_credit,
        "acct_curr_cyc_debit": account.acct_curr_cyc_debit,
        "acct_addr_zip": account.acct_addr_zip,
        "acct_group_id": account.acct_group_id,
        **customer_data,
    }


def update_account(db: Session, acct_id: int, data: dict) -> dict:
    """Update account details, ported from COACTUPC.

    This is the most complex update service. It:
    1. Reads the account with FOR UPDATE
    2. Validates each updatable field
    3. Detects changes (compares new vs old)
    4. Also updates customer fields if provided (via card_xref look-up)
    5. Commits only if changes were made

    Returns:
        dict with success message.

    Raises:
        RecordNotFoundError: If account not found.
        ValidationError: If field validation fails or no changes detected.
    """
    # Read account with FOR UPDATE lock (COACTUPC READ UPDATE)
    account = (
        db.query(Account)
        .filter(Account.acct_id == acct_id)
        .with_for_update()
        .first()
    )

    if not account:
        raise RecordNotFoundError(
            "Did not find this account in account master file"
        )

    changes_detected = False

    # --- Validate and apply account field updates ---

    # acct_active_status: must be Y or N
    if "acct_active_status" in data:
        is_valid, err = validate_yes_no(data["acct_active_status"])
        if not is_valid:
            raise ValidationError(
                f"Account Active Status {err}",
                field="acct_active_status",
            )
        new_val = data["acct_active_status"].upper()
        if new_val != account.acct_active_status:
            account.acct_active_status = new_val
            changes_detected = True

    # acct_credit_limit: validate as decimal
    if "acct_credit_limit" in data:
        is_valid, parsed, err = validate_signed_decimal(
            str(data["acct_credit_limit"])
        )
        if not is_valid:
            raise ValidationError(err, field="acct_credit_limit")
        if parsed != account.acct_credit_limit:
            account.acct_credit_limit = parsed
            changes_detected = True

    # acct_cash_credit_limit: validate as decimal
    if "acct_cash_credit_limit" in data:
        is_valid, parsed, err = validate_signed_decimal(
            str(data["acct_cash_credit_limit"])
        )
        if not is_valid:
            raise ValidationError(err, field="acct_cash_credit_limit")
        if parsed != account.acct_cash_credit_limit:
            account.acct_cash_credit_limit = parsed
            changes_detected = True

    # acct_curr_bal: validate as decimal
    if "acct_curr_bal" in data:
        is_valid, parsed, err = validate_signed_decimal(
            str(data["acct_curr_bal"])
        )
        if not is_valid:
            raise ValidationError(err, field="acct_curr_bal")
        if parsed != account.acct_curr_bal:
            account.acct_curr_bal = parsed
            changes_detected = True

    # acct_curr_cyc_credit: validate as decimal
    if "acct_curr_cyc_credit" in data:
        is_valid, parsed, err = validate_signed_decimal(
            str(data["acct_curr_cyc_credit"])
        )
        if not is_valid:
            raise ValidationError(err, field="acct_curr_cyc_credit")
        if parsed != account.acct_curr_cyc_credit:
            account.acct_curr_cyc_credit = parsed
            changes_detected = True

    # acct_curr_cyc_debit: validate as decimal
    if "acct_curr_cyc_debit" in data:
        is_valid, parsed, err = validate_signed_decimal(
            str(data["acct_curr_cyc_debit"])
        )
        if not is_valid:
            raise ValidationError(err, field="acct_curr_cyc_debit")
        if parsed != account.acct_curr_cyc_debit:
            account.acct_curr_cyc_debit = parsed
            changes_detected = True

    # Date fields: validate via validate_date_ccyymmdd
    date_fields = ["acct_open_date", "acct_expiration_date", "acct_reissue_date"]
    for field_name in date_fields:
        if field_name in data:
            value = data[field_name]
            if value and str(value).strip():
                is_valid, err = validate_date_ccyymmdd(str(value))
                if not is_valid:
                    raise ValidationError(err, field=field_name)
            current_val = getattr(account, field_name)
            if value != current_val:
                setattr(account, field_name, value)
                changes_detected = True

    # acct_addr_zip
    if "acct_addr_zip" in data:
        if data["acct_addr_zip"] != account.acct_addr_zip:
            account.acct_addr_zip = data["acct_addr_zip"]
            changes_detected = True

    # acct_group_id
    if "acct_group_id" in data:
        if data["acct_group_id"] != account.acct_group_id:
            account.acct_group_id = data["acct_group_id"]
            changes_detected = True

    # --- Update customer fields if provided (via card_xref look-up) ---
    customer_fields = [
        "cust_first_name",
        "cust_middle_name",
        "cust_last_name",
        "cust_addr_line_1",
        "cust_addr_line_2",
        "cust_addr_line_3",
        "cust_addr_state_cd",
        "cust_addr_country_cd",
        "cust_addr_zip",
        "cust_phone_num_1",
        "cust_phone_num_2",
        "cust_ssn",
        "cust_govt_issued_id",
        "cust_dob_yyyymmdd",
        "cust_eft_account_id",
        "cust_pri_card_holder_ind",
        "cust_fico_credit_score",
    ]

    has_customer_updates = any(f in data for f in customer_fields)

    if has_customer_updates:
        xref = (
            db.query(CardXref)
            .filter(CardXref.xref_acct_id == acct_id)
            .first()
        )
        if xref:
            customer = (
                db.query(Customer)
                .filter(Customer.cust_id == xref.xref_cust_id)
                .with_for_update()
                .first()
            )
            if customer:
                # Validate DOB date if provided
                if "cust_dob_yyyymmdd" in data:
                    dob_val = data["cust_dob_yyyymmdd"]
                    if dob_val and str(dob_val).strip():
                        is_valid, err = validate_date_ccyymmdd(str(dob_val))
                        if not is_valid:
                            raise ValidationError(
                                err, field="cust_dob_yyyymmdd"
                            )

                for field_name in customer_fields:
                    if field_name in data:
                        current_val = getattr(customer, field_name)
                        new_val = data[field_name]
                        if new_val != current_val:
                            setattr(customer, field_name, new_val)
                            changes_detected = True

    if not changes_detected:
        raise ValidationError(
            "No change detected with respect to values fetched"
        )

    db.commit()

    return {"message": "Changes committed"}
