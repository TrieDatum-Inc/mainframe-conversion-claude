# User Administration API

FastAPI backend for the CardDemo User Administration module.

Converted from COBOL programs:
- **COUSR00C** (CU00) — User List
- **COUSR01C** (CU01) — User Add
- **COUSR02C** (CU02) — User Update
- **COUSR03C** (CU03) — User Delete

## COBOL Bugs Fixed

1. **User type validation** (COUSR01C): Original only checked `NOT SPACES`, allowing any single character. Fixed to enforce `user_type IN ('A', 'U')` at both Pydantic schema and database CHECK constraint levels.
2. **Delete error message** (COUSR03C): Original said "Unable to Update User" on DELETE failure (copy-paste from COUSR02C). Fixed to "Unable to Delete User".

## Setup

### Prerequisites

- Python 3.11+
- Poetry
- PostgreSQL 14+

### Install

```bash
poetry install
```

### Database

```bash
psql -U postgres -c "CREATE DATABASE carddemo;"
psql -U postgres -d carddemo -f sql/create_tables.sql
psql -U postgres -d carddemo -f sql/seed_data.sql
```

### Configure

Copy `.env.example` to `.env` and update values:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/carddemo
SECRET_KEY=your-strong-random-secret
BCRYPT_ROUNDS=12
```

### Run

```bash
poetry run uvicorn app.main:app --reload --app-dir src
```

API docs: http://localhost:8000/api/docs

## API Endpoints

| Method | Path | COBOL Equivalent | Description |
|--------|------|-----------------|-------------|
| GET | `/api/users` | COUSR00C STARTBR/READNEXT | Paginated user list |
| POST | `/api/users` | COUSR01C WRITE | Create user |
| GET | `/api/users/{user_id}` | COUSR02C/03C READ | Get user by ID |
| PUT | `/api/users/{user_id}` | COUSR02C REWRITE | Update user |
| DELETE | `/api/users/{user_id}` | COUSR03C DELETE | Delete user |

All endpoints require `X-User-Type: A` header (admin-only, maps to COADM01C access control).

### Pagination

`GET /api/users?page=1&page_size=10&search_user_id=admin`

- `page_size` defaults to 10 (COUSR00C shows 10 rows per BMS screen)
- `search_user_id` positions the browse at that key (COUSR00C USRIDINI field)

## Tests

```bash
poetry run pytest tests/ -v
```

72 tests covering unit (service business logic) and integration (API endpoints).

## Architecture

```
src/app/
├── main.py              # FastAPI app
├── config.py            # Settings (pydantic-settings)
├── database.py          # Async SQLAlchemy engine + session
├── models/user.py       # SQLAlchemy ORM (maps to USRSEC VSAM)
├── schemas/user.py      # Pydantic request/response schemas
├── repositories/        # Data access layer
│   └── user_repository.py
├── services/            # Business logic (COBOL paragraph logic)
│   └── user_service.py
├── routers/             # HTTP layer
│   └── users.py
└── utils/
    └── password.py      # bcrypt hashing (replaces PIC X(08) plaintext)
```
