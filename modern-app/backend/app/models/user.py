"""SQLAlchemy ORM model for the users table.

Maps directly to the USRSEC VSAM file from the CardDemo mainframe application:
  SEC-USR-ID    X(8)  -> user_id   VARCHAR(8)  PRIMARY KEY
  SEC-USR-FNAME X(20) -> first_name VARCHAR(20)
  SEC-USR-LNAME X(20) -> last_name  VARCHAR(20)
  SEC-USR-PWD   X(8)  -> password_hash VARCHAR(255) (bcrypt-hashed)
  SEC-USR-TYPE  X(1)  -> user_type  VARCHAR(1) CHECK IN ('A','U')
"""
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

# COBOL 88-level condition names preserved as constants
USER_TYPE_ADMIN = "A"
USER_TYPE_REGULAR = "U"
VALID_USER_TYPES = {USER_TYPE_ADMIN, USER_TYPE_REGULAR}


class User(Base):
    """Represents a CardDemo application user.

    Mirrors the USRSEC VSAM KSDS record layout (CSUSR01Y copybook).
    The user_id is the VSAM primary key (SEC-USR-ID).
    """

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("user_type IN ('A', 'U')", name="ck_users_user_type"),
    )

    user_id: Mapped[str] = mapped_column(
        String(8),
        primary_key=True,
        comment="VSAM key — SEC-USR-ID X(8)",
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
        comment="bcrypt hash of SEC-USR-PWD X(8)",
    )
    user_type: Mapped[str] = mapped_column(
        String(1),
        nullable=False,
        comment="SEC-USR-TYPE: A=Admin, U=Regular",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<User user_id={self.user_id!r} user_type={self.user_type!r}>"
