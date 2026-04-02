# Technical Specification: COPAU01 BMS Mapset

## Screen Name and Purpose

**Mapset Name:** COPAU01  
**Source File:** `/app/app-authorization-ims-db2-mq/bms/COPAU01.bms`  
**BMS Copybook:** `/app/app-authorization-ims-db2-mq/cpy-bms/COPAU01.cpy`  
**Map Name:** COPAU1A  
**Type:** BMS Map Definition (DFHMSD/DFHMDI/DFHMDF macros)  
**Application:** CardDemo - Authorization Module  
**Function:** Pending Authorization Detail Screen — displays all fields of a single authorization record

COPAU01 defines the detail screen used by program COPAUS1C (transaction CPVD). When an operator selects an authorization from the COPAU00 summary screen, this screen renders the complete set of fields from that authorization record: card number, dates, response details, merchant information, fraud status, and match status. The operator can also toggle the fraud flag (PF5) and navigate to the next authorization (PF8).

---

## Mapset-Level Attributes

Defined at the DFHMSD macro (line 19):

| Attribute | Value | Meaning |
|-----------|-------|---------|
| CTRL | ALARM,FREEKB | Trigger alarm; free keyboard after send |
| EXTATT | YES | Extended attributes supported |
| LANG | COBOL | Generate COBOL copybook |
| MODE | INOUT | Used for input and output |
| STORAGE | AUTO | Auto storage |
| TIOAPFX | YES | TIOA prefix included |
| TYPE | &&SYSPARM | Assembly type from SYSPARM |

---

## Map COPAU1A — Physical Layout

**Map:** COPAU1A  
**Size:** 24 rows x 80 columns (SIZE=(24,80))  
**Start:** COLUMN=1, LINE=1

### Screen Layout Diagram

```
Row 1:  Tran:[TRNNAME] (4)         [TITLE01 (40)                ]   Date:[CURDATE (8)]
Row 2:  Prog:[PGMNAME] (8)         [TITLE02 (40)                ]   Time:[CURTIME (8)]
Row 3:  (blank)
Row 4:                        View Authorization Details
Row 5:  (blank)
Row 6:  (blank)
Row 7:  Card #: [CARDNUM (16)         ]   Auth Date: [AUTHDT (10) ]   Auth Time: [AUTHTM (10)]
Row 8:  (blank)
Row 9:  Auth Resp: [R(1)]  Resp Reason: [AUTHRSN (20)        ]   Auth Code: [AUTHCD (6)]
Row 10: (blank)
Row 11: Amount: [AUTHAMT (12)  ]   POS Entry Mode: [PEMD(4)]   Source   : [AUTHSRC (10)]
Row 12: (blank)
Row 13: MCC Code: [MCC(4)]   Card Exp. Date: [CRDEXP(5)]   Auth Type: [AUTHTYP (14)   ]
Row 14: (blank)
Row 15: Tran Id: [TRNID (15)         ]   Match Status: [M(1)]   Fraud Status: [AUTHFRD (10)]
Row 16: (blank)
Row 17: Merchant Details ---------------------------------------------------------------
Row 18: (blank)
Row 19: Name: [MERNAME (25)           ]   Merchant ID: [MERID (15)    ]
Row 20: (blank)
Row 21: City: [MERCITY (25)           ]   State: [ST(2)]  Zip: [MERZIP (10)  ]
Row 22: (blank)
Row 23: [ERRMSG (78 chars, RED, BRIGHT)                                                ]
Row 24:  F3=Back  F5=Mark/Remove Fraud  F8=Next Auth
```

---

## Field Inventory

### Header Fields (Rows 1–2)

| Field Name | Row | Col | Length | Attribute | Color | Description |
|------------|-----|-----|--------|-----------|-------|-------------|
| (literal) | 1 | 1 | 5 | ASKIP,NORM | BLUE | 'Tran:' |
| TRNNAME | 1 | 7 | 4 | ASKIP,NORM | BLUE | Transaction ID output |
| TITLE01 | 1 | 21 | 40 | ASKIP,NORM | YELLOW | Screen title line 1 |
| (literal) | 1 | 65 | 5 | ASKIP,NORM | BLUE | 'Date:' |
| CURDATE | 1 | 71 | 8 | ASKIP,NORM | BLUE | Current date MM/DD/YY |
| (literal) | 2 | 1 | 5 | ASKIP,NORM | BLUE | 'Prog:' |
| PGMNAME | 2 | 7 | 8 | ASKIP,NORM | BLUE | Program name output |
| TITLE02 | 2 | 21 | 40 | ASKIP,NORM | YELLOW | Screen title line 2 |
| (literal) | 2 | 65 | 5 | ASKIP,NORM | BLUE | 'Time:' |
| CURTIME | 2 | 71 | 8 | ASKIP,NORM | BLUE | Current time HH:MM:SS |

**Note:** Header fields in COPAU01 do not use FSET (unlike COPAU00). This means the values are only transmitted on full-erase send.

### Screen Title

| Row | Col | Length | Color | Content |
|-----|-----|--------|-------|---------|
| 4 | 27 | 26 | NEUTRAL | 'View Authorization Details' (ASKIP,BRT) |

### Authorization Detail Fields (Rows 7–21)

#### Row 7 — Card and Date/Time

| Field Name | Row | Col | Length | Attribute | Color | Description |
|------------|-----|-----|--------|-----------|-------|-------------|
| (literal) | 7 | 2 | 7 | ASKIP,NORM | TURQUOISE | 'Card #:' |
| CARDNUM | 7 | 11 | 16 | ASKIP,NORM | PINK | Card number (output) |
| (literal) | 7 | 31 | 10 | ASKIP,NORM | TURQUOISE | 'Auth Date:' |
| AUTHDT | 7 | 43 | 10 | ASKIP,NORM | PINK | Authorization date MM/DD/YY (output) |
| (literal) | 7 | 56 | 10 | ASKIP,NORM | TURQUOISE | 'Auth Time:' |
| AUTHTM | 7 | 68 | 10 | ASKIP,NORM | PINK | Authorization time HH:MM:SS (output) |

#### Row 9 — Response Information

| Field Name | Row | Col | Length | Attribute | Color | Description |
|------------|-----|-----|--------|-----------|-------|-------------|
| (literal) | 9 | 2 | 10 | ASKIP,NORM | TURQUOISE | 'Auth Resp:' |
| AUTHRSP | 9 | 14 | 1 | ASKIP,NORM | PINK | 'A'=Approved, 'D'=Declined (output, color set by program) |
| (literal) | 9 | 18 | 12 | ASKIP,NORM | TURQUOISE | 'Resp Reason:' |
| AUTHRSN | 9 | 32 | 20 | ASKIP,NORM | BLUE | Decoded reason text e.g. "4100-INSUFFICNT FUND" (output) |
| (literal) | 9 | 56 | 10 | ASKIP,NORM | TURQUOISE | 'Auth Code:' |
| AUTHCD | 9 | 68 | 6 | ASKIP,NORM | BLUE | Authorization ID code (output) |

#### Row 11 — Financial and Technical Details

| Field Name | Row | Col | Length | Attribute | Color | Description |
|------------|-----|-----|--------|-----------|-------|-------------|
| (literal) | 11 | 2 | 7 | ASKIP,NORM | TURQUOISE | 'Amount:' |
| AUTHAMT | 11 | 11 | 12 | ASKIP,NORM | BLUE | Transaction/approved amount (output) |
| (literal) | 11 | 29 | 15 | ASKIP,NORM | TURQUOISE | 'POS Entry Mode:' |
| POSEMD | 11 | 46 | 4 | ASKIP,NORM | BLUE | POS entry mode numeric (output) |
| (literal) | 11 | 56 | 10 | ASKIP,NORM | TURQUOISE | 'Source   :' |
| AUTHSRC | 11 | 68 | 10 | ASKIP,NORM | BLUE | Message source (output) |

#### Row 13 — Card and Merchant Category Details

| Field Name | Row | Col | Length | Attribute | Color | Description |
|------------|-----|-----|--------|-----------|-------|-------------|
| (literal) | 13 | 2 | 9 | ASKIP,NORM | TURQUOISE | 'MCC Code:' |
| MCCCD | 13 | 13 | 4 | ASKIP,NORM | BLUE | Merchant category code (output) |
| (literal) | 13 | 25 | 15 | ASKIP,NORM | TURQUOISE | 'Card Exp. Date:' |
| CRDEXP | 13 | 42 | 5 | ASKIP,NORM | BLUE | Card expiry MM/YY (output) |
| (literal) | 13 | 52 | 10 | ASKIP,NORM | TURQUOISE | 'Auth Type:' |
| AUTHTYP | 13 | 64 | 14 | ASKIP,NORM | BLUE | Authorization type (output) |

#### Row 15 — Transaction and Fraud Status

| Field Name | Row | Col | Length | Attribute | Color | Description |
|------------|-----|-----|--------|-----------|-------|-------------|
| (literal) | 15 | 2 | 18 | ASKIP,NORM | TURQUOISE | 'Tran Id:' (label is 18 chars but content is 'Tran Id:') |
| TRNID | 15 | 12 | 15 | ASKIP,NORM | BLUE | Transaction ID (output) |
| (literal) | 15 | 31 | 13 | ASKIP,NORM | TURQUOISE | 'Match Status:' |
| AUTHMTC | 15 | 46 | 1 | ASKIP,NORM | RED | Match status: P/D/E/M (output) |
| (literal) | 15 | 52 | 13 | ASKIP,NORM | TURQUOISE | 'Fraud Status:' |
| AUTHFRD | 15 | 67 | 10 | ASKIP,NORM | RED | Fraud flag display "F-mmddyyyy" or "-" (output) |

#### Row 17 — Merchant Section Header

| Row | Col | Length | Color | Content |
|-----|-----|--------|-------|---------|
| 17 | 2 | 76 | NEUTRAL | 'Merchant Details ----' (separator line) |

#### Rows 19 and 21 — Merchant Details

| Field Name | Row | Col | Length | Attribute | Color | Description |
|------------|-----|-----|--------|-----------|-------|-------------|
| (literal) | 19 | 2 | 5 | ASKIP,NORM | TURQUOISE | 'Name:' |
| MERNAME | 19 | 9 | 25 | ASKIP,NORM | BLUE | Merchant name (output) |
| (literal) | 19 | 41 | 12 | ASKIP,NORM | TURQUOISE | 'Merchant ID:' |
| MERID | 19 | 55 | 15 | ASKIP,NORM | BLUE | Merchant ID (output) |
| (literal) | 21 | 2 | 5 | ASKIP,NORM | TURQUOISE | 'City:' |
| MERCITY | 21 | 9 | 25 | ASKIP,NORM | BLUE | Merchant city (output) |
| (literal) | 21 | 41 | 6 | ASKIP,NORM | TURQUOISE | 'State:' |
| MERST | 21 | 49 | 2 | ASKIP,NORM | BLUE | Merchant state (output) |
| (literal) | 21 | 55 | 4 | ASKIP,NORM | TURQUOISE | 'Zip:' |
| MERZIP | 21 | 61 | 10 | ASKIP,NORM | BLUE | Merchant ZIP (output) |

### Footer Fields (Rows 23–24)

| Field Name | Row | Col | Length | Attribute | Color | Description |
|------------|-----|-----|--------|-----------|-------|-------------|
| ERRMSG | 23 | 1 | 78 | ASKIP,BRT,FSET | RED | Error/status message |
| (PF guide) | 24 | 1 | 45 | ASKIP,NORM | YELLOW | ' F3=Back  F5=Mark/Remove Fraud  F8=Next Auth' |

---

## Input Fields

This screen is **entirely output** except for ERRMSG (FSET means it will be transmitted back on the receive, but it is protected/ASKIP). There are **no UNPROT (unprotected/editable) input fields** on COPAU01. The operator can only press AID keys (ENTER, PF3, PF5, PF8) — they cannot type data on this screen.

---

## BMS Copybook — COPAU01.cpy Structures

The generated copybook defines:

- **01 COPAU1AI** — Input structure (suffix I for data fields)
- **01 COPAU1AO REDEFINES COPAU1AI** — Output structure (suffix O/C/P/H/V)

Fields in COPAU1AI (lines 17–180 of COPAU01.cpy):

| Map Field | Input Field | Length |
|-----------|-------------|--------|
| TRNNAME | TRNNAMEI | X(4) |
| TITLE01 | TITLE01I | X(40) |
| CURDATE | CURDATEI | X(8) |
| PGMNAME | PGMNAMEI | X(8) |
| TITLE02 | TITLE02I | X(40) |
| CURTIME | CURTIMEI | X(8) |
| CARDNUM | CARDNUMI | X(16) |
| AUTHDT | AUTHDTI | X(10) |
| AUTHTM | AUTHTMI | X(10) |
| AUTHRSP | AUTHRSPI | X(1) |
| AUTHRSN | AUTHRSNI | X(20) |
| AUTHCD | AUTHCDI | X(6) |
| AUTHAMT | AUTHAMTI | X(12) |
| POSEMD | POSEMDI | X(4) |
| AUTHSRC | AUTHSRCI | X(10) |
| MCCCD | MCCCDI | X(4) |
| CRDEXP | CRDEXPI | X(5) |
| AUTHTYP | AUTHTYPI | X(14) |
| TRNID | TRNIDI | X(15) |
| AUTHMTC | AUTHMTCI | X(1) |
| AUTHFRD | AUTHFRDI | X(10) |
| MERNAME | MERNAMEI | X(25) |
| MERID | MERIDI | X(15) |
| MERCITY | MERCITYI | X(25) |
| MERST | MERSTI | X(2) |
| MERZIP | MERZIPI | X(10) |
| ERRMSG | ERRMSGI | X(78) |

---

## Attribute Summary

| Category | Fields | Attribute |
|----------|--------|-----------|
| All data output fields | CARDNUM, AUTHDT, AUTHTM, AUTHRSP, AUTHRSN, AUTHCD, AUTHAMT, POSEMD, AUTHSRC, MCCCD, CRDEXP, AUTHTYP, TRNID, AUTHMTC, AUTHFRD, MERNAME, MERID, MERCITY, MERST, MERZIP | ASKIP,NORM (protected, no input) |
| Error message | ERRMSG | ASKIP,BRT,FSET (bright, red, transmitted back) |
| Labels/literals | All literal text | ASKIP,NORM |
| Title area | TITLE01, TITLE02 | ASKIP,NORM, YELLOW |

This screen is read-only — the only user interaction is via function keys.

---

## Dynamic Attribute Modification in COPAUS1C

COPAUS1C modifies field attributes at runtime:

| Field | Condition | Color Set |
|-------|-----------|-----------|
| AUTHRSP | PA-AUTH-RESP-CODE = '00' (approved) | DFHGREEN |
| AUTHRSP | PA-AUTH-RESP-CODE != '00' (declined) | DFHRED |

The AUTHRSN field combines the decline reason code and description: `"4100-INSUFFICNT FUND"`. The color remains BLUE (defined in BMS) regardless.

---

## Screen Navigation

| Key | Action in COPAUS1C |
|-----|--------------------|
| ENTER | Re-read and refresh the current authorization |
| PF3 | XCTL back to COPAUS0C (summary list) |
| PF5 | Toggle fraud flag: LINK to COPAUS2C, then IMS REPL |
| PF8 | GNP to next authorization in IMS, display it |
| Any other key | Display CCDA-MSG-INVALID-KEY error |

---

## Field-to-Program-to-Copybook Mapping

| Screen Field | Map Output Field | Source in COPAUS1C | Source Data |
|-------------|------------------|--------------------|-------------|
| CARDNUM | CARDNUMO | Direct MOVE | PA-CARD-NUM (CIPAUDTY) |
| AUTHDT | AUTHDTO | WS-AUTH-DATE | PA-AUTH-ORIG-DATE reformatted MM/DD/YY |
| AUTHTM | AUTHTMO | WS-AUTH-TIME | PA-AUTH-ORIG-TIME formatted HH:MM:SS |
| AUTHRSP | AUTHRSPO | 'A' or 'D' | PA-AUTH-RESP-CODE = '00' ? |
| AUTHRSN | AUTHRSNO | SEARCH ALL result | WS-DECLINE-REASON-TAB(code)-'-'-description |
| AUTHCD | AUTHCDO | Direct MOVE | PA-PROCESSING-CODE |
| AUTHAMT | AUTHAMTO | WS-AUTH-AMT | PA-APPROVED-AMT formatted |
| POSEMD | POSEMDO | Direct MOVE | PA-POS-ENTRY-MODE |
| AUTHSRC | AUTHSRCO | Direct MOVE | PA-MESSAGE-SOURCE |
| MCCCD | MCCCDO | Direct MOVE | PA-MERCHANT-CATAGORY-CODE |
| CRDEXP | CRDEXPO | Formatted MM/YY | PA-CARD-EXPIRY-DATE positions 1-2 '/' 3-4 |
| AUTHTYP | AUTHTYPO | Direct MOVE | PA-AUTH-TYPE |
| TRNID | TRNIDO | Direct MOVE | PA-TRANSACTION-ID |
| AUTHMTC | AUTHMTCO | Direct MOVE | PA-MATCH-STATUS |
| AUTHFRD | AUTHFRDO | Conditional format | PA-AUTH-FRAUD + '-' + PA-FRAUD-RPT-DATE, or '-' |
| MERNAME | MERNAMEO | Direct MOVE | PA-MERCHANT-NAME |
| MERID | MERIDO | Direct MOVE | PA-MERCHANT-ID |
| MERCITY | MERCITYO | Direct MOVE | PA-MERCHANT-CITY |
| MERST | MERSTO | Direct MOVE | PA-MERCHANT-STATE |
| MERZIP | MERZIPO | Direct MOVE | PA-MERCHANT-ZIP |
| ERRMSG | ERRMSGO | WS-MESSAGE | Error/info messages |
| TRNNAME | TRNNAMEO | WS-CICS-TRANID | 'CPVD' |
| PGMNAME | PGMNAMEO | WS-PGM-AUTH-DTL | 'COPAUS1C' |
| TITLE01 | TITLE01O | CCDA-TITLE01 | From COTTL01Y |
| TITLE02 | TITLE02O | CCDA-TITLE02 | From COTTL01Y |
| CURDATE | CURDATEO | WS-CURDATE-MM-DD-YY | CSDAT01Y formatted |
| CURTIME | CURTIMEO | WS-CURTIME-HH-MM-SS | CSDAT01Y formatted |

---

## Comparison: COPAU00 vs COPAU01

| Attribute | COPAU00 (Summary) | COPAU01 (Detail) |
|-----------|-------------------|------------------|
| Map name | COPAU0A | COPAU1A |
| Program | COPAUS0C | COPAUS1C |
| Transaction | CPVS | CPVD |
| Input fields | ACCTID + 5x SEL00nn | None (PF keys only) |
| Output rows | Up to 5 auth list rows | Single auth record, all fields |
| PF7/PF8 | Page backward/forward through list | PF8 = next single auth record |
| PF5 | Not handled | Fraud flag toggle |
| ERRMSG | Row 23, RED, BRT, FSET | Row 23, RED, BRT, FSET |
| Header FSET | Yes (FSET on header fields) | No (no FSET on most headers) |
