"""User ORM model — maps to the `users` table.

Derived from the COBOL CSUSR01Y copybook / USRSEC VSAM KSDS file:
  SEC-USR-ID   PIC X(8)  -> user_id VARCHAR(8)   (PK)
  SEC-USR-FNAME PIC X(20) -> first_name VARCHAR(20)
  SEC-USR-LNAME PIC X(20) -> last_name  VARCHAR(20)
  SEC-USR-PWD  PIC X(8)  -> password_hash VARCHAR(255) (bcrypt replaces plain-text)
  SEC-USR-TYPE PIC X(1)  -> user_type CHAR(1)  CHECK IN ('A','U')
"""

import enum
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserType(str, enum.Enum):
    """Maps to COBOL condition names on SEC-USR-TYPE."""

    ADMIN = "A"
    USER = "U"


class User(Base):
    """Represents a CardDemo application user (USRSEC VSAM record)."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("user_type IN ('A', 'U')", name="ck_users_user_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(8), unique=True, nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    last_name: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    user_type: Mapped[str] = mapped_column(String(1), nullable=False, default=UserType.USER)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<User user_id={self.user_id!r} user_type={self.user_type!r}>"
