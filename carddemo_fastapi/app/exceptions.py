"""Custom exception classes and FastAPI exception handlers.

Error messages are preserved verbatim from the original COBOL programs
to maintain functional equivalence.
"""

from fastapi import Request
from fastapi.responses import JSONResponse


class RecordNotFoundError(Exception):
    """Raised when a requested record does not exist in the database."""

    def __init__(self, message: str = "Record not found"):
        self.message = message
        super().__init__(self.message)


class DuplicateRecordError(Exception):
    """Raised when attempting to create a record that already exists."""

    def __init__(self, message: str = "Record already exists"):
        self.message = message
        super().__init__(self.message)


class ValidationError(Exception):
    """Raised when input validation fails.

    Preserves the exact error messages from COBOL programs.
    """

    def __init__(self, message: str, field: str | None = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        self.message = message
        super().__init__(self.message)


class AuthorizationError(Exception):
    """Raised when user lacks permission for an action."""

    def __init__(self, message: str = "No access - Admin Only option"):
        self.message = message
        super().__init__(self.message)


class DatabaseError(Exception):
    """Raised when a database operation fails unexpectedly."""

    def __init__(self, message: str = "Database operation failed"):
        self.message = message
        super().__init__(self.message)


# --- FastAPI Exception Handlers ---

async def record_not_found_handler(request: Request, exc: RecordNotFoundError):
    return JSONResponse(status_code=404, content={"error_message": exc.message})


async def duplicate_record_handler(request: Request, exc: DuplicateRecordError):
    return JSONResponse(status_code=409, content={"error_message": exc.message})


async def validation_error_handler(request: Request, exc: ValidationError):
    content = {"error_message": exc.message}
    if exc.field:
        content["field"] = exc.field
    return JSONResponse(status_code=422, content=content)


async def authentication_error_handler(request: Request, exc: AuthenticationError):
    return JSONResponse(status_code=401, content={"error_message": exc.message})


async def authorization_error_handler(request: Request, exc: AuthorizationError):
    return JSONResponse(status_code=403, content={"error_message": exc.message})


async def database_error_handler(request: Request, exc: DatabaseError):
    return JSONResponse(status_code=500, content={"error_message": exc.message})
