# Technical Specification: COPAU00
## Authorization Summary Screen

---

### 1. Screen Overview

| Attribute        | Value                                               |
|------------------|-----------------------------------------------------|
| Mapset Name      | COPAU00                                             |
| Map Name         | COPAU0A                                             |
| BMS Source       | bms/COPAU00.bms                                     |
| BMS Copybook     | cpy-bms/COPAU00.cpy                                 |
| Owning Program   | COPAUS0C                                            |
| Transaction ID   | CPVS                                                |
| Size             | 24 rows x 80 columns                               |
| Purpose          | Display list of pending authorizations for an account |
| CSD Definition   | CRDDEMO2.csd: DEFINE MAPSET(COPAU00) GROUP(CARDDEMO) |

**Description:** This screen allows an operator to search for pending authorization records by account ID. The account and customer summary information is displayed in the upper portion of the screen, and up to 5 authorization records are listed in rows. The operator selects a record using 'S' and presses ENTER to navigate to the authorization detail screen (COPAU01).

---

### 2. Map Definition

| BMS Attribute | Value                              |
|---------------|------------------------------------|
| CTRL          | (ALARM,FREEKB)                     |
| EXTATT        | YES                                |
| LANG          | COBOL                              |
| MODE          | INOUT                              |
| STORAGE       | AUTO                               |
| TIOAPFX       | YES                                |
| TYPE          | &&SYSPARM                          |

DFHMDI parameters: COLUMN=1, LINE=1, SIZE=(24,80).

---

### 3. Screen Layout (ASCII Art)

```
Col:  1234567890123456789012345678901234567890123456789012345678901234567890123456789
      |        |        |        |        |        |        |        |        |
Row1: Tran:XXXX                  TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT  Date:DDDDDDDD
Row2: Prog:PPPPPPPP              TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT  Time:TTTTTTTT
Row3:                            View Authorizations
Row4:
Row5:    Search Acct Id: AAAAAAAAAAA
Row6:    Name:  NNNNNNNNNNNNNNNNNNNNNNNNN   Customer Id:  CCCCCCCCC
Row7:           AAAAAAAAAAAAAAAAAAAAAAAAAAA Acct Status:  S
Row8:           AAAAAAAAAAAAAAAAAAAAAAAAAAA
Row9:       PH: PPPPPPPPPPPPP              Approval # : NNN Decline #:NNN
Row10:
Row11:    Credit Lim: LLLLLLLLLLLL  Cash Lim: CCCCCCCCC  Appr Amt: AAAAAAAAAA
Row12:    Credit Bal: BBBBBBBBBBBB  Cash Bal: CCCCCCCCC  Decl Amt: DDDDDDDDDD
Row13:
Row14:  Sel  Transaction ID     Date     Time    Type  A/D STS    Amount
Row15:  ---  ----------------  --------  --------  ----  ---  ---  ------------
Row16:  _    XXXXXXXXXXXXXXXX  MM/DD/YY  HH:MM:SS  TTTT  A   P    -zzzzzzzz9.99
Row17:  _    XXXXXXXXXXXXXXXX  MM/DD/YY  HH:MM:SS  TTTT  A   P    -zzzzzzzz9.99
Row18:  _    XXXXXXXXXXXXXXXX  MM/DD/YY  HH:MM:SS  TTTT  A   P    -zzzzzzzz9.99
Row19:  _    XXXXXXXXXXXXXXXX  MM/DD/YY  HH:MM:SS  TTTT  A   P    -zzzzzzzz9.99
Row20:  _    XXXXXXXXXXXXXXXX  MM/DD/YY  HH:MM:SS  TTTT  A   P    -zzzzzzzz9.99
Row21:
Row22:            Type 'S' to View Authorization details from the list
Row23: [ERROR MESSAGE IN RED - 78 chars                                         ]
Row24: ENTER=Continue  F3=Back  F7=Backward  F8=Forward
```

**Legend:** `_` = input field (underlined green), `X` = output data field (blue), labels are fixed literals.

---

### 4. Field Definitions

All fields listed with BMS position (row, column), length, and attributes.

#### 4.1 Header Fields

| Field Name | BMS Name | Row | Col | Len | Attr           | Color  | Description                        |
|------------|----------|-----|-----|-----|----------------|--------|------------------------------------|
| (literal)  | —        | 1   | 1   | 5   | ASKIP,NORM     | BLUE   | 'Tran:' label                      |
| TRNNAME    | TRNNAME  | 1   | 7   | 4   | ASKIP,FSET,NORM| BLUE   | Current transaction ID (CPVS)      |
| TITLE01    | TITLE01  | 1   | 21  | 40  | ASKIP,FSET,NORM| YELLOW | Application title line 1           |
| (literal)  | —        | 1   | 65  | 5   | ASKIP,NORM     | BLUE   | 'Date:' label                      |
| CURDATE    | CURDATE  | 1   | 71  | 8   | ASKIP,FSET,NORM| BLUE   | Current date mm/dd/yy              |
| (literal)  | —        | 2   | 1   | 5   | ASKIP,NORM     | BLUE   | 'Prog:' label                      |
| PGMNAME    | PGMNAME  | 2   | 7   | 8   | ASKIP,FSET,NORM| BLUE   | Current program name (COPAUS0C)    |
| TITLE02    | TITLE02  | 2   | 21  | 40  | ASKIP,FSET,NORM| YELLOW | Application title line 2           |
| (literal)  | —        | 2   | 65  | 5   | ASKIP,NORM     | BLUE   | 'Time:' label                      |
| CURTIME    | CURTIME  | 2   | 71  | 8   | ASKIP,FSET,NORM| BLUE   | Current time hh:mm:ss              |
| (literal)  | —        | 3   | 30  | 19  | COLOR=NEUTRAL  | NEUTRAL| 'View Authorizations' subtitle     |

#### 4.2 Search / Account Fields

| Field Name | BMS Name | Row | Col | Len | Attr                   | Color     | Description                              |
|------------|----------|-----|-----|-----|------------------------|-----------|------------------------------------------|
| (literal)  | —        | 5   | 3   | 15  | ASKIP,NORM             | TURQUOISE | 'Search Acct Id:' label                  |
| ACCTID     | ACCTID   | 5   | 19  | 11  | FSET,NORM,UNPROT; HILIGHT=UNDERLINE | GREEN | Account ID input field (editable)  |
| (stopper)  | —        | 5   | 31  | 0   | ASKIP,NORM             | —         | Auto-skip stopper after ACCTID           |
| (literal)  | —        | 6   | 3   | 6   | —                      | DEFAULT   | 'Name: ' label                           |
| CNAME      | CNAME    | 6   | 10  | 25  | ASKIP,NORM             | BLUE      | Customer name                            |
| (literal)  | —        | 6   | 44  | 13  | —                      | —         | 'Customer Id: ' label                    |
| CUSTID     | CUSTID   | 6   | 58  | 9   | ASKIP,NORM             | BLUE      | Customer ID                              |
| ADDR001    | ADDR001  | 7   | 10  | 25  | ASKIP,NORM             | BLUE      | Address line 1                           |
| (literal)  | —        | 7   | 44  | 13  | —                      | —         | 'Acct Status: ' label                    |
| ACCSTAT    | ACCSTAT  | 7   | 58  | 1   | ASKIP,NORM             | BLUE      | Account status (1 char)                  |
| ADDR002    | ADDR002  | 8   | 10  | 25  | ASKIP,NORM             | BLUE      | Address line 2                           |
| (literal)  | —        | 9   | 10  | 3   | —                      | —         | 'PH:' label                              |
| PHONE1     | PHONE1   | 9   | 15  | 13  | ASKIP,NORM             | BLUE      | Phone number                             |
| (literal)  | —        | 9   | 44  | 13  | —                      | —         | 'Approval # : ' label                    |
| APPRCNT    | APPRCNT  | 9   | 58  | 3   | ASKIP,NORM             | BLUE      | Count of approved authorizations         |
| (literal)  | —        | 9   | 64  | 10  | —                      | —         | 'Decline #:' label                       |
| DECLCNT    | DECLCNT  | 9   | 76  | 3   | ASKIP,NORM             | BLUE      | Count of declined authorizations         |

#### 4.3 Financial Summary Fields

| Field Name | BMS Name | Row | Col | Len | Attr           | Color   | Description                         |
|------------|----------|-----|-----|-----|----------------|---------|-------------------------------------|
| (literal)  | —        | 11  | 6   | 11  | —              | DEFAULT | 'Credit Lim:' label                 |
| CREDLIM    | CREDLIM  | 11  | 19  | 12  | ASKIP,FSET,NORM| BLUE    | Credit limit                        |
| (literal)  | —        | 11  | 35  | 9   | —              | DEFAULT | 'Cash Lim:' label                   |
| CASHLIM    | CASHLIM  | 11  | 46  | 9   | ASKIP,FSET,NORM| BLUE    | Cash limit                          |
| (literal)  | —        | 11  | 58  | 9   | —              | DEFAULT | 'Appr Amt:' label                   |
| APPRAMT    | APPRAMT  | 11  | 69  | 10  | ASKIP,FSET,NORM| BLUE    | Total approved amount               |
| (literal)  | —        | 12  | 6   | 11  | —              | DEFAULT | 'Credit Bal:' label                 |
| CREDBAL    | CREDBAL  | 12  | 19  | 12  | ASKIP,FSET,NORM| BLUE    | Credit balance                      |
| (literal)  | —        | 12  | 35  | 9   | —              | DEFAULT | 'Cash Bal:' label                   |
| CASHBAL    | CASHBAL  | 12  | 46  | 9   | ASKIP,FSET,NORM| BLUE    | Cash balance                        |
| (literal)  | —        | 12  | 58  | 9   | —              | DEFAULT | 'Decl Amt:' label                   |
| DECLAMT    | DECLAMT  | 12  | 69  | 10  | ASKIP,FSET,NORM| BLUE    | Total declined amount               |

#### 4.4 Authorization List Column Headers (Row 14–15)

| Row | Col | Len | Content                             |
|-----|-----|-----|-------------------------------------|
| 14  | 2   | 3   | 'Sel'                               |
| 14  | 8   | 16  | ' Transaction ID '                  |
| 14  | 27  | 8   | '  Date  '                          |
| 14  | 38  | 8   | '  Time  '                          |
| 14  | 49  | 5   | 'Type '                             |
| 14  | 56  | 3   | 'A/D'                               |
| 14  | 61  | 3   | 'STS'                               |
| 14  | 67  | 12  | '   Amount   '                      |
| 15  | 2   | 3   | '---' (separator)                   |
| 15  | 8   | 16  | '----------------' (separator)      |
| 15  | 27  | 8   | '--------'                          |
| 15  | 37  | 8   | '--------'                          |
| 15  | 49  | 4   | '----'                              |
| 15  | 56  | 3   | '---'                               |
| 15  | 61  | 3   | '---'                               |
| 15  | 67  | 12  | '------------'                      |

#### 4.5 Authorization List Detail Rows (5 rows, rows 16–20)

Each row n (n=1..5) at BMS row (15+n) contains the following fields:

| Field Suffix | BMS Name (n=01–05) | Col | Len | Attr                        | Color | Description                     |
|--------------|---------------------|-----|-----|-----------------------------|-------|---------------------------------|
| SEL000n      | SEL000n             | 3   | 1   | FSET,NORM,UNPROT; UNDERLINE | GREEN | Selection input ('S' or space)  |
| (stopper)    | —                   | 5   | 0   | ASKIP,NORM                  | —     | Skip stopper after selection    |
| TRNIDnn      | TRNIDnn             | 8   | 16  | ASKIP,FSET,NORM             | BLUE  | Transaction ID (from PAUTDTL1)  |
| PDATEnn      | PDATEnn             | 27  | 8   | ASKIP,FSET,NORM             | BLUE  | Authorization date MM/DD/YY     |
| PTIMEnn      | PTIMEnn             | 38  | 8   | ASKIP,FSET,NORM             | BLUE  | Authorization time HH:MM:SS     |
| PTYPEnn      | PTYPEnn             | 49  | 4   | ASKIP,FSET,NORM             | BLUE  | Authorization type              |
| PAPRVnn      | PAPRVnn             | 58  | 1   | ASKIP,FSET,NORM             | BLUE  | Approval status 'A'=Approved 'D'=Declined |
| PSTATnn      | PSTATnn             | 63  | 1   | ASKIP,FSET,NORM             | BLUE  | Match status code               |
| PAMTnnn      | PAMTnnn             | 67  | 12  | ASKIP,FSET,NORM             | BLUE  | Approved amount (formatted)     |

**Note on row 20 (row 5):** BMS source shows TRNID05 at position (20,8) appearing BEFORE SEL0005 at position (20,3). The order in the source is: TRNID05, PDATE05, PTIME05, PTYPE05, PAPRV05, PSTAT05, PAMT005, SEL0005. This is a minor anomaly in the BMS source — at runtime the TIOAPFX=YES generates the fields in map order, but visually all fields appear at their correct column positions.

#### 4.6 Navigation / Message Fields

| BMS Name | Row | Col | Len | Attr               | Color   | Description                                |
|----------|-----|-----|-----|--------------------|---------|--------------------------------------------|
| (literal)| 22  | 12  | 52  | ASKIP,BRT          | NEUTRAL | "Type 'S' to View Authorization details from the list" |
| ERRMSG   | 23  | 1   | 78  | ASKIP,BRT,FSET     | RED     | Error/status message area                  |
| (literal)| 24  | 1   | 48  | ASKIP,NORM         | YELLOW  | 'ENTER=Continue  F3=Back  F7=Backward  F8=Forward' |

---

### 5. Navigation (PF Key Assignments)

| Key      | Action                                                                   |
|----------|--------------------------------------------------------------------------|
| ENTER    | Submit account ID search or process selected authorization                |
| PF3      | Return to main menu (XCTL to COMEN01C)                                   |
| PF7      | Scroll backward one page of authorization records                        |
| PF8      | Scroll forward one page of authorization records                         |
| PF1–PF2, PF4–PF6, PF9–PF24 | Invalid key — error message displayed              |

---

### 6. Data Flow

#### 6.1 Input to Program (on RECEIVE)

| Map Field | COBOL Reference      | Description                                            |
|-----------|----------------------|--------------------------------------------------------|
| ACCTIDI   | ACCTIDI OF COPAU0AI  | Account ID entered by operator; validated numeric/11-digit |
| SEL0001I–SEL0005I | SELnnnnI OF COPAU0AI | Selection character for rows 1–5        |

#### 6.2 Output from Program (on SEND)

| Map Field    | Source in COPAUS0C                        | Content                                |
|--------------|-------------------------------------------|----------------------------------------|
| TRNNAMEO     | WS-CICS-TRANID ('CPVS')                  | Transaction name                       |
| TITLE01O     | CCDA-TITLE01 (from COTTL01Y)             | 'AWS Mainframe Cloud Demo'             |
| TITLE02O     | CCDA-TITLE02 (from COTTL01Y)             | 'Credit Card Demo Application'         |
| CURDATEO     | WS-CURDATE-MM-DD-YY                      | Current date MM/DD/YY                  |
| PGMNAMEO     | WS-PGM-AUTH-SMRY ('COPAUS0C')            | Program name                           |
| CURTIMEO     | WS-CURTIME-HH-MM-SS                      | Current time HH:MM:SS                  |
| ACCTIDO      | WS-ACCT-ID / CDEMO-ACCT-ID               | Echoed account ID                      |
| CNAMEO       | Customer name from CVCUS01Y              | Customer full name (25 chars)          |
| CUSTIDO      | CUST-ID from CVCUS01Y                    | Customer ID                            |
| ADDR001O     | Customer address line 1                  | First address line                     |
| ACCSTATO     | Account status from CVACT01Y             | Account status code                    |
| ADDR002O     | Customer address line 2                  | Second address line                    |
| PHONE1O      | Customer phone 1                         | Primary phone number                   |
| APPRCNTO     | WS-DISPLAY-COUNT of PA-APPROVED-AUTH-CNT | Approved count from IMS                |
| DECLCNTO     | WS-DISPLAY-COUNT of PA-DECLINED-AUTH-CNT | Declined count from IMS                |
| CREDLIMO     | PA-CREDIT-LIMIT (formatted)              | Credit limit from IMS summary          |
| CASHLIMO     | PA-CASH-LIMIT (formatted)               | Cash limit from IMS summary            |
| APPRAMTO     | PA-APPROVED-AUTH-AMT (formatted)         | Total approved amount                  |
| CREDBALO     | PA-CREDIT-BALANCE (formatted)            | Credit balance from IMS                |
| CASHBALO     | PA-CASH-BALANCE (formatted)              | Cash balance from IMS                  |
| DECLAMTO     | PA-DECLINED-AUTH-AMT (formatted)         | Total declined amount                  |
| TRNIDnnO     | PA-TRANSACTION-ID                        | Transaction ID for each row            |
| PDATEnnO     | WS-AUTH-DATE (MM/DD/YY)                  | Authorization date                     |
| PTIMEnnO     | WS-AUTH-TIME (HH:MM:SS)                  | Authorization time                     |
| PTYPEnnO     | PA-AUTH-TYPE                             | Authorization type code                |
| PAPRVnnO     | WS-AUTH-APRV-STAT ('A' or 'D')          | Approval indicator                     |
| PSTATnnO     | PA-MATCH-STATUS                          | Match status ('P','D','E','M')         |
| PAMTnnnO     | WS-AUTH-AMT (PIC -zzzzzzz9.99)          | Formatted approved amount              |
| SELnnnnA     | DFHBMUNP / DFHBMPRO                      | Attribute: UNPROTECT if data exists, PROTECT if empty |
| ERRMSGO      | WS-MESSAGE                               | Error or informational message         |

---

### 7. Related Screens

| Screen  | Mapset  | Relationship                                                  |
|---------|---------|---------------------------------------------------------------|
| COPAU01 | COPAU01 | Detail screen — navigated to when 'S' selected and ENTER pressed |
| (menu)  | —       | Main menu — navigated to on PF3; program name COMEN01C        |

---
