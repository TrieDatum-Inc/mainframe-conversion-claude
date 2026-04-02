# Technical Specification: COCRDLI.BMS (BMS Mapset)

## 1. Mapset Overview

| Attribute        | Value                                         |
|------------------|-----------------------------------------------|
| Mapset Name      | COCRDLI                                       |
| Source File      | app/bms/COCRDLI.bms                           |
| Map Name         | CCRDLIA                                       |
| BMS Copybook     | app/cpy-bms/COCRDLI.CPY                       |
| Screen Title     | List Credit Cards                             |
| Screen Size      | 24 rows x 80 columns                          |
| MODE             | INOUT (used for both send and receive)        |
| STORAGE          | AUTO                                          |
| TIOAPFX          | YES (TIOABAR prefix required)                 |
| LANG             | COBOL                                         |
| Owning Program   | COCRDLIC.CBL (Transaction CCLI)               |
| Version Tag      | CardDemo_v1.0-70-g193b394-123                 |

### Purpose

This mapset defines the credit card list screen. It presents a paginated, scrollable list of up to 7 credit card records at a time. Each row shows a selection field, account number, card number, and active status. The user types 'S' to view detail or 'U' to update for exactly one row per submission. Optional account and card number filter fields are provided at the top.

---

## 2. Screen Layout (24 x 80)

```
Col:  1         2         3         4         5         6         7         8
      1234567890123456789012345678901234567890123456789012345678901234567890123456789 0

Row 1: Tran: CCLI                [TITLE01 - 40 chars yellow]       Date: mm/dd/yy
Row 2: Prog: COCRDLIC            [TITLE02 - 40 chars yellow]       Time: hh:mm:ss
Row 3: (blank)
Row 4:                               List Credit Cards              Page NNN
Row 5: (blank)
Row 6:                       Account Number    : [ACCTSID - 11 chars green underline]
Row 7:                       Credit Card Number: [CARDSID - 16 chars green underline]
Row 8: (blank)
Row 9:           Select    Account Number     Card Number      Active
Row10:           ------    ---------------    ---------------  --------
Row11:           [SEL1]    [ACCTNO1        ]  [CRDNUM1       ] [S1]
Row12:           [SEL2]    [ACCTNO2        ]  [CRDNUM2       ] [S2]
Row13:           [SEL3]    [ACCTNO3        ]  [CRDNUM3       ] [S3]
Row14:           [SEL4]    [ACCTNO4        ]  [CRDNUM4       ] [S4]
Row15:           [SEL5]    [ACCTNO5        ]  [CRDNUM5       ] [S5]
Row16:           [SEL6]    [ACCTNO6        ]  [CRDNUM6       ] [S6]
Row17:           [SEL7]    [ACCTNO7        ]  [CRDNUM7       ] [S7]
Row18: (blank)
Row19: (blank)
Row20:                    [INFOMSG - 45 chars neutral                        ]
Row21: (blank)
Row22: (blank)
Row23: [ERRMSG - 78 chars RED bright                                        ]
Row24:   F3=Exit F7=Backward  F8=Forward
```

Column positions for data rows (rows 11-17):
- Selection field: col 12, length 1
- Account Number: col 22, length 11
- Card Number: col 43, length 16
- Active Status: col 67, length 1

---

## 3. Field Inventory

### 3.1 Header Fields (Read-Only, ASKIP)

| Field Name | Row | Col | Length | Color    | Description                              |
|------------|-----|-----|--------|----------|------------------------------------------|
| (literal)  | 1   | 1   | 5      | BLUE     | 'Tran:' label                            |
| TRNNAME    | 1   | 7   | 4      | BLUE     | Transaction ID (populated by COCRDLIC)   |
| TITLE01    | 1   | 21  | 40     | YELLOW   | Application title line 1 (from COTTL01Y)|
| (literal)  | 1   | 65  | 5      | BLUE     | 'Date:' label                            |
| CURDATE    | 1   | 71  | 8      | BLUE     | Current date MM/DD/YY format             |
| (literal)  | 2   | 1   | 5      | BLUE     | 'Prog:' label                            |
| PGMNAME    | 2   | 7   | 8      | BLUE     | Program name (populated by COCRDLIC)     |
| TITLE02    | 2   | 21  | 40     | YELLOW   | Application title line 2 (from COTTL01Y)|
| (literal)  | 2   | 65  | 5      | BLUE     | 'Time:' label                            |
| CURTIME    | 2   | 71  | 8      | BLUE     | Current time HH:MM:SS format             |
| (literal)  | 4   | 31  | 17     | NEUTRAL  | 'List Credit Cards' screen title         |
| (literal)  | 4   | 70  | 5      | —        | 'Page ' label                            |
| PAGENO     | 4   | 76  | 3      | —        | Current page number                      |
| (literal)  | 9   | 10  | 10     | NEUTRAL  | 'Select    ' column header               |
| (literal)  | 9   | 21  | 14     | NEUTRAL  | 'Account Number' column header           |
| (literal)  | 9   | 45  | 13     | NEUTRAL  | ' Card Number ' column header            |
| (literal)  | 9   | 66  | 7      | NEUTRAL  | 'Active ' column header                  |
| (separator lines at row 10)                                                    |
| (literal)  | 24  | 1   | 34     | TURQUOISE| 'F3=Exit F7=Backward  F8=Forward' key guide|

### 3.2 Filter Entry Fields (User Input)

| Field Name | Row | Col | Length | Attribute          | Color | Description                                   |
|------------|-----|-----|--------|--------------------|-------|-----------------------------------------------|
| (label)    | 6   | 22  | 19     | ASKIP,NORM         | TURQUOISE | 'Account Number    :' label               |
| ACCTSID    | 6   | 44  | 11     | FSET,IC,NORM,UNPROT| GREEN, UNDERLINE | Account number filter; IC=initial cursor |
| (stopper)  | 6   | 56  | 0      | —                  | —     | Field stopper after ACCTSID                   |
| (label)    | 7   | 22  | 19     | ASKIP,NORM         | TURQUOISE | 'Credit Card Number:' label              |
| CARDSID    | 7   | 44  | 16     | FSET,NORM,UNPROT   | GREEN, UNDERLINE | Card number filter                       |
| (stopper)  | 7   | 61  | 0      | —                  | —     | Field stopper after CARDSID                   |

**Notes on filter fields**:
- Both ACCTSID and CARDSID are declared UNPROT in the BMS source (user can type in them).
- COCRDLIC dynamically overrides attributes: when coming from card list (self-loop), both may remain editable; the program can set DFHBMPRF (protected) or DFHBMFSE (unprotected) via ACCTSIDA/CARDSIDA attribute bytes in the symbolic map.
- ACCTSID has IC (initial cursor) so the terminal cursor lands here by default.
- FSET ensures the fields are always sent back to the host even if unchanged.

### 3.3 Data Rows (7 Repeating Row Groups)

Each of the 7 data rows (rows 11–17) has the same structure. Only row 1 differs slightly in the select field stopper definition:

| Field Pattern | Rows     | Col | Length | BMS Attribute       | Color   | Description                                      |
|---------------|----------|-----|--------|---------------------|---------|--------------------------------------------------|
| CRDSELn       | 11–17    | 12  | 1      | FSET,NORM,PROT (BMS default) | DEFAULT,UNDERLINE | Selection field: user types 'S' or 'U' |
| (stopper)     | 11–17    | 14  | 0      | —                   | —       | Stopper after CRDSELn                            |
| CRDSTPn       | 12–17    | 14  | 1      | ASKIP,DRK,FSET      | DEFAULT | Hidden stop field (rows 2-7 only; row 1 omitted) |
| ACCTNOn       | 11–17    | 22  | 11     | NORM,PROT           | DEFAULT | Account number (display only)                    |
| CRDNUMn       | 11–17    | 43  | 16     | NORM,PROT           | DEFAULT | Card number (display only)                       |
| CRDSTSn       | 11–17    | 67  | 1      | NORM,PROT           | DEFAULT | Active status Y/N (display only)                 |

**Notes on selection fields**:
- CRDSELn fields are defined PROT in BMS source. COCRDLIC overrides this dynamically: sets DFHBMFSE (unprotected) for populated rows with valid data, and DFHBMPRF (protected) for empty rows or when FLG-PROTECT-SELECT-ROWS-YES is set.
- CRDSTPn: A hidden dark stopper field present on rows 2–7. This is a common BMS technique to prevent tab-through from one row's selection field into the next row's data area. Row 1 uses a zero-length field instead.
- ACCTNOn, CRDNUMn, CRDSTSn are always PROT; they display data only.

### 3.4 Message Fields

| Field Name | Row | Col | Length | Attribute       | Color   | Description                                   |
|------------|-----|-----|--------|-----------------|---------|-----------------------------------------------|
| INFOMSG    | 20  | 19  | 45     | PROT            | NEUTRAL | Informational message (e.g., 'TYPE S FOR DETAIL...') |
| (stopper)  | 20  | 65  | 0      | —               | —       | Stopper after INFOMSG                         |
| ERRMSG     | 23  | 1   | 78     | ASKIP,BRT,FSET  | RED     | Error / status message (bright red)           |

---

## 4. BMS Symbolic Map Fields (from COCRDLI.CPY)

The BMS assembler generates two 01-level structures in COCRDLI.CPY:
- **CCRDLIAI** — input structure (fields suffixed I for input: ACCTSIDI, CARDSIDI, CRDSELnI, etc.)
- **CCRDLIAO** — output structure (REDEFINES CCRDLIAI; fields suffixed O, C, A, P, H, V for output attribute control)

Each field in the symbolic map has these sub-fields (using ACCTSID as example):
- `ACCTSIDL` — COMP PIC S9(4): field length as received (BMS auto-populated)
- `ACCTSIDA` — PIC X: attribute byte (can be set on output to change field characteristics)
- `ACCTSIDI` / `ACCTSIDO` — PIC X(11): the data value
- `ACCTSIDC` — PIC X: color extended attribute
- `ACCTSIDP` — PIC X: PS (programmatic symbols) extended attribute
- `ACCTSIDH` — PIC X: highlight extended attribute
- `ACCTSIDV` — PIC X: validation extended attribute

Full symbolic map field inventory:

| CCRDLIAI Input Field | PIC    | Description                         |
|----------------------|--------|-------------------------------------|
| TRNNAMEI             | X(4)   | Transaction name                    |
| TITLE01I             | X(40)  | Title line 1                        |
| CURDATEI             | X(8)   | Current date                        |
| PGMNAMEI             | X(8)   | Program name                        |
| TITLE02I             | X(40)  | Title line 2                        |
| CURTIMEI             | X(8)   | Current time                        |
| PAGENOI              | X(3)   | Page number                         |
| ACCTSIDI             | X(11)  | Account number filter input         |
| CARDSIDI             | X(16)  | Card number filter input            |
| CRDSEL1I–CRDSEL7I    | X(1) each | Selection codes for rows 1–7    |
| CRDSTP2I–CRDSTP7I    | X(1) each | Hidden stoppers (rows 2–7)      |
| ACCTNO1I–ACCTNO7I    | X(11) each| Account numbers for rows 1–7   |
| CRDNUM1I–CRDNUM7I    | X(16) each| Card numbers for rows 1–7      |
| CRDSTS1I–CRDSTS7I    | X(1) each | Active status for rows 1–7     |
| INFOMSGI             | X(45)  | Informational message input         |
| ERRMSGI              | X(78)  | Error message input                 |

---

## 5. Dynamic Attribute Control Used by COCRDLIC

COCRDLIC dynamically modifies these attribute/color bytes when building the output map:

| Field Attribute Modified    | When                                  | Value Set       | Effect                            |
|-----------------------------|---------------------------------------|-----------------|-----------------------------------|
| ACCTSIDA                    | Account filter error                  | DFHBMFSE        | Unprotected (user can re-enter)   |
| ACCTSIDA                    | Account filter valid (from self)      | DFHBMFSE        | Unprotected                       |
| CARDSIDA                    | Same as above                         | DFHBMFSE        | Unprotected                       |
| ACCTSIDC                    | Account filter error                  | DFHRED          | Red color                         |
| CARDSIDC                    | Card filter error                     | DFHRED          | Red color                         |
| ACCTSIDL                    | Account error (cursor here)           | -1              | Positions cursor                  |
| CARDSIDL                    | Card error (cursor here)              | -1              | Positions cursor                  |
| CRDSELnA (rows 1–7)         | Row empty or protect flag             | DFHBMPRF        | Protected (no input allowed)      |
| CRDSELnA (rows 1–7)         | Row populated, no error               | DFHBMFSE        | Unprotected (user can type S/U)   |
| CRDSELnC (rows 1–7)         | Row selection error                   | DFHRED          | Red color on selection field      |
| INFOMSGC                    | No message                            | DFHBMDAR        | Dark (invisible)                  |
| INFOMSGC                    | Message present                       | DFHNEUTR        | Neutral (visible)                 |

---

## 6. Transaction Flow

This mapset is used exclusively within transaction CCLI (COCRDLIC). It is sent and received as part of the CICS RETURN pseudo-conversational loop.

```
Terminal User                CICS / COCRDLIC
     |                            |
     |-- enter CCLI ------------> |
     |                            | SEND MAP(CCRDLIA) -- display list
     |<-- screen displayed -------|
     |-- type filters, press key->|
     |                            | RECEIVE MAP(CCRDLIA)
     |                            | validate, browse CARDDAT
     |                            | SEND MAP(CCRDLIA) -- updated list
     |<-- updated list ---------- |
     |-- type S or U, press ENTER>|
     |                            | RECEIVE MAP(CCRDLIA)
     |                            | XCTL to COCRDSLC or COCRDUPC
```

---

## 7. Key Design Notes

1. **7-row page size**: The BMS mapset defines exactly 7 selection rows (CRDSEL1–CRDSEL7). The COCRDLIC constant WS-MAX-SCREEN-LINES = 7 matches this exactly.

2. **Row 1 stopper asymmetry**: Row 1 (CRDSEL1) uses a zero-length DFHMDF stopper at col 14 without a separate DRK field. Rows 2–7 each have an additional CRDSTP field (ASKIP,DRK,FSET) at col 14 to prevent tabbing into the row's data area. This is intentional design — row 1 is the primary landing field.

3. **FSET on CRDSEL fields**: The FSET attribute on the selection fields ensures their content is always transmitted back to the host on ENTER even if the user did not touch them, which is needed so COCRDLIC can read all 7 selection positions.

4. **GREEN color on filter fields**: ACCTSID and CARDSID have COLOR=GREEN in the BMS source, making them visually distinct as entry fields. COCRDLIC may override these to RED when validation errors occur.

5. **No VALIDN constraints**: Despite DSATTS/MAPATTS including VALIDN, no DFHMDF fields in this mapset define VALIDN= edit rules. Validation is entirely done in COBOL.
