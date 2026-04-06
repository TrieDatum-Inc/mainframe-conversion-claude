# Technical Specification: CBTRN03C — Transaction Detail Report

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | CBTRN03C |
| Source File | `app/cbl/CBTRN03C.cbl` |
| Type | Batch COBOL |
| JCL | TRANREPT procedure, STEP10R |

## 2. Purpose

CBTRN03C reads a sorted/filtered transaction file, joins with reference files for descriptions, filters by date range, and produces a **formatted 133-column transaction detail report**.

## 3. Files Accessed

| File DD | Direction | Access | Key | Layout |
|---------|-----------|--------|-----|--------|
| TRANFILE | Input | Sequential | — | CVTRA05Y (350 bytes) |
| CARDXREF | Input | KSDS random | XREF-CARD-NUM | CVACT03Y (50 bytes) |
| TRANTYPE | Input | KSDS random | FD-TRAN-TYPE X(2) | CVTRA03Y (60 bytes) |
| TRANCATG | Input | KSDS random | TYPE-CD(2)+CAT-CD(4) | CVTRA04Y (60 bytes) |
| TRANREPT | Output | Sequential | — | 133-byte report lines |
| DATEPARM | Input | Sequential | — | 80-byte date parameters |

## 4. Date Parameters (DATEPARM)

Single record: `WS-START-DATE(10) + SPACE + WS-END-DATE(10)` in YYYY-MM-DD format.
Transactions are filtered by TRAN-PROC-TS against this date range.

## 5. Report Layout (CVTRA07Y)

- 133-byte print lines (LRECL=133, RECFM=FB)
- Report name: DALYREPT
- Columns: TRAN-ID, ACCT-ID, TYPE-CD/DESC, CAT-CD/DESC, SOURCE, AMOUNT
- Amount format: `-ZZZ,ZZZ,ZZZ.ZZ`
- Page size: 20 lines per page
- Control breaks on card number change
- Accumulates: page total, account total, grand total

## 6. Dependencies

TRANTYPE.VSAM.KSDS and TRANCATG.VSAM.KSDS must be current — refreshed daily by TRANEXTR JCL from DB2.

## 7. Copybooks Used

CVTRA05Y, CVACT03Y, CVTRA03Y, CVTRA04Y, CVTRA07Y
