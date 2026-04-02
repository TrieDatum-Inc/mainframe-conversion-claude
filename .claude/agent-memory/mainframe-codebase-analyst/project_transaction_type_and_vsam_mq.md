---
name: Transaction Type DB2 Subsystem and VSAM-MQ Service Programs
description: COBTUPDT batch utility, COTRTLIC/COTRTUPC CICS programs, COTRTLI/COTRTUP BMS maps, COACCT01/CODATE01 MQ-triggered services — architecture, patterns, and known gaps
type: project
---

## Transaction Type DB2 Subsystem

### Programs
- **COBTUPDT** (batch): Reads DD INPFILE (sequential, 53-byte records), performs INSERT/UPDATE/DELETE to CARDDEMO.TRANSACTION_TYPE based on record type code (A/U/D/*). No CICS, no COMMIT. Sets RETURN-CODE=4 on error but continues processing. File open failure is non-fatal (latent defect).
- **COTRTLIC** (CICS, trans CTLI): Paginated list screen using BMS COTRTLI/CTRTLIA. Up to 7 rows; bidirectional DB2 cursor paging (C-TR-TYPE-FORWARD / C-TR-TYPE-BACKWARD). Filter by type code (exact) and description (LIKE with % wildcards). Action codes D (delete) and U (update) per row. Inline UPDATE/DELETE with EXEC CICS SYNCPOINT. PERFORM 9998-PRIMING-QUERY (SELECT 1 FROM SYSIBM.SYSDUMMY1) at startup. Calls DSNTIAC for DB2 error formatting.
- **COTRTUPC** (CICS, trans CTTU): Single-record add/update/delete detail screen using BMS COTRTUP/CTRTUPA. Full state machine via TTUP-CHANGE-ACTION (16 states). SELECT on entry, UPDATE attempts first with INSERT fallback on +100, DELETE with SQLCODE -532 RI check. All DML followed by EXEC CICS SYNCPOINT.

### DB2 Table
- `CARDDEMO.TRANSACTION_TYPE` columns: TR_TYPE (PIC X(2)), TR_DESCRIPTION (varchar, accessed via DCLGEN DCLTRTYP with DCL-TR-DESCRIPTION-TEXT and DCL-TR-DESCRIPTION-LEN)

### BMS Maps
- COTRTLI (mapset) / CTRTLIA (map): 24×80, 7 data rows (rows 12-18), filter fields row 6 and 8, PF keys F2/F3/F7/F8/F10 on row 24. Program REDEFINES symbolic map to create OCCURS 7 TIMES array.
- COTRTUP (mapset) / CTRTUPA (map): 24×80, 2 data fields (TRTYPCD row 12, TRTYDSC row 14), 4 PF key labels initially DRK (F4/F5/F6/F12) made bright by program based on state.

### COMMAREA Structure (COTRTLIC / COTRTUPC)
- Part 1: CARDDEMO-COMMAREA (from COCOM01Y) — navigation state
- Part 2: Program-specific (WS-THIS-PROGCOMMAREA) — paging state for COTRTLIC; TTUP-CHANGE-ACTION + OLD/NEW detail snapshots for COTRTUPC

### Copybooks Unique to This Subsystem
- CSDB2RWY: DB2 common working storage (WS-DB2-COMMON-VARS, DSNTIAC vars, WS-DISP-SQLCODE)
- CSDB2RPY: DB2 common procedures (9998-PRIMING-QUERY, 9999-FORMAT-DB2-MESSAGE using CALL DSNTIAC)

### Known Design Issues
1. COBTUPDT: No COMMIT — DB2 unit-of-work management entirely external
2. COBTUPDT: File open failure non-fatal — processing continues into guaranteed READ failure
3. COTRTUPC: UPDATE fallback to INSERT on +100 — possible duplicate under concurrent inserts
4. DCLTRTYP not available — host variable PIC clauses unverified

---

## VSAM-MQ Service Programs

### Programs
- **COACCT01** (CICS MQ-triggered): Account lookup service. EXEC CICS RETRIEVE gets queue name from CICS MQ trigger message (MQTM-QNAME). Reads ACCTDAT VSAM KSDS via EXEC CICS READ keyed on WS-KEY (11-digit account ID). Only responds to function code 'INQA'. Reply queue: CARD.DEMO.REPLY.ACCT.
- **CODATE01** (CICS MQ-triggered): Date/time service. Identical infrastructure to COACCT01 except: no VSAM access, uses EXEC CICS ASKTIME + FORMATTIME, returns 'SYSTEM DATE : MM-DD-YYYY SYSTEM TIME : HH:MM:SS'. Ignores request content entirely. Reply queue: CARD.DEMO.REPLY.DATE.

### MQ Queue Names
- CARD.DEMO.REPLY.ACCT — reply queue for account lookups
- CARD.DEMO.REPLY.DATE — reply queue for date/time requests
- CARD.DEMO.ERROR — shared error queue (both programs)
- Input queue — obtained dynamically from CICS RETRIEVE (MQTM-QNAME)

### MQ API Sequence (both programs)
MQOPEN(error queue) → CICS RETRIEVE → MQOPEN(input, MQOO-INPUT-SHARED) → MQOPEN(output, MQOO-OUTPUT) → [MQGET(MQGMO-SYNCPOINT+MQGMO-WAIT 5000ms) → process → MQPUT reply → EXEC CICS SYNCPOINT] loop until MQRC-NO-MSG-AVAILABLE → MQCLOSE all → EXEC CICS RETURN

### Request Message Format (COACCT01)
Bytes 1-4: WS-FUNC (must be 'INQA'); Bytes 5-15: WS-KEY (11-digit account ID); Bytes 16-1000: filler

### Known Design Issues
1. Both programs: WS-REPLY-QUEUE-STS flag named 'REPLY-QUEUE-OPEN' but actually tracks the input queue handle — naming defect
2. CODATE01: CICS FORMATTIME not error-checked
3. CODATE01: Request message content completely ignored — cannot distinguish request types
4. Both: QMGR-NAME left as SPACES — relies on CICS-managed MQ connection (implicit)
5. Both: MQ-MSG-COUNT accumulated but never reported

### Spec Files Written
All 7 spec files in /tech_specs/:
- COBTUPDT_spec.md, COTRTLIC_spec.md, COTRTUPC_spec.md
- COTRTLI_bms_spec.md, COTRTUP_bms_spec.md
- COACCT01_spec.md, CODATE01_spec.md

**Why:** User requested detailed technical specification documents for the Transaction Type DB2 and VSAM-MQ subsystems as part of the CardDemo mainframe modernization analysis (2026-04-02).
**How to apply:** These specs cover all 7 requested artifacts. Reference them when asked about transaction type maintenance, MQ service patterns, or VSAM account/date service architecture.
