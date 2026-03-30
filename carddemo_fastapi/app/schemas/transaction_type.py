"""Transaction type schemas matching COBOL CVTRA03Y.cpy and COTRTLIC/COTRTUPC screens.

- TransactionTypeItem: list/read display from COTRTLIC columns
- TransactionTypeCreate: new transaction type input from COTRTUPC
- TransactionTypeUpdate: transaction type update from COTRTUPC
"""

from pydantic import BaseModel, Field


class TransactionTypeItem(BaseModel):
    """Transaction type item matching COTRTLIC screen columns.

    Fields from CVTRA03Y.cpy TRAN-TYPE-RECORD (RECLN 60).
    """

    tran_type: str = Field(
        ..., max_length=2, description="Transaction type code (TRAN-TYPE PIC X(02))"
    )
    tran_type_desc: str = Field(
        ..., max_length=50, description="Type description (TRAN-TYPE-DESC PIC X(50))"
    )


class TransactionTypeCreate(BaseModel):
    """New transaction type input matching COTRTUPC create mode."""

    tran_type: str = Field(
        ..., max_length=2, description="Transaction type code (TRAN-TYPE PIC X(02))"
    )
    tran_type_desc: str = Field(
        ..., max_length=50, description="Type description (TRAN-TYPE-DESC PIC X(50))"
    )


class TransactionTypeUpdate(BaseModel):
    """Transaction type update matching COTRTUPC update mode.

    Type code is immutable; only description can be changed.
    """

    tran_type_desc: str = Field(
        ..., max_length=50, description="Type description (TRAN-TYPE-DESC PIC X(50))"
    )
