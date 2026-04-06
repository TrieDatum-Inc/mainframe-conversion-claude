"""
Global FastAPI exception handlers.

Ensures all unhandled errors produce the standard ErrorResponse envelope
matching the COBOL program's error message display pattern (WS-MESSAGE on ERRMSGO).
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers on the FastAPI application."""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """
        Convert Pydantic validation errors to the standard ErrorResponse format.

        COBOL origin: Field-level blank checks in COUSR01C/COUSR02C PROCESS-ENTER-KEY:
          IF FNAMEI = SPACES → 'First Name can NOT be empty...'
          IF LNAMEI = SPACES → 'Last Name can NOT be empty...'
        """
        details = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            details.append({"field": field, "message": error["msg"]})

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error_code": "VALIDATION_ERROR",
                "message": "Input validation failed",
                "details": details,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """
        Catch-all for unexpected errors.

        COBOL origin: RESP=OTHER path in READ/WRITE/DELETE handlers:
          'Unable to Add/Update/Delete User...' + DISPLAY RESP/RESP2
        Here we log the exception and return a generic 500.
        """
        logger.exception("Unhandled exception on %s %s", request.method, request.url)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": [],
            },
        )
