"""Disclosure group model.

Derived from COBOL copybook: DISCGRP (DISCGRP.CPY).
Maps the disclosure / interest-rate group record that associates
account groups with transaction-type-specific interest rates
in the CardDemo application.
"""

from sqlalchemy import Column, Integer, Numeric, String

from app.database import Base


class DisclosureGroup(Base):
    """Disclosure / interest-rate group record.

    Corresponds to the VSAM KSDS file DISCGRP with a composite key
    of DIS-ACCT-GROUP-ID + DIS-TRAN-TYPE-CD + DIS-TRAN-CAT-CD
    as defined in DISCGRP.CPY.
    """

    __tablename__ = "disclosure_groups"

    # PIC X(10) - Account group identifier (part of composite PK)
    dis_acct_group_id = Column(String(10), primary_key=True)

    # PIC X(2) - Transaction type code (part of composite PK)
    dis_tran_type_cd = Column(String(2), primary_key=True)

    # PIC 9(4) - Transaction category code (part of composite PK)
    dis_tran_cat_cd = Column(Integer, primary_key=True)

    # PIC S9(4)V99 - Interest rate
    dis_int_rate = Column(Numeric(6, 2))

    def __repr__(self) -> str:
        return (
            f"<DisclosureGroup(group='{self.dis_acct_group_id}', "
            f"type='{self.dis_tran_type_cd}', "
            f"cat={self.dis_tran_cat_cd}, "
            f"rate={self.dis_int_rate})>"
        )
