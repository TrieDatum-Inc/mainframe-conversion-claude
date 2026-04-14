# COUSR03 — Delete User Screen Technical Specification

## 1. Screen Overview

**Purpose:** Provides a confirmation form for deleting an existing CardDemo system user. The operator enters a User ID and presses ENTER to fetch and display the user's details (First Name, Last Name, User Type) in read-only form. The administrator then presses PF5 to confirm and execute the deletion. This screen is an admin-only function.

**Driving Program:** COUSR03C (Delete User program)

**Source File:** `/app/bms/COUSR03.bms`
**Copybook:** `/app/cpy-bms/COUSR03.CPY`

---

## 2. Map/Mapset Definition

| Attribute    | Value             |
|--------------|-------------------|
| MAPSET name  | COUSR03           |
| MAP name     | COUSR3A           |
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
Row4:                                   Delete User
Row5:
Row6:      Enter User ID:[USRIDIN-]
Row7:
Row8:      ***********************************************************************
Row9:
Row10:
Row11:     First Name:[FNAME--------------]
Row12:
Row13:     Last Name:[LNAME--------------]
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
Row24: ENTER=Fetch  F3=Back  F4=Clear  F5=Delete
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
| 4   | 35  | 11     | `Delete User` | ASKIP,BRT | NEUTRAL |

### User ID Lookup (row 6)

| Field Name | Row | Col | Length | ATTRB               | Color | Hilight   | I/O   | Notes                                 |
|------------|-----|-----|--------|---------------------|-------|-----------|-------|---------------------------------------|
| (label)    | 6   | 6   | 14     | ASKIP,NORM          | GREEN | —         | O     | `Enter User ID:`                      |
| USRIDIN    | 6   | 21  | 8      | FSET,IC,NORM,UNPROT | GREEN | UNDERLINE | Input | User ID to delete; IC positions here  |
| (stopper)  | 6   | 30  | 0      | ASKIP,NORM          | —     | —         | —     | Tab stop                              |

### Visual Separator (row 8)

| Row | Col | Length | Content   | Color  |
|-----|-----|--------|-----------|--------|
| 8   | 6   | 70     | 70 asterisks | YELLOW |

### Display-Only User Details (rows 11–15)

**Critical distinction from COUSR02:** All three data fields on COUSR03 are **ASKIP** (auto-skip/protected), meaning they are display-only. The operator cannot edit them. This is intentional — the delete confirmation screen shows who will be deleted but does not permit modification.

| Field Name | Row | Col | Length | ATTRB           | Color     | Hilight   | I/O | Notes                            |
|------------|-----|-----|--------|-----------------|-----------|-----------|-----|----------------------------------|
| (label)    | 11  | 6   | 11     | ASKIP,NORM      | TURQUOISE | —         | O   | `First Name:`                    |
| FNAME      | 11  | 18  | 20     | ASKIP,FSET,NORM | BLUE      | UNDERLINE | O   | First name — **ASKIP** (display only) |
| (stopper)  | 11  | 39  | 0      | ASKIP,NORM      | —         | —         | —   | Tab stop                         |
| (label)    | 13  | 6   | 10     | ASKIP,NORM      | TURQUOISE | —         | O   | `Last Name:`                     |
| LNAME      | 13  | 18  | 20     | ASKIP,FSET,NORM | BLUE      | UNDERLINE | O   | Last name — **ASKIP** (display only)  |
| (stopper)  | 13  | 39  | 0      | GREEN           | —         | —         | —   | Tab stop                         |
| (label)    | 15  | 6   | 11     | ASKIP,NORM      | TURQUOISE | —         | O   | `User Type: `                    |
| USRTYPE    | 15  | 17  | 1      | ASKIP,FSET,NORM | BLUE      | UNDERLINE | O   | User type — **ASKIP** (display only) |
| (hint)     | 15  | 19  | 17     | ASKIP,NORM      | BLUE      | —         | O   | `(A=Admin, U=User)`              |

### Message and Navigation (rows 23–24)

| Field Name | Row | Col | Length | ATTRB          | Color  | I/O | Notes                                   |
|------------|-----|-----|--------|----------------|--------|-----|-----------------------------------------|
| ERRMSG     | 23  | 1   | 78     | ASKIP,BRT,FSET | RED    | O   | Error message                           |
| (fkeys)    | 24  | 1   | 58     | ASKIP,NORM     | YELLOW | O   | `ENTER=Fetch  F3=Back  F4=Clear  F5=Delete` |

---

## 5. Two-Phase Interaction Pattern

**Phase 1 — Fetch:**
1. Operator types User ID in USRIDIN and presses ENTER
2. Program looks up user record
3. FNAME, LNAME, USRTYPE fields are populated with the user's current data
4. Map re-sent showing the user's details for review

**Phase 2 — Confirm Delete:**
1. Operator reviews the displayed details
2. Presses PF5 to confirm and execute the deletion
3. Program deletes the user record
4. Success message displayed in ERRMSG; form cleared
5. PF3/PF4 cancels without deleting

---

## 6. Screen Navigation

| Key   | Action                                                                       |
|-------|------------------------------------------------------------------------------|
| ENTER | Fetches user record; populates FNAME, LNAME, USRTYPE for review              |
| PF3   | Returns to previous screen without deleting                                  |
| PF4   | Clears all fields                                                             |
| PF5   | **Executes delete** of the currently displayed user record                   |

---

## 7. Validation Rules

| Field   | BMS Constraint          | Program-Level Validation                                |
|---------|-------------------------|---------------------------------------------------------|
| USRIDIN | Length=8, UNPROT, FSET  | Must not be blank; must exist in the user file          |

Display fields (FNAME, LNAME, USRTYPE) are ASKIP — no input from operator; no validation needed.

**Safety check (program level):** The program should prevent deletion of the currently logged-in user and may prevent deletion of the last administrator account. These constraints are enforced by COUSR03C, not by the BMS map.

---

## 8. Key Structural Comparison: COUSR02 vs COUSR03

| Aspect           | COUSR02 (Update)                    | COUSR03 (Delete)                      |
|------------------|-------------------------------------|---------------------------------------|
| FNAME            | FSET,NORM,UNPROT — editable         | ASKIP,FSET,NORM — display only        |
| LNAME            | FSET,NORM,UNPROT — editable         | ASKIP,FSET,NORM — display only        |
| PASSWD           | DRK,FSET,UNPROT — editable (present)| Not present (no password field)       |
| USRTYPE          | FSET,NORM,UNPROT — editable         | ASKIP,FSET,NORM — display only        |
| Layout of FNAME/LNAME | Both on same row 11             | On separate rows 11 and 13            |
| PF3              | Save&Exit                           | Back (no save)                        |
| PF5              | Save                                | Delete (destructive)                  |
| PF12             | Cancel                              | Not present                           |

---

## 9. Related Screens

| Screen  | Mapset  | Relationship                                              |
|---------|---------|-----------------------------------------------------------|
| COUSR00 | COUSR00 | Navigate FROM (user list; `D` selector leads here)        |
| COADM01 | COADM01 | Navigate TO (admin menu, after completion or cancel)      |
