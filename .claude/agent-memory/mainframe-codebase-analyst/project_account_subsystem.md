---
name: CardDemo Account Subsystem — Programs and Specs
description: Analysis of 6 account-related programs (COACTVWC, COACTUPC, CBACT01C–04C): state machines, file access chains, business rules, known anomalies
type: project
---

## Online Account Programs (CICS)

### COACTVWC — Account View (read-only)
- Spec: `/tech_specs/COACTVWC_spec.md`
- Source: `/app/cbl/COACTVWC.cbl`, BMS: `/app/bms/COACTVW.bms`
- Transaction: CACV, links from COSGN00C and other menu programs
- 3-file read chain via CICS: CXACAIX (alternate index by account ID) → ACCTDAT (account record) → CUSTDAT (customer record)
- Copybooks: COCOM01Y (COMMAREA), CVACT01Y (account record), CVCUS01Y (customer record), CVACT03Y (card xref)
- Notable: CXACAIX is a VSAM alternate index path on XREFFILE keyed by XREF-ACCT-ID; primary key is XREF-CARD-NUM
- Notable: Duplicate paragraph label `0000-MAIN-EXIT` at lines 408 and 411 — coding defect

### COACTUPC — Account Update (CICS, most complex online program)
- Spec: `/tech_specs/COACTUPC_spec.md`
- Source: `/app/cbl/COACTUPC.cbl` (~4,237 lines), BMS: `/app/bms/COACTUP.bms`
- State machine via `ACUP-CHANGE-ACTION` X(1) in COMMAREA extension:
  - LOW-VALUES = not yet fetched
  - 'S' = data shown, awaiting confirmation
  - 'E' = validation errors on screen
  - 'N' = user confirmed, not yet written
  - 'C' = write complete (done)
  - 'L' = record locked by another user
  - 'F' = write failed
- 3-phase flow: (1) fetch account/customer via CICS READ, (2) present editable screen, (3) validate edits + optimistic concurrency check + atomic REWRITE both files
- Optimistic concurrency: `9500-STORE-FETCHED-DATA` snapshots old values; `9700-CHECK-CHANGE-IN-REC` re-reads with UPDATE lock and compares; if changed, sets state='L'
- Atomic write: `9600-WRITE-PROCESSING` — READ UPDATE both files, compare, REWRITE both; SYNCPOINT ROLLBACK if customer REWRITE fails
- 30+ field validators in `1200-EDIT-MAP-INPUTS`; calls COBDATFT for date format conversion
- BMS fields: all UNPROT (editable). Dates split into YEAR/MON/DAY sub-fields. SSN split into 3 parts (ACTSSN1/2/3). Phone numbers split 3 ways each.

## Batch Account Programs (CBACT series)

### CBACT01C — Account File Reader/Writer
- Spec: `/tech_specs/CBACT01C_spec.md`
- Source: `/app/cbl/CBACT01C.cbl`
- Opens 4 files: ACCTFILE (input KSDS), OUTFILE (sequential output), ARRYFILE (array output), VBRCFILE (variable-length output)
- Calls COBDATFT for reissue date conversion from YYYYMMDD to MMDDYYYY
- Known anomalies:
  - Hardcoded test values: `2525.00` substituted for zero cycle debit; array hardcoded with `1005.00`, `1525.00`, `-2500.00`, `-1025.00`
  - Only ACCTFILE explicitly closed; OUTFILE, ARRYFILE, VBRCFILE have no CLOSE statements — resource leak bug
- VBRCFILE uses RECORDING MODE IS V; WS-RECD-LEN controls variable record size

### CBACT02C — Card File Printer (read-only display utility)
- Spec: `/tech_specs/CBACT02C_spec.md`
- Source: `/app/cbl/CBACT02C.cbl` (178 lines)
- Reads CARDFILE (KSDS, 150-byte records) sequentially, DISPLAYs each record to SYSOUT
- MISSING ARTIFACT: Copybook CVACT02Y referenced (line 44) but NOT FOUND in `/app/cpy/` directory
- Card record FD: FD-CARD-NUM X(16) + FD-CARD-DATA X(134) = 150 bytes

### CBACT03C — Card Cross-Reference File Printer (read-only display utility)
- Spec: `/tech_specs/CBACT03C_spec.md`
- Source: `/app/cbl/CBACT03C.cbl` (178 lines)
- Reads XREFFILE (KSDS, 50-byte records) sequentially, DISPLAYs each record to SYSOUT
- Copybook CVACT03Y: XREF-CARD-NUM X(16), XREF-CUST-ID 9(9), XREF-ACCT-ID 9(11), FILLER X(14)
- Known bug: DISPLAY CARD-XREF-RECORD appears BOTH inside `1000-XREFFILE-GET-NEXT` (line 95) AND the main loop (line 77) — each record displayed TWICE

### CBACT04C — Interest Calculator (most complex batch program)
- Spec: `/tech_specs/CBACT04C_spec.md`
- Source: `/app/cbl/CBACT04C.cbl` (~653 lines)
- Receives run date via JCL PARM field
- 5 files: TCATBALF (input, must be pre-sorted by account ID), XREF-FILE (input, random), DISCGRP (input, random), ACCOUNT-FILE (input/output), TRANSACT (output)
- Interest formula: `(TRAN-CAT-BAL × DIS-INT-RATE) / 1200` — annual rate ÷ 1200 for monthly
- Falls back to 'DEFAULT' disclosure group if no match found for ACCT-GROUP-ID
- Writes one TRANSACT record per transaction category per account
- Updates account: adds interest to ACCT-CURR-BAL, zeros ACCT-CURR-CYC-CREDIT and ACCT-CURR-CYC-DEBIT
- Known anomaly: `1400-COMPUTE-FEES` paragraph is an unimplemented stub — no processing code
- XREF-FILE vs XREFFILE: Same physical VSAM KSDS, different DD names in batch vs. online (CXACAIX). Batch uses primary key (card number); online uses AIX by account ID.

## Key Copybooks (Account Domain)

| Copybook | Record | Size | Key Fields |
|----------|--------|------|-----------|
| CVACT01Y | ACCT-REC / account record | 300 bytes | ACCT-ID 9(11), ACCT-ACTIVE-STATUS X(1), ACCT-CURR-BAL S9(10)V99, ACCT-CREDIT-LIMIT, ACCT-GROUP-ID X(10) |
| CVCUS01Y | CUST-REC / customer record | 500 bytes | CUST-ID 9(9), names X(25) each, addresses X(50) each, CUST-SSN 9(9), CUST-FICO-CREDIT-SCORE 9(3) |
| CVACT03Y | CARD-XREF-RECORD | 50 bytes | XREF-CARD-NUM X(16), XREF-CUST-ID 9(9), XREF-ACCT-ID 9(11) |
| CVTRA01Y | TRAN-CAT-BAL-RECORD | 50 bytes | TRANCAT-ACCT-ID 9(11), TRANCAT-TYPE-CD X(2), TRANCAT-CD 9(4), TRAN-CAT-BAL S9(9)V99 |
| CVTRA02Y | DISCGRP-RECORD | 50 bytes | DIS-ACCT-GROUP-ID X(10), DIS-TRAN-TYPE-CD X(2), DIS-TRAN-CAT-CD 9(4), DIS-INT-RATE S9(4)V99 |
| CVTRA05Y | TRAN-RECORD | 350 bytes | TRAN-ID X(16), TRAN-TYPE-CD X(2), TRAN-CAT-CD 9(4), TRAN-AMT S9(9)V99, TRAN-CARD-NUM X(16) |
| COCOM01Y | CARDDEMO-COMMAREA | variable | Routing fields (FROM/TO TRANID, PROGRAM), USER-ID, PGM-CONTEXT 9(1) (0=ENTER/1=REENTER) |
| CVACT02Y | CARD-RECORD | 150 bytes | MISSING — not found in /app/cpy/ |

## External Programs Called (Account Domain)

| Program | Type | Caller | Purpose |
|---------|------|--------|---------|
| CEE3ABD | Static CALL | CBACT01C–04C | IBM LE abnormal termination, abend code 999 |
| COBDATFT | Static CALL | CBACT01C, COACTUPC | External assembler routine: date format conversion (YYYYMMDD ↔ MMDDYYYY) via CODATECN-REC |

**Why:** Full analysis session of account subsystem; high-value reference for future migration work.
**How to apply:** Use when analyzing account data flows, understanding state machine patterns in COACTUPC, or cross-referencing batch vs. online access paths to the same VSAM files.
