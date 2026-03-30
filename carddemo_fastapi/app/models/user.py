"""User (security) model.

Derived from COBOL copybook: USRSEC (COUSR.CPY).
Maps the application user / security record used for authentication
and role-based access control in the CardDemo application.
"""

from sqlalchemy import Column, String

from app.database import Base


class User(Base):
    """Application user / security record.

    Corresponds to the VSAM KSDS file USRSEC keyed by USR-ID
    as defined in COUSR.CPY.  The usr_type field distinguishes
    administrators ('A') from regular users ('U').
    """

    __tablename__ = "users"

    # PIC X(8) - User identifier
    usr_id = Column(String(8), primary_key=True)

    # PIC X(20) - First name
    usr_fname = Column(String(20), nullable=False)

    # PIC X(20) - Last name
    usr_lname = Column(String(20), nullable=False)

    # PIC X(8) - Password
    usr_pwd = Column(String(8), nullable=False)

    # PIC X(1) - User type: 'A' (Admin) or 'U' (User)
    usr_type = Column(String(1), nullable=False)

    def __repr__(self) -> str:
        return (
            f"<User(usr_id='{self.usr_id}', "
            f"name='{self.usr_fname} {self.usr_lname}', "
            f"type='{self.usr_type}')>"
        )
