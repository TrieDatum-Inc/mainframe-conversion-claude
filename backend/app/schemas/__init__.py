"""Pydantic request/response schemas for the CardDemo authorization module."""
from app.schemas.authorization import (
    AuthDetailResponse,
    AuthFraudLogResponse,
    AuthListResponse,
    AuthSummaryResponse,
    FraudToggleRequest,
    FraudToggleResponse,
)
from app.schemas.common import ErrorResponse, PaginatedResponse

__all__ = [
    "AuthSummaryResponse",
    "AuthDetailResponse",
    "AuthListResponse",
    "FraudToggleRequest",
    "FraudToggleResponse",
    "AuthFraudLogResponse",
    "ErrorResponse",
    "PaginatedResponse",
]
