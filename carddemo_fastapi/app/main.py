"""CardDemo FastAPI Application.

Migrated from COBOL/CICS mainframe application to Python FastAPI.
This is the main entry point that wires all routers, exception handlers,
and middleware together.

Original COBOL Programs Mapped:
- COSGN00C → /api/auth/login
- COMEN01C, COADM01C → /api/menu/*
- COACTVWC, COACTUPC → /api/accounts/*
- COCRDLIC, COCRDSLC, COCRDUPC → /api/cards/*
- COTRN00C, COTRN01C, COTRN02C → /api/transactions/*
- COUSR00C-03C → /api/users/*
- COBIL00C → /api/bill-payment
- CORPT00C → /api/reports
- COPAUA0C, COPAUS0C-2C → /api/authorizations/*
- COTRTLIC, COTRTUPC → /api/transaction-types/*
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.exceptions import (
    RecordNotFoundError,
    DuplicateRecordError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    DatabaseError,
    record_not_found_handler,
    duplicate_record_handler,
    validation_error_handler,
    authentication_error_handler,
    authorization_error_handler,
    database_error_handler,
)
from app.routers import (
    auth,
    accounts,
    cards,
    transactions,
    users,
    bill_payment,
    reports,
    authorizations,
    transaction_types,
)

app = FastAPI(
    title="CardDemo API",
    description=(
        "CardDemo credit card management system migrated from "
        "COBOL/CICS to Python FastAPI. Preserves all original "
        "business logic, validations, and error handling."
    ),
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register custom exception handlers (maps COBOL error message patterns)
app.add_exception_handler(RecordNotFoundError, record_not_found_handler)
app.add_exception_handler(DuplicateRecordError, duplicate_record_handler)
app.add_exception_handler(ValidationError, validation_error_handler)
app.add_exception_handler(AuthenticationError, authentication_error_handler)
app.add_exception_handler(AuthorizationError, authorization_error_handler)
app.add_exception_handler(DatabaseError, database_error_handler)

# Register routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(accounts.router, prefix="/api/accounts", tags=["Accounts"])
app.include_router(cards.router, prefix="/api/cards", tags=["Cards"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["Transactions"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(bill_payment.router, prefix="/api/bill-payment", tags=["Bill Payment"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(authorizations.router, prefix="/api/authorizations", tags=["Authorizations"])
app.include_router(
    transaction_types.router,
    prefix="/api/transaction-types",
    tags=["Transaction Types"],
)


@app.get("/", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "application": "CardDemo API",
        "version": "1.0.0",
    }
