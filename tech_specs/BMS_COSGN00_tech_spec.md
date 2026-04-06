# Technical Specification: BMS Screen — COSGN00 (Login)

## 1. Screen Overview

| Attribute | Value |
|-----------|-------|
| Mapset | COSGN00 |
| Map | COSGN0A |
| Source File | `app/bms/COSGN00.bms` |
| Copybook | `app/cpy-bms/COSGN00.CPY` |
| COBOL Program | COSGN00C |
| Domain | Authentication |

## 2. Purpose

Entry point screen for the CardDemo application. Collects User ID and Password for authentication. Features a decorative ASCII art dollar bill and promotional text.

## 3. Screen Layout (24 rows x 80 columns)

```
Row 1:  Tran: XXXX  |  AWS Mainframe Modernization      | Date: mm/dd/yy
Row 2:  Prog: XXXXXXXX | CardDemo                        | Time: hh:mm:ss
Row 3:  AppID: XXXXXXXX                                    SysID: XXXXXXXX
Row 5:  "This is a Credit Card Demo Application for Mainframe Modernization"
Row 7-15: [Dollar bill ASCII art - decorative]
Row 17: "Type your User ID and Password, then press ENTER:"
Row 19:                 User ID     : [________] (8 Char)
Row 20:                 Password    : [________] (8 Char) -- non-display
Row 23: [Error message - RED, 78 chars]
Row 24: ENTER=Sign-on  F3=Exit
```

## 4. Field Definitions

### Input Fields
| Field | Row,Col | Length | Attributes | Description |
|-------|---------|--------|------------|-------------|
| USERID | 19,43 | 8 | FSET,IC,NORM,UNPROT,GREEN | User ID — cursor initial |
| PASSWD | 20,43 | 8 | DRK,FSET,UNPROT,GREEN | Password — non-display |

### Output Fields
| Field | Row,Col | Length | Attributes | Description |
|-------|---------|--------|------------|-------------|
| TRNNAME | 1,8 | 4 | ASKIP,FSET,NORM,BLUE | Transaction name |
| TITLE01 | 1,21 | 40 | ASKIP,FSET,NORM,YELLOW | Title line 1 |
| CURDATE | 1,71 | 8 | ASKIP,FSET,NORM,BLUE | Current date (mm/dd/yy) |
| PGMNAME | 2,8 | 8 | FSET,NORM,PROT,BLUE | Program name |
| TITLE02 | 2,21 | 40 | ASKIP,FSET,NORM,YELLOW | Title line 2 |
| CURTIME | 2,71 | 9 | FSET,NORM,PROT,BLUE | Current time |
| APPLID | 3,8 | 8 | FSET,NORM,PROT,BLUE | CICS APPLID |
| SYSID | 3,71 | 8 | FSET,NORM,PROT,BLUE | CICS SysID |
| ERRMSG | 23,1 | 78 | ASKIP,BRT,FSET,RED | Error message |

## 5. Function Keys

| Key | Action |
|-----|--------|
| ENTER | Sign-on (authenticate) |
| F3 | Exit application |

## 6. BMS Technical Details

- CTRL=(ALARM,FREEKB)
- EXTATT=YES
- Standard 2-row header extended to 3 rows (row 3 adds APPLID and SYSID)

## 7. Symbolic Map Structures

- Input: `COSGN0AI` — USERIDL/USERIDF/USERIDA/USERIDI, PASSWDL/PASSWDF/PASSWDA/PASSWDI
- Output: `COSGN0AO` — USERIDC/USERIDP/USERIDH/USERIDO, etc.
