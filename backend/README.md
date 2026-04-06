# CardDemo Backend — FastAPI

Python FastAPI backend for the CardDemo mainframe modernization project.
Replaces CICS/COBOL/VSAM with FastAPI/SQLAlchemy/PostgreSQL.

## COBOL Programs Replaced

| COBOL Program | Transaction | Module | Status |
|--------------|-------------|--------|--------|
| COSGN00C | CC00 | auth | Implemented |
| COUSR00C-03C | CU00-03 | users | Stub (schemas defined) |
| (all other programs) | — | various | Future modules |

## Quick Start

### Using Docker Compose (recommended)

```bash
cd backend/
docker compose up -d
```

This starts PostgreSQL and the FastAPI application with seed data.

### Manual Setup

1. Install dependencies:
```bash
pip install -r requirements-dev.txt
# OR using Poetry:
poetry install
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. Run database migrations:
```bash
alembic upgrade head
```

4. Seed the database:
```bash
psql -U carddemo -d carddemo -f sql/seed_data.sql
```

5. Start the server:
```bash
uvicorn app.main:app --reload --port 8000
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Test Credentials

After seeding, use these credentials:

| User ID | Password | Type | Redirect |
|---------|----------|------|----------|
| ADMIN001 | Admin1234 | Admin | /admin/menu |
| USER0001 | User1234 | Regular | /menu |

## Running Tests

```bash
# Install dev dependencies first
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run specific test module
pytest tests/test_services/test_auth_service.py -v
```

## Architecture

```
app/
├── main.py          # FastAPI app factory + lifespan
├── config.py        # Settings from env vars
├── database.py      # Async SQLAlchemy engine + session
├── models/          # ORM models (VSAM → PostgreSQL tables)
│   └── user.py      # users table (USRSEC VSAM → PostgreSQL)
├── schemas/         # Pydantic request/response DTOs
│   ├── auth.py      # LoginRequest, LoginResponse, TokenPayload
│   ├── user.py      # UserBase, UserResponse, UserListResponse
│   └── common.py    # ErrorResponse, MessageResponse
├── repositories/    # Database access (CICS FILE CONTROL → SQL)
│   └── user_repository.py
├── services/        # Business logic (COBOL PROCEDURE DIVISION)
│   └── auth_service.py
├── api/             # HTTP layer (thin controllers)
│   ├── router.py
│   └── endpoints/
│       └── auth.py  # POST /auth/login, POST /auth/logout, GET /auth/me
├── exceptions/      # Exception classes + global handlers
└── utils/
    └── security.py  # JWT + bcrypt utilities
```

## Security Notes

- Passwords are hashed with bcrypt (rounds=12) — never stored in plain text
- JWT tokens expire after 60 minutes (configurable via JWT_EXPIRE_MINUTES)
- User enumeration prevented: same 401 for user-not-found and wrong-password
- `password_hash` is never returned in any API response
- All database queries use parameterized SQLAlchemy ORM (no SQL injection risk)
