"""
User ORM model — maps USRSEC VSAM KSDS to PostgreSQL `users` table.

COBOL source: CSUSR01Y copybook, USRSEC VSAM KSDS
Key change: SEC-USR-PWD X(8) plain text → password_hash VARCHAR(255) bcrypt hash.
"""

from datetime import datetime

from sqlalchemy import CHAR, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    """PostgreSQL `users` table — replaces USRSEC VSAM KSDS."""

    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(
        String(8), primary_key=True,
        comment="COBOL: SEC-USR-ID PIC X(08) — VSAM KSDS primary key",
    )
    first_name: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="COBOL: SEC-USR-FNAME PIC X(20)",
    )
    last_name: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="COBOL: SEC-USR-LNAME PIC X(20)",
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False,
        comment="COBOL: SEC-USR-PWD PIC X(08) — bcrypt hash; NEVER plain text",
    )
    user_type: Mapped[str] = mapped_column(
        CHAR(1), nullable=False,
        comment="COBOL: SEC-USR-TYPE PIC X(01) — 'A'=Admin, 'U'=User",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<User user_id={self.user_id!r} user_type={self.user_type!r}>"
