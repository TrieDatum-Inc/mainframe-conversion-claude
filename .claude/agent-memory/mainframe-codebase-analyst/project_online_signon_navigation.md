---
name: CardDemo Online Sign-on and Navigation Programs
description: Detailed architecture of the CICS sign-on and menu programs: COSGN00C, COMEN01C, COADM01C and their BMS screens
type: project
---

## Sign-on and Navigation Subsystem (analyzed 2026-04-02)

**Why:** These three programs form the entry point and navigation hub of the entire CardDemo CICS application. Understanding their COMMAREA protocol, user-type routing, and XCTL patterns is prerequisite to analyzing any downstream functional program.

### Transaction IDs and Program Mapping

| Transaction | Program | Screen Mapset | Map | User Type |
|---|---|---|---|---|
| CC00 | COSGN00C | COSGN00 | COSGN0A | N/A (pre-auth) |
| CM00 | COMEN01C | COMEN01 | COMEN1A | Regular ('U') |
| CA00 | COADM01C | COADM01 | COADM1A | Admin ('A') |

### CARDDEMO-COMMAREA (COCOM01Y.cpy — the application-wide COMMAREA)

Key fields used by every program in the application:
- `CDEMO-FROM-TRANID X(04)` — source transaction
- `CDEMO-FROM-PROGRAM X(08)` — source program
- `CDEMO-TO-TRANID X(04)` — target transaction (set before XCTL)
- `CDEMO-TO-PROGRAM X(08)` — target program (set before XCTL)
- `CDEMO-USER-ID X(08)` — authenticated user ID (set by COSGN00C on login)
- `CDEMO-USER-TYPE X(01)` — 'A'=Admin (88 CDEMO-USRTYP-ADMIN), 'U'=User (88 CDEMO-USRTYP-USER)
- `CDEMO-PGM-CONTEXT 9(01)` — 0=first entry (88 CDEMO-PGM-ENTER), 1=re-entry (88 CDEMO-PGM-REENTER)
- Total structure: approx 130 bytes including customer/account/card fields used by downstream programs

### Authentication Flow (COSGN00C)

1. VSAM file: USRSEC (KSDS, key=user ID X(8), record=SEC-USER-DATA 80 bytes from CSUSR01Y.cpy)
2. Password stored and compared plain-text (SEC-USR-PWD vs WS-USER-PWD, both X(8) upper-cased)
3. RESP=0 → password match → XCTL to COADM01C (type 'A') or COMEN01C (type 'U')
4. Before XCTL: CDEMO-PGM-CONTEXT set to ZEROS (= CDEMO-PGM-ENTER = 0)
5. No CICS HANDLE CONDITION — unhandled errors go to CICS default abend

### Menu Option Data Sources

- COMEN01C menu options: **COMEN02Y.cpy** — 01 CARDDEMO-MAIN-MENU-OPTIONS
  - CDEMO-MENU-OPT-COUNT = 11
  - Array: CDEMO-MENU-OPT OCCURS 12 TIMES (fields: NUM, NAME, PGMNAME, USRTYPE)
  - All 11 options have USRTYPE='U'

- COADM01C admin options: **COADM02Y.cpy** — 01 CARDDEMO-ADMIN-MENU-OPTIONS
  - CDEMO-ADMIN-OPT-COUNT = 6
  - Array: CDEMO-ADMIN-OPT OCCURS 9 TIMES (fields: NUM, NAME, PGMNAME — no USRTYPE)
  - Options 1-4: user management (COUSR00C/01C/02C/03C)
  - Options 5-6: DB2 transaction type management (COTRTLIC, COTRTUPC) — added later (v2.0 copybook)

### Program Dispatch Differences (COMEN01C vs COADM01C)

| Aspect | COMEN01C | COADM01C |
|---|---|---|
| Missing program detection | EXEC CICS INQUIRE PROGRAM NOHANDLE (checks EIBRESP) | EXEC CICS HANDLE CONDITION PGMIDERR(PGMIDERR-ERR-PARA) |
| COPAUS0C special case | Yes — explicit INQUIRE branch for option 11 | Not applicable |
| Error message colour | RED for "not installed" | GREEN for "not installed" |
| Access control | Checks CDEMO-MENU-OPT-USRTYPE per option | No per-option check (all admin-only by screen access) |

### PF3 Navigation Pattern (both menus)

RETURN-TO-SIGNON-SCREEN paragraph:
- XCTL to CDEMO-TO-PROGRAM (defaults to 'COSGN00C')
- **No COMMAREA passed** — COSGN00C receives EIBCALEN=0 and presents fresh sign-on
- This is the application-wide "back to login" mechanism

### CDEMO-PGM-CONTEXT Protocol (used by ALL online programs)

- Sending program sets CDEMO-PGM-CONTEXT = ZEROS before XCTL
- Receiving program tests: IF NOT CDEMO-PGM-REENTER → first entry → send screen
- Receiving program sets CDEMO-PGM-REENTER = TRUE on first entry
- On subsequent pseudo-conversational returns, CDEMO-PGM-REENTER = TRUE → receive input

### BMS Screen Conventions (all three screens)

- All use CTRL=(ALARM,FREEKB), EXTATT=YES, STORAGE=AUTO, TIOAPFX=YES
- Header: row 1 (Tran/Title01/Date), row 2 (Prog/Title02/Time)
- Only COSGN00 has APPLID and SYSID fields (rows 3+)
- ERRMSG: row 23, col 1, LENGTH=78, ASKIP,BRT,FSET, COLOR=RED
- Function key legend: row 24, col 1
- Menu screens (COMEN01/COADM01) are structurally identical except title text

### Shared Utility Copybooks (used by all three programs)

- COTTL01Y.cpy → CCDA-TITLE01/TITLE02 constants ('AWS Mainframe Modernization' / 'CardDemo')
- CSDAT01Y.cpy → WS-DATE-TIME group (CURRENT-DATE → MM/DD/YY and HH:MM:SS formatting)
- CSMSG01Y.cpy → CCDA-MSG-THANK-YOU, CCDA-MSG-INVALID-KEY
- CSUSR01Y.cpy → SEC-USER-DATA layout (used for I/O only in COSGN00C; included in all three)

### Known Issues / Code Defects

- COMEN01C: duplicate MOVE WS-PGMNAME TO CDEMO-FROM-PROGRAM at lines 179-180 (copy-paste)
- COADM01C: PGMIDERR-ERR-PARA has option name reference commented out — generic "not installed" message
- All three: WS-USRSEC-FILE declared but only COSGN00C actually reads USRSEC
- All three: RECEIVE MAP RESP not tested — MAPFAIL condition unhandled
- COADM02Y copybook version (v2.0, 2024-01-21) is much newer than COADM01C program (v1.0, 2022-07-19)

**How to apply:** When analyzing any downstream functional program (COACTVWC, COUSR00C, etc.), expect EIBCALEN > 0 with CARDDEMO-COMMAREA and use the CDEMO-PGM-CONTEXT pattern to understand first-entry vs. re-entry logic. CDEMO-FROM-PROGRAM will be 'COMEN01C' or 'COADM01C'. PF3 in sub-programs typically XCTLs back to CDEMO-FROM-PROGRAM.
