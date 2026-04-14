"""
Global FastAPI exception handlers.

Ensures all errors return the standard ErrorResponse envelope
rather than FastAPI's default detail format.
"""

import structlog
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas.common import ErrorResponse

logger = structlog.get_logger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all global exception handlers on the FastAPI app."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        """
        Convert HTTPException to the standard ErrorResponse envelope.
        """
        detail = exc.detail
        if isinstance(detail, dict):
            error_code = detail.get("error_code", "HTTP_ERROR")
            message = detail.get("message", str(exc.detail))
        else:
            error_code = "HTTP_ERROR"
            message = str(detail)

        if exc.status_code >= 500:
            logger.error(
                "server_error",
                status_code=exc.status_code,
                path=str(request.url),
                error=message,
            )

        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error_code=error_code,
                message=message,
            ).model_dump(),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """
        Convert Pydantic validation errors to 422 with the standard envelope.
        """
        details = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
            details.append({"field": field, "message": error["msg"]})

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                error_code="VALIDATION_ERROR",
                message="Request validation failed",
                details=details,
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """
        Catch-all handler for unexpected exceptions.
        Logs the full traceback; returns a generic 500 without leaking internals.
        """
        logger.exception(
            "unhandled_exception",
            path=str(request.url),
            exc_type=type(exc).__name__,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error_code="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred",
            ).model_dump(),
        )
