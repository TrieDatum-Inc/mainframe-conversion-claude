"""User management service ported from COUSR00C, COUSR01C, COUSR02C, COUSR03C.

COUSR00C: Browse users via STARTBR/READNEXT on USRSEC file.
COUSR01C: Add a new user record to the USRSEC file.
COUSR02C: View and update an existing user record.
COUSR03C: Delete a user record from the USRSEC file.
"""

from sqlalchemy.orm import Session

from app.models.user import User
from app.exceptions import (
    DuplicateRecordError,
    RecordNotFoundError,
    ValidationError,
)


def list_users(db: Session, page: int = 1, page_size: int = 10) -> dict:
    """Paginated browse of users, ported from COUSR00C STARTBR/READNEXT.

    Orders by usr_id to match VSAM KSDS key ordering.

    Returns:
        PaginatedResponse-compatible dict with items, total_count, has_next_page.
    """
    total_count = db.query(User).count()

    offset = (page - 1) * page_size
    users = (
        db.query(User)
        .order_by(User.usr_id)
        .offset(offset)
        .limit(page_size)
        .all()
    )

    has_next_page = (offset + page_size) < total_count

    return {
        "items": [
            {
                "usr_id": u.usr_id,
                "usr_fname": u.usr_fname,
                "usr_lname": u.usr_lname,
                "usr_type": u.usr_type,
            }
            for u in users
        ],
        "page": page,
        "page_size": page_size,
        "total_count": total_count,
        "has_next_page": has_next_page,
    }


def add_user(db: Session, data: dict) -> dict:
    """Add a new user record, ported from COUSR01C.

    Validates all required fields and checks for duplicate user IDs
    before writing the record.

    Returns:
        dict with success message.
    """
    # Validate all fields not empty (COUSR01C field-level validation)
    required_fields = {
        "usr_fname": "First Name",
        "usr_lname": "Last Name",
        "usr_id": "User ID",
        "usr_pwd": "Password",
        "usr_type": "User Type",
    }
    for field, label in required_fields.items():
        value = data.get(field, "")
        if not value or str(value).strip() == "":
            raise ValidationError(f"{label} can NOT be empty", field=field)

    # Validate user type is 'A' or 'U'
    usr_type = data["usr_type"].upper()
    if usr_type not in ("A", "U"):
        raise ValidationError(
            "User Type must be A (Admin) or U (User)", field="usr_type"
        )

    # Check for duplicate (COUSR01C READ check)
    usr_id = data["usr_id"].upper()
    existing = db.query(User).filter(User.usr_id == usr_id).first()
    if existing:
        raise DuplicateRecordError("User ID already exist")

    # Write to database
    new_user = User(
        usr_id=usr_id,
        usr_fname=data["usr_fname"].strip(),
        usr_lname=data["usr_lname"].strip(),
        usr_pwd=data["usr_pwd"],
        usr_type=usr_type,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": f"User {usr_id} has been added ..."}


def get_user(db: Session, usr_id: str) -> dict:
    """Get a single user record, ported from COUSR02C PROCESS-ENTER-KEY.

    Returns:
        dict with all user fields.

    Raises:
        RecordNotFoundError: If user not found.
    """
    user = db.query(User).filter(User.usr_id == usr_id.upper()).first()

    if not user:
        raise RecordNotFoundError("User ID NOT found")

    return {
        "usr_id": user.usr_id,
        "usr_fname": user.usr_fname,
        "usr_lname": user.usr_lname,
        "usr_pwd": user.usr_pwd,
        "usr_type": user.usr_type,
    }


def update_user(db: Session, usr_id: str, data: dict) -> dict:
    """Update an existing user record, ported from COUSR02C.

    Performs change detection -- if no fields were actually modified,
    returns an error message matching the COBOL program behavior.

    Returns:
        dict with success message.
    """
    user = db.query(User).filter(User.usr_id == usr_id.upper()).first()

    if not user:
        raise RecordNotFoundError("User ID NOT found")

    # Change detection logic (COUSR02C compares each field)
    changes_detected = False

    if "usr_fname" in data and data["usr_fname"].strip() != user.usr_fname:
        user.usr_fname = data["usr_fname"].strip()
        changes_detected = True

    if "usr_lname" in data and data["usr_lname"].strip() != user.usr_lname:
        user.usr_lname = data["usr_lname"].strip()
        changes_detected = True

    if "usr_pwd" in data and data["usr_pwd"] != user.usr_pwd:
        user.usr_pwd = data["usr_pwd"]
        changes_detected = True

    if "usr_type" in data:
        new_type = data["usr_type"].upper()
        if new_type not in ("A", "U"):
            raise ValidationError(
                "User Type must be A (Admin) or U (User)", field="usr_type"
            )
        if new_type != user.usr_type:
            user.usr_type = new_type
            changes_detected = True

    if not changes_detected:
        raise ValidationError("Please modify to update")

    db.commit()
    db.refresh(user)

    return {"message": f"User {usr_id.upper()} has been updated ..."}


def delete_user(db: Session, usr_id: str) -> dict:
    """Delete a user record, ported from COUSR03C.

    Returns:
        dict with success message.

    Raises:
        RecordNotFoundError: If user not found.
    """
    user = db.query(User).filter(User.usr_id == usr_id.upper()).first()

    if not user:
        raise RecordNotFoundError("User ID NOT found")

    db.delete(user)
    db.commit()

    return {"message": f"User {usr_id.upper()} has been deleted"}
