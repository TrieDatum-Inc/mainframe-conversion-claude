"""
Custom exception classes for the CardDemo backend.

COBOL origin: Maps CICS RESP codes and program-level error conditions
to Python exceptions that produce structured HTTP error responses.

RESP code → HTTP status mapping:
  RESP=NOTFND (CICS 13)    → 404 Not Found      → UserNotFoundError
  RESP=DUPKEY/DUPREC       → 409 Conflict        → UserAlreadyExistsError
  Blank field validation   → 422 Unprocessable   → ValidationError (Pydantic)
  No fields modified       → 422 Unprocessable   → NoChangesDetectedError
  EIBCALEN=0 / no token    → 401 Unauthorized    → raised by auth dependency
  Non-admin access         → 403 Forbidden       → raised by require_admin dependency
"""

from fastapi import HTTPException, status


class UserNotFoundError(HTTPException):
    """
    COBOL origin: COUSR02C/COUSR03C READ-USER-SEC-FILE RESP=NOTFND.
    Message: 'User ID NOT found in the system'
    """

    def __init__(self, user_id: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "USER_NOT_FOUND",
                "message": f"User ID NOT found in the system: {user_id}",
                "details": [],
            },
        )


class UserAlreadyExistsError(HTTPException):
    """
    COBOL origin: COUSR01C WRITE-USER-SEC-FILE RESP=DUPKEY or RESP=DUPREC.
    Message: 'User ID already exist...'
    """

    def __init__(self, user_id: str) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_code": "USER_ALREADY_EXISTS",
                "message": f"User ID already exist: {user_id}",
                "details": [],
            },
        )


class NoChangesDetectedError(HTTPException):
    """
    COBOL origin: COUSR02C UPDATE-USER-INFO — USR-MODIFIED-NO path.
    Message: 'Please modify to update...'
    Color: DFHRED (red message bar)
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "NO_CHANGES_DETECTED",
                "message": "Please modify at least one field to update",
                "details": [],
            },
        )


class AdminRequiredError(HTTPException):
    """
    Raised when a non-admin user attempts to access an admin-only endpoint.

    COBOL origin: COUSR00C, COUSR01C, COUSR02C, COUSR03C are all admin-only,
    reachable only from COADM01C. Non-admin users cannot reach these programs
    via the CICS menu.
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "ADMIN_REQUIRED",
                "message": "This operation requires administrator privileges",
                "details": [],
            },
        )


class UnauthorizedError(HTTPException):
    """
    COBOL origin: EIBCALEN=0 check — unauthenticated session returns to COSGN00C.
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "UNAUTHORIZED",
                "message": "Authentication required",
                "details": [],
            },
            headers={"WWW-Authenticate": "Bearer"},
        )


# ---------------------------------------------------------------------------
# Transaction Type errors (COTRTLIC / COTRTUPC)
# ---------------------------------------------------------------------------


class TransactionTypeNotFoundError(HTTPException):
    """
    COBOL origin: COTRTUPC 9100-GET-TRANSACTION-TYPE → SQLCODE +100 (NOT FOUND).
    Message: 'Record not found. Deleted by others ?...' (COTRTLIC 9200-UPDATE-RECORD)
    """

    def __init__(self, type_code: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "TRANSACTION_TYPE_NOT_FOUND",
                "message": f"Transaction type '{type_code}' not found in the system",
                "details": [],
            },
        )


class TransactionTypeAlreadyExistsError(HTTPException):
    """
    COBOL origin: COTRTUPC 9700-INSERT-RECORD implicit duplicate check.
    Detected via SELECT before INSERT; returns 409 Conflict.
    """

    def __init__(self, type_code: str) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_code": "TRANSACTION_TYPE_ALREADY_EXISTS",
                "message": f"Transaction type '{type_code}' already exists",
                "details": [],
            },
        )


class TransactionTypeHasDependentsError(HTTPException):
    """
    COBOL origin: COTRTLIC 9300-DELETE-RECORD SQLCODE -532 (FK violation).
    Message: 'Please delete associated child records first:...'
    Raised when transactions reference this type_code.
    """

    def __init__(self, type_code: str) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_code": "TRANSACTION_TYPE_HAS_DEPENDENTS",
                "message": (
                    f"Transaction type '{type_code}' cannot be deleted. "
                    "Please delete associated transaction records first."
                ),
                "details": [],
            },
        )


class TransactionTypeOptimisticLockError(HTTPException):
    """
    Replaces COTRTLIC WS-DATACHANGED-FLAG and COTRTUPC 1205-COMPARE-OLD-NEW.
    Raised when the client's updated_at version does not match the server's current value,
    indicating another user modified the record between GET and PUT.
    """

    def __init__(self, type_code: str) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_code": "OPTIMISTIC_LOCK_CONFLICT",
                "message": (
                    f"Transaction type '{type_code}' was modified by another user. "
                    "Please refresh and try again."
                ),
                "details": [],
            },
        )


class TransactionTypeNoChangesError(HTTPException):
    """
    COBOL origin: COTRTLIC WS-MESG-NO-CHANGES-DETECTED.
    'No change detected with respect to database values.'
    Raised when the new description equals the current stored description.
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "NO_CHANGES_DETECTED",
                "message": "No change detected with respect to database values",
                "details": [],
            },
        )


# ---------------------------------------------------------------------------
# Account errors (COACTVWC / COACTUPC)
# ---------------------------------------------------------------------------


class AccountNotFoundError(HTTPException):
    """
    COBOL origin: COACTVWC/COACTUPC READ-ACCT-BY-ACCT-ID RESP=NOTFND.
    """

    def __init__(self, account_id: int) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "ACCOUNT_NOT_FOUND",
                "message": f"Account ID {account_id} not found in the system",
                "details": [],
            },
        )


class CustomerNotFoundError(HTTPException):
    """
    COBOL origin: COACTVWC READ-CUST-BY-CUST-ID RESP=NOTFND.
    """

    def __init__(self, account_id: int) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "CUSTOMER_NOT_FOUND",
                "message": f"No customer linked to account ID {account_id}",
                "details": [],
            },
        )


class AccountNoChangesDetectedError(HTTPException):
    """
    COBOL origin: COACTUPC WS-DATACHANGED-FLAG = 'N' path.
    Message: 'No changes detected. Nothing to update.'
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "NO_CHANGES_DETECTED",
                "message": "No changes detected. Nothing to update.",
                "details": [],
            },
        )


# ---------------------------------------------------------------------------
# Credit card errors (COCRDLIC / COCRDSLC / COCRDUPC)
# ---------------------------------------------------------------------------


class CardNotFoundError(HTTPException):
    """
    COBOL origin: COCRDSLC/COCRDUPC READ DATASET(CARDDAT) RESP=NOTFND.
    """

    def __init__(self, card_number: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "CARD_NOT_FOUND",
                "message": f"Credit card {card_number} not found in the system",
                "details": [],
            },
        )


class CardOptimisticLockError(HTTPException):
    """
    COBOL origin: COCRDUPC CCUP-OLD-DETAILS snapshot mismatch.
    'Record changed by another user.' → SYNCPOINT ROLLBACK → HTTP 409.
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_code": "OPTIMISTIC_LOCK_CONFLICT",
                "message": (
                    "Credit card record was modified by another user. "
                    "Please refresh and try again."
                ),
                "details": [],
            },
        )


# ---------------------------------------------------------------------------
# Transaction errors (COTRN00C / COTRN01C / COTRN02C)
# ---------------------------------------------------------------------------


class TransactionNotFoundError(HTTPException):
    """
    COBOL origin: COTRN01C PROCESS-ENTER-KEY READ TRANSACT RESP=NOTFND.
    Message: 'Transaction not found'
    """

    def __init__(self, transaction_id: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "TRANSACTION_NOT_FOUND",
                "message": f"Transaction ID {transaction_id} not found in the system",
                "details": [],
            },
        )


# ---------------------------------------------------------------------------
# Billing errors (COBIL00C)
# ---------------------------------------------------------------------------


class NothingToPayError(HTTPException):
    """
    COBOL origin: COBIL00C PROCESS-ENTER-KEY:
    IF ACCT-CURR-BAL <= 0: 'You have nothing to pay...' cursor to ACTIDINI
    """

    def __init__(self, account_id: int) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "NOTHING_TO_PAY",
                "message": f"Account {account_id} has nothing to pay (balance is zero or negative)",
                "details": [],
            },
        )


# ---------------------------------------------------------------------------
# Report errors (CORPT00C)
# ---------------------------------------------------------------------------


class ReportRequestNotFoundError(HTTPException):
    """
    No COBOL equivalent — CORPT00C had no status-check capability.
    New error added for the report status polling feature.
    """

    def __init__(self, request_id: int) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "REPORT_REQUEST_NOT_FOUND",
                "message": f"Report request {request_id} not found",
                "details": [],
            },
        )


# ---------------------------------------------------------------------------
# Generic validation error
# ---------------------------------------------------------------------------


class ValidationError(HTTPException):
    """Generic field validation error."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": message,
                "details": [{"field": field, "message": message}],
            },
        )
