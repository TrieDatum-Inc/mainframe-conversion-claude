"""Card management service ported from COCRDLIC, COCRDSLC, COCRDUPC.

COCRDLIC: List/browse cards with optional account filter via CARDAIX
          alternate index.  BMS page size = 7.
COCRDSLC: View card details by card number and/or account ID.
COCRDUPC: Update card fields with field-level validation (name, status,
          expiry month/year) and change detection.
"""

from sqlalchemy.orm import Session

from app.models.card import Card
from app.exceptions import RecordNotFoundError, ValidationError
from app.services.validation import (
    validate_alpha_only,
    validate_card_expiry_month,
    validate_card_expiry_year,
    validate_yes_no,
)


def list_cards(
    db: Session,
    acct_id: int | None = None,
    page: int = 1,
    page_size: int = 7,
) -> dict:
    """Paginated card list, ported from COCRDLIC.

    If acct_id is provided, filters by card_acct_id (like CARDAIX
    alternate index browse).  Page size 7 matches the BMS screen layout.

    Returns:
        PaginatedResponse-compatible dict.
    """
    query = db.query(Card)

    if acct_id is not None:
        query = query.filter(Card.card_acct_id == acct_id)

    total_count = query.count()

    offset = (page - 1) * page_size
    cards = (
        query.order_by(Card.card_num)
        .offset(offset)
        .limit(page_size)
        .all()
    )

    has_next_page = (offset + page_size) < total_count

    return {
        "items": [
            {
                "card_num": c.card_num,
                "card_acct_id": c.card_acct_id,
                "card_active_status": c.card_active_status,
                "card_expiration_date": c.card_expiration_date,
            }
            for c in cards
        ],
        "page": page,
        "page_size": page_size,
        "total_count": total_count,
        "has_next_page": has_next_page,
    }


def get_card_detail(
    db: Session,
    card_num: str,
    acct_id: int | None = None,
) -> dict:
    """Get card details, ported from COCRDSLC.

    If acct_id is provided, queries by composite key (card_num + card_acct_id).
    Otherwise queries by card_num only.

    Returns:
        dict with all card fields.

    Raises:
        RecordNotFoundError: If card not found.
    """
    query = db.query(Card).filter(Card.card_num == card_num)

    if acct_id is not None:
        query = query.filter(Card.card_acct_id == acct_id)

    card = query.first()

    if not card:
        raise RecordNotFoundError(
            "Did not find cards for this search condition"
        )

    return {
        "card_num": card.card_num,
        "card_acct_id": card.card_acct_id,
        "card_cvv_cd": card.card_cvv_cd,
        "card_embossed_name": card.card_embossed_name,
        "card_expiration_date": card.card_expiration_date,
        "card_active_status": card.card_active_status,
    }


def update_card(db: Session, card_num: str, acct_id: int, data: dict) -> dict:
    """Update card details, ported from COCRDUPC.

    Validates:
    - card_embossed_name: alpha + spaces only
    - card_active_status: Y or N
    - Expiry month: 1-12
    - Expiry year: 1950-2099
    - Change detection: if no changes, returns error

    Returns:
        dict with success message.

    Raises:
        RecordNotFoundError: If card not found.
        ValidationError: If validation fails or no changes detected.
    """
    # Read card with FOR UPDATE lock
    card = (
        db.query(Card)
        .filter(Card.card_num == card_num, Card.card_acct_id == acct_id)
        .with_for_update()
        .first()
    )

    if not card:
        raise RecordNotFoundError(
            "Did not find cards for this search condition"
        )

    changes_detected = False

    # Validate and apply card_embossed_name
    if "card_embossed_name" in data:
        is_valid, err = validate_alpha_only(data["card_embossed_name"])
        if not is_valid:
            raise ValidationError(
                "Card name can only contain alphabets and spaces",
                field="card_embossed_name",
            )
        if data["card_embossed_name"] != card.card_embossed_name:
            card.card_embossed_name = data["card_embossed_name"]
            changes_detected = True

    # Validate and apply card_active_status
    if "card_active_status" in data:
        new_status = data["card_active_status"].upper()
        is_valid, err = validate_yes_no(new_status)
        if not is_valid:
            raise ValidationError(
                "Card Active Status must be Y or N",
                field="card_active_status",
            )
        if new_status != card.card_active_status:
            card.card_active_status = new_status
            changes_detected = True

    # Validate and apply expiry month (embedded in card_expiration_date)
    if "card_expiry_month" in data:
        is_valid, err = validate_card_expiry_month(str(data["card_expiry_month"]))
        if not is_valid:
            raise ValidationError(
                "Card expiry month must be between 1 and 12",
                field="card_expiry_month",
            )

    # Validate and apply expiry year
    if "card_expiry_year" in data:
        is_valid, err = validate_card_expiry_year(str(data["card_expiry_year"]))
        if not is_valid:
            raise ValidationError(
                "Invalid card expiry year",
                field="card_expiry_year",
            )

    # Build new expiration date if month or year changed
    if "card_expiry_month" in data or "card_expiry_year" in data:
        # Parse existing expiration date components
        existing_date = card.card_expiration_date or ""
        existing_parts = existing_date.split("-") if "-" in existing_date else []

        if len(existing_parts) == 3:
            existing_year = existing_parts[0]
            existing_month = existing_parts[1]
            existing_day = existing_parts[2]
        else:
            existing_year = existing_date[0:4] if len(existing_date) >= 4 else "2000"
            existing_month = existing_date[4:6] if len(existing_date) >= 6 else "01"
            existing_day = existing_date[6:8] if len(existing_date) >= 8 else "01"

        new_month = str(data.get("card_expiry_month", existing_month)).zfill(2)
        new_year = str(data.get("card_expiry_year", existing_year)).zfill(4)
        new_exp_date = f"{new_year}-{new_month}-{existing_day}"

        if new_exp_date != card.card_expiration_date:
            card.card_expiration_date = new_exp_date
            changes_detected = True

    # Direct card_expiration_date override
    if "card_expiration_date" in data:
        if data["card_expiration_date"] != card.card_expiration_date:
            card.card_expiration_date = data["card_expiration_date"]
            changes_detected = True

    if not changes_detected:
        raise ValidationError(
            "No change detected with respect to values fetched"
        )

    try:
        db.commit()
        db.refresh(card)
        return {"message": "Changes committed"}
    except Exception:
        db.rollback()
        raise ValidationError("Changes unsuccessful. Please try again")
