"""User ORM model — maps to the `users` table (USRSEC VSAM file equivalent).

COBOL source copybook: CSUSR01Y.cpy
COBOL 01-level: SEC-USER-DATA (80-byte record)
Key field: SEC-USR-ID PIC X(08) — stored as VARCHAR(8) PRIMARY KEY
"""
from datetime import datetime

from sqlalchemy import CHAR, TIMESTAMP, VARCHAR, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    """Maps to users table.

    User type values:
      'A' — Admin (routed to COADM01C → /admin-menu in modern stack)
      'U' — Regular user (routed to COMEN01C → /main-menu in modern stack)

    COBOL BR-003: user_id is uppercased before lookup.
    COBOL BR-005: password comparison is character-exact (uppercased plaintext).
    Modern equivalent: password is bcrypt-hashed; login service uppercases input before verify.
    """

    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(
        VARCHAR(8), primary_key=True, comment="SEC-USR-ID PIC X(08)"
    )
    first_name: Mapped[str] = mapped_column(
        VARCHAR(20), nullable=False, comment="SEC-USR-FNAME PIC X(20)"
    )
    last_name: Mapped[str] = mapped_column(
        VARCHAR(20), nullable=False, comment="SEC-USR-LNAME PIC X(20)"
    )
    password: Mapped[str] = mapped_column(
        VARCHAR(255),
        nullable=False,
        comment="bcrypt hash — COBOL stored plaintext SEC-USR-PWD PIC X(08)",
    )
    user_type: Mapped[str] = mapped_column(
        CHAR(1),
        nullable=False,
        server_default=text("'U'"),
        comment="SEC-USR-TYPE PIC X(01): A=Admin U=Regular",
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    @property
    def is_admin(self) -> bool:
        """True when user_type = 'A' (CDEMO-USRTYP-ADMIN condition)."""
        return self.user_type == "A"

    @property
    def is_regular_user(self) -> bool:
        """True when user_type = 'U' (CDEMO-USRTYP-USER condition)."""
        return self.user_type == "U"
