---
name: Billing and Reporting Subsystem
description: COBIL00C (bill payment CB00) and CORPT00C (report submission CR00) - programs, BMS maps, interactions, and design patterns
type: project
---

## COBIL00C — Bill Payment (Transaction CB00)

**Why:** Analyzed and spec'd in tech_specs/COBIL00C_spec.md as part of migration_1 branch work.

- Program: app/cbl/COBIL00C.cbl | BMS: app/bms/COBIL00.bms | Map copybook: app/cpy-bms/COBIL00.CPY
- Files accessed: ACCTDAT (READ UPDATE + REWRITE), CXACAIX (READ via alternate index), TRANSACT (STARTBR/READPREV/ENDBR/WRITE)
- Copybooks: COCOM01Y, CVACT01Y, CVACT03Y, CVTRA05Y, COTTL01Y, CSDAT01Y, CSMSG01Y
- Two-phase pattern: First ENTER shows balance; second ENTER with Y in CONFIRM executes payment
- Transaction ID generation: STARTBR at HIGH-VALUES + READPREV to get last TRAN-ID, then +1
- Payment writes TRAN-TYPE-CD='02', TRAN-CAT-CD=2, full balance as TRAN-AMT, merchant='BILL PAYMENT'
- ACCTDAT balance decremented: ACCT-CURR-BAL = ACCT-CURR-BAL - TRAN-AMT after WRITE succeeds
- Known gap: If TRANSACT file is empty, STARTBR(HIGH-VALUES) returns NOTFND, blocking first ever payment

## CORPT00C — Transaction Report Submission (Transaction CR00)

**Why:** Analyzed and spec'd in tech_specs/CORPT00C_spec.md.

- Program: app/cbl/CORPT00C.cbl | BMS: app/bms/CORPT00.bms | Map copybook: app/cpy-bms/CORPT00.CPY
- No direct file I/O - submits batch job via CICS TDQ 'JOBS' (extra-partition = internal reader)
- Three report types: Monthly (1st to last day current month), Yearly (Jan-1 to Dec-31), Custom (user date range)
- Embedded JCL template in Working-Storage (JOB-DATA-1/2): job TRNRPT00, PROC=TRANREPT, PROC library=AWS.M2.CARDDEMO.PROC
- PROC TRANREPT: [ARTIFACT NOT AVAILABLE FOR INSPECTION]
- CALL 'CSUTLDTC' used twice for custom date validation (start and end dates); format mask='YYYY-MM-DD'; msg '2513' (future date) is accepted
- SEND-TRNRPT-SCREEN always performs GO TO RETURN-TO-CICS - every PERFORM of this paragraph is non-returning
- WS-SEND-ERASE-FLG declared but never set to 'N' - the non-ERASE branch is dead code
- Copybooks: COCOM01Y, CVTRA05Y (unused for I/O), COTTL01Y, CSDAT01Y, CSMSG01Y

## BMS Conventions Confirmed

- All CardDemo online screens follow same header pattern: rows 1-2 with Tran/Prog/Title/Date/Time
- ERRMSG always at row 23, col 1, length 78, COLOR=RED, ATTRB=(ASKIP,BRT,FSET)
- Key legend always at row 24
- DFHGREEN used to color ERRMSG on success (ERRMSGC = DFHGREEN)
- CONFIRM field (1 char, Y/N) appears on both COBIL00 and CORPT00 screens for two-phase confirmation

**How to apply:** When migrating COBIL00C, the critical path is: read account (exclusive lock) -> read XREF AIX -> browse TRANSACT for last ID -> write new transaction -> update account balance. All five operations must be atomic in the target system.
