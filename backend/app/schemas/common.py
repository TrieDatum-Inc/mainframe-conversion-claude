"""
Shared Pydantic schema models used across all modules.
"""

from typing import Any, List, Optional
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """
    Standard error envelope returned on all 4xx/5xx responses.

    Maps to the WS-MESSAGE field in COBOL programs that was
    displayed in the ERRMSG output field of BMS maps.
    """
    error_code: str
    message: str
    details: List[Any] = []


class MessageResponse(BaseModel):
    """Generic success message response."""
    message: str
