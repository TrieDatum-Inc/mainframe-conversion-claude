# Technical Specification: CBACT01C — Account File Extract

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | CBACT01C |
| Source File | `app/cbl/CBACT01C.cbl` |
| Type | Batch COBOL |

## 2. Purpose

CBACT01C reads the ACCTFILE VSAM KSDS sequentially and writes account records to three output files in different formats: a flat extract, an array-format file, and a variable-length record file. Demonstrates COMP, COMP-3, arrays, and VB records.

## 3. Files Accessed

| File DD | Direction | Format | Description |
|---------|-----------|--------|-------------|
| ACCTFILE | Input | KSDS sequential | Account records (CVACT01Y, 300 bytes) |
| OUTFILE | Output | Sequential fixed | Flat extract of account fields |
| ARRYFILE | Output | Sequential fixed | Array format (5 occurrences of balance/debit pairs) |
| VBRCFILE | Output | Sequential variable (RECORDING MODE V) | Two record formats: VB1 (12 bytes) and VB2 (39 bytes) |

## 4. Copybooks Used

| Copybook | Purpose |
|----------|---------|
| CVACT01Y | ACCOUNT-RECORD layout (300 bytes) |
| CODATECN | Date conversion interface for COBDATFT |

## 5. External Calls

| Target | Method | Purpose |
|--------|--------|---------|
| COBDATFT | CALL USING CODATECN-REC | Assembler date format converter (reissue date) |
| CEE3ABD | CALL | LE abend routine |

## 6. Business Logic Notes

- When ACCT-CURR-CYC-DEBIT = 0, substitutes 2525.00 — appears to be a test-data defaulting rule.
- VBRCFILE demonstrates variable-length records: VB1 format (ACCT-ID + status, 12 bytes) and VB2 format (ACCT-ID + balance + credit limit + reissue year, 39 bytes).
