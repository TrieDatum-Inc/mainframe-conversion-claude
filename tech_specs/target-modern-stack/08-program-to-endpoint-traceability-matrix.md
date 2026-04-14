# Program-to-Endpoint Traceability Matrix

## Document Purpose

Exhaustive row-per-program and row-per-screen traceability covering all 44 COBOL programs and 21 BMS screens in the CardDemo application. Each row maps the legacy COBOL program or BMS map to its modern equivalent: PostgreSQL table(s), FastAPI endpoint(s), and Next.js route/component. Business logic paragraphs are mapped to service function names. Every known bug and anomaly from the source is noted.

---

## 1. Reading This Document

**Columns explained**:
- **COBOL Program**: Source COBOL program ID and transaction ID (if online)
- **BMS Map(set)**: Associated BMS mapset and map name
- **Module**: Base / Authorization / TranTypeDB2 / VSAM-MQ / Batch
- **COBOL Paragraphs → Service Functions**: Key COBOL PROCEDURE DIVISION paragraphs mapped to Python service function names
- **FastAPI Endpoint(s)**: HTTP method + path for each operation
- **Next.js Route**: App Router path
- **PostgreSQL Tables**: Tables read and/or written
- **Known Issues**: Bugs, anomalies, or copy-paste artifacts from the COBOL source

---

## 2. Online Programs — Base Module

### 2.1 COSGN00C — Sign-On / Authentication

| Attribute | Value |
|-----------|-------|
| Transaction ID | CC00 |
| BMS Mapset/Map | COSGN00 / COSGN0A |
| Module | Base |
| Source File | app/cbl/COSGN00C.cbl |

**Paragraph → Service Function Mapping**:

| COBOL Paragraph | Lines | Service Function | Notes |
|----------------|-------|-----------------|-------|
| MAIN-PARA | 75–130 | `auth_service.authenticate_user()` | EIBCALEN=0 check → 401 if no token |
| PROCESS-ENTER-KEY | 135–170 | `auth_service.authenticate_user()` | Validates non-blank USERIDINI + PASSWDI |
| READ-USER-SEC-FILE | 175–210 | `user_repository.get_by_id()` | VSAM READ → `SELECT * FROM users WHERE user_id = $1` |
| SEND-SIGNON-SCREEN | 215–225 | — | React page render |
| RECEIVE-SIGNON-SCREEN | 230–240 | — | Form submit |

**Endpoint Mapping**:

| COBOL Operation | HTTP Method | Endpoint | Request Body | Response |
|----------------|-------------|----------|-------------|----------|
| ENTER: authenticate user | POST | `/api/v1/auth/login` | `LoginRequest{user_id, password}` | `LoginResponse{access_token, user_type}` |
| PF3: exit | — | Frontend navigation to `/` | — | — |

**Screen → Next.js Route**:

| BMS Map | Field | BMS Attribute | Next.js Component | Notes |
|---------|-------|---------------|------------------|-------|
| COSGN0A | USERIDINI | IC+UNPROT+FSET | `<input autoFocus>` | Auto-focus on load |
| COSGN0A | PASSWDI | DRK+FSET+UNPROT | `<input type="password">` | DRK → password masking |
| COSGN0A | ERRMSG | BRT+RED | `<MessageBar variant="error">` | 78-char EBCDIC color field |

**Next.js Route**: `/` (redirects to `/login`), `/login`

**PostgreSQL Tables**: `users` (READ)

**Known Issues**: None for COSGN00C itself. Systemic issue: plain-text password comparison replaced by bcrypt verify (see `07-security-specification.md` Section 2.2).

---

### 2.2 COMEN01C — Main Menu (Regular Users)

| Attribute | Value |
|-----------|-------|
| Transaction ID | CM00 |
| BMS Mapset/Map | COMEN01 / COMEN1A |
| Module | Base |
| Source File | app/cbl/COMEN01C.cbl |

**Paragraph → Service Function Mapping**:

| COBOL Paragraph | Service Function / Modern Equivalent |
|----------------|--------------------------------------|
| MAIN-PARA | Next.js route `/dashboard`; menu options rendered from `COMEN02Y` copybook constants |
| PROCESS-ENTER-KEY | Frontend router: `router.push(menuOptionRoutes[selectedOption])` |
| RETURN-TO-PREV-SCREEN | `router.push('/login')` on PF3/exit |

**No backend API endpoints** for COMEN01C — it is purely a navigation menu. The 11 menu options map to frontend routes.

**Menu Option → Route Mapping**:

| Option | COBOL Target (XCTL) | Next.js Route |
|--------|---------------------|---------------|
| 1 | COACTVWC | `/accounts/view` |
| 2 | COACTUPC | `/accounts/update` |
| 3 | COCRDLIC | `/cards` |
| 4 | COCRDSLC | `/cards/view` |
| 5 | COCRDUPC | `/cards/update` |
| 6 | COTRN00C | `/transactions` |
| 7 | COTRN01C | `/transactions/view` |
| 8 | COTRN02C | `/transactions/new` |
| 9 | CORPT00C | `/reports` |
| 10 | COBIL00C | `/billing` |
| 11 | COPAUS0C | `/authorizations` |

**Screen → Next.js Route**: `/dashboard`

**PostgreSQL Tables**: None

---

### 2.3 COADM01C — Admin Menu

| Attribute | Value |
|-----------|-------|
| Transaction ID | CA00 |
| BMS Mapset/Map | COADM01 / COADM1A |
| Module | Base |
| Source File | app/cbl/COADM01C.cbl |

**No backend API endpoints** — pure navigation menu for admins. 6 options from `COADM02Y` copybook.

**Menu Option → Route Mapping**:

| Option | COBOL Target (XCTL) | Next.js Route |
|--------|---------------------|---------------|
| 1 | COUSR01C | `/admin/users/new` |
| 2 | COUSR00C | `/admin/users` |
| 3 | COUSR02C | `/admin/users/update` |
| 4 | COUSR03C | `/admin/users/delete` |
| 5 | COTRTLIC | `/admin/transaction-types` |
| 6 | COTRTUPC | `/admin/transaction-types/new` |

**Access Control**: All `/admin/*` routes are protected by `require_admin` dependency; non-admin users redirected to `/dashboard` by Next.js middleware.

**Screen → Next.js Route**: `/admin`

**PostgreSQL Tables**: None

---

### 2.4 COACTVWC — Account View

| Attribute | Value |
|-----------|-------|
| Transaction ID | CAVW |
| BMS Mapset/Map | COACTVW / COACTVWA |
| Module | Base |
| Source File | app/cbl/COACTVWC.cbl |

**Paragraph → Service Function Mapping**:

| COBOL Paragraph | Service Function |
|----------------|-----------------|
| PROCESS-ENTER-KEY | `account_service.get_account_detail()` |
| READ-ACCT-DATA | `account_repository.get_by_id()` → `SELECT * FROM accounts WHERE account_id = $1` |
| READ-CUST-DATA | `customer_repository.get_by_account_id()` → `SELECT * FROM customers WHERE account_id = $1` |
| READ-CARD-DATA (CARDAIX browse) | `card_repository.list_by_account_id()` → `SELECT * FROM credit_cards WHERE account_id = $1` |
| POPULATE-HEADER-INFO | Header fields populated from JWT claims |

**Endpoint Mapping**:

| COBOL Operation | HTTP Method | Endpoint | Response |
|----------------|-------------|----------|----------|
| ENTER: look up account | GET | `/api/v1/accounts/{account_id}` | `AccountDetailResponse` |
| Read customer (embedded) | GET | `/api/v1/accounts/{account_id}` | Includes customer sub-object |
| Read cards (embedded) | GET | `/api/v1/accounts/{account_id}/cards` | `CreditCardResponse[]` |

**Screen Field → API Field Mapping**:

| BMS Field | Direction | COBOL Source | API Response Field |
|-----------|-----------|-------------|-------------------|
| ACCTSID | Input | User-entered account ID | Path param `account_id` |
| ACRDLIM | Output | ACCT-CREDIT-LIMIT COMP-3 | `credit_limit` NUMERIC(12,2) |
| ACSHLIM | Output | ACCT-CASH-CREDIT-LIMIT COMP-3 | `cash_credit_limit` NUMERIC(12,2) |
| ACURBAL | Output | ACCT-CURR-BAL COMP-3 | `current_balance` NUMERIC(12,2) |
| ACRCYCR | Output | ACCT-CURR-CYC-CREDIT COMP-3 | `curr_cycle_credit` NUMERIC(12,2) |
| ACRCYDB | Output | ACCT-CURR-CYC-DEBIT COMP-3 | `curr_cycle_debit` NUMERIC(12,2) |
| OPNYEAR/OPNMON/OPNDAY | Output | ACCT-OPEN-DATE X(10) | `open_date` DATE (formatted YYYY-MM-DD) |

**Screen → Next.js Route**: `/accounts/view`

**PostgreSQL Tables**: `accounts` (READ), `customers` (READ), `credit_cards` (READ)

---

### 2.5 COACTUPC — Account Update

| Attribute | Value |
|-----------|-------|
| Transaction ID | — (no dedicated transaction; entered via COMEN01C) |
| BMS Mapset/Map | COACTUP / COACTUPA |
| Module | Base |
| Source File | app/cbl/COACTUPC.cbl |

**Paragraph → Service Function Mapping**:

| COBOL Paragraph | Service Function |
|----------------|-----------------|
| PROCESS-ENTER-KEY | `account_service.get_account_for_update()` |
| UPDATE-ACCOUNT-DATA | `account_service.update_account()` |
| VALIDATE-INPUT-KEY-FIELDS | `account_service.validate_account_update()` (Pydantic validators) |
| CALL CSUTLDTC | `date_validation_service.validate_date()` → Python `datetime` parsing |
| WRITE-UPDATE-DB | `account_repository.update()` → `UPDATE accounts SET ... WHERE account_id = $1` |

**Endpoint Mapping**:

| COBOL Operation | HTTP Method | Endpoint | Request/Response |
|----------------|-------------|----------|-----------------|
| ENTER: look up account | GET | `/api/v1/accounts/{account_id}` | `AccountDetailResponse` |
| PF5: save changes | PUT | `/api/v1/accounts/{account_id}` | `AccountUpdateRequest` → `AccountDetailResponse` |

**Split Field Reconstruction** (BMS has split date/SSN/phone; API accepts unified):

| BMS Fields (split) | API Field (unified) |
|-------------------|---------------------|
| OPNYEAR + OPNMON + OPNDAY | `open_date: date` |
| ACTSSN1(3) + ACTSSN2(2) + ACTSSN3(4) | `ssn: str` (9-digit; encrypted on server) |
| ACSPH1A + ACSPH1B + ACSPH1C | `phone_number_1: str` |

**Initially-DRK buttons** (BMS FKEY05/FKEY12 begin DRK):
- Frontend `showSaveCancel: boolean` state initialized to `false`
- Set to `true` after successful account data load
- `Save (F5)` and `Cancel (F12)` buttons rendered conditionally

**Screen → Next.js Route**: `/accounts/update`

**PostgreSQL Tables**: `accounts` (READ, UPDATE), `customers` (READ)

**Known Issues**: CSUTLDTC LINK replaced by Python `datetime.strptime` validation; no separate service call needed.

---

### 2.6 COCRDLIC — Credit Card List

| Attribute | Value |
|-----------|-------|
| Transaction ID | CC00 |
| BMS Mapset/Map | COCRDLI / CCRDLIA |
| Module | Base |
| Source File | app/cbl/COCRDLIC.cbl |

**Paragraph → Service Function Mapping**:

| COBOL Paragraph | Service Function |
|----------------|-----------------|
| MAIN-PARA / PROCESS-ENTER-KEY | `card_service.list_cards()` |
| STARTBR / READNEXT / ENDBR | `card_repository.list_paginated()` → `SELECT ... LIMIT $page_size OFFSET $offset` |
| PF7 READPREV | `card_repository.list_paginated(page=page-1)` |
| PF8 READNEXT | `card_repository.list_paginated(page=page+1)` |

**Endpoint Mapping**:

| COBOL Operation | HTTP Method | Endpoint | Query Params |
|----------------|-------------|----------|-------------|
| ENTER: list/filter cards | GET | `/api/v1/cards` | `account_id`, `card_number`, `page`, `page_size` |
| PF7: previous page | GET | `/api/v1/cards` | `page=page-1` |
| PF8: next page | GET | `/api/v1/cards` | `page=page+1` |
| Select row (ENTER on selected row) | GET | `/api/v1/cards/{card_number}` | — |

**7-row display**: BMS shows 7 data rows (CRDSEL1–7, CRDSTP2–7). Frontend renders a paginated table with page_size=7 to match. Row selection navigates to `/cards/view/{card_number}`.

**Screen → Next.js Route**: `/cards`

**PostgreSQL Tables**: `credit_cards` (READ), `accounts` (READ for filter)

---

### 2.7 COCRDSLC — Credit Card View / Select

| Attribute | Value |
|-----------|-------|
| Transaction ID | CCDL |
| BMS Mapset/Map | COCRDSL / CCRDSLA |
| Module | Base |
| Source File | app/cbl/COCRDSLC.cbl |

**Paragraph → Service Function Mapping**:

| COBOL Paragraph | Service Function |
|----------------|-----------------|
| PROCESS-ENTER-KEY | `card_service.get_card_detail()` |
| READ-CARD-DATA | `card_repository.get_by_number()` |

**Endpoint Mapping**:

| COBOL Operation | HTTP Method | Endpoint |
|----------------|-------------|----------|
| ENTER: look up card | GET | `/api/v1/cards/{card_number}` |

**Key difference from COCRDUPC**: `ACCTSID` is `UNPROT` on COCRDSL (user can change account ID to search), vs `PROT` on COCRDUP (locked after data load). Frontend: COCRDSL has both account_id and card_number as editable search fields.

**Screen → Next.js Route**: `/cards/view`

**PostgreSQL Tables**: `credit_cards` (READ), `accounts` (READ)

---

### 2.8 COCRDUPC — Credit Card Update

| Attribute | Value |
|-----------|-------|
| Transaction ID | — |
| BMS Mapset/Map | COCRDUP / CCRDUPA |
| Module | Base |
| Source File | app/cbl/COCRDUPC.cbl |

**Paragraph → Service Function Mapping**:

| COBOL Paragraph | Service Function |
|----------------|-----------------|
| PROCESS-ENTER-KEY | `card_service.get_card_for_update()` |
| UPDATE-CARD-DATA | `card_service.update_card()` |
| WRITE-UPDATE-DB | `card_repository.update()` → `UPDATE credit_cards SET ... WHERE card_number = $1` |

**Endpoint Mapping**:

| COBOL Operation | HTTP Method | Endpoint |
|----------------|-------------|----------|
| ENTER: look up card | GET | `/api/v1/cards/{card_number}` |
| PF5: save changes | PUT | `/api/v1/cards/{card_number}` |

**Optimistic locking**: `updated_at` returned as `optimistic_lock_version` in GET response; included in PUT body; backend returns 409 if timestamp mismatch (record changed between GET and PUT).

**EXPDAY hidden field** (COCRDUP EXPDAY DRK+FSET+PROT): Day component of expiry date. Never displayed; preserved as TypeScript type field `expiration_day: number`; included in PUT payload for data integrity.

**Initially-DRK FKEYSC button** (F5=Save F12=Cancel label): `showSaveCancel: boolean` state initialized `false`; set `true` after card data loaded.

**Screen → Next.js Route**: `/cards/update`

**PostgreSQL Tables**: `credit_cards` (READ, UPDATE)

---

### 2.9 COTRN00C — Transaction List

| Attribute | Value |
|-----------|-------|
| Transaction ID | CT00 |
| BMS Mapset/Map | COTRN00 / COTRN0A |
| Module | Base |
| Source File | app/cbl/COTRN00C.cbl |

**Paragraph → Service Function Mapping**:

| COBOL Paragraph | Service Function |
|----------------|-----------------|
| MAIN-PARA | `transaction_service.list_transactions()` |
| STARTBR/READNEXT/ENDBR | `transaction_repository.list_paginated()` |
| PF7 | `transaction_repository.list_paginated(page=page-1)` |
| PF8 | `transaction_repository.list_paginated(page=page+1)` |

**Endpoint Mapping**:

| COBOL Operation | HTTP Method | Endpoint | Query Params |
|----------------|-------------|----------|-------------|
| ENTER: list transactions | GET | `/api/v1/transactions` | `account_id`, `card_number`, `page`, `page_size` (default 10) |
| PF7: previous page | GET | `/api/v1/transactions` | `page=page-1` |
| PF8: next page | GET | `/api/v1/transactions` | `page=page+1` |
| Select row | GET | `/api/v1/transactions/{transaction_id}` | — |

**10-row display**: BMS shows 10 rows (SEL0001–SEL0010). Frontend page_size=10.

**Screen → Next.js Route**: `/transactions`

**PostgreSQL Tables**: `transactions` (READ)

---

### 2.10 COTRN01C — Transaction View

| Attribute | Value |
|-----------|-------|
| Transaction ID | — |
| BMS Mapset/Map | COTRN01 / COTRN1A |
| Module | Base |
| Source File | app/cbl/COTRN01C.cbl |

**Endpoint Mapping**:

| COBOL Operation | HTTP Method | Endpoint |
|----------------|-------------|----------|
| ENTER: fetch transaction | GET | `/api/v1/transactions/{transaction_id}` |
| PF4: clear fields | Frontend state reset | — |
| PF5: browse transactions | GET | `/api/v1/transactions` (navigates to list) |

**Known Issue — COTRN01C READ UPDATE bug**: The COBOL program issues `EXEC CICS READ DATASET(TRANSACT) UPDATE` for a display-only operation. This holds an exclusive lock on the transaction record for the entire CICS interaction cycle, creating a potential denial-of-service for high-volume read operations. The modern `GET /api/v1/transactions/{id}` uses a plain SELECT with no lock. This is documented in the overall specification (section 12) and is intentionally corrected.

**Screen → Next.js Route**: `/transactions/view`

**PostgreSQL Tables**: `transactions` (READ — no lock, correcting COBOL bug)

---

### 2.11 COTRN02C — Transaction Add

| Attribute | Value |
|-----------|-------|
| Transaction ID | — |
| BMS Mapset/Map | COTRN02 / COTRN2A |
| Module | Base |
| Source File | app/cbl/COTRN02C.cbl |

**Paragraph → Service Function Mapping**:

| COBOL Paragraph | Service Function |
|----------------|-----------------|
| PROCESS-ENTER-KEY | `transaction_service.validate_transaction_input()` |
| VALIDATE-INPUT-KEY-FIELDS | Pydantic `TransactionCreateRequest` validators |
| READ-ACCT-DATA | `account_repository.get_by_id()` (validate account exists) |
| READ-CARD-DATA (CCXREF) | `card_repository.get_xref_by_card()` (validate card belongs to account) |
| GET-DB-KEY | `NEXTVAL('transaction_id_seq')` (atomic; replaces STARTBR+READPREV) |
| WRITE-TRANSACT-FILE | `transaction_repository.create()` → `INSERT INTO transactions` |
| CALL CSUTLDTC | Python `datetime` validation for transaction date |

**Endpoint Mapping**:

| COBOL Operation | HTTP Method | Endpoint |
|----------------|-------------|----------|
| ENTER → PF5: add transaction | POST | `/api/v1/transactions` |
| PF5: copy last transaction | GET | `/api/v1/transactions?account_id={id}&limit=1&sort=desc` |

**Known Issue — COTRN02C Race Condition**: COBOL generates transaction ID via STARTBR from HIGH-VALUES + READPREV + ADD 1. Concurrent users can generate duplicate IDs. Replaced with PostgreSQL `NEXTVAL('transaction_id_seq')` which is atomic and conflict-free.

**Screen → Next.js Route**: `/transactions/new`

**PostgreSQL Tables**: `transactions` (READ for copy-last, WRITE for create), `accounts` (READ for validation), `credit_cards` (READ for validation), `card_account_xref` (READ for validation)

---

### 2.12 COBIL00C — Bill Payment

| Attribute | Value |
|-----------|-------|
| Transaction ID | — |
| BMS Mapset/Map | COBIL00 / COBIL0A |
| Module | Base |
| Source File | app/cbl/COBIL00C.cbl |

**Two-phase flow**:
1. Phase 1 (ENTER with account ID): Look up account, display current balance → GET endpoint
2. Phase 2 (ENTER with CONFIRM='Y'): Post payment → POST endpoint

**Paragraph → Service Function Mapping**:

| COBOL Paragraph | Service Function |
|----------------|-----------------|
| PROCESS-ENTER-KEY (lookup) | `billing_service.get_account_balance()` |
| PROCESS-ENTER-KEY (confirm) | `billing_service.post_payment()` |
| MQ request to COACCT01 (account data) | Replaced by direct `account_repository.get_by_id()` |
| MQ request to CODATE01 (current date) | Replaced by `datetime.now(tz=UTC)` |
| CICS SYNCPOINT | SQLAlchemy session commit (single atomic transaction) |

**Endpoint Mapping**:

| COBOL Operation | HTTP Method | Endpoint |
|----------------|-------------|----------|
| ENTER: look up account | GET | `/api/v1/billing/account/{account_id}` |
| ENTER with CONFIRM='Y': post payment | POST | `/api/v1/billing/payment` |

**Known Issue — ZIP Code Bug (COACCT01)**: COBOL MQ reply from COACCT01 drops ACCT-ADDR-ZIP (present in VSAM, not included in MQ message). The modern `billing_service.get_account_balance()` reads directly from PostgreSQL `accounts` and always includes `zip_code`.

**Screen → Next.js Route**: `/billing`

**PostgreSQL Tables**: `accounts` (READ, UPDATE for payment posting), `transactions` (WRITE — payment creates a transaction record)

---

### 2.13 CORPT00C — Report Request

| Attribute | Value |
|-----------|-------|
| Transaction ID | CR00 |
| BMS Mapset/Map | CORPT00 / CORPT0A |
| Module | Base |
| Source File | app/cbl/CORPT00C.cbl |

**Paragraph → Service Function Mapping**:

| COBOL Paragraph | Service Function |
|----------------|-----------------|
| PROCESS-ENTER-KEY | `report_service.request_report()` |
| CALL CSUTLDTC | Python `datetime` date range validation |
| WIRTE-JOBSUB-TDQ (sic) | `report_service.submit_report_job()` — submits background task |
| BUILD-JCL | Replaced by background task or async worker |

**Endpoint Mapping**:

| COBOL Operation | HTTP Method | Endpoint |
|----------------|-------------|----------|
| ENTER: submit report | POST | `/api/v1/reports/request` |
| Check job status (new) | GET | `/api/v1/reports/status/{job_id}` |

**Known Issues**:
- `WIRTE-JOBSUB-TDQ`: Typo in COBOL source (WIRTE vs WRITE). Preserved as comment in Python code; modern function correctly named `write_job_submission`.
- Hardcoded JCL path `'AWS.M2.CARDDEMO.PROC'`: Replaced by configurable `settings.REPORT_TEMPLATE_PATH`.

**Screen → Next.js Route**: `/reports`

**PostgreSQL Tables**: None for immediate report trigger; background worker reads `transactions` and `accounts`

---

### 2.14 COUSR00C — User List

| Attribute | Value |
|-----------|-------|
| Transaction ID | CU00 |
| BMS Mapset/Map | COUSR00 / COUSR0A |
| Module | Base |
| Source File | app/cbl/COUSR00C.cbl |
| Access | Admin only |

**Paragraph → Service Function Mapping**:

| COBOL Paragraph | Service Function |
|----------------|-----------------|
| STARTBR/READNEXT/ENDBR (USRSEC) | `user_repository.list_paginated()` → `SELECT ... FROM users LIMIT $ps OFFSET $off ORDER BY user_id` |
| PF7/PF8 | Pagination via `page` param |
| Select 'U' → COUSR02C | Frontend: navigate to `/admin/users/{user_id}/edit` |
| Select 'D' → COUSR03C | Frontend: navigate to `/admin/users/{user_id}/delete` |

**Endpoint Mapping**:

| COBOL Operation | HTTP Method | Endpoint |
|----------------|-------------|----------|
| ENTER: list users (paged) | GET | `/api/v1/users?page={n}&page_size=10` |
| PF7: previous page | GET | `/api/v1/users?page={n-1}` |
| PF8: next page | GET | `/api/v1/users?page={n+1}` |

**10-row display**: BMS shows 10 rows (SEL0001–SEL0010). Frontend page_size=10.

**Screen → Next.js Route**: `/admin/users`

**PostgreSQL Tables**: `users` (READ)

**Access Control**: `require_admin` dependency on all `/api/v1/users` endpoints.

---

### 2.15 COUSR01C — User Add

| Attribute | Value |
|-----------|-------|
| Transaction ID | — |
| BMS Mapset/Map | COUSR01 / COUSR1A |
| Module | Base |
| Source File | app/cbl/COUSR01C.cbl |
| Access | Admin only |

**Paragraph → Service Function Mapping**:

| COBOL Paragraph | Service Function |
|----------------|-----------------|
| PROCESS-ENTER-KEY (validate) | `user_service.validate_new_user()` (Pydantic) |
| WRITE-USER-SEC-FILE | `user_repository.create()` → `INSERT INTO users` |
| Hash password | `security.hash_password(plain_text)` (new; no equivalent in COBOL) |

**Endpoint Mapping**:

| COBOL Operation | HTTP Method | Endpoint |
|----------------|-------------|----------|
| ENTER + PF5: add user | POST | `/api/v1/users` |

**Field validations (from COBOL PROCESS-ENTER-KEY)**:
- FNAME non-blank → `first_name: str = Field(..., min_length=1, max_length=20)`
- LNAME non-blank → `last_name: str = Field(..., min_length=1, max_length=20)`
- USERID non-blank, unique → `user_id: str = Field(..., min_length=1, max_length=8)` + DB unique check
- PASSWD non-blank → `password: str = Field(..., min_length=8, max_length=72)`
- USRTYPE IN ('A','U') → `user_type: Literal['A','U']`

**Screen → Next.js Route**: `/admin/users/new`

**PostgreSQL Tables**: `users` (READ for uniqueness check, WRITE for create)

---

### 2.16 COUSR02C — User Update

| Attribute | Value |
|-----------|-------|
| Transaction ID | CU02 |
| BMS Mapset/Map | COUSR02 / COUSR2A |
| Module | Base |
| Source File | app/cbl/COUSR02C.cbl |
| Access | Admin only |

**Paragraph → Service Function Mapping**:

| COBOL Paragraph | Service Function |
|----------------|-----------------|
| PROCESS-ENTER-KEY | `user_service.get_user_for_update()` |
| READ-USER-SEC-FILE | `user_repository.get_by_id()` |
| UPDATE-USER-INFO | `user_service.update_user()` |
| Field-level change detection (lines 219–234) | `useFormWithChanges` hook (frontend); backend also checks for no-op |
| UPDATE-USER-SEC-FILE (REWRITE) | `user_repository.update()` → `UPDATE users SET ... WHERE user_id = $1` |

**Endpoint Mapping**:

| COBOL Operation | HTTP Method | Endpoint |
|----------------|-------------|----------|
| ENTER: look up user | GET | `/api/v1/users/{user_id}` |
| PF5: save changes | PUT | `/api/v1/users/{user_id}` |
| PF3: save and exit | PUT then navigate | PUT `/api/v1/users/{user_id}` then `router.back()` |

**No-change detection**: COBOL checks each field against stored value; if no field changed, returns "Please modify to update..." error in DFHRED. Modern equivalent: if PUT body matches current values, return `422 {"error_code": "NO_CHANGES", "message": "Please modify to update..."}`.

**Screen → Next.js Route**: `/admin/users/{user_id}/edit`

**PostgreSQL Tables**: `users` (READ, UPDATE)

---

### 2.17 COUSR03C — User Delete

| Attribute | Value |
|-----------|-------|
| Transaction ID | CU03 |
| BMS Mapset/Map | COUSR03 / COUSR3A |
| Module | Base |
| Source File | app/cbl/COUSR03C.cbl |
| Access | Admin only |

**Paragraph → Service Function Mapping**:

| COBOL Paragraph | Service Function |
|----------------|-----------------|
| PROCESS-ENTER-KEY | `user_service.get_user_for_delete()` |
| READ-USER-SEC-FILE (UPDATE lock) | `user_repository.get_by_id()` (plain SELECT; lock not needed in REST model) |
| DELETE-USER-INFO | `user_service.delete_user()` |
| DELETE-USER-SEC-FILE | `user_repository.delete()` → `DELETE FROM users WHERE user_id = $1` |
| INITIALIZE-ALL-FIELDS (after delete) | Frontend: form state reset after successful DELETE |

**Endpoint Mapping**:

| COBOL Operation | HTTP Method | Endpoint |
|----------------|-------------|----------|
| ENTER: look up user for confirmation | GET | `/api/v1/users/{user_id}` |
| PF5: confirm delete | DELETE | `/api/v1/users/{user_id}` |

**Two-step delete workflow preserved**: ENTER → display name/type for confirmation → PF5 → delete. Frontend shows confirmation dialog after GET response.

**Password not displayed**: COUSR3A map has no PASSWDI field (by design — unlike COUSR02C). Frontend delete screen has no password field — matches the COBOL intent.

**COBOL Re-read pattern**: COBOL re-reads with UPDATE lock before DELETE because CICS RETURN releases locks between interactions. REST is stateless — the DELETE endpoint simply re-reads and deletes atomically within one transaction. No explicit re-read needed.

**Known Issues**:
- Delete failure error message says "Unable to Update User..." (copy-paste from COUSR02C). Modern API returns `"error_code": "DELETE_FAILED", "message": "Unable to delete user"` (corrected).
- `WS-USR-MODIFIED` defined but never used in COUSR03C — dead working storage. No equivalent in modern code.

**Screen → Next.js Route**: `/admin/users/{user_id}/delete`

**PostgreSQL Tables**: `users` (READ, DELETE)

---

### 2.18 CSUTLDTC — Date Validation Utility (LINK Subroutine)

| Attribute | Value |
|-----------|-------|
| Transaction ID | — (LINK only, not XCTL) |
| BMS Map | None |
| Module | Base |
| Source File | app/cbl/CSUTLDTC.cbl |

**No API endpoint.** Replaced by Python standard library `datetime` parsing.

**Callers in COBOL**: COACTUPC (account open date), COTRN02C (transaction date), CORPT00C (report date range)

**Modern equivalent**:
```python
# In each service that validates dates:
def validate_date(year: int, month: int, day: int) -> date:
    """
    COBOL origin: Replaces EXEC CICS LINK PROGRAM('CSUTLDTC').
    CSUTLDTC used IBM LE CEEDAYS for date arithmetic and validation.
    """
    try:
        return date(year, month, day)
    except ValueError:
        raise ValueError(f"Invalid date: {year:04d}-{month:02d}-{day:02d}")
```

**PostgreSQL Tables**: None

---

## 3. Online Programs — Authorization Module

### 3.1 COPAUS0C — Pending Authorization Summary List

| Attribute | Value |
|-----------|-------|
| Transaction ID | CPVS |
| BMS Mapset/Map | COPAU00 / COPAU0A |
| Module | Authorization |
| Source File | app/cbl/COPAUS0C.cbl |
| Access | Admin only |

**Paragraph → Service Function Mapping**:

| COBOL Paragraph | Service Function |
|----------------|-----------------|
| DL/I GU to PAUTHSUM | `authorization_repository.list_summary()` → `SELECT ... FROM pending_authorizations GROUP BY card_number` |
| DL/I GN (browse) | `authorization_repository.list_summary_paginated()` |
| PF7/PF8 | SQL LIMIT/OFFSET pagination |
| Select row → COPAUS1C | Navigate to `/admin/authorizations/{card_number}` |

**Endpoint Mapping**:

| COBOL Operation | HTTP Method | Endpoint |
|----------------|-------------|----------|
| ENTER: list authorization summaries | GET | `/api/v1/authorizations?page={n}` |

**Screen → Next.js Route**: `/admin/authorizations`

**PostgreSQL Tables**: `pending_authorizations` (READ with GROUP BY aggregation)

---

### 3.2 COPAUS1C — Pending Authorization Detail View

| Attribute | Value |
|-----------|-------|
| Transaction ID | CPVD |
| BMS Mapset/Map | COPAU01 / COPAU1A |
| Module | Authorization |
| Source File | app/cbl/COPAUS1C.cbl |
| Access | Admin only |

**Paragraph → Service Function Mapping**:

| COBOL Paragraph | Service Function |
|----------------|-----------------|
| DL/I GU to PAUTHDTL | `authorization_repository.get_detail_by_card()` |
| LINK to COPAUS2C (PF5) | `fraud_flag_service.toggle_fraud_flag()` (inline; no separate LINK) |

**Endpoint Mapping**:

| COBOL Operation | HTTP Method | Endpoint |
|----------------|-------------|----------|
| ENTER: view auth detail | GET | `/api/v1/authorizations/{card_number}` |
| PF5: toggle fraud flag | POST | `/api/v1/authorizations/{card_number}/fraud-flag` |

**Screen → Next.js Route**: `/admin/authorizations/{card_number}`

**PostgreSQL Tables**: `pending_authorizations` (READ), `fraud_flags` (READ for current flag state)

---

### 3.3 COPAUS2C — Fraud Flag Toggle

| Attribute | Value |
|-----------|-------|
| Transaction ID | CPVD (shared with COPAUS1C) |
| BMS Map | None (LINK subroutine; no screen) |
| Module | Authorization |
| Source File | app/cbl/COPAUS2C.cbl |
| Access | Admin only |

**COBOL behavior**: COPAUS2C is invoked via CICS LINK from COPAUS1C. It performs a DB2 INSERT or UPDATE on AUTHFRDS (fraud flag table) then returns to COPAUS1C. It also updates IMS (CICS SYNCPOINT commits both DB2 and IMS changes atomically).

**Modern equivalent**: `fraud_flag_service.toggle_fraud_flag()` — single atomic PostgreSQL transaction updating `fraud_flags` and `pending_authorizations.fraud_flagged` in one commit.

**Known Issue**: COPAUS2C performs a two-phase commit: IMS REPL (update PAUTHDTL) + DB2 INSERT (AUTHFRDS) + CICS SYNCPOINT. Modern equivalent is a single PostgreSQL transaction (all in one database; no distributed commit needed).

**Endpoint**: Part of `POST /api/v1/authorizations/{card_number}/fraud-flag` (see COPAUS1C)

**PostgreSQL Tables**: `fraud_flags` (INSERT/UPDATE), `pending_authorizations` (UPDATE fraud_flagged)

---

### 3.4 COPAUA0C — Authorization MQ Processor (Batch/Trigger)

| Attribute | Value |
|-----------|-------|
| Transaction ID | CP00 |
| BMS Map | None (MQ trigger program) |
| Module | Authorization |
| Source File | app/cbl/COPAUA0C.cbl |

**No API endpoint in the modern web application.** This is an MQ-triggered batch program that:
1. Receives authorization request messages from IBM MQ
2. Validates card and account via VSAM
3. Writes to IMS PAUTHDTL
4. Sends MQ response

**Modern equivalent**: A background worker service (Celery task or FastAPI background task) that accepts authorization requests via a REST endpoint or message queue adapter. Not in scope for the primary web application conversion.

**If modernized**: `POST /api/v1/authorizations/process` (internal endpoint, not user-facing)

**PostgreSQL Tables**: `cards` (READ), `accounts` (READ), `pending_authorizations` (WRITE)

---

## 4. Online Programs — Transaction Type DB2 Module

### 4.1 COTRTLIC — Transaction Type List

| Attribute | Value |
|-----------|-------|
| Transaction ID | CTLI |
| BMS Mapset/Map | COTRTLI / CTRTLIA |
| Module | TranTypeDB2 |
| Source File | app/cbl/COTRTLIC.cbl |
| Access | Admin only |

**Paragraph → Service Function Mapping**:

| COBOL Paragraph | Service Function |
|----------------|-----------------|
| DB2 SELECT TRNTYPE (cursor OPEN/FETCH/CLOSE) | `tran_type_repository.list_paginated()` |
| Select 'U' → COTRTUPC | Navigate to `/admin/transaction-types/{code}/edit` |
| Select 'D' | `tran_type_service.delete_transaction_type()` |

**Endpoint Mapping**:

| COBOL Operation | HTTP Method | Endpoint |
|----------------|-------------|----------|
| ENTER: list transaction types | GET | `/api/v1/transaction-types?page={n}` |
| Select 'D': delete type | DELETE | `/api/v1/transaction-types/{type_code}` |
| PF7/PF8: pagination | GET | `/api/v1/transaction-types?page={n}` |

**8th row always protected**: BMS defines 8 rows but WS-MAX-SCREEN-LINES=7. The 8th row (TRTSELA/TRTTYPA/TRTDSCA) is never populated. Frontend renders exactly 7 data rows per page; 8th row never rendered.

**Screen → Next.js Route**: `/admin/transaction-types`

**PostgreSQL Tables**: `transaction_types` (READ, DELETE)

---

### 4.2 COTRTUPC — Transaction Type Add/Edit (15-State Machine)

| Attribute | Value |
|-----------|-------|
| Transaction ID | CTTU |
| BMS Mapset/Map | COTRTUP / CTRTUPA |
| Module | TranTypeDB2 |
| Source File | app/cbl/COTRTUPC.cbl |
| Access | Admin only |

**15-state machine**: COTRTUPC uses WS-CA-SCREEN-STATE (15 possible values) to manage a complex state machine for the add/edit/view workflow. The REST API is stateless; state is managed entirely on the frontend.

**State mapping** (15 COBOL states → ~8 React UI states):

| COBOL State(s) | React UI State | Description |
|---------------|----------------|-------------|
| S001 (initial blank form) | `mode: 'initial'` | Empty form |
| S002 (new type ready) | `mode: 'new_entered'` | Type code entered, not saved |
| S003 (existing displayed) | `mode: 'existing_loaded'` | Fetched from DB |
| S004–S006 (saving) | `mode: 'saving'` | PUT/POST in flight |
| S007 (saved success) | `mode: 'saved'` | Success message displayed |
| S008–S010 (delete confirm) | `mode: 'confirm_delete'` | Confirmation dialog |
| S011–S012 (error) | `mode: 'error'` | Error message displayed |
| S013–S015 (not found) | `mode: 'not_found'` | Type code not in DB |

**Endpoint Mapping**:

| COBOL Operation | HTTP Method | Endpoint |
|----------------|-------------|----------|
| Look up transaction type | GET | `/api/v1/transaction-types/{type_code}` |
| Add new type | POST | `/api/v1/transaction-types` |
| Update type | PUT | `/api/v1/transaction-types/{type_code}` |

**Known Issues**:
- F6=Add label in BMS (FKEYSC6) is never made visible by COTRTUPC program logic. Frontend: F6/Add button not rendered.
- `DCLTRCAT` included in COBOL program but no SQL against `TRANSACTION_TYPE_CATEGORY` table. Frontend: no category field rendered.

**Screen → Next.js Route**: `/admin/transaction-types/new`, `/admin/transaction-types/{code}/edit`

**PostgreSQL Tables**: `transaction_types` (READ, INSERT, UPDATE)

---

## 5. Batch Programs

### 5.1 Batch Program → Modern Equivalent Mapping

All batch COBOL programs are replaced by either:
- Scheduled PostgreSQL queries run by a job scheduler (pg_cron or external CRON)
- Background FastAPI tasks submitted via API
- Database stored procedures or views (for reporting aggregation)

| COBOL Batch Program | JCL | Function | Modern Equivalent |
|--------------------|-----|----------|------------------|
| CBACT01C | READACCT.jcl | Account file read/report | `GET /api/v1/reports/accounts` or pg_cron scheduled query |
| CBACT02C | — | Account list report | SQL `SELECT` + CSV export endpoint |
| CBACT03C | — | Account details extract | `GET /api/v1/accounts?export=true` |
| CBACT04C | — | Account update batch | `PUT /api/v1/accounts/batch` (bulk update endpoint) |
| CBCUS01C | READCUST.jcl | Customer file report | SQL query + report endpoint |
| CBTRN01C | — | Transaction processing report | SQL aggregation query |
| CBTRN02C | TRANREPT.jcl | Transaction category report | `POST /api/v1/reports/request` (category) |
| CBTRN03C | TRANBKP.jcl | Transaction purge/archive | Scheduled task: `DELETE FROM transactions WHERE processed_date < $cutoff` |
| CBSTM03A | CREASTMT.JCL | Statement generation phase A | Background task: collect transactions per account |
| CBSTM03B | CREASTMT.JCL | Statement generation phase B | Background task: format and generate PDF |
| CBEXPORT | CBEXPORT.jcl | VSAM data export | `GET /api/v1/export/{entity}?format=csv` |
| CBIMPORT | CBIMPORT.jcl | VSAM data import | `POST /api/v1/import/{entity}` |
| COBSWAIT | WAITSTEP.jcl | MVS wait utility | Not needed; no mainframe wait semantics in modern system |
| COBTUPDT | MNTTRDB2.jcl | Batch transaction type maintenance | `POST /api/v1/transaction-types/batch` |
| CBPAUP0C | CBPAUP0J.jcl | Purge expired pending authorizations | Scheduled task: `DELETE FROM pending_authorizations WHERE expires_at < NOW()` |

**Known Issues in batch programs**:

| Issue | Program | Correction |
|-------|---------|-----------|
| No COMMIT after DB2 DML | COBTUPDT | SQLAlchemy session auto-commits on context manager exit |
| ABEND continues (RC=4 not STOP RUN) | COBTUPDT | Python exception propagation terminates function; background task marks job as FAILED |

---

## 6. VSAM-MQ Programs

### 6.1 COACCT01 — Account Inquiry (MQ Triggered)

| Attribute | Value |
|-----------|-------|
| Transaction ID | CDRA |
| BMS Map | None |
| Module | VSAM-MQ |
| Source File | app/cbl/COACCT01.cbl (spec: COACCT01-spec.md) |

**No direct API endpoint.** Replaced by direct PostgreSQL access in `account_service`.

**Known Issues**:
- `LIT-ACCTFILENAME`, `WS-RESP-CD`, `WS-REAS-CD` declared but unused (dead working storage)
- ZIP code dropped from MQ reply (ACCT-ADDR-ZIP in VSAM, not in reply message)
- Both issues corrected in modern system: dead variables eliminated; ZIP always included in `AccountResponse`

**PostgreSQL Tables**: `accounts` (READ)

---

### 6.2 CODATE01 — Date/Time Inquiry (MQ Triggered)

| Attribute | Value |
|-----------|-------|
| Transaction ID | CDRD |
| BMS Map | None |
| Module | VSAM-MQ |
| Source File | app/cbl/CODATE01.cbl (spec: CODATE01-spec.md) |

**No API endpoint.** Replaced by `datetime.now(tz=timezone.utc)` in any service that needs the current date/time.

**Known Issues**:
- `ASKTIME`/`FORMATTIME` have no RESP/RESP2 checking in COBOL source
- Dead working storage: `LIT-ACCTFILENAME`, `WS-RESP-CD`, `WS-REAS-CD`
- All corrected: Python datetime raises exceptions on error; dead variables eliminated

**PostgreSQL Tables**: None

---

## 7. BMS Screen-to-Next.js Route Summary

Complete mapping of all 21 BMS maps to Next.js App Router routes:

| BMS Mapset | BMS Map | Program | Module | Next.js Route | Page Component |
|-----------|---------|---------|--------|---------------|----------------|
| COSGN00 | COSGN0A | COSGN00C | Base | `/login` | `LoginPage` |
| COMEN01 | COMEN1A | COMEN01C | Base | `/dashboard` | `MainMenuPage` |
| COADM01 | COADM1A | COADM01C | Base | `/admin` | `AdminMenuPage` |
| COACTVW | COACTVWA | COACTVWC | Base | `/accounts/view` | `AccountViewPage` |
| COACTUP | COACTUPA | COACTUPC | Base | `/accounts/update` | `AccountUpdatePage` |
| COBIL00 | COBIL0A | COBIL00C | Base | `/billing` | `BillingPage` |
| COCRDLI | CCRDLIA | COCRDLIC | Base | `/cards` | `CardListPage` |
| COCRDSL | CCRDSLA | COCRDSLC | Base | `/cards/view` | `CardViewPage` |
| COCRDUP | CCRDUPA | COCRDUPC | Base | `/cards/update` | `CardUpdatePage` |
| CORPT00 | CORPT0A | CORPT00C | Base | `/reports` | `ReportRequestPage` |
| COTRN00 | COTRN0A | COTRN00C | Base | `/transactions` | `TransactionListPage` |
| COTRN01 | COTRN1A | COTRN01C | Base | `/transactions/view` | `TransactionViewPage` |
| COTRN02 | COTRN2A | COTRN02C | Base | `/transactions/new` | `TransactionAddPage` |
| COUSR00 | COUSR0A | COUSR00C | Base | `/admin/users` | `UserListPage` |
| COUSR01 | COUSR1A | COUSR01C | Base | `/admin/users/new` | `UserAddPage` |
| COUSR02 | COUSR2A | COUSR02C | Base | `/admin/users/[user_id]/edit` | `UserEditPage` |
| COUSR03 | COUSR3A | COUSR03C | Base | `/admin/users/[user_id]/delete` | `UserDeletePage` |
| COPAU00 | COPAU0A | COPAUS0C | Authorization | `/admin/authorizations` | `AuthSummaryPage` |
| COPAU01 | COPAU1A | COPAUS1C | Authorization | `/admin/authorizations/[card_number]` | `AuthDetailPage` |
| COTRTLI | CTRTLIA | COTRTLIC | TranTypeDB2 | `/admin/transaction-types` | `TranTypeListPage` |
| COTRTUP | CTRTUPA | COTRTUPC | TranTypeDB2 | `/admin/transaction-types/new`, `/admin/transaction-types/[code]/edit` | `TranTypeMaintPage` |

---

## 8. CICS Transaction ID to API Module Mapping

| CICS Transaction ID | COBOL Program | API Module/Router | Base Path |
|--------------------|--------------|------------------|-----------|
| CC00 | COSGN00C | `auth` | `/api/v1/auth` |
| CM00 | COMEN01C | — (frontend only) | — |
| CA00 | COADM01C | — (frontend only) | — |
| CAVW | COACTVWC | `accounts` | `/api/v1/accounts` |
| — | COACTUPC | `accounts` | `/api/v1/accounts` |
| CC00 | COCRDLIC | `cards` | `/api/v1/cards` |
| CCDL | COCRDSLC | `cards` | `/api/v1/cards` |
| — | COCRDUPC | `cards` | `/api/v1/cards` |
| CT00 | COTRN00C | `transactions` | `/api/v1/transactions` |
| — | COTRN01C | `transactions` | `/api/v1/transactions` |
| — | COTRN02C | `transactions` | `/api/v1/transactions` |
| — | COBIL00C | `billing` | `/api/v1/billing` |
| CR00 | CORPT00C | `reports` | `/api/v1/reports` |
| CU00 | COUSR00C | `users` | `/api/v1/users` |
| — | COUSR01C | `users` | `/api/v1/users` |
| CU02 | COUSR02C | `users` | `/api/v1/users` |
| CU03 | COUSR03C | `users` | `/api/v1/users` |
| CPVS | COPAUS0C | `authorizations` | `/api/v1/authorizations` |
| CPVD | COPAUS1C, COPAUS2C | `authorizations` | `/api/v1/authorizations` |
| CP00 | COPAUA0C | (background worker) | — |
| CTLI | COTRTLIC | `transaction-types` | `/api/v1/transaction-types` |
| CTTU | COTRTUPC | `transaction-types` | `/api/v1/transaction-types` |
| CDRA | COACCT01 | (internal; no endpoint) | — |
| CDRD | CODATE01 | (internal; no endpoint) | — |

---

## 9. Copybook → PostgreSQL Column Mapping Summary

Key copybooks and their column-level mappings to PostgreSQL tables:

| Copybook | COBOL Structure | PostgreSQL Table | Key Fields Mapped |
|----------|----------------|-----------------|------------------|
| COCOM01Y | CARDDEMO-COMMAREA | (JWT claims) | CDEMO-USER-ID→`sub`, CDEMO-USER-TYPE→`user_type` |
| CSUSR01Y | SEC-USER-DATA | `users` | SEC-USR-ID, SEC-USR-PWD→`password_hash`, FNAME, LNAME, TYPE |
| CVACT01Y | ACCT-RECORD | `accounts` | All account fields; COMP-3 financials |
| CVACT02Y | ACCT-RECORD (ext.) | `accounts` | Extended account fields |
| CVACT03Y | ACCT-RECORD (ext2.) | `accounts` | Additional account metadata |
| CVCRD01Y | CARD-RECORD | `credit_cards` | CARD-NUM→masked, CARD-ACCT-ID, EXPIRY, STATUS |
| CUSTREC / CVCUS01Y | CUST-RECORD | `customers` | All customer fields; SSN→encrypted |
| CVTRA01Y–CVTRA07Y | TRAN-RECORD (7 variants) | `transactions` | TRAN-ID, TRAN-TYPE-CD, TRAN-AMT COMP-3, dates, merchant |
| CIPAUDTY | PAUTH-DETAIL | `pending_authorizations` | CARD-NUM, inverted timestamp, amount, merchant |
| CIPAUSMY | PAUTH-SUMMARY | (view over pending_authorizations) | CARD-NUM, aggregates |
| DCLTRTYP | TRNTYPE DB2 DCL | `transaction_types` | TR_TYPE, TR_TYPE_DESC |
| DCLTRCAT | TRNTYCAT DB2 DCL | `transaction_type_categories` | Category code, description |
| CCPAURLY | AUTH-REPLY | `fraud_flags` | Card, timestamp, fraud flag |

---

## 10. Programs With No Modern API Endpoint

The following programs require no dedicated REST endpoint because their function is either replaced by infrastructure, absorbed into another service, or not applicable to the web application:

| Program | Reason No Endpoint Needed |
|---------|--------------------------|
| CSUTLDTC | LINK subroutine replaced by Python `datetime` |
| COBSWAIT | MVS wait utility — no equivalent needed |
| COACCT01 | MQ trigger replaced by direct DB access in account_service |
| CODATE01 | Replaced by `datetime.now()` |
| COPAUA0C | Async authorization processor — background worker, not web endpoint |
| CBPAUP0C | Purge batch — scheduled database maintenance task |
| DBUNLDGS | IMS unload — one-time migration utility |
| PAUDBUNL | IMS unload — one-time migration utility |
| PAUDBLOD | IMS load — one-time migration utility |
| CBACT01C–CBACT04C | Batch account processing → scheduled or on-demand API |
| CBCUS01C | Batch customer processing → scheduled task |
| CBTRN01C–CBTRN03C | Batch transaction processing → scheduled tasks |
| CBSTM03A, CBSTM03B | Statement generation → background task triggered by `POST /api/v1/reports` |
| CBEXPORT, CBIMPORT | Data exchange → `GET/POST /api/v1/export,import` (optional phase 2) |

---

## 11. Known Issues Traceability

All 14 known issues from `overall-system-specification.md` section 12 mapped to their correction location:

| # | Issue | Original Location | Corrected In |
|---|-------|------------------|-------------|
| 1 | Plain-text passwords | COSGN00C + USRSEC | `07-security-specification.md` §2.3; `users.password_hash` in `01-database-specification.md` |
| 2 | No session timeout | All programs | `07-security-specification.md` §2.1 (JWT `exp` = 3600s) |
| 3 | No password masking at rest | USRSEC VSAM | `01-database-specification.md` §2.1; `07-security-specification.md` §4.1 |
| 4 | Transaction ID race condition | COTRN02C | `02-api-specification.md` POST /transactions; `NEXTVAL` sequence |
| 5 | Unnecessary UPDATE lock | COTRN01C | §2.10 above; GET uses plain SELECT |
| 6 | Missing COMMIT | COBTUPDT | §5.1 above; SQLAlchemy session management |
| 7 | Error continues after ABEND | COBTUPDT | §5.1 above; Python exception propagation |
| 8 | Copy-paste error message | COUSR03C | §2.17 above; corrected to "Unable to delete user" |
| 9 | Dead working storage (COUSR03C WS-USR-MODIFIED) | COUSR03C | §2.17 above; no equivalent declared |
| 10 | Dead working storage (CODATE01) | CODATE01 | §6.2 above; dead variables eliminated |
| 11 | Misspelled paragraph WIRTE-JOBSUB-TDQ | CORPT00C | §2.13 above; corrected function name in Python |
| 12 | ZIP code dropped from MQ reply | COACCT01 | §6.1 above; ZIP always in AccountResponse |
| 13 | Hardcoded JCL path | CORPT00C | §2.13 above; `settings.REPORT_TEMPLATE_PATH` |
| 14 | No ASKTIME error handling | CODATE01 | §6.2 above; Python datetime raises on invalid state |

---

*This matrix provides complete traceability for all 44 COBOL programs, 21 BMS screens, and 14 known issues from the CardDemo mainframe application to their modern FastAPI + PostgreSQL + Next.js equivalents.*
