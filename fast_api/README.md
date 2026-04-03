# CardDemo Transaction Processing API

FastAPI backend converted from COBOL CICS programs COTRN00C, COTRN01C, COTRN02C.

## COBOL to Modern Stack Mapping

| COBOL Program | Transaction | Modern Equivalent |
|---|---|---|
| COTRN00C | CT00 | GET /api/transactions (paginated list) |
| COTRN01C | CT01 | GET /api/transactions/{tran_id} (detail view) |
| COTRN02C | CT02 | POST /api/transactions/validate + POST /api/transactions |

## Setup

```bash
poetry install
cp .env.example .env
# Edit DATABASE_URL in .env

psql -d carddemo -f sql/create_tables.sql
psql -d carddemo -f sql/seed_data.sql

poetry run uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
```

## Running Tests

```bash
poetry run pytest tests/ -v
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | /api/transactions | List transactions (paginated, mirrors CT00) |
| GET | /api/transactions/{tran_id} | View transaction detail (mirrors CT01) |
| POST | /api/transactions/validate | Validate input fields (step 1 of CT02 add flow) |
| POST | /api/transactions | Create transaction (step 2, requires confirm=Y) |
| GET | /api/transactions/copy-last | Copy last transaction data (PF5 from CT02) |

## Key Business Rules Preserved

1. Cursor-based pagination using first/last tran_id (mirrors COBOL STARTBR+READNEXT pattern)
2. Search start_tran_id must be numeric (mirrors TRNIDINI field validation)
3. Transaction ID auto-increment: reads highest existing ID + 1 (mirrors HIGH-VALUES READPREV + 1)
4. Two card/account cross-reference paths (account ID via CXACAIX AIX, card number via CCXREF)
5. Account active_status must be 'Y' to allow transaction creation
6. Amount format: +-99999999.99 (mirrors COBOL PIC +99999999.99)
7. Date validation: YYYY-MM-DD with calendar check (mirrors CSUTLDTC utility)
8. Two-phase add: validate step then confirm=Y required
9. No update locking on detail view (COBOL READ WITH UPDATE was a known anomaly)
