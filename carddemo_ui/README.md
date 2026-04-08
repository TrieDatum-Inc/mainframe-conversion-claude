# CardDemo UI

A modern Next.js web application that is functionally equivalent to the CardDemo COBOL/CICS mainframe application. This UI connects to the Python FastAPI backend (`fast_api/`) which replaced the original IBM CICS transactions.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Setup Instructions](#setup-instructions)
4. [Environment Variables](#environment-variables)
5. [Project Structure](#project-structure)
6. [Development Workflow](#development-workflow)
7. [Screen Mapping Reference](#screen-mapping-reference)
8. [API Integration](#api-integration)
9. [Testing](#testing)
10. [Key Architectural Decisions](#key-architectural-decisions)
11. [Migration Status](#migration-status)

---

## Overview

CardDemo is a credit card management demo application originally built on IBM COBOL/CICS running on z/OS mainframe. This Next.js application provides a modern web UI that is **functionally equivalent** to the original BMS screen definitions, while offering:

- Responsive, modern web design (not a terminal replica)
- Full integration with the FastAPI REST backend
- Preserved COBOL business logic (validations, field lengths, error messages)
- Clean architecture: validators, services, and components are separated
- Comprehensive test suite (validators: 100% coverage target, components: 90%+)

### Mainframe Origins

| Mainframe Component | Modernization |
|---------------------|--------------|
| IBM COBOL (45 programs) | Python FastAPI service |
| CICS BMS screens | Next.js 14 App Router pages |
| CICS VSAM files | PostgreSQL via SQLAlchemy |
| IBM MQ (authorizations) | Synchronous REST POST |
| CICS TDQ (reports) | FastAPI BackgroundTasks |
| COMMAREA session | JWT Bearer tokens |

---

## Prerequisites

- **Node.js** 18.17+ (LTS recommended — required by Next.js 14)
- **npm** 9+ or **pnpm** 8+ or **yarn** 4+
- **Python FastAPI backend** running at `http://localhost:8000` (see `fast_api/README.md`)

Check your Node version:
```bash
node --version
```

---

## Setup Instructions

### 1. Clone and navigate

```bash
cd carddemo_ui
```

### 2. Install dependencies

```bash
npm install
# or
pnpm install
```

### 3. Configure environment

```bash
cp .env.example .env.local
```

Edit `.env.local` and set:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4. Start the FastAPI backend

In a separate terminal (from the project root):
```bash
cd fast_api
poetry install
uvicorn app.main:app --reload --port 8000
```

### 5. Start the Next.js dev server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### 6. Default credentials

Use the test accounts seeded in the FastAPI database:
- **Admin**: `ADMIN001` / `Admin123`
- **Regular user**: `USER0001` / `User1234`

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | FastAPI backend base URL |
| `NODE_ENV` | `development` | Node environment |

The Next.js dev server proxies `/api/*` requests to the FastAPI backend via `next.config.js` rewrites.

---

## Project Structure

```
carddemo_ui/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── login/              # COSGN00C — login screen
│   │   ├── dashboard/          # COMEN01 / COADM01 — main menu
│   │   ├── accounts/           # COACTVWC / COACTUPC / COBIL00C
│   │   │   └── [id]/
│   │   │       ├── page.tsx        # Account view
│   │   │       ├── edit/           # Account update
│   │   │       └── payment/        # Bill payment
│   │   ├── cards/              # COCRDLIC / COCRDSLC / COCRDUPC
│   │   │   └── [cardNum]/
│   │   │       ├── page.tsx        # Card view
│   │   │       └── edit/           # Card update
│   │   ├── transactions/       # COTRN00C / COTRN01C / COTRN02C
│   │   │   ├── [id]/               # Transaction view
│   │   │   └── new/                # Create transaction
│   │   ├── authorizations/     # COPAUA0C / COPAUS0C / COPAUS1C
│   │   │   ├── accounts/[acctId]/  # Auth history by account
│   │   │   ├── [authId]/           # Auth detail + fraud marking
│   │   │   └── new/                # Process authorization
│   │   └── admin/              # Admin-only screens
│   │       ├── page.tsx            # COADM01C menu
│   │       ├── users/              # COUSR00C-03C
│   │       ├── reports/            # CORPT00C
│   │       └── transaction-types/  # COTRTLIC / COTRTUPC
│   ├── components/
│   │   ├── ui/                 # Reusable primitives
│   │   │   ├── Button.tsx
│   │   │   ├── FormField.tsx   # Label + input + error wrapper
│   │   │   ├── Alert.tsx       # Error/success messages (maps to ERRMSG BMS field)
│   │   │   ├── StatusBadge.tsx
│   │   │   └── Pagination.tsx  # PF7/PF8 navigation
│   │   └── layout/
│   │       └── AppShell.tsx    # Sidebar nav + main content area
│   ├── hooks/
│   │   ├── useAuth.ts          # Authentication state
│   │   └── usePagination.ts    # STARTBR/READNEXT keyset pagination
│   ├── lib/
│   │   ├── validators/         # Zod schemas (derived from COBOL EVALUATE chains)
│   │   │   ├── auth.ts         # COSGN00C rules
│   │   │   ├── account.ts      # COACTUPC + COBIL00C rules
│   │   │   ├── card.ts         # COCRDUPC rules
│   │   │   ├── transaction.ts  # COTRN02C rules
│   │   │   ├── user.ts         # COUSR01C/02C rules
│   │   │   └── report.ts       # CORPT00C rules
│   │   ├── types/
│   │   │   └── api.ts          # TypeScript types matching FastAPI Pydantic schemas
│   │   ├── utils/
│   │   │   ├── cn.ts           # Tailwind class merging
│   │   │   └── format.ts       # Currency, date, card number formatting
│   │   └── constants/
│   │       └── routes.ts       # Centralized route constants
│   ├── services/               # API service layer (one file per domain)
│   │   ├── apiClient.ts        # Axios client + JWT injection + 401 handling
│   │   ├── authService.ts
│   │   ├── accountService.ts
│   │   ├── cardService.ts
│   │   ├── transactionService.ts
│   │   ├── transactionTypeService.ts
│   │   ├── userService.ts
│   │   ├── adminService.ts
│   │   ├── reportService.ts
│   │   └── authorizationService.ts
│   └── styles/
│       └── globals.css         # Tailwind base styles + reusable component classes
├── __tests__/
│   ├── validators/             # 100% coverage target
│   │   ├── auth.test.ts
│   │   ├── account.test.ts
│   │   ├── card.test.ts
│   │   ├── transaction.test.ts
│   │   ├── user.test.ts
│   │   └── report.test.ts
│   ├── components/             # 90%+ coverage target
│   │   ├── Button.test.tsx
│   │   ├── FormField.test.tsx
│   │   └── StatusBadge.test.tsx
│   ├── hooks/
│   │   └── usePagination.test.ts
│   └── integration/
│       └── login.test.tsx      # End-to-end login flow test
├── docs/
│   ├── screen-mapping.md       # BMS screen to Next.js route table
│   └── migration-notes.md      # Architectural decisions and deviations
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.js
└── .env.example
```

---

## Development Workflow

### Adding a new screen

1. Identify the BMS map and COBOL program
2. Document field inventory (name, type, position, attributes)
3. Add Zod validator in `src/lib/validators/` — **tests first**
4. Add TypeScript types in `src/lib/types/api.ts` if needed
5. Add service method in the appropriate `src/services/` file
6. Create the page component in `src/app/`
7. Add route constant in `src/lib/constants/routes.ts`
8. Update `docs/screen-mapping.md`

### Running tests

```bash
# Run all tests
npm test

# Run in watch mode
npm run test:watch

# Run with coverage report
npm run test:coverage

# CI mode (no interactive)
npm run test:ci
```

### Type checking

```bash
npm run type-check
```

### Linting

```bash
npm run lint
npm run lint:fix
```

### Building for production

```bash
npm run build
npm start
```

---

## Screen Mapping Reference

See [docs/screen-mapping.md](docs/screen-mapping.md) for the complete BMS screen to Next.js route mapping table.

Quick reference:

| Screen | Route | Description |
|--------|-------|-------------|
| COSGN00 | `/login` | User sign-on |
| COMEN01 / COADM01 | `/dashboard` | Main / Admin menu |
| COACTVW | `/accounts/[id]` | Account view |
| COACTUP | `/accounts/[id]/edit` | Account update |
| COBIL00 | `/accounts/[id]/payment` | Bill payment |
| COCRDLI | `/cards` | Card list |
| COCRDSL | `/cards/[cardNum]` | Card view |
| COCRDUP | `/cards/[cardNum]/edit` | Card update |
| COTRN00 | `/transactions` | Transaction list |
| COTRN01 | `/transactions/[id]` | Transaction detail |
| COTRN02 | `/transactions/new` | Create transaction |
| COUSR00 | `/admin/users` | User list |
| COUSR01 | `/admin/users/new` | Add user |
| COUSR02 | `/admin/users/[id]/edit` | Edit user |
| CORPT00 | `/admin/reports` | Transaction reports |
| COTRTLI | `/admin/transaction-types` | Transaction type list |
| COTRTUP | `/admin/transaction-types/[code]` | Edit transaction type |
| COPAU00 | `/authorizations/accounts/[acctId]` | Auth history |
| COPAU01 | `/authorizations/[authId]` | Auth detail + fraud marking |
| — | `/authorizations/new` | Process authorization |

---

## API Integration

The UI connects to all FastAPI endpoints:

| Domain | Endpoints |
|--------|-----------|
| Auth | `POST /api/v1/auth/login`, `POST /api/v1/auth/token` |
| Accounts | `GET/PUT /api/v1/accounts/{id}`, `POST /api/v1/accounts/{id}/payments` |
| Cards | `GET /api/v1/cards`, `GET/PUT /api/v1/cards/{card_num}` |
| Transactions | `GET /api/v1/transactions`, `GET/POST /api/v1/transactions/{id}`, `POST /api/v1/transactions/payment` |
| Users (admin) | `GET/POST /api/v1/admin/users`, `GET/PUT/DELETE /api/v1/admin/users/{id}` |
| Admin Menu | `GET /api/v1/admin/menu`, `GET /api/v1/admin/menu/{option}` |
| Reports (admin) | `POST /api/v1/reports/transactions`, `GET /api/v1/reports/transactions/{job_id}` |
| Transaction Types (admin) | `GET/POST /api/v1/transaction-types`, `GET/PUT/DELETE /api/v1/transaction-types/{code}` |
| Authorizations | `POST /api/v1/authorizations`, `GET /api/v1/authorizations/accounts/{id}`, `GET /api/v1/authorizations/details/{id}`, `GET /api/v1/authorizations/accounts/{id}/next`, `POST /api/v1/authorizations/details/{id}/fraud` |

All API calls are centralized in `src/services/` with automatic JWT injection via `src/services/apiClient.ts`.

---

## Testing

### Coverage targets

| Layer | Target |
|-------|--------|
| Validators (`src/lib/validators/`) | 100% |
| Screen components (`src/app/`) | 90%+ |
| Hooks (`src/hooks/`) | 90%+ |
| Services (`src/services/`) | 80%+ |

### Test organization

- **Unit tests** (`__tests__/validators/`): Test every Zod validation rule derived from COBOL EVALUATE chains
- **Component tests** (`__tests__/components/`): Render tests for UI primitives
- **Hook tests** (`__tests__/hooks/`): State management logic tests
- **Integration tests** (`__tests__/integration/`): Full screen render tests with mocked API

### Running specific tests

```bash
# Run only validator tests
npm test -- validators

# Run with specific file
npm test -- login.test.tsx

# Run with verbose output
npm test -- --verbose
```

---

## Key Architectural Decisions

1. **Next.js 14 App Router** — Server components where possible; client components (`'use client'`) only for interactive screens with state and event handlers.

2. **Zod validation** — All business rules from COBOL EVALUATE/IF chains are encoded as Zod schemas. Error messages match COBOL text verbatim.

3. **React Hook Form** — Form management with `zodResolver`. Provides the same field-level focus behavior as COBOL cursor positioning on error.

4. **Keyset pagination** — Matches the COBOL `STARTBR/READNEXT` pattern. The `cursor` is the last item's key, equivalent to positioning the file pointer.

5. **Service layer** — All HTTP calls are in `src/services/`, not in components. Components receive data and call service functions; they never directly use axios.

6. **JWT in localStorage** — Simple for demo purposes. For production, `httpOnly` cookies with CSRF protection would be more secure.

7. **Tailwind CSS** — Utility-first CSS keeps styles co-located with components and avoids style conflicts.

8. **Decimal as string** — Monetary amounts are kept as strings throughout the UI to preserve COBOL COMP-3 precision (never converted to JavaScript float).

---

## Migration Status

### Completed

- [x] Login screen (COSGN00C)
- [x] Main/Admin dashboard (COMEN01C / COADM01C)
- [x] Account view (COACTVWC)
- [x] Account update (COACTUPC)
- [x] Bill payment (COBIL00C)
- [x] Card list (COCRDLIC)
- [x] Card view (COCRDSLC)
- [x] Card update (COCRDUPC)
- [x] Transaction list (COTRN00C)
- [x] Transaction view (COTRN01C)
- [x] Transaction create (COTRN02C)
- [x] User list (COUSR00C)
- [x] User create (COUSR01C)
- [x] User update (COUSR02C)
- [x] User delete (COUSR03C)
- [x] Transaction report submission (CORPT00C)
- [x] Transaction type list (COTRTLIC)
- [x] Transaction type update (COTRTUPC)
- [x] Authorization processing (COPAUA0C)
- [x] Authorization history (COPAUS0C)
- [x] Authorization detail + fraud marking (COPAUS1C / COPAUS2C)
- [x] Service layer (all 10 FastAPI endpoint groups)
- [x] Zod validators for all screens
- [x] Test suite (validators + components + hooks + integration)

### Not yet implemented

- [ ] Playwright E2E tests
- [ ] Dark mode
- [ ] Accessibility audit (WCAG 2.1 AA)
- [ ] Performance monitoring
- [ ] Production deployment configuration
