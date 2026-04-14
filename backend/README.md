# CardDemo Backend — FastAPI

Modern Python backend migrated from the CardDemo COBOL CICS mainframe application.

## Migration Overview

This backend replaces the following mainframe components:

| Legacy Component | Modern Replacement |
|---|---|
| **COSGN00C** (COBOL sign-on program) | `app/api/endpoints/auth.py` — login/logout REST endpoints |
| **COSGN0A** (BMS sign-on screen map) | N/A — UI moved to Next.js frontend |
| **USRSEC VSAM KSDS** (user security file) | PostgreSQL `users` table via SQLAlchemy + Alembic |
| **CICS COMMAREA** (session state) | JWT access tokens with `jti`-based revocation |
| **Plain-text SEC-USR-PWD** | bcrypt (12 rounds) one-way password hashing |

### Security Improvements

- **Password storage**: Plain-text `SEC-USR-PWD` replaced with bcrypt hashing
- **Session management**: CICS pseudo-conversational sessions replaced with JWT tokens (1-hour expiry + logout revocation)
- **Rate limiting**: 5 requests/minute per IP on the login endpoint (via `slowapi`)
- **User enumeration prevention**: Identical `401` response for user-not-found and wrong-password
- **Production safeguards**: Startup blocked if `SECRET_KEY` is the default sentinel when `DEBUG=False`

## Project Structure

```
backend/
├── alembic/                  # Database migrations
│   └── versions/
│       └── 001_initial_schema.py
├── app/
│   ├── api/endpoints/        # Route handlers
│   │   └── auth.py           # POST /login, POST /logout
│   ├── config.py             # Pydantic settings (env-based)
│   ├── database.py           # Async SQLAlchemy engine
│   ├── main.py               # FastAPI app entry point
│   ├── middleware/            # CORS, logging
│   ├── models/               # SQLAlchemy ORM models
│   ├── repositories/         # Data access layer
│   ├── schemas/              # Pydantic request/response models
│   ├── services/             # Business logic
│   │   └── auth_service.py   # Authentication service
│   └── utils/
│       ├── security.py       # JWT + bcrypt utilities
│       └── rate_limit.py     # Rate limiter config
├── sql/
│   └── seed_data.sql         # Test user data
├── tests/
│   ├── conftest.py           # Async test fixtures (aiosqlite)
│   ├── test_auth_endpoints.py
│   └── test_auth_service.py
├── alembic.ini
└── pyproject.toml
```

## Prerequisites

- Python 3.11+
- PostgreSQL 14+
- [Poetry](https://python-poetry.org/) for dependency management

## Setup

### 1. Install dependencies

```bash
cd backend
poetry install
```

### 2. Configure environment

Create a `.env` file in the `backend/` directory:

```env
DATABASE_URL=postgresql+asyncpg://carddemo:carddemo@localhost/carddemo
SECRET_KEY=<generate-with-command-below>
DEBUG=true
CORS_ORIGINS=["http://localhost:3000"]
```

Generate a strong secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Create the database

```bash
createdb carddemo
# Or via psql:
# psql -U postgres -c "CREATE DATABASE carddemo;"
# psql -U postgres -c "CREATE USER carddemo WITH PASSWORD 'carddemo';"
# psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE carddemo TO carddemo;"
```

### 4. Run database migrations

```bash
poetry run alembic upgrade head
```

### 5. Seed test data (development only)

```bash
psql -U carddemo -d carddemo -f sql/seed_data.sql
```

This creates 5 test users:

| User ID | Password | Role |
|---|---|---|
| ADMIN001 | AdminPass1! | Admin |
| ADMIN002 | AdminPass2! | Admin |
| USER0001 | UserPass1! | User |
| USER0002 | UserPass2! | User |
| USER0003 | UserPass3! | User |

### 6. Start the server

```bash
# Development (with auto-reload)
poetry run uvicorn app.main:app --reload --port 8000

# Production
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000`.

API docs (development only): `http://localhost:8000/docs`

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/auth/login` | Authenticate user, returns JWT |
| `POST` | `/api/v1/auth/logout` | Revoke JWT (requires `Authorization` header) |

### Login example

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"user_id": "USER0001", "password": "UserPass1!"}'
```

### Logout example

```bash
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer <access_token>"
```

## Running Tests

```bash
# Run all tests
poetry run pytest

# With coverage report
poetry run pytest --cov=app --cov-report=term-missing

# Run a specific test file
poetry run pytest tests/test_auth_endpoints.py -v
```

Tests use an in-memory SQLite database (`aiosqlite`) — no PostgreSQL instance required.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://carddemo:carddemo@localhost/carddemo` | Async database connection string |
| `SECRET_KEY` | `change-me-in-production-...` | JWT signing key (must set for production) |
| `ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_SECONDS` | `3600` | Token expiry (seconds) |
| `BCRYPT_ROUNDS` | `12` | bcrypt cost factor |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed CORS origins |
| `DEBUG` | `false` | Enables API docs and relaxed secret key validation |
| `BLACKLIST_BACKEND` | `memory` | Token blacklist backend (`memory` or `redis`) |
