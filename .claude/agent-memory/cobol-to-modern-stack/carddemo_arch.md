---
name: CardDemo Architecture Conventions
description: Project-specific decisions for the CardDemo mainframe conversion project
type: project
---

## Admin Auth Stub

All admin-only FastAPI endpoints use a header-based stub `require_admin` dependency that checks `X-User-Type: A`.

**Why:** The auth module (COSGN00C) is converted in a separate PR. The stub allows each module to be tested independently without circular dependencies.

**How to apply:** When the auth module JWT middleware is ready, replace `require_admin` in each router with the real JWT dependency. The header name `X-User-Type` will be set by the JWT middleware after validating the token.

## Folder Layout Convention

```
fast_api/
├── src/app/
│   ├── models/       — SQLAlchemy ORM (one file per table)
│   ├── schemas/      — Pydantic request/response (one file per domain)
│   ├── repositories/ — Data access only, no business logic
│   ├── services/     — ALL business logic (COBOL paragraph logic goes here)
│   ├── routers/      — HTTP layer only (status codes, request parsing)
│   └── utils/        — Pure functions (password hashing, formatting)
├── sql/
│   ├── create_tables.sql
│   └── seed_data.sql
└── tests/
    ├── unit/         — Service method tests (use SQLite in-memory)
    └── integration/  — API endpoint tests (use SQLite in-memory)

front_end/src/
├── app/              — Next.js App Router pages
├── components/
│   ├── ui/           — Reusable primitives (Button, FormField, StatusMessage, PageHeader)
│   └── forms/        — Screen-level form components (one per COBOL program)
├── lib/
│   ├── api.ts        — Centralised API service layer
│   └── utils.ts      — Formatting helpers
├── hooks/            — Custom React hooks
└── types/            — TypeScript interfaces matching Pydantic schemas
```

## Test Fixture Pattern

SQLite in-memory DB via `aiosqlite` for all tests (no PostgreSQL required in CI).
`seed_users` fixture provides 2 admin + 3 regular users matching `seed_data.sql`.
`ADMIN_HEADERS = {"X-User-Type": "A"}` constant for all integration test calls.

## Module Conversion Status

| Module | Branch | Programs | Status |
|--------|--------|----------|--------|
| Auth/Navigation | feature/auth-navigation-module | COSGN00C, COMEN01C, COADM01C | Converted |
| Account Management | feature/account-management-module | COACTVWC, COACTUPC | Converted |
| Credit Card | feature/credit-card-module | COCRDLIC, COCRDSLC, COCRDUPC | Converted |
| Transaction Processing | feature/transaction-processing-module | COTRN00C-02C | Converted |
| User Administration | feature/user-administration-module | COUSR00C-03C | Converted (this PR) |
