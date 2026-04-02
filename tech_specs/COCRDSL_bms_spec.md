# Technical Specification: COCRDSL.BMS (BMS Mapset)

## 1. Mapset Overview

| Attribute        | Value                                         |
|------------------|-----------------------------------------------|
| Mapset Name      | COCRDSL                                       |
| Source File      | app/bms/COCRDSL.bms                           |
| Map Name         | CCRDSLA                                       |
| BMS Copybook     | app/cpy-bms/COCRDSL.CPY                       |
| Screen Title     | View Credit Card Detail                       |
| Screen Size      | 24 rows x 80 columns                          |
| MODE             | INOUT                                         |
| STORAGE          | AUTO                                          |
| TIOAPFX          | YES                                           |
| LANG             | COBOL                                         |
| Owning Program   | COCRDSLC.CBL (Transaction CCDL)               |
| Version Tag      | CardDemo_v1.0-70-g193b394-123                 |

### Purpose

This mapset defines the credit card detail view screen. It displays the details of a single credit card record retrieved from CARDDAT. The screen is primarily read-only — all displayed card detail fields (name, status, expiry) are ASKIP (protected). The user can enter an account number and card number at the top if not coming from the card list screen. PF3 exits; ENTER searches.

---

## 2. Screen Layout (24 x 80)

```
Col:  1         2         3         4         5         6         7         8
      1234567890123456789012345678901234567890123456789012345678901234567890123456789 0

Row 1: Tran: CCDL                [TITLE01 - 40 chars yellow]       Date: mm/dd/yy
Row 2: Prog: COCRDSLC            [TITLE02 - 40 chars yellow]       Time: hh:mm:ss
Row 3: (blank)
Row 4:                               View Credit Card Detail
Row 5: (blank)
Row 6: (blank)
Row 7:                        Account Number    : [ACCTSID - 11 chars underline]
Row 8:                        Card Number       : [CARDSID - 16 chars underline]
Row 9: (blank)
Row10: (blank)
Row11:     Name on card      : [CRDNAME - 50 chars underline                    ]
Row12: (blank)
Row13:     Card Active Y/N   :  [CRDSTCD - 1 char underline]
Row14: (blank)
Row15:     Expiry Date       :  [EXPMON 2] /[EXPYEAR 4  ]
Row16: (blank)
Row17: (blank)
Row18: (blank)
Row19: (blank)
Row20:                          [INFOMSG - 40 chars neutral             ]
Row21: (blank)
Row22: (blank)
Row23: [ERRMSG - 80 chars RED bright                                            ]
Row24: ENTER=Search Cards  F3=Exit
```

---

## 3. Field Inventory

### 3.1 Header Fields (Read-Only, ASKIP)

| Field Name | Row | Col | Length | Color    | Description                              |
|------------|-----|-----|--------|----------|------------------------------------------|
| (literal)  | 1   | 1   | 5      | BLUE     | 'Tran:' label                            |
| TRNNAME    | 1   | 7   | 4      | BLUE     | Transaction ID (CCDL)                    |
| TITLE01    | 1   | 21  | 40     | YELLOW   | Application title line 1                 |
| (literal)  | 1   | 65  | 5      | BLUE     | 'Date:' label                            |
| CURDATE    | 1   | 71  | 8      | BLUE     | Current date MM/DD/YY                    |
| (literal)  | 2   | 1   | 5      | BLUE     | 'Prog:' label                            |
| PGMNAME    | 2   | 7   | 8      | BLUE     | Program name (COCRDSLC)                  |
| TITLE02    | 2   | 21  | 40     | YELLOW   | Application title line 2                 |
| (literal)  | 2   | 65  | 5      | BLUE     | 'Time:' label                            |
| CURTIME    | 2   | 71  | 8      | BLUE     | Current time HH:MM:SS                    |
| (literal)  | 4   | 30  | 23     | NEUTRAL  | 'View Credit Card Detail' screen title   |

### 3.2 Search Key Entry Fields

| Field Name | Row | Col | Length | Attribute              | Highlight  | Color   | Description                                            |
|------------|-----|-----|--------|------------------------|------------|---------|--------------------------------------------------------|
| (label)    | 7   | 23  | 19     | ASKIP,NORM             | —          | TURQUOISE | 'Account Number    :' label                          |
| ACCTSID    | 7   | 45  | 11     | FSET,IC,NORM,UNPROT    | UNDERLINE  | DEFAULT | Account number entry; IC=initial cursor               |
| (stopper)  | 7   | 57  | 0      | —                      | —          | —       | Field stopper                                         |
| (label)    | 8   | 23  | 19     | ASKIP,NORM             | —          | TURQUOISE | 'Card Number       :' label                          |
| CARDSID    | 8   | 45  | 16     | FSET,NORM,UNPROT       | UNDERLINE  | DEFAULT | Card number entry field                               |
| (stopper)  | 8   | 62  | 0      | —                      | —          | —       | Field stopper                                         |

**Notes**:
- ACCTSID has IC (initial cursor) ensuring the terminal cursor starts here.
- Both fields are UNPROT in BMS source. COCRDSLC may override to DFHBMPRF (protected) when the screen is reached from COCRDLIC (data already known).
- COLOR=DEFAULT (not explicitly set to green as in COCRDLI) — inherits terminal default color.

### 3.3 Card Detail Display Fields (Read-Only)

All card detail fields are defined with ASKIP attribute in the BMS source, making them read-only display fields. The user cannot modify them on this screen.

| Field Name | Row | Col | Length | Attribute | Highlight  | Color    | Description                              |
|------------|-----|-----|--------|-----------|------------|----------|------------------------------------------|
| (label)    | 11  | 4   | 20     | —         | —          | TURQUOISE| 'Name on card      :' label              |
| CRDNAME    | 11  | 25  | 50     | ASKIP (default) | UNDERLINE | —   | Embossed name on card                    |
| (stopper)  | 11  | 76  | 0      | —         | —          | —        | Field stopper                            |
| (label)    | 13  | 4   | 20     | —         | —          | TURQUOISE| 'Card Active Y/N   : ' label             |
| CRDSTCD    | 13  | 25  | 1      | ASKIP     | UNDERLINE  | —        | Active status (Y=active, N=inactive)     |
| (stopper)  | 13  | 27  | 0      | —         | —          | —        | Field stopper                            |
| (label)    | 15  | 4   | 20     | —         | —          | TURQUOISE| 'Expiry Date       : ' label             |
| EXPMON     | 15  | 25  | 2      | ASKIP     | UNDERLINE  | —        | Expiry month (MM)                        |
| (literal)  | 15  | 28  | 1      | —         | —          | —        | '/' separator                            |
| EXPYEAR    | 15  | 30  | 4      | ASKIP     | UNDERLINE  | —        | Expiry year (YYYY)                       |
| (stopper)  | 15  | 35  | 0      | —         | —          | —        | Field stopper                            |

**Note on ASKIP**: All detail fields (CRDNAME, CRDSTCD, EXPMON, EXPYEAR) are ASKIP in the BMS definition, meaning the terminal will skip over them when tabbing and the user cannot type into them. This enforces the read-only nature of this screen.

### 3.4 Message and Key Guide Fields

| Field Name | Row | Col | Length | Attribute      | Color   | Description                              |
|------------|-----|-----|--------|----------------|---------|------------------------------------------|
| INFOMSG    | 20  | 25  | 40     | PROT           | NEUTRAL | Informational message                    |
| ERRMSG     | 23  | 1   | 80     | ASKIP,BRT,FSET | RED     | Error / status message (bright red)      |
| FKEYS      | 24  | 1   | 75     | ASKIP,NORM     | YELLOW  | 'ENTER=Search Cards  F3=Exit' key guide  |

---

## 4. BMS Symbolic Map Fields (from COCRDSL.CPY)

The generated copybook provides:
- **CCRDSLAI** — input structure
- **CCRDSLAO** — output structure (REDEFINES CCRDSLAI)

Full field inventory:

### Input Structure (CCRDSLAI)

| Field Name  | PIC    | Description                              |
|-------------|--------|------------------------------------------|
| TRNNAMEI    | X(4)   | Transaction name                         |
| TITLE01I    | X(40)  | Title line 1                             |
| CURDATEI    | X(8)   | Current date                             |
| PGMNAMEI    | X(8)   | Program name                             |
| TITLE02I    | X(40)  | Title line 2                             |
| CURTIMEI    | X(8)   | Current time                             |
| ACCTSIDI    | X(11)  | Account number input                     |
| CARDSIDI    | X(16)  | Card number input                        |
| CRDNAMEI    | X(50)  | Card name (read back on receive; ASKIP so always blank) |
| CRDSTCDI    | X(1)   | Card status (ASKIP — blank on receive)   |
| EXPMONI     | X(2)   | Expiry month (ASKIP — blank on receive)  |
| EXPYEARI    | X(4)   | Expiry year (ASKIP — blank on receive)   |
| INFOMSGI    | X(40)  | Informational message                    |
| ERRMSGI     | X(80)  | Error message                            |
| FKEYSI      | X(75)  | Function key guide                       |

### Output Structure (CCRDSLAO) — selected fields

| Field Name  | PIC    | Description                              |
|-------------|--------|------------------------------------------|
| TRNNAMEO    | X(4)   | Transaction name output                  |
| TITLE01O    | X(40)  | Title line 1 output                      |
| CURDATEO    | X(8)   | Date output                              |
| PGMNAMEO    | X(8)   | Program name output                      |
| TITLE02O    | X(40)  | Title line 2 output                      |
| CURTIMEO    | X(8)   | Time output                              |
| ACCTSIDO    | X(11)  | Account number output                    |
| ACCTSIDA    | X(1)   | Attribute byte for ACCTSID               |
| ACCTSIDC    | X(1)   | Color extended attribute for ACCTSID     |
| CARDSIDO    | X(16)  | Card number output                       |
| CARDSIDA    | X(1)   | Attribute byte for CARDSID               |
| CARDSIDC    | X(1)   | Color extended attribute for CARDSID     |
| CRDNAMEO    | X(50)  | Card name output                         |
| CRDSTCDO    | X(1)   | Card status output                       |
| EXPMONO     | X(2)   | Expiry month output                      |
| EXPYEARO    | X(4)   | Expiry year output                       |
| INFOMSGO    | X(40)  | Informational message output             |
| INFOMSGC    | X(1)   | Color attribute for INFOMSG              |
| ERRMSGO     | X(80)  | Error message output                     |
| FKEYSO      | X(75)  | Function key guide output                |
| FKEYSC      | X(1)   | Color attribute for FKEYS                |

---

## 5. Dynamic Attribute Control Used by COCRDSLC

COCRDSLC dynamically modifies these attributes in paragraph 1300-SETUP-SCREEN-ATTRS:

| Attribute Modified  | Condition                                        | Value          | Effect                              |
|---------------------|--------------------------------------------------|----------------|-------------------------------------|
| ACCTSIDA            | Came from COCRDLIC (CDEMO-LAST-MAPSET=COCRDLI)   | DFHBMPRF       | Protect account field               |
| CARDSIDA            | Same                                             | DFHBMPRF       | Protect card field                  |
| ACCTSIDA            | Not from COCRDLIC                                | DFHBMFSE       | Unprotect for entry                 |
| CARDSIDA            | Not from COCRDLIC                                | DFHBMFSE       | Unprotect for entry                 |
| ACCTSIDL            | Account filter error or blank                    | -1             | Cursor to account field             |
| CARDSIDL            | Card filter error or blank                       | -1             | Cursor to card field                |
| ACCTSIDC            | Came from list (no error)                        | DFHDFCOL       | Default color                       |
| ACCTSIDC            | Account error                                    | DFHRED         | Red                                 |
| CARDSIDC            | Same for card                                    | DFHRED         | Red                                 |
| ACCTSIDO + ACCTSIDC | Blank field on re-entry                          | '*' + DFHRED   | Placeholder asterisk + RED          |
| CARDSIDO + CARDSIDC | Blank field on re-entry                          | '*' + DFHRED   | Placeholder asterisk + RED          |
| INFOMSGC            | No message                                       | DFHBMDAR       | Dark (invisible)                    |
| INFOMSGC            | Message present                                  | DFHNEUTR       | Neutral (visible)                   |

---

## 6. Data Flow: Map Fields to CARD-RECORD

When a card is successfully found (FOUND-CARDS-FOR-ACCOUNT set), COCRDSLC populates the output map (paragraph 1200-SETUP-SCREEN-VARS):

| Map Output Field | Source Field in CARD-RECORD                    |
|------------------|------------------------------------------------|
| CRDNAMEO         | CARD-EMBOSSED-NAME (X(50))                     |
| EXPMONO          | CARD-EXPIRY-MONTH (positions 6-7 of CARD-EXPIRAION-DATE, via CARD-EXPIRAION-DATE-X REDEFINES) |
| EXPYEARO         | CARD-EXPIRY-YEAR (positions 1-4)               |
| CRDSTCDO         | CARD-ACTIVE-STATUS (X(1))                      |
| ACCTSIDO         | CC-ACCT-ID (from COMMAREA / user input)        |
| CARDSIDO         | CC-CARD-NUM (from COMMAREA / user input)       |

CVV code (CARD-CVV-CD) is **not displayed** on this screen. It is stored in CARD-RECORD but intentionally omitted from the BMS map and the display logic.

---

## 7. Transaction Flow Context

```
COCRDLIC (CCLI)
    |
    | XCTL with COMMAREA (CDEMO-ACCT-ID, CDEMO-CARD-NUM)
    v
COCRDSLC (CCDL)
    |-- CICS RETURN(CCDL) -- screen re-display loop
    |-- PF3 XCTL --> calling program (COCRDLIC or COMEN01C)
```

When CDEMO-LAST-MAPSET = COCRDLI (came from list):
- ACCTSID and CARDSID are protected.
- Screen immediately shows card data (no user entry needed).

When entered independently:
- ACCTSID and CARDSID are unprotected.
- User types search keys and presses ENTER.

---

## 8. Key Design Notes

1. **Read-only card details**: All card detail fields (CRDNAME, CRDSTCD, EXPMON, EXPYEAR) are defined with ATTRB=ASKIP in the BMS source. This is a strict display-only screen; updates are handled by COCRDUPC on mapset COCRDUP.

2. **No explicit VALIDN rules**: The BMS DSATTS/MAPATTS include VALIDN but no field defines VALIDN= edit constraints. All validation is in COBOL.

3. **Expiry date display format**: Only month (MM) and year (YYYY) are shown, separated by a literal '/'. The day component from CARD-EXPIRAION-DATE is not displayed. Compare with COCRDUP which also omits day from user editing.

4. **Account field position difference from COCRDLI**: In COCRDLI, ACCTSID is at row 6 col 44. In COCRDSL, ACCTSID is at row 7 col 45 and CARDSID at row 8 col 45 (one column further right, one row lower).

5. **FKEYS field is a named field**: Unlike COCRDLI where the key guide is an anonymous literal, COCRDSL names its key guide field FKEYS (with FKEYSA/FKEYSO/FKEYSC in the symbolic map). This allows COCRDSLC to programmatically modify its attributes if needed, though in the current implementation it is not dynamically changed.

6. **Expiry day not present**: The BMS map has no field for expiry day. The day component of the expiration date (CARD-EXPIRAION-DATE positions 9-10) is not shown to the user on this screen at all.
