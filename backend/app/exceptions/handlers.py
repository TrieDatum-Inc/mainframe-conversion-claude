"""
Global exception handlers — centralized error response formatting.

COBOL origin: Replaces scattered CICS ABEND handling, RESP code checking,
and WS-MESSAGE formatting spread across every COBOL program's error paths.
Provides a single consistent error response format for all error conditions.

Error response format:
    {"error_code": "...", "message": "...", "details": [...]}
"""

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.exceptions.errors import (
    CardDemoException,
    DuplicateResourceError,
    InvalidCredentialsError,
    NotFoundError,
    PermissionDeniedError,
    TransactionTypeAlreadyExistsError,
    TransactionTypeHasDependentsError,
    TransactionTypeNoChangesError,
    TransactionTypeNotFoundError,
    TransactionTypeOptimisticLockError,
)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all global exception handlers on the FastAPI application.

    Call this in create_app() after creating the FastAPI instance.
    """

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """
        Normalize FastAPI HTTPException detail into the standard error response format.

        When services raise HTTPException with detail={"error_code": ..., "message": ...},
        FastAPI would normally wrap it as {"detail": {...}}. This handler unwraps it
        into the flat ErrorResponse format for consistency.
        """
        if isinstance(exc.detail, dict) and "error_code" in exc.detail:
            content = {
                "error_code": exc.detail["error_code"],
                "message": exc.detail.get("message", str(exc.detail)),
                "details": exc.detail.get("details", []),
            }
        else:
            content = {
                "error_code": f"HTTP_{exc.status_code}",
                "message": str(exc.detail),
                "details": [],
            }
        headers = getattr(exc, "headers", None)
        return JSONResponse(
            status_code=exc.status_code,
            content=content,
            headers=headers,
        )

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        """
        Maps CICS RESP=DFHRESP(NOTFND) (13) → HTTP 404.
        """
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error_code": exc.error_code, "message": exc.message, "details": []},
        )

    @app.exception_handler(DuplicateResourceError)
    async def duplicate_handler(
        request: Request, exc: DuplicateResourceError
    ) -> JSONResponse:
        """
        Maps CICS RESP=DFHRESP(DUPKEY/DUPREC) → HTTP 409 Conflict.
        """
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"error_code": exc.error_code, "message": exc.message, "details": []},
        )

    @app.exception_handler(InvalidCredentialsError)
    async def invalid_credentials_handler(
        request: Request, exc: InvalidCredentialsError
    ) -> JSONResponse:
        """
        Maps password mismatch or user-not-found → HTTP 401 Unauthorized.
        """
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error_code": exc.error_code, "message": exc.message, "details": []},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(PermissionDeniedError)
    async def permission_denied_handler(
        request: Request, exc: PermissionDeniedError
    ) -> JSONResponse:
        """
        Maps CDEMO-USRTYP-ADMIN check failure → HTTP 403 Forbidden.
        """
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"error_code": exc.error_code, "message": exc.message, "details": []},
        )

    # -------------------------------------------------------------------------
    # Transaction Type exception handlers — COTRTLIC / COTRTUPC
    # -------------------------------------------------------------------------

    @app.exception_handler(TransactionTypeNotFoundError)
    async def tt_not_found_handler(
        request: Request, exc: TransactionTypeNotFoundError
    ) -> JSONResponse:
        """
        COTRTLIC SQLCODE +100 / COTRTUPC TTUP-DETAILS-NOT-FOUND → HTTP 404.
        """
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error_code": exc.error_code, "message": exc.message, "details": []},
        )

    @app.exception_handler(TransactionTypeAlreadyExistsError)
    async def tt_already_exists_handler(
        request: Request, exc: TransactionTypeAlreadyExistsError
    ) -> JSONResponse:
        """
        COTRTUPC 9700-INSERT-RECORD SQLCODE -803 (duplicate key) → HTTP 409 Conflict.
        """
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"error_code": exc.error_code, "message": exc.message, "details": []},
        )

    @app.exception_handler(TransactionTypeHasDependentsError)
    async def tt_has_dependents_handler(
        request: Request, exc: TransactionTypeHasDependentsError
    ) -> JSONResponse:
        """
        COTRTLIC/COTRTUPC delete SQLCODE -532 (FK violation) → HTTP 409 Conflict.
        """
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"error_code": exc.error_code, "message": exc.message, "details": []},
        )

    @app.exception_handler(TransactionTypeOptimisticLockError)
    async def tt_optimistic_lock_handler(
        request: Request, exc: TransactionTypeOptimisticLockError
    ) -> JSONResponse:
        """
        COTRTLIC WS-DATACHANGED-FLAG / COTRTUPC 1205-COMPARE-OLD-NEW → HTTP 409 Conflict.
        """
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"error_code": exc.error_code, "message": exc.message, "details": []},
        )

    @app.exception_handler(TransactionTypeNoChangesError)
    async def tt_no_changes_handler(
        request: Request, exc: TransactionTypeNoChangesError
    ) -> JSONResponse:
        """
        COTRTLIC WS-MESG-NO-CHANGES-DETECTED → HTTP 422 Unprocessable Entity.
        """
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error_code": exc.error_code, "message": exc.message, "details": []},
        )

    @app.exception_handler(CardDemoException)
    async def carddemo_exception_handler(
        request: Request, exc: CardDemoException
    ) -> JSONResponse:
        """
        Catch-all for any other CardDemo domain exception → HTTP 400.
        """
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error_code": exc.error_code, "message": exc.message, "details": []},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """
        Pydantic validation failure → HTTP 422 Unprocessable Entity.

        COBOL origin: Maps WS-ERR-FLG-ON / blank-field checks.
        Formats Pydantic errors into the standard ErrorResponse structure.
        """
        details = []
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            details.append({"field": field, "message": error["msg"]})

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error_code": "VALIDATION_ERROR",
                "message": "Input validation failed",
                "details": details,
            },
        )
