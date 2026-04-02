# Technical Specification: COUSR03 BMS Mapset — Delete User Screen

## 1. Executive Summary

COUSR03 is a BMS mapset defining the terminal screen for the CardDemo "Delete User" function. The screen shows a User ID lookup field and a read-only display of the fetched user's data (First Name, Last Name, User Type) for confirmation before deletion. Critically, all data fields are protected (ASKIP) — the operator can only look up the record and confirm or cancel the deletion. No editing is possible. The mapset is consumed by program COUSR03C (transaction CU03).

---

## 2. Artifact Identification

| Attribute          | Value                              |
|-------------------|------------------------------------|
| Mapset Name       | COUSR03                            |
| Source File       | app/bms/COUSR03.bms                |
| Map Name          | COUSR3A                            |
| Generated Copybook | app/cpy-bms/COUSR03.CPY          |
| Consuming Program | COUSR03C                           |
| Transaction ID    | CU03                               |
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

## 4. Map Definition — COUSR3A (DFHMDI — line 26)

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
 4                                    Delete User
 5   (blank)
 6      Enter User ID:[USRIDIN ] 
 7   (blank)
 8      *********************************************************************
 9   (blank)
10   (blank)
11      First Name:[  FNAME (display-only) ]
12   (blank)
13      Last Name: [  LNAME (display-only) ]
14   (blank)
15      User Type: [U] (A=Admin, U=User)
16–22 (blank)
23   [                          ERRMSG                                        ]
24   ENTER=Fetch  F3=Back  F4=Clear  F5=Delete
```

Note: Unlike COUSR02, the First Name and Last Name fields appear on separate rows (11 and 13), and there is no Password field at all. All displayed data fields are ASKIP (protected, read-only).

---

## 6. Field Definitions

### 6.1 Header Fields (Rows 1–2)

| Field Name | Row | Col | Len | Color  | Attributes      | Purpose                         |
|-----------|-----|-----|-----|--------|-----------------|---------------------------------|
| (literal) | 1   | 1   | 5   | BLUE   | ASKIP,NORM      | 'Tran:'                         |
| TRNNAME   | 1   | 7   | 4   | BLUE   | ASKIP,FSET,NORM | Transaction ID output (CU03)   |
| TITLE01   | 1   | 21  | 40  | YELLOW | ASKIP,FSET,NORM | Title line 1                    |
| (literal) | 1   | 65  | 5   | BLUE   | ASKIP,NORM      | 'Date:'                         |
| CURDATE   | 1   | 71  | 8   | BLUE   | ASKIP,FSET,NORM | Current date MM/DD/YY          |
| (literal) | 2   | 1   | 5   | BLUE   | ASKIP,NORM      | 'Prog:'                         |
| PGMNAME   | 2   | 7   | 8   | BLUE   | ASKIP,FSET,NORM | Program name output (COUSR03C) |
| TITLE02   | 2   | 21  | 40  | YELLOW | ASKIP,FSET,NORM | Title line 2                    |
| (literal) | 2   | 65  | 5   | BLUE   | ASKIP,NORM      | 'Time:'                         |
| CURTIME   | 2   | 71  | 8   | BLUE   | ASKIP,FSET,NORM | Current time HH:MM:SS          |

### 6.2 Screen Title (Row 4)

| Field Name | Row | Col | Len | Color   | Attributes | Content       |
|-----------|-----|-----|-----|---------|------------|---------------|
| (literal) | 4   | 35  | 11  | NEUTRAL | ASKIP,BRT  | 'Delete User' |

### 6.3 User ID Lookup Field (Row 6)

| Field Name | Row | Col | Len | Color | Attributes          | Highlight | Purpose                               |
|-----------|-----|-----|-----|-------|---------------------|-----------|---------------------------------------|
| (literal) | 6   | 6   | 14  | GREEN | ASKIP,NORM          | None      | 'Enter User ID:'                      |
| USRIDIN   | 6   | 21  | 8   | GREEN | FSET,IC,NORM,UNPROT | UNDERLINE | User ID entry — cursor home (IC)     |
| (stopper) | 6   | 30  | 0   | —     | ASKIP,NORM          | —         | Field terminator                      |

### 6.4 Visual Separator (Row 8)

| Row | Col | Len | Color  | Content                                                      |
|-----|-----|-----|--------|--------------------------------------------------------------|
| 8   | 6   | 70  | YELLOW | 70 asterisks — visual separator (no BMS field name)          |

Identical to COUSR02 screen.

### 6.5 Read-Only Data Display Fields (Rows 11–15)

These fields are **ASKIP** (protected) — they cannot be modified by the operator. COUSR03C populates them from the read USRSEC record for confirmation purposes only.

#### Row 11 — First Name

| Field Name | Row | Col | Len | Color     | Attributes        | Highlight | Purpose                              |
|-----------|-----|-----|-----|-----------|-------------------|-----------|--------------------------------------|
| (literal) | 11  | 6   | 11  | TURQUOISE | ASKIP,NORM        | None      | 'First Name:'                        |
| FNAME     | 11  | 18  | 20  | BLUE      | ASKIP,FSET,NORM   | UNDERLINE | First name — protected display only  |
| (stopper) | 11  | 39  | 0   | —         | ASKIP,NORM        | —         | Field terminator                     |

#### Row 13 — Last Name

| Field Name | Row | Col | Len | Color     | Attributes        | Highlight | Purpose                              |
|-----------|-----|-----|-----|-----------|-------------------|-----------|--------------------------------------|
| (literal) | 13  | 6   | 10  | TURQUOISE | ASKIP,NORM        | None      | 'Last Name:'                         |
| LNAME     | 13  | 18  | 20  | BLUE      | ASKIP,FSET,NORM   | UNDERLINE | Last name — protected display only   |
| (stopper) | 13  | 39  | 0   | GREEN     | ASKIP,NORM        | —         | Field terminator                     |

#### Row 15 — User Type

| Field Name | Row | Col | Len | Color     | Attributes        | Highlight | Purpose                              |
|-----------|-----|-----|-----|-----------|-------------------|-----------|--------------------------------------|
| (literal) | 15  | 6   | 11  | TURQUOISE | ASKIP,NORM        | None      | 'User Type: '                        |
| USRTYPE   | 15  | 17  | 1   | BLUE      | ASKIP,FSET,NORM   | UNDERLINE | User type code — protected display   |
| (literal) | 15  | 19  | 17  | BLUE      | ASKIP,NORM        | None      | '(A=Admin, U=User)' hint             |

**Key difference from COUSR02:** In COUSR03, FNAME, LNAME, and USRTYPE all have ATTRB=ASKIP,FSET,NORM (protected) rather than FSET,NORM,UNPROT (editable). This prevents the operator from modifying the displayed record before deletion.

**No PASSWD field:** COUSR03 does not define a PASSWD field. The password is read from USRSEC into SEC-USR-DATA by the program but is not displayed on screen.

### 6.6 Message and Function Key Fields (Rows 23–24)

| Field Name | Row | Col | Len | Color  | Attributes      | Purpose                                        |
|-----------|-----|-----|-----|--------|-----------------|------------------------------------------------|
| ERRMSG    | 23  | 1   | 78  | RED    | ASKIP,BRT,FSET  | Error/status/confirmation message              |
| (literal) | 24  | 1   | 58  | YELLOW | ASKIP,NORM      | 'ENTER=Fetch  F3=Back  F4=Clear  F5=Delete'   |

Note: The function key line (BMS line 148) lists only ENTER, F3, F4, and F5 — no F12. COUSR03C does handle DFHPF12 in MAIN-PARA (line 124) but it is not advertised on the screen.

---

## 7. Symbolic Map Structure (COUSR03.CPY — app/cpy-bms/COUSR03.CPY)

**COUSR3AI (Input, lines 17–84):**

| Symbolic Field | PIC        | Length | BMS Field  |
|----------------|------------|--------|------------|
| USRIDINL       | COMP S9(4) | 2      | USRIDIN cursor/length |
| USRIDINI       | X(8)       | 8      | USRIDIN data |
| FNAMEL         | COMP S9(4) | 2      | FNAME cursor control |
| FNAMEI         | X(20)      | 20     | FNAME data (ASKIP — not editable) |
| LNAMEL         | COMP S9(4) | 2      | LNAME cursor control |
| LNAMEI         | X(20)      | 20     | LNAME data (ASKIP) |
| USRTYPEL       | COMP S9(4) | 2      | USRTYPE cursor control |
| USRTYPEI       | X(1)       | 1      | USRTYPE data (ASKIP) |
| ERRMSGL        | COMP S9(4) | 2      | ERRMSG cursor control |
| ERRMSGI        | X(78)      | 78     | ERRMSG data |

Plus header fields: TRNNAMEL/I, TITLE01L/I, CURDATEL/I, PGMNAMEL/I, TITLE02L/I, CURTIMEL/I.

Note: No PASSWDL/PASSWDI fields are generated — the BMS map has no PASSWD field.

**COUSR3AO (Output, REDEFINES COUSR3AI, lines 85–152):**
Exposes C/P/H/V/O variants for USRIDIN, FNAME, LNAME, USRTYPE, ERRMSG, and all header fields.

---

## 8. Structural Comparison: COUSR02 vs COUSR03 Data Zone

| Aspect              | COUSR02 (Update)                            | COUSR03 (Delete)                            |
|---------------------|---------------------------------------------|---------------------------------------------|
| First Name field    | Row 11, col 18, UNPROT (editable)           | Row 11, col 18, ASKIP (read-only)           |
| Last Name field     | Row 11, col 56 (same row as First Name)     | Row 13, col 18 (separate row)              |
| Password field      | Row 13, DRK, UNPROT (editable)              | Not present                                 |
| User Type field     | Row 15, UNPROT (editable)                   | Row 15, ASKIP (read-only)                  |
| Data field color    | GREEN (editable visual cue)                 | BLUE (display visual cue)                  |
| F12 key             | Advertised as 'Cancel' on Row 24            | Not advertised (but program handles it)    |
| F5 key label        | 'Save'                                      | 'Delete'                                   |

---

## 9. Field-to-Program Data Mapping

| BMS Field | Sym In     | Sym Out    | COUSR03C Program Usage                                         |
|-----------|------------|------------|----------------------------------------------------------------|
| USRIDIN   | USRIDINI   | USRIDINO   | Input: User ID for VSAM key lookup; pre-set from COMMAREA    |
| FNAME     | FNAMEI     | FNAMEO     | Output only: populated from SEC-USR-FNAME for display        |
| LNAME     | LNAMEI     | LNAMEO     | Output only: populated from SEC-USR-LNAME for display        |
| USRTYPE   | USRTYPEI   | USRTYPEO   | Output only: populated from SEC-USR-TYPE for display         |
| ERRMSG    | ERRMSGI    | ERRMSGO    | Messages: ERRMSGC colored DFHNEUTR or DFHGREEN               |
| TRNNAME   | —          | TRNNAMEO   | 'CU03'                                                         |
| PGMNAME   | —          | PGMNAMEO   | 'COUSR03C'                                                     |
| TITLE01   | —          | TITLE01O   | From CCDA-TITLE01                                              |
| TITLE02   | —          | TITLE02O   | From CCDA-TITLE02                                              |
| CURDATE   | —          | CURDATEO   | MM/DD/YY                                                       |
| CURTIME   | —          | CURTIMEO   | HH:MM:SS                                                       |

---

## 10. Navigation / Function Key Definitions

As shown in static label Row 24 (BMS lines 144–148):

| Key   | Advertised | COUSR03C Handling                                               |
|-------|------------|-----------------------------------------------------------------|
| ENTER | Fetch      | PROCESS-ENTER-KEY: read user by USRIDIN and display (read-only) |
| F3    | Back       | RETURN-TO-PREV-SCREEN (no delete)                              |
| F4    | Clear      | CLEAR-CURRENT-SCREEN: blank all fields                         |
| F5    | Delete     | DELETE-USER-INFO: READ UPDATE then DELETE                      |
| F12   | (unlisted) | RETURN-TO-PREV-SCREEN to COADM01C — handled but not shown     |

---

## 11. Design Notes and Observations

- **All data display fields are ASKIP.** This is the fundamental design difference from COUSR02. The operator's only action after fetching a record is to confirm (PF5) or cancel (PF3/PF12). No modification of the displayed data is possible.
- **No password display.** The password column is absent from this screen. This is intentional — the password has no relevance to a delete confirmation and hiding it reduces inadvertent exposure.
- **BLUE data field color** (vs GREEN in COUSR02) provides a visual cue that the fields are read-only, leveraging the 3270 color convention where green fields are typically editable.
- **Layout difference from COUSR02:** COUSR02 places First Name and Last Name on the same row (11) in a two-column layout. COUSR03 places them on separate rows (11 and 13) in a single-column layout, which is a simpler arrangement consistent with the read-only nature of the screen.
- **FSET on ASKIP fields:** FNAME, LNAME, and USRTYPE carry ATTRB=ASKIP,FSET,NORM. The FSET ensures that data placed into these output fields by the program is always retransmitted back in the input stream. However, since these fields are ASKIP, the operator cannot change their values — FSET here simply ensures the displayed values are available to the program on receive (allowing COUSR03C to read back what was last displayed, though the program does not use these returned values for delete logic).
- **F12 discrepancy:** COUSR03C handles DFHPF12 (line 124, MAIN-PARA) but Row 24 of the screen does not list it. This means a user pressing F12 will get the correct "cancel" behavior but the key is undocumented on screen.
- **USRIDIN IC attribute:** Cursor automatically positions on the User ID field, consistent with the primary workflow being "type a User ID, press ENTER."
