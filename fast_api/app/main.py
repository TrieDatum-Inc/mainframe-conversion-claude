"""
CardDemo FastAPI Application
Converted from IBM z/OS COBOL/CICS mainframe application.

Original system: CardDemo by AWS Mainframe Modernization
Converted to: FastAPI + PostgreSQL + async SQLAlchemy

Programs covered:
  Online (CICS):
    COSGN00C  -> POST /auth/login
    COMEN01C  -> (menu navigation, replaced by REST routing)
    COADM01C  -> (admin navigation, replaced by role-based auth)
    COACTVWC  -> GET /accounts/{acct_id}
    COACTUPC  -> PUT /accounts/{acct_id}
    COCRDLIC  -> GET /cards
    COCRDSLC  -> GET /cards/{card_num}
    COCRDUPC  -> PUT /cards/{card_num}
    COTRN00C  -> GET /transactions
    COTRN01C  -> GET /transactions/{tran_id}
    COTRN02C  -> POST /transactions
    COBIL00C  -> POST /billing/pay
    CORPT00C  -> POST /reports/generate
    COUSR00C  -> GET /users
    COUSR01C  -> POST /users
    COUSR02C  -> PUT /users/{usr_id}
    COUSR03C  -> DELETE /users/{usr_id}
    COPAUS0C  -> GET /authorizations
    COPAUS1C  -> GET /authorizations/{acct_id}/details
    COPAUS2C  -> POST /authorizations/fraud-flag
    COPAUA0C  -> POST /authorizations/process
    COTRTLIC  -> GET /transaction-types
    COTRTUPC  -> POST/PUT/DELETE /transaction-types

"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import (
    account_routes,
    auth_routes,
    authorization_routes,
    card_routes,
    tran_type_routes,
    transaction_routes,
    user_routes,
)
from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessValidationError,
    CardDemoBaseError,
    DuplicateKeyError,
    FileIOError,
    RecordLockedError,
    ResourceNotFoundError,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup/shutdown lifecycle."""
    # Startup: verify database connectivity
    from app.infrastructure.database import engine
    async with engine.connect() as conn:
        await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
    yield
    # Shutdown: dispose engine
    await engine.dispose()


app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description="""
    CardDemo REST API — converted from IBM z/OS COBOL/CICS mainframe application.

    ## System Architecture

    This API replaces the CardDemo mainframe application which consisted of:
    - **CICS Online Subsystem**: 17 online programs for real-time card/account/transaction management
    - **Authorization Subsystem**: IMS/DB2/MQ programs for pending card authorization management
    - **Transaction Type DB2 Subsystem**: DB2-based transaction type code maintenance

    ## Data Storage

    All VSAM KSDS files, DB2 tables, and IMS databases are replaced by PostgreSQL:
    - `accounts` <- ACCTDAT VSAM (CVACT01Y)
    - `customers` <- CUSTDAT VSAM (CVCUS01Y)
    - `cards` <- CARDDAT VSAM (CVACT02Y)
    - `card_xref` <- CXACAIX VSAM AIX (CVACT03Y)
    - `transactions` <- TRANSACT VSAM (CVTRA05Y)
    - `users` <- USRSEC VSAM (CSUSR01Y)
    - `transaction_types` <- DB2 CARDDEMO.TRANSACTION_TYPE
    - `auth_summary` / `auth_detail` <- IMS PAUT database (CIPAUSMY/CIPAUDTY)
    - `auth_fraud` <- DB2 CARDDEMO.AUTHFRDS

    ## Authentication

    JWT Bearer token auth (replaces COSGN00C plain-text USRSEC comparison).
    User type 'A' = Admin (access to all endpoints).
    User type 'U' = Regular User (no user management).
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers — map CardDemo exceptions to HTTP responses
@app.exception_handler(ResourceNotFoundError)
async def not_found_handler(request: Request, exc: ResourceNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error_code": exc.error_code, "message": exc.message},
    )


@app.exception_handler(DuplicateKeyError)
async def duplicate_key_handler(request: Request, exc: DuplicateKeyError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"error_code": exc.error_code, "message": exc.message},
    )


@app.exception_handler(RecordLockedError)
async def locked_handler(request: Request, exc: RecordLockedError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"error_code": exc.error_code, "message": exc.message},
    )


@app.exception_handler(AuthenticationError)
async def auth_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"error_code": exc.error_code, "message": exc.message},
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(AuthorizationError)
async def authz_handler(request: Request, exc: AuthorizationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"error_code": exc.error_code, "message": exc.message},
    )


@app.exception_handler(BusinessValidationError)
async def validation_handler(request: Request, exc: BusinessValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error_code": exc.error_code, "message": exc.message, "field": exc.field},
    )


@app.exception_handler(FileIOError)
async def file_io_handler(request: Request, exc: FileIOError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": exc.error_code,
            "message": exc.message,
            "operation": exc.operation,
            "filename": exc.filename,
        },
    )


# Register all routers
app.include_router(auth_routes.router)
app.include_router(account_routes.router)
app.include_router(card_routes.router)
app.include_router(transaction_routes.router)
app.include_router(transaction_routes.billing_router)
app.include_router(transaction_routes.report_router)
app.include_router(user_routes.router)
app.include_router(tran_type_routes.router)
app.include_router(authorization_routes.router)


@app.get("/", tags=["Health"])
async def root() -> dict:
    """Health check endpoint."""
    return {
        "application": settings.app_applid,
        "system_id": settings.app_sysid,
        "version": settings.app_version,
        "status": "UP",
        "description": "CardDemo REST API - AWS Mainframe Modernization",
    }


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Detailed health check."""
    return {
        "status": "healthy",
        "applid": settings.app_applid,
        "sysid": settings.app_sysid,
    }
