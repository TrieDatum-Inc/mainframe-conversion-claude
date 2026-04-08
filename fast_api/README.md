# CardDemo FastAPI Backend

Modernized AWS CardDemo credit card management system — converted from COBOL/CICS/VSAM mainframe to Python FastAPI with PostgreSQL.

---

## Project Overview

**Source system:** AWS CardDemo — a COBOL/CICS application running on IBM z/OS (or AWS Mainframe Modernization service) with:
- 45 COBOL programs
- 9 VSAM KSDS files (+ alternate indexes)
- 3 DB2 tables
- 62 copybooks
- 21 BMS maps

**Target system:** Python 3.11 FastAPI application with PostgreSQL, SQLAlchemy async ORM, and JWT authentication.

---

## Conversion Traceability Matrix

### COBOL Program → Python Module

| COBOL Program | CICS Transaction | Python Module | HTTP Endpoint |
|---|---|---|---|
| COSGN00C | CC00 | `app/services/auth_service.py` | POST /api/v1/auth/login |
| COACTVWC | CA0V | `app/services/account_service.py` | GET /api/v1/accounts/{id} |
| COACTUPC | CA0U | `app/services/account_service.py` | PUT /api/v1/accounts/{id} |
| COCRDLIC | CC0L | `app/services/card_service.py` | GET /api/v1/cards |
| COCRDSLC | CC0S | `app/services/card_service.py` | GET /api/v1/cards/{card_num} |
| COCRDUPC | CC0U | `app/services/card_service.py` | PUT /api/v1/cards/{card_num} |
| COTRN00C | CT00 | `app/services/transaction_service.py` | GET /api/v1/transactions |
| COTRN01C | CT01 | `app/services/transaction_service.py` | GET /api/v1/transactions/{id} |
| COTRN02C | CT02 | `app/services/transaction_service.py` | POST /api/v1/transactions |
| COBIL00C | CB00 | `app/services/transaction_service.py` | POST /api/v1/transactions/payment |
| COUSR00C | CU00 | `app/services/user_service.py` | GET /api/v1/admin/users |
| COUSR01C | CU01 | `app/services/user_service.py` | POST /api/v1/admin/users |
| COUSR02C | CU02 | `app/services/user_service.py` | PUT /api/v1/admin/users/{id} |
| COUSR03C | CU03 | `app/services/user_service.py` | DELETE /api/v1/admin/users/{id} |

### COBOL Paragraph → Python Function

| Program | Paragraph | Python Function |
|---|---|---|
| COSGN00C | PROCESS-ENTER-KEY | `AuthService.authenticate_user()` |
| COSGN00C | READ-USER-SEC-FILE | `AuthService._verify_credentials()` |
| COACTVWC | READ-PROCESSING | `AccountService.get_account()` |
| COACTUPC | PROCESS-ENTER-KEY | `AccountService.update_account()` |
| COACTUPC | VALIDATE-INPUT-FIELDS | `AccountService._validate_update()` |
| COACTUPC | CHECK-CHANGE-IN-REC | `AccountService._apply_changes()` |
| COCRDLIC | BROWSE-CARDS-FORWARD | `CardService.list_cards(direction='forward')` |
| COCRDLIC | BROWSE-CARDS-BACKWARD | `CardService.list_cards(direction='backward')` |
| COCRDSLC | READ-CARD-DATA | `CardService.get_card()` |
| COCRDUPC | PROCESS-ENTER-KEY | `CardService.update_card()` |
| COTRN00C | BROWSE-TRANSACTIONS | `TransactionService.list_transactions()` |
| COTRN01C | READ-TRANSACTION | `TransactionService.get_transaction()` |
| COTRN02C | PROCESS-ENTER-KEY | `TransactionService.create_transaction()` |
| COBIL00C | PROCESS-PAYMENT | `TransactionService.process_bill_payment()` |
| COUSR00C | BROWSE-USERS | `UserService.list_users()` |
| COUSR01C | PROCESS-ENTER-KEY | `UserService.create_user()` |
| COUSR02C | PROCESS-ENTER-KEY | `UserService.update_user()` |
| COUSR03C | PROCESS-ENTER-KEY | `UserService.delete_user()` |

### Copybook → Pydantic Schema / SQLAlchemy Model

| Copybook | Record Length | SQLAlchemy Model | Pydantic Schema |
|---|---|---|---|
| CVACT01Y.cpy (ACCOUNT-RECORD) | 300 bytes | `models/account.py:Account` | `schemas/account.py` |
| CVACT02Y.cpy (CARD-RECORD) | 150 bytes | `models/card.py:Card` | `schemas/card.py` |
| CVACT03Y.cpy (CARD-XREF-RECORD) | 50 bytes | `models/card.py:CardXref` | — |
| CVCUS01Y.cpy (CUSTOMER-RECORD) | 500 bytes | `models/customer.py:Customer` | — |
| CVTRA05Y.cpy (TRAN-RECORD) | 350 bytes | `models/transaction.py:Transaction` | `schemas/transaction.py` |
| CVTRA01Y.cpy (TRAN-CAT-BAL-RECORD) | 50 bytes | `models/transaction.py:TranCatBalance` | — |
| CVTRA02Y.cpy (DIS-GROUP-RECORD) | 50 bytes | `models/transaction.py:DisclosureGroup` | — |
| CSUSR01Y.cpy (SEC-USER-DATA) | 80 bytes | `models/user.py:User` | `schemas/user.py` |
| COCOM01Y.cpy (CARDDEMO-COMMAREA) | variable | JWT token claims | `schemas/auth.py:TokenData` |

---

## API Design

### Endpoint Summary

| Method | Path | Description | Source COBOL |
|---|---|---|---|
| POST | /api/v1/auth/login | Sign on — returns JWT | COSGN00C (CC00) |
| GET | /api/v1/accounts/{acct_id} | View account + customer | COACTVWC (CA0V) |
| PUT | /api/v1/accounts/{acct_id} | Update account fields | COACTUPC (CA0U) |
| GET | /api/v1/cards | Browse cards (paginated) | COCRDLIC (CC0L) |
| GET | /api/v1/cards/{card_num} | View card details | COCRDSLC (CC0S) |
| PUT | /api/v1/cards/{card_num} | Update card | COCRDUPC (CC0U) |
| GET | /api/v1/transactions | Browse transactions | COTRN00C (CT00) |
| GET | /api/v1/transactions/{tran_id} | View transaction | COTRN01C (CT01) |
| POST | /api/v1/transactions | Create transaction | COTRN02C (CT02) |
| POST | /api/v1/transactions/payment | Process bill payment | COBIL00C (CB00) |
| GET | /api/v1/admin/users | List users (admin only) | COUSR00C (CU00) |
| POST | /api/v1/admin/users | Create user (admin only) | COUSR01C (CU01) |
| GET | /api/v1/admin/users/{id} | View user (admin only) | EXEC CICS READ |
| PUT | /api/v1/admin/users/{id} | Update user (admin only) | COUSR02C (CU02) |
| DELETE | /api/v1/admin/users/{id} | Delete user (admin only) | COUSR03C (CU03) |

### Authentication

JWT Bearer tokens replace CICS COMMAREA (COCOM01Y):
- `sub` claim → CDEMO-USER-ID (PIC X(08))
- `role` claim → CDEMO-USER-TYPE ('A'=admin, 'U'=regular)

### Pagination

All list endpoints use keyset (cursor-based) pagination, mirroring VSAM STARTBR/READNEXT:
- `cursor` parameter = last key from previous page
- SQL equivalent: `WHERE key > :cursor ORDER BY key LIMIT n`
- COBOL equivalent: `EXEC CICS STARTBR ... GTEQ` then `READNEXT`

---

## Database Mapping

### VSAM File → PostgreSQL Table

| VSAM File | CICS Name | Rec Len | PK Type | PostgreSQL Table |
|---|---|---|---|---|
| ACCTDATA.VSAM.KSDS | ACCTDAT | 300 | PIC 9(11) | accounts |
| CARDDATA.VSAM.KSDS | CARDDAT | 150 | PIC X(16) | cards |
| CARDXREF.VSAM.KSDS | CCXREF | 50 | PIC X(16) | card_xref |
| CUSTDATA.VSAM.KSDS | CUSTDAT | 500 | PIC 9(09) | customers |
| TRANSACT.VSAM.KSDS | TRANSACT | 350 | PIC X(16) | transactions |
| USRSEC.VSAM.KSDS | USRSEC | 80 | PIC X(08) | users |
| TRANTYPE.VSAM.KSDS | TRANTYPE | 60 | PIC X(02) | transaction_types |
| TRANCATG.VSAM.KSDS | TRANCATG | 60 | composite | transaction_type_categories |
| TCATBALF.VSAM.KSDS | TCATBALF | 50 | composite | tran_cat_balances |
| DISCGRP.VSAM.KSDS | DISCGRP | 50 | composite | disclosure_groups |

### Alternate Index → PostgreSQL Index

| VSAM AIX | Key Field | PostgreSQL Index |
|---|---|---|
| CARDAIX (on CARDDAT) | CARD-ACCT-ID PIC 9(11) | ix_cards_acct_id |
| CXACAIX (on CCXREF) | XREF-ACCT-ID PIC 9(11) | ix_card_xref_acct_id |

### Data Type Mapping

| COBOL PIC | PostgreSQL | Python |
|---|---|---|
| PIC 9(11) | BIGINT | int |
| PIC 9(09) | INTEGER | int |
| PIC X(n) | VARCHAR(n) or CHAR(n) | str |
| PIC S9(10)V99 COMP-3 | NUMERIC(12,2) | Decimal |
| PIC S9(09)V99 COMP-3 | NUMERIC(11,2) | Decimal |
| PIC S9(04)V99 COMP-3 | NUMERIC(6,2) | Decimal |
| PIC 9(03) | SMALLINT | int |

---

## How to Run

### Prerequisites

- Python 3.11+
- Poetry (`pip install poetry`)
- PostgreSQL 14+

### Installation

```bash
cd fast_api
poetry install
```

### Database Setup

```bash
# Create database
psql -U postgres -c "CREATE USER carddemo WITH PASSWORD 'carddemo';"
psql -U postgres -c "CREATE DATABASE carddemo OWNER carddemo;"

# Create tables
psql -U mridul -d carddemo_3 -f sql/create_tables.sql

# Load seed data
psql -U mridul -d carddemo_3 -f sql/seed_data.sql
```

### Configuration

```bash
cp .env.example .env
# Edit .env: set DATABASE_URL, JWT_SECRET_KEY
```

### Run the Application

```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at: http://localhost:8000/docs

### Run Tests

```bash
# All tests with coverage
poetry run pytest

# Unit tests only
poetry run pytest tests/unit/

# Integration tests only
poetry run pytest tests/integration/

# Specific test file
poetry run pytest tests/unit/test_cobol_compat.py -v
```

---

## Business Rules Catalog

All business rules are preserved from the original COBOL programs:

### Authentication (COSGN00C)

| Rule | Source Location | Python Location |
|---|---|---|
| User ID is uppercased before lookup | COSGN00C:132 `FUNCTION UPPER-CASE` | `AuthService.authenticate_user()` |
| Empty user_id rejected | COSGN00C:118 `WHEN USERIDI = SPACES` | `LoginRequest.user_id` validator |
| RESP=13 → "User not found. Try again ..." | COSGN00C:248 `WHEN 13` | `AuthService.authenticate_user()` |
| Wrong password → "Wrong Password. Try again ..." | COSGN00C:242 `ELSE MOVE 'Wrong Password'` | `AuthService._verify_password()` |
| User type 'A' → admin menu (COADM01C) | COSGN00C:230 `IF CDEMO-USRTYP-ADMIN` | JWT role='A' claim |

### Account Management (COACTVWC / COACTUPC)

| Rule | Source Location | Python Location |
|---|---|---|
| Account view joins CUSTDAT via CCXREF | COACTVWC READ-PROCESSING | `AccountRepository.get_with_customer()` |
| Only admin can update group_id | COACTUPC VALIDATE-INPUT-FIELDS | `AccountService._validate_update()` |
| Read-then-rewrite pattern | COACTUPC PROCESS-ENTER-KEY | `AccountService.update_account()` |
| credit_limit must be >= 0 | COACTUPC input validation | `AccountUpdateRequest.credit_limit` |

### Bill Payment (COBIL00C)

| Rule | Source Location | Python Location |
|---|---|---|
| Payment creates TRANSACT record | COBIL00C WRITE FILE(TRANSACT) | `TransactionService.process_bill_payment()` |
| ACCT-CURR-BAL reduced by payment | COBIL00C REWRITE FILE(ACCTDAT) | `process_bill_payment()` balance update |
| Payment amount must be <= balance | COBIL00C screen validation | `TransactionService.process_bill_payment()` |
| Browse CXACAIX for card lookup | COBIL00C STARTBR CXACAIX | `CardRepository.list_xref_by_account()` |

### Transaction Browsing (COTRN00C)

| Rule | Source Location | Python Location |
|---|---|---|
| Sequential browse by TRAN-ID | COTRN00C STARTBR TRANSACT | `TransactionRepository.list_paginated()` |
| CDEMO-CT00-TRNID-FIRST/LAST | COTRN00C COMMAREA fields | `cursor` / `next_cursor` in response |
| 10 rows per page | COTRN00C screen layout | `limit=10` default |

### User Management (COUSR01C-03C)

| Rule | Source Location | Python Location |
|---|---|---|
| User ID 8-char uppercase padded | COUSR01C PIC X(08) | `pad_user_id()` in `UserService.create_user()` |
| DUPREC on duplicate user_id | COUSR01C RESP=14 | `UserRepository.create()` |
| Read-then-delete pattern | COUSR03C READ + DELETE | `UserRepository.delete()` |
| Password stored as bcrypt hash | N/A (COBOL plaintext) | `AuthService.hash_password()` |

### Interest Calculation (CBACT04C — batch, reference)

| Rule | Source | Python Location (future batch job) |
|---|---|---|
| Monthly interest formula | CBACT04C | `cobol_compat.calculate_monthly_interest()` |
| `interest = balance * rate / 100 / 12` | CBACT04C COMPUTE | `calculate_monthly_interest()` |
| Uses DISCGRP for rate lookup | CBACT04C READ DISCGRP | `disclosure_groups` table |

---

## COBOL Compatibility Utilities

`app/utils/cobol_compat.py` provides:

| Utility | COBOL Equivalent | Usage |
|---|---|---|
| `to_decimal(v, scale)` | PIC S9(n)Vnn COMP-3 | All monetary fields |
| `calculate_monthly_interest()` | CBACT04C COMPUTE | Interest calculation |
| `cobol_move_x(v, n)` | MOVE to PIC X(n) | Field padding/truncation |
| `cobol_trim(v)` | FUNCTION TRIM TRAILING | Display of PIC X fields |
| `cobol_upper(v)` | FUNCTION UPPER-CASE | User ID normalization |
| `cobol_spaces_or_low_values(v)` | = SPACES OR LOW-VALUES | Input validation |
| `pad_user_id(v)` | SEC-USR-ID PIC X(08) | User ID normalization |
| `decode_overpunch(v, scale)` | SIGN TRAILING notation | ASCII data file parsing |
| `parse_cobol_date(v)` | PIC X(10) date fields | Date conversion |
| `parse_cobol_timestamp(v)` | PIC X(26) timestamp | TRAN-ORIG-TS parsing |
| `generate_transaction_id()` | COBIL00C WS-TRAN-ID-NUM | TRAN-ID generation |

---

## CICS RESP Code → HTTP Status Mapping

| CICS RESP Code | Condition | HTTP Status | Exception Class |
|---|---|---|---|
| 0 | NORMAL | 200/201/204 | — |
| 13 | NOTFND | 404 | `RecordNotFoundError` |
| 14 | DUPREC | 409 | `DuplicateRecordError` |
| 22 | LENGERR | 400 | `ValidationError` |
| 27 | INVREQ | 400 | `ValidationError` |
| 70 | NOTAUTH | 403 | `AuthorizationError` |
| other | — | 500 | `FileIOError` |
