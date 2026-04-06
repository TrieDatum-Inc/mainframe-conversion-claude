# Technical Specification: CBCUS01C — Customer File Dump

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | CBCUS01C |
| Source File | `app/cbl/CBCUS01C.cbl` |
| Type | Batch COBOL (Diagnostic/Utility) |

## 2. Purpose

Reads CUSTFILE VSAM KSDS sequentially and DISPLAYs each customer record to SYSOUT. Diagnostic utility.

## 3. Files Accessed

| File DD | Direction | Key | Record Layout |
|---------|-----------|-----|---------------|
| CUSTFILE | Input (KSDS sequential) | FD-CUST-ID 9(9) | CVCUS01Y (500 bytes) |

## 4. Record Layout (CVCUS01Y)

| Field | PIC | Description |
|-------|-----|-------------|
| CUST-ID | 9(9) | Customer ID (primary key) |
| CUST-FIRST-NAME | X(25) | First name |
| CUST-MIDDLE-NAME | X(25) | Middle name |
| CUST-LAST-NAME | X(25) | Last name |
| CUST-ADDR-LINE-1/2/3 | X(50) each | Address lines |
| CUST-ADDR-STATE-CD | X(2) | State |
| CUST-ADDR-COUNTRY-CD | X(3) | Country |
| CUST-ADDR-ZIP | X(10) | Zip code |
| CUST-PHONE-NUM-1/2 | X(15) each | Phone numbers |
| CUST-SSN | 9(9) | Social Security Number |
| CUST-GOVT-ISSUED-ID | X(20) | Government ID |
| CUST-DOB-YYYY-MM-DD | X(10) | Date of birth |
| CUST-EFT-ACCOUNT-ID | X(10) | EFT account |
| CUST-PRI-CARD-HOLDER-IND | X(1) | Primary holder flag |
| CUST-FICO-CREDIT-SCORE | 9(3) | FICO score |
| FILLER | X(168) | Reserved |
