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
