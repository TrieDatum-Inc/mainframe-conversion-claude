"""
SQLAlchemy ORM model for the `users` table.

COBOL origin: USRSEC VSAM KSDS (CSUSR01Y copybook).
  SEC-USR-ID     X(08)  → user_id VARCHAR(8) PRIMARY KEY
  SEC-USR-PWD    X(08)  → password_hash VARCHAR(255) [bcrypt; never plain text]
  SEC-USR-FNAME  X(20)  → first_name VARCHAR(20)
  SEC-USR-LNAME  X(20)  → last_name VARCHAR(20)
  SEC-USR-TYPE   X(01)  → user_type CHAR(1) CHECK IN ('A','U')
  SEC-USR-FILLER X(23)  → (not migrated; unused padding)

Security note: SEC-USR-PWD was stored as plain text in USRSEC.
This model stores only the bcrypt hash — the original plain-text
password can never be recovered from this column.
"""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    """
    Persistent user record — maps to the `users` PostgreSQL table.

    COBOL equivalent: SEC-USER-DATA group (CSUSR01Y copybook).
    CICS file: USRSEC KSDS keyed on SEC-USR-ID.
    """

    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint("user_type IN ('A', 'U')", name="chk_users_type"),
    )

    user_id: Mapped[str] = mapped_column(
        String(8),
        primary_key=True,
        comment="SEC-USR-ID X(08) — VSAM primary key; 1-8 alphanumeric chars",
    )
    first_name: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="SEC-USR-FNAME X(20)",
    )
    last_name: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="SEC-USR-LNAME X(20)",
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="bcrypt hash of SEC-USR-PWD; plain-text password never stored",
    )
    user_type: Mapped[str] = mapped_column(
        String(1),
        nullable=False,
        comment="SEC-USR-TYPE X(01): 'A'=Admin, 'U'=Regular user",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Row creation timestamp (not in original VSAM record)",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Row last-modified timestamp; updated by trigger on every REWRITE",
    )

    def __repr__(self) -> str:
        return f"User(user_id={self.user_id!r}, user_type={self.user_type!r})"
