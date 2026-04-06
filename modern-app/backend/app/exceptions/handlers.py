"""Custom exception classes for the transaction module.

Error messages are derived directly from the COBOL source:
  COBIL00C error table and CSMSG01Y standard messages.
"""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


class TransactionNotFoundError(HTTPException):
    """Raised when a transaction ID is not found in TRANSACT.

    COBOL equivalent: NOTFND condition on TRANSACT READ.
    HTTP 404 — maps to COBOL response code 'NOT FOUND'.
    """

    def __init__(self, transaction_id: str) -> None:
        super().__init__(
            status_code=404,
            detail=f"Transaction ID '{transaction_id}' not found",
        )


class AccountNotFoundError(HTTPException):
    """Raised when account_id is not found in ACCTDAT.

    COBOL equivalent: NOTFND condition on ACCTDAT READ.
    COBIL00C message: "Account ID NOT found"
    HTTP 404.
    """

    def __init__(self, account_id: str) -> None:
        super().__init__(
            status_code=404,
            detail=f"Account ID '{account_id}' not found",
        )


class CardNotFoundError(HTTPException):
    """Raised when card/xref lookup fails.

    COBOL equivalent: NOTFND on CCXREF or CXACAIX.
    HTTP 404.
    """

    def __init__(self, identifier: str) -> None:
        super().__init__(
            status_code=404,
            detail=f"Card or cross-reference not found for '{identifier}'",
        )


class NothingToPayError(HTTPException):
    """Raised when account balance <= 0 during bill payment.

    COBOL equivalent: COBIL00C "You have nothing to pay"
    HTTP 422 (unprocessable — business rule violation).
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=422,
            detail="You have nothing to pay",
        )


class TransactionWriteError(HTTPException):
    """Raised when TRANSACT WRITE fails.

    COBOL equivalent: COBIL00C "Unable to Add Bill pay Transaction"
    HTTP 500.
    """

    def __init__(self, message: str = "Unable to write transaction record") -> None:
        super().__init__(status_code=500, detail=message)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unexpected server errors."""
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again."},
    )
