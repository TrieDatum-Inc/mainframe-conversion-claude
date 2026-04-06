"""
Shared Pydantic schemas: pagination envelope, error response, message response.

COBOL origin: Replicates the standard COMMAREA pagination fields
(CDEMO-CU00-NEXT-PAGE-FLG, CDEMO-CU00-USRID-FIRST, CDEMO-CU00-USRID-LAST)
and the WS-MESSAGE / ERRMSG error display pattern used by all COUSR programs.
"""

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Standard paginated list envelope.

    COBOL origin: COUSR00C POPULATE-USER-DATA browse state variables.
    Maps:
      items           ← list of row objects (USRID1O–USRID10O, FNAME1O–FNAME10O, etc.)
      page            ← CDEMO-CU00-PAGE-NUM 9(08)
      page_size       ← hardcoded 10 in COUSR00C POPULATE-USER-DATA
      total_count     ← computed via COUNT(*) (no COBOL equivalent; VSAM had no count)
      has_next        ← CDEMO-CU00-NEXT-PAGE-FLG 'Y'/'N'
      has_previous    ← page > 1
      first_item_key  ← CDEMO-CU00-USRID-FIRST X(08)
      last_item_key   ← CDEMO-CU00-USRID-LAST X(08)
    """

    items: list[T]
    page: int
    page_size: int
    total_count: int
    has_next: bool
    has_previous: bool
    first_item_key: Optional[str] = None
    last_item_key: Optional[str] = None


class ErrorResponse(BaseModel):
    """
    Standard API error envelope.

    COBOL origin: WS-MESSAGE X(80) + DFHRED color on ERRMSGO field.
    Maps COBOL RESP codes to structured HTTP error bodies.
    """

    error_code: str
    message: str
    details: list[Any] = []


class MessageResponse(BaseModel):
    """
    Simple success message response.

    COBOL origin: DFHGREEN color on ERRMSGO field (success messages).
    Example: 'User [ID] has been deleted successfully'
    """

    message: str
