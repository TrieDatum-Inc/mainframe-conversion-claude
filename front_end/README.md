# Account Management Frontend

Next.js frontend for the CardDemo Account Management module.

## Screens

| Screen | Route | COBOL Equivalent |
|--------|-------|-----------------|
| Account Search (View) | `/accounts` | COACTVWC — CDEMO-PGM-ENTER (blank) |
| Account View Detail | `/accounts/[acctId]` | COACTVWC — CACTVWA screen |
| Account Update Search | `/accounts/update` | COACTUPC — blank state |
| Account Update Form | `/accounts/[acctId]/update` | COACTUPC — CACTUPA screen |

## Setup

```bash
cp .env.local.example .env.local
npm install
npm run dev
```

Open http://localhost:3000

## Architecture

- **App Router** pages in `src/app/`
- **Shared UI components** in `src/components/ui/` — mirrors BMS field attributes
- **Form components** in `src/components/forms/`
- **Custom hooks** in `src/hooks/` — `useAccountUpdate` implements COACTUPC state machine
- **API client** in `src/lib/api.ts` — centralised HTTP calls
- **Validation** in `src/lib/validationSchemas.ts` — Zod schemas mirroring Pydantic validators

## BMS → UI Field Mapping

| BMS Attribute | UI Behaviour |
|---|---|
| ASKIP / PROT | `ReadOnlyField` component (not editable) |
| UNPROT | `Input` component (editable) |
| FSET, IC | First editable field receives `autoFocus` |
| VALIDN=MUSTFILL | Zod `min(1)` constraint |
| HILIGHT=UNDERLINE | `border-b` CSS class on ReadOnlyField |
| BRT RED (ERRMSG) | Red bordered alert `div` with `role="alert"` |
| NEUTRAL (INFOMSG) | Gray `div` with `aria-live="polite"` |
| DFHBMPRF (protected at runtime) | `ReadOnlyField` regardless of BMS UNPROT |
| PF3=Exit | `F3=Exit` button/link → back navigation |
| PF5=Save | `F5=Save` button — only enabled at confirming state |
| PF12=Cancel | `F12=Cancel` button — resets to show state |

## Optimistic Concurrency

The `updated_at` field returned from `GET /api/accounts/{acct_id}` is stored in the form and
sent back in the `PUT` request. If the record was modified by another user in the meantime,
the API returns `409 Conflict` and the user sees an error toast — equivalent to COBOL
`DATA-WAS-CHANGED-BEFORE-UPDATE`.
