# CardDemo FastAPI

A Python FastAPI migration of the AWS CardDemo COBOL/CICS mainframe credit card management application.

## Overview

This project is a functionally identical migration of 23 CICS COBOL programs into a modern REST API. All business logic, validations, and error handling are preserved exactly as in the original COBOL source.

### COBOL Program to API Mapping

| COBOL Program | API Endpoint | Description |
|---|---|---|
| COSGN00C | `POST /api/auth/login` | User authentication |
| COACTVWC | `GET /api/accounts/{id}` | View account details |
| COACTUPC | `PUT /api/accounts/{id}` | Update account |
| COCRDLIC | `GET /api/cards` | List credit cards |
| COCRDSLC | `GET /api/cards/{num}` | View card details |
| COCRDUPC | `PUT /api/cards/{num}` | Update card |
| COTRN00C | `GET /api/transactions` | List transactions |
| COTRN01C | `GET /api/transactions/{id}` | View transaction |
| COTRN02C | `POST /api/transactions` | Add transaction |
| COUSR00C | `GET /api/users` | List users (admin) |
| COUSR01C | `POST /api/users` | Add user (admin) |
| COUSR02C | `PUT /api/users/{id}` | Update user (admin) |
| COUSR03C | `DELETE /api/users/{id}` | Delete user (admin) |
| COBIL00C | `POST /api/bill-payment` | Bill payment |
| CORPT00C | `POST /api/reports` | Submit report |
| COPAUA0C | `POST /api/authorizations/decision` | Card authorization |
| COPAUS0C | `GET /api/authorizations/summary` | Auth summary |
| COPAUS1C | `GET /api/authorizations/{id}/detail` | Auth detail |
| COPAUS2C | `POST /api/authorizations/fraud` | Mark fraud |
| COTRTLIC | `GET /api/transaction-types` | List transaction types |
| COTRTUPC | `POST/PUT/DELETE /api/transaction-types` | Manage transaction types |

## Tech Stack

- **Backend**: Python 3.11+ with FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy 2.0
- **Authentication**: JWT (python-jose)
- **Package Manager**: Poetry
- **Testing**: pytest + httpx

## Prerequisites

- Python 3.11 or higher
- PostgreSQL 14 or higher
- Poetry (Python package manager)

## Setup Instructions

### 1. Install Poetry (if not installed)

```bash
# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# macOS/Linux
curl -sSL https://install.python-poetry.org | python3 -
```

### 2. Clone and Install Dependencies

```bash
cd carddemo_fastapi
poetry install
```

### 3. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your database credentials
# DATABASE_URL=postgresql://postgres:postgres@localhost:5432/carddemo
# JWT_SECRET=your-super-secret-key-change-in-production
# JWT_ALGORITHM=HS256
# JWT_EXPIRE_MINUTES=60
```

### 4. Create Database and Load Schema

```bash
# Create the database
createdb carddemo

# Run the table creation script
psql -d carddemo -f sql/001_create_tables.sql

# Create indexes
psql -d carddemo -f sql/002_create_indexes.sql

# Load seed data
psql -d carddemo -f sql/003_seed_data.sql
```

Or via Python/psql with connection string:

```bash
psql "postgresql://postgres:postgres@localhost:5432/carddemo" -f sql/001_create_tables.sql
psql "postgresql://postgres:postgres@localhost:5432/carddemo" -f sql/002_create_indexes.sql
psql "postgresql://postgres:postgres@localhost:5432/carddemo" -f sql/003_seed_data.sql
```

### 5. Run the Application

```bash
# Development mode with auto-reload
poetry run uvicorn app.main:app --reload --port 8000

# Production mode
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 6. Access the API

- **API Documentation (Swagger)**: http://localhost:8000/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/

## Running Tests

```bash
# Run all tests
poetry run pytest tests/ -v

# Run specific test file
poetry run pytest tests/test_auth.py -v

# Run with coverage
poetry run pytest tests/ -v --cov=app
```

## Authentication

The API uses JWT Bearer tokens. To authenticate:

1. Call `POST /api/auth/login` with credentials:

```json
{
    "user_id": "admin1",
    "password": "ADMIN123"
}
```

2. Use the returned token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### Test Users (from seed data)

| User ID | Password | Type | Access |
|---------|----------|------|--------|
| admin1 | ADMIN123 | A (Admin) | Full access |
| user001 | USER0001 | U (User) | Standard access |
| user002 | USER0002 | U (User) | Standard access |

Admin users can access user management and transaction type maintenance endpoints.

## Database Schema

The PostgreSQL schema is derived from the original COBOL copybooks:

| Table | COBOL Source | Description |
|-------|-------------|-------------|
| customers | CUSTREC.cpy | Customer master records |
| accounts | CVACT01Y.cpy | Account master records |
| cards | CVACT02Y.cpy | Credit card records |
| card_xref | CVACT03Y.cpy | Card-Customer-Account cross-reference |
| transactions | CVTRA05Y.cpy | Transaction records |
| users | CSUSR01Y.cpy | User security records |
| transaction_types | CVTRA03Y.cpy | Transaction type master |
| transaction_categories | CVTRA04Y.cpy | Transaction category master |
| tran_cat_balance | CVTRA01Y.cpy | Category balance per account |
| disclosure_groups | CVTRA02Y.cpy | Interest rate disclosure groups |
| auth_fraud | AUTHFRDS.ddl | Authorization fraud records |
| pending_auth_summary | CIPAUSMY.cpy | Pending auth summary (IMS) |
| pending_auth_details | CIPAUDTY.cpy | Pending auth details (IMS) |

## Project Structure

```
carddemo_fastapi/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Environment configuration
│   ├── database.py          # SQLAlchemy engine & session
│   ├── dependencies.py      # Auth dependencies (JWT)
│   ├── exceptions.py        # Custom exceptions & handlers
│   ├── models/              # SQLAlchemy ORM models (13 tables)
│   ├── schemas/             # Pydantic request/response models
│   ├── services/            # Business logic layer
│   ├── routers/             # FastAPI route handlers
│   └── middleware/          # Auth middleware
├── sql/                     # Database DDL & seed data
├── tests/                   # Unit tests
├── pyproject.toml           # Poetry project definition
└── README.md                # This file
```
