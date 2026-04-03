# CardDemo Credit Card API

FastAPI backend for the Credit Card Management module.

| COBOL Program | Transaction | Converted To |
|---|---|---|
| COCRDLIC | CCLI | GET /api/cards |
| COCRDSLC | CCDL | GET /api/cards/{card_num} |
| COCRDUPC | CCUP | PUT /api/cards/{card_num} |

## Setup

```bash
cd fast_api
poetry install
cp .env.example .env   # set DATABASE_URL
psql -d carddemo -f sql/create_tables.sql
psql -d carddemo -f sql/seed_data.sql
poetry run uvicorn app.main:app --reload --port 8000
```

## Tests
```bash
poetry run pytest tests/ -v --cov=src/app
```

## Key Business Logic

- Cursor-based pagination via card_num (STARTBR GTEQ + READNEXT)
- Optimistic concurrency via updated_at timestamp token
- Alphabetic-only name validation (INSPECT CONVERTING equivalent)
- Expiry day preserved server-side (hidden EXPDAY field)
- Page size = 7 (WS-MAX-SCREEN-LINES)
