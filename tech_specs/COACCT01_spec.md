# Technical Specification: COACCT01

## 1. Executive Summary

COACCT01 is a **CICS MQ-triggered COBOL program** in the VSAM-MQ subsystem of the CardDemo application. It acts as a **VSAM account lookup service**: it listens on an IBM MQ input queue for request messages, reads account records from the VSAM KSDS file `ACCTDAT`, and returns formatted account details to a reply queue. The program implements a request-reply messaging pattern using IBM MQ API calls (`MQOPEN`, `MQGET`, `MQPUT`, `MQCLOSE`) and CICS file services (`EXEC CICS READ`). It is triggered by CICS MQ bridge, which starts the CICS transaction and passes the triggering queue name via `EXEC CICS RETRIEVE`. The program processes messages in a loop until the input queue is empty, then terminates cleanly.

---

## 2. Artifact Inventory

| Artifact | Type | Location |
|---|---|---|
| COACCT01.cbl | CICS online COBOL program (MQ-triggered) | `app/app-vsam-mq/cbl/COACCT01.cbl` |
| CVACT01Y | VSAM account record layout copybook | Standard CardDemo (included at line 171) |
| CMQGMOV | IBM MQ GET message options structure | IBM MQ-supplied |
| CMQPMOV | IBM MQ PUT message options structure | IBM MQ-supplied |
| CMQMDV | IBM MQ message descriptor structure | IBM MQ-supplied |
| CMQODV | IBM MQ object descriptor structure | IBM MQ-supplied |
| CMQV | IBM MQ constants | IBM MQ-supplied |
| CMQTML | IBM MQ trigger message layout | IBM MQ-supplied |

---

## 3. Program Identity

| Attribute | Value | Source |
|---|---|---|
| Program-ID | COACCT01 IS INITIAL | Line 2 |
| Author | AWS | Line 3 |
| Date Written | 03/21 | Line 4 |
| Invocation | CICS MQ-triggered (EXEC CICS RETRIEVE) | Lines 191-210 |
| VSAM File | ACCTDAT | Line 115 (LIT-ACCTFILENAME = 'ACCTDAT ') |
| Reply queue | CARD.DEMO.REPLY.ACCT | Line 198 (hardcoded) |
| Error queue | CARD.DEMO.ERROR | Line 294 (hardcoded) |
| Function code | 'INQA' | Line 393 (required in request message) |

---

## 4. MQ Infrastructure

### 4.1 Queue Names

| Queue Name | Role | Set At |
|---|---|---|
| (from RETRIEVE MQTM-QNAME) | Input queue — request messages arrive here | Line 197 — from CICS MQ trigger message |
| CARD.DEMO.REPLY.ACCT | Reply queue — response messages sent here | Line 198 (hardcoded literal) |
| CARD.DEMO.ERROR | Error queue — error details sent here | Line 294 (hardcoded literal) |

### 4.2 MQ Objects and Working Storage

| Field | PIC | Purpose |
|---|---|---|
| MQ-QUEUE | PIC X(48) | Current queue name being operated on |
| MQ-QUEUE-REPLY | PIC X(48) | Reply queue name from MQMD-REPLYTOQ |
| MQ-HCONN | PIC S9(9) BINARY | MQ connection handle |
| MQ-CONDITION-CODE | PIC S9(9) BINARY | MQ return code (MQCC-OK, etc.) |
| MQ-REASON-CODE | PIC S9(9) BINARY | MQ reason code (MQRC-*) |
| MQ-HOBJ | PIC S9(9) BINARY | MQ object handle (queue handle) |
| MQ-OPTIONS | PIC S9(9) BINARY | MQOPEN/MQCLOSE options |
| MQ-BUFFER-LENGTH | PIC S9(9) BINARY | Buffer size for GET/PUT (1000) |
| MQ-BUFFER | PIC X(1000) | Message data buffer |
| MQ-DATA-LENGTH | PIC S9(9) BINARY | Actual length returned by MQGET |
| MQ-CORRELID | PIC X(24) | Correlation ID from received message |
| MQ-MSG-ID | PIC X(24) | Message ID from received message |
| MQ-MSG-COUNT | PIC 9(9) | Count of messages processed |
| SAVE-CORELID | PIC X(24) | Preserved MQMD-CORRELID for PUT reply |
| SAVE-MSGID | PIC X(24) | Preserved MQMD-MSGID for PUT reply |
| SAVE-REPLY2Q | PIC X(48) | Preserved MQMD-REPLYTOQ |
| INPUT-QUEUE-HANDLE | PIC S9(9) BINARY | Handle for input queue |
| OUTPUT-QUEUE-HANDLE | PIC S9(9) BINARY | Handle for reply queue |
| ERROR-QUEUE-HANDLE | PIC S9(9) BINARY | Handle for error queue |
| QMGR-HANDLE-CONN | PIC S9(9) BINARY | Queue manager connection handle |

### 4.3 MQ Copybook Structures

| Copybook | Structure Name | Purpose |
|---|---|---|
| CMQGMOV | MQ-GET-MESSAGE-OPTIONS (MQGMO) | Controls MQGET behavior |
| CMQPMOV | MQ-PUT-MESSAGE-OPTIONS (MQPMO) | Controls MQPUT behavior |
| CMQMDV | MQ-MESSAGE-DESCRIPTOR (MQMD) | Message header (MsgId, CorrelId, Format, ReplyToQ) |
| CMQODV | MQ-OBJECT-DESCRIPTOR (MQOD) | Queue object descriptor (ObjectName, ObjectQMgrName) |
| CMQV | MQ-CONSTANTS | MQCC-OK, MQRC-*, MQOO-*, MQGMO-*, MQPMO-*, etc. |
| CMQTML | MQ-GET-QUEUE-MESSAGE (MQTM) | CICS MQ trigger message layout (contains MQTM-QNAME) |

---

## 5. Request Message Format

Request messages arrive with this structure (REQUEST-MSG-COPY, lines 109-112):

| Offset | Len | Field | PIC | Description |
|---|---|---|---|---|
| 1 | 4 | WS-FUNC | X(4) | Function code; must be 'INQA' for account query |
| 5 | 11 | WS-KEY | 9(11) | Account ID (numeric, 11 digits) |
| 16 | 985 | WS-FILLER | X(985) | Unused padding |

Total message length: 1000 bytes (matching MQ-BUFFER-LENGTH).

---

## 6. Response Message Format

On successful lookup, the reply is WS-ACCT-RESPONSE (lines 130-169) moved into REPLY-MESSAGE and then into MQ-BUFFER:

| Field | PIC | Label Prefix in Message |
|---|---|---|
| WS-ACCT-LBL + WS-ACCT-ID | PIC X(13) + 9(11) | 'ACCOUNT ID : ' + value |
| WS-STATUS-LBL + WS-ACCT-ACTIVE-STATUS | PIC X(17) + X(1) | 'ACCOUNT STATUS : ' + value |
| WS-CURR-BAL-LBL + WS-ACCT-CURR-BAL | PIC X(10) + S9(10)V99 | 'BALANCE : ' + value |
| WS-CRDT-LMT-LBL + WS-ACCT-CREDIT-LIMIT | PIC X(15) + S9(10)V99 | 'CREDIT LIMIT : ' + value |
| WS-CASH-LIMIT-LBL + WS-ACCT-CASH-CREDIT-LIMIT | PIC X(13) + S9(10)V99 | 'CASH LIMIT : ' + value |
| WS-OPEN-DATE-LBL + WS-ACCT-OPEN-DATE | PIC X(12) + X(10) | 'OPEN DATE : ' + value |
| WS-EXPR-DATE-LBL + WS-ACCT-EXPIRAION-DATE | PIC X(12) + X(10) | 'EXPR DATE : ' + value |
| WS-REISSUE-DT-LBL + WS-ACCT-REISSUE-DATE | PIC X(12) + X(10) | 'REIS DATE : ' + value |
| WS-CURR-CYC-CREDIT-LBL + WS-ACCT-CURR-CYC-CREDIT | PIC X(13) + S9(10)V99 | 'CREDIT BAL : ' + value |
| WS-CURR-CYC-DEBIT-LBL + WS-ACCT-CURR-CYC-DEBIT | PIC X(12) + S9(10)V99 | 'DEBIT BAL : ' + value |
| WS-ACCT-GRP-LBL + WS-ACCT-GROUP-ID | PIC X(11) + X(10) | 'GROUP ID : ' + value |

---

## 7. VSAM File Operations

### 7.1 File Definition

| Attribute | Value |
|---|---|
| CICS File Name | ACCTDAT (LIT-ACCTFILENAME = 'ACCTDAT ') |
| Access Type | CICS-managed VSAM KSDS (accessed via EXEC CICS READ) |
| Key Type | Account ID (numeric, 11 digits) |
| Record Layout | ACCOUNT-RECORD (from CVACT01Y copybook) |

### 7.2 Read Operation (paragraph 4000-PROCESS-REQUEST-REPLY, lines 390-457)

```
EXEC CICS READ
     DATASET   (LIT-ACCTFILENAME)
     RIDFLD    (WS-CARD-RID-ACCT-ID-X)
     KEYLENGTH (LENGTH OF WS-CARD-RID-ACCT-ID-X)
     INTO      (ACCOUNT-RECORD)
     LENGTH    (LENGTH OF ACCOUNT-RECORD)
     RESP      (WS-RESP-CD)
     RESP2     (WS-REAS-CD)
END-EXEC
```

Key field: `WS-CARD-RID-ACCT-ID-X` (PIC X(11)) — alphanumeric form of `WS-CARD-RID-ACCT-ID` (PIC 9(11)).

Key is set: `MOVE WS-KEY TO WS-CARD-RID-ACCT-ID` (line 394).

RESP handling:
- `DFHRESP(NORMAL)`: Maps ACCOUNT-RECORD fields to WS-ACCT-RESPONSE, then PERFORM 4100-PUT-REPLY
- `DFHRESP(NOTFND)`: STRINGs 'INVALID REQUEST PARAMETERS ACCT ID : ' + WS-KEY into REPLY-MESSAGE, then PERFORM 4100-PUT-REPLY
- OTHER: Formats error, PERFORM 9000-ERROR then PERFORM 8000-TERMINATION

### 7.3 ACCOUNT-RECORD Fields Extracted (from CVACT01Y copybook)

| Source Field | Target Field | Purpose |
|---|---|---|
| ACCT-ID | WS-ACCT-ID | Account ID |
| ACCT-ACTIVE-STATUS | WS-ACCT-ACTIVE-STATUS | Active/inactive flag |
| ACCT-CURR-BAL | WS-ACCT-CURR-BAL | Current balance |
| ACCT-CREDIT-LIMIT | WS-ACCT-CREDIT-LIMIT | Credit limit |
| ACCT-CASH-CREDIT-LIMIT | WS-ACCT-CASH-CREDIT-LIMIT | Cash credit limit |
| ACCT-OPEN-DATE | WS-ACCT-OPEN-DATE | Account open date |
| ACCT-EXPIRAION-DATE | WS-ACCT-EXPIRAION-DATE | Expiration date |
| ACCT-REISSUE-DATE | WS-ACCT-REISSUE-DATE | Reissue date |
| ACCT-CURR-CYC-CREDIT | WS-ACCT-CURR-CYC-CREDIT | Current cycle credit |
| ACCT-CURR-CYC-DEBIT | WS-ACCT-CURR-CYC-DEBIT | Current cycle debit |
| ACCT-GROUP-ID | WS-ACCT-GROUP-ID | Account group ID |

[ARTIFACT NOT AVAILABLE FOR INSPECTION: CVACT01Y full field PIC clauses not provided in the analyzed directory. The above is derived from field references in COACCT01.cbl lines 408-425.]

---

## 8. CICS Commands

| Command | Paragraph | Purpose |
|---|---|---|
| `EXEC CICS RETRIEVE INTO(MQTM) RESP(...) RESP2(...)` | `1000-CONTROL` (lines 191-210) | Retrieve MQ trigger message from CICS — contains input queue name |
| `EXEC CICS READ DATASET(ACCTDAT) ...` | `4000-PROCESS-REQUEST-REPLY` (lines 396-404) | Read account record from VSAM |
| `EXEC CICS SYNCPOINT` | `4000-MAIN-PROCESS` (lines 326-328) | Commit after each message cycle |
| `EXEC CICS RETURN` | `8000-TERMINATION` (line 549) | Return to CICS after processing all messages |

---

## 9. MQ Operations (Detailed)

### 9.1 2100-OPEN-ERROR-QUEUE (lines 289-322)

- Sets `ERROR-QUEUE-NAME = 'CARD.DEMO.ERROR'`
- Sets MQOD-OBJECTNAME = ERROR-QUEUE-NAME
- MQ-OPTIONS = MQOO-OUTPUT + MQOO-PASS-ALL-CONTEXT + MQOO-FAIL-IF-QUIESCING
- `CALL 'MQOPEN'` — stores handle in ERROR-QUEUE-HANDLE
- On failure: DISPLAY MQ-ERR-DISPLAY, PERFORM 8000-TERMINATION

### 9.2 2300-OPEN-INPUT-QUEUE (lines 222-253)

- Sets MQOD-OBJECTNAME = INPUT-QUEUE-NAME (from CICS RETRIEVE)
- MQ-OPTIONS = MQOO-INPUT-SHARED + MQOO-SAVE-ALL-CONTEXT + MQOO-FAIL-IF-QUIESCING
- `CALL 'MQOPEN'` — stores handle in INPUT-QUEUE-HANDLE
- On failure: PERFORM 9000-ERROR, PERFORM 8000-TERMINATION

### 9.3 2400-OPEN-OUTPUT-QUEUE (lines 255-287)

- Sets MQOD-OBJECTNAME = REPLY-QUEUE-NAME ('CARD.DEMO.REPLY.ACCT')
- MQ-OPTIONS = MQOO-OUTPUT + MQOO-PASS-ALL-CONTEXT + MQOO-FAIL-IF-QUIESCING
- `CALL 'MQOPEN'` — stores handle in OUTPUT-QUEUE-HANDLE
- On failure: PERFORM 9000-ERROR, PERFORM 8000-TERMINATION

### 9.4 3000-GET-REQUEST (lines 334-388)

- MQGMO-WAITINTERVAL = 5000 (5 second wait)
- Clears MQ-CORRELID, MQ-MSG-ID
- MQGMO-OPTIONS = MQGMO-SYNCPOINT + MQGMO-FAIL-IF-QUIESCING + MQGMO-CONVERT + MQGMO-WAIT
- Sets MQMD-MSGID = MQMI-NONE, MQMD-CORRELID = MQCI-NONE
- `CALL 'MQGET' USING MQ-HCONN MQ-HOBJ MQ-MESSAGE-DESCRIPTOR MQ-GET-MESSAGE-OPTIONS MQ-BUFFER-LENGTH MQ-BUFFER MQ-DATA-LENGTH MQ-CONDITION-CODE MQ-REASON-CODE`
- On MQCC-OK:
  - Saves MQMD-MSGID → SAVE-MSGID
  - Saves MQMD-CORRELID → SAVE-CORELID
  - Saves MQMD-REPLYTOQ → MQ-QUEUE-REPLY and SAVE-REPLY2Q
  - Moves MQ-BUFFER → REQUEST-MESSAGE → REQUEST-MSG-COPY
  - PERFORMs 4000-PROCESS-REQUEST-REPLY
  - Increments MQ-MSG-COUNT
- On MQRC-NO-MSG-AVAILABLE: SET NO-MORE-MSGS TO TRUE (exits 4000-MAIN-PROCESS loop)
- Other error: PERFORM 9000-ERROR, PERFORM 8000-TERMINATION

### 9.5 4100-PUT-REPLY (lines 462-499)

- MOVE REPLY-MESSAGE TO MQ-BUFFER (1000 bytes)
- Restores MQMD-MSGID = SAVE-MSGID, MQMD-CORRELID = SAVE-CORELID
- MQMD-FORMAT = MQFMT-STRING
- MQMD-CODEDCHARSETID = MQCCSI-Q-MGR
- MQPMO-OPTIONS = MQPMO-SYNCPOINT + MQPMO-DEFAULT-CONTEXT + MQPMO-FAIL-IF-QUIESCING
- `CALL 'MQPUT' USING MQ-HCONN OUTPUT-QUEUE-HANDLE MQ-MESSAGE-DESCRIPTOR MQ-PUT-MESSAGE-OPTIONS MQ-BUFFER-LENGTH MQ-BUFFER MQ-CONDITION-CODE MQ-REASON-CODE`
- On failure: PERFORM 9000-ERROR, PERFORM 8000-TERMINATION

### 9.6 9000-ERROR (lines 501-537)

- Moves MQ-ERR-DISPLAY → ERROR-MESSAGE → MQ-BUFFER
- MQMD-FORMAT = MQFMT-STRING
- MQPMO-OPTIONS = MQPMO-SYNCPOINT + MQPMO-DEFAULT-CONTEXT + MQPMO-FAIL-IF-QUIESCING
- `CALL 'MQPUT' USING MQ-HCONN ERROR-QUEUE-HANDLE ...` — writes error to CARD.DEMO.ERROR queue
- On MQPUT failure: DISPLAY MQ-ERR-DISPLAY, PERFORM 8000-TERMINATION

### 9.7 Close Paragraphs (5000, 5100, 5200)

All use `CALL 'MQCLOSE' USING MQ-HCONN MQ-HOBJ MQ-OPTIONS(MQCO-NONE) MQ-CONDITION-CODE MQ-REASON-CODE`.
- 5000-CLOSE-INPUT-QUEUE: closes INPUT-QUEUE-HANDLE
- 5100-CLOSE-OUTPUT-QUEUE: closes OUTPUT-QUEUE-HANDLE
- 5200-CLOSE-ERROR-QUEUE: closes ERROR-QUEUE-HANDLE

### 9.8 8000-TERMINATION (lines 538-549)

- Conditionally closes each queue if its open flag is set (REPLY-QUEUE-OPEN, RESP-QUEUE-OPEN, ERR-QUEUE-OPEN)
- `EXEC CICS RETURN END-EXEC`

---

## 10. PROCEDURE DIVISION — Paragraph-by-Paragraph Logic

### Control Flow

```
1000-CONTROL (entry point)
     |
     +---> PERFORM 2100-OPEN-ERROR-QUEUE
     |
     +---> EXEC CICS RETRIEVE INTO(MQTM)
     |         If OK: INPUT-QUEUE-NAME = MQTM-QNAME
     |                REPLY-QUEUE-NAME = 'CARD.DEMO.REPLY.ACCT'
     |         Else:  PERFORM 9000-ERROR, PERFORM 8000-TERMINATION
     |
     +---> PERFORM 2300-OPEN-INPUT-QUEUE
     +---> PERFORM 2400-OPEN-OUTPUT-QUEUE
     |
     +---> PERFORM 3000-GET-REQUEST      (prime the loop)
     |
     +---> PERFORM 4000-MAIN-PROCESS UNTIL NO-MORE-MSGS
     |           |
     |           +---> EXEC CICS SYNCPOINT
     |           +---> PERFORM 3000-GET-REQUEST
     |                     |
     |                     +---> MQGET message
     |                     +---> If OK: PERFORM 4000-PROCESS-REQUEST-REPLY
     |                     +---> If no more msgs: SET NO-MORE-MSGS
     |                     +---> If error: PERFORM 9000-ERROR, 8000-TERMINATION
     |
     +---> PERFORM 8000-TERMINATION
```

**4000-PROCESS-REQUEST-REPLY** (lines 390-460):
1. MOVE SPACES TO REPLY-MESSAGE; INITIALIZE WS-DATE-TIME
2. Check: IF WS-FUNC = 'INQA' AND WS-KEY > ZEROES:
   - Move WS-KEY → WS-CARD-RID-ACCT-ID → WS-CARD-RID-ACCT-ID-X
   - EXEC CICS READ DATASET(ACCTDAT) ...
   - On NORMAL: map ACCOUNT-RECORD → WS-ACCT-RESPONSE, PUT reply
   - On NOTFND: STRING invalid request message, PUT reply
   - On OTHER: format error, PERFORM 9000-ERROR, PERFORM 8000-TERMINATION
3. ELSE (wrong function or zero key):
   - STRING 'INVALID REQUEST PARAMETERS ACCT ID:... FUNCTION:...' INTO REPLY-MESSAGE
   - PERFORM 4100-PUT-REPLY

---

## 11. Error Handling

| Condition | Action |
|---|---|
| CICS RETRIEVE fails | PERFORM 9000-ERROR (put to error queue), PERFORM 8000-TERMINATION |
| MQOPEN (input) fails | PERFORM 9000-ERROR, PERFORM 8000-TERMINATION |
| MQOPEN (output) fails | PERFORM 9000-ERROR, PERFORM 8000-TERMINATION |
| MQOPEN (error queue) fails | DISPLAY MQ-ERR-DISPLAY, PERFORM 8000-TERMINATION |
| MQGET fails (not MQRC-NO-MSG-AVAILABLE) | PERFORM 9000-ERROR, PERFORM 8000-TERMINATION |
| CICS READ NOTFND | Returns 'INVALID REQUEST PARAMETERS' in reply message |
| CICS READ other error | PERFORM 9000-ERROR, PERFORM 8000-TERMINATION |
| MQPUT (reply) fails | PERFORM 9000-ERROR, PERFORM 8000-TERMINATION |
| MQPUT (error queue) fails | DISPLAY MQ-ERR-DISPLAY, PERFORM 8000-TERMINATION |
| MQCLOSE fails | PERFORM 8000-TERMINATION |
| Invalid function code or zero key | Returns 'INVALID REQUEST PARAMETERS' in reply message |

Error messages are structured in MQ-ERR-DISPLAY (lines 58-67):
- `MQ-ERROR-PARA`: 25-char paragraph name
- `MQ-APPL-RETURN-MESSAGE`: 25-char return message
- `MQ-APPL-CONDITION-CODE`: 2-digit condition code
- `MQ-APPL-REASON-CODE`: 5-digit reason code
- `MQ-APPL-QUEUE-NAME`: 48-char queue name

---

## 12. DB2 SQL Statements

None. This program does not use DB2.

---

## 13. BMS Screen / CICS Map Operations

None. This is a headless service program with no screen interaction.

---

## 14. Queue-Opened Status Flags

| Flag | PIC | 88-Level True Value | Meaning |
|---|---|---|---|
| WS-MQ-MSG-FLAG | X(1) | 'Y' = NO-MORE-MSGS | No more messages on input queue |
| WS-RESP-QUEUE-STS | X(1) | 'Y' = RESP-QUEUE-OPEN | Reply (output) queue is open |
| WS-ERR-QUEUE-STS | X(1) | 'Y' = ERR-QUEUE-OPEN | Error queue is open |
| WS-REPLY-QUEUE-STS | X(1) | 'Y' = REPLY-QUEUE-OPEN | Input queue handle stored (flag name is misleading — it tracks the input queue) |

Note: The flag `REPLY-QUEUE-OPEN` is SET in `2300-OPEN-INPUT-QUEUE` (line 245), but its name suggests it tracks the reply queue. This is a naming inconsistency in the code. At line 540 in `8000-TERMINATION`, `IF REPLY-QUEUE-OPEN PERFORM 5000-CLOSE-INPUT-QUEUE` confirms it actually gates the input queue close.

---

## 15. Inter-Program Interactions

| Component | Mechanism | Purpose |
|---|---|---|
| CICS MQ Bridge | EXEC CICS RETRIEVE | Provides triggering queue name (MQTM-QNAME) |
| IBM MQ (MQOPEN/MQGET/MQPUT/MQCLOSE) | Native MQ API CALL | Queue management and message exchange |
| ACCTDAT VSAM file | EXEC CICS READ | Account record lookup |
| CARD.DEMO.REPLY.ACCT queue | MQPUT | Sends account data replies |
| CARD.DEMO.ERROR queue | MQPUT | Sends error details |

---

## 16. Copybooks Referenced

| Copybook | Location | Purpose |
|---|---|---|
| CMQGMOV | Line 71 | MQ GET message options (MQGMO structure) |
| CMQPMOV | Line 75 | MQ PUT message options (MQPMO structure) |
| CMQMDV | Line 79 | MQ message descriptor (MQMD structure) |
| CMQODV | Line 83 | MQ object descriptor (MQOD structure) |
| CMQV | Line 87 | MQ constants (MQCC-OK, MQRC-*, MQOO-*, etc.) |
| CMQTML | Line 90 | MQ trigger message layout (MQTM, MQTM-QNAME) |
| CVACT01Y | Line 171 | VSAM account record layout (ACCOUNT-RECORD, ACCT-* fields) |

---

## 17. Open Questions and Gaps

1. **CVACT01Y**: Not available in the `app-vsam-mq` directory. The full ACCOUNT-RECORD field PIC clauses cannot be verified. Field names (ACCT-ID, ACCT-ACTIVE-STATUS, ACCT-CURR-BAL, etc.) are inferred from MOVE statements in lines 408-425.

2. **CICS transaction ID**: The triggering CICS transaction ID for COACCT01 is not defined in any artifact provided. It would be defined in the CICS CSD or DFHCSDUP definitions for the MQ bridge trigger.

3. **Queue Manager name**: QMGR-NAME is initialized to SPACES and never set — the MQ API calls use QMGR-HANDLE-CONN (initialized to binary 0) as the connection handle. This implies the program relies on the CICS-managed MQ connection rather than an explicit MQCONN call. CICS itself manages the queue manager connection in the MQ bridge scenario.

4. **WS-REPLY-QUEUE-STS naming**: The flag is named `REPLY-QUEUE-OPEN` but actually tracks whether the input queue is open. This is a code defect or naming error that should be noted for modernization.

5. **MQ-MSG-COUNT**: Incremented for each successfully processed message but never used or reported anywhere in the program.
