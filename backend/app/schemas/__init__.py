"""Pydantic schema registry."""

from app.schemas.account import (
    AccountUpdateRequest,
    AccountViewResponse,
    CustomerDetailResponse,
    CustomerUpdateRequest,
)
from app.schemas.common import ErrorResponse, MessageResponse, PaginatedResponse
from app.schemas.credit_card import (
    CardDetailResponse,
    CardListItem,
    CardListResponse,
    CardUpdateRequest,
)

__all__ = [
    "PaginatedResponse",
    "ErrorResponse",
    "MessageResponse",
    "AccountViewResponse",
    "AccountUpdateRequest",
    "CustomerDetailResponse",
    "CustomerUpdateRequest",
    "CardListItem",
    "CardListResponse",
    "CardDetailResponse",
    "CardUpdateRequest",
]
