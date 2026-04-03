---
name: COBOL-to-Python Mapping Patterns
description: Key technical patterns for converting COBOL/CICS constructs to FastAPI/PostgreSQL/Next.js
type: reference
---

## Data Type Mappings (COBOL → PostgreSQL)
- PIC 9(11) account ID → VARCHAR(11) with zero-pad normalization in service layer
- PIC S9(10)V99 → NUMERIC(12, 2)
- PIC X(n) → VARCHAR(n)
- PIC X(1) Y/N fields → CHAR(1) with CHECK constraint IN ('Y', 'N')
- COMP-3 → NUMERIC
- PIC 9(8) date → DATE
- CICS timestamp → TIMESTAMP WITH TIME ZONE with `updated_at` trigger

## CICS → FastAPI Mappings
- EXEC CICS READ DATASET('ACCTDAT') → `SELECT FROM accounts WHERE acct_id = ?`
- EXEC CICS READ ... CXACAIX alternate index → SQL JOIN on card_cross_references with index on xref_acct_id
- EXEC CICS READ FILE('ACCTDAT') UPDATE → `SELECT ... FOR UPDATE NOWAIT` (raises OperationalError → LockAcquisitionError)
- EXEC CICS REWRITE FILE → SQLAlchemy flush + refresh
- EXEC CICS SYNCPOINT → session.commit()
- EXEC CICS SYNCPOINT ROLLBACK → session.rollback() — called in except block after write failure
- EXEC CICS RETURN TRANSID → HTTP response (pseudo-conversational → stateless REST)

## State Machine Conversion (COACTUPC ACUP-CHANGE-ACTION)
- ACUP-DETAILS-NOT-FETCHED → React state 'idle'
- ACUP-SHOW-DETAILS → React state 'show'
- ACUP-CHANGES-OK-NOT-CONFIRMED → React state 'confirming'
- ACUP-CHANGES-OKAYED-AND-DONE → React state 'done'
- ACUP-CHANGES-OKAYED-BUT-FAILED → React state 'failed'
- Implemented in `useAccountUpdate` hook

## Optimistic Concurrency (9700-CHECK-CHANGE-IN-REC)
- COBOL compared ACUP-OLD-DETAILS snapshot field-by-field against re-read locked record
- Modern equivalent: compare `updated_at` timestamp from client token against actual DB timestamps
- Client sends `updated_at` in PUT request body (not headers)
- If acct.updated_at > client_token OR cust.updated_at > client_token → 409 Conflict
- HTTP 409 = DATA-WAS-CHANGED-BEFORE-UPDATE; HTTP 423 = COULD-NOT-LOCK-*-FOR-UPDATE

## SSN Formatting
- COBOL: STRING CUST-SSN(1:3) '-' CUST-SSN(4:2) '-' CUST-SSN(6:4)
- Python: `f"{digits[0:3]}-{digits[3:5]}-{digits[5:9]}"` in `format_ssn()`
- COACTUPC stores SSN as 9-digit string; screen splits into ACTSSN1(3)/ACTSSN2(2)/ACTSSN3(4)
- Frontend: three separate Input fields, reassembled server-side as `part1+part2+part3`

## Phone Formatting
- COBOL: STRING '(' AREA ')' PREFIX '-' LINE-NUMBER
- Python: `f"({phone.area_code}){phone.prefix}-{phone.line_number}"` in `format_phone()`
- Frontend: three sub-fields ACSPH1A(3)/ACSPH1B(3)/ACSPH1C(4)

## BMS Field Attribute → UI Component
- ASKIP / PROT → ReadOnlyField (non-editable, border-b underline)
- UNPROT + HILIGHT=UNDERLINE → Input component
- DFHBMPRF (runtime-protected) → ReadOnlyField regardless of BMS UNPROT
- BRT RED ERRMSG field → red div with role="alert"
- NEUTRAL INFOMSG field → gray div with aria-live="polite"
- PF3=Exit → Link with F3=Exit label
- PF5=Save → Button only enabled in 'confirming' state
- PF12=Cancel → Button to reset to 'show' state
- VALIDN=MUSTFILL → Zod/Pydantic `min(1)` constraint
