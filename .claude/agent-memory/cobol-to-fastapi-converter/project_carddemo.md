---
name: CardDemo COBOL-to-FastAPI Conversion Project
description: Ongoing mainframe modernization of AWS CardDemo COBOL/CICS application to FastAPI + PostgreSQL
type: project
---

Full conversion of AWS CardDemo mainframe application. Output: `/home/mridul/projects/triedatum-inc/one/mainframe-conversion-claude/fast_api/`

**Why:** Mainframe modernization initiative — replace COBOL/CICS with Python REST API.

**How to apply:** When continuing work, check `fast_api/` directory for existing files before generating anything new. The project is on branch `migration_1`.

## Status (as of 2026-04-02)
All source files created. Pending: validate tests run correctly against the codebase.

## Key architecture decisions
- Poetry project at `fast_api/pyproject.toml`
- Clean architecture: routes → services → repositories → ORM
- SQLite + aiosqlite for tests (avoids needing PostgreSQL in CI)
- `tests/conftest.py` patches `app.router.lifespan_context` with no-op to skip PostgreSQL connectivity check
- JWT Bearer token replaces COSGN00C plain-text USRSEC auth
- bcrypt hashing for SEC-USR-PWD (was plain-text in COBOL)

## Program → endpoint mapping
- COSGN00C → POST /auth/login
- COACTVWC → GET /accounts/{acct_id}
- COACTUPC → PUT /accounts/{acct_id}
- COCRDLIC → GET /cards (7/page)
- COCRDSLC → GET /cards/{card_num}
- COCRDUPC → PUT /cards/{card_num}
- COTRN00C → GET /transactions
- COTRN01C → GET /transactions/{tran_id}
- COTRN02C → POST /transactions
- COBIL00C → POST /billing/pay
- CORPT00C → POST /reports/generate
- COUSR00C-03C → /users (admin only)
- COTRTLIC → GET /transaction-types
- COTRTUPC → POST/PUT/DELETE /transaction-types (admin only)
- COPAUS0C → GET /authorizations
- COPAUS1C → GET /authorizations/{id}/details
- COPAUS2C → POST /authorizations/fraud-flag
- COPAUA0C → POST /authorizations/process
- CBACT04C → POST /batch/interest-calculation
- CBTRN01C → POST /batch/transaction-validation
- CBTRN02C → POST /batch/transaction-posting
- CBSTM03A → POST /batch/statement-generation
- CBEXPORT → POST /batch/export
- CBIMPORT → POST /batch/import
- COBTUPDT → POST /batch/transaction-type-update

## Critical business rules
- COPAUA0C: available = credit_limit - |curr_bal| - approved_running; approve if >= requested
- CBACT04C: interest = tran_cat_bal * int_rate / 12 (monthly)
- COTRN02C: tran_id = last_tran_id + 1, zero-padded to 16 chars
- COTRN02C: two card lookup paths — card_num direct OR acct_id → CXACAIX
- COACTUPC: REWRITE ACCTDAT + REWRITE CUSTDAT must be atomic (one SQLAlchemy transaction)
- COPAUS2C: INSERT AUTHFRDS if new, UPDATE if exists; always set PAUTDTL1.fraud_flag='Y'
- CSLKPCDY: US state validation table → frozenset in customer_orm.py
- Phone format: (999)999-9999 (CSLKPCDY)

## VSAM → PostgreSQL table mapping
- ACCTDAT → accounts (acct_id BIGINT PK)
- CUSTDAT → customers (cust_id INTEGER PK)
- CARDDAT → cards (card_num VARCHAR(16) PK)
- CXACAIX → card_xref + ix_card_xref_acct_id (replaces VSAM AIX)
- TRANSACT → transactions (tran_id VARCHAR(16) PK)
- USRSEC → users (usr_id VARCHAR(8) PK, bcrypt pwd_hash)
- TRAN-CAT-BAL-FILE → tran_cat_bal (composite PK)
- DIS-GROUP-FILE → disclosure_groups (composite PK)
- DB2 TRANSACTION_TYPE → transaction_types
- IMS PAUTSUM0 → auth_summary
- IMS PAUTDTL1 → auth_detail (composite PK: auth_date + auth_time + acct_id)
- DB2 AUTHFRDS → auth_fraud (SERIAL PK)

## Test strategy
- Service tests: unit tests using `seeded_db` fixture (SQLite in-memory)
- Repository tests: same
- Route tests: integration via `async_client` (httpx AsyncClient with ASGITransport)
- Seed data: 3 customers/accounts/cards, 4 transactions, 2 auth summaries, 2 auth details
- `conftest.py` patches lifespan to skip PostgreSQL connectivity check
