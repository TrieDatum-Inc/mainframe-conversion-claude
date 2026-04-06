# Technical Specification: COUSR02C — Update User

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | COUSR02C |
| Source File | `app/cbl/COUSR02C.cbl` |
| Type | CICS Online |
| Transaction ID | CU02 |
| BMS Mapset | COUSR02 |
| BMS Map | COUSR2A |

## 2. Purpose

COUSR02C is an **admin function** that updates an existing user record. It reads the user by ID with an UPDATE lock, displays current values, allows modification of name/password/type, and only issues a REWRITE if at least one field has changed.

## 3. Copybooks Used

| Copybook | Purpose |
|----------|---------|
| COCOM01Y | CARDDEMO-COMMAREA (extended with CDEMO-CU02-INFO) |
| COUSR02 | BMS symbolic map |
| COTTL01Y, CSDAT01Y, CSMSG01Y, CSUSR01Y | Standard infrastructure |
| DFHAID, DFHBMSCA | CICS constants |

## 4. VSAM Files Accessed

| File DD | Access Mode | Operations | Key |
|---------|-------------|------------|-----|
| USRSEC | Update | READ with UPDATE, REWRITE | SEC-USR-ID X(8) |

## 5. Screen Fields

### Input Fields
| Field | Length | Description |
|-------|--------|-------------|
| USRIDIN | 8 | User ID to fetch (cursor initial) |
| FNAME | 20 | First name (editable after fetch) |
| LNAME | 20 | Last name |
| PASSWD | 8 | New password (non-display) |
| USRTYPE | 1 | User type |

### Function Keys
| Key | Action |
|-----|--------|
| ENTER | Fetch user record |
| PF3 | Save and exit to calling program |
| PF4 | Clear form |
| PF5 | Save changes |
| PF12 | Cancel, return to COADM01C |

## 6. Program Flow (Two-Phase)

```
Phase 1 — Fetch (ENTER):
   a. READ USRSEC by USRIDIN
   b. Display current field values
   c. Prompt "Press PF5 to save"

Phase 2 — Update (PF5):
   a. Re-validate all fields non-empty
   b. READ USRSEC with UPDATE (acquire lock)
   c. Compare each screen field to stored value
   d. Set USR-MODIFIED-YES if any field differs
   e. If modified: REWRITE with new values
   f. If no changes: "Please modify to update"
```

## 7. Business Rules

1. Only issues REWRITE if at least one field has actually changed (optimistic update check).
2. Uses READ with UPDATE for VSAM record locking during the update phase.
3. All fields must be non-empty for the update to proceed.

## 8. Inter-Program Communication

| Target | Method | Condition |
|--------|--------|-----------|
| CDEMO-FROM-PROGRAM (caller) | XCTL | PF3 |
| COADM01C | XCTL | PF12 or default |
