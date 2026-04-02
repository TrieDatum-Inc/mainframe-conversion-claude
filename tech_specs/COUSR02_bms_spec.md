# Technical Specification: COUSR02 BMS Mapset — Update User Screen

## 1. Executive Summary

COUSR02 is a BMS mapset defining the terminal screen for the CardDemo "Update User" function. The screen has two distinct zones: a User ID lookup entry field at the top, and an editable data section populated after the record is fetched. Users enter a User ID, press ENTER to fetch the record, modify the displayed fields, then press PF5 to save (or PF3 to save-and-return). The mapset is consumed by program COUSR02C (transaction CU02).

---

## 2. Artifact Identification

| Attribute          | Value                              |
|-------------------|------------------------------------|
| Mapset Name       | COUSR02                            |
| Source File       | app/bms/COUSR02.bms                |
| Map Name          | COUSR2A                            |
| Generated Copybook | app/cpy-bms/COUSR02.CPY          |
| Consuming Program | COUSR02C                           |
| Transaction ID    | CU02                               |
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

## 4. Map Definition — COUSR2A (DFHMDI — line 26)

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
 4                                    Update User
 5   (blank)
 6      Enter User ID:[USRIDIN ] 
 7   (blank)
 8      *********************************************************************
 9   (blank)
10   (blank)
11      First Name:[       FNAME        ]      Last Name:[       LNAME        ]
12   (blank)
13      Password:[PASSWD  ] (8 Char)
14   (blank)
15      User Type: [U] (A=Admin, U=User)
16–22 (blank)
23   [                          ERRMSG                                        ]
24   ENTER=Fetch  F3=Save&&Exit  F4=Clear  F5=Save  F12=Cancel
```

---

## 6. Field Definitions

### 6.1 Header Fields (Rows 1–2)

Identical pattern to COUSR01. See COUSR01_bms_spec.md Section 6.1 for structure.

| Field Name | Row | Col | Len | Color  | Attributes      | Purpose                         |
|-----------|-----|-----|-----|--------|-----------------|---------------------------------|
| (literal) | 1   | 1   | 5   | BLUE   | ASKIP,NORM      | 'Tran:'                         |
| TRNNAME   | 1   | 7   | 4   | BLUE   | ASKIP,FSET,NORM | Transaction ID output (CU02)   |
| TITLE01   | 1   | 21  | 40  | YELLOW | ASKIP,FSET,NORM | Title line 1                    |
| (literal) | 1   | 65  | 5   | BLUE   | ASKIP,NORM      | 'Date:'                         |
| CURDATE   | 1   | 71  | 8   | BLUE   | ASKIP,FSET,NORM | Current date MM/DD/YY          |
| (literal) | 2   | 1   | 5   | BLUE   | ASKIP,NORM      | 'Prog:'                         |
| PGMNAME   | 2   | 7   | 8   | BLUE   | ASKIP,FSET,NORM | Program name output (COUSR02C) |
| TITLE02   | 2   | 21  | 40  | YELLOW | ASKIP,FSET,NORM | Title line 2                    |
| (literal) | 2   | 65  | 5   | BLUE   | ASKIP,NORM      | 'Time:'                         |
| CURTIME   | 2   | 71  | 8   | BLUE   | ASKIP,FSET,NORM | Current time HH:MM:SS          |

### 6.2 Screen Title (Row 4)

| Field Name | Row | Col | Len | Color   | Attributes | Content       |
|-----------|-----|-----|-----|---------|------------|---------------|
| (literal) | 4   | 35  | 11  | NEUTRAL | ASKIP,BRT  | 'Update User' |

### 6.3 User ID Lookup Field (Row 6)

| Field Name | Row | Col | Len | Color | Attributes          | Highlight | Purpose                               |
|-----------|-----|-----|-----|-------|---------------------|-----------|---------------------------------------|
| (literal) | 6   | 6   | 14  | GREEN | ASKIP,NORM          | None      | 'Enter User ID:'                      |
| USRIDIN   | 6   | 21  | 8   | GREEN | FSET,IC,NORM,UNPROT | UNDERLINE | User ID entry field; cursor home (IC) |
| (stopper) | 6   | 30  | 0   | —     | ASKIP,NORM          | —         | Field terminator                      |

USRIDIN carries IC (Initial Cursor) — cursor starts here when screen is displayed. COUSR02C also sets USRIDINL=-1 explicitly to maintain cursor position. Stored in symbolic map as USRIDINI / USRIDINO.

### 6.4 Visual Separator (Row 8)

| Row | Col | Len | Color  | Content                                                      |
|-----|-----|-----|--------|--------------------------------------------------------------|
| 8   | 6   | 70  | YELLOW | '***...***' (70 asterisks as a visual separator between lookup and data areas) |

This separator delineates the "search" zone (rows 1–7) from the "data entry" zone (rows 9+). It has no attribute code in source (defaults to ASKIP,NORM).

### 6.5 Editable Data Fields (Rows 11–15)

These fields are populated by COUSR02C after a successful READ from USRSEC and are editable by the operator.

#### Row 11 — First Name and Last Name

| Field Name | Row | Col | Len | Color     | Attributes        | Highlight | Purpose                          |
|-----------|-----|-----|-----|-----------|-------------------|-----------|----------------------------------|
| (literal) | 11  | 6   | 11  | TURQUOISE | ASKIP,NORM        | None      | 'First Name:'                    |
| FNAME     | 11  | 18  | 20  | GREEN     | FSET,NORM,UNPROT  | UNDERLINE | First name (editable)            |
| (stopper) | 11  | 39  | 0   | —         | ASKIP,NORM        | —         | Field terminator                 |
| (literal) | 11  | 45  | 10  | TURQUOISE | ASKIP,NORM        | None      | 'Last Name:'                     |
| LNAME     | 11  | 56  | 20  | GREEN     | FSET,NORM,UNPROT  | UNDERLINE | Last name (editable)             |
| (stopper) | 11  | 77  | 0   | GREEN     | ASKIP,NORM        | —         | Field terminator                 |

#### Row 13 — Password

| Field Name | Row | Col | Len | Color     | Attributes        | Highlight | Purpose                               |
|-----------|-----|-----|-----|-----------|-------------------|-----------|---------------------------------------|
| (literal) | 13  | 6   | 9   | TURQUOISE | ASKIP,NORM        | None      | 'Password:'                           |
| PASSWD    | 13  | 16  | 8   | GREEN     | DRK,FSET,UNPROT   | UNDERLINE | Password entry — DARK (non-display)  |
| (literal) | 13  | 25  | 8   | BLUE      | ASKIP,NORM        | None      | '(8 Char)' hint                       |

#### Row 15 — User Type

| Field Name | Row | Col | Len | Color     | Attributes        | Highlight | Purpose                          |
|-----------|-----|-----|-----|-----------|-------------------|-----------|----------------------------------|
| (literal) | 15  | 6   | 11  | TURQUOISE | ASKIP,NORM        | None      | 'User Type: '                    |
| USRTYPE   | 15  | 17  | 1   | GREEN     | FSET,NORM,UNPROT  | UNDERLINE | User type code A or U            |
| (literal) | 15  | 19  | 17  | BLUE      | ASKIP,NORM        | None      | '(A=Admin, U=User)' hint         |

### 6.6 Message and Function Key Fields (Rows 23–24)

| Field Name | Row | Col | Len | Color  | Attributes      | Purpose                                                             |
|-----------|-----|-----|-----|--------|-----------------|---------------------------------------------------------------------|
| ERRMSG    | 23  | 1   | 78  | RED    | ASKIP,BRT,FSET  | Error/status/confirmation message                                  |
| (literal) | 24  | 1   | 58  | YELLOW | ASKIP,NORM      | 'ENTER=Fetch  F3=Save&&Exit  F4=Clear  F5=Save  F12=Cancel'        |

Note: '&&' in BMS source represents a literal single '&' after assembly, so the displayed text reads 'F3=Save&Exit'.

---

## 7. Symbolic Map Structure (COUSR02.CPY — app/cpy-bms/COUSR02.CPY)

**COUSR2AI (Input, lines 17–90):**

| Symbolic Field | PIC       | Length | BMS Field   |
|----------------|-----------|--------|-------------|
| USRIDINL       | COMP S9(4)| 2      | USRIDIN cursor/length |
| USRIDINI       | X(8)      | 8      | USRIDIN data input |
| FNAMEL         | COMP S9(4)| 2      | FNAME cursor control |
| FNAMEI         | X(20)     | 20     | FNAME data |
| LNAMEL         | COMP S9(4)| 2      | LNAME cursor control |
| LNAMEI         | X(20)     | 20     | LNAME data |
| PASSWDL        | COMP S9(4)| 2      | PASSWD cursor control |
| PASSWDI        | X(8)      | 8      | PASSWD data |
| USRTYPEL       | COMP S9(4)| 2      | USRTYPE cursor control |
| USRTYPEI       | X(1)      | 1      | USRTYPE data |
| ERRMSGL        | COMP S9(4)| 2      | ERRMSG cursor control |
| ERRMSGI        | X(78)     | 78     | ERRMSG data |

Plus header fields: TRNNAMEL/I, TITLE01L/I, CURDATEL/I, PGMNAMEL/I, TITLE02L/I, CURTIMEL/I.

**COUSR2AO (Output, REDEFINES COUSR2AI, lines 91–164):**
Exposes USRIDINC/P/H/V/O, FNAMEC/P/H/V/O, LNAMEC/P/H/V/O, PASSWDC/P/H/V/O, USRTYPEC/P/H/V/O, ERRMSGC/P/H/V/O, and header output fields.

---

## 8. Field-to-Program Data Mapping

| BMS Field | Sym In     | Sym Out    | COUSR02C Program Usage                                        |
|-----------|------------|------------|---------------------------------------------------------------|
| USRIDIN   | USRIDINI   | USRIDINO   | Input: User ID for VSAM key lookup; pre-set from COMMAREA   |
| FNAME     | FNAMEI     | FNAMEO     | Populated from SEC-USR-FNAME; compared/updated on save      |
| LNAME     | LNAMEI     | LNAMEO     | Populated from SEC-USR-LNAME; compared/updated on save      |
| PASSWD    | PASSWDI    | PASSWDO    | Populated from SEC-USR-PWD; compared/updated on save        |
| USRTYPE   | USRTYPEI   | USRTYPEO   | Populated from SEC-USR-TYPE; compared/updated on save       |
| ERRMSG    | ERRMSGI    | ERRMSGO    | Messages; ERRMSGC colored DFHNEUTR, DFHGREEN, or DFHRED    |
| TRNNAME   | —          | TRNNAMEO   | 'CU02'                                                        |
| PGMNAME   | —          | PGMNAMEO   | 'COUSR02C'                                                    |
| TITLE01   | —          | TITLE01O   | From CCDA-TITLE01                                             |
| TITLE02   | —          | TITLE02O   | From CCDA-TITLE02                                             |
| CURDATE   | —          | CURDATEO   | MM/DD/YY                                                      |
| CURTIME   | —          | CURTIMEO   | HH:MM:SS                                                      |

---

## 9. Navigation / Function Key Definitions

As shown in static label Row 24 (BMS lines 163–164):

| Key   | Advertised Action | COUSR02C Handling                                              |
|-------|-------------------|----------------------------------------------------------------|
| ENTER | Fetch             | PROCESS-ENTER-KEY: read user by USRIDIN and display           |
| F3    | Save & Exit       | UPDATE-USER-INFO then RETURN-TO-PREV-SCREEN                  |
| F4    | Clear             | CLEAR-CURRENT-SCREEN: blank all fields                        |
| F5    | Save              | UPDATE-USER-INFO: validate + change-detect + REWRITE         |
| F12   | Cancel            | RETURN-TO-PREV-SCREEN to COADM01C (no save)                  |

---

## 10. Design Notes and Observations

- This screen serves a dual workflow role: the USRIDIN field (Row 6) is used for initial lookup, while FNAME, LNAME, PASSWD, USRTYPE (Rows 11–15) are populated from the read record and become editable. The visual separator (Row 8) communicates this boundary to the operator.
- USRIDIN has ATTRB=IC (Initial Cursor), pre-positioning the cursor for the lookup step. However, when COUSR02C is invoked from COUSR00C with a pre-selected user, the program bypasses manual entry and performs the fetch automatically — cursor will be positioned by the USRIDINL=-1 setting at SEND time.
- The PASSWD field uses ATTRB=DRK,FSET,UNPROT. After a fetch, the current password is placed in PASSWDI via the output alias PASSWDO, and sent to the terminal as DRK (invisible). When the operator sends the screen back, the existing password is returned if they did not change it (FSET ensures MDT is set). If they type a new password, the new value replaces it.
- ERRMSGC is set dynamically by COUSR02C:
  - DFHNEUTR: neutral color when showing 'Press PF5 key to save...'
  - DFHGREEN: green on successful update
  - DFHRED: red when 'Please modify to update ...' (no changes detected)
- The BMS asterisk separator line (Row 8) carries no field name and uses COLOR=YELLOW for visual impact.
- The map does not contain a row-level protection mechanism for USRIDIN after the fetch. An operator can overtype the User ID field after fetching a record and press ENTER again to look up a different record.
