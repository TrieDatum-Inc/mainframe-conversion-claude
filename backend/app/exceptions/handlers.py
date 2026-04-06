"""
Centralized exception handlers.
Maps Python/SQLAlchemy exceptions to HTTP status codes, preserving
the COBOL error code/message pattern for frontend consumption.
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError


def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers on the FastAPI app."""

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(
        request: Request, exc: IntegrityError
    ) -> JSONResponse:
        """
        Handle database constraint violations.
        Replaces: COBOL SQLCODE -803 (duplicate key) handling in COPAUS2C.
        """
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error_code": "DUPLICATE_RECORD",
                "message": "A record with this key already exists",
                "details": [str(exc.orig) if exc.orig else ""],
            },
        )

    @app.exception_handler(OperationalError)
    async def operational_error_handler(
        request: Request, exc: OperationalError
    ) -> JSONResponse:
        """
        Handle database connection errors.
        Replaces: COBOL SQLCODE other / IMS non-GE status code handling.
        """
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error_code": "DATABASE_ERROR",
                "message": "A database error occurred",
                "details": [],
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(
        request: Request, exc: ValueError
    ) -> JSONResponse:
        """Handle validation errors not caught by Pydantic."""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error_code": "VALIDATION_ERROR",
                "message": str(exc),
                "details": [],
            },
        )
