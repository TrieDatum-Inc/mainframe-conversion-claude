# Technical Specification: COSGN00C — Sign-On Screen

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | COSGN00C |
| Source File | `app/cbl/COSGN00C.cbl` |
| Type | CICS Online |
| Transaction ID | CC00 |
| BMS Mapset | COSGN00 |
| BMS Map | COSGN0A |
| Language | Enterprise COBOL |

## 2. Purpose

COSGN00C is the **entry point** for the entire CardDemo application. It displays a sign-on screen, collects a User ID and Password, authenticates the user against the USRSEC VSAM file, and routes to either the admin menu (COADM01C) or the regular user menu (COMEN01C) based on the user's type.

## 3. Copybooks Used

| Copybook | Purpose |
|----------|---------|
| COCOM01Y | CARDDEMO-COMMAREA — inter-program communication area |
| COSGN00 | BMS symbolic map (COSGN0AI / COSGN0AO) |
| COTTL01Y | Application title strings |
| CSDAT01Y | Date/time working storage |
| CSMSG01Y | Common screen messages |
| CSUSR01Y | SEC-USER-DATA record layout (USRSEC) |
| DFHAID | CICS attention identifier constants |
| DFHBMSCA | BMS field attribute constants |

## 4. VSAM Files Accessed

| File DD | Dataset | Access Mode | Key | Record Layout |
|---------|---------|-------------|-----|---------------|
| USRSEC | AWS.M2.CARDDEMO.USRSEC.VSAM.KSDS | READ | SEC-USR-ID X(8) | CSUSR01Y (80 bytes) |

## 5. Screen Fields

### Input Fields
| Field | Length | Type | Description |
|-------|--------|------|-------------|
| USERID | 8 | X(8) | User ID — cursor initial position |
| PASSWD | 8 | X(8) | Password — non-display (DRK attribute) |

### Output Fields
| Field | Length | Description |
|-------|--------|-------------|
| TRNNAME | 4 | Transaction name (CC00) |
| PGMNAME | 8 | Program name (COSGN00C) |
| TITLE01 | 40 | 'AWS Mainframe Modernization' |
| TITLE02 | 40 | 'CardDemo' |
| CURDATE | 8 | Current date (MM/DD/YY) |
| CURTIME | 9 | Current time (HH:MM:SS) |
| APPLID | 8 | CICS APPLID |
| SYSID | 8 | CICS System ID |
| ERRMSG | 78 | Error message (row 23, RED) |

### Function Keys
| Key | Action |
|-----|--------|
| ENTER | Authenticate and route |
| PF3 | Exit application |

## 6. Program Flow

```
1. If EIBCALEN = 0 (first entry):
   → Send blank sign-on screen with cursor on USERID
   → RETURN TRANSID('CC00')

2. On ENTER:
   a. RECEIVE MAP(COSGN0A)
   b. Validate USERID not blank
   c. Validate PASSWD not blank
   d. Uppercase both USERID and PASSWORD
   e. Move USERID to CDEMO-USER-ID in COMMAREA
   f. READ USRSEC with key = WS-USER-ID
   g. Compare SEC-USR-PWD to entered password
   h. If match:
      - Set CDEMO-FROM-TRANID = 'CC00'
      - Set CDEMO-FROM-PROGRAM = 'COSGN00C'
      - Set CDEMO-USER-TYPE from SEC-USR-TYPE
      - Set CDEMO-PGM-CONTEXT = 0
      - If ADMIN user → XCTL to COADM01C
      - If REGULAR user → XCTL to COMEN01C
   i. If no match → display "Wrong Password"

3. On PF3:
   → Send "Thank you" message
   → RETURN (ends CICS session — no TRANSID)

4. Any other key:
   → Display "Invalid key" error
```

## 7. Inter-Program Communication

### COMMAREA Passed (COCOM01Y)
| Field | Value Set |
|-------|-----------|
| CDEMO-FROM-TRANID | 'CC00' |
| CDEMO-FROM-PROGRAM | 'COSGN00C' |
| CDEMO-USER-ID | Entered User ID |
| CDEMO-USER-TYPE | 'A' (admin) or 'U' (regular) |
| CDEMO-PGM-CONTEXT | 0 (first entry) |

### Programs Called
| Target Program | Method | Condition |
|---------------|--------|-----------|
| COADM01C | EXEC CICS XCTL | User type = Admin |
| COMEN01C | EXEC CICS XCTL | User type = Regular |

## 8. Error Handling

| Condition | Message |
|-----------|---------|
| USRSEC READ RESP=NOTFND | "User not found" |
| Password mismatch | "Wrong Password" |
| Other RESP codes | "Unable to verify the User" |
| Blank USERID | Cursor repositioned to USERID field |
| Blank PASSWD | Cursor repositioned to PASSWD field |
| Invalid AID key | "Invalid key" |

## 9. Business Rules

1. Authentication is performed against the USRSEC VSAM file using exact match on User ID and Password.
2. Both User ID and Password are uppercased before comparison.
3. User type determines the target menu: Admin users go to COADM01C, regular users go to COMEN01C.
4. PF3 terminates the CICS session entirely (no TRANSID on RETURN).

## 10. Data Flow Diagram

```
User Terminal
    |
    | (USERID, PASSWD)
    v
COSGN00C ──READ──> USRSEC VSAM
    |                  |
    |          (SEC-USR-PWD, SEC-USR-TYPE)
    |
    |── Admin ──> XCTL ──> COADM01C (CA00)
    |
    └── User  ──> XCTL ──> COMEN01C (CM00)
```
