# Technical Specification: CBACT02C — Card File Dump

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | CBACT02C |
| Source File | `app/cbl/CBACT02C.cbl` |
| Type | Batch COBOL (Diagnostic/Utility) |

## 2. Purpose

Reads CARDFILE VSAM KSDS sequentially and DISPLAYs each card record to SYSOUT. Diagnostic/verification utility.

## 3. Files Accessed

| File DD | Direction | Key | Record Layout |
|---------|-----------|-----|---------------|
| CARDFILE | Input (KSDS sequential) | FD-CARD-NUM X(16) | CVACT02Y (150 bytes) |

## 4. Record Layout (CVACT02Y)

| Field | PIC | Description |
|-------|-----|-------------|
| CARD-NUM | X(16) | Card number (primary key) |
| CARD-ACCT-ID | 9(11) | Account ID |
| CARD-CVV-CD | 9(3) | CVV code |
| CARD-EMBOSSED-NAME | X(50) | Name on card |
| CARD-EXPIRAION-DATE | X(10) | Expiration date |
| CARD-ACTIVE-STATUS | X(1) | Active status |
| FILLER | X(59) | Reserved |
