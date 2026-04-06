# Technical Specification: COMEN01C — Regular User Main Menu

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | COMEN01C |
| Source File | `app/cbl/COMEN01C.cbl` |
| Type | CICS Online |
| Transaction ID | CM00 |
| BMS Mapset | COMEN01 |
| BMS Map | COMEN1A |

## 2. Purpose

COMEN01C is the **main navigation menu** for regular (non-admin) users. It displays up to 12 numbered menu options populated from the COMEN02Y copybook array, accepts a 2-digit numeric selection, validates access permissions, and routes (XCTL) to the selected program.

## 3. Copybooks Used

| Copybook | Purpose |
|----------|---------|
| COCOM01Y | CARDDEMO-COMMAREA |
| COMEN02Y | Menu option array (11 options with program names and user types) |
| COMEN01 | BMS symbolic map |
| COTTL01Y | Application title strings |
| CSDAT01Y | Date/time working storage |
| CSMSG01Y | Common screen messages |
| CSUSR01Y | User record layout |
| DFHAID | CICS AID constants |
| DFHBMSCA | BMS field attribute constants |

## 4. VSAM Files Accessed

None directly. This program is purely a navigation router.

## 5. Menu Options (from COMEN02Y)

| Option | Display Name | Target Program | User Type |
|--------|-------------|----------------|-----------|
| 01 | Account View | COACTVWC | U |
| 02 | Account Update | COACTUPC | U |
| 03 | Credit Card List | COCRDLIC | U |
| 04 | Credit Card View | COCRDSLC | U |
| 05 | Credit Card Update | COCRDUPC | U |
| 06 | Transaction List | COTRN00C | U |
| 07 | Transaction View | COTRN01C | U |
| 08 | Transaction Add | COTRN02C | U |
| 09 | Transaction Reports | CORPT00C | U |
| 10 | Bill Payment | COBIL00C | U |
| 11 | Pending Authorization View | COPAUS0C | U |

## 6. Screen Fields

### Input Fields
| Field | Length | Type | Description |
|-------|--------|------|-------------|
| OPTION | 2 | X(2), NUM | 2-digit option number (right-justified, zero-fill) |

### Output Fields
| Field | Length | Description |
|-------|--------|-------------|
| OPTN001–OPTN012 | 40 each | Menu option display lines |
| ERRMSG | 78 | Error message |
| Standard header | — | TRNNAME, PGMNAME, TITLE01, TITLE02, CURDATE, CURTIME |

### Function Keys
| Key | Action |
|-----|--------|
| ENTER | Navigate to selected option |
| PF3 | Return to sign-on screen (COSGN00C) |

## 7. Program Flow

```
1. If EIBCALEN = 0:
   → XCTL to COSGN00C (session lost, redirect to login)

2. First entry (CDEMO-PGM-REENTER not set):
   → Set CDEMO-PGM-REENTER flag
   → BUILD-MENU-OPTIONS: populate OPTN001–012 from COMEN02Y array
   → SEND MAP with menu options

3. On ENTER:
   a. RECEIVE MAP
   b. Parse OPTION as numeric
   c. Validate option is in range 1..CDEMO-MENU-OPT-COUNT (11)
   d. Check CDEMO-MENU-OPT-USRTYPE(option):
      - If 'A' and user is not admin → "No access" error
   e. Check if program name starts with 'DUMMY' → "Coming soon"
   f. If program = COPAUS0C:
      - EXEC CICS INQUIRE PROGRAM(COPAUS0C) to verify installed
      - If not installed → show error
   g. Set COMMAREA fields and XCTL to target program

4. On PF3:
   → XCTL to COSGN00C
```

## 8. Inter-Program Communication

### COMMAREA Fields Set Before XCTL
| Field | Value |
|-------|-------|
| CDEMO-FROM-TRANID | CM00 |
| CDEMO-FROM-PROGRAM | COMEN01C |
| CDEMO-TO-PROGRAM | Target program name from array |

### Programs Called
| Target | Method | Condition |
|--------|--------|-----------|
| COACTVWC–COPAUS0C | XCTL | Based on option selected |
| COSGN00C | XCTL | PF3 or EIBCALEN=0 |

## 9. Business Rules

1. Admin-only menu options (USRTYPE='A') are blocked for regular users with "No access" error.
2. Options pointing to programs starting with 'DUMMY' show "Coming soon" — placeholder for unimplemented features.
3. COPAUS0C (authorization view) is dynamically checked with EXEC CICS INQUIRE PROGRAM before navigation — handles the case where the authorization sub-application is not installed.
4. The menu is data-driven: adding/removing options only requires changes to the COMEN02Y copybook.

## 10. Data Flow Diagram

```
COSGN00C ──XCTL──> COMEN01C
                      |
                      | (OPTION selected)
                      v
              COMEN02Y array lookup
                      |
    ┌─────────────────┼─────────────────┐
    v                 v                 v
COACTVWC         COTRN00C          COBIL00C
(Account)      (Transactions)    (Bill Pay)
    ...              ...              ...
```
