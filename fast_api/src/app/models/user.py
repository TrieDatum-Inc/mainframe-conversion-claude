"""SQLAlchemy ORM model for the users table.

Maps to the USRSEC VSAM KSDS file, record layout defined in CSUSR01Y.cpy:
    SEC-USR-ID     PIC X(08)  → user_id   VARCHAR(8)  PRIMARY KEY
    SEC-USR-FNAME  PIC X(20)  → first_name VARCHAR(20) NOT NULL
    SEC-USR-LNAME  PIC X(20)  → last_name  VARCHAR(20) NOT NULL
    SEC-USR-PWD    PIC X(08)  → password   VARCHAR(255) NOT NULL  (bcrypt)
    SEC-USR-TYPE   PIC X(01)  → user_type  CHAR(1)     CHECK ('A','U')
    SEC-USR-FILLER PIC X(23)  → (discarded — no modern equivalent needed)
"""
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    """User security record.  Corresponds to one 80-byte USRSEC VSAM record."""

    __tablename__ = "users"
    __table_args__ = (
        # COBOL bug fix: enforce 'A' or 'U' — original COUSR01C only checked NOT SPACES
        CheckConstraint("user_type IN ('A', 'U')", name="ck_users_user_type"),
    )

    # PIC X(08) — VSAM KSDS primary key
    user_id: Mapped[str] = mapped_column(String(8), primary_key=True)

    # PIC X(20) — SEC-USR-FNAME
    first_name: Mapped[str] = mapped_column(String(20), nullable=False)

    # PIC X(20) — SEC-USR-LNAME
    last_name: Mapped[str] = mapped_column(String(20), nullable=False)

    # PIC X(08) in COBOL, but stored as bcrypt hash here (up to 255 chars)
    password: Mapped[str] = mapped_column(String(255), nullable=False)

    # PIC X(01) — 'A'=Admin, 'U'=User
    user_type: Mapped[str] = mapped_column(String(1), nullable=False)

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
        return (
            f"User(user_id={self.user_id!r}, "
            f"first_name={self.first_name!r}, "
            f"last_name={self.last_name!r}, "
            f"user_type={self.user_type!r})"
        )
