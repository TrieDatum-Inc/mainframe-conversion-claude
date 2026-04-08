"""
Pydantic schemas for transaction type management.

Source programs:
  app/app-transaction-type-db2/cbl/COTRTLIC.cbl — List/browse (CICS CTLI)
  app/app-transaction-type-db2/cbl/COTRTUPC.cbl — Update (CICS CTTU)

DB2 table: CARDDEMO.TRANSACTION_TYPE
  TR_TYPE        CHAR(2)   NOT NULL PRIMARY KEY
  TR_DESCRIPTION CHAR(50)  NOT NULL

Endpoint mapping:
  GET  /api/v1/transaction-types        → COTRTLIC (cursor-based list)
  GET  /api/v1/transaction-types/{id}   → COTRTLIC/COTRTUPC 9000-READ-TRANTYPE
  PUT  /api/v1/transaction-types/{id}   → COTRTUPC 9600-WRITE-PROCESSING

COTRTLIC DB2 cursor (forward):
  DECLARE C-TR-TYPE-FORWARD CURSOR FOR
    SELECT TR_TYPE, TR_DESCRIPTION
    FROM   CARDDEMO.TRANSACTION_TYPE
    WHERE  TR_TYPE >= :WS-START-KEY
    AND    ((:WS-EDIT-TYPE-FLAG = '1' AND TR_TYPE = :WS-TYPE-CD-FILTER) OR ...)
    AND    ((:WS-EDIT-DESC-FLAG = '1' AND TR_DESCRIPTION LIKE ...) OR ...)
    ORDER BY TR_TYPE

Max rows per page: WS-MAX-SCREEN-LINES = 7 (COTRTLIC constant)

COTRTUPC 9600-WRITE-PROCESSING SQL:
  UPDATE CARDDEMO.TRANSACTION_TYPE
  SET    TR_DESCRIPTION = :TTUP-NEW-TTYP-TYPE-DESC
  WHERE  TR_TYPE = :TTUP-OLD-TTYP-TYPE

COTRTUPC validation rules (1210-EDIT-TRANTYPE, 1230-EDIT-ALPHANUM-REQD):
  - type_cd: exactly 2 chars, numeric, non-zero
    (COTRTUPC 1245-EDIT-NUM-REQD: FUNCTION TEST-NUMVAL, FUNCTION NUMVAL != 0)
  - description: non-blank, alphanumeric + spaces only, max 50 chars
    (COTRTUPC 1230-EDIT-ALPHANUM-REQD: INSPECT CONVERTING LIT-ALL-ALPHANUM-FROM)
  - description must differ from current DB value
    (COTRTUPC 1205-COMPARE-OLD-NEW: FUNCTION UPPER-CASE comparison)
"""
import re

from pydantic import BaseModel, Field, field_validator


class TransactionTypeResponse(BaseModel):
    """
    Single transaction type record.

    Maps to COTRTLIC screen row (EACH-ROWO):
      TRTTYPO PIC X(02) — TR_TYPE
      TRTYPDO PIC X(50) — TR_DESCRIPTION

    Also used for COTRTUPC 9000-READ-TRANTYPE response.
    """

    type_cd: str = Field(..., max_length=2, description="TR_TYPE CHAR(2) — PIC X(02)")
    description: str = Field(..., max_length=50, description="TR_DESCRIPTION CHAR(50) — PIC X(50)")

    model_config = {"from_attributes": True}


class TransactionTypeListResponse(BaseModel):
    """
    Paginated transaction type list.

    Maps to COTRTLIC screen page (WS-MAX-SCREEN-LINES = 7 rows per page).

    Keyset pagination mirrors DB2 cursor:
      DECLARE C-TR-TYPE-FORWARD CURSOR FOR ... WHERE TR_TYPE >= :WS-START-KEY ORDER BY TR_TYPE
      next_cursor = last TR_TYPE on page (WS-CA-LAST-TR-CODE)
      prev_cursor = first TR_TYPE on page (WS-CA-FIRST-TR-CODE)

    CA-NEXT-PAGE-EXISTS (WS-CA-NEXT-PAGE-IND = 'Y') → has_next_page = True
    CA-FIRST-PAGE      (WS-CA-SCREEN-NUM = 1)       → cursor is None on first page
    """

    items: list[TransactionTypeResponse]
    total: int = Field(..., description="Total matching records in TRANSACTION_TYPE table")
    next_cursor: str | None = Field(
        None,
        description=(
            "Last TR_TYPE on this page (WS-CA-LAST-TR-CODE). "
            "None when CA-NEXT-PAGE-NOT-EXISTS."
        ),
    )
    prev_cursor: str | None = Field(
        None,
        description=(
            "First TR_TYPE on this page (WS-CA-FIRST-TR-CODE). "
            "None on first page (CA-FIRST-PAGE)."
        ),
    )


class TransactionTypeUpdateRequest(BaseModel):
    """
    Update request for PUT /api/v1/transaction-types/{type_cd}.

    Maps to COTRTUPC 1000-PROCESS-INPUTS → 1150-STORE-MAP-IN-NEW → 1200-EDIT-MAP-INPUTS.

    Fields on screen (CTRTUPA BMS map):
      TRTYPCDI  PIC X(02) — type code (key field, read-only in update)
      TRTYDSCI  PIC X(50) — description (updatable)

    COTRTUPC 9600-WRITE-PROCESSING SQL:
      UPDATE CARDDEMO.TRANSACTION_TYPE
      SET    TR_DESCRIPTION = :TTUP-NEW-TTYP-TYPE-DESC
      WHERE  TR_TYPE = :TTUP-OLD-TTYP-TYPE

    Validation rules from COTRTUPC 1230-EDIT-ALPHANUM-REQD:
      1. description must not be blank or spaces
      2. description can only contain alphanumeric chars and spaces
         (INSPECT WS-EDIT-ALPHANUM-ONLY CONVERTING LIT-ALL-ALPHANUM-FROM TO LIT-ALPHANUM-SPACES-TO)
      3. description max 50 chars (WS-EDIT-ALPHANUM-LENGTH = 50)
    """

    description: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="TR_DESCRIPTION CHAR(50) — TRTYDSCI PIC X(50)",
    )

    @field_validator("description")
    @classmethod
    def validate_alphanum_only(cls, v: str) -> str:
        """
        COTRTUPC 1230-EDIT-ALPHANUM-REQD validation.

        INSPECT WS-EDIT-ALPHANUM-ONLY CONVERTING LIT-ALL-ALPHANUM-FROM TO LIT-ALPHANUM-SPACES-TO
        — all alphanumeric + space chars are converted to spaces; if any remain, error.

        LIT-ALL-ALPHANUM-FROM-X = upper + lower (26+26) + digits (10) = 62 chars.
        """
        stripped = v.strip()
        if not stripped:
            raise ValueError("description must not be blank (COTRTUPC: must be supplied)")
        # Allow alphanumeric and space only (COTRTUPC LIT-ALL-ALPHANUM-FROM-X)
        if not re.match(r"^[A-Za-z0-9 ]+$", v):
            raise ValueError(
                "description can have numbers or alphabets only "
                "(COTRTUPC: 1230-EDIT-ALPHANUM-REQD)"
            )
        return v
