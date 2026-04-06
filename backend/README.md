# CardDemo Authorization Backend

FastAPI backend for the Authorization module, modernizing COPAUS0C, COPAUS1C, and COPAUS2C COBOL programs.

## Setup

```bash
poetry install
poetry run uvicorn app.main:app --reload
```

## Tests

```bash
poetry run pytest tests/ -v
```

## API Endpoints

- `GET /api/v1/authorizations` — Paginated authorization summaries (COPAUS0C)
- `GET /api/v1/authorizations/{account_id}/details` — Detail list for account (COPAUS0C)
- `GET /api/v1/authorizations/detail/{auth_id}` — Single detail view (COPAUS1C)
- `PUT /api/v1/authorizations/detail/{auth_id}/fraud` — Fraud toggle (COPAUS1C PF5 → COPAUS2C)
- `GET /api/v1/authorizations/detail/{auth_id}/fraud-logs` — Audit trail (DB2 AUTHFRDS)

## Database Setup

```bash
psql -d carddemo -f sql/create_tables.sql
psql -d carddemo -f sql/seed_data.sql
```

## COBOL Mappings

| COBOL Program | Python Module | Purpose |
|---------------|---------------|---------|
| COPAUS0C | `services/authorization_service.py:list_details_for_account` | Summary browse |
| COPAUS1C | `services/authorization_service.py:get_authorization_detail` | Detail view |
| COPAUS1C MARK-AUTH-FRAUD | `services/authorization_service.py:toggle_fraud_flag` | Fraud toggle |
| COPAUS2C | `repositories/authorization_repository.py:upsert_fraud_log` | DB2 audit log |
