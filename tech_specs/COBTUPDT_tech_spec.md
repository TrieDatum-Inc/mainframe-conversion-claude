# Technical Specification: COBTUPDT — Batch Transaction Type Maintenance

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | COBTUPDT |
| Source File | `app/app-transaction-type-db2/cbl/COBTUPDT.cbl` |
| Type | Batch COBOL (DB2) |
| JCL | MNTTRDB2.jcl |

## 2. Purpose

COBTUPDT reads a sequential input file and performs **bulk INSERT, UPDATE, or DELETE operations** on the DB2 CARDDEMO.TRANSACTION_TYPE table. Used for batch reference data maintenance.

## 3. Input File Layout

| Field | PIC | Description |
|-------|-----|-------------|
| INPUT-REC-TYPE | X(1) | 'A'=Add, 'U'=Update, 'D'=Delete, '*'=Comment |
| INPUT-REC-NUMBER | X(2) | Transaction type code |
| INPUT-REC-DESC | X(50) | Description |

## 4. DB2 Operations

| Action | SQL |
|--------|-----|
| 'A' | INSERT INTO TRANSACTION_TYPE |
| 'U' | UPDATE TRANSACTION_TYPE SET TR_DESCRIPTION WHERE TR_TYPE |
| 'D' | DELETE FROM TRANSACTION_TYPE WHERE TR_TYPE |
| '*' | Skip (comment record) |

## 5. JCL (MNTTRDB2.jcl)

Runs under TSO/IKJEFT01 with DSN command processor:
```
DSN SYSTEM(DAZ1)
RUN PROGRAM(COBTUPDT) PLAN(CARDDEMO)
```
DBRMLIB = AWS.M2.CARDDEMO.DBRMLIB
