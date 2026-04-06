# Technical Specification: COUSR01C — Add User

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | COUSR01C |
| Source File | `app/cbl/COUSR01C.cbl` |
| Type | CICS Online |
| Transaction ID | CU01 |
| BMS Mapset | COUSR01 |
| BMS Map | COUSR1A |

## 2. Purpose

COUSR01C is an **admin function** that creates a new user record in the USRSEC VSAM file. It collects first name, last name, user ID, password, and user type, validates all fields, and writes the new record.

## 3. Copybooks Used

| Copybook | Purpose |
|----------|---------|
| COCOM01Y | CARDDEMO-COMMAREA |
| COUSR01 | BMS symbolic map |
| COTTL01Y, CSDAT01Y, CSMSG01Y, CSUSR01Y | Standard infrastructure |
| DFHAID, DFHBMSCA | CICS constants |

## 4. VSAM Files Accessed

| File DD | Access Mode | Operations | Key |
|---------|-------------|------------|-----|
| USRSEC | Write | WRITE | SEC-USR-ID X(8) |

## 5. Screen Fields

### Input Fields
| Field | Length | Description |
|-------|--------|-------------|
| FNAME | 20 | First name (cursor initial) |
| LNAME | 20 | Last name |
| USERID | 8 | User ID |
| PASSWD | 8 | Password (non-display, DRK) |
| USRTYPE | 1 | User type (A=Admin, U=User) |

### Function Keys
| Key | Action |
|-----|--------|
| ENTER | Add user record |
| PF3 | Back to admin menu |
| PF4 | Clear form |

## 6. Program Flow

```
1. On ENTER:
   a. Validate all 5 fields non-empty (sequential checks)
   b. Move screen fields into SEC-USER-DATA record:
      - SEC-USR-ID = USERID
      - SEC-USR-FNAME = FNAME
      - SEC-USR-LNAME = LNAME
      - SEC-USR-PWD = PASSWD
      - SEC-USR-TYPE = USRTYPE
   c. EXEC CICS WRITE to USRSEC with RIDFLD=SEC-USR-ID
   d. On success: clear fields, show "User XXXX has been added"
   e. On DUPKEY/DUPREC: "User ID already exist"
```

## 7. Error Handling

| Condition | Message |
|-----------|---------|
| Any field blank | Field-specific error with cursor repositioned |
| Duplicate key (WRITE) | "User ID already exist" |

## 8. Inter-Program Communication

| Target | Method | Condition |
|--------|--------|-----------|
| COADM01C | XCTL | PF3 |
