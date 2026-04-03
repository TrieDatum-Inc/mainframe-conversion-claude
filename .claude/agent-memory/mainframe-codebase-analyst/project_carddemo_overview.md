---
name: CardDemo Project Overview
description: Overview of the CardDemo mainframe application being analyzed for modernization — structure, key programs, transaction IDs, and codebase layout
type: project
---

The project is analyzing the CardDemo application, an AWS Mainframe Modernization demo CICS/COBOL application.

**Why:** The goal is to produce technical specifications to support a mainframe-to-modern conversion project.

**How to apply:** All analysis should be grounded in the source artifacts in /home/mridul/projects/triedatum-inc/one/mainframe-conversion-claude/app/. Tech specs go to /home/mridul/projects/triedatum-inc/one/mainframe-conversion-claude/tech_specs/.

## Codebase Layout

- app/cbl/ — COBOL source programs
- app/bms/ — BMS mapset source files
- app/cpy/ — Application copybooks
- app/cpy-bms/ — BMS-generated symbolic map copybooks
- app/jcl/ — JCL jobs
- app/cpy (others) — VSAM, DB2, IMS variants in subdirectories

## Entry-Point Transaction Flow

```
CC00 -> COSGN00C (Signon)
  -> if Admin (type='A') -> CA00/COADM01C (Admin Menu)
  -> if User  (type='U') -> CM00/COMEN01C (Main Menu)
```

## Key Programs Analyzed

| Program   | TransID | Function                  | Spec File |
|-----------|---------|---------------------------|-----------|
| COSGN00C  | CC00    | Signon/Login              | tech_specs/COSGN00C_spec.md |
| COMEN01C  | CM00    | Main Menu (users)         | tech_specs/COMEN01C_spec.md |
| COADM01C  | CA00    | Admin Menu (admins)       | tech_specs/COADM01C_spec.md |
| CORPT00C  | CR00    | Transaction Report Submit | tech_specs/CORPT00C_spec.md |
| COBIL00C  | CB00    | Online Bill Payment       | tech_specs/COBIL00C_spec.md |
| CBEXPORT  | batch   | Branch Migration Export   | tech_specs/CBEXPORT_spec.md |
| CBIMPORT  | batch   | Branch Migration Import   | tech_specs/CBIMPORT_spec.md |
| CBCUS01C  | batch   | Customer File Print       | tech_specs/CBCUS01C_spec.md |
| CSUTLDTC  | utility | Date Validation Subpgm    | tech_specs/CSUTLDTC_spec.md |
| COBSWAIT  | utility | Batch Wait/Sleep Utility  | tech_specs/COBSWAIT_spec.md |

## Shared Infrastructure Copybooks

- COCOM01Y.cpy — CARDDEMO-COMMAREA (shared across ALL programs)
- COTTL01Y.cpy — CCDA-SCREEN-TITLE (title constants)
- CSDAT01Y.cpy — WS-DATE-TIME (date/time working storage)
- CSMSG01Y.cpy — CCDA-COMMON-MESSAGES (standard messages)
- CSUSR01Y.cpy — SEC-USER-DATA (USRSEC VSAM record layout, 80 bytes)
- DFHAID / DFHBMSCA — CICS system copybooks

## VSAM File: USRSEC
- Key: 8-byte user ID (SEC-USR-ID)
- Record: SEC-USER-DATA (80 bytes) — ID, first/last name, password, type ('A'/'U'), filler
- Only written/read in COSGN00C (read-only) and COUSR* admin programs

## Naming Conventions
- Programs: CO<subsystem><seq>C.cbl (C = CICS COBOL)
- Mapsets: CO<subsystem><seq>.bms
- Copybooks (app data): C<category><seq>Y.cpy
- BMS symbolic maps: CO<subsystem><seq>.CPY (uppercase, in cpy-bms/)
- Transaction IDs: 2-char app prefix + 2-digit seq (CC00, CM00, CA00, etc.)
