"""
Global exception handlers — converts application exceptions to HTTP responses.

COBOL origin: Replaces CICS HANDLE CONDITION / RESP code processing.
All errors use consistent JSON format: {"error_code": ..., "message": ..., "details": []}.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.exceptions.errors import (
    CardDemoException,
    DuplicateResourceError,
    InvalidCredentialsError,
    NoChangesDetectedError,
    NotFoundError,
    OptimisticLockError,
    PermissionDeniedError,
    ValidationError,
)


def _error_response(error_code: str, message: str, status_code: int) -> JSONResponse:
    """Build a consistent error response envelope."""
    return JSONResponse(
        status_code=status_code,
        content={"detail": {"error_code": error_code, "message": message, "details": []}},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI application."""

    @app.exception_handler(NotFoundError)
    async def handle_not_found(request: Request, exc: NotFoundError) -> JSONResponse:
        return _error_response(exc.error_code, exc.message, status.HTTP_404_NOT_FOUND)

    @app.exception_handler(DuplicateResourceError)
    async def handle_duplicate(request: Request, exc: DuplicateResourceError) -> JSONResponse:
        return _error_response(exc.error_code, exc.message, status.HTTP_409_CONFLICT)

    @app.exception_handler(InvalidCredentialsError)
    async def handle_invalid_creds(request: Request, exc: InvalidCredentialsError) -> JSONResponse:
        return _error_response(exc.error_code, exc.message, status.HTTP_401_UNAUTHORIZED)

    @app.exception_handler(PermissionDeniedError)
    async def handle_permission(request: Request, exc: PermissionDeniedError) -> JSONResponse:
        return _error_response(exc.error_code, exc.message, status.HTTP_403_FORBIDDEN)

    @app.exception_handler(ValidationError)
    async def handle_validation(request: Request, exc: ValidationError) -> JSONResponse:
        return _error_response(exc.error_code, exc.message, status.HTTP_422_UNPROCESSABLE_ENTITY)

    @app.exception_handler(OptimisticLockError)
    async def handle_optimistic_lock(request: Request, exc: OptimisticLockError) -> JSONResponse:
        return _error_response(exc.error_code, exc.message, status.HTTP_409_CONFLICT)

    @app.exception_handler(NoChangesDetectedError)
    async def handle_no_changes(request: Request, exc: NoChangesDetectedError) -> JSONResponse:
        return _error_response(exc.error_code, exc.message, status.HTTP_422_UNPROCESSABLE_ENTITY)

    @app.exception_handler(CardDemoException)
    async def handle_carddemo_base(request: Request, exc: CardDemoException) -> JSONResponse:
        return _error_response(exc.error_code, exc.message, status.HTTP_400_BAD_REQUEST)

    @app.exception_handler(IntegrityError)
    async def handle_integrity(request: Request, exc: IntegrityError) -> JSONResponse:
        return _error_response(
            "DATABASE_INTEGRITY_ERROR",
            "A database constraint was violated. Check for duplicate or missing references.",
            status.HTTP_409_CONFLICT,
        )
