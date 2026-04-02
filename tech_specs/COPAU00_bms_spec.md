# Technical Specification: COPAU00 BMS Mapset

## Screen Name and Purpose

**Mapset Name:** COPAU00  
**Source File:** `/app/app-authorization-ims-db2-mq/bms/COPAU00.bms`  
**BMS Copybook:** `/app/app-authorization-ims-db2-mq/cpy-bms/COPAU00.cpy`  
**Map Name:** COPAU0A  
**Type:** BMS Map Definition (DFHMSD/DFHMDI/DFHMDF macros)  
**Application:** CardDemo - Authorization Module  
**Function:** Pending Authorization Summary Screen — Account search and paginated authorization list

COPAU00 defines the screen used by program COPAUS0C (transaction CPVS) to display a searchable, paginated list of pending authorization transactions for a given account. The screen is a 24-row by 80-column 3270 terminal screen presenting account demographics, financial summary, and up to 5 authorization records per page.

---

## Mapset-Level Attributes

Defined at the DFHMSD macro (line 19):

| Attribute | Value | Meaning |
|-----------|-------|---------|
| CTRL | ALARM,FREEKB | Trigger alarm on send; free keyboard after send |
| EXTATT | YES | Extended attributes supported |
| LANG | COBOL | Generates COBOL copybook |
| MODE | INOUT | Map used for both input and output |
| STORAGE | AUTO | Automatic working storage allocation |
| TIOAPFX | YES | TIOA prefix generated |
| TYPE | &&SYSPARM | Assembly type controlled by SYSPARM |

---

## Map COPAU0A — Physical Layout

**Map:** COPAU0A  
**Size:** 24 rows x 80 columns (SIZE=(24,80))  
**Start:** COLUMN=1, LINE=1

### Screen Layout Diagram

```
Row 1:  Tran:[TRNNAME  ]         [     TITLE01 (40 chars)          ]   Date:[CURDATE ]
Row 2:  Prog:[PGMNAME  ]         [     TITLE02 (40 chars)          ]   Time:[CURTIME ]
Row 3:                               View Authorizations
Row 4:  (blank)
Row 5:  Search Acct Id:[ACCTID        ]
Row 6:  Name: [CNAME                  ]   Customer Id: [CUSTID   ]
Row 7:  [ADDR001               ]          Acct Status: [A]
Row 8:  [ADDR002               ]
Row 9:  PH:[PHONE1          ]           Approval # :[APR] Decline #:[DEC]
Row 10: (blank)
Row 11: Credit Lim:[CREDLIM       ]  Cash Lim:[CASHLIM ]  Appr Amt:[APPRAMT   ]
Row 12: Credit Bal:[CREDBAL       ]  Cash Bal:[CASHBAL ]  Decl Amt:[DECLAMT   ]
Row 13: (blank)
Row 14: Sel  Transaction ID      Date      Time    Type  A/D STS    Amount
Row 15: ---  ----------------  --------  --------  ----  ---  ---  ------------
Row 16: [S1] [TRNID01          ] [PDATE01 ] [PTIME01 ] [TY01] [A1] [ST1] [PAMT001    ]
Row 17: [S2] [TRNID02          ] [PDATE02 ] [PTIME02 ] [TY02] [A2] [ST2] [PAMT002    ]
Row 18: [S3] [TRNID03          ] [PDATE03 ] [PTIME03 ] [TY03] [A3] [ST3] [PAMT003    ]
Row 19: [S4] [TRNID04          ] [PDATE04 ] [PTIME04 ] [TY04] [A4] [ST4] [PAMT004    ]
Row 20: [S5] [TRNID05          ] [PDATE05 ] [PTIME05 ] [TY05] [A5] [ST5] [PAMT005    ]
Row 21: (blank)
Row 22:            Type 'S' to View Authorization details from the list
Row 23: [ERRMSG (78 chars, RED, BRIGHT)                                              ]
Row 24: ENTER=Continue  F3=Back  F7=Backward  F8=Forward
```

---

## Field Inventory

### Header Fields (Rows 1–2)

| Field Name | Row | Col | Length | Attribute | Color | Description |
|------------|-----|-----|--------|-----------|-------|-------------|
| (literal) | 1 | 1 | 5 | ASKIP,NORM | BLUE | 'Tran:' label |
| TRNNAME | 1 | 7 | 4 | ASKIP,FSET,NORM | BLUE | Transaction ID (output) |
| TITLE01 | 1 | 21 | 40 | ASKIP,FSET,NORM | YELLOW | Screen title line 1 |
| (literal) | 1 | 65 | 5 | ASKIP,NORM | BLUE | 'Date:' label |
| CURDATE | 1 | 71 | 8 | ASKIP,FSET,NORM | BLUE | Current date MM/DD/YY |
| (literal) | 2 | 1 | 5 | ASKIP,NORM | BLUE | 'Prog:' label |
| PGMNAME | 2 | 7 | 8 | ASKIP,FSET,NORM | BLUE | Program name (output) |
| TITLE02 | 2 | 21 | 40 | ASKIP,FSET,NORM | YELLOW | Screen title line 2 |
| (literal) | 2 | 65 | 5 | ASKIP,NORM | BLUE | 'Time:' label |
| CURTIME | 2 | 71 | 8 | ASKIP,FSET,NORM | BLUE | Current time HH:MM:SS |

### Search and Account Information (Rows 3–12)

| Field Name | Row | Col | Length | Attribute | Color | Description |
|------------|-----|-----|--------|-----------|-------|-------------|
| (literal) | 3 | 30 | 19 | — | NEUTRAL | 'View Authorizations' |
| (literal) | 5 | 3 | 15 | ASKIP,NORM | TURQUOISE | 'Search Acct Id:' |
| ACCTID | 5 | 19 | 11 | FSET,NORM,UNPROT | GREEN | Account ID input field (UNDERLINE highlight) |
| (stopper) | 5 | 31 | 0 | ASKIP,NORM | — | Cursor stop after ACCTID |
| (literal) | 6 | 3 | 6 | — | DEFAULT | 'Name: ' |
| CNAME | 6 | 10 | 25 | ASKIP,NORM | BLUE | Customer name (output) |
| (literal) | 6 | 44 | 13 | — | — | 'Customer Id: ' |
| CUSTID | 6 | 58 | 9 | ASKIP,NORM | BLUE | Customer ID (output) |
| ADDR001 | 7 | 10 | 25 | ASKIP,NORM | BLUE | Address line 1 (output) |
| (literal) | 7 | 44 | 13 | — | — | 'Acct Status: ' |
| ACCSTAT | 7 | 58 | 1 | ASKIP,NORM | BLUE | Account status code (output) |
| ADDR002 | 8 | 10 | 25 | ASKIP,NORM | BLUE | Address line 2 (output) |
| (literal) | 9 | 10 | 3 | — | — | 'PH:' |
| PHONE1 | 9 | 15 | 13 | ASKIP,NORM | BLUE | Phone number (output) |
| (literal) | 9 | 44 | 13 | — | — | 'Approval # : ' |
| APPRCNT | 9 | 58 | 3 | ASKIP,NORM | BLUE | Approved authorization count (output) |
| (literal) | 9 | 64 | 10 | — | — | 'Decline #:' |
| DECLCNT | 9 | 76 | 3 | ASKIP,NORM | BLUE | Declined authorization count (output) |
| (literal) | 11 | 6 | 11 | — | DEFAULT | 'Credit Lim:' |
| CREDLIM | 11 | 19 | 12 | ASKIP,FSET,NORM | BLUE | Credit limit (output) |
| (literal) | 11 | 35 | 9 | — | DEFAULT | 'Cash Lim:' |
| CASHLIM | 11 | 46 | 9 | ASKIP,FSET,NORM | BLUE | Cash limit (output) |
| (literal) | 11 | 58 | 9 | — | DEFAULT | 'Appr Amt:' |
| APPRAMT | 11 | 69 | 10 | ASKIP,FSET,NORM | BLUE | Approved amount total (output) |
| (literal) | 12 | 6 | 11 | — | DEFAULT | 'Credit Bal:' |
| CREDBAL | 12 | 19 | 12 | ASKIP,FSET,NORM | BLUE | Credit balance (output) |
| (literal) | 12 | 35 | 9 | — | DEFAULT | 'Cash Bal:' |
| CASHBAL | 12 | 46 | 9 | ASKIP,FSET,NORM | BLUE | Cash balance (output) |
| (literal) | 12 | 58 | 9 | — | DEFAULT | 'Decl Amt:' |
| DECLAMT | 12 | 69 | 10 | ASKIP,FSET,NORM | BLUE | Declined amount total (output) |

### Authorization List Header (Rows 14–15)

Column headers are ASKIP,NORM NEUTRAL literals:
- Row 14: 'Sel' (col 2), 'Transaction ID' (col 8), 'Date' (col 27), 'Time' (col 38), 'Type' (col 49), 'A/D' (col 56), 'STS' (col 61), 'Amount' (col 67)
- Row 15: Separator dashes

### Authorization List Rows (Rows 16–20) — 5 Repeating Row Groups

Each row has the same structure. The 5 sets are defined individually (no BMS OCCURS support):

**Row structure for each of the 5 authorization rows:**

| Field Name | Col | Length | Attribute | Color | Description |
|------------|-----|--------|-----------|-------|-------------|
| SEL000n | 3 | 1 | FSET,NORM,UNPROT | GREEN+UNDERLINE | Selection input ('S' to select) |
| (stopper) | 5 | 0 | ASKIP,NORM | — | Input stop after selection |
| TRNIDnn | 8 | 16 | ASKIP,FSET,NORM | BLUE | Transaction ID (output) |
| PDATEnn | 27 | 8 | ASKIP,FSET,NORM | BLUE | Auth date MM/DD/YY (output) |
| PTIMEnn | 38 | 8 | ASKIP,FSET,NORM | BLUE | Auth time HH:MM:SS (output) |
| PTYPEnn | 49 | 4 | ASKIP,FSET,NORM | BLUE | Auth type (output) |
| PAPRVnn | 58 | 1 | ASKIP,FSET,NORM | BLUE | A=Approved, D=Declined (output) |
| PSTATnn | 63 | 1 | ASKIP,FSET,NORM | BLUE | Match status (output) |
| PAMTnnn | 67 | 12 | ASKIP,FSET,NORM | BLUE | Amount (output) |

Where nn = 01–05, nnn = 001–005.

**Row assignments:**
- Row 16: SEL0001, TRNID01, PDATE01, PTIME01, PTYPE01, PAPRV01, PSTAT01, PAMT001
- Row 17: SEL0002, TRNID02, PDATE02, PTIME02, PTYPE02, PAPRV02, PSTAT02, PAMT002
- Row 18: SEL0003, TRNID03, PDATE03, PTIME03, PTYPE03, PAPRV03, PSTAT03, PAMT003
- Row 19: SEL0004, TRNID04, PDATE04, PTIME04, PTYPE04, PAPRV04, PSTAT04, PAMT004
- Row 20: SEL0005, TRNID05, PDATE05, PTIME05, PTYPE05, PAPRV05, PSTAT05, PAMT005

**Note:** Row 20 is slightly anomalous — the SEL0005 field definition (line 488) is placed after the five data fields TRNID05–PAMT005 (lines 453–486) rather than before them. COPAUS0C reads the five SEL fields from COPAU0AI input area, so this ordering affects the attribute byte position in the TIOA.

### Footer Fields (Rows 22–24)

| Field | Row | Col | Length | Attribute | Color | Description |
|-------|-----|-----|--------|-----------|-------|-------------|
| (instruction) | 22 | 12 | 52 | ASKIP,BRT | NEUTRAL | "Type 'S' to View Authorization details from the list" |
| ERRMSG | 23 | 1 | 78 | ASKIP,BRT,FSET | RED | Error/status messages |
| (PF key guide) | 24 | 1 | 48 | ASKIP,NORM | YELLOW | 'ENTER=Continue  F3=Back  F7=Backward  F8=Forward' |

---

## BMS Copybook Generated Structures (COPAU00.cpy)

The generated copybook defines two 01-level areas:

- **COPAU0AI** — input area (suffix I fields): used for EXEC CICS RECEIVE MAP
- **COPAU0AO** — output area redefined over COPAU0AI (suffix O/C/P/H/V fields): used for EXEC CICS SEND MAP

For each named field (e.g., ACCTID), the copybook generates:
- `ACCTIDl` COMP PIC S9(4) — length of data received
- `ACCTIDf` PICTURE X — flag byte
- `ACCTIDa` PICTURE X — attribute byte (redefines flag)
- FILLER PICTURE X(4) — color/hilight/etc.
- `ACCTIDI` PIC X(11) — input data
- `ACCTIDO` PIC X(11) — output data (in O area)
- `ACCTIDP/H/V/C` — pen/highlight/validation/color control bytes (in O area)

---

## Attribute Summary

| Category | Fields | Attribute |
|----------|--------|-----------|
| Input fields | ACCTID, SEL0001–SEL0005 | UNPROT (editable), FSET (transmit even if unchanged) |
| Output labels | Most literals | ASKIP,NORM (protected) |
| Output data | TRNNAME, CURDATE, CURTIME, PGMNAME, TITLE01, TITLE02, CREDLIM, CASHLIM, etc. | ASKIP,FSET,NORM |
| Error message | ERRMSG | ASKIP,BRT,FSET (bright for visibility) |
| Selection instruction | Row 22 text | ASKIP,BRT |
| PF key guide | Row 24 text | ASKIP,NORM,YELLOW |

---

## Screen Navigation

| Key | Action in COPAUS0C |
|-----|--------------------|
| ENTER | Process account ID entry or selection; refresh page |
| PF3 | XCTL to COMEN01C (main menu) |
| PF7 | Page backward in authorization list |
| PF8 | Page forward in authorization list |
| PF5 | Not handled in COPAUS0C (defaults to invalid key message) |
| Type 'S' in selection field + ENTER | XCTL to COPAUS1C with selected auth key |

---

## Field-to-Program-to-Copybook Mapping

| Screen Field | Map Field | COPAUS0C Source | Source Data |
|-------------|-----------|-----------------|-------------|
| ACCTID | ACCTIDI/O | WS-ACCT-ID | User input / CDEMO-ACCT-ID |
| CNAME | CNAMEO | Formatted from CVCUS01Y | CUST-FIRST/MIDDLE/LAST-NAME |
| CUSTID | CUSTIDO | CUST-ID | From CVCUS01Y |
| ADDR001 | ADDR001O | Formatted | CUST-ADDR-LINE-1 + LINE-2 |
| ADDR002 | ADDR002O | Formatted | CUST-ADDR-LINE-3 + STATE + ZIP |
| PHONE1 | PHONE1O | Direct | CUST-PHONE-NUM-1 |
| CREDLIM | CREDLIMO | Formatted amount | ACCT-CREDIT-LIMIT |
| CASHLIM | CASHLIMO | Formatted amount | ACCT-CASH-CREDIT-LIMIT |
| CREDBAL | CREDBALO | Formatted amount | PA-CREDIT-BALANCE (CIPAUSMY) |
| CASHBAL | CASHBALO | Formatted amount | PA-CASH-BALANCE (CIPAUSMY) |
| APPRCNT | APPRCNTO | WS-DISPLAY-COUNT | PA-APPROVED-AUTH-CNT |
| DECLCNT | DECLCNTO | WS-DISPLAY-COUNT | PA-DECLINED-AUTH-CNT |
| APPRAMT | APPRAMTO | Formatted amount | PA-APPROVED-AUTH-AMT |
| DECLAMT | DECLAMTO | Formatted amount | PA-DECLINED-AUTH-AMT |
| TRNIDnn | TRNIDnnI/O | PA-TRANSACTION-ID | From CIPAUDTY |
| PDATEnn | PDATEnnI/O | WS-AUTH-DATE | Formatted PA-AUTH-ORIG-DATE |
| PTIMEnn | PTIMEnnI/O | WS-AUTH-TIME | Formatted PA-AUTH-ORIG-TIME |
| PTYPEnn | PTYPEnnI/O | PA-AUTH-TYPE | From CIPAUDTY |
| PAPRVnn | PAPRVnnI/O | WS-AUTH-APRV-STAT | 'A'/'D' from PA-AUTH-RESP-CODE |
| PSTATnn | PSTATnnI/O | PA-MATCH-STATUS | From CIPAUDTY |
| PAMTnnn | PAMTnnnI/O | WS-AUTH-AMT | PA-APPROVED-AMT formatted |
| ERRMSG | ERRMSGO | WS-MESSAGE | Error/info messages |
| TRNNAME | TRNNAMEO | WS-CICS-TRANID | 'CPVS' |
| PGMNAME | PGMNAMEO | WS-PGM-AUTH-SMRY | 'COPAUS0C' |
| TITLE01 | TITLE01O | CCDA-TITLE01 | From COTTL01Y |
| TITLE02 | TITLE02O | CCDA-TITLE02 | From COTTL01Y |
| CURDATE | CURDATEO | WS-CURDATE-MM-DD-YY | CSDAT01Y formatted |
| CURTIME | CURTIMEO | WS-CURTIME-HH-MM-SS | CSDAT01Y formatted |
