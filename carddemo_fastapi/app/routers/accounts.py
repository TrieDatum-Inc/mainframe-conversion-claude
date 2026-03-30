"""Account router porting COBOL programs COACTVWC and COACTUP.

COACTVWC displays account details joined with customer data by reading
ACCTDAT (CVACT01Y.cpy) and CUSTDAT (CVCUS01Y.cpy) via the XREFDAT
cross-reference file.

COACTUP allows updates to account and customer fields, validating each
field before writing back to the VSAM files.

This router replaces both screens with REST endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.account import AccountUpdate, AccountView
from app.schemas.common import MessageResponse
from app.services import account_service

router = APIRouter(tags=["accounts"])


@router.get("/{acct_id}", response_model=AccountView)
def get_account(
    acct_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> AccountView:
    """Retrieve account details with joined customer information.

    Ports COBOL program COACTVWC which reads the ACCTDAT and CUSTDAT
    VSAM files and displays the combined account/customer view.
    """
    return account_service.get_account_view(db, acct_id)


@router.put("/{acct_id}", response_model=MessageResponse)
def update_account(
    acct_id: int,
    body: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> MessageResponse:
    """Update account and/or customer fields.

    Ports COBOL program COACTUP which validates and writes changes to
    the ACCTDAT and CUSTDAT VSAM files. Only non-None fields are applied.
    """
    return account_service.update_account(db, acct_id, body.model_dump(exclude_unset=True))
