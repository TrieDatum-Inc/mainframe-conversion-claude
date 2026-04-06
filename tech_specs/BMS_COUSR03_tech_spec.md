# Technical Specification: BMS Screen — COUSR03 (Delete User)

## 1. Screen Overview

| Attribute | Value |
|-----------|-------|
| Mapset | COUSR03 |
| Map | COUSR3A |
| Source File | `app/bms/COUSR03.bms` |
| Copybook | `app/cpy-bms/COUSR03.CPY` |
| COBOL Program | COUSR03C |
| Domain | User Administration |

## 2. Screen Layout

```
Row 1-2:  [Standard header]
Row 4:    "Delete User"
Row 6:    "Enter User ID:" [________]
Row 11:   First Name: XXXXXXXXXXXXXXXXXXXX (read-only, BLUE)
Row 13:   Last Name:  XXXXXXXXXXXXXXXXXXXX (read-only)
Row 15:   User Type:  X (read-only)
Row 23:   [Error message]
Row 24:   ENTER=Fetch  F3=Back  F4=Clear  F5=Delete
```

## 3. Key Difference from COUSR02

FNAME, LNAME, USRTYPE are **ASKIP/FSET/NORM** (output-only, not editable) — user can only confirm deletion.

## 4. Two-Phase Operation

Phase 1: ENTER fetches user record (display only).
Phase 2: F5 confirms deletion.

## 5. Function Keys

ENTER=Fetch, F3=Back, F4=Clear, F5=Delete
