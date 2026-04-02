"""
Custom exception classes mapping COBOL/CICS error conditions to HTTP semantics.

Maps:
  CICS RESP=13 (NOTFND)          -> ResourceNotFoundError -> HTTP 404
  CICS RESP=70 (DUPKEY)          -> DuplicateKeyError     -> HTTP 409
  CICS RESP=45 (LOCKED)          -> RecordLockedError     -> HTTP 409
  Authentication failure          -> AuthenticationError  -> HTTP 401
  Authorization failure           -> AuthorizationError   -> HTTP 403
  Validation errors               -> ValidationError      -> HTTP 422
  CICS ABEND / unexpected error   -> SystemError          -> HTTP 500
"""

from fastapi import HTTPException, status


class CardDemoBaseError(Exception):
    """Base exception for all CardDemo business logic errors."""

    def __init__(self, message: str, error_code: str = "CDERR000") -> None:
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class ResourceNotFoundError(CardDemoBaseError):
    """
    Maps CICS RESP=13 (DFHRESP NOTFND).

    Raised when:
    - VSAM READ returns NOTFND (account, customer, card, transaction not found)
    - User not found in USRSEC (COSGN00C error: 'User not found. Try again ...')
    """

    def __init__(self, resource: str, key: str) -> None:
        super().__init__(
            message=f"{resource} with key '{key}' not found.",
            error_code="CDERR013",
        )
        self.resource = resource
        self.key = key


class DuplicateKeyError(CardDemoBaseError):
    """
    Maps CICS RESP=70 (DFHRESP DUPREC) or DB2 SQLCODE=-803.

    Raised when:
    - VSAM WRITE finds duplicate key (COUSR01C duplicate user ID)
    - DB2 INSERT duplicate on TRANSACTION_TYPE (COTRTUPC)
    """

    def __init__(self, resource: str, key: str) -> None:
        super().__init__(
            message=f"{resource} with key '{key}' already exists.",
            error_code="CDERR070",
        )
        self.resource = resource
        self.key = key


class RecordLockedError(CardDemoBaseError):
    """
    Maps CICS RESP=45 (DFHRESP LOCKED).

    Raised when:
    - COACTUPC optimistic concurrency lock detected (ACUP-CHANGES-OKAYED-LOCK-ERROR state)
    - COCRDUPC concurrent modification detected
    """

    def __init__(self, resource: str, key: str) -> None:
        super().__init__(
            message=f"{resource} with key '{key}' is locked by another user.",
            error_code="CDERR045",
        )
        self.resource = resource
        self.key = key


class AuthenticationError(CardDemoBaseError):
    """
    Maps COSGN00C authentication failures.

    Raised when:
    - Wrong password ('Wrong Password. Try again ...')
    - User not found
    - JWT token invalid/expired
    """

    def __init__(self, message: str = "Authentication failed.") -> None:
        super().__init__(message=message, error_code="CDERR401")


class AuthorizationError(CardDemoBaseError):
    """
    Maps user type authorization checks.

    Raised when:
    - Non-admin user attempts admin-only operation
    - CDEMO-USER-TYPE='U' but admin function requested
    """

    def __init__(self, message: str = "Insufficient privileges.") -> None:
        super().__init__(message=message, error_code="CDERR403")


class BusinessValidationError(CardDemoBaseError):
    """
    Maps COBOL field-level validation errors.

    Raised when:
    - COACTUPC 35+ field validations fail (invalid dates, phone formats, state codes)
    - COTRN02C transaction add validation fails
    - COBIL00C bill payment amount validation fails
    """

    def __init__(self, message: str, field: str = "") -> None:
        super().__init__(message=message, error_code="CDERR422")
        self.field = field


class FileIOError(CardDemoBaseError):
    """
    Maps CICS VSAM OTHER response code (unexpected I/O error).

    Raised when:
    - WS-FILE-ERROR-MESSAGE formatted for any RESP not 0 or 13
    - 'Unable to verify the User ...' in COSGN00C
    """

    def __init__(self, operation: str, filename: str, resp: int = 0) -> None:
        super().__init__(
            message=f"File Error: {operation} on {filename} returned RESP {resp}",
            error_code="CDERR500",
        )
        self.operation = operation
        self.filename = filename
        self.resp = resp


class AccountInactiveError(CardDemoBaseError):
    """Account is not active - cannot perform operations on it."""

    def __init__(self, account_id: int) -> None:
        super().__init__(
            message=f"Account {account_id} is not active.",
            error_code="CDBIZ001",
        )


class InsufficientCreditError(CardDemoBaseError):
    """
    Maps COPAUA0C authorization decline decision.
    Available credit < requested amount.
    """

    def __init__(self, available: float, requested: float) -> None:
        super().__init__(
            message=(
                f"Insufficient credit. Available: {available:.2f}, "
                f"Requested: {requested:.2f}"
            ),
            error_code="CDBIZ002",
        )


def not_found_http(resource: str, key: str) -> HTTPException:
    """Convenience function to raise HTTP 404."""
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"error_code": "CDERR013", "message": f"{resource} '{key}' not found."},
    )


def conflict_http(resource: str, key: str) -> HTTPException:
    """Convenience function to raise HTTP 409."""
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "error_code": "CDERR070",
            "message": f"{resource} '{key}' already exists.",
        },
    )


def unauthorized_http(message: str = "Authentication required.") -> HTTPException:
    """Convenience function to raise HTTP 401."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error_code": "CDERR401", "message": message},
        headers={"WWW-Authenticate": "Bearer"},
    )


def forbidden_http(message: str = "Insufficient privileges.") -> HTTPException:
    """Convenience function to raise HTTP 403."""
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"error_code": "CDERR403", "message": message},
    )
