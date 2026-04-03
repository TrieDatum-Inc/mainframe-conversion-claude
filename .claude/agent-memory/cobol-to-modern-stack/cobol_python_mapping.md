---
name: COBOL-to-Python Mapping Patterns
description: How specific COBOL/CICS constructs map to FastAPI, SQLAlchemy, and Python equivalents
type: reference
---

## VSAM Operations to SQL

| COBOL CICS Command | Python/SQLAlchemy Equivalent |
|-------------------|------------------------------|
| EXEC CICS STARTBR/READNEXT | `SELECT ORDER BY key OFFSET/LIMIT` (paginated browse) |
| EXEC CICS READ DATASET RIDFLD | `SELECT WHERE primary_key = :id` |
| EXEC CICS READ ... UPDATE | `SELECT FOR UPDATE` (SQLAlchemy row-level lock) |
| EXEC CICS WRITE DATASET | `session.add(obj); session.flush()` — IntegrityError on dup |
| EXEC CICS REWRITE DATASET | Mutate tracked SQLAlchemy object; `session.flush()` |
| EXEC CICS DELETE DATASET | `session.delete(obj); session.flush()` |
| DFHRESP(NOTFND) | `result.scalar_one_or_none()` returns None |
| DFHRESP(DUPKEY) / DUPREC | `sqlalchemy.exc.IntegrityError` |

## COBOL Data Types to PostgreSQL

| COBOL PIC | PostgreSQL Type |
|-----------|----------------|
| PIC X(n) | VARCHAR(n) |
| PIC 9(n) | INTEGER or NUMERIC(n) |
| PIC 9(n)V9(m) | NUMERIC(n+m, m) |
| COMP-3 | NUMERIC |
| PIC 9(8) date | DATE |
| PIC X(01) flag | CHAR(1) with CHECK constraint |

## COBOL Program Structure to Clean Architecture

| COBOL Element | Modern Layer |
|--------------|-------------|
| PROCESS-ENTER-KEY / PROCESS-PF5-KEY paragraphs | Service layer methods |
| WRITE/REWRITE/DELETE paragraphs | Repository methods |
| SEND-SCREEN / POPULATE-HEADER-INFO | Router response formatting |
| WS-VARIABLES (working storage flags) | Service method local variables |
| 88-level condition names (ERR-FLG-ON) | Custom exception classes |
| CARDDEMO-COMMAREA CDEMO-CU0x-INFO fields | URL path params + query params |

## Password Hashing Pattern

COBOL stores plaintext PIC X(08). Modern equivalent:
- Input: accept plaintext (max 72 bytes for bcrypt)
- Storage: `bcrypt.hashpw(plaintext.encode(), bcrypt.gensalt(rounds=12))`
- Verification: `bcrypt.checkpw(plaintext.encode(), hashed.encode())`
- Never return hash or plaintext in API responses

## Pagination Pattern

COUSR00C STARTBR/READNEXT pattern:
- `page_size=10` (hardcoded in BMS — 10 rows per screen)
- `ORDER BY user_id` (VSAM KSDS key order)
- `OFFSET (page-1)*page_size LIMIT page_size`
- Lookahead: `(page * page_size) < total_count` → has_next_page
- Top-of-list guard: `page > 1` → has_prev_page

## Error Handling Pattern

CICS RESP codes → FastAPI HTTPException:
- DFHRESP(NOTFND) → HTTP 404
- DFHRESP(DUPKEY) / DUPREC → HTTP 409
- No-change (COUSR02C) → HTTP 422
- Unexpected error → HTTP 500
- Admin-only access denied → HTTP 403
