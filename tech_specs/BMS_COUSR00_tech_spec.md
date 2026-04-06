# Technical Specification: BMS Screen — COUSR00 (List Users)

## 1. Screen Overview

| Attribute | Value |
|-----------|-------|
| Mapset | COUSR00 |
| Map | COUSR0A |
| Source File | `app/bms/COUSR00.bms` |
| Copybook | `app/cpy-bms/COUSR00.CPY` |
| COBOL Program | COUSR00C |
| Domain | User Administration |

## 2. Screen Layout

```
Row 1-2:  [Standard header]      PAGENUM at row 4,71
Row 6:    "Search User ID:" [________]
Row 8:    Column headers: Sel | User ID | First Name | Last Name | Type
Row 10-19: [10 data rows]
Row 21:   "Type 'U' to Update or 'D' to Delete a User from the list"
Row 23:   [Error message]
Row 24:   ENTER=Continue  F3=Back  F7=Backward  F8=Forward
```

## 3. Fields

### Input
USRIDIN(8), SEL0001–SEL0010(1 each, 'U'=update, 'D'=delete)

### Output (10 rows)
USRID01–USRID10(8), FNAME01–FNAME10(20), LNAME01–LNAME10(20), UTYPE01–UTYPE10(1)

## 4. Function Keys

ENTER=Process, F3=Back, F7=Page backward, F8=Page forward

## 5. Navigation

'U' → COUSR02 (Update User), 'D' → COUSR03 (Delete User)
