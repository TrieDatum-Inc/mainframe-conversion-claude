# Technical Specification: CBSTM03B — Statement File I/O Subroutine

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | CBSTM03B |
| Source File | `app/cbl/CBSTM03B.CBL` |
| Type | Batch COBOL (Called Subroutine) |

## 2. Purpose

CBSTM03B is a **file I/O dispatcher** called by CBSTM03A. It provides a single CALL entry point for all file operations, with the operation type specified via a code in the linkage area.

## 3. LINKAGE Section

| Field | PIC | Description |
|-------|-----|-------------|
| LK-M03B-DD | X(8) | File DD name |
| LK-M03B-OPER | X(1) | Operation: O/C/R/K/W/Z |
| LK-M03B-RC | X(2) | Return code |
| LK-M03B-KEY | X(25) | Record key |
| LK-M03B-KEY-LN | S9(4) | Key length |
| LK-M03B-FLDT | X(1000) | Record data area |

## 4. Files Managed

| File DD | Type | Key | Layout |
|---------|------|-----|--------|
| TRNXFILE | KSDS sequential | FD-TRNXS-ID = card-num(16) + tran-id(16) = 32 bytes | COSTM01 (350 bytes) |
| XREFFILE | KSDS sequential | FD-XREF-CARD-NUM X(16) | CVACT03Y (50 bytes) |
| CUSTFILE | KSDS random | FD-CUST-ID 9(9) | CVCUS01Y (500 bytes) |
| ACCTFILE | KSDS random | FD-ACCT-ID 9(11) | CVACT01Y (300 bytes) |

## 5. Operation Codes

| Code | Operation |
|------|-----------|
| O | OPEN file |
| C | CLOSE file |
| R | READ NEXT (sequential) |
| K | READ by key (random) |
| W | WRITE record |
| Z | REWRITE record |
