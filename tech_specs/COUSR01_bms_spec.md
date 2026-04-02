# Technical Specification: COUSR01 BMS Mapset — Add User Screen

## 1. Executive Summary

COUSR01 is a BMS mapset defining the terminal screen for the CardDemo "Add User" function. It presents a data entry form collecting all required fields to create a new user record: First Name, Last Name, User ID, Password, and User Type. The mapset is consumed by program COUSR01C (transaction CU01).

---

## 2. Artifact Identification

| Attribute          | Value                              |
|-------------------|------------------------------------|
| Mapset Name       | COUSR01                            |
| Source File       | app/bms/COUSR01.bms                |
| Map Name          | COUSR1A                            |
| Generated Copybook | app/cpy-bms/COUSR01.CPY          |
| Consuming Program | COUSR01C                           |
| Transaction ID    | CU01                               |
| Screen Size       | 24 rows x 80 columns               |
| Version Tag       | CardDemo_v1.0-70-g193b394-123, 2022-08-22 |

---

## 3. Mapset-Level Attributes (DFHMSD — line 19)

| Attribute | Value        | Meaning                                      |
|-----------|--------------|----------------------------------------------|
| CTRL      | ALARM,FREEKB | Sound alarm; free keyboard after send        |
| EXTATT    | YES          | Extended attributes (color, highlight)       |
| LANG      | COBOL        | COBOL-format generated copybook              |
| MODE      | INOUT        | Used for both send and receive               |
| STORAGE   | AUTO         | Automatic TIOA storage                       |
| TIOAPFX   | YES          | Include TIOA prefix                          |
| TYPE      | &&SYSPARM    | Resolved at assembly time                    |

---

## 4. Map Definition — COUSR1A (DFHMDI — line 26)

| Attribute | Value   | Meaning                    |
|-----------|---------|----------------------------|
| COLUMN    | 1       | Map starts at column 1     |
| LINE      | 1       | Map starts at row 1        |
| SIZE      | (24,80) | Full 24x80 3270 screen     |

---

## 5. Screen Layout

```
Col:  1         2         3         4         5         6         7         8
      0123456789012345678901234567890123456789012345678901234567890123456789012345678901
Row:
 1   Tran:[TRNNAME ]        [         TITLE01          ]        Date:[CURDATE ]
 2   Prog:[PGMNAME ]        [         TITLE02          ]        Time:[CURTIME ]
 3   (blank)
 4                                     Add User
 5   (blank)
 6   (blank)
 7   (blank)
 8       First Name:[       FNAME        ]      Last Name:[       LNAME        ]
 9   (blank)
10   (blank)
11      User ID:[USERID  ] (8 Char)       Password:[PASSWD  ] (8 Char)
12   (blank)
13   (blank)
14      User Type: [U] (A=Admin, U=User)
15   (blank)
16–22 (blank)
23   [                          ERRMSG                                        ]
24   ENTER=Add User  F3=Back  F4=Clear  F12=Exit
```

Fields in brackets are input-capable (UNPROT). All other content is static labels or display-only.

---

## 6. Field Definitions

### 6.1 Header Fields (Rows 1–2)

| Field Name | Row | Col | Len | Color  | Attributes      | Purpose                        |
|-----------|-----|-----|-----|--------|-----------------|--------------------------------|
| (literal) | 1   | 1   | 5   | BLUE   | ASKIP,NORM      | 'Tran:'                        |
| TRNNAME   | 1   | 7   | 4   | BLUE   | ASKIP,FSET,NORM | Transaction ID output (CU01)  |
| TITLE01   | 1   | 21  | 40  | YELLOW | ASKIP,FSET,NORM | Title line 1 (COTTL01Y)       |
| (literal) | 1   | 65  | 5   | BLUE   | ASKIP,NORM      | 'Date:'                        |
| CURDATE   | 1   | 71  | 8   | BLUE   | ASKIP,FSET,NORM | Current date MM/DD/YY         |
| (literal) | 2   | 1   | 5   | BLUE   | ASKIP,NORM      | 'Prog:'                        |
| PGMNAME   | 2   | 7   | 8   | BLUE   | ASKIP,FSET,NORM | Program name output (COUSR01C)|
| TITLE02   | 2   | 21  | 40  | YELLOW | ASKIP,FSET,NORM | Title line 2                   |
| (literal) | 2   | 65  | 5   | BLUE   | ASKIP,NORM      | 'Time:'                        |
| CURTIME   | 2   | 71  | 8   | BLUE   | ASKIP,FSET,NORM | Current time HH:MM:SS         |

### 6.2 Screen Title (Row 4)

| Field Name | Row | Col | Len | Color   | Attributes | Content       |
|-----------|-----|-----|-----|---------|------------|---------------|
| (literal) | 4   | 35  | 9   | NEUTRAL | ASKIP,BRT  | 'Add User'    |

Note: BMS source (line 79) specifies LENGTH=9 for 'Add User' (8 chars + space).

### 6.3 Name Fields (Row 8)

| Field Name | Row | Col | Len | Color     | Attributes           | Highlight | Purpose                          |
|-----------|-----|-----|-----|-----------|----------------------|-----------|----------------------------------|
| (literal) | 8   | 6   | 11  | TURQUOISE | (default)            | None      | 'First Name:'                    |
| FNAME     | 8   | 18  | 20  | GREEN     | FSET,IC,NORM,UNPROT  | UNDERLINE | First name input; cursor home (IC) |
| (stopper) | 8   | 39  | 0   | —         | ASKIP,NORM           | —         | Field terminator                 |
| (literal) | 8   | 45  | 10  | TURQUOISE | ASKIP,NORM           | None      | 'Last Name:'                     |
| LNAME     | 8   | 56  | 20  | GREEN     | FSET,NORM,UNPROT     | UNDERLINE | Last name input                  |
| (stopper) | 8   | 77  | 0   | GREEN     | ASKIP,NORM           | —         | Field terminator                 |

FNAME carries the IC (Initial Cursor) attribute, making it the cursor home field when the screen is first displayed. This aligns with COUSR01C setting FNAMEL = -1 as the cursor control.

### 6.4 User ID and Password Fields (Row 11)

| Field Name | Row | Col | Len | Color     | Attributes        | Highlight | Purpose                          |
|-----------|-----|-----|-----|-----------|-------------------|-----------|----------------------------------|
| (literal) | 11  | 6   | 8   | TURQUOISE | ASKIP,NORM        | None      | 'User ID:'                       |
| USERID    | 11  | 15  | 8   | GREEN     | FSET,NORM,UNPROT  | UNDERLINE | User ID input (8 chars)          |
| (literal) | 11  | 24  | 8   | BLUE      | ASKIP,NORM        | None      | '(8 Char)' hint                  |
| (literal) | 11  | 45  | 9   | TURQUOISE | ASKIP,NORM        | None      | 'Password:'                      |
| PASSWD    | 11  | 55  | 8   | GREEN     | DRK,FSET,UNPROT   | UNDERLINE | Password input — DARK (non-display) |
| (literal) | 11  | 64  | 8   | BLUE      | ASKIP,NORM        | None      | '(8 Char)' hint                  |

PASSWD uses ATTRB=DRK which suppresses display of the typed characters on the terminal screen (password masking). The typed data is still transmitted in the input stream.

### 6.5 User Type Field (Row 14)

| Field Name | Row | Col | Len | Color     | Attributes        | Highlight | Purpose                          |
|-----------|-----|-----|-----|-----------|-------------------|-----------|----------------------------------|
| (literal) | 14  | 6   | 11  | TURQUOISE | ASKIP,NORM        | None      | 'User Type: '                    |
| USRTYPE   | 14  | 17  | 1   | GREEN     | FSET,NORM,UNPROT  | UNDERLINE | Single-char type: A or U         |
| (literal) | 14  | 19  | 17  | BLUE      | ASKIP,NORM        | None      | '(A=Admin, U=User)' hint         |

### 6.6 Message and Function Key Fields (Rows 23–24)

| Field Name | Row | Col | Len | Color  | Attributes      | Purpose                                              |
|-----------|-----|-----|-----|--------|-----------------|------------------------------------------------------|
| ERRMSG    | 23  | 1   | 78  | RED    | ASKIP,BRT,FSET  | Error/status message display area                    |
| (literal) | 24  | 1   | 43  | YELLOW | ASKIP,NORM      | 'ENTER=Add User  F3=Back  F4=Clear  F12=Exit'        |

Note: The function key line (line 159) shows F12=Exit but COUSR01C's MAIN-PARA does not handle DFHPF12 explicitly — it falls into the OTHER branch (invalid key). **This is a discrepancy between the screen instruction and the program's implemented key handling.** COUSR01C handles only DFHENTER, DFHPF3, and DFHPF4.

---

## 7. Symbolic Map Structure (COUSR01.CPY — app/cpy-bms/COUSR01.CPY)

Generated structures (lines 17–164 of COUSR01.CPY):

**COUSR1AI (Input, lines 17–90):**

| Symbolic Field | Type       | Length | BMS Field |
|----------------|------------|--------|-----------|
| TRNNAMEL       | COMP S9(4) | 2      | TRNNAME length |
| TRNNAMEI       | PIC X(4)   | 4      | TRNNAME data |
| TITLE01I       | PIC X(40)  | 40     | TITLE01 data |
| CURDATEI       | PIC X(8)   | 8      | CURDATE data |
| PGMNAMEI       | PIC X(8)   | 8      | PGMNAME data |
| TITLE02I       | PIC X(40)  | 40     | TITLE02 data |
| CURTIMEI       | PIC X(8)   | 8      | CURTIME data |
| FNAMEL         | COMP S9(4) | 2      | FNAME cursor control |
| FNAMEI         | PIC X(20)  | 20     | FNAME data |
| LNAMEL         | COMP S9(4) | 2      | LNAME cursor control |
| LNAMEI         | PIC X(20)  | 20     | LNAME data |
| USERIDL        | COMP S9(4) | 2      | USERID cursor control |
| USERIDI        | PIC X(8)   | 8      | USERID data |
| PASSWDL        | COMP S9(4) | 2      | PASSWD cursor control |
| PASSWDI        | PIC X(8)   | 8      | PASSWD data |
| USRTYPEL       | COMP S9(4) | 2      | USRTYPE cursor control |
| USRTYPEI       | PIC X(1)   | 1      | USRTYPE data |
| ERRMSGL        | COMP S9(4) | 2      | ERRMSG cursor control |
| ERRMSGI        | PIC X(78)  | 78     | ERRMSG data |

**COUSR1AO (Output, REDEFINES COUSR1AI, lines 91–164):**
Exposes C/P/H/V/O variants for each field (color, print, highlight, video, output data).

---

## 8. Field-to-Program Data Mapping

| BMS Field | Symbolic In | Symbolic Out | COUSR01C Program Usage                          |
|-----------|-------------|--------------|--------------------------------------------------|
| FNAME     | FNAMEI      | FNAMEO       | Input: validated not blank; moved to SEC-USR-FNAME |
| LNAME     | LNAMEI      | LNAMEO       | Input: validated not blank; moved to SEC-USR-LNAME |
| USERID    | USERIDI     | USERIDO      | Input: validated not blank; moved to SEC-USR-ID (VSAM key) |
| PASSWD    | PASSWDI     | PASSWDO      | Input: validated not blank; moved to SEC-USR-PWD |
| USRTYPE   | USRTYPEI    | USRTYPEO     | Input: validated not blank; moved to SEC-USR-TYPE |
| ERRMSG    | ERRMSGI     | ERRMSGO      | Output: error/success messages; ERRMSGC for color |
| TRNNAME   | —           | TRNNAMEO     | Output: literal 'CU01'                           |
| PGMNAME   | —           | PGMNAMEO     | Output: literal 'COUSR01C'                       |
| TITLE01   | —           | TITLE01O     | Output: from CCDA-TITLE01 (COTTL01Y)             |
| TITLE02   | —           | TITLE02O     | Output: from CCDA-TITLE02 (COTTL01Y)             |
| CURDATE   | —           | CURDATEO     | Output: current date MM/DD/YY                    |
| CURTIME   | —           | CURTIMEO     | Output: current time HH:MM:SS                    |

Cursor positioning: COUSR01C sets XL fields to -1 to position cursor. FNAME field has IC (Initial Cursor) in BMS definition, which the program overrides by setting FNAMEL=-1 on all screen sends.

---

## 9. Navigation / Function Key Definitions

As shown in static label Row 24 (BMS lines 155–159):

| Key   | Advertised Action | COUSR01C Handling                                |
|-------|-------------------|--------------------------------------------------|
| ENTER | Add User          | PROCESS-ENTER-KEY: validate + WRITE USRSEC      |
| F3    | Back              | RETURN-TO-PREV-SCREEN to COADM01C               |
| F4    | Clear             | CLEAR-CURRENT-SCREEN: clear all input fields    |
| F12   | Exit              | NOT implemented in COUSR01C (falls to OTHER; shows invalid key error) |

---

## 10. Design Notes and Observations

- FNAME has ATTRB=FSET,IC,NORM,UNPROT. The IC attribute places the cursor on this field when the map is sent without a specific cursor override. COUSR01C also explicitly sets FNAMEL=-1, so cursor behavior is consistent.
- PASSWD has ATTRB=DRK,FSET,UNPROT. DRK renders the field invisible on the 3270 terminal. FSET ensures the password data is always included in the terminal input stream (MDT bit always set), preventing the field from appearing empty when the user only tabs past it without typing.
- The LNAME field stopper (LENGTH=0 at position 8,77) and the PASSWD stopper approach follow standard BMS multi-field-per-row layout patterns.
- The F12=Exit key shown on Row 24 is not handled by COUSR01C, which would display an invalid key error if pressed. This is a documentation-code discrepancy. F12 handling was added to COUSR02C and COUSR03C but not COUSR01C.
- Layout uses a two-column arrangement: First Name and Last Name on Row 8; User ID and Password on Row 11. User Type stands alone on Row 14.
