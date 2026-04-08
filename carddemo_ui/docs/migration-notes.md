# Migration Notes & Architectural Decisions

## Overview

This document records decisions made during the COBOL/CICS to Next.js migration of the CardDemo application.

## Key Decisions

### 1. Authentication: JWT Tokens (replacing CICS COMMAREA)

**Original:** COSGN00C stored session state in CICS COMMAREA (`CARDDEMO-COMMAREA`), passed between XCTL calls.

**Decision:** JWT Bearer tokens stored in `localStorage`. The token encodes `sub` (user_id) and `role` (user_type: 'A'/'U'). The FastAPI backend validates tokens on every request.

**Tradeoff:** localStorage is susceptible to XSS. For production, consider `httpOnly` cookies. The choice of localStorage was made to keep the initial migration simple and allow Swagger UI testing.

### 2. Navigation: React Router (replacing CICS XCTL)

**Original:** Screen transitions used `EXEC CICS XCTL PROGRAM(next-program)` to transfer control.

**Decision:** Next.js App Router with `router.push()` for programmatic navigation and `<Link>` for declarative navigation. The navigation map is in `src/lib/constants/routes.ts`.

### 3. Pagination: Keyset (replacing VSAM STARTBR/READNEXT)

**Original:** COBOL programs used `EXEC CICS STARTBR`, `READNEXT`, `READPREV` to browse VSAM files. Page boundaries tracked in `CDEMO-CL00-CARDNUM-FIRST/LAST`.

**Decision:** Keyset pagination using `cursor` (last item key from previous page) and `direction` query parameters. This mirrors the STARTBR positioning semantics exactly and scales well. The `usePagination` hook manages cursor state.

### 4. Validation: Zod (matching COBOL EVALUATE chains)

**Original:** COBOL validated fields in sequence in `PROCESS-ENTER-KEY → VALIDATE-INPUT-FIELDS` paragraphs.

**Decision:** Zod schemas in `src/lib/validators/` replicate the exact same conditions and error messages. React Hook Form with `zodResolver` triggers validation on submit. Error messages are copied verbatim from the COBOL source where practical.

### 5. Monetary Fields: Strings (preserving COMP-3 precision)

**Original:** COBOL stored amounts as `PIC S9(10)V99 COMP-3` (packed decimal).

**Decision:** API returns and accepts `string` types for monetary fields (Python `Decimal` serializes to string). The UI displays them using `Intl.NumberFormat` for currency formatting, never converting to JavaScript `float` (which would lose precision).

### 6. Authorization Module: Synchronous (replacing IBM MQ)

**Original:** COPAUA0C used IBM MQ (`MQOPEN/MQGET/MQPUT1`) for async request/reply authorization processing.

**Decision:** The FastAPI endpoint `POST /api/v1/authorizations` performs the authorization synchronously. The UI sends a form and waits for the decision, which is simpler and sufficient for demo/development purposes.

### 7. Reports: Fire-and-Forget (matching TDQ async pattern)

**Original:** CORPT00C submitted JCL via `EXEC CICS WRITEQ TD QUEUE('JOBS')` — inherently asynchronous.

**Decision:** `POST /api/v1/reports/transactions` returns HTTP 202 (Accepted) with a `job_id`. The UI shows the job_id and status. This preserves the async semantics. A `GET /api/v1/reports/transactions/{job_id}` endpoint allows status polling.

## Field Naming Conventions Discovered

- All COBOL program names end in `C` (e.g., `COSGN00C`, `COACTVWC`)
- BMS map names match program names without the trailing `C` (e.g., `COSGN00`, `COACTVW`)
- CICS transaction IDs are 4-char codes derived from the first 2 chars of the program + sequence (e.g., `CC00`, `CA0V`)
- VSAM file names are short uppercase (e.g., `ACCTDAT`, `CARDDAT`, `USRSEC`)
- Field names in COBOL use prefix notation: `ACCT-CURR-BAL`, `CARD-ACTIVE-STATUS`, `SEC-USR-ID`

## Error Message Preservation

Original COBOL error messages are preserved where they map to API validation errors. The FastAPI backend's Pydantic validators include the original COBOL text in the `ValueError` messages. The UI displays these messages directly without paraphrasing.

Examples:
- `"User not found. Try again ..."` (COSGN00C READ-USER-SEC-FILE)
- `"Wrong Password. Try again ..."` (COSGN00C PROCESS-ENTER-KEY)
- `"Changes committed to database"` (COTRTUPC 9600-WRITE-PROCESSING)
- `"No record found for this key"` (COTRTUPC SQLCODE=100)
- `"You have nothing to pay..."` (COBIL00C: ACCT-CURR-BAL <= ZEROS)

## Admin vs Regular User Access

The original COBOL used two separate menu programs:
- `COMEN01C` — regular user main menu
- `COADM01C` — admin-only menu (guards checked `CDEMO-USER-TYPE = 'A'`)

The Next.js app unifies these into a single dashboard that conditionally shows admin-only menu items based on `user.user_type === 'A'`. The API enforces the same restrictions server-side via the `AdminUser` dependency in FastAPI.

## Migration Status

See `README.md` for the current migration completion checklist.
