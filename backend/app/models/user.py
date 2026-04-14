"""
User ORM model — maps to the `users` PostgreSQL table.

COBOL origin: USRSEC VSAM KSDS file (CSUSR01Y copybook).
  - SEC-USR-ID    X(8)  → user_id VARCHAR(8) PRIMARY KEY
  - SEC-USR-FNAME X(20) → first_name VARCHAR(20)
  - SEC-USR-LNAME X(20) → last_name VARCHAR(20)
  - SEC-USR-PWD   X(8)  → password_hash VARCHAR(255)  [SECURITY: bcrypt replaces plain text]
  - SEC-USR-TYPE  X(1)  → user_type CHAR(1) CHECK IN ('A','U')
  - SEC-USR-FILLER X(23) → DISCARDED (unused padding)

Security improvement: SEC-USR-PWD was stored and compared as plain text in COSGN00C.
The modern system stores only a bcrypt hash. The original plain-text password is never
stored, logged, or returned in any response.
"""

from datetime import datetime
from sqlalchemy import String, DateTime, func, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(
        String(8), primary_key=True, nullable=False,
        comment="SEC-USR-ID X(8) — VSAM KSDS primary key"
    )
    first_name: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="SEC-USR-FNAME X(20)"
    )
    last_name: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="SEC-USR-LNAME X(20)"
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False,
        comment="bcrypt hash; replaces SEC-USR-PWD X(8) plain text"
    )
    user_type: Mapped[str] = mapped_column(
        String(1), nullable=False,
        comment="SEC-USR-TYPE X(1): A=Admin, U=Regular"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("user_type IN ('A', 'U')", name="chk_users_type"),
    )

    def __repr__(self) -> str:
        return f"<User user_id={self.user_id!r} user_type={self.user_type!r}>"
