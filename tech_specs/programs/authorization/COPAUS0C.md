# Technical Specification: COPAUS0C
## Authorization Summary Display Program

---

### 1. Program Overview

| Attribute       | Value                                       |
|-----------------|---------------------------------------------|
| Program Name    | COPAUS0C                                    |
| Source File     | cbl/COPAUS0C.cbl                            |
| Program Type    | CICS COBOL — IMS + BMS                     |
| Function        | Summary View of Authorization Messages      |
| Transaction ID  | CPVS                                        |
| Author          | AWS                                         |
| PSB Used        | PSBPAUTB                                    |
| IMS PCB         | PAUT-PCB-NUM = 1 (DBPAUTP0, PROCOPT=AP)    |
| BMS Mapset      | COPAU00, Map COPAU0A                        |

**Purpose:** COPAUS0C provides the online user interface for viewing pending credit card authorizations. The operator enters an account ID, and the program retrieves account/customer information from VSAM files and IMS authorization records. Up to five authorization records are displayed per page, with PF7/PF8 for backward/forward paging. Selecting an authorization with 'S' transfers to COPAUS1C for detail viewing.

---

### 2. Program Flow

```
MAIN-PARA
  |
  +-- Initialize flags (ERR-FLG-OFF, AUTHS-NOT-EOF, NEXT-PAGE-NO, SEND-ERASE-YES)
  |
  +-- [EIBCALEN = 0 -- First entry]
  |     Initialize CARDDEMO-COMMAREA
  |     Set CDEMO-PGM-REENTER to TRUE
  |     Clear COPAU0AO map
  |     SEND-PAULST-SCREEN (initial blank screen)
  |
  +-- [EIBCALEN > 0 -- Re-entry]
  |     Move DFHCOMMAREA to CARDDEMO-COMMAREA
  |     [NOT CDEMO-PGM-REENTER -- First display after navigation here]
  |     |   Set CDEMO-PGM-REENTER
  |     |   Populate account ID if CDEMO-ACCT-ID is numeric
  |     |   GATHER-DETAILS
  |     |   SEND-PAULST-SCREEN (ERASE)
  |     |
  |     [CDEMO-PGM-REENTER -- Subsequent interaction]
  |         RECEIVE-PAULST-SCREEN
  |         EVALUATE EIBAID:
  |           DFHENTER  -> PROCESS-ENTER-KEY -> SEND-PAULST-SCREEN
  |           DFHPF3    -> RETURN-TO-PREV-SCREEN (XCTL to COMEN01C)
  |           DFHPF7    -> PROCESS-PF7-KEY -> SEND-PAULST-SCREEN
  |           DFHPF8    -> PROCESS-PF8-KEY -> SEND-PAULST-SCREEN
  |           OTHER     -> error message -> SEND-PAULST-SCREEN
  |
  +-- EXEC CICS RETURN TRANSID(CPVS) COMMAREA(CARDDEMO-COMMAREA)
```

#### GATHER-DETAILS (when account ID is entered)
```
GATHER-DETAILS
  +-- Reset page number to 0
  +-- [if WS-ACCT-ID not LOW-VALUES]
        GATHER-ACCOUNT-DETAILS
          +-- Read CCXREF by card number (GET by acct path)
          +-- Read ACCTDAT by account ID
          +-- Read CUSTDAT by customer ID
        INITIALIZE-AUTH-DATA (clear 5 screen rows)
        [if FOUND-PAUT-SMRY-SEG]
          PROCESS-PAGE-FORWARD
```

#### PROCESS-PAGE-FORWARD (read and display up to 5 detail records)
```
PROCESS-PAGE-FORWARD
  WS-IDX = 1 to 5 (or until AUTHS-EOF):
    [if PF7 and first record] REPOSITION-AUTHORIZATIONS (GNP with SSA)
    [else]                    GET-AUTHORIZATIONS (GNP unqualified)
    if AUTHS-NOT-EOF: POPULATE-AUTH-LIST (fill screen row WS-IDX)
      - Save PA-AUTHORIZATION-KEY to CDEMO-CPVS-AUTH-KEYS(WS-IDX)
      - Set CDEMO-CPVS-PAUKEY-LAST to last key displayed
      - On row 2: increment page number, save first key of page
  Peek at one more record to determine if NEXT-PAGE-YES
```

---

### 3. Data Structures

#### 3.1 Working Storage Key Fields (cbl/COPAUS0C.cbl, lines 32–115)

| Field                       | Picture            | Description                                       |
|-----------------------------|--------------------|---------------------------------------------------|
| WS-PGM-AUTH-SMRY            | PIC X(08)          | 'COPAUS0C' — this program                         |
| WS-PGM-AUTH-DTL             | PIC X(08)          | 'COPAUS1C' — detail program target                |
| WS-PGM-MENU                 | PIC X(08)          | 'COMEN01C' — main menu (PF3 target)               |
| WS-CICS-TRANID              | PIC X(04)          | 'CPVS'                                            |
| WS-ACCTFILENAME             | PIC X(8)           | 'ACCTDAT '                                        |
| WS-CUSTFILENAME             | PIC X(8)           | 'CUSTDAT '                                        |
| WS-CARDFILENAME             | PIC X(8)           | 'CARDDAT '                                        |
| WS-CARDXREFNAME-ACCT-PATH   | PIC X(8)           | 'CXACAIX '                                        |
| WS-CCXREF-FILE              | PIC X(08)          | 'CCXREF  '                                        |
| WS-ACCT-ID                  | PIC X(11)          | Account ID from screen input                      |
| WS-AUTH-KEY-SAVE            | PIC X(08)          | Saved authorization key for paging                |
| WS-REC-COUNT                | PIC S9(04) COMP    | Record counter                                    |
| WS-IDX                      | PIC S9(04) COMP    | Screen row index (1–5)                            |
| WS-PAGE-NUM                 | PIC S9(04) COMP    | Current page number                               |
| WS-AUTH-AMT                 | PIC -zzzzzzz9.99   | Formatted authorization amount                    |
| WS-AUTH-DATE                | PIC X(08)          | Formatted date MM/DD/YY                           |
| WS-AUTH-TIME                | PIC X(08)          | Formatted time HH:MM:SS                           |

#### 3.2 COMMAREA Extension (lines 116–127, after COPY COCOM01Y)

The CDEMO-CPVS-INFO area is appended after the CARDDEMO-COMMAREA standard fields:

| Field                      | Picture             | Description                                    |
|----------------------------|---------------------|------------------------------------------------|
| CDEMO-CPVS-PAU-SEL-FLG     | PIC X(01)           | Selection character entered by user            |
| CDEMO-CPVS-PAU-SELECTED    | PIC X(08)           | Key of selected authorization                  |
| CDEMO-CPVS-PAUKEY-PREV-PG  | PIC X(08) OCCURS 20 | First key of each previous page (PF7 backtrack)|
| CDEMO-CPVS-PAUKEY-LAST     | PIC X(08)           | Last key displayed on current page             |
| CDEMO-CPVS-PAGE-NUM        | PIC S9(04) COMP     | Current page number                            |
| CDEMO-CPVS-NEXT-PAGE-FLG   | PIC X(01)           | 'Y'=more pages exist, 'N'=at last page        |
| CDEMO-CPVS-AUTH-KEYS       | PIC X(08) OCCURS 5  | Keys of the 5 currently displayed records      |

#### 3.3 IMS Variables (lines 74–91)

PSB-NAME = 'PSBPAUTB', PAUT-PCB-NUM = +1. Status code 88-levels identical to COPAUA0C.

---

### 4. CICS, IMS, and MQ Commands

#### 4.1 CICS Commands

| Command                  | Location                    | Parameters / Notes                                        |
|--------------------------|-----------------------------|-----------------------------------------------------------|
| EXEC CICS SEND MAP       | SEND-PAULST-SCREEN          | MAP('COPAU0A') MAPSET('COPAU00') FROM(COPAU0AO) ERASE (or no ERASE if SEND-ERASE-NO) CURSOR |
| EXEC CICS RECEIVE MAP    | RECEIVE-PAULST-SCREEN       | MAP('COPAU0A') MAPSET('COPAU00') INTO(COPAU0AI) NOHANDLE  |
| EXEC CICS XCTL           | RETURN-TO-PREV-SCREEN       | PROGRAM(CDEMO-TO-PROGRAM) COMMAREA(CARDDEMO-COMMAREA)    |
| EXEC CICS XCTL           | PROCESS-ENTER-KEY           | PROGRAM(CDEMO-TO-PROGRAM='COPAUS1C') when 'S' selected   |
| EXEC CICS SYNCPOINT      | SEND-PAULST-SCREEN          | Issued before each screen send if IMS-PSB-SCHD (line 685)|
| EXEC CICS RETURN         | MAIN-PARA                   | TRANSID(CPVS) COMMAREA(CARDDEMO-COMMAREA)                |

**IMS PSB termination before screen send:** The IMS PSB is implicitly terminated via EXEC CICS SYNCPOINT in SEND-PAULST-SCREEN (lines 684–688) if the PSB is currently scheduled. The flag is then reset to IMS-PSB-NOT-SCHD. This ensures IMS resources are released before the task pseudo-returns.

#### 4.2 IMS DLI Commands

| Command       | Paragraph                  | Segment    | Qualifier                             | Purpose                                              |
|---------------|----------------------------|------------|---------------------------------------|------------------------------------------------------|
| EXEC DLI SCHD | GET-AUTH-SUMMARY (implied) | —          | PSB((PSB-NAME)) NODHABEND             | Schedule PSB; TC status causes TERM + re-SCHD        |
| EXEC DLI GU   | GET-AUTH-SUMMARY           | PAUTSUM0   | WHERE(ACCNTID = WS-CARD-RID-ACCT-ID) | Retrieve summary for account                        |
| EXEC DLI GNP  | GET-AUTHORIZATIONS         | PAUTDTL1   | Unqualified                           | Get next detail record under current summary         |
| EXEC DLI GNP  | REPOSITION-AUTHORIZATIONS  | PAUTDTL1   | WHERE(PAUT9CTS = PA-AUTHORIZATION-KEY)| Position to specific detail key for page navigation |

**Note:** The GET-AUTH-SUMMARY paragraph is inferred from the GATHER-DETAILS and paging logic. COPAUS0C.cbl references paragraphs GATHER-ACCOUNT-DETAILS and GET-AUTH-SUMMARY which are used in the GATHER-DETAILS and PF7/PF8 key handlers (lines 349–412). These paragraphs call IMS GU with a WHERE clause on ACCNTID.

#### 4.3 VSAM File Access

| File     | Key                              | Structure     | Purpose                     |
|----------|----------------------------------|---------------|-----------------------------|
| CCXREF   | XREF-CARD-NUM (16 bytes)         | CVACT03Y      | Resolve card→account→customer |
| ACCTDAT  | WS-CARD-RID-ACCT-ID-X (11 bytes) | CVACT01Y      | Read account master record   |
| CUSTDAT  | WS-CARD-RID-CUST-ID-X (9 bytes)  | CVCUS01Y      | Read customer master record  |

---

### 5. Screen Interaction

Screen is COPAU0A within mapset COPAU00.

#### 5.1 Key Actions

| EIBAID   | Action                                                                            |
|----------|-----------------------------------------------------------------------------------|
| DFHENTER | Validate account ID; handle row selection; call GATHER-DETAILS; display screen   |
| DFHPF3   | XCTL back to COMEN01C (main menu)                                                 |
| DFHPF7   | Scroll backward one page (decrement page number, reposition IMS)                  |
| DFHPF8   | Scroll forward one page (use PAUKEY-LAST to position, then read 5 more)           |
| OTHER    | Display 'Invalid key' message, redisplay screen                                   |

#### 5.2 Row Selection Logic (PROCESS-ENTER-KEY, lines 285–332)

When ENTER is pressed, the program checks SEL0001I through SEL0005I for non-spaces/low-values. The first non-blank selection field maps to CDEMO-CPVS-AUTH-KEYS(n). If the value is 'S' or 's':
- Set CDEMO-TO-PROGRAM = 'COPAUS1C'
- Set CDEMO-FROM-TRANID = 'CPVS', CDEMO-FROM-PROGRAM = 'COPAUS0C'
- EXEC CICS XCTL to COPAUS1C with COMMAREA

Invalid selection values produce error message: 'Invalid selection. Valid value is S'.

#### 5.3 Paging Logic

**Forward (PF8):**
1. Save CDEMO-CPVS-PAUKEY-LAST to WS-AUTH-KEY-SAVE
2. Call GET-AUTH-SUMMARY to re-establish IMS position at the summary segment
3. Call REPOSITION-AUTHORIZATIONS to GNP with WHERE on the saved last key
4. Call PROCESS-PAGE-FORWARD to read the next 5 records

**Backward (PF7):**
1. Decrement CDEMO-CPVS-PAGE-NUM
2. Load CDEMO-CPVS-PAUKEY-PREV-PG(new page num) into WS-AUTH-KEY-SAVE
3. Call GET-AUTH-SUMMARY to re-establish IMS position
4. PROCESS-PAGE-FORWARD reads 5 records starting at first record of that page (REPOSITION-AUTHORIZATIONS is called from within PROCESS-PAGE-FORWARD when EIBAID = DFHPF7 and WS-IDX = 1)

**Maximum pages tracked:** 20 (CDEMO-CPVS-PAUKEY-PREV-PG OCCURS 20 TIMES).

---

### 6. Screen Populate — POPULATE-AUTH-LIST (lines 525–605)

For each of 5 rows (WS-IDX 1–5), the following fields are populated in COPAU0AI:

| Screen Field (Xn suffix) | Source Field             | Description               |
|--------------------------|--------------------------|---------------------------|
| TRNIDnnI                 | PA-TRANSACTION-ID        | Transaction identifier    |
| PDATEnnI                 | WS-AUTH-DATE (MM/DD/YY)  | Authorization date        |
| PTIMEnnI                 | WS-AUTH-TIME (HH:MM:SS)  | Authorization time        |
| PTYPEnnI                 | PA-AUTH-TYPE             | Authorization type code   |
| PAPRVnnI                 | WS-AUTH-APRV-STAT        | 'A'=Approved / 'D'=Declined |
| PSTATnnI                 | PA-MATCH-STATUS          | Match status code         |
| PAMTnnnI                 | WS-AUTH-AMT              | Approved amount formatted |
| SELnnnnA                 | DFHBMUNP                 | Attribute set to unprotected (enable input) |

After INITIALIZE-AUTH-DATA, attribute bytes for all 5 rows are set to DFHBMPRO (protected). After POPULATE-AUTH-LIST for each row, the attribute for that row's selection field is set back to DFHBMUNP.

---

### 7. Called Programs (via XCTL only)

| Program  | When Called                            | Direction     |
|----------|----------------------------------------|---------------|
| COPAUS1C | 'S' selection on authorization row     | XCTL forward  |
| COMEN01C | PF3 pressed                            | XCTL back     |

---

### 8. Error Handling

| Condition                              | Response                                              |
|----------------------------------------|-------------------------------------------------------|
| Account ID blank on ENTER              | WS-MESSAGE = 'Please enter Acct Id...'               |
| Account ID not numeric                 | WS-MESSAGE = 'Acct Id must be Numeric ...'           |
| Invalid selection character            | WS-MESSAGE = 'Invalid selection. Valid value is S'   |
| Invalid PF key                         | WS-MESSAGE = CCDA-MSG-INVALID-KEY                    |
| Already at top of page (PF7)           | WS-MESSAGE = 'You are already at the top of the page...' |
| Already at bottom of page (PF8)        | WS-MESSAGE = 'You are already at the bottom of the page...' |
| IMS GNP / GU error                     | WS-MESSAGE set with IMS status code; ERR-FLG-ON set  |
| CICS file read errors (XREF, ACCT, CUST)| WS-MESSAGE set; ERR-FLG-ON set; screen re-sent     |

All error messages are displayed in the ERRMSG field (row 23) of the COPAU0A map.

---

### 9. Business Rules

1. Account ID must be present and numeric.
2. Selection character must be 'S' or 's'; any other value is rejected.
3. Up to 20 pages of backward navigation are supported (PAUKEY-PREV-PG array).
4. The header area (rows 6–12) is populated from IMS PAUTSUM0 and VSAM account/customer data.
5. Only PAUTDTL1 child segments under the matched PAUTSUM0 are displayed (GNP within parent).

---

### 10. I/O Specification

| Direction | Resource     | Operation | Data Displayed / Entered                              |
|-----------|--------------|-----------|-------------------------------------------------------|
| Input     | Map COPAU0A  | RECEIVE   | Account ID (ACCTIDI), Selection fields (SEL0001I–SEL0005I) |
| Output    | Map COPAU0A  | SEND      | Header (name, customer ID, address, phone, account stats, amounts); 5 auth rows |
| Input     | CCXREF VSAM  | READ      | Card cross-reference by card number                   |
| Input     | ACCTDAT VSAM | READ      | Account master by account ID                          |
| Input     | CUSTDAT VSAM | READ      | Customer master by customer ID                        |
| Input     | IMS PAUTSUM0 | GU        | Authorization summary segment by account ID           |
| Input     | IMS PAUTDTL1 | GNP       | Authorization detail records (up to 5 per page)       |

---
