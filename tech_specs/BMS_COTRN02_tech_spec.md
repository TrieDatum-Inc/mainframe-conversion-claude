# Technical Specification: BMS Screen — COTRN02 (Add Transaction)

## 1. Screen Overview

| Attribute | Value |
|-----------|-------|
| Mapset | COTRN02 |
| Map | COTRN2A |
| Source File | `app/bms/COTRN02.bms` |
| Copybook | `app/cpy-bms/COTRN02.CPY` |
| COBOL Program | COTRN02C |
| Domain | Transactions |

## 2. Purpose

Data entry form for creating a new transaction record. All fields are UNPROT (editable). Requires Y/N confirmation before committing.

## 3. Screen Layout

```
Row 1-2:  [Standard header]
Row 4:    "Add Transaction" (centered)
Row 6:    "Enter Acct #:" [___________]   "Card #:" [________________]
Row 10:   Type: [__]  Category: [____]  Source: [__________]
Row 12:   Description: [____________________________________________________________]
Row 14:   Amount: [____________]  Orig Date: [__________]  Proc Date: [__________]
Row 15:   (-99999999.99)         (YYYY-MM-DD)              (YYYY-MM-DD)
Row 16:   Merchant ID: [_________]  Name: [______________________________]
Row 18:   City: [_________________________]  Zip: [__________]
Row 21:   "You are about to add this transaction. Please confirm:" [_] (Y/N)
Row 23:   [Error message]
Row 24:   ENTER=Continue  F3=Back  F4=Clear  F5=Copy Last Tran.
```

## 4. Input Fields

ACTIDIN(11), CARDNIN(16), TTYPCD(2), TCATCD(4), TRNSRC(10), TDESC(60), TRNAMT(12), TORIGDT(10), TPROCDT(10), MID(9), MNAME(30), MCITY(25), MZIP(10), CONFIRM(1)

## 5. Function Keys

| Key | Action |
|-----|--------|
| ENTER | Submit (if CONFIRM=Y) |
| F3 | Back |
| F4 | Clear all fields |
| F5 | Copy last transaction into fields |
