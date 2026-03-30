"""Card schemas matching COBOL CVACT02Y.cpy and COCRDLIC/COCRDSLC/COCRDUPC screens.

- CardListItem: list columns from COCRDLIC screen
- CardDetail: full card detail from COCRDSLC output
- CardUpdate: editable fields from COCRDUPC input
"""

from typing import Optional

from pydantic import BaseModel, Field


class CardListItem(BaseModel):
    """Card list item matching COCRDLIC screen columns.

    Fields from CVACT02Y.cpy CARD-RECORD (RECLN 150).
    """

    card_num: str = Field(..., max_length=16, description="Card number (CARD-NUM PIC X(16))")
    card_acct_id: int = Field(..., description="Account ID (CARD-ACCT-ID PIC 9(11))")
    card_active_status: str = Field(
        ..., max_length=1, description="Active status Y/N (CARD-ACTIVE-STATUS PIC X(01))"
    )
    card_expiration_date: str = Field(
        ..., max_length=10, description="Expiration date (CARD-EXPIRAION-DATE PIC X(10))"
    )


class CardDetail(BaseModel):
    """Full card detail matching COCRDSLC output.

    All fields from CVACT02Y.cpy CARD-RECORD (RECLN 150).
    """

    card_num: str = Field(..., max_length=16, description="Card number (CARD-NUM PIC X(16))")
    card_acct_id: int = Field(..., description="Account ID (CARD-ACCT-ID PIC 9(11))")
    card_cvv_cd: int = Field(..., description="CVV code (CARD-CVV-CD PIC 9(03))")
    card_embossed_name: str = Field(
        ..., max_length=50, description="Embossed name (CARD-EMBOSSED-NAME PIC X(50))"
    )
    card_expiration_date: str = Field(
        ..., max_length=10, description="Expiration date (CARD-EXPIRAION-DATE PIC X(10))"
    )
    card_active_status: str = Field(
        ..., max_length=1, description="Active status Y/N (CARD-ACTIVE-STATUS PIC X(01))"
    )


class CardUpdate(BaseModel):
    """Card update matching COCRDUPC input. Only non-None fields are applied."""

    card_embossed_name: Optional[str] = Field(
        None, max_length=50, description="Embossed name"
    )
    card_active_status: Optional[str] = Field(
        None, max_length=1, description="Active status Y/N"
    )
    card_expiration_date: Optional[str] = Field(
        None, max_length=10, description="Expiration date"
    )
