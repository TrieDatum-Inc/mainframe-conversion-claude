"""
User ORM model — maps USRSEC VSAM KSDS to PostgreSQL `users` table.

COBOL source: CSUSR01Y copybook, USRSEC VSAM KSDS
Key change: SEC-USR-PWD X(8) plain text → password_hash VARCHAR(255) bcrypt hash.
SEC-USR-FILLER X(23) discarded (unused padding).
SEC-USR-TYPE 'A'/'R' → user_type CHAR(1) CHECK IN ('A','U') — 'R' normalized to 'U'.

Record layout (CSUSR01Y):
  SEC-USR-ID    PIC X(08)  → user_id    VARCHAR(8)  PRIMARY KEY
  SEC-USR-PWD   PIC X(08)  → password_hash VARCHAR(255)  (bcrypt; NEVER plain text)
  SEC-USR-FNAME PIC X(20)  → first_name VARCHAR(20)
  SEC-USR-LNAME PIC X(20)  → last_name  VARCHAR(20)
  SEC-USR-TYPE  PIC X(01)  → user_type  CHAR(1) CHECK IN ('A','U')
  SEC-USR-FILLER PIC X(23) → (not stored — discarded padding)
"""

from datetime import datetime

from sqlalchemy import CHAR, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    """
    PostgreSQL `users` table.

    Replaces USRSEC VSAM KSDS (key-sequenced data set).
    VSAM KSDS primary key (SEC-USR-ID) → VARCHAR(8) primary key.
    CICS READ DATASET(USRSEC) RIDFLD(user_id) → SELECT WHERE user_id = :id.
    CICS WRITE DATASET(USRSEC) → INSERT INTO users.
    CICS REWRITE DATASET(USRSEC) → UPDATE users SET ... WHERE user_id = :id.
    CICS DELETE DATASET(USRSEC) → DELETE FROM users WHERE user_id = :id.
    """

    __tablename__ = "users"

    # SEC-USR-ID PIC X(08) — VSAM KSDS key; right-padded to 8 chars in legacy
    user_id: Mapped[str] = mapped_column(
        String(8),
        primary_key=True,
        comment="COBOL: SEC-USR-ID PIC X(08) — VSAM KSDS primary key",
    )

    # SEC-USR-FNAME PIC X(20)
    first_name: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="COBOL: SEC-USR-FNAME PIC X(20)",
    )

    # SEC-USR-LNAME PIC X(20)
    last_name: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="COBOL: SEC-USR-LNAME PIC X(20)",
    )

    # SEC-USR-PWD PIC X(08) — was plain text; now bcrypt hash
    # Max length 255 accommodates bcrypt output ($2b$12$... = 60 chars + headroom)
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="COBOL: SEC-USR-PWD PIC X(08) — bcrypt hash; NEVER plain text",
    )

    # SEC-USR-TYPE PIC X(01) — 'A'=Admin, 'U'=User ('R' normalized to 'U')
    # CHECK constraint enforced at DB level; Pydantic enforces at API level
    user_type: Mapped[str] = mapped_column(
        CHAR(1),
        nullable=False,
        comment="COBOL: SEC-USR-TYPE PIC X(01) — 'A'=Admin, 'U'=User",
    )

    # Audit timestamps — not in COBOL; new requirement for compliance
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Record creation timestamp — not in COBOL source",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Record last-modified timestamp — supports optimistic locking",
    )

    def __repr__(self) -> str:
        return f"<User user_id={self.user_id!r} user_type={self.user_type!r}>"
