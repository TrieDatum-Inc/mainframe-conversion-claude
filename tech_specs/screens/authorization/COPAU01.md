# Technical Specification: COPAU01
## Authorization Details Screen

---

### 1. Screen Overview

| Attribute        | Value                                                           |
|------------------|-----------------------------------------------------------------|
| BMS Source File  | bms/COPAU01.bms                                                 |
| Copybook         | cpy-bms/COPAU01.cpy                                             |
| Mapset Name      | COPAU01                                                         |
| Map Name         | COPAU1A                                                         |
| Screen Size      | 24 rows x 80 columns                                            |
| CICS Transaction | CPVD                                                            |
| Primary Program  | COPAUS1C (Authorization Details View and Fraud Toggle)          |
| Sub-program      | COPAUS2C (Fraud DB2 Update, invoked via EXEC CICS LINK)         |
| MODE             | INOUT                                                           |
| STORAGE          | AUTO                                                            |
| CTRL             | (ALARM, FREEKB)                                                 |
| EXTATT           | YES                                                             |
| TIOAPFX          | YES                                                             |

**Purpose:** COPAU01 displays the full detail record for a single pending authorization transaction. It shows the card number, authorization date/time, response code and reason, authorization code, transaction amount, POS entry mode, source, MCC code, card expiry, authorization type, transaction ID, match status, fraud status, and merchant details. The screen also serves as the entry point for marking or removing the fraud flag on an authorization record (PF5 action).

---

### 2. Map Definition

```
COPAU01 DFHMSD CTRL=(ALARM,FREEKB),
               EXTATT=YES,
               LANG=COBOL,
               MODE=INOUT,
               STORAGE=AUTO,
               TIOAPFX=YES,
               TYPE=&&SYSPARM
COPAU1A DFHMDI COLUMN=1, LINE=1, SIZE=(24,80)
```

Source: COPAU01.bms, lines 19–28.

---

### 3. Screen Layout (ASCII Art)

```
Col: 1234567890123456789012345678901234567890123456789012345678901234567890123456789 0
Row 1:  Tran:XXXX         [TITLE01                    ]     Date:mm/dd/yy
Row 2:  Prog:XXXXXXXX     [TITLE02                    ]     Time:hh:mm:ss
Row 3:
Row 4:                           View Authorization Details
Row 5:
Row 6:
Row 7:  Card #:XXXXXXXXXXXXXXXXX   Auth Date:XXXXXXXXXX   Auth Time:XXXXXXXXXX
Row 8:
Row 9:  Auth Resp:X    Resp Reason:XXXXXXXXXXXXXXXXXXXX   Auth Code:XXXXXX
Row 10:
Row 11: Amount:XXXXXXXXXXXX   POS Entry Mode:XXXX   Source   :XXXXXXXXXX
Row 12:
Row 13: MCC Code:XXXX   Card Exp. Date:XXXXX   Auth Type:XXXXXXXXXXXXXX
Row 14:
Row 15: Tran Id:               XXXXXXXXXXXXXXX   Match Status:X   Fraud Status:XXXXXXXXXX
Row 16:
Row 17: Merchant Details ---------------------------------------------------------
Row 18:
Row 19: Name:XXXXXXXXXXXXXXXXXXXXXXXXX   Merchant ID:XXXXXXXXXXXXXXX
Row 20:
Row 21: City:XXXXXXXXXXXXXXXXXXXXXXXXX   State:XX   Zip:XXXXXXXXXX
Row 22:
Row 23: [ERRMSG - 78 chars, RED BRT                                             ]
Row 24:  F3=Back  F5=Mark/Remove Fraud  F8=Next Auth
```

Notes:
- AUTHMTC (Match Status, row 15) and AUTHFRD (Fraud Status, row 15) are displayed in RED to draw operator attention to anomalies.
- ERRMSG (row 23) has FSET attribute — it is always transmitted to the host even if unmodified by the user.
- Row 4 title "View Authorization Details" is displayed in NEUTRAL color BRT (bright intensity).
- The merchant separator on row 17 spans 76 characters.

---

### 4. Field Definitions

All fields in COPAU1A are ASKIP (autoskip — no operator input accepted). This is a read-only display screen with one exception noted below (ERRMSG has FSET).

#### 4.1 Header Fields

| BMS Name | Row | Col | Length | Color    | Attr       | Initial Value    | Description                        |
|----------|-----|-----|--------|----------|------------|------------------|------------------------------------|
| (label)  | 1   | 1   | 5      | BLUE     | ASKIP,NORM | 'Tran:'          | Static label                       |
| TRNNAME  | 1   | 7   | 4      | BLUE     | ASKIP,NORM | (none)           | CICS transaction name (CPVD)       |
| TITLE01  | 1   | 21  | 40     | YELLOW   | ASKIP,NORM | (none)           | Screen title line 1                |
| (label)  | 1   | 65  | 5      | BLUE     | ASKIP,NORM | 'Date:'          | Static label                       |
| CURDATE  | 1   | 71  | 8      | BLUE     | ASKIP,NORM | 'mm/dd/yy'       | Current date (mm/dd/yy)            |
| (label)  | 2   | 1   | 5      | BLUE     | ASKIP,NORM | 'Prog:'          | Static label                       |
| PGMNAME  | 2   | 7   | 8      | BLUE     | ASKIP,NORM | (none)           | Program name (COPAUS1C)            |
| TITLE02  | 2   | 21  | 40     | YELLOW   | ASKIP,NORM | (none)           | Screen title line 2                |
| (label)  | 2   | 65  | 5      | BLUE     | ASKIP,NORM | 'Time:'          | Static label                       |
| CURTIME  | 2   | 71  | 8      | BLUE     | ASKIP,NORM | 'hh:mm:ss'       | Current time (hh:mm:ss)            |

Source: COPAU01.bms, lines 29–74.

#### 4.2 Screen Title

| BMS Name  | Row | Col | Length | Color   | Attr      | Initial Value              | Description           |
|-----------|-----|-----|--------|---------|-----------|----------------------------|-----------------------|
| (literal) | 4   | 27  | 26     | NEUTRAL | ASKIP,BRT | 'View Authorization Details'| Screen title heading |

Source: COPAU01.bms, lines 75–79.

#### 4.3 Authorization Identity Fields (Row 7)

| BMS Name | Row | Col | Length | Color     | Attr       | Initial Value | Description                                          |
|----------|-----|-----|--------|-----------|------------|---------------|------------------------------------------------------|
| (label)  | 7   | 2   | 7      | TURQUOISE | ASKIP,NORM | 'Card #:'     | Static label                                         |
| CARDNUM  | 7   | 11  | 16     | PINK      | ASKIP,NORM | ' '           | 16-digit card number (PA-CARD-NUM from PAUTDTL1)     |
| (label)  | 7   | 31  | 10     | TURQUOISE | ASKIP,NORM | 'Auth Date:'  | Static label                                         |
| AUTHDT   | 7   | 43  | 10     | PINK      | ASKIP,NORM | ' '           | Authorization date formatted MM/DD/YYYY              |
| (label)  | 7   | 56  | 10     | TURQUOISE | ASKIP,NORM | 'Auth Time:'  | Static label                                         |
| AUTHTM   | 7   | 68  | 10     | PINK      | ASKIP,NORM | ' '           | Authorization time formatted HH:MM:SS                |

Source: COPAU01.bms, lines 80–108.

**Data derivation:** AUTHDT and AUTHTM are reconstructed in COPAUS1C from PA-AUTH-ORIG-DATE (6 chars YYMMDD) and PA-AUTH-ORIG-TIME (6 chars HHMMSS). These are NOT the inverted key fields (PA-AUTH-DATE-9C / PA-AUTH-TIME-9C). The formatted values use MOVE with explicit date/time picture clauses (COPAUS1C.md, section on POPULATE-DETAIL-SCREEN).

#### 4.4 Response Fields (Row 9)

| BMS Name | Row | Col | Length | Color     | Attr       | Initial Value | Description                                           |
|----------|-----|-----|--------|-----------|------------|---------------|-------------------------------------------------------|
| (label)  | 9   | 2   | 10     | TURQUOISE | ASKIP,NORM | 'Auth Resp:'  | Static label                                          |
| AUTHRSP  | 9   | 14  | 1      | PINK      | ASKIP,NORM | ' '           | Authorization response code (1 char: '0'=Approved, other=Declined) |
| (label)  | 9   | 18  | 12     | TURQUOISE | ASKIP,NORM | 'Resp Reason:'| Static label                                          |
| AUTHRSN  | 9   | 32  | 20     | BLUE      | ASKIP,NORM | ' '           | Decline reason description (from embedded table in COPAUS1C) |
| (label)  | 9   | 56  | 10     | TURQUOISE | ASKIP,NORM | 'Auth Code:'  | Static label                                          |
| AUTHCD   | 9   | 68  | 6      | BLUE      | ASKIP,NORM | ' '           | Authorization approval code (PA-AUTH-CODE)            |

Source: COPAU01.bms, lines 109–138.

**Note on AUTHRSN:** The reason description is resolved in COPAUS1C via a SEARCH ALL against a 10-entry inline table of decline reason codes (WS-DECLINE-REASONS). If the response code is not found in the table, the raw code is displayed. If the authorization was approved ('00'), the reason field is left blank or set to 'APPROVED'.

#### 4.5 Transaction Fields (Row 11)

| BMS Name | Row | Col | Length | Color     | Attr       | Initial Value    | Description                                        |
|----------|-----|-----|--------|-----------|------------|------------------|----------------------------------------------------|
| (label)  | 11  | 2   | 7      | TURQUOISE | ASKIP,NORM | 'Amount:'        | Static label                                       |
| AUTHAMT  | 11  | 11  | 12     | BLUE      | ASKIP,NORM | ' '              | Transaction amount (PA-TRANSACTION-AMT formatted)  |
| (label)  | 11  | 29  | 15     | TURQUOISE | ASKIP,NORM | 'POS Entry Mode:'| Static label                                       |
| POSEMD   | 11  | 46  | 4      | BLUE      | ASKIP,NORM | ' '              | POS entry mode code (PA-POS-ENTRY-MODE)            |
| (label)  | 11  | 56  | 10     | TURQUOISE | ASKIP,NORM | 'Source   :'     | Static label (note trailing spaces in source)      |
| AUTHSRC  | 11  | 68  | 10     | BLUE      | ASKIP,NORM | ' '              | Authorization source (PA-AUTH-SOURCE)              |

Source: COPAU01.bms, lines 139–168.

#### 4.6 Card and Classification Fields (Row 13)

| BMS Name | Row | Col | Length | Color     | Attr       | Initial Value     | Description                                       |
|----------|-----|-----|--------|-----------|------------|-------------------|---------------------------------------------------|
| (label)  | 13  | 2   | 9      | TURQUOISE | ASKIP,NORM | 'MCC Code:'       | Static label                                      |
| MCCCD    | 13  | 13  | 4      | BLUE      | ASKIP,NORM | ' '               | Merchant Category Code (PA-MCC-CODE)              |
| (label)  | 13  | 25  | 15     | TURQUOISE | ASKIP,NORM | 'Card Exp. Date:' | Static label                                      |
| CRDEXP   | 13  | 42  | 5      | BLUE      | ASKIP,NORM | ' '               | Card expiration date (PA-CARD-EXPIRY-DATE)        |
| (label)  | 13  | 52  | 10     | TURQUOISE | ASKIP,NORM | 'Auth Type:'      | Static label                                      |
| AUTHTYP  | 13  | 64  | 14     | BLUE      | ASKIP,NORM | ' '               | Authorization type description (PA-AUTH-TYPE)     |

Source: COPAU01.bms, lines 169–198.

#### 4.7 Status Fields (Row 15)

| BMS Name | Row | Col | Length | Color     | Attr       | Initial Value | Description                                                       |
|----------|-----|-----|--------|-----------|------------|---------------|-------------------------------------------------------------------|
| (label)  | 15  | 2   | 18     | TURQUOISE | ASKIP,NORM | 'Tran Id:'    | Static label (length=18 oversizes label, actual text is shorter)  |
| TRNID    | 15  | 12  | 15     | BLUE      | ASKIP,NORM | ' '           | Transaction identifier (PA-TRANSACTION-ID)                        |
| (label)  | 15  | 31  | 13     | TURQUOISE | ASKIP,NORM | 'Match Status:'| Static label                                                     |
| AUTHMTC  | 15  | 46  | 1      | RED       | ASKIP,NORM | ' '           | Match status: P=Pending, D=Direct match, E=Exact, M=Manual       |
| (label)  | 15  | 52  | 13     | TURQUOISE | ASKIP,NORM | 'Fraud Status:'| Static label                                                     |
| AUTHFRD  | 15  | 67  | 10     | RED       | ASKIP,NORM | ' '           | Fraud status: 'FRAUD' or 'REMOVED' (from PA-AUTH-FRAUD)          |

Source: COPAU01.bms, lines 199–228.

**Note on AUTHMTC values:** The 88-level definitions in CIPAUDTY.cpy define: PA-MATCH-PENDING (VALUE 'P'), PA-MATCH-DIRECT (VALUE 'D'), PA-MATCH-EXACT (VALUE 'E'), PA-MATCH-MANUAL (VALUE 'M'). The single character is displayed; no lookup table maps it to a description on this screen.

**Note on AUTHFRD values:** COPAUS1C populates AUTHFRDO with the string 'FRAUD' when PA-AUTH-FRAUD = 'F' (88-level PA-FRAUD-CONFIRMED) and 'REMOVED' when PA-AUTH-FRAUD = 'R' (88-level PA-FRAUD-REMOVED). The field length of 10 accommodates both strings.

#### 4.8 Merchant Detail Separator (Row 17)

| BMS Name  | Row | Col | Length | Color   | Attr  | Initial Value                              | Description             |
|-----------|-----|-----|--------|---------|-------|--------------------------------------------|-------------------------|
| (literal) | 17  | 2   | 76     | NEUTRAL | —     | 'Merchant Details ----...' (dashes fill)   | Visual separator line   |

Source: COPAU01.bms, lines 229–233. Note: no ATTRB specified — inherits default (ASKIP,NORM).

#### 4.9 Merchant Name and ID (Row 19)

| BMS Name | Row | Col | Length | Color     | Attr       | Initial Value  | Description                                          |
|----------|-----|-----|--------|-----------|------------|----------------|------------------------------------------------------|
| (label)  | 19  | 2   | 5      | TURQUOISE | ASKIP,NORM | 'Name:'        | Static label                                         |
| MERNAME  | 19  | 9   | 25     | BLUE      | ASKIP,NORM | ' '            | Merchant name (PA-MERCHANT-NAME, max 25 chars)       |
| (label)  | 19  | 41  | 12     | TURQUOISE | ASKIP,NORM | 'Merchant ID:' | Static label                                         |
| MERID    | 19  | 55  | 15     | BLUE      | ASKIP,NORM | ' '            | Merchant identifier (PA-MERCHANT-ID)                 |

Source: COPAU01.bms, lines 234–253.

**Note:** DB2 table CARDDEMO.AUTHFRDS stores MERCHANT_NAME as VARCHAR(22) (AUTHFRDS.ddl, column 22). The BMS field MERNAME is 25 characters. The IMS PAUTDTL1 segment field PA-MERCHANT-NAME is the source displayed here; the DB2 column is populated separately by COPAUS2C for fraud records.

#### 4.10 Merchant Location (Row 21)

| BMS Name | Row | Col | Length | Color     | Attr       | Initial Value | Description                                          |
|----------|-----|-----|--------|-----------|------------|---------------|------------------------------------------------------|
| (label)  | 21  | 2   | 5      | TURQUOISE | ASKIP,NORM | 'City:'       | Static label                                         |
| MERCITY  | 21  | 9   | 25     | BLUE      | ASKIP,NORM | ' '           | Merchant city (PA-MERCHANT-CITY)                     |
| (label)  | 21  | 41  | 6      | TURQUOISE | ASKIP,NORM | 'State:'      | Static label                                         |
| MERST    | 21  | 49  | 2      | BLUE      | ASKIP,NORM | ' '           | Merchant state code (PA-MERCHANT-STATE, 2 chars)     |
| (label)  | 21  | 55  | 4      | TURQUOISE | ASKIP,NORM | 'Zip:'        | Static label                                         |
| MERZIP   | 21  | 61  | 10     | BLUE      | ASKIP,NORM | ' '           | Merchant postal code (PA-MERCHANT-ZIP)               |

Source: COPAU01.bms, lines 254–283.

#### 4.11 Error Message and Navigation (Rows 23–24)

| BMS Name  | Row | Col | Length | Color  | Attr           | Initial Value                                    | Description                     |
|-----------|-----|-----|--------|--------|----------------|--------------------------------------------------|---------------------------------|
| ERRMSG    | 23  | 1   | 78     | RED    | ASKIP,BRT,FSET | (none)                                           | Error/status message area       |
| (literal) | 24  | 1   | 45     | YELLOW | ASKIP,NORM     | ' F3=Back  F5=Mark/Remove Fraud  F8=Next Auth'   | Navigation key legend           |

Source: COPAU01.bms, lines 284–292.

**ERRMSG FSET attribute:** FSET forces the ERRMSG field to be included in every RECEIVE MAP transmission regardless of whether the operator modified it. In practice this screen is read-only (no UNPROT fields), so RECEIVE MAP is not used; the FSET attribute here ensures the field is always sent on SEND MAP even if the program sets it to spaces (to clear a prior error).

---

### 5. Copybook Structures (COPAU01.cpy)

The generated copybook at cpy-bms/COPAU01.cpy defines two 01-level structures.

#### 5.1 COPAU1AI (Input Structure)

Each named field has the standard BMS-generated triple:
- `fieldnameL` — COMP PIC S9(4): length of data received
- `fieldnameF` / `fieldnameA` — PIC X: flag/attribute byte (via REDEFINES)
- `fieldnameI` — PIC X(n): the data value

The 12-byte TIOA prefix (`02 FILLER PIC X(12)`) precedes the first field entry due to TIOAPFX=YES.

| Field Stem | Input Data Field | Length |
|------------|-----------------|--------|
| TRNNAME    | TRNNAMEI        | PIC X(4) |
| TITLE01    | TITLE01I        | PIC X(40) |
| CURDATE    | CURDATEI        | PIC X(8) |
| PGMNAME    | PGMNAMEI        | PIC X(8) |
| TITLE02    | TITLE02I        | PIC X(40) |
| CURTIME    | CURTIMEI        | PIC X(8) |
| CARDNUM    | CARDNUMI        | PIC X(16) |
| AUTHDT     | AUTHDTI         | PIC X(10) |
| AUTHTM     | AUTHTMI         | PIC X(10) |
| AUTHRSP    | AUTHRSPI        | PIC X(1) |
| AUTHRSN    | AUTHRSNI        | PIC X(20) |
| AUTHCD     | AUTHCDI         | PIC X(6) |
| AUTHAMT    | AUTHAMTI        | PIC X(12) |
| POSEMD     | POSEMDI         | PIC X(4) |
| AUTHSRC    | AUTHSRCI        | PIC X(10) |
| MCCCD      | MCCCDI          | PIC X(4) |
| CRDEXP     | CRDEXPI         | PIC X(5) |
| AUTHTYP    | AUTHTYPI        | PIC X(14) |
| TRNID      | TRNIDI          | PIC X(15) |
| AUTHMTC    | AUTHMTCI        | PIC X(1) |
| AUTHFRD    | AUTHFRDI        | PIC X(10) |
| MERNAME    | MERNAMEI        | PIC X(25) |
| MERID      | MERIDI          | PIC X(15) |
| MERCITY    | MERCITYI        | PIC X(25) |
| MERST      | MERSTI          | PIC X(2) |
| MERZIP     | MERZIPI         | PIC X(10) |
| ERRMSG     | ERRMSGI         | PIC X(78) |

Source: COPAU01.cpy, lines 17–180.

#### 5.2 COPAU1AO (Output Structure)

`COPAU1AO REDEFINES COPAU1AI`. Each field has four output bytes plus the data field:
- `fieldnameC` — color byte
- `fieldnameP` — PS/extended highlighting byte
- `fieldnameH` — hilite byte
- `fieldnameV` — validation byte
- `fieldnameO` — PIC X(n): the output data value

Source: COPAU01.cpy, lines 181–344.

COPAUS1C uses the O-suffix fields (CARDNUMO, AUTHDTO, etc.) to populate the map before EXEC CICS SEND MAP. The C-suffix fields (AUTHMTCC, AUTHFRDC) allow dynamic color overrides at runtime — for example, if fraud is confirmed the program may intensify the fraud status field color.

---

### 6. Navigation (PF Key Assignments)

| Key | Label             | Action in COPAUS1C                                                                    |
|-----|-------------------|---------------------------------------------------------------------------------------|
| F3  | Back              | EXEC CICS XCTL COPAUS0C — return to Authorization Summary screen (COPAU00/COPAU0A)   |
| F5  | Mark/Remove Fraud | Toggles PA-AUTH-FRAUD flag via EXEC CICS LINK COPAUS2C; re-displays with updated status |
| F8  | Next Auth         | Advances to next PAUTDTL1 record under the same PAUTSUM0 parent; re-sends COPAU1A    |
| F12 | (not shown)       | [UNRESOLVED] — Cannot be determined from BMS source; check COPAUS1C AID key handling |

**F5 Fraud Toggle sequence (as documented in COPAUS1C.md):**
1. COPAUS1C issues EXEC CICS LINK PROGRAM('COPAUS2C') COMMAREA(WS-CA-FRAUD-RECORD).
2. COPAUS2C performs IMS REPL to toggle PA-AUTH-FRAUD ('F' or 'R') and DB2 INSERT/UPDATE to CARDDEMO.AUTHFRDS.
3. COPAUS2C issues EXEC CICS SYNCPOINT or EXEC CICS SYNCPOINT ROLLBACK.
4. COPAUS1C checks the returned COMMAREA for success/failure and sends the updated screen.

Source: COPAU01.bms, lines 288–292 (navigation legend); COPAUS1C program logic.

---

### 7. Data Flow

#### 7.1 Output Fields — Populated by COPAUS1C before SEND MAP

| Screen Field | COPAU1AO Suffix | Source Data Element            | IMS Segment / Field           |
|--------------|-----------------|--------------------------------|-------------------------------|
| TRNNAMEO     | TRNNAMEO        | EIBTRNID (CICS system field)   | — (CICS-supplied)             |
| TITLE01O     | TITLE01O        | Literal 'View Auth Details'    | — (hardcoded)                 |
| CURDATEO     | CURDATEO        | Formatted current date         | — (ACCEPT FROM DATE)          |
| PGMNAMEO     | PGMNAMEO        | Literal 'COPAUS1C'             | — (hardcoded)                 |
| TITLE02O     | TITLE02O        | Account context info           | PAUTSUM0: PA-ACCT-ID          |
| CURTIMEO     | CURTIMEO        | Formatted current time         | — (ACCEPT FROM TIME)          |
| CARDNUMO     | CARDNUMO        | PA-CARD-NUM                    | PAUTDTL1 (CIPAUDTY.cpy)       |
| AUTHDTO      | AUTHDTO         | Formatted from PA-AUTH-ORIG-DATE | PAUTDTL1 (6-char YYMMDD)   |
| AUTHTMO      | AUTHTMO         | Formatted from PA-AUTH-ORIG-TIME | PAUTDTL1 (6-char HHMMSS)   |
| AUTHRSPO     | AUTHRSPO        | PA-AUTH-RESP-CODE              | PAUTDTL1 (CIPAUDTY.cpy)       |
| AUTHRSNO     | AUTHRSNO        | Resolved from WS-DECLINE-REASONS table | COPAUS1C inline table  |
| AUTHCDO      | AUTHCDO         | PA-AUTH-CODE                   | PAUTDTL1 (CIPAUDTY.cpy)       |
| AUTHAMTO     | AUTHAMTO        | PA-TRANSACTION-AMT formatted   | PAUTDTL1 (CIPAUDTY.cpy)       |
| POSEMDO      | POSEMDO         | PA-POS-ENTRY-MODE              | PAUTDTL1 (CIPAUDTY.cpy)       |
| AUTHSRCO     | AUTHSRCO        | PA-AUTH-SOURCE                 | PAUTDTL1 (CIPAUDTY.cpy)       |
| MCCCDO       | MCCCDO          | PA-MCC-CODE                    | PAUTDTL1 (CIPAUDTY.cpy)       |
| CRDEXPO      | CRDEXPO         | PA-CARD-EXPIRY-DATE            | PAUTDTL1 (CIPAUDTY.cpy)       |
| AUTHTYPO     | AUTHTYPO        | PA-AUTH-TYPE                   | PAUTDTL1 (CIPAUDTY.cpy)       |
| TRNIDO       | TRNIDO          | PA-TRANSACTION-ID              | PAUTDTL1 (CIPAUDTY.cpy)       |
| AUTHMTCO     | AUTHMTCO        | PA-MATCH-STATUS (single char)  | PAUTDTL1 (CIPAUDTY.cpy)       |
| AUTHFRDO     | AUTHFRDO        | 'FRAUD'/'REMOVED'/spaces       | PA-AUTH-FRAUD (CIPAUDTY.cpy)  |
| MERNAMEO     | MERNAMEO        | PA-MERCHANT-NAME               | PAUTDTL1 (CIPAUDTY.cpy)       |
| MERIDO       | MERIDO          | PA-MERCHANT-ID                 | PAUTDTL1 (CIPAUDTY.cpy)       |
| MERCITYO     | MERCITYO        | PA-MERCHANT-CITY               | PAUTDTL1 (CIPAUDTY.cpy)       |
| MERSTO       | MERSTO          | PA-MERCHANT-STATE              | PAUTDTL1 (CIPAUDTY.cpy)       |
| MERZIPO      | MERZIPO         | PA-MERCHANT-ZIP                | PAUTDTL1 (CIPAUDTY.cpy)       |
| ERRMSGO      | ERRMSGO         | Error message text or SPACES   | — (program-generated)         |

#### 7.2 Input Fields — Received from Terminal

This screen has no UNPROT (operator-enterable) fields. EXEC CICS RECEIVE MAP is not used for data entry. The only action inputs are AID keys (PF3, PF5, PF8) which are read via EIBAID.

#### 7.3 Communication Area (COMMAREA)

COPAUS1C uses the CDEMO-CPVS-COMMAREA (from COSGN00.cpy or equivalent common commarea structure) to pass state between screen interactions:
- The selected authorization key (PA-AUTH-DATE-9C + PA-AUTH-TIME-9C = 8-byte PAUTDTL1 key) is stored in commarea to support F8 (next auth) and F5 (fraud toggle) operations.
- The parent account ID (PA-ACCT-ID) is stored to position GNP calls under the correct root.

[UNRESOLVED] — The exact COMMAREA structure used by COPAUS1C cannot be fully confirmed without reading CDEMO commarea copybooks not present in this codebase directory.

---

### 8. Related Screens

| Screen   | Mapset  | Map    | Transaction | Program  | Relationship                                           |
|----------|---------|--------|-------------|----------|--------------------------------------------------------|
| COPAU00  | COPAU00 | COPAU0A| CPVS        | COPAUS0C | Parent summary list; F3 from COPAU01 returns here      |
| COPAU01  | COPAU01 | COPAU1A| CPVD        | COPAUS1C | This screen; F8 re-sends this map with the next record |

**Navigation entry point:** COPAU01 is reached only from COPAU00 when an operator selects a specific authorization row using the SEL0001–SEL0005 input fields and presses Enter. COPAUS0C then passes the selected key to COPAUS1C via commarea and issues EXEC CICS XCTL PROGRAM('COPAUS1C').

---

### 9. IMS Context for This Screen

The data displayed on COPAU01 comes from a single PAUTDTL1 child segment retrieved from IMS database DBPAUTP0. The segment is 200 bytes and is defined in copybook CIPAUDTY.cpy. The key structure (PA-AUTH-DATE-9C 5-byte COMP-3 + PA-AUTH-TIME-9C 9-byte COMP-3 = 8 bytes) is inverted to force newest records first.

The parent PAUTSUM0 root segment (CIPAUSMY.cpy) provides the account context (PA-ACCT-ID) but its fields are not directly displayed on COPAU01 (they appear on COPAU00).

---

### 10. DB2 Integration

When the operator presses F5 (Mark/Remove Fraud), COPAUS2C is invoked via EXEC CICS LINK. COPAUS2C performs:
1. IMS REPL to toggle PA-AUTH-FRAUD on the PAUTDTL1 segment.
2. EXEC SQL INSERT INTO CARDDEMO.AUTHFRDS with the full transaction detail (26 columns).
3. On SQLCODE -803 (duplicate primary key): EXEC SQL UPDATE CARDDEMO.AUTHFRDS with the fraud flag toggle.
4. EXEC CICS SYNCPOINT (commit both IMS and DB2) or EXEC CICS SYNCPOINT ROLLBACK on failure.

After COPAUS2C returns, COPAUS1C refreshes the COPAU01 screen with the updated AUTHFRDO value ('FRAUD' or 'REMOVED').

---
