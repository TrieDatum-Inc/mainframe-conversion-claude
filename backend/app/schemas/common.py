"""
Common Pydantic schemas shared across all modules.
Implements standard API response envelope patterns.
"""
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorResponse(BaseModel):
    """
    Standard error response format for all API errors.
    Replaces COBOL WS-MESSAGE and ERRMSG BMS field patterns.
    """

    error_code: str
    message: str
    details: list[str] = []


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Paginated response envelope.
    Replaces COPAUS0C IMS browse pattern with CDEMO-CPVS-PAUKEY-PREV-PG array.
    page_size default=5 maps to COPAUS0C's 5 rows per screen.
    """

    items: list[T]
    page: int
    page_size: int
    total_count: int
    has_next: bool
    has_previous: bool


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str
