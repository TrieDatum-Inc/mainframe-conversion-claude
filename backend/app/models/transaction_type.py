"""
SQLAlchemy ORM model for the `transaction_types` table.

COBOL origin: DB2 table CARDDEMO.TRANSACTION_TYPE (DCLTRTYP DCLGEN copybook).
  TR_TYPE        CHAR(2)    → type_code VARCHAR(2) PRIMARY KEY
  TR_DESCRIPTION VARCHAR(50) → description VARCHAR(50) NOT NULL

Programs:
  COTRTLIC - List/filter/page/update/delete transaction types
  COTRTUPC - Add and update individual transaction type records

DB2 constraints replicated as PostgreSQL CHECK constraints:
  - COTRTUPC 1210-EDIT-TRANTYPE: NUMERIC test + non-zero → chk_tt_type_code_numeric + chk_tt_type_code_nonzero
  - COTRTUPC 1230-EDIT-ALPHANUM-REQD: alphanumeric only → chk_tt_description_alphanum
  - COTRTLIC 9300-DELETE-RECORD: SQLCODE -532 FK violation → FK transactions.transaction_type_code
"""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TransactionType(Base):
    """
    Persistent transaction type record — maps to the `transaction_types` PostgreSQL table.

    COBOL equivalent: CARDDEMO.TRANSACTION_TYPE DB2 table (accessed via DCLTRTYP DCLGEN).
    Used by COTRTLIC (list/browse) and COTRTUPC (add/update/delete).

    The type_code is a 2-digit numeric string (e.g., '01', '02') that serves as a
    foreign key in the transactions table. Type codes must be non-zero numeric (01-99).

    Note on CHECK constraints:
      The original COTRTUPC validation rules (1210-EDIT-TRANTYPE + 1230-EDIT-ALPHANUM-REQD)
      are enforced at the API/service layer via Pydantic validators rather than via SQLAlchemy
      CHECK constraints. This is because the constraints use PostgreSQL-specific syntax
      (~ regex operator, ::INTEGER cast) that is incompatible with SQLite used in tests.
      The constraints ARE present in sql/create_tables.sql and the Alembic migration
      for production PostgreSQL deployments.
    """

    __tablename__ = "transaction_types"

    type_code: Mapped[str] = mapped_column(
        String(2),
        primary_key=True,
        comment="TR_TYPE CHAR(2) — 2-digit numeric code e.g. '01', '02'. Numeric 01-99, non-zero.",
    )
    description: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="TR_DESCRIPTION VARCHAR(50) — alphanumeric only, no special characters.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Row creation timestamp (not in original DB2 table; added for audit trail).",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Row last-modified timestamp; updated by trigger on every UPDATE (replaces WS-DATACHANGED-FLAG).",
    )

    def __repr__(self) -> str:
        return f"TransactionType(type_code={self.type_code!r}, description={self.description!r})"
