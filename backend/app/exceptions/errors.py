"""
Custom exception classes for the CardDemo application.

COBOL origin: Maps CICS RESP codes and ABEND conditions to typed Python exceptions.
These exceptions are caught by global handlers in handlers.py and converted
to structured HTTP responses with consistent error_code/message format.

COBOL → Exception mapping:
    RESP=DFHRESP(NOTFND) (13)     → NotFoundError → HTTP 404
    RESP=DFHRESP(DUPKEY) (16)     → DuplicateResourceError → HTTP 409
    RESP=DFHRESP(DUPREC) (17)     → DuplicateResourceError → HTTP 409
    Password mismatch              → InvalidCredentialsError → HTTP 401
    CDEMO-USRTYP-ADMIN check fail → PermissionDeniedError → HTTP 403
    Field validation failure       → ValidationError → HTTP 422
"""


class CardDemoException(Exception):
    """Base exception for all CardDemo application errors."""

    def __init__(self, error_code: str, message: str) -> None:
        self.error_code = error_code
        self.message = message
        super().__init__(message)


class NotFoundError(CardDemoException):
    """
    Resource not found.

    COBOL: RESP=DFHRESP(NOTFND) from CICS READ/DELETE.
    Examples: user not found, account not found, card not found.
    """

    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(
            error_code=f"{resource.upper()}_NOT_FOUND",
            message=f"{resource} ID NOT found in the system: {identifier}",
        )


class DuplicateResourceError(CardDemoException):
    """
    Duplicate key on write.

    COBOL: RESP=DFHRESP(DUPKEY) or DFHRESP(DUPREC) from CICS WRITE.
    Example: user ID already exists when creating a new user.
    """

    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(
            error_code=f"{resource.upper()}_ALREADY_EXISTS",
            message=f"{resource} ID already exist: {identifier}",
        )


class InvalidCredentialsError(CardDemoException):
    """
    Invalid user ID or password.

    COBOL: RESP=NOTFND or password mismatch in COSGN00C PROCESS-ENTER-KEY.
    Uses uniform message to prevent user enumeration (preserves COBOL behavior).
    """

    def __init__(self) -> None:
        super().__init__(
            error_code="INVALID_CREDENTIALS",
            message="Invalid User ID or Password",
        )


class PermissionDeniedError(CardDemoException):
    """
    Insufficient privileges for the requested operation.

    COBOL: CDEMO-USRTYP-ADMIN check — regular users cannot access admin screens.
    """

    def __init__(self) -> None:
        super().__init__(
            error_code="ADMIN_REQUIRED",
            message="This function requires administrator privileges",
        )


class ValidationError(CardDemoException):
    """
    Business rule validation failure.

    COBOL: WS-ERR-FLG-ON paths — field blank checks, cross-field validations.
    """

    def __init__(self, error_code: str, message: str) -> None:
        super().__init__(error_code=error_code, message=message)


# =============================================================================
# Transaction Type error classes — COTRTLIC / COTRTUPC
# =============================================================================


class TransactionTypeNotFoundError(CardDemoException):
    """
    Transaction type not found by type_code lookup.

    COBOL: COTRTLIC 9200-UPDATE-RECORD SQLCODE +100 (no rows returned).
            COTRTUPC TTUP-DETAILS-NOT-FOUND state (9000-READ-TRANTYPE returns empty).
    Maps to HTTP 404.
    """

    def __init__(self, type_code: str) -> None:
        super().__init__(
            error_code="TRANSACTION_TYPE_NOT_FOUND",
            message=f"Transaction type not found: {type_code}",
        )


class TransactionTypeAlreadyExistsError(CardDemoException):
    """
    Duplicate type_code on INSERT.

    COBOL: COTRTUPC 9700-INSERT-RECORD SQLCODE -803 (duplicate key).
    Maps to HTTP 409.
    """

    def __init__(self, type_code: str) -> None:
        super().__init__(
            error_code="TRANSACTION_TYPE_ALREADY_EXISTS",
            message=f"Transaction type already exists: {type_code}",
        )


class TransactionTypeHasDependentsError(CardDemoException):
    """
    Cannot delete a transaction type that is referenced by transactions.

    COBOL: COTRTUPC 9800-DELETE-PROCESSING SQLCODE -532 (referential integrity violation).
           COTRTLIC 9300-DELETE-RECORD FK violation.
    Maps to HTTP 409.
    """

    def __init__(self, type_code: str) -> None:
        super().__init__(
            error_code="TRANSACTION_TYPE_HAS_DEPENDENTS",
            message=(
                f"Transaction type '{type_code}' cannot be deleted "
                "because transactions reference it."
            ),
        )


class TransactionTypeOptimisticLockError(CardDemoException):
    """
    Optimistic lock conflict on update — record modified since last fetch.

    COBOL: COTRTLIC WS-DATACHANGED-FLAG — set when a concurrent user modified
           the same row between the browse and the update.
           COTRTUPC 1205-COMPARE-OLD-NEW — compares current DB row against the
           CCUP-OLD-DETAILS snapshot taken at TTUP-SHOW-DETAILS time.
    Maps to HTTP 409.
    """

    def __init__(self, type_code: str) -> None:
        super().__init__(
            error_code="OPTIMISTIC_LOCK_CONFLICT",
            message=(
                f"Transaction type '{type_code}' was modified by another user. "
                "Please reload and retry."
            ),
        )


class TransactionTypeNoChangesError(CardDemoException):
    """
    No-op update — submitted description equals current database value.

    COBOL: COTRTLIC WS-MESG-NO-CHANGES-DETECTED.
    Maps to HTTP 422 (Unprocessable Entity — valid request, but no action needed).
    """

    def __init__(self, type_code: str) -> None:
        super().__init__(
            error_code="NO_CHANGES_DETECTED",
            message=(
                f"No change detected with respect to database values "
                f"for transaction type '{type_code}'."
            ),
        )
