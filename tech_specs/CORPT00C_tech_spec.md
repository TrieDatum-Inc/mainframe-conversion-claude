# Technical Specification: CORPT00C — Transaction Report Submission

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | CORPT00C |
| Source File | `app/cbl/CORPT00C.cbl` |
| Type | CICS Online |
| Transaction ID | CR00 |
| BMS Mapset | CORPT00 |
| BMS Map | CORPT0A |

## 2. Purpose

CORPT00C allows users to **submit batch transaction report jobs** via CICS TDQ (Transient Data Queue). It supports three report modes: Monthly, Yearly, and Custom date range. The JCL for the report job is pre-built in WORKING-STORAGE and written to the JOBS extra-partition TDQ.

## 3. Copybooks Used

| Copybook | Purpose |
|----------|---------|
| COCOM01Y | CARDDEMO-COMMAREA |
| CORPT00 | BMS symbolic map |
| COTTL01Y, CSDAT01Y, CSMSG01Y | Standard infrastructure |
| CVTRA05Y | Transaction record layout |
| DFHAID, DFHBMSCA | CICS constants |

## 4. Resources Used

| Resource | Type | Operations |
|----------|------|------------|
| JOBS | Extra-Partition TDQ | EXEC CICS WRITEQ TD |

No direct VSAM file access. Report execution is delegated to batch via JCL submission.

## 5. Screen Fields

### Input Fields
| Field | Length | Description |
|-------|--------|-------------|
| MONTHLY | 1 | Select monthly report (cursor initial) |
| YEARLY | 1 | Select yearly report |
| CUSTOM | 1 | Select custom date range |
| SDTMM/SDTDD/SDTYYYY | 2/2/4 | Start date (MM/DD/YYYY) |
| EDTMM/EDTDD/EDTYYYY | 2/2/4 | End date (MM/DD/YYYY) |
| CONFIRM | 1 | Y/N confirmation before submit |

### Function Keys
| Key | Action |
|-----|--------|
| ENTER | Submit report |
| PF3 | Back to COMEN01C |

## 6. Program Flow

```
1. User selects one of three report modes:
   - Monthly: uses current month's start/end dates
   - Yearly: uses Jan 1 to Dec 31 of current year
   - Custom: uses entered start/end dates

2. For Custom mode:
   → CALL CSUTLDTC to validate start date
   → CALL CSUTLDTC to validate end date
   → Validate end date >= start date

3. If CONFIRM = 'Y':
   → SUBMIT-JOB-TO-INTRDR:
     - Loop through JOB-LINES(1..1000) in WORKING-STORAGE
     - Write each 80-byte record to TDQ 'JOBS'
     - Stop at '/*EOF' or spaces/low-values
   → JCL runs procedure TRANREPT from AWS.M2.CARDDEMO.PROC
```

## 7. External Program Calls

| Target | Method | Purpose |
|--------|--------|---------|
| CSUTLDTC | CALL | Date validation for custom date range |

## 8. JCL Submission

The JCL is stored as a literal array (JOB-DATA, lines 81–128 in source) in WORKING-STORAGE. Date parameters are substituted at runtime. The TDQ 'JOBS' feeds an internal reader that submits the batch job.

The batch job invokes the **TRANREPT** cataloged procedure which:
1. Backs up TRANSACT VSAM to GDG
2. Sorts and filters transactions by date range
3. Runs CBTRN03C to produce the formatted report

## 9. Business Rules

1. Monthly report: automatically derives first and last day of current month.
2. Yearly report: Jan 1 to Dec 31 of current year.
3. Custom report: requires valid CSUTLDTC-validated dates.
4. CONFIRM='Y' required before TDQ write.

## 10. Inter-Program Communication

| Target | Method | Condition |
|--------|--------|-----------|
| COMEN01C | XCTL | PF3 |
