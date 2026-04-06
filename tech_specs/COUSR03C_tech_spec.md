# Technical Specification: COUSR03C — Delete User

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | COUSR03C |
| Source File | `app/cbl/COUSR03C.cbl` |
| Type | CICS Online |
| Transaction ID | CU03 |
| BMS Mapset | COUSR03 |
| BMS Map | COUSR3A |

## 2. Purpose

COUSR03C is an **admin function** for deleting a user record from the USRSEC VSAM file. It follows a two-phase approach: first fetch and display the record for confirmation, then delete on PF5.

## 3. Copybooks Used

| Copybook | Purpose |
|----------|---------|
| COCOM01Y | CARDDEMO-COMMAREA (extended with CDEMO-CU03-INFO) |
| COUSR03 | BMS symbolic map |
| COTTL01Y, CSDAT01Y, CSMSG01Y, CSUSR01Y | Standard infrastructure |
| DFHAID, DFHBMSCA | CICS constants |

## 4. VSAM Files Accessed

| File DD | Access Mode | Operations | Key |
|---------|-------------|------------|-----|
| USRSEC | Delete | READ with UPDATE, DELETE | SEC-USR-ID X(8) |

## 5. Screen Fields

### Input Fields
| Field | Length | Description |
|-------|--------|-------------|
| USRIDIN | 8 | User ID to fetch/delete |

### Output Fields (read-only display)
| Field | Length | Description |
|-------|--------|-------------|
| FNAME | 20 | First name (ASKIP — protected) |
| LNAME | 20 | Last name (ASKIP — protected) |
| USRTYPE | 1 | User type (ASKIP — protected) |

### Function Keys
| Key | Action |
|-----|--------|
| ENTER | Fetch user record for confirmation |
| PF3 | Back to calling program |
| PF4 | Clear form |
| PF5 | Confirm delete |

## 6. Program Flow (Two-Phase)

```
Phase 1 — Fetch (ENTER):
   a. Validate USRIDIN not empty
   b. READ USRSEC with UPDATE (lock)
   c. Display record fields as protected output
   d. Prompt "Press PF5 to delete"

Phase 2 — Delete (PF5):
   a. Re-validate USRIDIN not empty
   b. READ USRSEC with UPDATE (re-acquire lock)
   c. EXEC CICS DELETE (uses existing lock token)
   d. Clear fields, show "User XXXX has been deleted"
```

## 7. Key Difference from COUSR02C

FNAME, LNAME, USRTYPE are **ASKIP/FSET/NORM** (output-only, not editable) — the user can only view the record before confirming deletion.

## 8. Inter-Program Communication

| Target | Method | Condition |
|--------|--------|-----------|
| CDEMO-FROM-PROGRAM | XCTL | PF3 |
| COADM01C | XCTL | PF12 or default |
