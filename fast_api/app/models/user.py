"""
SQLAlchemy ORM model for the `users` table.

Source copybook: app/cpy/CSUSR01Y.cpy — SEC-USER-DATA (80 bytes)
Source VSAM file: AWS.M2.CARDDEMO.USRSEC.VSAM.KSDS (USRSEC)
Primary key: SEC-USR-ID PIC X(08)

Security note:
  Original COBOL stores plaintext passwords (SEC-USR-PWD PIC X(08)).
  This model stores bcrypt hashes instead. The seed data script generates
  hashed versions of the original test passwords.

Access patterns:
  EXEC CICS READ   FILE(USRSEC) RIDFLD(WS-USER-ID) → UserRepository.get_by_id()
  EXEC CICS WRITE  FILE(USRSEC)                     → UserRepository.create()
  EXEC CICS REWRITE FILE(USRSEC)                    → UserRepository.update()
  EXEC CICS DELETE FILE(USRSEC)                     → UserRepository.delete()
  EXEC CICS STARTBR/READNEXT FILE(USRSEC)           → UserRepository.list_paginated()
"""
from sqlalchemy import CheckConstraint, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

# User type constants — from SEC-USR-TYPE 88-level conditions
USER_TYPE_ADMIN: str = "A"   # 88 CDEMO-USRTYP-ADMIN VALUE 'A' (COCOM01Y)
USER_TYPE_REGULAR: str = "U"  # regular user


class User(Base):
    """
    User security record.

    Maps to COBOL SEC-USER-DATA (CSUSR01Y.cpy).
    SEC-USR-ID is 8-char fixed-length, uppercase (COSGN00C applies UPPER-CASE).
    """

    __tablename__ = "users"
    __table_args__ = (
        # SEC-USR-TYPE: only 'A' (admin) or 'U' (regular) are valid
        CheckConstraint("user_type IN ('A', 'U')", name="ck_users_type"),
    )

    # SEC-USR-ID PIC X(08) — primary key, uppercase, space-padded in COBOL
    user_id: Mapped[str] = mapped_column(
        String(8), primary_key=True, comment="SEC-USR-ID PIC X(08) [uppercase, 8-char fixed]"
    )

    # SEC-USR-FNAME PIC X(20)
    first_name: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="SEC-USR-FNAME PIC X(20)")

    # SEC-USR-LNAME PIC X(20)
    last_name: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="SEC-USR-LNAME PIC X(20)")

    # SEC-USR-PWD PIC X(08) in COBOL (plaintext) → stored as bcrypt hash (60 chars)
    password_hash: Mapped[str] = mapped_column(
        String(60), nullable=False,
        comment="SEC-USR-PWD PIC X(08) [original plaintext; stored as bcrypt hash]"
    )

    # SEC-USR-TYPE PIC X(01) — 'A'=admin, 'U'=regular user
    user_type: Mapped[str] = mapped_column(
        String(1), nullable=False, default=USER_TYPE_REGULAR,
        comment="SEC-USR-TYPE PIC X(01): A=admin, U=regular"
    )

    @property
    def is_admin(self) -> bool:
        """88-level condition equivalent: CDEMO-USRTYP-ADMIN VALUE 'A'."""
        return self.user_type == USER_TYPE_ADMIN
