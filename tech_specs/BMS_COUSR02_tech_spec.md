# Technical Specification: BMS Screen — COUSR02 (Update User)

## 1. Screen Overview

| Attribute | Value |
|-----------|-------|
| Mapset | COUSR02 |
| Map | COUSR2A |
| Source File | `app/bms/COUSR02.bms` |
| Copybook | `app/cpy-bms/COUSR02.CPY` |
| COBOL Program | COUSR02C |
| Domain | User Administration |

## 2. Screen Layout

```
Row 1-2:  [Standard header]
Row 4:    "Update User"
Row 6:    "Enter User ID:" [________]
Row 8:    [Separator]
Row 11:   First Name: [____________________]  Last Name: [____________________]
Row 13:   Password: [________] (non-display)
Row 15:   User Type: [_]
Row 23:   [Error message]
Row 24:   ENTER=Fetch  F3=Save&&Exit  F4=Clear  F5=Save  F12=Cancel
```

## 3. Two-Phase Operation

Phase 1: ENTER fetches user by USRIDIN, populates editable fields.
Phase 2: F5 saves changes, F3 saves and exits.

## 4. Function Keys

ENTER=Fetch, F3=Save&Exit, F4=Clear, F5=Save, F12=Cancel
