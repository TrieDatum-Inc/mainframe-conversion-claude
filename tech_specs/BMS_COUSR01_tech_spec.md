# Technical Specification: BMS Screen — COUSR01 (Add User)

## 1. Screen Overview

| Attribute | Value |
|-----------|-------|
| Mapset | COUSR01 |
| Map | COUSR1A |
| Source File | `app/bms/COUSR01.bms` |
| Copybook | `app/cpy-bms/COUSR01.CPY` |
| COBOL Program | COUSR01C |
| Domain | User Administration |

## 2. Screen Layout

```
Row 1-2:  [Standard header]
Row 4:    "Add User"
Row 8:    First Name: [____________________]  Last Name: [____________________]
Row 11:   User ID: [________] (8 Char)  Password: [________] (8 Char, non-display)
Row 14:   User Type: [_] (A=Admin, U=User)
Row 23:   [Error message]
Row 24:   ENTER=Add User  F3=Back  F4=Clear  F12=Exit
```

## 3. Fields

### Input
FNAME(20, cursor initial), LNAME(20), USERID(8), PASSWD(8, DRK), USRTYPE(1)

## 4. Function Keys

ENTER=Add user, F3=Back, F4=Clear, F12=Exit
