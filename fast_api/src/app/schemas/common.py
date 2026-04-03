from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str
    field: str | None = None


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    has_next_page: bool
    has_prev_page: bool
    first_tran_id: str | None = None
    last_tran_id: str | None = None
