"""Common schema definitions for paginated responses, errors, and messages.

Mirrors COBOL STARTBR/READNEXT pagination patterns and CSMSG01Y/CSMSG02Y
message structures.
"""

from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response matching COBOL STARTBR/READNEXT pattern."""

    items: List[T]
    page: int
    page_size: int
    total_count: int
    has_next_page: bool


class ErrorResponse(BaseModel):
    """Error response preserving COBOL error messages verbatim."""

    error_message: str
    field: Optional[str] = None


class MessageResponse(BaseModel):
    """Success/info message response."""

    message: str
    message_type: str = "info"  # info, success, error
