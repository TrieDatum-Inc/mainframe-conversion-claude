---
name: CardDemo Architecture
description: Core CardDemo application architecture - VSAM files, copybook conventions, program types, and key design patterns
type: project
---

## Application: CardDemo (AWS sample mainframe application)

**Why:** This is a reference mainframe application used as a modernization exercise target.

### Five Core VSAM KSDS Files

| DD Name  | Copybook  | Key Field        | Record Len | Content             |
|----------|-----------|------------------|------------|---------------------|
| CUSTFILE | CVCUS01Y  | CUST-ID 9(09)    | 500 bytes  | Customer demographics |
| ACCTFILE | CVACT01Y  | ACCT-ID 9(11)    | 300 bytes  | Account financial data |
| XREFFILE | CVACT03Y  | XREF-CARD-NUM X(16) | 50 bytes | Card-to-customer-account cross-reference |
| CARDFILE | CVACT02Y  | CARD-NUM X(16)   | 150 bytes  | Physical card data |
| TRANSACT | CVTRA05Y  | TRAN-ID X(16)    | 350 bytes  | Transactions |

Also: TRNXFILE uses COSTM01.CPY (different layout from CVTRA05Y - has composite key CARD-NUM+TRAN-ID).

### Copybook Naming Convention
- CV* = VSAM record layouts (CVACT01Y, CVACT02Y, CVACT03Y, CVCUS01Y, CVTRA05Y)
- CS* = Shared working-storage utilities (CSUTLDWY = date validation WS, CSUTLDPY = date validation procedure)
- CO* = BMS map copybooks in app/cpy-bms/
- CUSTREC.cpy = alternate customer record layout (field CUST-DOB-YYYYMMDD without dashes, vs CVCUS01Y which has CUST-DOB-YYYY-MM-DD)
- CVEXPORT.cpy = multi-type union export record (500 bytes, REDEFINES for C/A/X/T/D record types)

### Program Types
- CB* = Batch COBOL (CBSTM03A/B, CBEXPORT, CBIMPORT, CBACT*, CBTRN*, CBCUS01C)
- CO* = Online CICS COBOL (COACTUPC, COSGN00C, COTRN*, COUSR*, etc.)
- CS* = Utility subroutines (CSUTLDTC = date validator)
- COBSWAIT = batch wait utility

### CICS Dataset Names (FCT logical names used in EXEC CICS READ/WRITE)
- ACCTDAT = account file (batch DD: ACCTFILE)
- CUSTDAT = customer file (batch DD: CUSTFILE)
- CARDDAT = card file (batch DD: CARDFILE)
- TRANSACT = transaction file (batch DD: TRANFILE)
- USRSEC = user security file
- CXACAIX = alternate index on CARDDAT by account ID (used in COACTUPC, COBIL00C, COACTVWC)

### DB2 Tables (schema CARDDEMO)
- CARDDEMO.TRANSACTION_TYPE — transaction type codes; maintained by COTRTLIC/COTRTUPC/COBTUPDT
- CARDDEMO.AUTHFRDS — authorization fraud records; maintained by COPAUS2C
- CARDDEMO.TRANSACTION_CATEGORY — transaction category codes (inferred, DCLTRCAT referenced by COTRTUPC)

### IMS Databases
- PAUT PCB (keyfb 255) — authorization table root; used by PAUDBLOD/PAUDBUNL/DBUNLDGS
- PASFL PCB (keyfb 100) — authorization summary (CIPAUSMY segment); used by DBUNLDGS only
- PADFL PCB (keyfb 255) — authorization details (CIPAUDTY segment); used by DBUNLDGS only

### CICS Transaction IDs
- CC00=COSGN00C, CA00=COADM01C, CM00=COMEN01C
- CT00=COTRN00C, CT01=COTRN01C, CT02=COTRN02C
- CR00=CORPT00C, CB00=COBIL00C, CU00-CU03=COUSR00-03C
- CTLI=COTRTLIC

### Tech Spec Documents Written
- tech_specs/COPYBOOKS_spec.md — full catalog of all 57 copybooks with field layouts, usage map, sharing patterns
- tech_specs/SYSTEM_OVERVIEW_spec.md — architecture, program inventory, XCTL graph, data model, screen navigation, batch flows

### Known Design Patterns
- ALTER/GO TO dispatch in CBSTM03A (deprecated legacy pattern)
- PSA/TCB/TIOT control block walk in CBSTM03A (z/OS-specific diagnostic)
- File I/O delegation pattern: CBSTM03A delegates all VSAM I/O to CBSTM03B via 1047-byte parameter block
- Multi-type export/import pattern: CBEXPORT writes type-coded records (C/A/X/T/D) to EXPFILE; CBIMPORT reads and splits by type
- CEE3ABD = standard LE abend call used across all batch programs for fatal error termination
- CSUTLDTC = shared date validation utility; called via CSUTLDPY procedure copybook pattern

### Known Field Name Typos (Consistent Across Codebase)
- ACCT-EXPIRAION-DATE (missing 'T' in EXPIRATION) - in CVACT01Y and everywhere ACCT is used
- CARD-EXPIRAION-DATE (same typo) - in CVACT02Y

**How to apply:** When analyzing any program that references account or card expiration dates, expect the typo field name. Do not flag as an error in individual programs; it is a consistent system-wide naming issue.
