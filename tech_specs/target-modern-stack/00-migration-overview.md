# CardDemo Migration Overview

## Document Purpose

This document defines the overall strategy, architecture decisions, and mapping framework for converting the CardDemo IBM mainframe application to a modern web-based stack. It serves as the anchor document for the remaining 8 specifications.

---

## 1. Source System Summary

The CardDemo system is a CICS/COBOL/BMS application running on IBM z/OS. It consists of:

| Category | Count | Examples |
|----------|-------|---------|
| Online CICS Programs | 25 | COSGN00C, COACTUPC, COTRN02C |
| Batch COBOL Programs | 16 | CBACT01C–04C, CBTRN01C–03C, CBSTM03A/B |
| Authorization Programs | 7 | COPAUA0C, COPAUS0C/1C/2C, CBPAUP0C, DBUNLDGS, PAUDBLOD/BUNL |
| Transaction-Type Programs | 3 | COTRTLIC, COTRTUPC, COBTUPDT |
| MQ Programs | 2 | COACCT01, CODATE01 |
| BMS Screen Maps | 21 | COSGN0A, COACTVW, COUSR0A–3A, COPAU0A/1A, CTRTLIA/CTRTUPA |
| VSAM Files | 6 | USRSEC, ACCTDAT, CUSTDAT, CARDDAT, CARDXREF, TRANSACT |
| DB2 Tables | 3 | TRANSACTION_TYPE, AUTHFRDS, system tables |
| IMS Databases | 2 | DBPAUTP0 (PAUTSUM0 + PAUTDTL1 segments) |
| IBM MQ Queues | 7 | REQSTQ, RPLSTQ, DEADQ, AUTH queues |

### Source Transaction Registry

| Transaction ID | Program | Function |
|---------------|---------|---------|
| COSG | COSGN00C | Sign-on |
| CA00 | COADM01C | Admin menu |
| CM00 | COMEN01C | Main menu |
| CAV0 | COACTVWC | Account view |
| CAUP | COACTUPC | Account update |
| CBL0 | COBIL00C | Bill payment |
| CCL0 | COCRDLIC | Card list |
| CCSL | COCRDSLC | Card detail |
| CCUP | COCRDUPC | Card update |
| CT00 | COTRN00C | Transaction list |
| CT01 | COTRN01C | Transaction view |
| CT02 | COTRN02C | Transaction add |
| CU00 | COUSR00C | User list |
| CU01 | COUSR01C | User add |
| CU02 | COUSR02C | User update |
| CU03 | COUSR03C | User delete |
| CRPT | CORPT00C | Report request |
| CPVS | COPAUS0C | Auth summary |
| CPVD | COPAUS1C | Auth detail |
| CTLI | COTRTLIC | Transaction type list |
| CTTU | COTRTUPC | Transaction type edit |

---

## 2. Target Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| REST API | Python 3.11+ / FastAPI | Async-first, automatic OpenAPI docs, Pydantic integration |
| ORM | SQLAlchemy 2.x (async) | Full async support, clean repository pattern |
| Schema Validation | Pydantic v2 | Replaces COBOL EVALUATE/IF field validation |
| Database | PostgreSQL 15+ | Replaces VSAM, DB2, IMS in a single RDBMS |
| Migrations | Alembic | Version-controlled schema evolution |
| Authentication | JWT (python-jose) + bcrypt | Replaces plain-text USRSEC password comparison |
| Background Tasks | FastAPI BackgroundTasks + Celery/Redis | Replaces IBM MQ trigger monitors and JCL batch |
| Frontend | Next.js 14 (App Router) + TypeScript | Replaces 3270 BMS screens |
| UI Framework | Tailwind CSS + shadcn/ui | Rapid consistent styling |
| Form Handling | React Hook Form + Zod | Replaces BMS field validation |
| Package Management | Poetry (backend) / npm (frontend) | Reproducible dependency management |
| Testing | pytest + httpx (backend), Jest + RTL (frontend) | TDD-first approach |

---

## 3. Architecture Overview

### Architectural Pattern

The modern system uses a three-tier architecture replacing CICS pseudo-conversational programs:

```
Browser (Next.js 14)
    |
    | HTTPS REST (JSON)
    |
FastAPI Application Server
    |--- Router (API layer — thin, no business logic)
    |--- Service Layer (all COBOL PROCEDURE DIVISION logic)
    |--- Repository Layer (all VSAM/DB2/IMS file access)
    |
PostgreSQL Database
    (replaces VSAM KSDS + VSAM AIX + DB2 + IMS)
```

### Key Architectural Decisions

**Decision 1: Stateless REST replaces CICS COMMAREA**
CICS programs carried state between interactions via COMMAREA (pseudo-conversational pattern). The modern equivalent is JWT tokens for authentication state plus client-side React state for form data. There is no server-side session for screen state.

**Decision 2: PostgreSQL replaces all storage tiers**
VSAM KSDS files, VSAM AIX (alternate index), DB2 tables, and IMS hierarchical databases all map to PostgreSQL tables with appropriate primary keys, foreign keys, and indexes. See `01-database-specification.md`.

**Decision 3: Background tasks replace JCL batch and MQ**
Batch programs (CBACT01C–04C, CBTRN01C–03C, etc.) become async FastAPI background tasks or Celery tasks. IBM MQ request/reply patterns (COACCT01, CODATE01) become synchronous REST endpoints.

**Decision 4: JWT replaces USRSEC plain-text authentication**
COSGN00C compared SEC-USR-PWD (plain text) directly. The modern system stores bcrypt-hashed passwords and issues JWT access tokens on successful login. User type (Admin/Regular) becomes a JWT claim used for RBAC.

**Decision 5: Role-based routing replaces CICS XCTL**
CICS XCTL to COADM01C vs COMEN01C based on SEC-USR-TYPE is replaced by React Router guards checking the `user_type` claim in the JWT.

---

## 4. Program-to-Endpoint Mapping

### Online Programs → FastAPI Endpoints

| COBOL Program | Transaction | Module | API Endpoints |
|--------------|-------------|--------|---------------|
| COSGN00C | COSG | auth | `POST /api/auth/login`, `POST /api/auth/logout` |
| COADM01C | CA00 | admin | `GET /api/admin/menu` |
| COMEN01C | CM00 | menu | `GET /api/menu` |
| COACTVWC | CAV0 | accounts | `GET /api/accounts/{account_id}` |
| COACTUPC | CAUP | accounts | `GET /api/accounts/{account_id}`, `PUT /api/accounts/{account_id}` |
| COBIL00C | CBL0 | billing | `GET /api/billing/{account_id}/balance`, `POST /api/billing/{account_id}/payment` |
| COCRDLIC | CCL0 | cards | `GET /api/cards?account_id=&card_number=&page=&page_size=` |
| COCRDSLC | CCSL | cards | `GET /api/cards/{card_number}` |
| COCRDUPC | CCUP | cards | `GET /api/cards/{card_number}`, `PUT /api/cards/{card_number}` |
| COTRN00C | CT00 | transactions | `GET /api/transactions?tran_id=&page=&page_size=` |
| COTRN01C | CT01 | transactions | `GET /api/transactions/{transaction_id}` |
| COTRN02C | CT02 | transactions | `POST /api/transactions` |
| COUSR00C | CU00 | users | `GET /api/users?user_id=&page=&page_size=` |
| COUSR01C | CU01 | users | `POST /api/users` |
| COUSR02C | CU02 | users | `GET /api/users/{user_id}`, `PUT /api/users/{user_id}` |
| COUSR03C | CU03 | users | `GET /api/users/{user_id}`, `DELETE /api/users/{user_id}` |
| CORPT00C | CRPT | reports | `POST /api/reports/request` |
| COPAUS0C | CPVS | auth-summary | `GET /api/authorizations?account_id=&page=&page_size=` |
| COPAUS1C | CPVD | auth-detail | `GET /api/authorizations/{transaction_id}`, `PUT /api/authorizations/{transaction_id}/fraud` |
| COPAUS2C | — | auth-detail | (internal — called by COPAUS1C logic, no separate endpoint) |
| COTRTLIC | CTLI | transaction-types | `GET /api/transaction-types?type_code=&description=&page=&page_size=` |
| COTRTUPC | CTTU | transaction-types | `POST /api/transaction-types`, `PUT /api/transaction-types/{type_code}`, `DELETE /api/transaction-types/{type_code}` |
| COPAUA0C | — | auth-engine | `POST /api/internal/process-authorizations` (background task) |
| COACCT01 | — | mq-compat | `GET /api/account-inquiry/{account_id}` |
| CODATE01 | — | mq-compat | `GET /api/system/date-time` |

### Batch Programs → Background Tasks / Admin APIs

| COBOL Program | Replacement | API Trigger |
|--------------|-------------|-------------|
| CBACT01C | Async account export task | `POST /api/admin/tasks/account-export` |
| CBACT02C | Async account copy task | `POST /api/admin/tasks/account-copy` |
| CBACT03C | Async account update task | `POST /api/admin/tasks/account-update` |
| CBACT04C | Async account/customer create task | `POST /api/admin/tasks/account-create` |
| CBCUS01C | Async customer add task | `POST /api/admin/tasks/customer-create` |
| CBTRN01C | Async transaction verification task | `POST /api/admin/tasks/transaction-verify` |
| CBTRN02C | Async transaction post task | `POST /api/admin/tasks/transaction-post` |
| CBTRN03C | Async transaction categorization task | `POST /api/admin/tasks/transaction-categorize` |
| CBSTM03A | Async statement sort task | `POST /api/admin/tasks/statement-sort` |
| CBSTM03B | Async statement print task | `POST /api/admin/tasks/statement-print` |
| CBEXPORT | Async data export task | `POST /api/admin/tasks/data-export` |
| CBIMPORT | Async data import task | `POST /api/admin/tasks/data-import` |
| COBSWAIT | Internal utility (no API equivalent) | — |
| CBPAUP0C | Async auth population task | `POST /api/admin/tasks/auth-populate` |
| DBUNLDGS | Async IMS unload → PostgreSQL migrate | `POST /api/admin/tasks/auth-unload` |
| PAUDBLOD | Async auth bulk load | `POST /api/admin/tasks/auth-load` |
| PAUDBUNL | Async auth unload | `POST /api/admin/tasks/auth-bulk-unload` |
| COBTUPDT | Async transaction type bulk update | `POST /api/admin/tasks/transaction-type-update` |

---

## 5. BMS Map-to-Page Mapping

| BMS Mapset | Map | Transaction | Next.js Route | Page Component |
|------------|-----|------------|---------------|----------------|
| COSGN00 | COSGN0A | COSG | `/login` | `LoginPage` |
| COMEN01 | COMEN1A | CM00 | `/menu` | `MainMenuPage` |
| COADM01 | COADM1A | CA00 | `/admin/menu` | `AdminMenuPage` |
| COACTVW | CACTVWA | CAV0 | `/accounts/view` | `AccountViewPage` |
| COACTUP | CACTUPA | CAUP | `/accounts/[id]/edit` | `AccountUpdatePage` |
| COBIL00 | COBIL0A | CBL0 | `/billing/payment` | `BillPaymentPage` |
| COCRDLI | CCRDLIA | CCL0 | `/cards` | `CardListPage` |
| COCRDSL | CCRDSLA | CCSL | `/cards/view` | `CardViewPage` |
| COCRDUP | CCRDUPA | CCUP | `/cards/[number]/edit` | `CardUpdatePage` |
| CORPT00 | CORPT0A | CRPT | `/reports/request` | `ReportRequestPage` |
| COTRN00 | COTRN0A | CT00 | `/transactions` | `TransactionListPage` |
| COTRN01 | COTRN1A | CT01 | `/transactions/[id]` | `TransactionViewPage` |
| COTRN02 | COTRN2A | CT02 | `/transactions/add` | `TransactionAddPage` |
| COUSR00 | COUSR0A | CU00 | `/admin/users` | `UserListPage` |
| COUSR01 | COUSR1A | CU01 | `/admin/users/add` | `UserAddPage` |
| COUSR02 | COUSR2A | CU02 | `/admin/users/[id]/edit` | `UserUpdatePage` |
| COUSR03 | COUSR3A | CU03 | `/admin/users/[id]/delete` | `UserDeletePage` |
| COPAU00 | COPAU0A | CPVS | `/authorizations` | `AuthorizationListPage` |
| COPAU01 | COPAU1A | CPVD | `/authorizations/[id]` | `AuthorizationDetailPage` |
| COTRTLI | CTRTLIA | CTLI | `/admin/transaction-types` | `TransactionTypeListPage` |
| COTRTUP | CTRTUPA | CTTU | `/admin/transaction-types/[code]` | `TransactionTypeEditPage` |

---

## 6. Navigation Flow Mapping

### CICS XCTL Chains → Next.js Router

| COBOL Navigation Event | Modern Equivalent |
|----------------------|-------------------|
| COSGN00C → COADM01C (Admin user) | Login success → `/admin/menu` (JWT claim `user_type=A`) |
| COSGN00C → COMEN01C (Regular user) | Login success → `/menu` (JWT claim `user_type=U`) |
| COMEN01C Option 1 → COBIL00C | `/menu` → `/billing/payment` |
| COMEN01C Option 2 → COACTVWC | `/menu` → `/accounts/view` |
| COMEN01C Option 3 → COTRN01C | `/menu` → `/transactions/[id]` |
| COMEN01C Option 4 → COTRN00C | `/menu` → `/transactions` |
| COMEN01C Option 5 → COCRDSLC | `/menu` → `/cards/view` |
| COMEN01C Option 6 → COCRDLIC | `/menu` → `/cards` |
| COMEN01C Option 7 → CORPT00C | `/menu` → `/reports/request` |
| COADM01C Option 1 → COUSR00C | `/admin/menu` → `/admin/users` |
| COADM01C Option 2 → COUSR01C | `/admin/menu` → `/admin/users/add` |
| COADM01C Option 3 → COUSR02C | `/admin/menu` → `/admin/users/[id]/edit` |
| COADM01C Option 4 → COUSR03C | `/admin/menu` → `/admin/users/[id]/delete` |
| COADM01C Option 5 → COTRTLIC | `/admin/menu` → `/admin/transaction-types` |
| COADM01C Option 6 → COTRTUPC | `/admin/menu` → `/admin/transaction-types/[code]` |
| COUSR00C 'U' selection → COUSR02C | `/admin/users` row update → `/admin/users/[id]/edit` |
| COUSR00C 'D' selection → COUSR03C | `/admin/users` row delete → `/admin/users/[id]/delete` |
| COCRDLIC 'S' selection → COCRDSLC | `/cards` row select → `/cards/view?card_number=X` |
| COCRDLIC 'U' selection → COCRDUPC | `/cards` row update → `/cards/[number]/edit` |
| COTRN00C 'S' selection → COTRN01C | `/transactions` row select → `/transactions/[id]` |
| COTRN01C PF5 → COTRN02C | `/transactions/[id]` → `/transactions/add` |
| COPAUS0C 'S' selection → COPAUS1C | `/authorizations` row select → `/authorizations/[id]` |
| COTRTLIC F2 → COTRTUPC | `/admin/transaction-types` → `/admin/transaction-types/new` |
| Any PF3 back | Browser `router.back()` or explicit route link |

---

## 7. Key Business Rule Preservation Summary

### Security Issues Being Corrected

| Original Flaw | Correction |
|--------------|-----------|
| Plain-text passwords in USRSEC (SEC-USR-PWD X(8)) | bcrypt hashing with cost factor ≥ 12 |
| No session expiry (CICS task-scoped only) | JWT with 1-hour expiry + refresh tokens |
| No HTTPS requirement | Enforced via deployment; all endpoints HTTPS-only |
| READ UPDATE locking held across screen interactions | Optimistic locking (ETag / `updated_at` timestamp comparison) |

### Race Conditions Being Fixed

| Original Race | Fix |
|--------------|-----|
| COTRN02C / COBIL00C STARTBR+READPREV+ADD1 for TRAN-ID | PostgreSQL sequence (`nextval`) for atomic ID generation |
| COACTUPC concurrent update detection (WS-DATACHANGED-FLAG) | PostgreSQL `updated_at` column + optimistic locking check before UPDATE |
| COCRDUPC 7-state machine CCUP-CHANGE-ACTION | Server-side state in DB (`card_change_action` column) with 15-minute TTL |

### Original Bugs Being Fixed

| Original Bug | Fix |
|-------------|-----|
| COUSR03C DELETE failure shows "Unable to Update User" | Error message corrected to "Unable to delete user" |
| COTRN01C READ UPDATE for display-only (unnecessary lock) | Use regular SELECT with no lock |
| COBIL00C ZIP code dropped from MQ reply | ZIP code included in all account responses |
| CBTRN01C opens CUSTFILE/CARDFILE/TRANSACT-FILE but never reads them | Simplified — only opens required files |
| CSUTLDTC RETURN-CODE always '1200' (not useful) | Replaced with Python `datetime.strptime` validation |

---

## 8. Pagination Pattern

All list screens with VSAM browse (STARTBR/READNEXT/READPREV) or DB2 cursors map to offset-based pagination:

```
GET /api/resource?page=1&page_size=10&filter_field=value
```

Response envelope:
```json
{
  "items": [...],
  "page": 1,
  "page_size": 10,
  "total_count": 125,
  "has_next": true,
  "has_previous": false
}
```

| COBOL Pattern | Modern Equivalent |
|--------------|-------------------|
| STARTBR key = LOW-VALUES → READNEXT N rows | `SELECT ... ORDER BY key ASC LIMIT N OFFSET 0` |
| STARTBR key = CDEMO-LAST-KEY → READNEXT N rows | `SELECT ... WHERE key > last_key ORDER BY key ASC LIMIT N` |
| STARTBR key = CDEMO-FIRST-KEY → READPREV N rows | `SELECT ... WHERE key < first_key ORDER BY key DESC LIMIT N` |
| USRIDINI filter → STARTBR key ≥ filter | `WHERE key >= filter_value ORDER BY key ASC` |
| Look-ahead READNEXT for NEXT-PAGE-FLG | `COUNT(*) > offset + page_size` |
| DB2 C-TR-TYPE-FORWARD cursor (>= key ASC) | `WHERE type_code >= start_code ORDER BY type_code ASC` |
| DB2 C-TR-TYPE-BACKWARD cursor (< key DESC) | `WHERE type_code < start_code ORDER BY type_code DESC` |

---

## 9. Module Structure (FastAPI)

```
backend/app/
├── api/endpoints/
│   ├── auth.py          (COSGN00C)
│   ├── accounts.py      (COACTVWC, COACTUPC)
│   ├── billing.py       (COBIL00C)
│   ├── cards.py         (COCRDLIC, COCRDSLC, COCRDUPC)
│   ├── transactions.py  (COTRN00C, COTRN01C, COTRN02C)
│   ├── users.py         (COUSR00C, COUSR01C, COUSR02C, COUSR03C)
│   ├── reports.py       (CORPT00C)
│   ├── authorizations.py (COPAUS0C, COPAUS1C)
│   ├── transaction_types.py (COTRTLIC, COTRTUPC)
│   ├── system.py        (CODATE01)
│   └── admin_tasks.py   (batch programs)
├── services/
│   ├── auth_service.py
│   ├── account_service.py
│   ├── billing_service.py
│   ├── card_service.py
│   ├── transaction_service.py
│   ├── user_service.py
│   ├── report_service.py
│   ├── authorization_service.py
│   └── transaction_type_service.py
├── repositories/
│   ├── user_repository.py
│   ├── account_repository.py
│   ├── card_repository.py
│   ├── transaction_repository.py
│   ├── authorization_repository.py
│   └── transaction_type_repository.py
└── models/
    ├── user.py
    ├── account.py
    ├── customer.py
    ├── card.py
    ├── card_xref.py
    ├── transaction.py
    ├── authorization.py
    └── transaction_type.py
```

---

## 10. Frontend Module Structure (Next.js 14)

```
front_end/src/
├── app/
│   ├── layout.tsx
│   ├── page.tsx               (redirects to /login)
│   ├── login/page.tsx         (COSGN00)
│   ├── menu/page.tsx          (COMEN01)
│   ├── admin/
│   │   ├── menu/page.tsx      (COADM01)
│   │   ├── users/
│   │   │   ├── page.tsx       (COUSR00)
│   │   │   ├── add/page.tsx   (COUSR01)
│   │   │   └── [id]/
│   │   │       ├── edit/page.tsx   (COUSR02)
│   │   │       └── delete/page.tsx (COUSR03)
│   │   └── transaction-types/
│   │       ├── page.tsx       (COTRTLI)
│   │       └── [code]/page.tsx (COTRTUP)
│   ├── accounts/
│   │   ├── view/page.tsx      (COACTVW)
│   │   └── [id]/edit/page.tsx (COACTUP)
│   ├── billing/
│   │   └── payment/page.tsx   (COBIL00)
│   ├── cards/
│   │   ├── page.tsx           (COCRDLI)
│   │   ├── view/page.tsx      (COCRDSL)
│   │   └── [number]/edit/page.tsx (COCRDUP)
│   ├── transactions/
│   │   ├── page.tsx           (COTRN00)
│   │   ├── add/page.tsx       (COTRN02)
│   │   └── [id]/page.tsx      (COTRN01)
│   ├── authorizations/
│   │   ├── page.tsx           (COPAU00)
│   │   └── [id]/page.tsx      (COPAU01)
│   └── reports/
│       └── request/page.tsx   (CORPT00)
├── components/
│   ├── ui/                    (shadcn/ui base components)
│   ├── layout/
│   │   ├── AppHeader.tsx      (standard header: Tran/Prog/Date/Time)
│   │   └── FunctionKeyBar.tsx (PF key → button mapping)
│   ├── auth/
│   │   └── AuthProvider.tsx
│   └── forms/
│       ├── AccountForm.tsx
│       ├── CardForm.tsx
│       ├── TransactionForm.tsx
│       ├── UserForm.tsx
│       └── ReportRequestForm.tsx
├── lib/
│   ├── api.ts                 (typed API client)
│   └── auth.ts                (JWT decode, role check)
├── hooks/
│   ├── useAuth.ts
│   ├── usePagination.ts
│   └── useToast.ts
└── types/
    ├── account.ts
    ├── card.ts
    ├── transaction.ts
    ├── user.ts
    └── authorization.ts
```

---

## 11. Assumptions and Decisions

1. **Password length**: Original USRSEC SEC-USR-PWD is 8 characters. The modern system accepts passwords up to 72 characters (bcrypt limit). Legacy 8-character passwords migrated as-is into bcrypt hashes.

2. **User type values**: Original SEC-USR-TYPE is 'A' (Admin) or 'U'/'R' (Regular). COUSR01C shows 'A=Admin, U=User'. The modern system uses enum `UserType.ADMIN` and `UserType.REGULAR` with string values 'A' and 'U'.

3. **Transaction ID format**: COTRN02C generates numeric TRAN-ID via STARTBR+READPREV+ADD1 (race condition). The modern system uses a UUID or a PostgreSQL sequence with a formatted string prefix.

4. **IMS replacement**: PAUTSUM0 and PAUTDTL1 IMS segments become two PostgreSQL tables (`authorization_summary` and `authorization_detail`) with a foreign key relationship and composite primary key.

5. **Batch programs**: The 16 batch COBOL programs are not translated one-for-one into running services. They become FastAPI background tasks that can be triggered via admin API endpoints. File I/O patterns (sequential reads/writes) become database queries.

6. **Report generation**: CORPT00C writes JCL to a CICS TDQ (internal reader) to submit a batch job. The modern equivalent is a background task that generates a CSV/PDF report and stores it for download.

7. **MQ programs**: COACCT01 and CODATE01 are MQ request/reply services. These are converted to direct REST endpoints since the MQ middleware layer is eliminated.

8. **COPAUS2C**: This program is invoked only via CICS LINK (not directly by a user). Its logic is absorbed into the authorization service layer, not exposed as a standalone endpoint.
