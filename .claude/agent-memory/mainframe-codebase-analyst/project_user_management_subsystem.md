---
name: User Management Subsystem — COUSR Programs
description: Architecture, data flows, defects, and key design patterns for the four COUSR online programs and their BMS maps (user list, add, update, delete)
type: project
---

## Programs and Transactions

| Program  | Transaction | Function        | Map    | Mapset  |
|----------|-------------|-----------------|--------|---------|
| COUSR00C | CU00        | List users      | COUSR0A| COUSR00 |
| COUSR01C | CU01        | Add user        | COUSR1A| COUSR01 |
| COUSR02C | CU02        | Update user     | COUSR2A| COUSR02 |
| COUSR03C | CU03        | Delete user     | COUSR3A| COUSR03 |

## VSAM File: USRSEC

Record layout (CSUSR01Y.cpy, 80 bytes total):
- SEC-USR-ID    X(08) — KSDS key
- SEC-USR-FNAME X(20)
- SEC-USR-LNAME X(20)
- SEC-USR-PWD   X(08) — plaintext, not encrypted
- SEC-USR-TYPE  X(01) — A=Admin, U=User
- SEC-USR-FILLER X(23)

## COMMAREA Extension Pattern

Each of COUSR00C, COUSR02C, COUSR03C defines an inline COMMAREA extension after COPY COCOM01Y:
- CDEMO-CU0x-INFO (x = 0, 2, 3) at the same physical byte positions
- Contains USRID-FIRST, USRID-LAST, PAGE-NUM, NEXT-PAGE-FLG, USR-SEL-FLG, USR-SELECTED
- COUSR00C populates USR-SELECTED before XCTL to COUSR02C or COUSR03C

## Navigation Flow

COADM01C → (CU00) → COUSR00C → [U] → COUSR02C → COADM01C or COUSR00C
                              → [D] → COUSR03C → COADM01C or COUSR00C
COADM01C → (CU01) → COUSR01C (add, standalone)

## BMS Screen Design Patterns

- All 4 mapsets use CTRL=(ALARM,FREEKB), EXTATT=YES, TIOAPFX=YES
- Header rows 1-2: Tran/Prog labels + TITLE01/TITLE02 (COTTL01Y) + Date/Time (CSDAT01Y)
- Row 23: ERRMSG (COLOR=RED, ASKIP,BRT,FSET)
- Row 24: Function key legend (COLOR=YELLOW)
- COUSR02 and COUSR03 include 70-asterisk visual separator at Row 8 (COLOR=YELLOW)
- COUSR02 data fields are GREEN + UNPROT (editable)
- COUSR03 data fields are BLUE + ASKIP (read-only — delete confirmation only)

## Known Defects / Design Issues

1. COUSR00C STARTBR has GTEQ commented out (line 592) — exact-match positioning only; may skip records when search term doesn't match exactly.
2. COUSR00C ENDBR has no RESP checking (lines 687-691).
3. COUSR01C WS-USER-DATA (lines 56-64) is dead code — never referenced in PROCEDURE DIVISION.
4. COUSR01C does not handle PF12 despite 'F12=Exit' appearing on Row 24 of the screen.
5. COUSR02C and COUSR03C: READ-USER-SEC-FILE issues SEND MAP internally on NORMAL response — causes double screen send when PF5/PF3 save path calls this paragraph.
6. COUSR03C DELETE-USER-SEC-FILE OTHER error message reads 'Unable to Update User...' (should be Delete) — copy-paste defect from COUSR02C.
7. COUSR03C: WS-USR-MODIFIED defined but never SET (dead code).
8. COUSR03C: DELETE-USER-INFO calls READ then DELETE without re-checking ERR-FLG-ON between them; if READ fails, DELETE is still attempted with no UPDATE lock.
9. Password stored and transmitted in plaintext across all programs.
10. User Type field (A/U) not range-validated in COUSR01C or COUSR02C — any non-blank single character is accepted.

## Copybooks Used by All Four Programs

- COCOM01Y (COMMAREA), CSUSR01Y (USRSEC record), COTTL01Y (titles), CSDAT01Y (date/time), CSMSG01Y (messages), DFHAID, DFHBMSCA
- BMS-generated copybooks: COUSR00.CPY, COUSR01.CPY, COUSR02.CPY, COUSR03.CPY (in app/cpy-bms/)

## Specs Written

All 8 spec files are in tech_specs/:
- COUSR00C_spec.md, COUSR01C_spec.md, COUSR02C_spec.md, COUSR03C_spec.md
- COUSR00_bms_spec.md, COUSR01_bms_spec.md, COUSR02_bms_spec.md, COUSR03_bms_spec.md

**Why:** User management subsystem fully analyzed as part of CardDemo mainframe-to-modern migration at Triedatum Inc.
**How to apply:** Reference these specs when designing replacement REST API or UI for user CRUD operations. Pay attention to the 10 known defects listed above when deciding whether to replicate or fix legacy behavior.
