"""User schemas — COUSR00C/01C/02C/03C."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class UserResponse(BaseModel):
    """User record response. password_hash is NEVER included."""
    user_id: str
    first_name: str
    last_name: str
    user_type: Literal["A", "U"]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserCreateRequest(BaseModel):
    """POST /users — COUSR01C WRITE-USER-SEC-FILE."""
    user_id: str = Field(..., min_length=1, max_length=8, pattern=r"^[A-Za-z0-9]+$")
    first_name: str = Field(..., min_length=1, max_length=20)
    last_name: str = Field(..., min_length=1, max_length=20)
    password: str = Field(..., min_length=1, max_length=8)
    user_type: Literal["A", "U"]


class UserUpdateRequest(BaseModel):
    """PUT /users/{user_id} — COUSR02C UPDATE-USER-SEC-FILE."""
    first_name: str = Field(..., min_length=1, max_length=20)
    last_name: str = Field(..., min_length=1, max_length=20)
    password: Optional[str] = Field(None, max_length=8)
    user_type: Literal["A", "U"]


class UserListResponse(BaseModel):
    """Paginated user list — COUSR00C POPULATE-USER-DATA."""
    items: list[UserResponse]
    page: int
    page_size: int
    total_count: int
    has_next: bool
    has_previous: bool
