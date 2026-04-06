# CardDemo Transaction API

FastAPI backend for the CardDemo Transaction Module, modernized from COBOL CICS programs.

## COBOL-to-Modern Mapping

| COBOL Program | CICS Trans | REST Endpoint |
|---------------|-----------|---------------|
| COTRN00C | CT00 | GET  /api/transactions |
| COTRN01C | CT01 | GET  /api/transactions/{id} |
| COTRN02C | CT02 | POST /api/transactions |
| COBIL00C | CB00 | GET  /api/bill-payment/preview/{account_id} |
| COBIL00C | CB00 | POST /api/bill-payment |
| CORPT00C | CR00 | POST /api/reports/transactions |

## Setup

```bash
# Install dependencies
poetry install

# Copy environment config
cp .env.example .env

# Run database migrations
poetry run alembic upgrade head

# Load seed data
psql $DATABASE_URL -f sql/seed_data.sql

# Start development server
poetry run uvicorn app.main:app --reload --port 8000
```

## Running Tests

```bash
poetry run pytest --cov=app --cov-report=term-missing
```

## Business Rules Preserved

- Transaction ID generation: SELECT MAX + 1 (COBOL STARTBR HIGH-VALUES + READPREV pattern)
- Amount format: -99999999.99 (COBOL S9(9)V99 COMP-3)
- Merchant ID: digits only (COBOL numeric validation)
- Confirmation required: `confirmed=true` maps to COBOL CONFIRM='Y'
- Bill payment: always full balance, type='02', merchant_id='999999999'
- Report dates: monthly/yearly auto-derived, custom validated (end >= start)
