"""
SQLAlchemy ORM model for the User Security entity.

Source: VSAM KSDS USRSEC / copybook CSUSR01Y (80 bytes)
Primary key: SEC-USR-ID PIC X(08)

Original COBOL stored passwords in plain text (SEC-USR-PWD).
This implementation uses bcrypt hashing (passlib) as a security improvement.
The API preserves the original field lengths and constraints.

Field mapping:
  SEC-USR-ID     PIC X(08)  -> usr_id         VARCHAR(8) PRIMARY KEY
  SEC-USR-FNAME  PIC X(20)  -> first_name      VARCHAR(20)
  SEC-USR-LNAME  PIC X(20)  -> last_name       VARCHAR(20)
  SEC-USR-PWD    PIC X(08)  -> pwd_hash        VARCHAR(72) (bcrypt hash; original was 8 chars plain)
  SEC-USR-TYPE   PIC X(01)  -> usr_type        CHAR(1) ('A'=Admin, 'U'=User)
  SEC-USR-FILLER PIC X(23)  -> (omitted)
"""

from sqlalchemy import CHAR, VARCHAR, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base


class UserORM(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "usr_type IN ('A', 'U')",
            name="ck_user_type_valid",
        ),
        CheckConstraint(
            "length(usr_id) >= 1 AND length(usr_id) <= 8",
            name="ck_user_id_length",
        ),
        Index("ix_users_usr_type", "usr_type"),
    )

    # SEC-USR-ID PIC X(08) - 8-character user ID (primary key)
    # COSGN00C: MOVE FUNCTION UPPER-CASE(USERIDI) TO WS-USER-ID -> keys are uppercase
    usr_id: Mapped[str] = mapped_column(VARCHAR(8), primary_key=True)

    # SEC-USR-FNAME PIC X(20)
    first_name: Mapped[str] = mapped_column(VARCHAR(20), nullable=False)

    # SEC-USR-LNAME PIC X(20)
    last_name: Mapped[str] = mapped_column(VARCHAR(20), nullable=False)

    # SEC-USR-PWD PIC X(08) - original was 8-char plain text
    # Stored as bcrypt hash (72 bytes max for bcrypt)
    # TODO(security): Original COBOL uses plain-text comparison. We use bcrypt.
    pwd_hash: Mapped[str] = mapped_column(VARCHAR(72), nullable=False)

    # SEC-USR-TYPE PIC X(01) - 'A'=Admin routes to COADM01C, 'U'=User routes to COMEN01C
    # BR-SGN-004: User type 'A' routes to Admin Menu; any other type routes to Main Menu
    usr_type: Mapped[str] = mapped_column(CHAR(1), nullable=False, default="U")

    def __repr__(self) -> str:
        return f"<User id={self.usr_id} type={self.usr_type}>"
