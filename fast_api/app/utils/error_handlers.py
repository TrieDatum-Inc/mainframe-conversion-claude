"""
Centralized error handling — maps CICS RESP codes to HTTP status codes.

CICS RESP code → HTTP status mapping (from HANDLE CONDITION blocks across all programs):
  RESP=0  (NORMAL)     → 200/201/204
  RESP=13 (NOTFND)     → 404 Not Found
  RESP=14 (DUPREC)     → 409 Conflict
  RESP=22 (LENGERR)    → 400 Bad Request
  RESP=27 (INVREQ)     → 400 Bad Request
  RESP=70 (NOTAUTH)    → 403 Forbidden
  RESP=other           → 500 Internal Server Error

References:
  COSGN00C: WHEN 13 → "User not found"
  COUSR01C/02C/03C: RESP checking for USRSEC file
  COACTVWC: RESP checking for ACCTDAT / CUSTDAT / CCXREF
"""
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


# ---------------------------------------------------------------------------
# Custom exception hierarchy
# ---------------------------------------------------------------------------

class CardDemoError(Exception):
    """Base exception for all CardDemo application errors."""

    def __init__(self, message: str, detail: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail or message


class RecordNotFoundError(CardDemoError):
    """
    CICS RESP=13 (NOTFND) equivalent.
    Raised when EXEC CICS READ returns NOTFND.
    """

    pass


class DuplicateRecordError(CardDemoError):
    """
    CICS RESP=14 (DUPREC) equivalent.
    Raised when EXEC CICS WRITE fails due to duplicate key.
    """

    pass


class AuthenticationError(CardDemoError):
    """
    Authentication failure — wrong password or user not found.
    From COSGN00C READ-USER-SEC-FILE paragraph.
    """

    pass


class AuthorizationError(CardDemoError):
    """
    CICS RESP=70 (NOTAUTH) equivalent.
    Admin-only operations attempted by regular user (COACTUPC group ID field).
    """

    pass


class ValidationError(CardDemoError):
    """
    Input validation failure.
    Maps to BMS screen error messages set in WS-MESSAGE across all programs.
    """

    pass


class FileIOError(CardDemoError):
    """
    Generic file I/O error for unexpected CICS RESP codes.
    Maps to WS-FILE-ERROR-MESSAGE construction in COACTVWC.
    """

    pass


# ---------------------------------------------------------------------------
# CICS RESP code → Exception mapper
# ---------------------------------------------------------------------------

CICS_RESP_MAP: dict[int, type[CardDemoError]] = {
    13: RecordNotFoundError,  # NOTFND
    14: DuplicateRecordError,  # DUPREC
    22: ValidationError,       # LENGERR
    27: ValidationError,       # INVREQ
    70: AuthorizationError,    # NOTAUTH
}


def raise_for_cics_resp(resp_cd: int, file_name: str, operation: str, key: str = "") -> None:
    """
    Raise appropriate Python exception based on CICS RESP code.

    Mirrors the EVALUATE WS-RESP-CD blocks found in every CICS program.

    Args:
        resp_cd: The CICS RESP code returned by the file operation.
        file_name: CICS file name (e.g., 'USRSEC', 'ACCTDAT').
        operation: Operation name ('READ', 'WRITE', 'REWRITE', 'DELETE').
        key: Record key for error message context.
    """
    if resp_cd == 0:
        return
    exc_class = CICS_RESP_MAP.get(resp_cd, FileIOError)
    msg = f"File Error: {operation} on {file_name} returned RESP {resp_cd}"
    if key:
        msg += f" key={key!r}"
    raise exc_class(msg)


# ---------------------------------------------------------------------------
# FastAPI exception handlers
# ---------------------------------------------------------------------------

async def record_not_found_handler(request: Request, exc: RecordNotFoundError) -> JSONResponse:
    """Maps RecordNotFoundError (CICS NOTFND) → HTTP 404."""
    return JSONResponse(status_code=404, content={"detail": exc.message})


async def duplicate_record_handler(request: Request, exc: DuplicateRecordError) -> JSONResponse:
    """Maps DuplicateRecordError (CICS DUPREC) → HTTP 409."""
    return JSONResponse(status_code=409, content={"detail": exc.message})


async def auth_error_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
    """Maps AuthenticationError → HTTP 401."""
    return JSONResponse(status_code=401, content={"detail": exc.message})


async def authz_error_handler(request: Request, exc: AuthorizationError) -> JSONResponse:
    """Maps AuthorizationError → HTTP 403."""
    return JSONResponse(status_code=403, content={"detail": exc.message})


async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Maps ValidationError → HTTP 422."""
    return JSONResponse(status_code=422, content={"detail": exc.message})


async def file_io_error_handler(request: Request, exc: FileIOError) -> JSONResponse:
    """Maps FileIOError (unexpected CICS RESP) → HTTP 500."""
    return JSONResponse(status_code=500, content={"detail": exc.message})


def register_exception_handlers(app) -> None:  # noqa: ANN001
    """Register all custom exception handlers with the FastAPI app."""
    app.add_exception_handler(RecordNotFoundError, record_not_found_handler)
    app.add_exception_handler(DuplicateRecordError, duplicate_record_handler)
    app.add_exception_handler(AuthenticationError, auth_error_handler)
    app.add_exception_handler(AuthorizationError, authz_error_handler)
    app.add_exception_handler(ValidationError, validation_error_handler)
    app.add_exception_handler(FileIOError, file_io_error_handler)
