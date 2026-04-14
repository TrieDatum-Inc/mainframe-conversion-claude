# COUSR02 — Update User Screen Technical Specification

## 1. Screen Overview

**Purpose:** Allows an administrator to update an existing user's profile. The operator enters a User ID and presses ENTER to fetch the current record, then modifies First Name, Last Name, Password, and User Type fields. Function keys F3=Save&Exit and F5=Save provide save options; F12=Cancel abandons changes.

**Driving Program:** COUSR02C (Update User program)

**Source File:** `/app/bms/COUSR02.bms`
**Copybook:** `/app/cpy-bms/COUSR02.CPY`

---

## 2. Map/Mapset Definition

| Attribute    | Value             |
|--------------|-------------------|
| MAPSET name  | COUSR02           |
| MAP name     | COUSR2A           |
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
Row4:                                   Update User
Row5:
Row6:      Enter User ID:[USRIDIN-]
Row7:
Row8:      ***********************************************************************
Row9:
Row10:
Row11:     First Name:[FNAME--------------]     Last Name:[LNAME--------------]
Row12:
Row13:     Password:[PASSWD--] (8 Char)
Row14:
Row15:     User Type: [T] (A=Admin, U=User)
Row16:
Row17:
Row18:
Row19:
Row20:
Row21:
Row22:
Row23: [---------------------------ERRMSG------------------------------------]
Row24: ENTER=Fetch  F3=Save&Exit  F4=Clear  F5=Save  F12=Cancel
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

### Screen Title (row 4)

| Row | Col | Length | Content       | ATTRB     | Color   |
|-----|-----|--------|---------------|-----------|---------|
| 4   | 35  | 11     | `Update User` | ASKIP,BRT | NEUTRAL |

### User ID Lookup (row 6)

| Field Name | Row | Col | Length | ATTRB               | Color | Hilight   | I/O   | Notes                             |
|------------|-----|-----|--------|---------------------|-------|-----------|-------|-----------------------------------|
| (label)    | 6   | 6   | 14     | ASKIP,NORM          | GREEN | —         | O     | `Enter User ID:`                  |
| USRIDIN    | 6   | 21  | 8      | FSET,IC,NORM,UNPROT | GREEN | UNDERLINE | Input | User ID to look up; IC here       |
| (stopper)  | 6   | 30  | 0      | ASKIP,NORM          | —     | —         | —     | Tab stop                          |

### Visual Separator (row 8)

| Row | Col | Length | Content   | Color  |
|-----|-----|--------|-----------|--------|
| 8   | 6   | 70     | 70 asterisks `***...***` | YELLOW |

### Editable User Detail Fields (rows 11–15)

| Field Name | Row | Col | Length | ATTRB            | Color     | Hilight   | I/O   | Notes                                  |
|------------|-----|-----|--------|------------------|-----------|-----------|-------|----------------------------------------|
| (label)    | 11  | 6   | 11     | ASKIP,NORM       | TURQUOISE | —         | O     | `First Name:`                          |
| FNAME      | 11  | 18  | 20     | FSET,NORM,UNPROT | GREEN     | UNDERLINE | Input | First name — editable after fetch      |
| (stopper)  | 11  | 39  | 0      | ASKIP,NORM       | —         | —         | —     | Tab stop                               |
| (label)    | 11  | 45  | 10     | ASKIP,NORM       | TURQUOISE | —         | O     | `Last Name:`                           |
| LNAME      | 11  | 56  | 20     | FSET,NORM,UNPROT | GREEN     | UNDERLINE | Input | Last name — editable after fetch       |
| (stopper)  | 11  | 77  | 0      | GREEN            | —         | —         | —     | Tab stop                               |
| (label)    | 13  | 6   | 9      | ASKIP,NORM       | TURQUOISE | —         | O     | `Password:`                            |
| PASSWD     | 13  | 16  | 8      | DRK,FSET,UNPROT  | GREEN     | UNDERLINE | Input | Password — **DRK** (masked); 8 chars   |
| (hint)     | 13  | 25  | 8      | ASKIP,NORM       | BLUE      | —         | O     | `(8 Char)`                             |
| (label)    | 15  | 6   | 11     | ASKIP,NORM       | TURQUOISE | —         | O     | `User Type: `                          |
| USRTYPE    | 15  | 17  | 1      | FSET,NORM,UNPROT | GREEN     | UNDERLINE | Input | A=Admin, U=User                        |
| (hint)     | 15  | 19  | 17     | ASKIP,NORM       | BLUE      | —         | O     | `(A=Admin, U=User)`                    |

### Message and Navigation (rows 23–24)

| Field Name | Row | Col | Length | ATTRB          | Color  | I/O | Notes                                           |
|------------|-----|-----|--------|----------------|--------|-----|-------------------------------------------------|
| ERRMSG     | 23  | 1   | 78     | ASKIP,BRT,FSET | RED    | O   | Error message                                   |
| (fkeys)    | 24  | 1   | 58     | ASKIP,NORM     | YELLOW | O   | `ENTER=Fetch  F3=Save&&Exit  F4=Clear  F5=Save  F12=Cancel` |

**Note on F3=Save&&Exit:** The double ampersand `&&` in the BMS source is the BMS escape sequence for a literal `&` character in the INITIAL value. The displayed text on screen row 24 is `ENTER=Fetch  F3=Save&Exit  F4=Clear  F5=Save  F12=Cancel`.

---

## 5. Two-Phase Interaction Pattern

**Phase 1 — Fetch:**
1. Operator types User ID in USRIDIN
2. Presses ENTER
3. Program reads USRIDINI, looks up user record
4. Program populates FNAME, LNAME, USRTYPE fields with current values
5. PASSWD field is cleared (not populated with masked stars — operator must re-enter if changing)
6. Map re-sent; detail fields become active for editing

**Phase 2 — Update:**
1. Operator modifies desired fields
2. Presses PF5 (save) or PF3 (save and exit)
3. Program reads modified fields and updates the user record
4. PF12 cancels without saving

---

## 6. Screen Navigation

| Key   | Action                                                                       |
|-------|------------------------------------------------------------------------------|
| ENTER | Fetches user record for USRIDIN; populates detail fields                     |
| PF3   | Save current changes and return to admin menu                                |
| PF4   | Clear all fields                                                             |
| PF5   | Save changes and remain on this screen                                       |
| PF12  | Cancel all changes; return to admin menu without saving                      |

---

## 7. Validation Rules

| Field   | BMS Constraint          | Program-Level Validation                                     |
|---------|-------------------------|--------------------------------------------------------------|
| USRIDIN | Length=8, UNPROT, FSET  | Must exist in the user file; error if not found              |
| FNAME   | Length=20, UNPROT, FSET | Must not be blank after fetch                                |
| LNAME   | Length=20, UNPROT, FSET | Must not be blank after fetch                                |
| PASSWD  | Length=8, DRK, UNPROT   | If non-blank, must be exactly 8 characters (new password)    |
| USRTYPE | Length=1, UNPROT, FSET  | Must be A or U                                               |

---

## 8. Related Screens

| Screen  | Mapset  | Relationship                                             |
|---------|---------|----------------------------------------------------------|
| COUSR00 | COUSR00 | Navigate FROM (user list; `U` selector leads here)       |
| COADM01 | COADM01 | Navigate TO/FROM (admin menu)                            |
