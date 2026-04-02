---
name: COBOL to Next.js Mapping Conventions
description: Field mapping, BMS-to-component patterns, and validation rules established during CardDemo conversion
type: reference
---

## PIC Clause to TypeScript/HTML Mappings

| COBOL PIC | TypeScript Type | HTML Input |
|---|---|---|
| PIC X(n) | string | type="text" maxLength={n} |
| PIC 9(n) | number | type="text" inputMode="numeric" or type="number" |
| PIC S9(n)V9(m) | number | type="number" step="0.01" |
| PIC XX (type code) | string | type="text" maxLength={2} uppercase |
| PIC X(8) (user ID) | string | maxLength={8} uppercase |

## Business Rule Validations (from COACTUP spec)
- Phone: regex `^\(\d{3}\)\d{3}-\d{4}$` — format (999)999-9999
- FICO score: int 300-850
- State code: 2-letter uppercase, validated against US state set
- User ID: 1-8 chars uppercase alphanumeric (`/^[A-Z0-9]+$/`)
- Password: 1-8 chars
- Transaction type code: exactly 2 uppercase chars
- Currency: positive decimal, multipleOf 0.01

## BMS Map to Component Patterns

| BMS Concept | Next.js Pattern |
|---|---|
| BMS message line (bottom of screen) | react-hot-toast notifications |
| BMS protected field | `disabled` or `readOnly` input; ReadonlyField component |
| BMS unprotected field | Regular controlled input |
| BMS dark field (hidden) | Not rendered or hidden |
| PF3 (Exit/Back) | Back button, `router.back()` |
| PF7/PF8 (Page Up/Down) | DataTable pagination controls |
| ENTER key (primary action) | Form submit button |
| Cursor to first error field | `autoFocus` on first error, react-hook-form auto-focus |

## Program to Page Mapping
| COBOL Program | Next.js Page |
|---|---|
| COSGN00C | /login |
| COMEN01C + COADM01C | /dashboard + Sidebar |
| COACTVWC | /accounts/[acctId] (view mode) |
| COACTUPC | /accounts/[acctId] (edit mode) |
| COCRDLIC + COCRDSLC | /cards |
| COCRDUPC | /cards/[cardNum] |
| COTRN00C | /transactions |
| COTRN01C | /transactions/[tranId] |
| COTRN02C | /transactions/new |
| CORPT00C | /reports |
| COBIL00C | /billing |
| COPAUS0C | /authorizations |
| COPAUS1C + COPAUS2C | /authorizations/[acctId] |
| COUSR00C | /users |
| COUSR01C | /users/new |
| COUSR02C + COUSR03C | /users/[usrId] |
| COTRTLIC | /transaction-types |
| COTRTUPC | /transaction-types/[typeCode] |
| Batch programs | /batch |

## Page Size Conventions (from BMS maps)
- COCRDLI: 7 rows → PAGE_SIZE = 7
- COTRN00: 10 rows → PAGE_SIZE = 10
- COUSR00: 10 rows → PAGE_SIZE = 10
- COTRTLI: 7 rows → PAGE_SIZE = 7
