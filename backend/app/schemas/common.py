"""Common response schemas shared across modules."""

from pydantic import BaseModel


class MessageResponse(BaseModel):
    """Generic success message response."""
    message: str


class ErrorDetail(BaseModel):
    """Single error detail item."""
    field: str | None = None
    message: str


class ErrorResponse(BaseModel):
    """Standard API error response envelope."""
    error_code: str
    message: str
    details: list[ErrorDetail] = []
