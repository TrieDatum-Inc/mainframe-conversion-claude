# COTRN00 — Transaction List Screen Technical Specification

## 1. Screen Overview

**Purpose:** Displays a paginated scrollable list of credit card transactions. Up to 10 transaction records are displayed per page. The operator can search by Transaction ID, scroll forward/backward through the list, and select a transaction for detailed view by typing `S` in the selection field for that row.

**Driving Program:** COTRN00C (Transaction List program)

**Source File:** `/app/bms/COTRN00.bms`
**Copybook:** `/app/cpy-bms/COTRN00.CPY`

---

## 2. Map/Mapset Definition

| Attribute    | Value             |
|--------------|-------------------|
| MAPSET name  | COTRN00           |
| MAP name     | COTRN0A           |
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
Row4:                               List Transactions           Page:[PAGENUM-]
Row5:
Row6:     Search Tran ID:[TRNIDIN-----------]
Row7:
Row8:  Sel  Transaction ID      Date       Description               Amount
Row9:  ---  ----------------  --------  --------------------------  ------------
Row10: [S1] [TRNID01--------] [TDATE01] [TDESC01-----------------] [TAMT001----]
Row11: [S2] [TRNID02--------] [TDATE02] [TDESC02-----------------] [TAMT002----]
Row12: [S3] [TRNID03--------] [TDATE03] [TDESC03-----------------] [TAMT003----]
Row13: [S4] [TRNID04--------] [TDATE04] [TDESC04-----------------] [TAMT004----]
Row14: [S5] [TRNID05--------] [TDATE05] [TDESC05-----------------] [TAMT005----]
Row15: [S6] [TRNID06--------] [TDATE06] [TDESC06-----------------] [TAMT006----]
Row16: [S7] [TRNID07--------] [TDATE07] [TDESC07-----------------] [TAMT007----]
Row17: [S8] [TRNID08--------] [TDATE08] [TDESC08-----------------] [TAMT008----]
Row18: [S9] [TRNID09--------] [TDATE09] [TDESC09-----------------] [TAMT009----]
Row19: [S0] [TRNID10--------] [TDATE10] [TDESC10-----------------] [TAMT010----]
Row20:
Row21:        Type 'S' to View Transaction details from the list
Row22:
Row23: [---------------------------ERRMSG------------------------------------]
Row24: ENTER=Continue  F3=Back  F7=Backward  F8=Forward
```

---

## 4. Field Definitions

### Header Fields (rows 1–2)

| Field Name | Row | Col | Length | ATTRB           | Color  | I/O | Notes                         |
|------------|-----|-----|--------|-----------------|--------|-----|-------------------------------|
| (label)    | 1   | 1   | 5      | ASKIP,NORM      | BLUE   | O   | `Tran:`                       |
| TRNNAME    | 1   | 7   | 4      | ASKIP,FSET,NORM | BLUE   | O   | Transaction name               |
| TITLE01    | 1   | 21  | 40     | ASKIP,FSET,NORM | YELLOW | O   | Title line 1                   |
| (label)    | 1   | 65  | 5      | ASKIP,NORM      | BLUE   | O   | `Date:`                        |
| CURDATE    | 1   | 71  | 8      | ASKIP,FSET,NORM | BLUE   | O   | Current date                   |
| (label)    | 2   | 1   | 5      | ASKIP,NORM      | BLUE   | O   | `Prog:`                        |
| PGMNAME    | 2   | 7   | 8      | ASKIP,FSET,NORM | BLUE   | O   | Program name                   |
| TITLE02    | 2   | 21  | 40     | ASKIP,FSET,NORM | YELLOW | O   | Title line 2                   |
| (label)    | 2   | 65  | 5      | ASKIP,NORM      | BLUE   | O   | `Time:`                        |
| CURTIME    | 2   | 71  | 8      | ASKIP,FSET,NORM | BLUE   | O   | Current time                   |

### Screen Title and Page Number (row 4)

| Field Name | Row | Col | Length | ATTRB           | Color     | I/O | Notes                     |
|------------|-----|-----|--------|-----------------|-----------|-----|---------------------------|
| (title)    | 4   | 30  | 17     | ASKIP,BRT       | NEUTRAL   | O   | `List Transactions`       |
| (label)    | 4   | 65  | 5      | ASKIP,BRT       | TURQUOISE | O   | `Page:`                   |
| PAGENUM    | 4   | 71  | 8      | ASKIP,FSET,NORM | BLUE      | O   | Current page number; init space |

### Search Field (row 6)

| Field Name | Row | Col | Length | ATTRB          | Color     | Hilight   | I/O   | Notes                                    |
|------------|-----|-----|--------|----------------|-----------|-----------|-------|------------------------------------------|
| (label)    | 6   | 5   | 15     | ASKIP,NORM     | TURQUOISE | —         | O     | `Search Tran ID:`                        |
| TRNIDIN    | 6   | 21  | 16     | FSET,NORM,UNPROT | GREEN   | UNDERLINE | Input | Transaction ID search key                |
| (stopper)  | 6   | 38  | 0      | ASKIP,NORM     | —         | —         | —     | Tab stop                                 |

### Column Headers (rows 8–9)

| Row | Col | Length | Content                    | Color   |
|-----|-----|--------|----------------------------|---------|
| 8   | 2   | 3      | `Sel`                      | NEUTRAL |
| 8   | 8   | 16     | ` Transaction ID `         | NEUTRAL |
| 8   | 27  | 8      | `  Date  `                 | NEUTRAL |
| 8   | 38  | 26     | `     Description          ` | NEUTRAL |
| 8   | 67  | 12     | `   Amount   `             | NEUTRAL |
| 9   | 2   | 3      | `---`                      | NEUTRAL |
| 9   | 8   | 16     | `----------------`         | NEUTRAL |
| 9   | 27  | 8      | `--------`                 | NEUTRAL |
| 9   | 38  | 26     | `--------------------------` | NEUTRAL |
| 9   | 67  | 12     | `------------`             | NEUTRAL |

### List Rows (rows 10–19) — 10 transaction slots

Each row (n = 01–10) follows an identical pattern:

| Field Name | Row  | Col | Length | ATTRB               | Color | Hilight   | I/O   | Notes                                    |
|------------|------|-----|--------|---------------------|-------|-----------|-------|------------------------------------------|
| SEL000n    | 9+n  | 3   | 1      | FSET,NORM,UNPROT    | GREEN | UNDERLINE | Input | Selection; type `S` to select; init space |
| (stopper)  | 9+n  | 5   | 0      | ASKIP,NORM          | —     | —         | —     | Tab stop after selector                  |
| TRNIDnn    | 9+n  | 8   | 16     | ASKIP,FSET,NORM     | BLUE  | —         | O     | Transaction ID; init space               |
| TDATEnn    | 9+n  | 27  | 8      | ASKIP,FSET,NORM     | BLUE  | —         | O     | Transaction date; init space             |
| TDESCnn    | 9+n  | 38  | 26     | ASKIP,FSET,NORM     | BLUE  | —         | O     | Transaction description; init space      |
| TAMTnnn    | 9+n  | 67  | 12     | ASKIP,FSET,NORM     | BLUE  | —         | O     | Transaction amount; init space           |

Complete field name table:

| Row | Selector | Tran ID  | Date    | Description | Amount  |
|-----|----------|----------|---------|-------------|---------|
| 10  | SEL0001  | TRNID01  | TDATE01 | TDESC01     | TAMT001 |
| 11  | SEL0002  | TRNID02  | TDATE02 | TDESC02     | TAMT002 |
| 12  | SEL0003  | TRNID03  | TDATE03 | TDESC03     | TAMT003 |
| 13  | SEL0004  | TRNID04  | TDATE04 | TDESC04     | TAMT004 |
| 14  | SEL0005  | TRNID05  | TDATE05 | TDESC05     | TAMT005 |
| 15  | SEL0006  | TRNID06  | TDATE06 | TDESC06     | TAMT006 |
| 16  | SEL0007  | TRNID07  | TDATE07 | TDESC07     | TAMT007 |
| 17  | SEL0008  | TRNID08  | TDATE08 | TDESC08     | TAMT008 |
| 18  | SEL0009  | TRNID09  | TDATE09 | TDESC09     | TAMT009 |
| 19  | SEL0010  | TRNID10  | TDATE10 | TDESC10     | TAMT010 |

**TRNID/TDATE/TDESC/TAMT fields:** ASKIP (protected), so they cannot be directly modified by the operator. FSET ensures their populated values are retransmitted on RECEIVE MAP for use in selection processing.

### Instructions and Navigation (rows 21–24)

| Field Name | Row | Col | Length | ATTRB          | Color     | I/O | Notes                                              |
|------------|-----|-----|--------|----------------|-----------|-----|----------------------------------------------------|
| (instruct) | 21  | 12  | 50     | ASKIP,BRT      | NEUTRAL   | O   | `Type 'S' to View Transaction details from the list` |
| ERRMSG     | 23  | 1   | 78     | ASKIP,BRT,FSET | RED       | O   | Error message                                      |
| (fkeys)    | 24  | 1   | 48     | ASKIP,NORM     | YELLOW    | O   | `ENTER=Continue  F3=Back  F7=Backward  F8=Forward` |

---

## 5. Screen Navigation

| Key   | Action                                                                          |
|-------|---------------------------------------------------------------------------------|
| ENTER | Process selection (if `S` in any SEL field) or refresh list with search criteria |
| PF3   | Return to previous screen (main menu)                                           |
| PF7   | Page backward through the transaction list                                      |
| PF8   | Page forward through the transaction list                                       |

---

## 6. Selection Mechanic

The operator types `S` into one of the SEL0001–SEL0010 fields and presses ENTER. The program:
1. Reads all 10 SEL fields from the input map
2. Identifies which row has a non-blank selector
3. Uses the corresponding TRNID field value to navigate to COTRN01 (Transaction View)

---

## 7. Validation Rules

| Field     | BMS Constraint          | Program-Level Validation                                 |
|-----------|-------------------------|----------------------------------------------------------|
| TRNIDIN   | Length=16, UNPROT, FSET | Optional search key; if provided filters the display list |
| SEL0001–10| Length=1, UNPROT, FSET  | Only `S` is a valid selector; only one row at a time     |

---

## 8. Related Screens

| Screen  | Mapset  | Relationship                                           |
|---------|---------|--------------------------------------------------------|
| COMEN01 | COMEN01 | Navigate FROM (transaction list menu option)           |
| COTRN01 | COTRN01 | Navigate TO (view details of selected transaction)     |
