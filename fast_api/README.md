# Account Management API

FastAPI backend for the CardDemo Account Management module.

Converted from COBOL CICS programs:
- **COACTVWC** (Transaction CAVW) → `GET /api/accounts/{acct_id}`
- **COACTUPC** (Transaction CAUP) → `PUT /api/accounts/{acct_id}`

## Architecture

```
fast_api/
├── sql/
│   ├── create_tables.sql    # Schema DDL (accounts, customers, cards, card_cross_references)
│   └── seed_data.sql        # 5 accounts, 5 customers, 10 cards with cross-references
└── src/app/
    ├── models/              # SQLAlchemy ORM (maps to VSAM copybooks)
    ├── schemas/             # Pydantic validation (maps to BMS field attributes)
    ├── repositories/        # Data access (maps to EXEC CICS READ/REWRITE)
    ├── services/            # Business logic (maps to COBOL paragraphs)
    ├── routers/             # HTTP endpoints
    └── utils/               # Formatters (SSN, phone) + custom exceptions
```

## Setup

```bash
# Install dependencies
poetry install

# Set environment variable
export DATABASE_URL=postgresql+asyncpg://cardemo:cardemo@localhost:5432/cardemo

# Apply schema and seed data
psql -U cardemo -d cardemo -f sql/create_tables.sql
psql -U cardemo -d cardemo -f sql/seed_data.sql

# Run the API
poetry run uvicorn app.main:app --reload --app-dir src/
```

API docs available at http://localhost:8000/docs

## Running Tests

```bash
poetry run pytest
```

## Key Business Rules Implemented

| COBOL Paragraph | Python Implementation |
|---|---|
| `2210-EDIT-ACCOUNT` | Router `_validate_acct_id()` |
| `1225-EDIT-ALPHA-REQD` | Pydantic `validate_required_alpha()` |
| `1270-EDIT-US-STATE-CD` | Pydantic `validate_state_code()` against `VALID_US_STATES` set |
| `1275-EDIT-FICO-SCORE` | Pydantic `ge=300, le=850` constraint |
| `1265-EDIT-US-SSN` | Pydantic `SsnInput` with part1 rules |
| `1260-EDIT-US-PHONE-NUM` | Pydantic `PhoneInput` with NANP validation |
| `EDIT-DATE-OF-BIRTH` | Pydantic `validate_dob_not_future()` |
| `9700-CHECK-CHANGE-IN-REC` | Service `_check_concurrency()` via `updated_at` timestamps |
| `EXEC CICS READ...UPDATE` | Repository `get_account_for_update()` with `FOR UPDATE NOWAIT` |
| `EXEC CICS SYNCPOINT ROLLBACK` | Repository `rollback()` on write failure |
| `STRING CUST-SSN...` | `format_ssn()` → `XXX-XX-XXXX` |
| `STRING phone parts...` | `format_phone()` → `(aaa)bbb-cccc` |

## Optimistic Concurrency Control

The `updated_at` timestamp from `GET /api/accounts/{acct_id}` must be sent
back in the `PUT` request body as `updated_at`. If either the account or
customer record has been modified since the client fetched the data, a
`409 Conflict` response is returned — equivalent to COBOL condition
`DATA-WAS-CHANGED-BEFORE-UPDATE`.
