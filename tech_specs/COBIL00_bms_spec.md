# Technical Specification: COBIL00 — Bill Payment BMS Mapset

## 1. Executive Summary

COBIL00 is a BMS (Basic Mapping Support) mapset definition for the CardDemo bill payment screen. It defines a single map, COBIL0A, rendered on a 24-row by 80-column 3270 terminal screen. The mapset supports CICS transaction CB00 and is used exclusively by program COBIL00C. The generated symbolic description copybook is COBIL00.CPY (located in app/cpy-bms/), which defines the COBIL0AI (input) and COBIL0AO (output) data structures referenced throughout COBIL00C.

Source file: `app/bms/COBIL00.bms`
Generated copybook: `app/cpy-bms/COBIL00.CPY`
Version stamp: `CardDemo_v1.0-70-g193b394-123 Date: 2022-08-22 17:02:42 CDT`

---

## 2. Artifact Inventory

| Artifact | Type | Location | Role |
|---|---|---|---|
| COBIL00.bms | BMS Source | app/bms/ | Mapset definition |
| COBIL00.CPY | BMS-generated Copybook | app/cpy-bms/ | Symbolic map structures COBIL0AI/O |
| COBIL00C.cbl | CICS COBOL Program | app/cbl/ | Consuming program |

---

## 3. Mapset-Level Definition (DFHMSD)

Source: COBIL00.bms lines 19–25

| Parameter | Value | Meaning |
|---|---|---|
| Name | COBIL00 | Mapset name |
| CTRL | (ALARM,FREEKB) | Sound alarm on send; free keyboard after send |
| EXTATT | YES | Extended attributes enabled |
| LANG | COBOL | Generate COBOL copybook |
| MODE | INOUT | Mapset used for both input and output |
| STORAGE | AUTO | Storage for symbolic map allocated automatically |
| TIOAPFX | YES | 12-byte TIOA prefix included in symbolic map |
| TYPE | &&SYSPARM | Map type determined at assembly time (MAP or DSECT) |

---

## 4. Map Definition: COBIL0A (DFHMDI)

Source: COBIL00.bms line 26–28

| Parameter | Value | Meaning |
|---|---|---|
| Name | COBIL0A | Map name referenced in EXEC CICS SEND/RECEIVE |
| COLUMN | 1 | Start at column 1 |
| LINE | 1 | Start at line 1 |
| SIZE | (24,80) | Full 24-row by 80-column screen |

---

## 5. Screen Layout

```
Row  Col  1         2         3         4         5         6         7         8
         12345678901234567890123456789012345678901234567890123456789012345678901234567890
Row  1:  Tran: TTTT         [        TITLE01 (40)          ]  Date: MM/DD/YY
Row  2:  Prog: PPPPPPPP     [        TITLE02 (40)          ]  Time: HH:MM:SS
Row  3:  (blank)
Row  4:  (blank)          (blank)       Bill Payment          (blank)
Row  5:  (blank)
Row  6:       Enter Acct ID: [AAAAAAAAAAA]
Row  7:  (blank)
Row  8:       [--------------------------------------------------------------------]
Row  9:  (blank)
Row 10:  (blank)
Row 11:       Your current balance is:  [BBBBBBBBBBBBBB]
Row 12:  (blank)
Row 13:  (blank)
Row 14:  (blank)
Row 15:       Do you want to pay your balance now. Please confirm:  [C] (Y/N)
Row 16:  (blank)
Row 17:  (blank)
Row 18:  (blank)
Row 19:  (blank)
Row 20:  (blank)
Row 21:  (blank)
Row 22:  (blank)
Row 23:  [ERRMSG - 78 chars - RED]
Row 24:  ENTER=Continue  F3=Back  F4=Clear
```

Legend: `[ ]` = unprotected (input-capable) field; `( )` = static/protected label

---

## 6. Field Inventory

All field entries sourced from COBIL00.bms and confirmed against COBIL00.CPY.

### 6.1 Static (ASKIP) Label Fields — No symbolic names

| Row | Col | Length | Color | Content | Notes |
|---|---|---|---|---|---|
| 1 | 1 | 5 | BLUE | 'Tran:' | Label for transaction ID |
| 1 | 65 | 5 | BLUE | 'Date:' | Label for current date |
| 2 | 1 | 5 | BLUE | 'Prog:' | Label for program name |
| 2 | 65 | 5 | BLUE | 'Time:' | Label for current time |
| 4 | 35 | 12 | NEUTRAL | 'Bill Payment' | Screen title; ATTRB=(ASKIP,BRT) |
| 6 | 6 | 14 | GREEN | 'Enter Acct ID:' | Prompt for account ID field |
| 8 | 6 | 70 | YELLOW | '---...---' (70 dashes) | Visual separator rule |
| 11 | 6 | 25 | TURQUOISE | 'Your current balance is: ' | Label for balance display |
| 15 | 6 | 53 | TURQUOISE | 'Do you want to pay your balance now. Please confirm: ' | Confirmation prompt |
| 15 | 63 | 5 | NEUTRAL | '(Y/N)' | Valid values hint |
| 24 | 1 | 33 | YELLOW | 'ENTER=Continue  F3=Back  F4=Clear' | Key legend |

### 6.2 Named Symbolic Fields — Header Area

These fields are output-only (ASKIP, FSET) set by COBIL00C POPULATE-HEADER-INFO paragraph.

| BMS Name | Symbolic Name (I/O) | Row | Col | Length | Color | Attr | Purpose |
|---|---|---|---|---|---|---|---|
| TRNNAME | TRNNAMEI / TRNNAMEO | 1 | 7 | 4 | BLUE | ASKIP,FSET,NORM | Transaction ID (CB00) |
| TITLE01 | TITLE01I / TITLE01O | 1 | 21 | 40 | YELLOW | ASKIP,FSET,NORM | Application title line 1 |
| CURDATE | CURDATEI / CURDATEO | 1 | 71 | 8 | BLUE | ASKIP,FSET,NORM | Current date (mm/dd/yy) |
| PGMNAME | PGMNAMEI / PGMNAMEO | 2 | 7 | 8 | BLUE | ASKIP,FSET,NORM | Program name (COBIL00C) |
| TITLE02 | TITLE02I / TITLE02O | 2 | 21 | 40 | YELLOW | ASKIP,FSET,NORM | Application title line 2 |
| CURTIME | CURTIMEI / CURTIMEO | 2 | 71 | 8 | BLUE | ASKIP,FSET,NORM | Current time (hh:mm:ss) |

### 6.3 Named Symbolic Fields — Input / Data Area

| BMS Name | Symbolic Name (I/O) | Row | Col | Length | Color | Attr | HILIGHT | Purpose |
|---|---|---|---|---|---|---|---|---|
| ACTIDIN | ACTIDINI / ACTIDINO | 6 | 21 | 11 | GREEN | FSET,IC,NORM,UNPROT | UNDERLINE | Account ID entry (11 chars); IC = initial cursor |
| CURBAL | CURBALI / CURBALO | 11 | 32 | 14 | BLUE | ASKIP,FSET,NORM | — | Current balance display (output only, protected) |
| CONFIRM | CONFIRMI / CONFIRMO | 15 | 60 | 1 | GREEN | FSET,NORM,UNPROT | UNDERLINE | Y/N confirmation entry |
| ERRMSG | ERRMSGI / ERRMSGO | 23 | 1 | 78 | RED | ASKIP,BRT,FSET | — | Error / status message display |

### 6.4 Stopper Fields (LENGTH=0)

Stopper fields immediately follow each unprotected field to terminate data entry:

| After Field | Row | Col |
|---|---|---|
| After ACTIDIN | 6 | 33 |
| After CURBAL | 11 | 47 |
| After CONFIRM | 15 | 62 |

---

## 7. Symbolic Map Structures (from COBIL00.CPY)

Source: app/cpy-bms/COBIL00.CPY

### 7.1 Input Structure: COBIL0AI (lines 17–78)

```cobol
01  COBIL0AI.
    02  FILLER       PIC X(12).          -- TIOA prefix
    -- Per named field (L=length, F=flag, A=attribute, I=data):
    02  TRNNAMEL     COMP PIC S9(4).
    02  TRNNAMEF     PICTURE X.          -- modified data tag
    02  FILLER REDEFINES TRNNAMEF.
      03 TRNNAMEA    PICTURE X.          -- attribute byte
    02  FILLER       PICTURE X(4).       -- reserved
    02  TRNNAMEI     PIC X(4).           -- data value
    [... same pattern for TITLE01, CURDATE, PGMNAME, TITLE02, CURTIME ...]
    02  ACTIDINL     COMP PIC S9(4).     -- length / cursor control (-1 = set cursor)
    02  ACTIDINF     PICTURE X.
    02  FILLER REDEFINES ACTIDINF.
      03 ACTIDINA    PICTURE X.
    02  FILLER       PICTURE X(4).
    02  ACTIDINI     PIC X(11).          -- Account ID entered by user
    02  CURBALL      COMP PIC S9(4).
    ...
    02  CURBALI      PIC X(14).          -- Balance display
    02  CONFIRML     COMP PIC S9(4).
    ...
    02  CONFIRMI     PIC X(1).           -- Y/N confirmation
    02  ERRMSGL      COMP PIC S9(4).
    ...
    02  ERRMSGI      PIC X(78).          -- Error message input (rarely used)
```

### 7.2 Output Structure: COBIL0AO (lines 79–141)

COBIL0AO REDEFINES COBIL0AI. Output fields have extended attribute bytes C (color), P (programmed symbols), H (highlight), V (validation) preceding the data field:

| Field Suffix | Meaning |
|---|---|
| C (e.g., ERRMSGC) | Color attribute byte — set to DFHGREEN for success |
| P (e.g., ERRMSGP) | Programmed symbols |
| H (e.g., ERRMSGH) | Highlight attribute |
| V (e.g., ERRMSGV) | Validation attribute |
| O (e.g., ERRMSGO) | Output data value |

COBIL00C sets ERRMSGC to DFHGREEN (line 526) to display the success message in green rather than the default red.

---

## 8. Attribute Byte Reference

| BMS Attribute | Meaning | Fields Using It |
|---|---|---|
| ASKIP | Auto-skip; protected from user input | All label and output fields |
| UNPROT | Unprotected; user can type | ACTIDIN, CONFIRM |
| NORM | Normal intensity | Most fields |
| BRT | Bright / high intensity | ERRMSG, 'Bill Payment' title |
| FSET | Field set; data transmitted even if unmodified | All named fields |
| IC | Initial cursor position | ACTIDIN (first entry) |
| HILIGHT=UNDERLINE | Field appears underlined | ACTIDIN, CONFIRM |

---

## 9. Inter-Screen Navigation

| Key | Action Taken by COBIL00C |
|---|---|
| ENTER | Process account ID, display balance, or execute payment |
| PF3 | Return to calling menu (COMEN01C or CDEMO-FROM-PROGRAM) |
| PF4 | Clear all screen fields, reset to initial state |
| Any other key | Display 'Invalid key pressed...' error in ERRMSG |

---

## 10. Screen Interaction Sequence

1. First display: ACTIDIN has initial cursor (IC attribute). CURBAL and CONFIRM are blank.
2. User enters Account ID, presses ENTER.
3. Program retrieves account, populates CURBAL with formatted balance. CONFIRM field is shown with prompt. Cursor moves to CONFIRM.
4. User enters 'Y' (confirm) or 'N' (cancel), presses ENTER.
5. On 'Y': payment is processed. Success message in green appears in ERRMSG row 23. All data fields cleared (INITIALIZE-ALL-FIELDS).
6. On 'N': screen is cleared.
7. Error conditions: red message in ERRMSG; cursor returns to offending field.

---

## 11. Mapset Termination

Source: COBIL00.bms line 136
```
DFHMSD TYPE=FINAL
END
```
Standard BMS mapset termination macro.

---

## 12. Open Questions and Gaps

1. **CURBAL display format**: The CURBAL field is defined as PIC X(14) in the symbolic map (COBIL00.CPY line 66) and COBIL00C moves the display-formatted `WS-CURR-BAL` (PIC +9999999999.99) into it. The PIC clause allows for a sign indicator and up to 13 digits/decimal. Alignment depends on the MOVE statement formatting.
2. **CONFIRM field on first pass**: The CONFIRM field (POS=(15,60)) is always visible on the screen from first display, but COBIL00C only checks it after the balance has been looked up. On the very first ENTER, if the user has already typed 'Y' in CONFIRM, the program will proceed directly to payment without a separate balance-display step. This is an intended shortcut for pre-populated invocations via CDEMO-CB00-TRN-SELECTED.
3. **ACTIDIN length vs ACCT-ID**: ACTIDINI is PIC X(11), matching ACCT-ID which is 9(11) — correct sizing. However no numeric validation of the field is performed in BMS (UNPROT, not NUM), leaving format validation entirely to the program.
