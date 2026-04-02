# Technical Specification: COPAUS1C

## Program Name and Purpose

**Program ID:** COPAUS1C  
**Source File:** `/app/app-authorization-ims-db2-mq/cbl/COPAUS1C.cbl`  
**Type:** CICS COBOL IMS BMS Program  
**Application:** CardDemo - Authorization Module  
**Function:** Detail View of a Single Authorization Message

COPAUS1C displays the complete detail of a single pending authorization record selected from the COPAUS0C summary screen. It renders the BMS mapset COPAU01 (map COPAU1A), showing card number, authorization date/time, response code, response reason decoded from a lookup table, authorization code, transaction amount, POS entry mode, message source, MCC code, card expiry, auth type, transaction ID, match status, fraud status, and complete merchant details.

From this screen the operator can:
- Press ENTER to refresh.
- Press PF3 to return to the summary list (COPAUS0C).
- Press PF5 to toggle the fraud flag on the current authorization (CICS LINK to COPAUS2C for DB2 INSERT/UPDATE).
- Press PF8 to advance to the next authorization for the same account.

---

## Artifact Inventory

| Artifact | Type | Role |
|----------|------|------|
| COPAUS1C.cbl | COBOL Source | Main program |
| COPAU01.bms | BMS Source | Screen definition |
| COPAU01.cpy | BMS Copybook | Generated I/O structures for map COPAU1A |
| CIPAUSMY.cpy | Copybook | IMS PAUTSUM0 segment layout |
| CIPAUDTY.cpy | Copybook | IMS PAUTDTL1 segment layout |
| COCOM01Y.cpy | Copybook | Common COMMAREA structure |
| COTTL01Y.cpy | Copybook | Screen title constants |
| CSDAT01Y.cpy | Copybook | Date/time formatting |
| CSMSG01Y.cpy | Copybook | Common message strings |
| CSMSG02Y.cpy | Copybook | Abend variables |
| DFHAID | IBM Copybook | AID key definitions |
| DFHBMSCA | IBM Copybook | BMS attribute byte constants |

---

## IDENTIFICATION DIVISION Metadata

- **PROGRAM-ID:** COPAUS1C  
- **AUTHOR:** AWS  
- Source lines 22–24

---

## DATA DIVISION

### Key Working-Storage Variables (lines 33–54)

| Field | PIC | Value | Purpose |
|-------|-----|-------|---------|
| WS-PGM-AUTH-DTL | X(08) | 'COPAUS1C' | This program's name |
| WS-PGM-AUTH-SMRY | X(08) | 'COPAUS0C' | Summary program (PF3 target) |
| WS-PGM-AUTH-FRAUD | X(08) | 'COPAUS2C' | Fraud handler (CICS LINK target) |
| WS-CICS-TRANID | X(04) | 'CPVD' | This program's CICS transaction ID |
| WS-ERR-FLG | X(01) | 'N' | Error flag |
| WS-AUTHS-EOF | X(01) | 'N' | IMS end-of-children |
| WS-SEND-ERASE-FLG | X(01) | 'Y' | Erase control |
| WS-RESP-CD / WS-REAS-CD | S9(09) COMP | 0 | CICS response codes |
| WS-ACCT-ID | 9(11) | — | Current account ID |
| WS-AUTH-KEY | X(08) | — | Current authorization key (8 bytes = date-9C + time-9C composite) |
| WS-AUTH-AMT | -zzzzzzz9.99 | — | Formatted amount |
| WS-AUTH-DATE | X(08) | '00/00/00' | Formatted date for display |
| WS-AUTH-TIME | X(08) | '00:00:00' | Formatted time for display |

### Decline Reason Lookup Table (lines 56–73)

```
WS-DECLINE-REASON-TABLE contains 10 entries of X(20) each:
  '0000APPROVED'
  '3100INVALID CARD'
  '4100INSUFFICNT FUND'
  '4200CARD NOT ACTIVE'
  '4300ACCOUNT CLOSED'
  '4400EXCED DAILY LMT'
  '5100CARD FRAUD'
  '5200MERCHANT FRAUD'
  '5300LOST CARD'
  '9000UNKNOWN'
```

Redefined as WS-DECLINE-REASON-TAB OCCURS 10 TIMES ASCENDING KEY IS DECL-CODE:
- `DECL-CODE` PIC X(4) — 4-digit reason code
- `DECL-DESC` PIC X(16) — descriptive text

Used with SEARCH ALL (binary search) in POPULATE-AUTH-DETAILS.

### IMS Variables (lines 75–91) — Same structure as COPAUS0C

| Field | Value | Purpose |
|-------|-------|---------|
| PSB-NAME | 'PSBPAUTB' | IMS PSB |
| PAUT-PCB-NUM | +1 | PCB number |

### Fraud Data Working Storage (lines 93–104)

```
01 WS-FRAUD-DATA.
  02 WS-FRD-ACCT-ID          PIC 9(11)
  02 WS-FRD-CUST-ID          PIC 9(9)
  02 WS-FRAUD-AUTH-RECORD    PIC X(200)  -- holds PENDING-AUTH-DETAILS copy
  02 WS-FRAUD-STATUS-RECORD
     05 WS-FRD-ACTION        PIC X(01)   -- F=Report Fraud, R=Remove Fraud
     05 WS-FRD-UPDATE-STATUS PIC X(01)   -- S=Success, F=Failed
     05 WS-FRD-ACT-MSG       PIC X(50)   -- message from COPAUS2C
```

This is the COMMAREA passed to COPAUS2C on CICS LINK.

### COMMAREA Extensions (lines 109–120)

Beyond COCOM01Y, in 05 CDEMO-CPVD-INFO:

| Field | PIC | Purpose |
|-------|-----|---------|
| CDEMO-CPVD-PAU-SEL-FLG | X(01) | Selection flag |
| CDEMO-CPVD-PAU-SELECTED | X(08) | Currently viewed auth key |
| CDEMO-CPVD-PAUKEY-PREV-PG | X(08) OCCURS 20 | Page keys for PF7 navigation |
| CDEMO-CPVD-PAUKEY-LAST | X(08) | Last key on page |
| CDEMO-CPVD-PAGE-NUM | S9(04) COMP | Page number |
| CDEMO-CPVD-NEXT-PAGE-FLG | X(01) | Next page available |
| CDEMO-CPVD-AUTH-KEYS | X(08) OCCURS 5 | Keys on current page |
| CDEMO-CPVD-FRAUD-DATA | X(100) | Fraud data propagation area |

---

## Copybooks Referenced

| Copybook | Line | Purpose |
|----------|------|---------|
| COCOM01Y | 109 | Standard CARDDEMO-COMMAREA |
| COPAU01 | 122 | BMS-generated I/O for map COPAU1A |
| COTTL01Y | 126 | Title constants |
| CSDAT01Y | 129 | Date/time variables |
| CSMSG01Y | 132 | Message strings (CCDA-MSG-INVALID-KEY) |
| CSMSG02Y | 135 | Abend variables |
| CIPAUSMY | 142 | PENDING-AUTH-SUMMARY |
| CIPAUDTY | 146 | PENDING-AUTH-DETAILS |
| DFHAID | 148 | EIBAID constants |
| DFHBMSCA | 149 | Attribute byte constants (DFHGREEN, DFHRED) |

---

## CICS Commands

| Command | Location | Purpose |
|---------|----------|---------|
| EXEC CICS RETURN TRANSID(CPVD) COMMAREA | MAIN-PARA (line 201) | Pseudo-conversational return |
| EXEC CICS XCTL PROGRAM(COPAUS0C) COMMAREA | RETURN-TO-PREV-SCREEN | PF3 back to summary |
| EXEC CICS LINK PROGRAM(COPAUS2C) COMMAREA(WS-FRAUD-DATA) | MARK-AUTH-FRAUD (line 248) | Fraud flag update |
| EXEC CICS SEND MAP(COPAU1A) MAPSET(COPAU01) ERASE CURSOR | SEND-AUTHVIEW-SCREEN | Full send with erase |
| EXEC CICS SEND MAP(COPAU1A) MAPSET(COPAU01) CURSOR | SEND-AUTHVIEW-SCREEN | Overlay send |
| EXEC CICS RECEIVE MAP(COPAU1A) MAPSET(COPAU01) INTO(COPAU1AI) | RECEIVE-AUTHVIEW-SCREEN | Receive map data |
| EXEC CICS SYNCPOINT | PROCESS-ENTER-KEY (line 220) | Commit after IMS reads |
| EXEC CICS ASKTIME / FORMATTIME | POPULATE-HEADER-INFO | Get current date/time |

---

## IMS DL/I Calls

All use EXEC DLI with PCB(1). PSB scheduling handled in SCHEDULE-PSB paragraph (same pattern as other programs — DLI SCHD PSBPAUTB, handle TC).

### READ-AUTH-RECORD (line 431)

**Step 1 — Get summary by account:**
```cobol
EXEC DLI GU USING PCB(PAUT-PCB-NUM)
    SEGMENT (PAUTSUM0)
    INTO (PENDING-AUTH-SUMMARY)
    WHERE (ACCNTID = PA-ACCT-ID)
END-EXEC
```

**Step 2 — Get specific detail by key under that summary:**
```cobol
EXEC DLI GNP USING PCB(PAUT-PCB-NUM)
    SEGMENT (PAUTDTL1)
    INTO (PENDING-AUTH-DETAILS)
    WHERE (PAUT9CTS = PA-AUTHORIZATION-KEY)
END-EXEC
```
- PAUT9CTS is the IMS field name for PA-AUTH-DATE-9C / PA-AUTH-TIME-9C composite key.

### READ-NEXT-AUTH-RECORD (line 493)

```cobol
EXEC DLI GNP USING PCB(PAUT-PCB-NUM)
    SEGMENT (PAUTDTL1)
    INTO (PENDING-AUTH-DETAILS)
END-EXEC
```
- Gets the next sibling detail segment (used for PF8 navigation).

### UPDATE-AUTH-DETAILS (called from MARK-AUTH-FRAUD after fraud toggle)

```cobol
EXEC DLI REPL USING PCB(PAUT-PCB-NUM)
    SEGMENT (PAUTDTL1)
    FROM (PENDING-AUTH-DETAILS)
END-EXEC
```
- Replaces the detail segment after toggling PA-AUTH-FRAUD.

### TAKE-SYNCPOINT

```cobol
EXEC DLI TERM END-EXEC
-- followed by --
EXEC CICS SYNCPOINT END-EXEC
```
- Terminates PSB and commits after IMS reads.

---

## Program Flow

### MAIN-PARA (line 157)

```
SET ERR-FLG-OFF, SEND-ERASE-YES
Clear WS-MESSAGE, ERRMSGO

IF EIBCALEN = 0 (no commarea):
    Initialize CARDDEMO-COMMAREA
    MOVE COPAUS0C to CDEMO-TO-PROGRAM
    PERFORM RETURN-TO-PREV-SCREEN (XCTL back to summary)
ELSE:
    MOVE DFHCOMMAREA to CARDDEMO-COMMAREA
    MOVE SPACES to CDEMO-CPVD-FRAUD-DATA
    IF NOT CDEMO-PGM-REENTER (first display of this auth):
        SET CDEMO-PGM-REENTER
        PERFORM PROCESS-ENTER-KEY
        PERFORM SEND-AUTHVIEW-SCREEN
    ELSE (re-entry):
        PERFORM RECEIVE-AUTHVIEW-SCREEN
        EVALUATE EIBAID
            WHEN DFHENTER: PROCESS-ENTER-KEY + SEND-AUTHVIEW-SCREEN
            WHEN DFHPF3:   MOVE COPAUS0C to CDEMO-TO-PROGRAM; RETURN-TO-PREV-SCREEN
            WHEN DFHPF5:   MARK-AUTH-FRAUD + SEND-AUTHVIEW-SCREEN
            WHEN DFHPF8:   PROCESS-PF8-KEY + SEND-AUTHVIEW-SCREEN
            WHEN OTHER:    PROCESS-ENTER-KEY + set invalid key message + SEND

EXEC CICS RETURN TRANSID(CPVD) COMMAREA
```

### PROCESS-ENTER-KEY (line 208)

```
MOVE LOW-VALUES to COPAU1AO (clear screen output)
IF CDEMO-ACCT-ID is numeric AND CDEMO-CPVD-PAU-SELECTED not spaces:
    MOVE account ID and auth key
    PERFORM READ-AUTH-RECORD
    IF IMS-PSB-SCHD: SET NOT-SCHD; PERFORM TAKE-SYNCPOINT
ELSE:
    SET ERR-FLG-ON
PERFORM POPULATE-AUTH-DETAILS
```

### MARK-AUTH-FRAUD (line 230) — PF5 Fraud Toggle

```
MOVE account/auth key
PERFORM READ-AUTH-RECORD
IF PA-FRAUD-CONFIRMED (already F):
    SET PA-FRAUD-REMOVED (R) and WS-REMOVE-FRAUD
ELSE:
    SET PA-FRAUD-CONFIRMED (F) and WS-REPORT-FRAUD

MOVE PENDING-AUTH-DETAILS to WS-FRAUD-AUTH-RECORD
MOVE CDEMO-ACCT-ID to WS-FRD-ACCT-ID
MOVE CDEMO-CUST-ID to WS-FRD-CUST-ID

EXEC CICS LINK PROGRAM('COPAUS2C')
               COMMAREA(WS-FRAUD-DATA)
               NOHANDLE
END-EXEC

IF EIBRESP = DFHRESP(NORMAL) AND WS-FRD-UPDT-SUCCESS:
    PERFORM UPDATE-AUTH-DETAILS    (IMS REPL of PAUTDTL1)
ELSE:
    PERFORM ROLL-BACK

MOVE PA-AUTHORIZATION-KEY to CDEMO-CPVD-PAU-SELECTED
PERFORM POPULATE-AUTH-DETAILS
```

### PROCESS-PF8-KEY (line 268) — Next Authorization

```
PERFORM READ-AUTH-RECORD       (positions IMS at current auth)
PERFORM READ-NEXT-AUTH-RECORD  (GNP to get next sibling)
IF IMS-PSB-SCHD: TAKE-SYNCPOINT
IF AUTHS-EOF:
    SET SEND-ERASE-NO; message "Already at the last Authorization..."
ELSE:
    MOVE PA-AUTHORIZATION-KEY to CDEMO-CPVD-PAU-SELECTED
    PERFORM POPULATE-AUTH-DETAILS
```

### POPULATE-AUTH-DETAILS (line 291)

Maps PENDING-AUTH-DETAILS fields to COPAU1AO output fields:

| Source Field | Target Map Field | Processing |
|-------------|------------------|------------|
| PA-CARD-NUM | CARDNUMO | Direct move |
| PA-AUTH-ORIG-DATE | AUTHDTO | Reformatted as MM/DD/YY |
| PA-AUTH-ORIG-TIME | AUTHTMO | Formatted as HH:MM:SS |
| PA-APPROVED-AMT | AUTHAMTO | Via WS-AUTH-AMT format |
| PA-AUTH-RESP-CODE | AUTHRSPO | 'A' if '00', 'D' otherwise; color DFHGREEN/'A' or DFHRED/'D' |
| PA-AUTH-RESP-REASON + DECL-DESC | AUTHRSNO | SEARCH ALL lookup: code-dash-description |
| PA-PROCESSING-CODE | AUTHCDO | Direct |
| PA-POS-ENTRY-MODE | POSEMDO | Direct |
| PA-MESSAGE-SOURCE | AUTHSRCO | Direct |
| PA-MERCHANT-CATAGORY-CODE | MCCCDO | Direct |
| PA-CARD-EXPIRY-DATE | CRDEXPO | Formatted as MM/YY |
| PA-AUTH-TYPE | AUTHTYPO | Direct |
| PA-TRANSACTION-ID | TRNIDO | Direct |
| PA-MATCH-STATUS | AUTHMTCO | Direct |
| PA-AUTH-FRAUD / PA-FRAUD-RPT-DATE | AUTHFRDO | "F-mmddyyyy" or "R-mmddyyyy" or "-" |
| PA-MERCHANT-NAME | MERNAMEO | Direct |
| PA-MERCHANT-ID | MERIDO | Direct |
| PA-MERCHANT-CITY | MERCITYO | Direct |
| PA-MERCHANT-STATE | MERSTO | Direct |
| PA-MERCHANT-ZIP | MERZIPO | Direct |

### ROLL-BACK

Issues `EXEC CICS SYNCPOINT ROLLBACK END-EXEC` to undo any IMS changes made before the COPAUS2C LINK failed.

---

## Error Handling

| Condition | Response |
|-----------|----------|
| EIBCALEN = 0 (no commarea) | XCTL back to COPAUS0C |
| CDEMO-ACCT-ID not numeric or auth key not set | SET ERR-FLG-ON (shows empty screen) |
| IMS GU/GNP returns non-spaces/non-GE/non-GB | Format error message with DIBSTAT; call SEND-AUTHVIEW-SCREEN |
| COPAUS2C LINK returns non-normal EIBRESP | ROLL-BACK |
| WS-FRD-UPDT-FAILED after LINK | Display WS-FRD-ACT-MSG; ROLL-BACK |
| AUTHS-EOF on PF8 | Display "Already at the last Authorization..." |
| Invalid AID | PROCESS-ENTER-KEY + display CCDA-MSG-INVALID-KEY |

---

## Transaction Flow Participation

| Element | Value | Role |
|---------|-------|------|
| CICS Transaction | CPVD | This program's transaction |
| Entered from | COPAUS0C via XCTL | With CDEMO-CPVD-PAU-SELECTED set to auth key |
| PF3 exits to | COPAUS0C (CPVS) | Via XCTL |
| PF5 calls | COPAUS2C | Via CICS LINK (fraud toggle) |

Flow:
```
COPAUS0C --[XCTL]--> COPAUS1C (CPVD)
                         |-- PF3 --[XCTL]--> COPAUS0C (CPVS)
                         |-- PF5 --[LINK]--> COPAUS2C (DB2 fraud update)
                         |-- PF8 (next auth, self-return)
                         |-- ENTER (refresh, self-return)
```

---

## Inter-Program Interactions

| Program | Method | Data Passed |
|---------|--------|-------------|
| COPAUS0C | EXEC CICS XCTL | CARDDEMO-COMMAREA (PF3) |
| COPAUS2C | EXEC CICS LINK | WS-FRAUD-DATA (PF5): account ID, customer ID, full auth detail, action flag, status return |
