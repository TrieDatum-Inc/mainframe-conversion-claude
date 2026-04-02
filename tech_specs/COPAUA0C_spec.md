# Technical Specification: COPAUA0C

## Program Name and Purpose

**Program ID:** COPAUA0C  
**Source File:** `/app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl`  
**Type:** CICS COBOL IMS MQ Program  
**Application:** CardDemo - Authorization Module  
**Function:** Card Authorization Decision Program

COPAUA0C is the core authorization engine for the CardDemo system. It is a CICS program driven by MQ trigger messages. When triggered, it opens the MQ request queue, reads up to 500 authorization request messages per invocation, and for each:

1. Resolves the card number to an account and customer via VSAM XREF lookup.
2. Reads the account master and customer master records.
3. Reads the IMS pending authorization summary segment (PAUTSUM0) to obtain the current running balances.
4. Makes an approve/decline decision based on available credit.
5. Puts the response onto an MQ reply queue.
6. Writes the authorization record into the IMS database (PAUTDTL1 child segment, and creates or updates the PAUTSUM0 summary).

The program uses IMS PSB scheduling within CICS (DLI SCHD/TERM) and CICS SYNCPOINT between each message processed.

---

## Artifact Inventory

| Artifact | Type | Role |
|----------|------|------|
| COPAUA0C.cbl | COBOL Source | Main program |
| CIPAUSMY.cpy | Copybook | IMS PAUTSUM0 segment layout |
| CIPAUDTY.cpy | Copybook | IMS PAUTDTL1 segment layout |
| CCPAURQY.cpy | Copybook | MQ authorization request message layout |
| CCPAURLY.cpy | Copybook | MQ authorization response message layout |
| CCPAUERY.cpy | Copybook | Application error log record layout |
| CMQODV | Copybook (IBM MQ) | MQ Object Descriptor |
| CMQMDV | Copybook (IBM MQ) | MQ Message Descriptor |
| CMQV | Copybook (IBM MQ) | MQ constants |
| CMQTML | Copybook (IBM MQ) | MQ Trigger message layout |
| CMQPMOV | Copybook (IBM MQ) | MQ Put Message Options |
| CMQGMOV | Copybook (IBM MQ) | MQ Get Message Options |
| CVACT03Y | Copybook (common) | Card XREF record layout |
| CVACT01Y | Copybook (common) | Account master record layout |
| CVCUS01Y | Copybook (common) | Customer master record layout |
| PSBPAUTB | IMS PSB | Program Specification Block for auth database |

---

## IDENTIFICATION DIVISION Metadata

- **PROGRAM-ID:** COPAUA0C  
- **AUTHOR:** SOUMA GHOSH  
- Source lines 22–24

---

## ENVIRONMENT DIVISION

No FILE-CONTROL entries. All file access uses CICS READ commands (not native COBOL I/O). Source line 27–28.

---

## DATA DIVISION

### Key Working-Storage Variables (lines 32–80)

| Field | PIC | Purpose |
|-------|-----|---------|
| WS-PGM-AUTH | X(08) | 'COPAUA0C' — program name |
| WS-CICS-TRANID | X(04) | 'CP00' — CICS transaction ID |
| WS-ACCTFILENAME | X(8) | 'ACCTDAT ' — CICS dataset name for account master |
| WS-CUSTFILENAME | X(8) | 'CUSTDAT ' — CICS dataset name for customer master |
| WS-CARDFILENAME | X(8) | 'CARDDAT ' — CICS dataset name for card master |
| WS-CARDFILENAME-ACCT-PATH | X(8) | 'CARDAIX ' — alternate index by account |
| WS-CCXREF-FILE | X(08) | 'CCXREF  ' — card cross-reference file |
| WS-REQSTS-PROCESS-LIMIT | S9(4) COMP | 500 — max messages per invocation |
| WS-MSG-PROCESSED | S9(4) COMP | Count of messages processed this invocation |
| WS-REQUEST-QNAME | X(48) | MQ request queue name (from trigger message) |
| WS-REPLY-QNAME | X(48) | MQ reply queue name (from MQMD-REPLYTOQ) |
| WS-SAVE-CORRELID | X(24) | Saved message correlation ID for reply |
| WS-WAIT-INTERVAL | S9(9) BINARY | 5000ms — MQ MQGET wait timeout |
| WS-AVAILABLE-AMT | S9(09)V99 COMP-3 | Computed available credit for decision |
| WS-TRANSACTION-AMT-AN | X(13) | Transaction amount as alphanumeric for UNSTRING |
| WS-TRANSACTION-AMT | S9(10)V99 | Transaction amount (numeric) |
| WS-APPROVED-AMT | S9(10)V99 | Approved amount |

### MQ Object and Buffer Areas (lines 99–108)

| Field | PIC | Purpose |
|-------|-----|---------|
| W01-HCONN-REQUEST | S9(9) BINARY | MQ request queue connection handle |
| W01-HOBJ-REQUEST | S9(9) BINARY | MQ request queue object handle |
| W01-BUFFLEN | S9(9) BINARY | Buffer length for MQGET |
| W01-DATALEN | S9(9) BINARY | Actual data length returned by MQGET |
| W01-GET-BUFFER | X(500) | MQ GET buffer (request message body) |
| W02-HCONN-REPLY | S9(9) BINARY | MQ reply connection handle (zero — MQPUT1 uses its own) |
| W02-BUFFLEN | S9(9) BINARY | Buffer length for MQPUT1 |
| W02-PUT-BUFFER | X(200) | MQ PUT buffer (response message body) |

### Switch Variables (lines 110–145)

| Switch | Values | Purpose |
|--------|--------|---------|
| WS-AUTH-RESP-FLG | A=Approved, D=Declined | Final decision flag |
| WS-MSG-LOOP-FLG | E=End | Controls main processing loop |
| WS-MSG-AVAILABLE-FLG | M=More, N=None | MQ message availability |
| WS-REQUEST-MQ-FLG | O=Open, C=Closed | Request queue state |
| WS-REPLY-MQ-FLG | O=Open, C=Closed | Reply queue state |
| WS-XREF-READ-FLG | Y=Found, N=Not found | Card XREF lookup result |
| WS-ACCT-MASTER-READ-FLG | Y=Found, N=Not found | Account master lookup result |
| WS-CUST-MASTER-READ-FLG | Y=Found, N=Not found | Customer master lookup result |
| WS-PAUT-SMRY-SEG-FLG | Y=Found, N=Not found | IMS summary segment existence |
| WS-DECLINE-FLG | A=Approve, D=Decline | Intermediate decision flag |
| WS-DECLINE-REASON-FLG | I=Insufficient, A=Not Active, C=Closed, F=Card Fraud, M=Merchant Fraud | Decline reason |

### IMS Variables (lines 81–95)

| Field | PIC | Value | Purpose |
|-------|-----|-------|---------|
| PSB-NAME | X(8) | 'PSBPAUTB' | PSB scheduled via DLI SCHD |
| PAUT-PCB-NUM | S9(4) COMP | +1 | PCB 1 (note: batch program CBPAUP0C uses PCB 2) |
| IMS-RETURN-CODE | X(02) | — | DIBSTAT capture |

### MQ Copybook Areas (lines 148–170)

| Variable | Copybook | Purpose |
|----------|----------|---------|
| MQM-OD-REQUEST | CMQODV | Object descriptor for request queue open |
| MQM-MD-REQUEST | CMQMDV | Message descriptor for MQGET |
| MQM-OD-REPLY | CMQODV | Object descriptor for reply MQPUT1 |
| MQM-MD-REPLY | CMQMDV | Message descriptor for MQPUT1 |
| MQM-CONSTANTS | CMQV | IBM MQ named constants |
| MQM-TRIGGER-DATA | CMQTML | Trigger message (received via CICS RETRIEVE) |
| MQM-PUT-MESSAGE-OPTIONS | CMQPMOV | Put message options |
| MQM-GET-MESSAGE-OPTIONS | CMQGMOV | Get message options |

### Staging Copybook Areas (lines 177–210)

| Variable | Copybook | Purpose |
|----------|----------|---------|
| PENDING-AUTH-REQUEST | CCPAURQY | MQ request message payload parsed into this area |
| PENDING-AUTH-RESPONSE | CCPAURLY | Response message built here before MQ PUT |
| ERROR-LOG-RECORD | CCPAUERY | Error log structure |
| PENDING-AUTH-SUMMARY | CIPAUSMY | IMS PAUTSUM0 root segment data |
| PENDING-AUTH-DETAILS | CIPAUDTY | IMS PAUTDTL1 child segment data |

### LINKAGE SECTION (line 212–215)

```
01 DFHCOMMAREA.
  05 LK-COMMAREA PIC X(4096).
```

---

## Copybooks Referenced

| Copybook | Line | Purpose |
|----------|------|---------|
| CMQODV | 149, 154 | MQ Object Descriptor |
| CMQMDV | 152, 157 | MQ Message Descriptor |
| CMQV | 161 | MQ Constants |
| CMQTML | 164 | MQ Trigger Message Layout |
| CMQPMOV | 167 | MQ Put Message Options |
| CMQGMOV | 170 | MQ Get Message Options |
| CCPAURQY | 178 | Auth request layout (see CCPAURQY.cpy) |
| CCPAURLY | 182 | Auth response layout (see CCPAURLY.cpy) |
| CCPAUERY | 185 | Error log record layout |
| CIPAUSMY | 193 | IMS summary segment |
| CIPAUDTY | 197 | IMS detail segment |
| CVACT03Y | 203 | Card XREF record (CARD-XREF-RECORD, XREF-CARD-NUM, XREF-ACCT-ID, XREF-CUST-ID) |
| CVACT01Y | 206 | Account master record (ACCOUNT-RECORD, ACCT-CREDIT-LIMIT, ACCT-CURR-BAL, ACCT-CASH-CREDIT-LIMIT) |
| CVCUS01Y | 209 | Customer master record |

---

## CCPAURQY.cpy — Authorization Request Message Fields

| Field | PIC | Description |
|-------|-----|-------------|
| PA-RQ-AUTH-DATE | X(06) | Auth date YYMMDD |
| PA-RQ-AUTH-TIME | X(06) | Auth time HHMMSS |
| PA-RQ-CARD-NUM | X(16) | Card number |
| PA-RQ-AUTH-TYPE | X(04) | Auth type |
| PA-RQ-CARD-EXPIRY-DATE | X(04) | Card expiry MMYY |
| PA-RQ-MESSAGE-TYPE | X(06) | ISO message type |
| PA-RQ-MESSAGE-SOURCE | X(06) | Source system |
| PA-RQ-PROCESSING-CODE | 9(06) | Processing code |
| PA-RQ-TRANSACTION-AMT | +9(10).99 | Transaction amount (alphanumeric with sign) |
| PA-RQ-MERCHANT-CATAGORY-CODE | X(04) | MCC |
| PA-RQ-ACQR-COUNTRY-CODE | X(03) | Country code |
| PA-RQ-POS-ENTRY-MODE | 9(02) | POS entry mode |
| PA-RQ-MERCHANT-ID | X(15) | Merchant ID |
| PA-RQ-MERCHANT-NAME | X(22) | Merchant name |
| PA-RQ-MERCHANT-CITY | X(13) | City |
| PA-RQ-MERCHANT-STATE | X(02) | State |
| PA-RQ-MERCHANT-ZIP | X(09) | ZIP |
| PA-RQ-TRANSACTION-ID | X(15) | Transaction ID |

## CCPAURLY.cpy — Authorization Response Message Fields

| Field | PIC | Description |
|-------|-----|-------------|
| PA-RL-CARD-NUM | X(16) | Card number (echoed) |
| PA-RL-TRANSACTION-ID | X(15) | Transaction ID (echoed) |
| PA-RL-AUTH-ID-CODE | X(06) | Authorization ID code |
| PA-RL-AUTH-RESP-CODE | X(02) | Response: '00'=Approved, '05'=Declined |
| PA-RL-AUTH-RESP-REASON | X(04) | Decline reason code |
| PA-RL-APPROVED-AMT | +9(10).99 | Approved amount |

---

## MQ Operations

### 1100-OPEN-REQUEST-QUEUE (line 255)

```cobol
CALL 'MQOPEN' USING W01-HCONN-REQUEST
                    MQM-OD-REQUEST
                    WS-OPTIONS         (MQOO-INPUT-SHARED)
                    W01-HOBJ-REQUEST
                    WS-COMPCODE
                    WS-REASON
```
- Opens the request queue for shared input.
- Queue name taken from trigger message MQTM-QNAME.
- Error location: 'M001'.

### 3100-READ-REQUEST-MQ (line 386)

```cobol
CALL 'MQGET' USING W01-HCONN-REQUEST
                   W01-HOBJ-REQUEST
                   MQM-MD-REQUEST
                   MQM-GET-MESSAGE-OPTIONS
                   W01-BUFFLEN
                   W01-GET-BUFFER
                   W01-DATALEN
                   WS-COMPCODE
                   WS-REASON
```
- Options: MQGMO-NO-SYNCPOINT + MQGMO-WAIT + MQGMO-CONVERT + MQGMO-FAIL-IF-QUIESCING
- Wait interval: 5000ms
- On success: saves MQMD-CORRELID to WS-SAVE-CORRELID, saves MQMD-REPLYTOQ to WS-REPLY-QNAME.
- MQRC-NO-MSG-AVAILABLE sets NO-MORE-MSG-AVAILABLE flag.
- Error location: 'M003'.

### 7100-SEND-RESPONSE (line 737)

```cobol
CALL 'MQPUT1' USING W02-HCONN-REPLY
                    MQM-OD-REPLY
                    MQM-MD-REPLY
                    MQM-PUT-MESSAGE-OPTIONS
                    W02-BUFFLEN
                    W02-PUT-BUFFER
                    WS-COMPCODE
                    WS-REASON
```
- Uses MQPUT1 (open+put+close in one call) to put reply.
- Reply queue name from WS-REPLY-QNAME (originally in MQMD-REPLYTOQ of request).
- MQMD-MSGTYPE = MQMT-REPLY; MQMD-CORRELID = WS-SAVE-CORRELID.
- Expiry: 50 (5 seconds).
- Options: MQPMO-NO-SYNCPOINT + MQPMO-DEFAULT-CONTEXT.
- Error location: 'M004'.

### 9100-CLOSE-REQUEST-QUEUE (line 953)

```cobol
CALL 'MQCLOSE' USING W01-HCONN-REQUEST
                     W01-HOBJ-REQUEST
                     MQCO-NONE
                     WS-COMPCODE
                     WS-REASON
```
- Closes the request queue only if previously opened.
- Error location: 'M005' (warning level, not critical).

---

## IMS DL/I Calls (within CICS via SCHD/TERM)

### 1200-SCHEDULE-PSB (line 292)

```cobol
EXEC DLI SCHD PSB((PSB-NAME)) NODHABEND END-EXEC
```
- Schedules PSB PSBPAUTB within the CICS task.
- If TC (already scheduled): terminates first, then re-schedules.
- Error location: 'I001'.

### 5500-READ-AUTH-SUMMRY (line 616)

```cobol
EXEC DLI GU USING PCB(PAUT-PCB-NUM)
    SEGMENT (PAUTSUM0)
    INTO (PENDING-AUTH-SUMMARY)
    WHERE (ACCNTID = PA-ACCT-ID)
END-EXEC
```
- Get Unique (GU) by account ID.
- Sets FOUND-PAUT-SMRY-SEG or NFOUND-PAUT-SMRY-SEG.
- Error location: 'I002'.

### 8400-UPDATE-SUMMARY — REPL or ISRT (lines 824–834)

```cobol
-- If summary already existed:
EXEC DLI REPL USING PCB(PAUT-PCB-NUM)
     SEGMENT (PAUTSUM0) FROM (PENDING-AUTH-SUMMARY) END-EXEC

-- If summary is new:
EXEC DLI ISRT USING PCB(PAUT-PCB-NUM)
     SEGMENT (PAUTSUM0) FROM (PENDING-AUTH-SUMMARY) END-EXEC
```
- Error location: 'I003'.

### 8500-INSERT-AUTH (line 913)

```cobol
EXEC DLI ISRT USING PCB(PAUT-PCB-NUM)
     SEGMENT (PAUTSUM0)
     WHERE (ACCNTID = PA-ACCT-ID)
     SEGMENT (PAUTDTL1)
     FROM (PENDING-AUTH-DETAILS)
     SEGLENGTH (LENGTH OF PENDING-AUTH-DETAILS)
END-EXEC
```
- Inserts a new PAUTDTL1 child segment under the located PAUTSUM0.
- Authorization key (PA-AUTH-DATE-9C / PA-AUTH-TIME-9C) computed as complement of current timestamp for descending IMS sort.
- Error location: 'I004'.

### 9000-TERMINATE (line 940)

```cobol
EXEC DLI TERM END-EXEC
```
- Terminates the PSB schedule when processing is complete.

---

## CICS Commands

| Command | Location | Purpose |
|---------|----------|---------|
| EXEC CICS RETRIEVE INTO(MQTM) | 1000-INITIALIZE (line 233) | Receives MQ trigger message |
| EXEC CICS RETURN | MAIN-PARA (line 226) | Returns to CICS |
| EXEC CICS SYNCPOINT | 2000-MAIN-PROCESS (line 334) | Commits after each message |
| EXEC CICS READ DATASET(CCXREF) | 5100-READ-XREF-RECORD (line 477) | Reads card XREF |
| EXEC CICS READ DATASET(ACCTDAT) | 5200-READ-ACCT-RECORD (line 525) | Reads account master |
| EXEC CICS READ DATASET(CUSTDAT) | 5300-READ-CUST-RECORD (line 573) | Reads customer master |
| EXEC CICS ASKTIME / FORMATTIME | 8500-INSERT-AUTH (lines 857–865) | Gets current timestamp for key |
| EXEC CICS ASKTIME / FORMATTIME | 9500-LOG-ERROR (lines 986–993) | Gets timestamp for error log |

---

## Program Flow — Paragraph Logic

### MAIN-PARA (line 220)

```
1. PERFORM 1000-INITIALIZE    (MQ trigger retrieve + open request queue + first MQGET)
2. PERFORM 2000-MAIN-PROCESS  (main processing loop)
3. PERFORM 9000-TERMINATE     (PSB TERM + MQ close)
4. EXEC CICS RETURN
```

### 1000-INITIALIZE (line 230)

- `EXEC CICS RETRIEVE INTO(MQTM)` — gets trigger message; moves queue name and trigger data.
- Sets WS-WAIT-INTERVAL to 5000.
- PERFORM 1100-OPEN-REQUEST-QUEUE.
- PERFORM 3100-READ-REQUEST-MQ (first message read).

### 2000-MAIN-PROCESS (line 323)

```
PERFORM UNTIL NO-MORE-MSG-AVAILABLE OR WS-LOOP-END
    PERFORM 2100-EXTRACT-REQUEST-MSG
    PERFORM 5000-PROCESS-AUTH
    ADD 1 TO WS-MSG-PROCESSED
    EXEC CICS SYNCPOINT
    SET IMS-PSB-NOT-SCHD TO TRUE
    IF WS-MSG-PROCESSED > 500 THEN SET WS-LOOP-END TO TRUE
    ELSE PERFORM 3100-READ-REQUEST-MQ
END-PERFORM
```

### 2100-EXTRACT-REQUEST-MSG (line 351)

- UNSTRING W01-GET-BUFFER by ',' into all CCPAURQY fields.
- FUNCTION NUMVAL converts the alphanumeric amount to numeric WS-TRANSACTION-AMT.

### 5000-PROCESS-AUTH (line 438)

```
SET APPROVE-AUTH TO TRUE
PERFORM 1200-SCHEDULE-PSB
SET CARD-FOUND-XREF, FOUND-ACCT-IN-MSTR TO TRUE
PERFORM 5100-READ-XREF-RECORD
IF CARD-FOUND-XREF
    PERFORM 5200-READ-ACCT-RECORD
    PERFORM 5300-READ-CUST-RECORD
    PERFORM 5500-READ-AUTH-SUMMRY
    PERFORM 5600-READ-PROFILE-DATA    (stub — CONTINUE)
PERFORM 6000-MAKE-DECISION
PERFORM 7100-SEND-RESPONSE
IF CARD-FOUND-XREF
    PERFORM 8000-WRITE-AUTH-TO-DB
```

### 6000-MAKE-DECISION (line 657) — Authorization Decision Logic

**Primary decision path:**

1. Echo PA-RQ-CARD-NUM and PA-RQ-TRANSACTION-ID into response fields.
2. Set PA-RL-AUTH-ID-CODE = PA-RQ-AUTH-TIME.
3. If FOUND-PAUT-SMRY-SEG: available = PA-CREDIT-LIMIT - PA-CREDIT-BALANCE.
4. Else if FOUND-ACCT-IN-MSTR: available = ACCT-CREDIT-LIMIT - ACCT-CURR-BAL.
5. Else: DECLINE-AUTH.
6. If transaction amount exceeds available: DECLINE-AUTH with INSUFFICIENT-FUND.

**Response code assignment:**

| Condition | PA-RL-AUTH-RESP-CODE | PA-RL-AUTH-RESP-REASON |
|-----------|----------------------|------------------------|
| Approved | '00' | '0000' |
| Card not in XREF | '05' | '3100' |
| Insufficient funds | '05' | '4100' |
| Card not active | '05' | '4200' |
| Account closed | '05' | '4300' |
| Card fraud | '05' | '5100' |
| Merchant fraud | '05' | '5200' |
| Other | '05' | '9000' |

**Response string built by STRING into W02-PUT-BUFFER:**
```
CARD_NUM , TRANSACTION_ID , AUTH_ID_CODE , RESP_CODE , RESP_REASON , APPROVED_AMT ,
```

### 8000-WRITE-AUTH-TO-DB (line 786)

Calls 8400-UPDATE-SUMMARY then 8500-INSERT-AUTH.

**8400-UPDATE-SUMMARY logic:**
- If NFOUND-PAUT-SMRY-SEG: initializes PENDING-AUTH-SUMMARY, sets account/customer IDs.
- Always sets credit limit and cash limit from ACCT record.
- If approved: increments PA-APPROVED-AUTH-CNT, adds to PA-APPROVED-AUTH-AMT, adds to PA-CREDIT-BALANCE, zeros PA-CASH-BALANCE.
- If declined: increments PA-DECLINED-AUTH-CNT, adds PA-TRANSACTION-AMT to PA-DECLINED-AUTH-AMT.
- Then REPL if found, ISRT if new.

**8500-INSERT-AUTH logic:**
- Gets current CICS timestamp.
- Computes PA-AUTH-DATE-9C = 99999 - YYDDD (descending sort key).
- Computes PA-AUTH-TIME-9C = 999999999 - time-with-milliseconds.
- Populates all CIPAUDTY fields from request and response.
- Sets PA-MATCH-STATUS: 'P' (Pending) if approved; 'D' (Declined) if declined.
- Clears PA-AUTH-FRAUD and PA-FRAUD-RPT-DATE.
- Inserts PAUTDTL1 child segment under the PAUTSUM0 parent.

---

## Error Handling

All errors are logged via **9500-LOG-ERROR** which formats an ERROR-LOG-RECORD (CCPAUERY) with:

| Location Code | Subsystem | Condition |
|---------------|-----------|-----------|
| M001 | MQ | Request queue open failure |
| M003 | CICS/MQ | MQGET failure |
| M004 | MQ | MQPUT1 reply failure |
| M005 | MQ | MQCLOSE warning |
| A001 | APP | Card not found in XREF |
| A002 | APP | Account not found |
| A003 | APP | Customer not found |
| C001 | CICS | XREF file read error |
| C002 | CICS | Account file read error |
| C003 | CICS | Customer file read error |
| I001 | IMS | PSB schedule failure |
| I002 | IMS | GU summary failure |
| I003 | IMS | REPL/ISRT summary failure |
| I004 | IMS | ISRT detail failure |

**Note:** The 9500-LOG-ERROR paragraph writes the error log record to a CICS resource (likely a transient data queue or file — the target is not visible in this source. The CCPAUERY copybook defines the ERROR-LOG-RECORD structure but the write destination is not coded in the visible portion of the source.)

---

## Transaction Flow Participation

| Element | Value | Role |
|---------|-------|------|
| CICS Transaction | CP00 | This program's own transaction ID |
| MQ Trigger | CICS RETRIEVE | Program is triggered by MQ trigger monitor |
| Request Queue | From MQTM-QNAME | Inbound authorization requests |
| Reply Queue | From MQMD-REPLYTOQ | Outbound authorization responses |

This program is the center of the authorization subsystem's online flow:

```
External System --[MQ Request Queue]--> COPAUA0C --[MQ Reply Queue]--> External System
                                              |
                                         VSAM CCXREF / ACCTDAT / CUSTDAT (read-only)
                                              |
                                         IMS PAUTSUM0 (REPL/ISRT)
                                         IMS PAUTDTL1 (ISRT)
```

---

## Inter-Program Interactions

| Program | Method | Purpose |
|---------|--------|---------|
| None | — | No CICS LINK/XCTL or CALL to other application programs |

COPAUA0C is self-contained. The authorization summary viewed by COPAUS0C and COPAUS1C is written by this program.
