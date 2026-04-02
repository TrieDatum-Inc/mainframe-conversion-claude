# Technical Specification: COCRDUP.BMS (BMS Mapset)

## 1. Mapset Overview

| Attribute        | Value                                         |
|------------------|-----------------------------------------------|
| Mapset Name      | COCRDUP                                       |
| Source File      | app/bms/COCRDUP.bms                           |
| Map Name         | CCRDUPA                                       |
| BMS Copybook     | app/cpy-bms/COCRDUP.CPY                       |
| Screen Title     | Update Credit Card Details                    |
| Screen Size      | 24 rows x 80 columns                          |
| MODE             | INOUT                                         |
| STORAGE          | AUTO                                          |
| TIOAPFX          | YES                                           |
| LANG             | COBOL                                         |
| Owning Program   | COCRDUPC.CBL (Transaction CCUP)               |
| Version Tag      | CardDemo_v1.0-70-g193b394-123                 |

### Purpose

This mapset defines the credit card update screen. It is the entry, display, and edit screen for COCRDUPC's multi-step update workflow. The screen serves multiple purposes within a single program depending on the current state:

1. **Entry mode**: ACCTSID and CARDSID are unprotected for key entry; detail fields are protected/hidden.
2. **Display/edit mode**: ACCTSID and CARDSID are protected (locked); detail fields are unprotected for editing.
3. **Confirmation mode**: All fields are protected; the function key guide brightens to highlight F5=Save and F12=Cancel.
4. **Post-commit mode**: All fields protected; informational message shows success or failure.

---

## 2. Screen Layout (24 x 80)

```
Col:  1         2         3         4         5         6         7         8
      1234567890123456789012345678901234567890123456789012345678901234567890123456789 0

Row 1: Tran: CCUP                [TITLE01 - 40 chars yellow]       Date: mm/dd/yy
Row 2: Prog: COCRDUPC            [TITLE02 - 40 chars yellow]       Time: hh:mm:ss
Row 3: (blank)
Row 4:                               Update Credit Card Details
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
Row15:     Expiry Date       :  [EXPMON 2] /[EXPYEAR 4  ] [EXPDAY 2 - hidden]
Row16: (blank)
Row17: (blank)
Row18: (blank)
Row19: (blank)
Row20:                          [INFOMSG - 40 chars neutral             ]
Row21: (blank)
Row22: (blank)
Row23: [ERRMSG - 80 chars RED bright                                            ]
Row24: ENTER=Process F3=Exit   [FKEYSC: F5=Save F12=Cancel - dark by default]
```

---

## 3. Field Inventory

### 3.1 Header Fields (Read-Only, ASKIP)

| Field Name | Row | Col | Length | Color    | Description                              |
|------------|-----|-----|--------|----------|------------------------------------------|
| (literal)  | 1   | 1   | 5      | BLUE     | 'Tran:' label                            |
| TRNNAME    | 1   | 7   | 4      | BLUE     | Transaction ID (CCUP)                    |
| TITLE01    | 1   | 21  | 40     | YELLOW   | Application title line 1                 |
| (literal)  | 1   | 65  | 5      | BLUE     | 'Date:' label                            |
| CURDATE    | 1   | 71  | 8      | BLUE     | Current date MM/DD/YY                    |
| (literal)  | 2   | 1   | 5      | BLUE     | 'Prog:' label                            |
| PGMNAME    | 2   | 7   | 8      | BLUE     | Program name (COCRDUPC)                  |
| TITLE02    | 2   | 21  | 40     | YELLOW   | Application title line 2                 |
| (literal)  | 2   | 65  | 5      | BLUE     | 'Time:' label                            |
| CURTIME    | 2   | 71  | 8      | BLUE     | Current time HH:MM:SS                    |
| (literal)  | 4   | 30  | 26     | NEUTRAL  | 'Update Credit Card Details' screen title|

### 3.2 Search Key / Identity Fields

| Field Name | Row | Col | Length | Attribute           | Highlight | Color   | Description                                             |
|------------|-----|-----|--------|---------------------|-----------|---------|----------------------------------------------------------|
| (label)    | 7   | 23  | 19     | ASKIP,NORM          | —         | TURQUOISE | 'Account Number    :' label                            |
| ACCTSID    | 7   | 45  | 11     | FSET,IC,NORM,PROT   | UNDERLINE | DEFAULT | Account number; **initially PROT** in BMS              |
| (stopper)  | 7   | 57  | 0      | —                   | —         | —       | Field stopper                                           |
| (label)    | 8   | 23  | 19     | ASKIP,NORM          | —         | TURQUOISE | 'Card Number       :' label                            |
| CARDSID    | 8   | 45  | 16     | FSET,NORM,UNPROT    | UNDERLINE | DEFAULT | Card number; **UNPROT** in BMS                          |
| (stopper)  | 8   | 62  | 0      | —                   | —         | —       | Field stopper                                           |

**Critical difference from COCRDSL**:
- ACCTSID is declared **PROT** in COCRDUP.BMS (line 84), whereas it is UNPROT in COCRDSL.BMS.
- CARDSID remains UNPROT in both.
- COCRDUPC overrides ACCTSIDA dynamically: sets DFHBMFSE (unprotected) in the search/entry state and DFHBMPRF (protected) after card data is fetched.

### 3.3 Editable Card Detail Fields

These fields are defined UNPROT in the BMS source (user can type into them), but COCRDUPC protects them dynamically in the non-edit states.

| Field Name | Row | Col | Length | BMS Attribute | Highlight | Justify | Description                             |
|------------|-----|-----|--------|---------------|-----------|---------|------------------------------------------|
| (label)    | 11  | 4   | 20     | —             | —         | —       | 'Name on card      :' label (TURQUOISE) |
| CRDNAME    | 11  | 25  | 50     | UNPROT        | UNDERLINE | —       | Embossed name on card (user-editable)   |
| (stopper)  | 11  | 76  | 0      | —             | —         | —       | Field stopper                           |
| (label)    | 13  | 4   | 20     | —             | —         | —       | 'Card Active Y/N   : ' label (TURQUOISE)|
| CRDSTCD    | 13  | 25  | 1      | UNPROT        | UNDERLINE | —       | Active status Y/N (user-editable)       |
| (stopper)  | 13  | 27  | 0      | —             | —         | —       | Field stopper                           |
| (label)    | 15  | 4   | 20     | —             | —         | —       | 'Expiry Date       : ' label (TURQUOISE)|
| EXPMON     | 15  | 25  | 2      | UNPROT        | UNDERLINE | RIGHT   | Expiry month MM (user-editable)         |
| (literal)  | 15  | 28  | 1      | —             | —         | —       | '/' date separator                      |
| EXPYEAR    | 15  | 30  | 4      | UNPROT        | UNDERLINE | RIGHT   | Expiry year YYYY (user-editable)        |
| (stopper)  | 15  | 35  | 0      | —             | —         | —       | Field stopper                           |
| EXPDAY     | 15  | 36  | 2      | DRK,FSET,PROT | OFF      | RIGHT   | Expiry day (hidden, not user-editable)  |
| (stopper)  | 15  | 39  | 0      | —             | —         | —       | Field stopper                           |

**EXPDAY**: Defined at col 36, length 2 with ATTRB=(DRK,FSET,PROT). It is:
- **DRK**: Always dark/hidden on the terminal — the user never sees or types in it.
- **FSET**: Always transmitted back to host even if the user didn't touch it.
- **PROT**: Protected — the cursor never lands here.
- **Purpose**: Carries the expiry day component across the CICS RETURN loop. Because the full expiration date stored in CARDDAT is YYYY-MM-DD (10 chars), and the user is only shown/allowed to change month and year, the day must be preserved invisibly so the STRING reconstruction in 9200-WRITE-PROCESSING can rebuild the full date.
- **JUSTIFY=(RIGHT)**: EXPMON, EXPYEAR, and EXPDAY all have JUSTIFY=(RIGHT), which means BMS right-justifies data in the field on send (useful for short numeric values).

### 3.4 Message and Function Key Fields

| Field Name | Row | Col | Length | Attribute       | Color   | Description                                           |
|------------|-----|-----|--------|-----------------|---------|-------------------------------------------------------|
| INFOMSG    | 20  | 25  | 40     | PROT            | NEUTRAL | Informational/status message                          |
| ERRMSG     | 23  | 1   | 80     | ASKIP,BRT,FSET  | RED     | Error / validation message (bright red)               |
| FKEYS      | 24  | 1   | 21     | ASKIP,NORM      | YELLOW  | 'ENTER=Process F3=Exit' — always visible              |
| FKEYSC     | 24  | 23  | 18     | ASKIP,DRK       | YELLOW  | 'F5=Save F12=Cancel' — **dark by default**; brightened by program when confirmation is needed |

**FKEYSC design**: Defined as DRK (dark/invisible) in BMS source. COCRDUPC makes it visible (DFHBMBRY = bright yellow) only when CCUP-CHANGES-OK-NOT-CONFIRMED state is active (i.e., when the user needs to press F5 to confirm the save). This provides a visual cue: F5 appears only when it is actionable.

---

## 4. BMS Symbolic Map Fields (from COCRDUP.CPY)

The generated copybook provides:
- **CCRDUPAI** — input structure
- **CCRDUPAO** — output structure (REDEFINES CCRDUPAI)

### Input Structure (CCRDUPAI)

| Field Name  | PIC    | Description                                        |
|-------------|--------|----------------------------------------------------|
| TRNNAMEI    | X(4)   | Transaction name                                   |
| TITLE01I    | X(40)  | Title line 1                                       |
| CURDATEI    | X(8)   | Current date                                       |
| PGMNAMEI    | X(8)   | Program name                                       |
| TITLE02I    | X(40)  | Title line 2                                       |
| CURTIMEI    | X(8)   | Current time                                       |
| ACCTSIDI    | X(11)  | Account number input                               |
| ACCTSIDA    | X(1)   | Attribute byte for ACCTSID                         |
| CARDSIDI    | X(16)  | Card number input                                  |
| CARDSIDA    | X(1)   | Attribute byte for CARDSID                         |
| CRDNAMEI    | X(50)  | Embossed name input                                |
| CRDNAMEA    | X(1)   | Attribute byte for CRDNAME                         |
| CRDSTCDI    | X(1)   | Active status input (Y/N)                          |
| CRDSTCDA    | X(1)   | Attribute byte for CRDSTCD                         |
| EXPMONI     | X(2)   | Expiry month input (MM)                            |
| EXPMONA     | X(1)   | Attribute byte for EXPMON                          |
| EXPYEARI    | X(4)   | Expiry year input (YYYY)                           |
| EXPYEARA    | X(1)   | Attribute byte for EXPYEAR                         |
| EXPDAYI     | X(2)   | Expiry day (hidden; always received)               |
| EXPDAYA     | X(1)   | Attribute byte for EXPDAY                          |
| INFOMSGI    | X(40)  | Informational message                              |
| INFOMSGA    | X(1)   | Attribute byte for INFOMSG                         |
| ERRMSGI     | X(80)  | Error message                                      |
| FKEYSI      | X(21)  | 'ENTER=Process F3=Exit'                            |
| FKEYSCA     | X(1)   | Attribute byte for FKEYSC                          |
| FKEYSCI     | X(18)  | 'F5=Save F12=Cancel'                               |

### Output Structure (CCRDUPAO) — selected fields

| Field Name  | PIC    | Description                                        |
|-------------|--------|----------------------------------------------------|
| ACCTSIDO    | X(11)  | Account number output                              |
| ACCTSIDC    | X(1)   | Color attribute for ACCTSID                        |
| CARDSIDO    | X(16)  | Card number output                                 |
| CARDSIDC    | X(1)   | Color attribute for CARDSID                        |
| CRDNAMEO    | X(50)  | Card name output                                   |
| CRDNAMEC    | X(1)   | Color attribute for CRDNAME                        |
| CRDSTCDO    | X(1)   | Card status output                                 |
| CRDSTCDC    | X(1)   | Color attribute for CRDSTCD                        |
| EXPMONO     | X(2)   | Expiry month output                                |
| EXPMONC     | X(1)   | Color attribute for EXPMON                         |
| EXPYEARO    | X(4)   | Expiry year output                                 |
| EXPYEARC    | X(1)   | Color attribute for EXPYEAR                        |
| EXPDAYO     | X(2)   | Expiry day output (hidden)                         |
| EXPDAYC     | X(1)   | Color attribute for EXPDAY (always DFHBMDAR)       |
| INFOMSGO    | X(40)  | Informational message output                       |
| INFOMSGA    | X(1)   | Attribute byte for INFOMSG (DFHBMDAR or DFHBMBRY)  |
| ERRMSGO     | X(80)  | Error message output                               |
| FKEYSO      | X(21)  | Function key guide output                          |
| FKEYSCO     | X(18)  | F5/F12 guide output                                |
| FKEYSCA     | X(1)   | Attribute byte for FKEYSC (dark → bright on confirm) |

---

## 5. Dynamic Attribute Control Used by COCRDUPC

COCRDUPC (paragraph 3300-SETUP-SCREEN-ATTRS) performs extensive dynamic attribute management:

### Field Protection by State

| Program State                    | ACCTSIDA | CARDSIDA | CRDNAMEA | CRDSTCDA | EXPMONA  | EXPYEARA |
|----------------------------------|----------|----------|----------|----------|----------|----------|
| CCUP-DETAILS-NOT-FETCHED         | DFHBMFSE | DFHBMFSE | DFHBMPRF | DFHBMPRF | DFHBMPRF | DFHBMPRF |
| CCUP-SHOW-DETAILS                | DFHBMPRF | DFHBMPRF | DFHBMFSE | DFHBMFSE | DFHBMFSE | DFHBMFSE |
| CCUP-CHANGES-NOT-OK              | DFHBMPRF | DFHBMPRF | DFHBMFSE | DFHBMFSE | DFHBMFSE | DFHBMFSE |
| CCUP-CHANGES-OK-NOT-CONFIRMED    | DFHBMPRF | DFHBMPRF | DFHBMPRF | DFHBMPRF | DFHBMPRF | DFHBMPRF |
| CCUP-CHANGES-OKAYED-AND-DONE     | DFHBMPRF | DFHBMPRF | DFHBMPRF | DFHBMPRF | DFHBMPRF | DFHBMPRF |
| OTHER (fallback)                 | DFHBMFSE | DFHBMFSE | DFHBMPRF | DFHBMPRF | DFHBMPRF | DFHBMPRF |

Note: EXPDAY (EXPDAYA) is not explicitly set in the protection EVALUATE — it is defined DRK/PROT in the BMS source and COCRDUPC does not change its attribute byte.

### Color Overrides

| Field | Condition                               | Color Set  | Description                             |
|-------|-----------------------------------------|------------|-----------------------------------------|
| ACCTSIDC | Came from COCRDLIC list              | DFHDFCOL   | Default color                           |
| ACCTSIDC | FLG-ACCTFILTER-NOT-OK                | DFHRED     | Red                                     |
| ACCTSIDO + ACCTSIDC | Blank on re-entry           | '*' + DFHRED | Asterisk placeholder, red color       |
| CARDSIDC | FLG-CARDFILTER-NOT-OK                | DFHRED     | Red                                     |
| CARDSIDO + CARDSIDC | Blank on re-entry          | '*' + DFHRED | Asterisk placeholder, red color       |
| CRDNAMEC | FLG-CARDNAME-NOT-OK + CCUP-CHANGES-NOT-OK | DFHRED | Red                                  |
| CRDNAMEO + CRDNAMEC | Blank + CCUP-CHANGES-NOT-OK | '*' + DFHRED | Asterisk placeholder, red         |
| CRDSTCDC | FLG-CARDSTATUS-NOT-OK + CCUP-CHANGES-NOT-OK | DFHRED | Red                               |
| CRDSTCDO + CRDSTCDC | Blank + CCUP-CHANGES-NOT-OK | '*' + DFHRED | Asterisk placeholder, red        |
| EXPDAYC  | Always                               | DFHBMDAR   | Dark (always invisible)                 |
| EXPMONC  | FLG-CARDEXPMON-NOT-OK + CCUP-CHANGES-NOT-OK | DFHRED | Red                               |
| EXPMONO + EXPMONC | Blank + CCUP-CHANGES-NOT-OK | '*' + DFHRED | Asterisk placeholder, red          |
| EXPYEARC | FLG-CARDEXPYEAR-NOT-OK + CCUP-CHANGES-NOT-OK | DFHRED | Red                             |
| EXPYEARO + EXPYEARC | Blank + CCUP-CHANGES-NOT-OK | '*' + DFHRED | Asterisk placeholder, red       |
| INFOMSGA | WS-NO-INFO-MESSAGE                   | DFHBMDAR   | Dark (invisible)                        |
| INFOMSGA | Message present                      | DFHBMBRY   | Bright                                  |
| FKEYSCA  | PROMPT-FOR-CONFIRMATION state        | DFHBMBRY   | Bright yellow — highlights F5/F12       |

### Cursor Positioning (by error flag priority)

| Priority | Condition                   | Cursor Placed At    |
|----------|-----------------------------|---------------------|
| 1        | FOUND-CARDS-FOR-ACCOUNT or NO-CHANGES-DETECTED | CRDNAMEL = -1  |
| 2        | FLG-ACCTFILTER-NOT-OK or BLANK | ACCTSIDL = -1   |
| 3        | FLG-CARDFILTER-NOT-OK or BLANK | CARDSIDL = -1   |
| 4        | FLG-CARDNAME-NOT-OK or BLANK | CRDNAMEL = -1     |
| 5        | FLG-CARDSTATUS-NOT-OK or BLANK | CRDSTCDL = -1   |
| 6        | FLG-CARDEXPMON-NOT-OK or BLANK | EXPMONL = -1    |
| 7        | FLG-CARDEXPYEAR-NOT-OK or BLANK | EXPYEARL = -1  |
| default  | OTHER                        | ACCTSIDL = -1      |

---

## 6. Comparison with COCRDSL.BMS

| Attribute         | COCRDSL (View)        | COCRDUP (Update)          |
|-------------------|-----------------------|---------------------------|
| Screen title      | View Credit Card Detail | Update Credit Card Details|
| CRDNAME attribute | ASKIP (read-only)     | UNPROT (user-editable)    |
| CRDSTCD attribute | ASKIP (read-only)     | UNPROT (user-editable)    |
| EXPMON attribute  | ASKIP (read-only)     | UNPROT (user-editable)    |
| EXPYEAR attribute | ASKIP (read-only)     | UNPROT (user-editable)    |
| EXPDAY field      | Not present           | Present (DRK,PROT)        |
| ACCTSID attribute | UNPROT in BMS         | PROT in BMS               |
| FKEYSC field      | Not present           | Present (DRK by default)  |
| Function keys     | ENTER + F3            | ENTER + F3 + F5 + F12     |

---

## 7. Transaction Flow Context

```
COCRDLIC (CCLI) or COMEN01C
    |
    | XCTL (CDEMO-ACCT-ID, CDEMO-CARD-NUM in COMMAREA)
    v
COCRDUPC (CCUP)
    |
    |-- State: CCUP-DETAILS-NOT-FETCHED --> SEND MAP (search screen)
    |-- User enters keys, ENTER
    |-- RECEIVE MAP, READ CARDDAT
    |-- State: CCUP-SHOW-DETAILS --> SEND MAP (display for edit)
    |-- User modifies fields, ENTER
    |-- RECEIVE MAP, validate
    |   |-- invalid --> State: CCUP-CHANGES-NOT-OK --> SEND MAP (show errors)
    |   |-- valid   --> State: CCUP-CHANGES-OK-NOT-CONFIRMED --> SEND MAP (confirm)
    |                    FKEYSC brightens
    |-- User presses F5
    |-- READ UPDATE, dirty check, REWRITE
    |   |-- success --> State: CCUP-CHANGES-OKAYED-AND-DONE
    |   |-- lock err--> State: CCUP-CHANGES-OKAYED-LOCK-ERROR
    |   |-- write err-> State: CCUP-CHANGES-OKAYED-BUT-FAILED
    |
    |-- PF3 or auto-exit --> SYNCPOINT; XCTL back to caller
```

---

## 8. Key Design Notes

1. **EXPDAY hidden field is critical for data integrity**: The expiry day is stored in CARDDAT as part of a 10-character YYYY-MM-DD string. Since the user cannot edit the day, it must survive the CICS RETURN round-trip without being lost. The DRK/FSET/PROT EXPDAY field at col 36 carries this value invisibly.

2. **ACCTSID is PROT in BMS but overridden to UNPROT by COCRDUPC**: This is an unusual design — the BMS default is protected, but the program makes it editable in the search state. This means that if the program fails to set DFHBMFSE on ACCTSIDA, the field will stay protected and the user cannot enter an account number. The program correctly handles this in paragraph 3300-SETUP-SCREEN-ATTRS.

3. **FKEYSC visual state machine**: The F5/F12 guide field is invisible until confirmation is needed. This prevents accidental F5 press before the user has reviewed the changes. It becomes bright (DFHBMBRY) only when CCUP-CHANGES-OK-NOT-CONFIRMED is the active state.

4. **JUSTIFY=(RIGHT) on expiry fields**: EXPMON, EXPYEAR, and EXPDAY all have JUSTIFY=(RIGHT). BMS will right-justify short values (e.g., month '1' → ' 1') on send. The COBOL validation paragraphs (1250-EDIT-EXPIRY-MON, 1260-EDIT-EXPIRY-YEAR) check the received values directly; they must handle leading spaces in the received data.

5. **No NUMVAL validation on EXPMON/EXPYEAR in BMS**: Despite being numeric fields in the data model, no VALIDN=MUSTFILL or numeric validation is defined in the BMS. The program handles numeric validation entirely in COBOL.

6. **Placeholder asterisk pattern**: When a required field is blank during error re-display, COCRDUPC places a literal '*' in the output field (e.g., ACCTSIDO = '*') and sets RED color. This gives the user a visual indicator that the field is required and currently empty, since a truly empty field might show no indication of where to type.
