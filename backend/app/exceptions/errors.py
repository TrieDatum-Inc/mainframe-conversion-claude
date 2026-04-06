"""
Custom exception classes for the CardDemo application.

COBOL origin: Maps CICS RESP codes and ABEND conditions to typed Python exceptions.
These exceptions are caught by global handlers in handlers.py and converted
to structured HTTP responses with consistent error_code/message format.

COBOL → Exception mapping:
    RESP=DFHRESP(NOTFND) (13)    → NotFoundError → HTTP 404
    RESP=DFHRESP(DUPKEY) (16)    → DuplicateResourceError → HTTP 409
    RESP=DFHRESP(DUPREC) (17)    → DuplicateResourceError → HTTP 409
    Password mismatch             → InvalidCredentialsError → HTTP 401
    CDEMO-USRTYP-ADMIN check fail → PermissionDeniedError → HTTP 403
    WS-ERR-FLG-ON validation      → ValidationError → HTTP 422
    CCUP-OLD-DETAILS mismatch     → OptimisticLockError → HTTP 409
    WS-DATACHANGED-FLAG = 'N'     → NoChangesDetectedError → HTTP 422
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
    """

    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(
            error_code=f"{resource.upper()}_NOT_FOUND",
            message=f"{resource} not found: {identifier}",
        )


class DuplicateResourceError(CardDemoException):
    """
    Duplicate key on write.

    COBOL: RESP=DFHRESP(DUPKEY) or DFHRESP(DUPREC) from CICS WRITE.
    """

    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(
            error_code=f"{resource.upper()}_ALREADY_EXISTS",
            message=f"{resource} already exists: {identifier}",
        )


class InvalidCredentialsError(CardDemoException):
    """
    Invalid user ID or password.

    COBOL: RESP=NOTFND or password mismatch in COSGN00C PROCESS-ENTER-KEY.
    Uniform message prevents user enumeration.
    """

    def __init__(self) -> None:
        super().__init__(
            error_code="INVALID_CREDENTIALS",
            message="Invalid User ID or Password",
        )


class PermissionDeniedError(CardDemoException):
    """
    Insufficient privileges.

    COBOL: CDEMO-USRTYP-ADMIN check.
    """

    def __init__(self) -> None:
        super().__init__(
            error_code="ADMIN_REQUIRED",
            message="This function requires administrator privileges",
        )


class ValidationError(CardDemoException):
    """
    Business rule validation failure.

    COBOL: WS-ERR-FLG-ON paths.
    """

    def __init__(self, error_code: str, message: str) -> None:
        super().__init__(error_code=error_code, message=message)


class OptimisticLockError(CardDemoException):
    """
    Record was modified since last fetch.

    COBOL: CCUP-OLD-DETAILS snapshot comparison in COCRDUPC.
    Also used for COACTUPC account update conflict detection.
    """

    def __init__(self, resource: str) -> None:
        super().__init__(
            error_code="OPTIMISTIC_LOCK_ERROR",
            message=(
                f"{resource} was modified by another process since you last loaded it. "
                "Please reload and try again."
            ),
        )


class NoChangesDetectedError(CardDemoException):
    """
    No fields were changed in an update request.

    COBOL: COACTUPC WS-DATACHANGED-FLAG = 'N' path.
    """

    def __init__(self, resource: str) -> None:
        super().__init__(
            error_code="NO_CHANGES_DETECTED",
            message=f"No changes were detected for {resource}.",
        )
