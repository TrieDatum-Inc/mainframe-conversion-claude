# Technical Specification: CBACT03C — Card Xref File Dump

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | CBACT03C |
| Source File | `app/cbl/CBACT03C.cbl` |
| Type | Batch COBOL (Diagnostic/Utility) |

## 2. Purpose

Reads XREFFILE (card-to-account cross-reference) VSAM KSDS sequentially and DISPLAYs each record to SYSOUT. Diagnostic utility.

## 3. Files Accessed

| File DD | Direction | Key | Record Layout |
|---------|-----------|-----|---------------|
| XREFFILE | Input (KSDS sequential) | FD-XREF-CARD-NUM X(16) | CVACT03Y (50 bytes) |

## 4. Record Layout (CVACT03Y)

| Field | PIC | Description |
|-------|-----|-------------|
| XREF-CARD-NUM | X(16) | Card number (primary key) |
| XREF-CUST-ID | 9(9) | Customer ID |
| XREF-ACCT-ID | 9(11) | Account ID |
| FILLER | X(14) | Reserved |
