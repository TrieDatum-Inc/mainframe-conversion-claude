---
name: CardDemo User Administration Subsystem
description: Architecture, programs, transactions, and VSAM file details for the CardDemo User CRUD subsystem (COUSR00C–COUSR03C)
type: project
---

The CardDemo User Administration subsystem consists of four CICS COBOL programs implementing full CRUD for user records in the USRSEC VSAM KSDS file.

**Why:** This subsystem is the target of mainframe-to-modern conversion work. Understanding it completely is required before migration.

**How to apply:** Use this when analyzing dependencies, data flows, or proposing a modern equivalent data model and API.

## Programs and Transactions

| Program  | Transaction | Function        | BMS Mapset/Map        |
|----------|-------------|-----------------|----------------------|
| COUSR00C | CU00        | List Users (paginated browse) | COUSR00/COUSR0A |
| COUSR01C | CU01        | Add User        | COUSR01/COUSR1A |
| COUSR02C | CU02        | Update User     | COUSR02/COUSR2A |
| COUSR03C | CU03        | Delete User     | COUSR03/COUSR3A |

## VSAM File: USRSEC

- Organization: KSDS
- Key: SEC-USR-ID, PIC X(8) — 8-character user ID
- Record layout defined in cpy/CSUSR01Y.cpy (80 bytes total)
- Fields: SEC-USR-ID(8), SEC-USR-FNAME(20), SEC-USR-LNAME(20), SEC-USR-PWD(8), SEC-USR-TYPE(1), SEC-USR-FILLER(23)
- User types: 'A' = Admin, 'U' = Regular user
- Password stored as plaintext (no hashing)

## Navigation Flow

```
COADM01C (Admin Menu)
  --> CU00 COUSR00C (List) -- PF7/PF8 paginate (10/page), STARTBR/READNEXT/READPREV/ENDBR
       |-- 'U' selection --> CU02 COUSR02C (Update) -- ENTER to fetch (READ+UPDATE), PF5 to save (REWRITE), PF3 save+exit
       |-- 'D' selection --> CU03 COUSR03C (Delete) -- ENTER to fetch (READ+UPDATE), PF5 to confirm (DELETE)
  --> CU01 COUSR01C (Add) -- ENTER to write (WRITE), PF4 to clear
```

## Key COMMAREA Fields

- CDEMO-PGM-CONTEXT: 0=first entry, 1=re-entry (pseudo-conversational gate)
- CDEMO-CU00-USR-SELECTED: selected user ID passed from COUSR00C to COUSR02C/COUSR03C
- CDEMO-FROM-PROGRAM: return address so COUSR02C/COUSR03C can XCTL back to COUSR00C

## Known Defects / Issues Identified

1. COUSR03C line 332: DELETE error message reads 'Unable to Update User...' — should be 'Unable to Delete User...' (copy-paste from COUSR02C)
2. COUSR03C: WS-USR-MODIFIED flag declared but never set to 'Y' — dead code
3. COUSR00C: WS-USER-DATA (OCCURS 10 table) declared but never populated — map fields are populated directly from SEC-USER-DATA
4. COUSR01C/COUSR03C: User type value not validated beyond blank-check; any single character can be written to VSAM
5. Passwords stored in plaintext in USRSEC

## Tech Spec Documents

All four tech specs produced at 2026-04-03 and stored in tech_specs/:
- COUSR00C_spec.md
- COUSR01C_spec.md
- COUSR02C_spec.md
- COUSR03C_spec.md
