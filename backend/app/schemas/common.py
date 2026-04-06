"""
Shared Pydantic schemas used across all API modules.

COBOL origin: Replaces CSMSG01Y copybook (common messages) and WS-MESSAGE
working storage fields present in every COBOL program.
"""

from typing import Any

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """
    Standard API error response envelope.

    Maps to COBOL WS-MESSAGE error display pattern:
        MOVE 'Error text' TO WS-MESSAGE
        PERFORM SEND-SCREEN

    The error_code field enables frontend to display context-specific messages
    without parsing message text — improves on the COBOL approach.
    """

    error_code: str
    message: str
    details: list[Any] = []


class MessageResponse(BaseModel):
    """
    Standard API success message response.

    Maps to COBOL WS-MESSAGE success display (e.g., CCDA-MSG-THANK-YOU).
    """

    message: str
