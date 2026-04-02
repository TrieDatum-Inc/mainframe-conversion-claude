---
name: Credit Card Management Subsystem
description: COCRDLIC/COCRDSLC/COCRDUPC programs and their BMS maps — credit card list, view, and update
type: project
---

## Credit Card Management Subsystem — Analyzed 2026-04-02

### Programs and Transactions

| Program   | Trans | Mapset   | Map     | Function               |
|-----------|-------|----------|---------|------------------------|
| COCRDLIC  | CCLI  | COCRDLI  | CCRDLIA | Paginated card list    |
| COCRDSLC  | CCDL  | COCRDSL  | CCRDSLA | Card detail view (R/O) |
| COCRDUPC  | CCUP  | COCRDUP  | CCRDUPA | Card detail update     |

### Navigation Flow
```
COMEN01C --> XCTL --> COCRDLIC
COCRDLIC  --> XCTL --> COCRDSLC (S selection)
COCRDLIC  --> XCTL --> COCRDUPC (U selection)
COCRDSLC  --> XCTL --> COCRDLIC (PF3)
COCRDUPC  --> XCTL --> COCRDLIC (post-update auto-exit) or COMEN01C (PF3)
```

### Files Accessed
- **CARDDAT** (VSAM KSDS, primary key CARD-NUM X(16)): All three programs access this.
  - COCRDLIC: STARTBR/READNEXT/READPREV/ENDBR for pagination
  - COCRDSLC: Direct READ by primary key
  - COCRDUPC: READ (display), READ UPDATE + REWRITE (update)
- **CARDAIX** (alternate index on CARDDAT keyed by CARD-ACCT-ID X(11)): Defined in constants of COCRDLIC and COCRDSLC but only indirectly relevant — COCRDLIC browsing uses primary key CARDDAT with post-read account filtering; COCRDSLC 9150-GETCARD-BYACCT is dead code.

### COMMAREA Protocol
- Base COMMAREA: CARDDEMO-COMMAREA from COCOM01Y (~100 bytes)
- Program-specific extension appended after base:
  - COCRDLIC: WS-THIS-PROGCOMMAREA includes first/last card keys, page number, last-page indicator, next-page indicator (pagination state)
  - COCRDSLC: WS-THIS-PROGCOMMAREA is minimal (CA-FROM-PROGRAM, CA-FROM-TRANID only)
  - COCRDUPC: WS-THIS-PROGCOMMAREA includes CCUP-CHANGE-ACTION state flag, CCUP-OLD-DETAILS snapshot, CCUP-NEW-DETAILS, CARD-UPDATE-RECORD

### Key Design Patterns
1. **COCRDLIC pagination**: 7-row pages, STARTBR/READNEXT forward browse with account/card filter applied post-read in 9500-FILTER-RECORDS. Backward browse uses STARTBR+READPREV from current first key.
2. **COCRDLIC selection**: WS-EDIT-SELECT-FLAGS (7 x X(1)) receives CRDSELnI values. Only one 'S' or 'U' allowed; multiple selections are rejected with error.
3. **COCRDUPC state machine**: CCUP-CHANGE-ACTION PIC X(1) drives all screen behavior — NOT-FETCHED, SHOW-DETAILS, CHANGES-NOT-OK, CHANGES-OK-NOT-CONFIRMED, OKAYED-AND-DONE, LOCK-ERROR, FAILED.
4. **COCRDUPC optimistic locking**: READ UPDATE locks record; 9300-CHECK-CHANGE-IN-REC compares current record against CCUP-OLD-DETAILS snapshot. If mismatch (concurrent update), aborts and re-displays with fresh data.
5. **COCRDUPC SYNCPOINT**: Issued before XCTL on exit to ensure REWRITE is committed.
6. **EXPDAY hidden field**: COCRDUP.BMS has DRK/FSET/PROT EXPDAY at row 15 col 36 to carry expiry day across the CICS RETURN loop without user access.
7. **FKEYSC bright-on-confirm**: COCRDUP.BMS FKEYSC field ('F5=Save F12=Cancel') is dark by default; COCRDUPC sets DFHBMBRY only in CCUP-CHANGES-OK-NOT-CONFIRMED state.

### Copybooks Shared Across All Three Programs
- CVCRD01Y: CC-WORK-AREAS, CCARD-AID-xxx, CC-ACCT-ID, CC-CARD-NUM
- COCOM01Y: CARDDEMO-COMMAREA
- CVACT02Y: CARD-RECORD layout (CARD-NUM/CARD-ACCT-ID/CARD-CVV-CD/CARD-EMBOSSED-NAME/CARD-EXPIRAION-DATE/CARD-ACTIVE-STATUS)
- CSSTRPFY: PFKey store inline COPY (maps EIBAID to CCARD-AID text value)

### Known Issues / Gaps
- COCRDSLC 9150-GETCARD-BYACCT (reads CARDAIX by account ID) is defined but never called — dead code.
- COCRDLIC paragraph 1250-SETUP-ARRAY-ATTRIBS: row 1 empty uses DFHBMPRF, rows 2-7 empty use DFHBMPRO — minor attribute inconsistency (DFHBMPRF vs DFHBMPRO differ in modified data tag behavior).
- COCRDLIC source line 790 appears to have a stray `I` on its own line between the DFHBMPRO statement and ELSE — potential source formatting artifact.

### Spec Files Written
- tech_specs/COCRDLIC_spec.md
- tech_specs/COCRDSLC_spec.md
- tech_specs/COCRDUPC_spec.md
- tech_specs/COCRDLI_bms_spec.md
- tech_specs/COCRDSL_bms_spec.md
- tech_specs/COCRDUP_bms_spec.md
