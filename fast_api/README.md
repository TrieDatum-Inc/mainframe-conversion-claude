# CardDemo Batch Processing API

FastAPI backend converted from IBM COBOL batch programs (CardDemo mainframe application).

## Programs Converted

| COBOL Program | Function | API Endpoint |
|---|---|---|
| CBTRN02C | Daily Transaction Posting | POST /api/batch/transaction-posting |
| CBTRN03C | Transaction Report Generator | POST /api/batch/transaction-report |
| CBACT04C | Interest and Fee Calculator | POST /api/batch/interest-calculation |
| CBEXPORT | Data Export | GET /api/batch/export |
| CBIMPORT | Data Import | POST /api/batch/import |

## Setup

```bash
poetry install
PYTHONPATH=src poetry run uvicorn app.main:app --reload
```

## Tests

```bash
PYTHONPATH=src poetry run pytest tests/ -v
```

59 tests pass using in-memory SQLite.
