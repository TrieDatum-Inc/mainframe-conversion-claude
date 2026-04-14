# COUSR01 — Add User Screen Technical Specification

## 1. Screen Overview

**Purpose:** Provides a data entry form for creating a new CardDemo system user. The administrator enters the user's first name, last name, a User ID (8 characters), a password (8 characters, masked), and a user type (A=Admin or U=User). This screen is an admin-only function.

**Driving Program:** COUSR01C (Add User program)

**Source File:** `/app/bms/COUSR01.bms`
**Copybook:** `/app/cpy-bms/COUSR01.CPY`

---

## 2. Map/Mapset Definition

| Attribute    | Value             |
|--------------|-------------------|
| MAPSET name  | COUSR01           |
| MAP name     | COUSR1A           |
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
Row4:                                    Add User
Row5:
Row6:
Row7:
Row8:      First Name:[FNAME--------------]     Last Name:[LNAME--------------]
Row9:
Row10:
Row11:     User ID:[USERID--] (8 Char)         Password:[PASSWD--] (8 Char)
Row12:
Row13:
Row14:     User Type: [T] (A=Admin, U=User)
Row15:
Row16:
Row17:
Row18:
Row19:
Row20:
Row21:
Row22:
Row23: [---------------------------ERRMSG------------------------------------]
Row24: ENTER=Add User  F3=Back  F4=Clear  F12=Exit
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

| Row | Col | Length | Content    | ATTRB     | Color   |
|-----|-----|--------|------------|-----------|---------|
| 4   | 35  | 9      | `Add User` | ASKIP,BRT | NEUTRAL |

### Name Fields (row 8)

| Field Name | Row | Col | Length | ATTRB               | Color     | Hilight   | I/O   | Notes                             |
|------------|-----|-----|--------|---------------------|-----------|-----------|-------|-----------------------------------|
| (label)    | 8   | 6   | 11     | (default)           | TURQUOISE | —         | O     | `First Name:`                     |
| FNAME      | 8   | 18  | 20     | FSET,IC,NORM,UNPROT | GREEN     | UNDERLINE | Input | First name; IC positions cursor here |
| (stopper)  | 8   | 39  | 0      | ASKIP,NORM          | —         | —         | —     | Tab stop                          |
| (label)    | 8   | 45  | 10     | ASKIP,NORM          | TURQUOISE | —         | O     | `Last Name:`                      |
| LNAME      | 8   | 56  | 20     | FSET,NORM,UNPROT    | GREEN     | UNDERLINE | Input | Last name                         |
| (stopper)  | 8   | 77  | 0      | GREEN               | —         | —         | —     | Tab stop                          |

### Credentials Fields (row 11)

| Field Name | Row | Col | Length | ATTRB            | Color | Hilight   | I/O   | Notes                                             |
|------------|-----|-----|--------|------------------|-------|-----------|-------|---------------------------------------------------|
| (label)    | 11  | 6   | 8      | ASKIP,NORM       | TURQUOISE| —       | O     | `User ID:`                                        |
| USERID     | 11  | 15  | 8      | FSET,NORM,UNPROT | GREEN | UNDERLINE | Input | User ID; 8 alphanumeric characters                |
| (hint)     | 11  | 24  | 8      | ASKIP,NORM       | BLUE  | —         | O     | `(8 Char)`                                        |
| (label)    | 11  | 45  | 9      | ASKIP,NORM       | TURQUOISE| —       | O     | `Password:`                                       |
| PASSWD     | 11  | 55  | 8      | DRK,FSET,UNPROT  | GREEN | UNDERLINE | Input | Password — **DRK** (masked display); 8 characters |
| (hint)     | 11  | 64  | 8      | ASKIP,NORM       | BLUE  | —         | O     | `(8 Char)`                                        |

**PASSWD notes:** DRK attribute suppresses display of typed characters. The FSET attribute ensures the password value is transmitted to the program even if the operator does not change it on re-entry. This matches the same pattern as COSGN00's PASSWD field.

### User Type Field (row 14)

| Field Name | Row | Col | Length | ATTRB            | Color | Hilight   | I/O   | Notes                              |
|------------|-----|-----|--------|------------------|-------|-----------|-------|------------------------------------|
| (label)    | 14  | 6   | 11     | ASKIP,NORM       | TURQUOISE| —       | O     | `User Type: `                      |
| USRTYPE    | 14  | 17  | 1      | FSET,NORM,UNPROT | GREEN | UNDERLINE | Input | A=Admin, U=User                    |
| (hint)     | 14  | 19  | 17     | ASKIP,NORM       | BLUE  | —         | O     | `(A=Admin, U=User)`                |

### Message and Navigation (rows 23–24)

| Field Name | Row | Col | Length | ATTRB          | Color  | I/O | Notes                                     |
|------------|-----|-----|--------|----------------|--------|-----|-------------------------------------------|
| ERRMSG     | 23  | 1   | 78     | ASKIP,BRT,FSET | RED    | O   | Error message                             |
| (fkeys)    | 24  | 1   | 43     | ASKIP,NORM     | YELLOW | O   | `ENTER=Add User  F3=Back  F4=Clear  F12=Exit` |

---

## 5. Screen Navigation

| Key   | Action                                                                  |
|-------|-------------------------------------------------------------------------|
| ENTER | Validates fields and creates the new user record                        |
| PF3   | Returns to admin menu without creating user                             |
| PF4   | Clears all input fields                                                 |
| PF12  | Exits to admin menu                                                     |

---

## 6. Validation Rules

| Field   | BMS Constraint          | Program-Level Validation                                      |
|---------|-------------------------|---------------------------------------------------------------|
| FNAME   | Length=20, UNPROT, FSET | Must not be blank                                             |
| LNAME   | Length=20, UNPROT, FSET | Must not be blank                                             |
| USERID  | Length=8, UNPROT, FSET  | Must be exactly 8 chars; must not already exist in user file  |
| PASSWD  | Length=8, DRK, UNPROT   | Must not be blank; complexity rules — program level           |
| USRTYPE | Length=1, UNPROT, FSET  | Must be A or U                                                |

---

## 7. Related Screens

| Screen  | Mapset  | Relationship                                   |
|---------|---------|------------------------------------------------|
| COADM01 | COADM01 | Navigate FROM (admin menu add user option)     |
| COUSR00 | COUSR00 | Navigate FROM (user list; add is separate path)|
