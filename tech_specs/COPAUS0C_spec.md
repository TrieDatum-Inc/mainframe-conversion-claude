# Technical Specification: COPAUS0C

## Program Name and Purpose

**Program ID:** COPAUS0C  
**Source File:** `/app/app-authorization-ims-db2-mq/cbl/COPAUS0C.cbl`  
**Type:** CICS COBOL IMS BMS Program  
**Application:** CardDemo - Authorization Module  
**Function:** Authorization Summary View — displays paginated list of pending authorization detail records for a given account

COPAUS0C is the CICS online inquiry program that presents the authorization summary screen (BMS mapset COPAU00, map COPAU0A). The operator enters an account ID and the program displays:
- Account holder demographics (name, address, phone)
- Account financial summary (credit limit, balances, approval/decline counts and amounts)
- A list of up to 5 authorization transactions per page (transaction ID, date, time, type, approve/decline indicator, match status, amount)

The operator can page forward (PF8) and backward (PF7), and select an individual authorization (typing 'S' in a selection field) to navigate to the detail view program COPAUS1C.

---

## Artifact Inventory

| Artifact | Type | Role |
|----------|------|------|
| COPAUS0C.cbl | COBOL Source | Main program |
| COPAU00.bms | BMS Source | Screen definition |
| COPAU00.cpy | BMS Copybook | Generated I/O structures for map COPAU0A |
| CIPAUSMY.cpy | Copybook | IMS PAUTSUM0 segment layout |
| CIPAUDTY.cpy | Copybook | IMS PAUTDTL1 segment layout |
| COCOM01Y.cpy | Copybook | Common COMMAREA structure |
| COTTL01Y.cpy | Copybook | Screen title constants |
| CSDAT01Y.cpy | Copybook | Current date formatting variables |
| CSMSG01Y.cpy | Copybook | Common message strings |
| CSMSG02Y.cpy | Copybook | Abend/diagnostic variables |
| CVACT01Y.cpy | Copybook | Account master record layout |
| CVACT02Y.cpy | Copybook | [ARTIFACT NOT AVAILABLE FOR INSPECTION] |
| CVACT03Y.cpy | Copybook | Card XREF record layout |
| CVCUS01Y.cpy | Copybook | Customer master record layout |
| DFHAID | IBM Copybook | AID key definitions |
| DFHBMSCA | IBM Copybook | BMS attribute byte constants |

---

## IDENTIFICATION DIVISION Metadata

- **PROGRAM-ID:** COPAUS0C  
- **AUTHOR:** AWS  
- Source lines 22–24

---

## ENVIRONMENT DIVISION

No FILE-CONTROL entries (line 27–28). All data access is via CICS commands.

---

## DATA DIVISION

### Key Working-Storage Variables (lines 32–60)

| Field | PIC | Value | Purpose |
|-------|-----|-------|---------|
| WS-PGM-AUTH-SMRY | X(08) | 'COPAUS0C' | This program's name |
| WS-PGM-AUTH-DTL | X(08) | 'COPAUS1C' | Detail view program (XCTL target) |
| WS-PGM-MENU | X(08) | 'COMEN01C' | Menu program (PF3 target) |
| WS-CICS-TRANID | X(04) | 'CPVS' | This program's CICS transaction ID |
| WS-ACCTFILENAME | X(8) | 'ACCTDAT ' | Account master CICS dataset |
| WS-CUSTFILENAME | X(8) | 'CUSTDAT ' | Customer master CICS dataset |
| WS-CARDFILENAME | X(8) | 'CARDDAT ' | Card master CICS dataset |
| WS-CARDXREFNAME-ACCT-PATH | X(8) | 'CXACAIX ' | Card XREF alternate index by account |
| WS-CCXREF-FILE | X(08) | 'CCXREF  ' | Card XREF by card number |
| WS-ACCT-ID | X(11) | — | Account ID entered on screen |
| WS-AUTH-KEY-SAVE | X(08) | — | Saved authorization key for paging |
| WS-PAGE-NUM | S9(04) COMP | 0 | Current page number |

### Switch Variables (lines 93–114)

| Switch | 88-levels | Purpose |
|--------|-----------|---------|
| WS-XREF-READ-FLG | Y=ACCT-FOUND-XREF, N=ACCT-NFOUND-XREF | XREF lookup result |
| WS-ACCT-MASTER-READ-FLG | Y=FOUND-ACCT-IN-MSTR, N=NFOUND-ACCT-IN-MSTR | Account lookup result |
| WS-CUST-MASTER-READ-FLG | Y=FOUND-CUST-IN-MSTR, N=NFOUND-CUST-IN-MSTR | Customer lookup result |
| WS-PAUT-SMRY-SEG-FLG | Y=FOUND-PAUT-SMRY-SEG, N=NFOUND-PAUT-SMRY-SEG | IMS summary existence |
| WS-ERR-FLG | Y=ERR-FLG-ON, N=ERR-FLG-OFF | Error condition |
| WS-AUTHS-EOF | Y=AUTHS-EOF, N=AUTHS-NOT-EOF | IMS end of children |
| WS-SEND-ERASE-FLG | Y=SEND-ERASE-YES, N=SEND-ERASE-NO | Controls ERASE vs overlay send |

### COMMAREA Extensions (lines 116–127)

Beyond COCOM01Y (standard CardDemo commarea), the following fields are appended in 05 CDEMO-CPVS-INFO:

| Field | PIC | Purpose |
|-------|-----|---------|
| CDEMO-CPVS-PAU-SEL-FLG | X(01) | Selection flag from screen ('S' or 's') |
| CDEMO-CPVS-PAU-SELECTED | X(08) | Auth key of selected record |
| CDEMO-CPVS-PAUKEY-PREV-PG | X(08) OCCURS 20 | Auth keys for backward paging (one per page) |
| CDEMO-CPVS-PAUKEY-LAST | X(08) | Auth key of last record on current page |
| CDEMO-CPVS-PAGE-NUM | S9(04) COMP | Current page number |
| CDEMO-CPVS-NEXT-PAGE-FLG | X(01) | Y=more pages available |
| CDEMO-CPVS-AUTH-KEYS | X(08) OCCURS 5 | Keys of 5 displayed authorizations |

### IMS Variables (lines 74–90)

| Field | Value | Purpose |
|-------|-------|---------|
| PSB-NAME | 'PSBPAUTB' | IMS PSB |
| PAUT-PCB-NUM | +1 | PCB number |
| IMS-RETURN-CODE | — | DIBSTAT |

---

## Copybooks Referenced

| Copybook | Line | Purpose |
|----------|------|---------|
| COCOM01Y | 116 | Common COMMAREA; CARDDEMO-COMMAREA, CDEMO-ACCT-ID, CDEMO-CUST-ID, etc. |
| COPAU00 | 129 | BMS-generated I/O for COPAU0A map (COPAU0AI input, COPAU0AO output) |
| COTTL01Y | 132 | CCDA-TITLE01, CCDA-TITLE02 screen title literals |
| CSDAT01Y | 135 | WS-CURDATE-DATA, WS-CURDATE-MM, WS-CURDATE-DD, WS-CURDATE-YY, WS-CURDATE-MM-DD-YY, WS-CURTIME-* |
| CSMSG01Y | 138 | CCDA-MSG-INVALID-KEY and other standard messages |
| CSMSG02Y | 141 | Abend diagnostic variables |
| CVACT01Y | 144 | ACCOUNT-RECORD: ACCT-CREDIT-LIMIT, ACCT-CASH-CREDIT-LIMIT, ACCT-CURR-BAL |
| CVACT02Y | 147 | [ARTIFACT NOT AVAILABLE FOR INSPECTION] |
| CVACT03Y | 150 | CARD-XREF-RECORD: XREF-CARD-NUM, XREF-ACCT-ID, XREF-CUST-ID |
| CVCUS01Y | 153 | CUSTOMER-RECORD: CUST-ID, CUST-FIRST-NAME, CUST-MIDDLE-NAME, CUST-LAST-NAME, CUST-ADDR-LINE-1 through -3, CUST-ADDR-STATE-CD, CUST-ADDR-ZIP, CUST-PHONE-NUM-1 |
| CIPAUSMY | 161 | PENDING-AUTH-SUMMARY (see CBPAUP0C spec for field list) |
| CIPAUDTY | 165 | PENDING-AUTH-DETAILS (see CBPAUP0C spec for field list) |
| DFHAID | 168 | EIBAID constants: DFHENTER, DFHPF3, DFHPF7, DFHPF8 |
| DFHBMSCA | 169 | DFHBMPRO, DFHBMUNP, DFHGREEN, DFHRED, etc. |

---

## CICS Commands

| Command | Location | Purpose |
|---------|----------|---------|
| EXEC CICS RETURN TRANSID(CPVS) COMMAREA | MAIN-PARA (line 254) | Pseudo-conversational return |
| EXEC CICS SEND MAP(COPAU0A) MAPSET(COPAU00) FROM(COPAU0AO) ERASE CURSOR | SEND-PAULST-SCREEN | Full screen send with erase |
| EXEC CICS SEND MAP(COPAU0A) MAPSET(COPAU00) FROM(COPAU0AO) CURSOR | SEND-PAULST-SCREEN | Overlay send without erase |
| EXEC CICS RECEIVE MAP(COPAU0A) MAPSET(COPAU00) INTO(COPAU0AI) | RECEIVE-PAULST-SCREEN | Receive map data |
| EXEC CICS XCTL PROGRAM(CDEMO-TO-PROGRAM) COMMAREA | RETURN-TO-PREV-SCREEN, PROCESS-ENTER-KEY | Transfer control for PF3 or selection |
| EXEC CICS SYNCPOINT | SEND-PAULST-SCREEN (line 686) | Commit IMS changes before screen send |
| EXEC CICS READ DATASET | GATHER-ACCOUNT-DETAILS (implied) | Reads ACCTDAT, CUSTDAT, CCXREF |

---

## IMS DL/I Calls

All calls use EXEC DLI syntax with PCB(1).

### GET-AUTH-SUMMARY — GU call

```cobol
EXEC DLI GU USING PCB(PAUT-PCB-NUM)
    SEGMENT (PAUTSUM0)
    INTO (PENDING-AUTH-SUMMARY)
    WHERE (ACCNTID = PA-ACCT-ID)
END-EXEC
```
- Retrieves summary segment by account ID.
- Sets FOUND-PAUT-SMRY-SEG or NFOUND-PAUT-SMRY-SEG.

### GET-AUTHORIZATIONS — GNP call (line 461)

```cobol
EXEC DLI GNP USING PCB(PAUT-PCB-NUM)
    SEGMENT (PAUTDTL1)
    INTO (PENDING-AUTH-DETAILS)
END-EXEC
```
- Gets next child detail segment under current position.
- Used in page-forward loop (PROCESS-PAGE-FORWARD).

### REPOSITION-AUTHORIZATIONS — GNP with WHERE (line 493)

```cobol
EXEC DLI GNP USING PCB(PAUT-PCB-NUM)
    SEGMENT (PAUTDTL1)
    INTO (PENDING-AUTH-DETAILS)
    WHERE (PAUT9CTS = PA-AUTHORIZATION-KEY)
END-EXEC
```
- Repositions IMS cursor to a specific authorization key.
- Used for PF7 (backward paging) to reposition to saved key.

### SCHEDULE-PSB (referenced within COPAUS0C)

```cobol
EXEC DLI SCHD PSB((PSB-NAME)) NODHABEND END-EXEC
```
- Called before IMS reads. Uses DLI SCHD in CICS environment.

---

## Program Flow

### MAIN-PARA (line 177)

```
SET flags to initial values (ERR-FLG-OFF, AUTHS-NOT-EOF, NEXT-PAGE-NO, SEND-ERASE-YES)
Clear ERRMSGO, set ACCTIDL = -1

IF EIBCALEN = 0 (first entry)
    INITIALIZE CARDDEMO-COMMAREA
    MOVE self to CDEMO-TO-PROGRAM
    SET CDEMO-PGM-REENTER
    SEND COPAU0A screen (erase)
ELSE
    MOVE DFHCOMMAREA to CARDDEMO-COMMAREA
    IF NOT CDEMO-PGM-REENTER (second entry from XCTL)
        SET CDEMO-PGM-REENTER
        Move CDEMO-ACCT-ID to WS-ACCT-ID and ACCTIDO
        PERFORM GATHER-DETAILS
        PERFORM SEND-PAULST-SCREEN
    ELSE (re-entry from self)
        PERFORM RECEIVE-PAULST-SCREEN
        EVALUATE EIBAID
            WHEN DFHENTER: PROCESS-ENTER-KEY + SEND-PAULST-SCREEN
            WHEN DFHPF3:   XCTL to COMEN01C (menu)
            WHEN DFHPF7:   PROCESS-PF7-KEY + SEND-PAULST-SCREEN
            WHEN DFHPF8:   PROCESS-PF8-KEY + SEND-PAULST-SCREEN
            WHEN OTHER:    Set error + SEND-PAULST-SCREEN

EXEC CICS RETURN TRANSID(CPVS) COMMAREA(CARDDEMO-COMMAREA)
```

### PROCESS-ENTER-KEY (line 261)

1. Validates ACCTIDI: must not be spaces/low-values and must be numeric.
2. Checks all 5 selection fields (SEL0001I through SEL0005I) for non-space/non-low-value.
3. If a selection is made and value is 'S'/'s': XCTLs to COPAUS1C with the selected auth key in CDEMO-CPVS-PAU-SELECTED.
4. If no selection, performs GATHER-DETAILS to refresh account and authorization data.

### GATHER-DETAILS (line 342)

```
MOVE 0 to CDEMO-CPVS-PAGE-NUM
IF WS-ACCT-ID not low-values:
    PERFORM GATHER-ACCOUNT-DETAILS
    PERFORM INITIALIZE-AUTH-DATA        (blank the 5 list rows)
    IF FOUND-PAUT-SMRY-SEG:
        PERFORM PROCESS-PAGE-FORWARD
```

### GATHER-ACCOUNT-DETAILS (line 750)

```
PERFORM GETCARDXREF-BYACCT
PERFORM GETACCTDATA-BYACCT
PERFORM GETCUSTDATA-BYCUST
Populate screen fields: CUSTIDO, CNAMEO, ADDR001O, ADDR002O, PHONE1O, CREDLIMO, CASHLIMO
PERFORM GET-AUTH-SUMMARY
IF FOUND-PAUT-SMRY-SEG:
    Populate: APPRCNTO, DECLCNTO, CREDBALO, CASHBALO, APPRAMTO, DECLAMTO
```

### PROCESS-PAGE-FORWARD (line 415)

```
PERFORM UNTIL WS-IDX > 5 OR AUTHS-EOF OR ERR-FLG-ON
    IF EIBAID = DFHPF7 AND WS-IDX = 1: REPOSITION-AUTHORIZATIONS
    ELSE: GET-AUTHORIZATIONS
    IF AUTHS-NOT-EOF:
        PERFORM POPULATE-AUTH-LIST
        Increment WS-IDX
        Save key to CDEMO-CPVS-PAUKEY-LAST
        If WS-IDX = 2: increment page num, save key to PAUKEY-PREV-PG(page)
END-PERFORM
Peek-ahead: GET-AUTHORIZATIONS; if found set NEXT-PAGE-YES, else NEXT-PAGE-NO
```

### POPULATE-AUTH-LIST (line 522)

Maps PENDING-AUTH-DETAILS fields to map row slots 1–5:
- Formats PA-AUTH-ORIG-DATE as MM/DD/YY.
- Formats PA-AUTH-ORIG-TIME as HH:MM:SS.
- Sets WS-AUTH-APRV-STAT = 'A' if resp code '00', else 'D'.
- Moves PA-TRANSACTION-ID, date, time, PA-AUTH-TYPE, approve/decline, PA-MATCH-STATUS, PA-APPROVED-AMT to appropriate TRNIDnn, PDATEnn, PTIMEnn, PTYPEnn, PAPRVnn, PSTATnn, PAMTnnn fields.
- Saves PA-AUTHORIZATION-KEY to CDEMO-CPVS-AUTH-KEYS(n).
- Sets selection field attribute to DFHBMUNP (unprotected) to enable input.

### PROCESS-PF7-KEY (line 362) — Backward Paging

```
IF CDEMO-CPVS-PAGE-NUM > 1:
    Decrement page number
    Restore key from CDEMO-CPVS-PAUKEY-PREV-PG(page)
    GET-AUTH-SUMMARY (re-establish IMS position)
    SET SEND-ERASE-NO, NEXT-PAGE-YES
    PERFORM INITIALIZE-AUTH-DATA
    PERFORM PROCESS-PAGE-FORWARD
ELSE: display "top of page" message
```

### PROCESS-PF8-KEY (line 388) — Forward Paging

```
IF CDEMO-CPVS-PAUKEY-LAST not spaces:
    Move PAUKEY-LAST to WS-AUTH-KEY-SAVE
    PERFORM GET-AUTH-SUMMARY
    PERFORM REPOSITION-AUTHORIZATIONS
SET SEND-ERASE-NO
IF NEXT-PAGE-YES:
    PERFORM INITIALIZE-AUTH-DATA
    PERFORM PROCESS-PAGE-FORWARD
ELSE: display "bottom of page" message
```

### SEND-PAULST-SCREEN (line 681)

```
IF IMS-PSB-SCHD: SET NOT-SCHD; EXEC CICS SYNCPOINT
PERFORM POPULATE-HEADER-INFO
Move WS-MESSAGE to ERRMSGO
IF SEND-ERASE-YES: EXEC CICS SEND MAP ERASE CURSOR
ELSE:              EXEC CICS SEND MAP CURSOR
```

---

## Error Handling

| Condition | Response |
|-----------|----------|
| Account ID blank or non-numeric | Set ERR-FLG-ON, display message "Please enter Acct Id..." or "Acct Id must be Numeric..." |
| Invalid selection character | Display "Invalid selection. Valid value is S" |
| Invalid AID key | Display CCDA-MSG-INVALID-KEY |
| IMS GNP status other than spaces/GE/GB | Set ERR-FLG-ON, format message with DIBSTAT, call SEND-PAULST-SCREEN |
| Top of page reached on PF7 | Display "You are already at the top of the page..." |
| Bottom of page reached on PF8 | Display "You are already at the bottom of the page..." |

---

## Transaction Flow Participation

| Element | Value | Role |
|---------|-------|------|
| CICS Transaction | CPVS | This program's pseudo-conversational transaction |
| Entered from | COPAUA0C (menu) or any program that XCTLs with CDEMO-ACCT-ID set | Entry context |
| Exits to (PF3) | COMEN01C | Back to menu |
| Exits to (Select) | COPAUS1C (CPVD) | Auth detail view |

Flow:
```
COMEN01C --[XCTL]--> COPAUS0C (CPVS)
                         |-- PF8/PF7 (paging, self-return)
                         |-- Enter + 'S' selection --[XCTL]--> COPAUS1C (CPVD)
                         |-- PF3 --[XCTL]--> COMEN01C
```

---

## Inter-Program Interactions

| Program | Method | Data Passed |
|---------|--------|-------------|
| COPAUS1C | EXEC CICS XCTL | CARDDEMO-COMMAREA with CDEMO-CPVS-PAU-SELECTED (auth key), CDEMO-ACCT-ID |
| COMEN01C | EXEC CICS XCTL | CARDDEMO-COMMAREA |
