# CardDemo FastAPI REST API

Mainframe modernization conversion of the **AWS CardDemo** COBOL/CICS application.
Replaces 17 online COBOL programs, 8 batch programs, and an authorization subsystem
with a FastAPI + PostgreSQL REST API.

## Architecture Overview

```
IBM z/OS Mainframe                   FastAPI Equivalent
─────────────────                    ──────────────────
CICS Online Subsystem           →    REST API (FastAPI)
VSAM KSDS files (ACCTDAT etc.)  →    PostgreSQL tables
DB2 CARDDEMO tables             →    PostgreSQL tables
IMS PAUT database               →    PostgreSQL tables
COSGN00C plain-text auth        →    bcrypt + JWT Bearer tokens
CICS COMMAREA session state     →    JWT token payload
EXEC CICS READ/REWRITE/WRITE    →    SQLAlchemy async ORM
CICS SYNCPOINT                  →    SQLAlchemy session commit
VSAM STARTBR/READNEXT/READPREV  →    Keyset pagination
MQ-triggered COPAUA0C           →    POST /authorizations/process
Batch JCL execution             →    POST /batch/* endpoints
```

## Prerequisites

- Python 3.11+
- PostgreSQL 14+
- [Poetry](https://python-poetry.org/) (dependency management)

## Setup

### 1. Clone and install dependencies

```bash
cd fast_api
poetry install
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your PostgreSQL credentials and a secure SECRET_KEY
```

### 3. Create PostgreSQL database

```sql
CREATE DATABASE carddemo;
CREATE USER carddemo WITH PASSWORD 'carddemo';
GRANT ALL PRIVILEGES ON DATABASE carddemo TO carddemo;
```

### 4. Run database migrations

```bash
# Apply schema
poetry run alembic upgrade head

# Load seed data (optional, for development/testing)
psql -U carddemo -d carddemo -f migrations/sql/002_seed_data.sql
```

Alternatively, run the raw SQL scripts directly:
```bash
psql -U carddemo -d carddemo -f migrations/sql/001_create_tables.sql
psql -U carddemo -d carddemo -f migrations/sql/002_seed_data.sql
```

### 5. Start the server

```bash
poetry run uvicorn app.main:app --reload --port 8000
```

API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc:       http://localhost:8000/redoc
- Health:      http://localhost:8000/health

## Running Tests

Tests use SQLite in-memory (no PostgreSQL required):

```bash
# All tests
poetry run pytest

# With coverage report
poetry run pytest --cov=app --cov-report=html

# Specific module
poetry run pytest tests/test_services/test_auth_service.py -v

# By keyword
poetry run pytest -k "auth" -v
```

## API Endpoint Reference

### Authentication

| Method | Path          | COBOL Source | Description                   |
|--------|---------------|--------------|-------------------------------|
| POST   | /auth/login   | COSGN00C     | Login; returns JWT token      |

**Login request:**
```json
{
  "user_id": "SYSADM00",
  "password": "Admin123"
}
```

**Login response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user_id": "SYSADM00",
  "user_type": "A",
  "first_name": "System",
  "last_name": "Admin"
}
```

All subsequent requests require: `Authorization: Bearer <token>`

### Accounts (COACTVWC / COACTUPC)

| Method | Path                  | Description                              |
|--------|-----------------------|------------------------------------------|
| GET    | /accounts/{acct_id}   | View account + customer (3-step read)    |
| PUT    | /accounts/{acct_id}   | Update account + customer (atomic REWRITE) |

### Cards (COCRDLIC / COCRDSLC / COCRDUPC)

| Method | Path               | Description                          |
|--------|--------------------|--------------------------------------|
| GET    | /cards             | List cards (7/page, keyset pagination) |
| GET    | /cards/{card_num}  | Card detail view                     |
| PUT    | /cards/{card_num}  | Update card                          |
| POST   | /cards             | Create card + xref                   |

### Transactions (COTRN00C / COTRN01C / COTRN02C)

| Method | Path                      | Description                           |
|--------|---------------------------|---------------------------------------|
| GET    | /transactions             | List transactions (10/page)           |
| GET    | /transactions/{tran_id}   | Transaction detail                    |
| POST   | /transactions             | Add transaction (card_num or acct_id) |
| POST   | /billing/pay              | Bill payment (COBIL00C)               |
| POST   | /reports/generate         | Transaction report (CORPT00C)         |

**Add transaction — two lookup paths (COTRN02C):**
```json
// Path 1: direct card_num
{ "card_num": "4111111111111001", "tran_type_cd": "DB", "tran_cat_cd": 1, "tran_amt": "75.50" }

// Path 2: acct_id -> CXACAIX lookup
{ "acct_id": 10000000001, "tran_type_cd": "DB", "tran_cat_cd": 1, "tran_amt": "75.50" }
```

### Users (COUSR00C-03C) — Admin Only

| Method | Path              | Description          |
|--------|-------------------|----------------------|
| GET    | /users            | List users (10/page) |
| POST   | /users            | Create user          |
| GET    | /users/{usr_id}   | View user            |
| PUT    | /users/{usr_id}   | Update user          |
| DELETE | /users/{usr_id}   | Delete user          |

### Transaction Types (COTRTLIC / COTRTUPC)

| Method | Path                         | Description                          |
|--------|------------------------------|--------------------------------------|
| GET    | /transaction-types           | List types (7/page)                  |
| POST   | /transaction-types           | Create type (admin only)             |
| GET    | /transaction-types/{cd}      | View type                            |
| PUT    | /transaction-types/{cd}      | Update type (admin only)             |
| DELETE | /transaction-types/{cd}      | Delete type (admin only)             |

### Authorizations (COPAUS0C / COPAUS1C / COPAUS2C / COPAUA0C)

| Method | Path                                         | Description                           |
|--------|----------------------------------------------|---------------------------------------|
| GET    | /authorizations                              | Summary list (COPAUS0C)               |
| GET    | /authorizations/{acct_id}/details            | Detail list for account (COPAUS1C)    |
| GET    | /authorizations/{acct_id}/details/{d}/{t}    | Single detail by composite key        |
| POST   | /authorizations/fraud-flag                   | Flag as fraud (COPAUS2C)              |
| POST   | /authorizations/process                      | Process authorization (COPAUA0C)      |

**Authorization decision (COPAUA0C algorithm):**
```
available = credit_limit - |curr_bal| - approved_running_total
if available >= requested_amt → APPROVE (response_code='00')
else                          → DECLINE (response_code='51')
```

### Batch Processing — Admin Only

| Method | Path                              | COBOL Source | Description              |
|--------|-----------------------------------|--------------|--------------------------|
| POST   | /batch/interest-calculation       | CBACT04C     | Monthly interest         |
| POST   | /batch/transaction-validation     | CBTRN01C     | Validate daily trans     |
| POST   | /batch/transaction-posting        | CBTRN02C     | Post to cat-bal file     |
| POST   | /batch/statement-generation       | CBSTM03A     | Generate statements      |
| POST   | /batch/export                     | CBEXPORT     | Export all data          |
| POST   | /batch/import                     | CBIMPORT     | Import data              |
| POST   | /batch/transaction-type-update    | COBTUPDT     | Batch type maintenance   |

**Interest calculation formula (CBACT04C):**
```
monthly_interest = tran_cat_bal * int_rate / 12
```

## HTTP Status Code Mapping

| COBOL CICS Condition    | HTTP Status   | CardDemo Exception           |
|-------------------------|---------------|------------------------------|
| RESP=NORMAL (0)         | 200 / 201     | —                            |
| RESP=NOTFND (13)        | 404           | ResourceNotFoundError        |
| RESP=DUPREC (70)        | 409           | DuplicateKeyError            |
| RESP=LOCKED (45)        | 409           | RecordLockedError            |
| Wrong password          | 401           | AuthenticationError          |
| User not found          | 401           | AuthenticationError          |
| Insufficient privilege  | 403           | AuthorizationError           |
| Validation failure      | 422           | BusinessValidationError      |
| File I/O error          | 500           | FileIOError                  |

## User Types

- `A` = Admin — full access including user management and batch endpoints
- `U` = Regular User — access to account/card/transaction/authorization endpoints

Seed admin credentials: `SYSADM00` / `Admin123`

## Database Tables

| Table                   | Source                          | COBOL Copybook  |
|-------------------------|---------------------------------|-----------------|
| accounts                | ACCTDAT VSAM KSDS               | CVACT01Y        |
| customers               | CUSTDAT VSAM KSDS               | CVCUS01Y        |
| cards                   | CARDDAT VSAM KSDS               | CVACT02Y        |
| card_xref               | CXACAIX VSAM AIX                | CVACT03Y        |
| transactions            | TRANSACT VSAM KSDS              | CVTRA05Y        |
| users                   | USRSEC VSAM KSDS                | CSUSR01Y        |
| tran_cat_bal            | TRAN-CAT-BAL-FILE VSAM          | CVTRA01Y        |
| disclosure_groups       | DIS-GROUP-FILE VSAM             | CVTRA02Y        |
| transaction_types       | DB2 CARDDEMO.TRANSACTION_TYPE   | CVTRA03Y        |
| transaction_categories  | DB2 CARDDEMO.TRANSACTION_CATEGORY | CVTRA04Y      |
| auth_summary            | IMS PAUTSUM0 segment            | CIPAUSMY        |
| auth_detail             | IMS PAUTDTL1 segment            | CIPAUDTY        |
| auth_fraud              | DB2 CARDDEMO.AUTHFRDS           | —               |

## Project Structure

```
fast_api/
├── app/
│   ├── main.py                        # FastAPI app + exception handlers
│   ├── api/
│   │   ├── dependencies.py            # JWT auth, require_admin, require_user
│   │   └── routes/                    # Route definitions (thin controllers)
│   │       ├── auth_routes.py         # POST /auth/login
│   │       ├── account_routes.py      # GET/PUT /accounts/{id}
│   │       ├── card_routes.py         # /cards
│   │       ├── transaction_routes.py  # /transactions, /billing, /reports
│   │       ├── user_routes.py         # /users (admin)
│   │       ├── tran_type_routes.py    # /transaction-types
│   │       ├── authorization_routes.py # /authorizations
│   │       └── batch_routes.py        # /batch/* (admin)
│   ├── core/
│   │   ├── config.py                  # Pydantic settings
│   │   └── exceptions.py             # Custom exception hierarchy
│   ├── domain/
│   │   └── services/                  # Business logic
│   │       ├── auth_service.py        # COSGN00C logic
│   │       ├── account_service.py     # COACTVWC/COACTUPC logic
│   │       ├── card_service.py        # COCRD*/COCRDUPC logic
│   │       ├── transaction_service.py # COTRN*/COBIL00C logic
│   │       ├── user_service.py        # COUSR00C-03C logic
│   │       ├── tran_type_service.py   # COTRTLIC/COTRTUPC logic
│   │       ├── authorization_service.py # COPAU*/COPAUA0C logic
│   │       └── batch_service.py       # CBACT04C, CBTRN01-03C, etc.
│   ├── infrastructure/
│   │   ├── database.py               # Async engine + get_db()
│   │   ├── orm/                      # SQLAlchemy ORM models
│   │   └── repositories/             # Data access layer
│   └── schemas/                      # Pydantic request/response models
├── tests/
│   ├── conftest.py                   # SQLite fixtures, seeded_db, HTTP clients
│   ├── test_services/                # Unit tests for business logic
│   ├── test_repositories/            # Unit tests for data access
│   └── test_routes/                  # Integration tests for HTTP layer
├── migrations/
│   └── sql/
│       ├── 001_create_tables.sql     # Raw DDL (alternative to Alembic)
│       └── 002_seed_data.sql         # Sample data
├── alembic/
│   ├── env.py                        # Async migration environment
│   └── versions/
│       └── 001_initial_schema.py     # Initial migration
├── alembic.ini                       # Alembic configuration
├── .env.example                      # Environment variable template
└── pyproject.toml                    # Poetry project configuration
```

## Key Business Rule Traceability

| Spec Requirement                        | Implementation Location                           |
|-----------------------------------------|---------------------------------------------------|
| COSGN00C: uppercase user_id             | `auth_schemas.py` `@field_validator` on `user_id` |
| COSGN00C: RESP=NOTFND error message     | `auth_service.py::authenticate_user`              |
| COACTVWC: 3-step read sequence          | `account_service.py::get_account_with_customer`   |
| COACTUPC: 35+ field validations         | `account_service.py::_validate_*_fields`          |
| CSLKPCDY: state code table              | `customer_orm.py::VALID_US_STATE_CODES`           |
| CSLKPCDY: phone format (999)999-9999   | `account_schemas.py::validate_phone`              |
| FICO score 300-850                      | `account_schemas.py::CustomerBase` + service      |
| COTRN02C: READPREV tran_id generation   | `transaction_service.py::_generate_tran_id`       |
| COTRN02C: two card lookup paths         | `transaction_service.py::_resolve_card_num`       |
| COBIL00C: active account required       | `transaction_service.py::process_bill_payment`    |
| CXACAIX: VSAM AIX by acct_id           | `ix_card_xref_acct_id` + `get_xref_by_account_id` |
| COPAUA0C: available credit formula      | `authorization_service.py::process_authorization` |
| COPAUA0C: '00'=approve, '51'=decline    | `authorization_service.py::process_authorization` |
| COPAUS2C: INSERT/UPDATE AUTHFRDS        | `authorization_service.py::flag_fraud`            |
| CBACT04C: interest = bal * rate / 12    | `batch_service.py::run_interest_calculation`      |
| CBSTM03A: XREF → ACCT → CUST sequence  | `batch_service.py::run_statement_generation`      |
| Batch: admin-only endpoints             | `api/dependencies.py::require_admin`              |
| CICS SYNCPOINT                          | `database.py::get_db` commit/rollback             |
