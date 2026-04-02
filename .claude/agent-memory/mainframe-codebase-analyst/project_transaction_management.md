---
name: Transaction Management Online Programs
description: COTRN00C/COTRN01C/COTRN02C program analysis - transaction list, view, add; VSAM browse patterns, xref lookups, pagination
type: project
---

## Transaction Management Subsystem — Online Programs

**Why:** Three programs form the complete online transaction management flow: list/browse, view detail, and add new transaction.

### Program Inventory

| Program | TransID | BMS Mapset | Map | Function |
|---|---|---|---|---|
| COTRN00C | CT00 | COTRN00 | COTRN0A | Paginated transaction list with VSAM browse |
| COTRN01C | CT01 | COTRN01 | COTRN1A | View single transaction detail (read-only) |
| COTRN02C | CT02 | COTRN02 | COTRN2A | Add new transaction with full validation |

### Navigation Flow
```
COMEN01C (menu) --> COTRN00C [CT00] --> (S selection) XCTL --> COTRN01C [CT01]
COTRN01C F3 --> back to COTRN00C (CDEMO-FROM-PROGRAM)
COTRN01C F5 --> XCTL to COTRN00C (browse)
COTRN00C F3 --> XCTL to COMEN01C
```

### COMMAREA Extension Pattern
All three programs extend CARDDEMO-COMMAREA after COPY COCOM01Y with a program-specific block:
- CDEMO-CT00-INFO / CDEMO-CT01-INFO / CDEMO-CT02-INFO
- Contains: TRNID-FIRST, TRNID-LAST, PAGE-NUM, NEXT-PAGE-FLG, TRN-SEL-FLG, TRN-SELECTED
- TRN-SELECTED passes the chosen Transaction ID from COTRN00C to COTRN01C via XCTL
- These fields share the same physical COMMAREA position; CT01 reads what CT00 wrote

### COTRN00C Pagination Design
- Uses CICS STARTBR/READNEXT/READPREV/ENDBR on TRANSACT VSAM file
- 10 rows per page; CDEMO-CT00-TRNID-FIRST and CDEMO-CT00-TRNID-LAST are browse anchors
- PF7=backward (uses TRNID-FIRST), PF8=forward (uses TRNID-LAST)
- Reads one extra record beyond 10 to set NEXT-PAGE-YES/NO for PF8 guard
- WS-SEND-ERASE-FLG=NO for boundary messages (preserves screen while posting message)
- Date display: extracts from TRAN-ORIG-TS timestamp into MM/DD/YY format

### COTRN01C Design Issues (Flag for Modernization)
- Issues READ UPDATE (exclusive lock) on TRANSACT file but never REWRITE or UNLOCK
- Lock held until pseudo-conversational RETURN ends the task — potential contention
- WS-USR-MODIFIED flag declared but never set (scaffolding for future update capability)

### COTRN02C Key Design Points
- Auto-increments Transaction ID: STARTBR(HIGH-VALUES) + READPREV = last record; key+1 = new key
- Race condition: two concurrent CT02 sessions could generate same ID; DUPKEY on WRITE is the only guard
- SEND-TRNADD-SCREEN contains embedded EXEC CICS RETURN (exits task on every send)
- MAIN-PARA RETURN at line 156 only reached when XCTL exits (no SEND path)
- Two-field key resolution: either ACTIDIN (account) or CARDNIN (card) accepted:
  - Account path: READ CXACAIX (AIX, keyed by XREF-ACCT-ID) to get card number
  - Card path: READ CCXREF (KSDS, keyed by XREF-CARD-NUM) to get account ID
- Date validation: CALL 'CSUTLDTC' for both TORIGDT and TPROCDT; tolerates msg '2513'
- CVACT01Y copied in but ACCOUNT-RECORD not used in procedure division (WS-ACCTDAT-FILE declared, unused)
- F5 copies last transaction's fields for batch entry of similar transactions

### Files Accessed by This Subsystem

| File | COTRN00C | COTRN01C | COTRN02C |
|---|---|---|---|
| TRANSACT | STARTBR/READNEXT/READPREV/ENDBR | READ UPDATE | STARTBR/READPREV/ENDBR/WRITE |
| CCXREF | — | — | READ (card → account) |
| CXACAIX | — | — | READ (account → card, AIX) |
| ACCTDAT | — | — | Declared only, never accessed |

### BMS Map Comparison

| Screen | Entry Key Field | Data Fields | Confirmation |
|---|---|---|---|
| COTRN0A | TRNIDIN (search filter, optional) | 10-row list: SEL+TRNID+DATE+DESC+AMT | None |
| COTRN1A | TRNIDIN (Tran ID to fetch) | TRNID,CARDNUM,TTYPCD,TCATCD,TRNSRC,TDESC,TRNAMT,TORIGDT,TPROCDT,MID,MNAME,MCITY,MZIP — all ASKIP | None |
| COTRN2A | ACTIDIN + CARDNIN | Same fields as COTRN1A but all UNPROT (editable); amount/date format hints on row 15 | CONFIRM Y/N field |

**How to apply:** When modernizing this subsystem, note the READ UPDATE issue in COTRN01C, the non-atomic ID generation in COTRN02C, and the COMMAREA positional aliasing between CT00/CT01/CT02 blocks.
