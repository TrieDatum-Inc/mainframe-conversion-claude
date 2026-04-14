# API Service Architecture Specification
# CardDemo Mainframe Modernization

## Document Purpose

This document defines the complete FastAPI project architecture for the CardDemo modernization. It covers directory structure, module organization, the layered service/repository/router pattern, session management, background task processing, and the mapping from COBOL program structure to Python module structure.

---

## 1. Architecture Overview

The backend follows a strict four-layer clean architecture that maps directly to the COBOL program structure:

| Layer | Python Module | COBOL Equivalent |
|-------|--------------|-----------------|
| API Endpoints | `app/api/endpoints/` | CICS SEND/RECEIVE MAP + AID key dispatch |
| Services | `app/services/` | PROCEDURE DIVISION paragraphs containing business logic |
| Repositories | `app/repositories/` | CICS READ/WRITE/DELETE/REWRITE + EXEC SQL + IMS GU/GN/REPL |
| Models | `app/models/` | VSAM record layouts, DB2 table definitions, IMS segment copybooks |

**Rule:** No business logic in endpoints. No database calls in services. Services only call repositories.

---

## 2. Complete Directory Structure

```
backend/
├── pyproject.toml
├── poetry.lock
├── alembic.ini
├── README.md
│
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 001_initial_schema.py
│
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app factory; lifespan; middleware registration
│   ├── config.py                  # Settings via pydantic-settings; env vars
│   ├── database.py                # SQLAlchemy async engine; session factory; get_db dependency
│   │
│   ├── models/                    # SQLAlchemy ORM models (COBOL data structure equivalents)
│   │   ├── __init__.py
│   │   ├── user.py                # USRSEC VSAM → users table (COUSR01Y / CSUSR01Y)
│   │   ├── account.py             # ACCTDAT VSAM → accounts table (CVACT01Y)
│   │   ├── customer.py            # CUSTDAT VSAM → customers table (CVCUS01Y)
│   │   ├── credit_card.py         # CARDDAT VSAM → credit_cards table (CVACT03Y)
│   │   ├── card_xref.py           # CARDXREF VSAM → card_account_xref table (CVCRD01Y)
│   │   ├── transaction.py         # TRANSACT VSAM → transactions table (DALYTRAN/TRNX01Y)
│   │   ├── transaction_type.py    # DB2 TRANSACTION_TYPE → transaction_types table
│   │   ├── authorization.py       # IMS PAUTDTL1 + DB2 AUTHFRDS → authorizations table
│   │   ├── report_request.py      # New: report_requests table (replaces JCL batch trigger)
│   │   └── audit_log.py           # New: audit_log table (replaces DISPLAY/sysprint statements)
│   │
│   ├── schemas/                   # Pydantic request/response DTOs
│   │   ├── __init__.py
│   │   ├── common.py              # Shared: PaginatedResponse, ErrorResponse, MessageResponse
│   │   ├── auth.py                # LoginRequest, LoginResponse, TokenPayload
│   │   ├── user.py                # UserBase, UserCreate, UserUpdate, UserResponse, UserListResponse
│   │   ├── account.py             # AccountViewResponse, AccountUpdateRequest, CustomerUpdateRequest
│   │   ├── credit_card.py         # CardResponse, CardUpdateRequest, CardListResponse
│   │   ├── transaction.py         # TransactionResponse, TransactionCreate, TransactionListResponse
│   │   ├── transaction_type.py    # TransactionTypeResponse, TransactionTypeCreate, TransactionTypeUpdate
│   │   ├── authorization.py       # AuthorizationResponse, AuthorizationListResponse, FraudToggleRequest
│   │   ├── billing.py             # BalanceResponse, PaymentRequest, PaymentResponse
│   │   ├── report.py              # ReportRequest, ReportResponse
│   │   └── menu.py                # MenuResponse (for dynamic menu endpoint)
│   │
│   ├── repositories/              # Data access layer — all SQLAlchemy queries
│   │   ├── __init__.py
│   │   ├── base.py                # BaseRepository with common CRUD methods
│   │   ├── user_repository.py     # Maps to CICS READ/WRITE/REWRITE/DELETE DATASET(USRSEC)
│   │   ├── account_repository.py  # Maps to CICS READ/WRITE DATASET(ACCTDAT)
│   │   ├── customer_repository.py # Maps to CICS READ/WRITE DATASET(CUSTDAT)
│   │   ├── credit_card_repository.py # Maps to CICS READ/WRITE DATASET(CARDDAT)
│   │   ├── card_xref_repository.py   # Maps to CICS READ DATASET(CARDXREF) / BROWSE
│   │   ├── transaction_repository.py # Maps to CICS STARTBR/READNEXT/READPREV/ENDBR DATASET(TRANSACT) + DB2 cursor
│   │   ├── transaction_type_repository.py # Maps to EXEC SQL SELECT/INSERT/UPDATE/DELETE TRANSACTION_TYPE
│   │   ├── authorization_repository.py    # Maps to IMS GU/GN/REPL + DB2 AUTHFRDS
│   │   ├── billing_repository.py          # Derived from COBIL00C MQ request/reply pattern
│   │   └── report_repository.py           # Report request storage
│   │
│   ├── services/                  # Business logic — ALL COBOL paragraph logic lives here
│   │   ├── __init__.py
│   │   ├── auth_service.py        # COSGN00C: credential validation + JWT issuance
│   │   ├── user_service.py        # COUSR01C/02C/03C/00C: user CRUD + validation
│   │   ├── account_service.py     # COACTVWC/COACTUPC: account view/update logic
│   │   ├── credit_card_service.py # COCRDLIC/COCRDSLIC/COCRDUPD: card list/view/update
│   │   ├── transaction_service.py # COTRN00C/01C/02C: transaction list/view/add
│   │   ├── transaction_type_service.py # COTRTLIC/COTRTUPC: type CRUD + state machine
│   │   ├── authorization_service.py    # COPAUS0C/1C/2C: auth list/detail/fraud toggle
│   │   ├── billing_service.py          # COBIL00C: balance fetch + payment processing
│   │   ├── report_service.py           # CORPT00C: report request creation
│   │   ├── menu_service.py             # COMEN01C/COADM01C: menu option resolution
│   │   └── date_service.py             # CSUTLDTC: date validation utility
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py              # Master router: aggregates all sub-routers
│   │   └── endpoints/
│   │       ├── __init__.py
│   │       ├── auth.py            # POST /auth/login, POST /auth/logout
│   │       ├── users.py           # GET/POST /users, GET/PUT/DELETE /users/{user_id}
│   │       ├── accounts.py        # GET /accounts/{id}, PUT /accounts/{id}
│   │       ├── credit_cards.py    # GET /cards, GET/PUT /cards/{card_number}
│   │       ├── transactions.py    # GET /transactions, GET /transactions/{id}, POST /transactions
│   │       ├── transaction_types.py # GET/POST /transaction-types, PUT/DELETE /transaction-types/{code}
│   │       ├── authorizations.py  # GET /authorizations, GET /authorizations/{id}, PUT /authorizations/{id}/fraud
│   │       ├── billing.py         # GET /billing/{id}/balance, POST /billing/{id}/payment
│   │       ├── reports.py         # POST /reports/request
│   │       ├── menus.py           # GET /menus/main, GET /menus/admin
│   │       └── system.py          # GET /system/date-time
│   │
│   ├── exceptions/
│   │   ├── __init__.py
│   │   ├── handlers.py            # Global exception handlers registered on FastAPI app
│   │   └── errors.py              # Custom exception classes
│   │
│   └── utils/
│       ├── __init__.py
│       ├── security.py            # JWT creation/verification; bcrypt hashing
│       ├── formatting.py          # COBOL PICOUT format equivalents (currency, date)
│       ├── pagination.py          # LIMIT/OFFSET builder; PaginatedResponse factory
│       └── validators.py          # Reusable field validators (SSN, FICO, date)
│
├── sql/
│   ├── create_tables.sql          # Full DDL for all 12 tables
│   └── seed_data.sql              # Minimum 10 rows per table
│
└── tests/
    ├── __init__.py
    ├── conftest.py                # pytest fixtures: test DB, test client, auth tokens
    ├── test_models/
    │   ├── __init__.py
    │   └── test_all_models.py
    ├── test_repositories/
    │   ├── __init__.py
    │   ├── test_user_repository.py
    │   ├── test_account_repository.py
    │   └── test_transaction_repository.py
    ├── test_services/
    │   ├── __init__.py
    │   ├── test_auth_service.py
    │   ├── test_user_service.py
    │   ├── test_account_service.py
    │   ├── test_credit_card_service.py
    │   ├── test_transaction_service.py
    │   └── test_transaction_type_service.py
    └── test_api/
        ├── __init__.py
        ├── test_auth_endpoints.py
        ├── test_user_endpoints.py
        ├── test_account_endpoints.py
        ├── test_transaction_endpoints.py
        └── test_transaction_type_endpoints.py
```

---

## 3. Poetry Project Configuration

**File:** `backend/pyproject.toml`

```toml
[tool.poetry]
name = "carddemo-backend"
version = "1.0.0"
description = "CardDemo mainframe modernization — FastAPI backend"
authors = ["CardDemo Team"]
python = "^3.11"

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.111.0"
uvicorn = {extras = ["standard"], version = "^0.29.0"}
sqlalchemy = {extras = ["asyncio"], version = "^2.0.0"}
asyncpg = "^0.29.0"          # async PostgreSQL driver
psycopg2-binary = "^2.9.0"   # sync driver for Alembic
pydantic = {extras = ["email"], version = "^2.7.0"}
pydantic-settings = "^2.2.0"
alembic = "^1.13.0"
python-jose = {extras = ["cryptography"], version = "^3.3.0"}  # JWT
passlib = {extras = ["bcrypt"], version = "^1.7.4"}             # bcrypt
python-multipart = "^0.0.9"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
pytest-asyncio = "^0.23.0"
pytest-cov = "^5.0.0"
httpx = "^0.27.0"          # async test client
black = "^24.0.0"
ruff = "^0.4.0"
mypy = "^1.9.0"
factory-boy = "^3.3.0"    # test data factories

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.black]
line-length = 100

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W"]
```

---

## 4. Application Factory

**File:** `app/main.py`

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings
from app.database import init_db
from app.exceptions.handlers import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management — replaces CICS PLTPI initialization."""
    await init_db()
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="CardDemo API",
        description="Modernized CardDemo mainframe application",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")
    register_exception_handlers(app)

    return app


app = create_app()
```

---

## 5. Configuration

**File:** `app/config.py`

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database (replaces CICS FILE CONTROL definitions)
    database_url: str = "postgresql+asyncpg://carddemo:carddemo@localhost:5432/carddemo"
    database_url_sync: str = "postgresql://carddemo:carddemo@localhost:5432/carddemo"

    # Security (replaces USRSEC plain-text password comparison)
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Application (mirrors COTTL01Y constants)
    app_title_line1: str = "AWS Mainframe Cloud Demo"
    app_title_line2: str = "Credit Card Demo Application"

    class Config:
        env_file = ".env"


settings = Settings()
```

---

## 6. Database Session Management

**File:** `app/database.py`

```python
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a database session.

    Replaces CICS HANDLE CONDITION / RESP handling pattern.
    The session is automatically committed on success and rolled back on exception.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Initialize database connection on startup."""
    async with engine.begin() as conn:
        pass  # Connection validation only; schema managed by Alembic
```

---

## 7. Layered Architecture Patterns

### 7.1 Base Repository

**File:** `app/repositories/base.py`

```python
from typing import Generic, TypeVar
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Base repository providing common CRUD operations.

    Maps to: CICS READ/WRITE/REWRITE/DELETE commands
    All VSAM file operations are replaced by these methods.
    """

    def __init__(self, model: type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_by_id(self, record_id: str) -> ModelType | None:
        """
        COBOL equivalent: EXEC CICS READ DATASET(file) INTO(record) RIDFLD(key)
        Returns None if not found (replaces RESP=DFHRESP(NOTFND) handling).
        """
        result = await self.db.execute(select(self.model).where(self.model.id == record_id))
        return result.scalar_one_or_none()

    async def get_paginated(
        self,
        page: int = 1,
        per_page: int = 10,
        order_by=None
    ) -> tuple[list[ModelType], int]:
        """
        COBOL equivalent: EXEC CICS STARTBR + READNEXT (per_page times) + ENDBR
        Returns (records, total_count) for pagination envelope construction.
        """
        offset = (page - 1) * per_page
        count_query = select(func.count()).select_from(self.model)
        total = (await self.db.execute(count_query)).scalar_one()

        query = select(self.model)
        if order_by is not None:
            query = query.order_by(order_by)
        query = query.offset(offset).limit(per_page)

        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def create(self, obj: ModelType) -> ModelType:
        """
        COBOL equivalent: EXEC CICS WRITE DATASET(file) FROM(record) RIDFLD(key)
        """
        self.db.add(obj)
        await self.db.flush()
        return obj

    async def update(self, obj: ModelType) -> ModelType:
        """
        COBOL equivalent: EXEC CICS REWRITE DATASET(file) FROM(record)
        Requires prior READ UPDATE lock — here enforced by optimistic locking in service layer.
        """
        await self.db.flush()
        return obj

    async def delete(self, obj: ModelType) -> None:
        """
        COBOL equivalent: EXEC CICS DELETE DATASET(file) RIDFLD(key)
        """
        await self.db.delete(obj)
        await self.db.flush()
```

### 7.2 Service Layer Pattern

Each service method corresponds to a COBOL paragraph. The docstring always references the COBOL paragraph name and program for traceability.

```python
# Pattern for all service methods
class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def get_user_for_display(self, user_id: str) -> UserResponse:
        """
        Maps to COUSR03C PROCESS-ENTER-KEY paragraph (lines 142-169).
        COBOL: MOVE USRIDINI to SEC-USR-ID; PERFORM READ-USER-SEC-FILE
        Returns user data for display without password.
        Raises NotFoundError if user not in USRSEC.
        """
        user = await self.user_repo.get_by_user_id(user_id)
        if user is None:
            raise NotFoundError(f"User ID NOT found: {user_id}")
        return UserResponse.from_orm(user)

    async def delete_user(self, user_id: str) -> None:
        """
        Maps to COUSR03C DELETE-USER-INFO paragraph (lines 174-192).
        COBOL: PERFORM READ-USER-SEC-FILE; PERFORM DELETE-USER-SEC-FILE
        Note: COBOL re-reads before delete to reacquire UPDATE lock.
        In SQL, DELETE is atomic — no pre-read lock required.
        """
        user = await self.user_repo.get_by_user_id(user_id)
        if user is None:
            raise NotFoundError(f"User ID NOT found: {user_id}")
        await self.user_repo.delete(user)
```

### 7.3 Endpoint Layer Pattern

Endpoints are thin — they validate HTTP concerns, call the service, and return the response.

```python
# Pattern for all endpoints
@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    current_user: TokenPayload = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Replaces COUSR03C transaction CU03 PF5 action.
    Admin only. Returns 204 No Content on success.
    """
    service = UserService(UserRepository(db))
    await service.delete_user(user_id)
```

---

## 8. Exception Handling

**File:** `app/exceptions/errors.py`

```python
class CardDemoError(Exception):
    """Base exception for all CardDemo business errors."""
    pass

class NotFoundError(CardDemoError):
    """
    Maps to CICS RESP=DFHRESP(NOTFND).
    HTTP 404.
    """
    pass

class DuplicateKeyError(CardDemoError):
    """
    Maps to CICS RESP=DFHRESP(DUPREC).
    HTTP 409.
    """
    pass

class ValidationError(CardDemoError):
    """
    Maps to business rule validation failures (WS-ERR-FLG ON).
    HTTP 422.
    """
    pass

class OptimisticLockError(CardDemoError):
    """
    Maps to COCRDUPC 7-state optimistic locking.
    HTTP 409.
    """
    pass

class UnauthorizedError(CardDemoError):
    """
    Maps to COSGN00C authentication failure.
    HTTP 401.
    """
    pass

class ForbiddenError(CardDemoError):
    """
    Maps to admin-only function access without admin type.
    HTTP 403.
    """
    pass
```

**File:** `app/exceptions/handlers.py`

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions.errors import (
    NotFoundError, DuplicateKeyError, ValidationError,
    OptimisticLockError, UnauthorizedError, ForbiddenError,
)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register global exception handlers.
    Maps CICS RESP/RESP2 error handling to HTTP status codes.
    """

    @app.exception_handler(NotFoundError)
    async def handle_not_found(request: Request, exc: NotFoundError):
        return JSONResponse(
            status_code=404,
            content={"error_code": "NOT_FOUND", "message": str(exc), "details": []}
        )

    @app.exception_handler(DuplicateKeyError)
    async def handle_duplicate_key(request: Request, exc: DuplicateKeyError):
        return JSONResponse(
            status_code=409,
            content={"error_code": "DUPLICATE_KEY", "message": str(exc), "details": []}
        )

    @app.exception_handler(ValidationError)
    async def handle_validation(request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=422,
            content={"error_code": "VALIDATION_ERROR", "message": str(exc), "details": []}
        )

    @app.exception_handler(OptimisticLockError)
    async def handle_optimistic_lock(request: Request, exc: OptimisticLockError):
        return JSONResponse(
            status_code=409,
            content={"error_code": "CONCURRENT_MODIFICATION", "message": str(exc), "details": []}
        )

    @app.exception_handler(UnauthorizedError)
    async def handle_unauthorized(request: Request, exc: UnauthorizedError):
        return JSONResponse(
            status_code=401,
            content={"error_code": "UNAUTHORIZED", "message": str(exc), "details": []}
        )

    @app.exception_handler(ForbiddenError)
    async def handle_forbidden(request: Request, exc: ForbiddenError):
        return JSONResponse(
            status_code=403,
            content={"error_code": "FORBIDDEN", "message": str(exc), "details": []}
        )
```

---

## 9. Security Module

**File:** `app/utils/security.py`

```python
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt

from app.config import settings
from app.schemas.auth import TokenPayload


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """
    Replaces plain-text password storage in USRSEC VSAM.
    COBOL: SEC-USR-PWD PIC X(8) stored and compared in plain text.
    Modern: bcrypt hash stored; plain-text never persisted.
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Replaces COBOL: IF SEC-USR-PWD = WS-PASSWORD THEN ...
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: str, user_type: str) -> str:
    """
    Creates JWT token replacing CICS pseudo-conversational COMMAREA.
    COBOL: CDEMO-USERID and CDEMO-USRTYP stored in CARDDEMO-COMMAREA.
    JWT payload: sub=user_id, user_type=user_type, exp=<expiry>.
    """
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": user_id,
        "user_type": user_type,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> TokenPayload:
    """
    Validates JWT and extracts payload.
    Raises JWTError if token is invalid or expired.
    """
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    return TokenPayload(**payload)
```

---

## 10. Authentication Dependency

**File:** `app/api/dependencies.py`

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError

from app.schemas.auth import TokenPayload
from app.utils.security import decode_access_token


bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> TokenPayload:
    """
    JWT authentication dependency — replaces CICS COMMAREA user context.
    COBOL: CDEMO-USERID and CDEMO-USRTYP read from CARDDEMO-COMMAREA on every program entry.
    Modern: JWT token validated on every request.
    """
    try:
        token_data = decode_access_token(credentials.credentials)
        return token_data
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "INVALID_TOKEN", "message": "Invalid or expired token", "details": []}
        )


async def require_admin(
    current_user: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    """
    Admin-only access guard — replaces COBOL check: IF CDEMO-USRTYP NOT = 'A' THEN error.
    Applied to all admin function endpoints (COUSR01C/02C/03C/00C, COTRTLIC/COTRTUPC, COADM01C).
    """
    if current_user.user_type != "A":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": "FORBIDDEN", "message": "Admin access required", "details": []}
        )
    return current_user
```

---

## 11. Service Module Specifications

### 11.1 Auth Service

**File:** `app/services/auth_service.py`

Maps to: COSGN00C

**Methods:**

| Method | COBOL Paragraph | Description |
|--------|----------------|-------------|
| `authenticate_user(user_id, password)` | COSGN00C PROCESS-SIGNON | Verify credentials; raise UnauthorizedError on failure |
| `create_session_token(user)` | COSGN00C RETURN-TO-PREV-SCREEN | Issue JWT; populate user_type for routing |

**Key logic:** COSGN00C compares `SEC-USR-PWD` directly against entered password (plain text). In the modern service, `verify_password(plain, hashed)` is used. User type `A` → admin token (redirect to admin menu). User type `U` → standard token (redirect to main menu).

### 11.2 User Service

**File:** `app/services/user_service.py`

Maps to: COUSR01C, COUSR02C, COUSR03C, COUSR00C

**Methods:**

| Method | COBOL Paragraph/Program | Description |
|--------|------------------------|-------------|
| `list_users(filter_user_id, page, per_page)` | COUSR00C PROCESS-PAGE-FORWARD/BACKWARD | Paginated user list with optional ID filter |
| `get_user_for_display(user_id)` | COUSR02C/03C PROCESS-ENTER-KEY | Lookup by ID; return display fields; no password |
| `create_user(request)` | COUSR01C PROCESS-ENTER-KEY | Validate all fields; hash password; write to users |
| `update_user(user_id, request)` | COUSR02C UPDATE-USER-INFO | Field-level change detection; only update if modified |
| `delete_user(user_id)` | COUSR03C DELETE-USER-INFO | Lookup + delete (two-step COBOL pattern collapsed to atomic operation) |

**`update_user` change detection (maps to WS-USR-MODIFIED flag):**
Compare each field in `request` against current database value. If no field differs, raise `ValidationError("Please modify to update...")` with DFHRED color mapping.

### 11.3 Account Service

**File:** `app/services/account_service.py`

Maps to: COACTVWC, COACTUPC

**Methods:**

| Method | COBOL Paragraph/Program | Description |
|--------|------------------------|-------------|
| `get_account_view(account_id)` | COACTVWC READ-ACCOUNT-FILE | Read account + customer; return formatted display response |
| `update_account(account_id, request)` | COACTUPC PROCESS-ENTER-KEY | Validate all fields; detect changes (WS-DATACHANGED-FLAG); rewrite if changed |

**Date assembly from split BMS fields:** COACTUPC receives split date inputs (OPNYEAR/OPNMON/OPNDAY etc.). The service assembles these into ISO dates before validation. The repository stores dates as PostgreSQL `DATE` type.

**Cognitive complexity limit:** The COBOL COACTUPC validation paragraph has many conditions. Break into:
- `_validate_dates(year, month, day, field_name)` → validates each date group
- `_validate_financials(credit_limit, cash_limit)` → validates cash <= credit
- `_validate_fico(fico_score)` → validates 300–850 range
- `_validate_status(status)` → validates Y/N

### 11.4 Credit Card Service

**File:** `app/services/credit_card_service.py`

Maps to: COCRDLIC, COCRDSLIC, COCRDUPD

**Methods:**

| Method | COBOL Paragraph/Program | Description |
|--------|------------------------|-------------|
| `list_cards(account_id, card_number, page, per_page)` | COCRDLIC PROCESS-PAGE-FORWARD/BACKWARD | Paginated card list; optional filters |
| `get_card(card_number)` | COCRDSLIC READ-CARD-FILE | Fetch single card by card number |
| `update_card(card_number, request, optimistic_lock_version)` | COCRDUPD UPDATE-CARD-DETAILS | Field validation; optimistic lock check; update |

**Optimistic locking (maps to COCRDUPC 7-state machine):** The `updated_at` timestamp of the fetched record is returned to the client as `optimistic_lock_version`. On PUT, compare provided version against current DB value. If mismatch: raise `OptimisticLockError`.

**EXPDAY hidden field:** The card record stores `expiry_day`. The GET response includes it. The PUT request must include it (even though the user never sees it). The service preserves the day when assembling the full expiry date from month+year+day.

### 11.5 Transaction Service

**File:** `app/services/transaction_service.py`

Maps to: COTRN00C, COTRN01C, COTRN02C

**Methods:**

| Method | COBOL Paragraph/Program | Description |
|--------|------------------------|-------------|
| `list_transactions(filter_id, page, per_page)` | COTRN00C PROCESS-PAGE-FORWARD/BACKWARD | Paginated; optional ID filter |
| `get_transaction(transaction_id)` | COTRN01C PROCESS-ENTER-KEY | Fetch by ID; no READ UPDATE lock |
| `get_last_transaction(user_id)` | COTRN02C COPY-LAST-TRANSACTION | Retrieve most recent transaction for PF5 copy |
| `create_transaction(request)` | COTRN02C PROCESS-ENTER-KEY | Validate; resolve account from card or vice versa; insert with generated ID |

**Transaction ID generation (fixes COTRN02C race condition):** COBOL uses STARTBR+READPREV+ADD1. Replace with PostgreSQL sequence: `NEXTVAL('transaction_id_seq')`.

**Mutual exclusivity of account_id and card_number:** At least one must be provided. If card_number provided: look up account via CARDXREF (equivalent of CICS READ DATASET(CARDXREF)). If both provided: validate card belongs to account.

### 11.6 Transaction Type Service

**File:** `app/services/transaction_type_service.py`

Maps to: COTRTLIC, COTRTUPC

**Methods:**

| Method | COBOL Paragraph/Program | Description |
|--------|------------------------|-------------|
| `list_transaction_types(type_code, description, page, per_page)` | COTRTLIC 9000-READ-DB2-TABLE | Filtered paginated list; description uses LIKE |
| `get_transaction_type(type_code)` | COTRTUPC 9000-READ-TRANTYPE | Fetch by type code |
| `create_transaction_type(request)` | COTRTUPC 9600-WRITE-PROCESSING (INSERT branch) | Validate; insert |
| `update_transaction_type(type_code, request)` | COTRTUPC 9600-WRITE-PROCESSING (UPDATE branch) | Change detection; deadlock handling |
| `delete_transaction_type(type_code)` | COTRTUPC 9800-DELETE-PROCESSING | Check FK violations (SQLCODE -532); delete |

**State machine:** The COTRTUPC 15-state machine is server-side. The API is stateless; the state is managed by the frontend. The backend validates the operation is valid (e.g., cannot delete a code that has child records) and returns appropriate errors.

**Description filter:** TRDESC value is wrapped with `%` on both sides for DB2 LIKE pattern. In SQLAlchemy: `ilike(f"%{description}%")`.

**No-change detection:** `update_transaction_type` compares submitted description against current database value. If identical: raise `ValidationError("No change detected with respect to database values.")`.

### 11.7 Authorization Service

**File:** `app/services/authorization_service.py`

Maps to: COPAUS0C, COPAUS1C, COPAUS2C

**Methods:**

| Method | COBOL Paragraph/Program | Description |
|--------|------------------------|-------------|
| `list_authorizations(account_id, page, per_page)` | COPAUS0C READ-IMS-SUMMARY + READ-IMS-DETAILS | Account summary + paginated auth list |
| `get_authorization(auth_id)` | COPAUS1C POPULATE-DETAIL-SCREEN | Full detail including merchant; resolve reason description from table |
| `toggle_fraud(auth_id)` | COPAUS2C PROCESS-FRAUD-UPDATE | Atomic toggle of fraud flag + upsert into authorization_fraud_records |

**Decline reason table (replaces COPAUS1C inline WS-DECLINE-REASONS SEARCH ALL):**

The 10-entry reason table is replicated in the service layer as a Python dict:

```python
DECLINE_REASONS: dict[str, str] = {
    "00": "APPROVED",
    "01": "DO NOT HONOR",
    "05": "DO NOT HONOR",
    "14": "INVALID CARD NUMBER",
    "51": "INSUFFICIENT FUNDS",
    "54": "EXPIRED CARD",
    "57": "TRANSACTION NOT PERMITTED",
    "62": "RESTRICTED CARD",
    "65": "WITHDRAWAL LIMIT EXCEEDED",
    "91": "ISSUER UNAVAILABLE",
}
```

**COPAUS2C two-phase commit (IMS REPL + DB2 INSERT + SYNCPOINT):** In PostgreSQL, this is a single atomic transaction: UPDATE authorizations SET fraud_status = ... + UPSERT authorization_fraud_records. No distributed transaction manager needed.

### 11.8 Billing Service

**File:** `app/services/billing_service.py`

Maps to: COBIL00C

**Methods:**

| Method | COBOL Paragraph/Program | Description |
|--------|------------------------|-------------|
| `get_balance(account_id)` | COBIL00C Phase 1 (MQ request to COACCT01) | Return current balance from accounts table |
| `process_payment(account_id, payment_request)` | COBIL00C Phase 2 (MQ request to CODATE01) | Validate confirmation=Y; apply payment to balance; record transaction |

**MQ elimination:** COBIL00C sends MQ messages to COACCT01 (account lookup) and CODATE01 (payment processing). Both are replaced by direct database operations in the billing service. No message queue needed.

**ZIP code preservation:** COBIL00C has a documented bug where the ZIP code is dropped from the MQ reply (COBIL00C.md note). The modern service always includes ZIP code in responses.

---

## 12. Background Task Architecture

The following COBOL batch programs are replaced by FastAPI background tasks and admin endpoints:

| COBOL Batch Program | Modern Replacement |
|--------------------|-------------------|
| CBACT01C (account extract → 3 output files) | `POST /api/v1/admin/tasks/account-extract` + background task |
| CBTRN01C (daily transaction verify) | `POST /api/v1/admin/tasks/transaction-verify` + background task |
| CBTRN02C (post transactions) | `POST /api/v1/admin/tasks/transaction-post` + background task |
| CBACT02C (account report) | Triggered by `POST /api/v1/reports/request` with type=account |
| CBACT03C (interest calculation) | `POST /api/v1/admin/tasks/interest-calc` + background task |
| CBACT04C (charge generation) | `POST /api/v1/admin/tasks/charge-gen` + background task |
| CBCUS01C (customer extract) | `POST /api/v1/admin/tasks/customer-extract` + background task |
| CBSTM03A/B (statement generation) | `POST /api/v1/admin/tasks/statement-gen` + background task |
| CORPT00C → batch print | Report request stored; async background task queries and generates report |

**Background task pattern:**

```python
from fastapi import BackgroundTasks

@router.post("/admin/tasks/account-extract")
async def trigger_account_extract(
    background_tasks: BackgroundTasks,
    current_user: TokenPayload = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Replaces CBACT01C JCL job submission."""
    task_id = await report_service.create_task_record(db, "ACCOUNT_EXTRACT", current_user.sub)
    background_tasks.add_task(account_extract_task, task_id)
    return {"task_id": task_id, "status": "SUBMITTED"}
```

---

## 13. Pagination Utility

**File:** `app/utils/pagination.py`

```python
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class PaginatedResponse(Generic[T]):
    """
    Standard pagination envelope.
    Replaces COBOL page-forward/backward COMMAREA state:
    - CDEMO-PAGE-NUM
    - CDEMO-NEXT-PAGE-FLG
    - CDEMO-LAST-PAGE-FLG
    """
    items: list[T]
    total_count: int
    page: int
    per_page: int
    total_pages: int

    @classmethod
    def create(cls, items: list[T], total_count: int, page: int, per_page: int):
        total_pages = (total_count + per_page - 1) // per_page
        return cls(
            items=items,
            total_count=total_count,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
        )
```

---

## 14. COBOL-to-Service Cognitive Complexity Management

COBOL paragraphs often have high cyclomatic complexity (many nested IF/EVALUATE conditions). The cognitive complexity limit of 15 per function is enforced by:

1. **Extract validation methods:** Each field validation becomes its own function. Example: COACTUPC's 40+ condition validation paragraph becomes 8 focused validator functions.

2. **Extract query builders:** Complex filter conditions in STARTBR equivalents become dedicated query builder methods in repositories.

3. **Use early returns:** COBOL PERFORM … THRU with GO TO EXIT patterns become Python functions with early `raise` or `return` instead of deeply nested if-else trees.

4. **Separate state transitions:** COTRTUPC's state machine has 15 states. Each state transition is a separate method: `_transition_to_show_details()`, `_transition_to_confirm_delete()`, etc.

**Example refactoring pattern:**

```python
# BAD — high cognitive complexity
async def update_user(self, user_id, request):
    if not request.first_name:
        if not request.last_name:
            if not request.password:
                # deeply nested...

# GOOD — extracted validators, early returns
async def update_user(self, user_id: str, request: UserUpdateRequest) -> UserResponse:
    """Maps to COUSR02C UPDATE-USER-INFO paragraph."""
    self._validate_update_fields(request)      # raises ValidationError if blank
    user = await self._require_user_exists(user_id)  # raises NotFoundError if missing
    if not self._has_changes(user, request):
        raise ValidationError("Please modify to update...")
    updated = self._apply_updates(user, request)
    return UserResponse.from_orm(await self.user_repo.update(updated))

def _validate_update_fields(self, request: UserUpdateRequest) -> None:
    """Maps to COUSR02C UPDATE-USER-INFO field blank checks (lines 190-220)."""
    if not request.first_name.strip():
        raise ValidationError("First Name can NOT be empty...")
    if not request.last_name.strip():
        raise ValidationError("Last Name can NOT be empty...")
    if not request.password.strip():
        raise ValidationError("Password can NOT be empty...")
    if not request.user_type.strip():
        raise ValidationError("User Type can NOT be empty...")
```

---

## 15. Test Strategy

### 15.1 Test Fixtures

**File:** `tests/conftest.py`

```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.database import get_db, Base

TEST_DATABASE_URL = "postgresql+asyncpg://carddemo_test:carddemo_test@localhost:5432/carddemo_test"

@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db(test_engine) -> AsyncSession:
    async with AsyncSession(test_engine) as session:
        yield session
        await session.rollback()

@pytest.fixture
async def client(db) -> AsyncClient:
    app.dependency_overrides[get_db] = lambda: db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.fixture
def admin_token():
    """JWT token for admin user — replaces CDEMO-USRTYP='A' test condition."""
    from app.utils.security import create_access_token
    return create_access_token("ADMIN001", "A")

@pytest.fixture
def user_token():
    """JWT token for regular user — replaces CDEMO-USRTYP='U' test condition."""
    from app.utils.security import create_access_token
    return create_access_token("USER0001", "U")
```

### 15.2 Critical Test Cases Derived from COBOL Logic

Each of the following COBOL error conditions must have a corresponding test:

| COBOL Condition | Test Method |
|-----------------|-------------|
| EIBCALEN=0 → redirect to COSGN00C | `test_login_required_for_all_protected_endpoints` |
| USRIDINI blank → error | `test_user_id_cannot_be_empty` |
| READ NOTFND → "User ID NOT found" | `test_user_not_found_returns_404` |
| No fields modified → "Please modify to update" | `test_update_with_no_changes_returns_422` |
| DELETE NOTFND → error | `test_delete_nonexistent_user_returns_404` |
| CONFIRM not Y → no action | `test_payment_requires_y_confirmation` |
| ACTIDIN and CARDNIN both blank → error | `test_transaction_requires_account_or_card` |
| FICO score out of range | `test_fico_score_must_be_300_to_850` |
| Type code non-numeric | `test_transaction_type_code_must_be_numeric` |
| DB2 FK violation on delete | `test_delete_type_code_with_transactions_returns_409` |
| Concurrent modification (optimistic lock) | `test_card_update_detects_concurrent_modification` |
| Admin-only endpoint with user token | `test_admin_endpoint_forbidden_for_regular_user` |
