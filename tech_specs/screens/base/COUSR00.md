# COUSR00 — User List Screen Technical Specification

## 1. Screen Overview

**Purpose:** Displays a paginated list of system users for administrative management. Up to 10 user records are shown per page. The operator can search by User ID, scroll forward/backward, and select a user for update (`U`) or delete (`D`) operations. This screen is an admin-only function.

**Driving Program:** COUSR00C (User List program)

**Source File:** `/app/bms/COUSR00.bms`
**Copybook:** `/app/cpy-bms/COUSR00.CPY`

---

## 2. Map/Mapset Definition

| Attribute    | Value             |
|--------------|-------------------|
| MAPSET name  | COUSR00           |
| MAP name     | COUSR0A           |
| SIZE         | (24, 80)          |
| COLUMN       | 1                 |
| LINE         | 1                 |
| CTRL         | ALARM, FREEKB     |
| EXTATT       | YES               |
| LANG         | COBOL             |
| MODE         | INOUT             |
| STORAGE      | AUTO              |
| TIOAPFX      | YES               |
| TYPE         | &&SYSPARM         |

---

## 3. Screen Layout (ASCII Representation)

```
Col:  1         2         3         4         5         6         7         8
      12345678901234567890123456789012345678901234567890123456789012345678901234567890
Row1: Tran:[TRNM]          [----------TITLE01----------]     Date:[CURDATE-]
Row2: Prog:[PGMNAME]       [----------TITLE02----------]     Time:[CURTIME-]
Row3:
Row4:                                    List Users              Page:[PAGENUM-]
Row5:
Row6:     Search User ID:[USRIDIN-]
Row7:
Row8:      Sel  User ID      First Name             Last Name             Type
Row9:      ---  --------  --------------------  --------------------  ----
Row10:     [S1] [USRID01-] [FNAME01------------] [LNAME01------------] [T1]
Row11:     [S2] [USRID02-] [FNAME02------------] [LNAME02------------] [T2]
Row12:     [S3] [USRID03-] [FNAME03------------] [LNAME03------------] [T3]
Row13:     [S4] [USRID04-] [FNAME04------------] [LNAME04------------] [T4]
Row14:     [S5] [USRID05-] [FNAME05------------] [LNAME05------------] [T5]
Row15:     [S6] [USRID06-] [FNAME06------------] [LNAME06------------] [T6]
Row16:     [S7] [USRID07-] [FNAME07------------] [LNAME07------------] [T7]
Row17:     [S8] [USRID08-] [FNAME08------------] [LNAME08------------] [T8]
Row18:     [S9] [USRID09-] [FNAME09------------] [LNAME09------------] [T9]
Row19:     [S0] [USRID10-] [FNAME10------------] [LNAME10------------] [T10]
Row20:
Row21:           Type 'U' to Update or 'D' to Delete a User from the list
Row22:
Row23: [---------------------------ERRMSG------------------------------------]
Row24: ENTER=Continue  F3=Back  F7=Backward  F8=Forward
```

---

## 4. Field Definitions

### Header Fields (rows 1–2)

| Field Name | Row | Col | Length | ATTRB           | Color  | I/O | Notes                        |
|------------|-----|-----|--------|-----------------|--------|-----|------------------------------|
| (label)    | 1   | 1   | 5      | ASKIP,NORM      | BLUE   | O   | `Tran:`                      |
| TRNNAME    | 1   | 7   | 4      | ASKIP,FSET,NORM | BLUE   | O   | Transaction name              |
| TITLE01    | 1   | 21  | 40     | ASKIP,FSET,NORM | YELLOW | O   | Title line 1                  |
| (label)    | 1   | 65  | 5      | ASKIP,NORM      | BLUE   | O   | `Date:`                       |
| CURDATE    | 1   | 71  | 8      | ASKIP,FSET,NORM | BLUE   | O   | Current date                  |
| (label)    | 2   | 1   | 5      | ASKIP,NORM      | BLUE   | O   | `Prog:`                       |
| PGMNAME    | 2   | 7   | 8      | ASKIP,FSET,NORM | BLUE   | O   | Program name                  |
| TITLE02    | 2   | 21  | 40     | ASKIP,FSET,NORM | YELLOW | O   | Title line 2                  |
| (label)    | 2   | 65  | 5      | ASKIP,NORM      | BLUE   | O   | `Time:`                       |
| CURTIME    | 2   | 71  | 8      | ASKIP,FSET,NORM | BLUE   | O   | Current time                  |

### Screen Title and Page Number (row 4)

| Field Name | Row | Col | Length | ATTRB           | Color     | I/O | Notes                     |
|------------|-----|-----|--------|-----------------|-----------|-----|---------------------------|
| (title)    | 4   | 35  | 10     | ASKIP,BRT       | NEUTRAL   | O   | `List Users`              |
| (label)    | 4   | 65  | 5      | ASKIP,BRT       | TURQUOISE | O   | `Page:`                   |
| PAGENUM    | 4   | 71  | 8      | ASKIP,FSET,NORM | BLUE      | O   | Current page; init space  |

### Search Field (row 6)

| Field Name | Row | Col | Length | ATTRB            | Color | Hilight   | I/O   | Notes                              |
|------------|-----|-----|--------|------------------|-------|-----------|-------|------------------------------------|
| (label)    | 6   | 5   | 15     | ASKIP,NORM       | TURQUOISE| —       | O     | `Search User ID:`                  |
| USRIDIN    | 6   | 21  | 8      | FSET,NORM,UNPROT | GREEN | UNDERLINE | Input | User ID search key                 |
| (stopper)  | 6   | 30  | 0      | ASKIP,NORM       | —     | —         | —     | Tab stop                           |

### Column Headers (rows 8–9)

| Row | Col | Length | Content                 | Color   |
|-----|-----|--------|-------------------------|---------|
| 8   | 5   | 3      | `Sel`                   | NEUTRAL |
| 8   | 12  | 8      | `User ID `              | NEUTRAL |
| 8   | 24  | 20     | `     First Name     `  | NEUTRAL |
| 8   | 48  | 20     | `     Last Name      `  | NEUTRAL |
| 8   | 72  | 4      | `Type`                  | NEUTRAL |
| 9   | 5   | 3      | `---`                   | NEUTRAL |
| 9   | 12  | 8      | `--------`              | NEUTRAL |
| 9   | 24  | 20     | `--------------------`  | NEUTRAL |
| 9   | 48  | 20     | `--------------------`  | NEUTRAL |
| 9   | 72  | 4      | `----`                  | NEUTRAL |

### List Rows (rows 10–19) — 10 user slots

Each row (n = 01–10) follows an identical pattern:

| Field Name | Row  | Col | Length | ATTRB               | Color | Hilight   | I/O   | Notes                                     |
|------------|------|-----|--------|---------------------|-------|-----------|-------|-------------------------------------------|
| SEL000n    | 9+n  | 6   | 1      | FSET,NORM,UNPROT    | GREEN | UNDERLINE | Input | Selector; `U`=update, `D`=delete; init space |
| (stopper)  | 9+n  | 8   | 0      | ASKIP,NORM          | —     | —         | —     | Tab stop                                  |
| USRIDnn    | 9+n  | 12  | 8      | ASKIP,FSET,NORM     | BLUE  | —         | O     | User ID; init space                       |
| FNAMEnn    | 9+n  | 24  | 20     | ASKIP,FSET,NORM     | BLUE  | —         | O     | First name; init space                    |
| LNAMEnn    | 9+n  | 48  | 20     | ASKIP,FSET,NORM     | BLUE  | —         | O     | Last name; init space                     |
| UTYPEnn    | 9+n  | 73  | 1      | ASKIP,FSET,NORM     | BLUE  | —         | O     | User type (A/U); init space               |

Complete field name reference:

| Row | Selector | User ID  | First Name | Last Name | Type    |
|-----|----------|----------|------------|-----------|---------|
| 10  | SEL0001  | USRID01  | FNAME01    | LNAME01   | UTYPE01 |
| 11  | SEL0002  | USRID02  | FNAME02    | LNAME02   | UTYPE02 |
| 12  | SEL0003  | USRID03  | FNAME03    | LNAME03   | UTYPE03 |
| 13  | SEL0004  | USRID04  | FNAME04    | LNAME04   | UTYPE04 |
| 14  | SEL0005  | USRID05  | FNAME05    | LNAME05   | UTYPE05 |
| 15  | SEL0006  | USRID06  | FNAME06    | LNAME06   | UTYPE06 |
| 16  | SEL0007  | USRID07  | FNAME07    | LNAME07   | UTYPE07 |
| 17  | SEL0008  | USRID08  | FNAME08    | LNAME08   | UTYPE08 |
| 18  | SEL0009  | USRID09  | FNAME09    | LNAME09   | UTYPE09 |
| 19  | SEL0010  | USRID10  | FNAME10    | LNAME10   | UTYPE10 |

### Instructions and Navigation (rows 21–24)

| Field Name | Row | Col | Length | ATTRB          | Color     | I/O | Notes                                              |
|------------|-----|-----|--------|----------------|-----------|-----|----------------------------------------------------|
| (instruct) | 21  | 12  | 56     | ASKIP,BRT      | NEUTRAL   | O   | `Type 'U' to Update or 'D' to Delete a User from the list` |
| ERRMSG     | 23  | 1   | 78     | ASKIP,BRT,FSET | RED       | O   | Error message                                      |
| (fkeys)    | 24  | 1   | 48     | ASKIP,NORM     | YELLOW    | O   | `ENTER=Continue  F3=Back  F7=Backward  F8=Forward` |

---

## 5. Screen Navigation

| Key   | Action                                                                          |
|-------|---------------------------------------------------------------------------------|
| ENTER | Process selected action (U or D) for chosen user row                            |
| PF3   | Return to admin menu (COADM01)                                                  |
| PF7   | Page backward through user list                                                 |
| PF8   | Page forward through user list                                                  |

**Selection mechanic:**
- `U` in a SEL field → navigates to COUSR02 (Update User) with that user's ID pre-loaded
- `D` in a SEL field → navigates to COUSR03 (Delete User) with that user's ID pre-loaded

---

## 6. Validation Rules

| Field     | BMS Constraint           | Program-Level Validation                                 |
|-----------|--------------------------|----------------------------------------------------------|
| USRIDIN   | Length=8, UNPROT, FSET   | Optional search key; filters the display                 |
| SEL0001–10| Length=1, UNPROT, FSET   | Valid values: `U` (update) or `D` (delete); only one row |

---

## 7. Related Screens

| Screen  | Mapset  | Relationship                                           |
|---------|---------|--------------------------------------------------------|
| COADM01 | COADM01 | Navigate FROM (admin menu user management option)      |
| COUSR01 | COUSR01 | Navigate TO for add user (from admin menu)             |
| COUSR02 | COUSR02 | Navigate TO when `U` selected for a user row           |
| COUSR03 | COUSR03 | Navigate TO when `D` selected for a user row           |
