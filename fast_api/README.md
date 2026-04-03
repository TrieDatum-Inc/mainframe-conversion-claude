# CardDemo API — Authentication & Navigation Module

FastAPI backend converting IBM COBOL mainframe programs to REST APIs.

## Programs Converted

| COBOL Program | Transaction | Modern Endpoint |
|---|---|---|
| COSGN00C | CC00 | `POST /auth/login`, `POST /auth/logout`, `GET /auth/me` |
| COMEN01C | CM00 | `GET /menu/main`, `POST /menu/main/navigate` |
| COADM01C | CA00 | `GET /menu/admin`, `POST /menu/admin/navigate` |

## Quick Start

```bash
# Install dependencies
poetry install

# Set environment variables
cp .env.example .env  # edit as needed

# Run database migrations (requires PostgreSQL)
psql -U postgres -d carddemo -f sql/create_tables.sql
psql -U postgres -d carddemo -f sql/seed_data.sql

# Start development server
PYTHONPATH=src poetry run uvicorn app.main:app --reload
```

API docs available at: http://localhost:8000/docs

## Test Users (from seed_data.sql)

| User ID  | Password | Type  | Menu |
|----------|----------|-------|------|
| ADMIN001 | ADMIN001 | Admin | /admin-menu |
| ADMIN002 | SYSADMIN | Admin | /admin-menu |
| USER0001 | USER0001 | User  | /main-menu |
| USER0002 | TESTPASS | User  | /main-menu |
| USER0003 | MYPASSWD | User  | /main-menu |

> Note: Passwords are stored as bcrypt hashes. The COBOL original stored plaintext PIC X(08).

## Running Tests

```bash
PYTHONPATH=src poetry run pytest tests/ -v
```

## Architecture

```
COBOL Paragraph              Modern Equivalent
─────────────────────────────────────────────
PROCESS-ENTER-KEY          → AuthService.authenticate()
READ-USER-SEC-FILE         → UserRepository.get_by_id() + verify_password()
POPULATE-HEADER-INFO       → server_time field in responses
BUILD-MENU-OPTIONS         → MenuService.get_main_menu() / get_admin_menu()
RETURN-TO-SIGNON-SCREEN    → 401/403 HTTP responses + client redirect
CARDDEMO-COMMAREA          → JWT token claims
EXEC CICS XCTL             → NavigateResponse.route field
```

## Business Rules

All COBOL business rules from COSGN00C, COMEN01C, and COADM01C are preserved:
- BR-001/BR-002: Required field validation (User ID and Password)
- BR-003: Uppercase before authentication
- BR-004: User not found (VSAM NOTFND → 401)
- BR-005: Password mismatch → 401
- BR-006: User type routing (A→admin-menu, U→main-menu)
- BR-007: PF3/logout endpoint
- COMEN01C BR-003/BR-004/BR-005/BR-006: Menu option validation and COPAUS0C check
- COADM01C BR-003/BR-004/BR-005: Admin menu validation and PGMIDERR handling
