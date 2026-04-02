---
name: Account Management Subsystem
description: COACTUPC/COACTVWC CICS programs + COACTUP/COACTVW BMS maps for account view and update; VSAM files, copybooks, state machine, optimistic locking
type: project
---

# Account Management Subsystem

Specs written to `tech_specs/` on 2026-04-02:
- `COACTUPC_spec.md` — full account update program
- `COACTVWC_spec.md` — full account view program
- `COACTUP_bms_spec.md` — update screen BMS
- `COACTVW_bms_spec.md` — view screen BMS

## Programs

| Program | Transaction | Map | Mapset | Function |
|---|---|---|---|---|
| COACTUPC | CAUP | CACTUPA | COACTUP | Account + customer update (read/validate/write) |
| COACTVWC | CAVW | CACTVWA | COACTVW | Account + customer view (read-only) |

## VSAM Files

| Logical Name | Key | Access in COACTUPC | Access in COACTVWC |
|---|---|---|---|
| ACCTDAT | ACCT-ID 9(11) | READ + READ UPDATE + REWRITE | READ |
| CUSTDAT | CUST-ID 9(09) | READ + READ UPDATE + REWRITE | READ |
| CXACAIX | XREF-ACCT-ID 9(11) | READ (alternate index) | READ (alternate index) |

## Copybooks (shared with card management)

| Copybook | Record | Record Length |
|---|---|---|
| CVACT01Y | ACCOUNT-RECORD | 300 bytes |
| CVCUS01Y | CUSTOMER-RECORD | 500 bytes |
| CVACT03Y | CARD-XREF-RECORD | 50 bytes |
| COCOM01Y | CARDDEMO-COMMAREA | ~140 bytes |

## COACTUPC State Machine (ACUP-CHANGE-ACTION)

| Value | 88-Level | Meaning |
|---|---|---|
| LOW-VALUES/SPACES | ACUP-DETAILS-NOT-FETCHED | Initial; show blank search screen |
| 'S' | ACUP-SHOW-DETAILS | Data fetched; show for editing |
| 'E' | ACUP-CHANGES-NOT-OK | Validation failed; show errors |
| 'N' | ACUP-CHANGES-OK-NOT-CONFIRMED | Valid; awaiting F5 confirm |
| 'C' | ACUP-CHANGES-OKAYED-AND-DONE | Saved OK |
| 'L' | ACUP-CHANGES-OKAYED-LOCK-ERROR | Lock failed |
| 'F' | ACUP-CHANGES-OKAYED-BUT-FAILED | REWRITE failed |

## COACTUPC Write Atomicity

- READ UPDATE on ACCTDAT, then READ UPDATE on CUSTDAT (lock both)
- 9700-CHECK-CHANGE-IN-REC: optimistic concurrency check (compare all fields vs. snapshot)
- REWRITE ACCTDAT, then REWRITE CUSTDAT
- If customer REWRITE fails: EXEC CICS SYNCPOINT ROLLBACK (COACTUPC line 4100)
- No SYNCPOINT ROLLBACK if account REWRITE fails (gap — account lock is not explicitly unlocked)

## Key Behavioral Differences: COACTVWC vs. COACTUPC

- COACTVWC has NO SYNCPOINT before F3 XCTL; COACTUPC does (line 953)
- COACTVW uses BMS PICOUT=+ZZZ,ZZZ,ZZZ.99 for currency (no COBOL formatting needed)
- COACTVW uses single date fields (ADTOPEN 10-char); COACTUP uses three split fields (OPNYEAR/MON/DAY)
- COACTVW uses single phone fields (ACSPHN1 13-char); COACTUP uses three split fields
- COACTVW has VALIDN=MUSTFILL + PICIN='99999999999' on ACCTSID (terminal-level enforcement)
- COACTUPC uses CSSETATY.CPY (via COPY REPLACING) to set field color to DFHRED for ~35 validated fields
- COACTUPC Country field (ACSCTRY) is protected during editing — no country validation implemented
- COACTUPC Customer ID (ACSTNUM) is display-only even in edit mode
- COACTUPC Address Line 2 has no validation ("NO EDITS CODED AS YET")

## Navigation Context

- Both programs called from COMEN01C (CM00) main menu via XCTL
- F3 returns to CDEMO-FROM-PROGRAM (or COMEN01C by default)
- COACTUPC can be reached from COCRDLIC (CCLI) card list context
- COACTUPC literal references: LIT-CARDUPDATE-PGM=COCRDUPC, LIT-CCLISTPGM=COCRDLIC
- COACTVWC literal references: LIT-CARDUPDATEPGM=COCRDUPC, LIT-CCLISTPGM=COCRDLIC, LIT-CARDDTLPGM=COCRDSLC

## Composite COMMAREA Pattern

Both programs use the same pattern:
- WS-COMMAREA PIC X(2000)
- First segment: CARDDEMO-COMMAREA (from COCOM01Y) — ~140 bytes
- Second segment: WS-THIS-PROGCOMMAREA (program-specific state) — variable
- COACTUPC private state: ~800+ bytes (ACUP-OLD-DETAILS + ACUP-NEW-DETAILS)
- COACTVWC private state: 12 bytes (CA-FROM-PROGRAM + CA-FROM-TRANID only)

**Why:** COACTUPC must carry the full old+new data snapshot across pseudo-conversational returns to support change detection and optimistic locking. COACTVWC is stateless between returns (re-reads on every ENTER).
