# Technical Specification: COACCT01
## Account Details Inquiry via MQ — VSAM/MQ Extension

---

## 1. Program Overview

| Attribute         | Value                                     |
|:------------------|:------------------------------------------|
| Program ID        | COACCT01                                  |
| Transaction ID    | CDRA                                      |
| Type              | Online (CICS)                             |
| Author            | AWS                                       |
| Date Written      | 03/21                                     |
| Compilation Mode  | IS INITIAL (fresh storage on every invocation) |
| CICS Group        | CARDDEMO                                  |
| Concurrency       | QUASIRENT                                 |
| EXECKEY           | USER                                      |
| Source File       | app/app-vsam-mq/cbl/COACCT01.cbl          |
| CSD Definition    | app/app-vsam-mq/csd/CRDDEMOM.csd          |

### Purpose

COACCT01 is a CICS-hosted MQ listener program. It is started by the CICS-MQ bridge when a message arrives on an IBM MQ input queue. The program:

1. Opens an error queue, an input queue, and an output (reply) queue.
2. Reads request messages one at a time from the input queue using MQGET.
3. For each request that carries function code `INQA` and a non-zero account key, it reads the matching account record from the VSAM KSDS dataset `ACCTDAT` via a CICS READ command.
4. Formats the account fields into a human-readable reply string.
5. Writes the reply string back to the reply queue using MQPUT.
6. Continues until no more messages are available (MQRC-NO-MSG-AVAILABLE), then closes all queues and returns to CICS.

The program demonstrates the request/response MQ integration pattern in a CICS environment, acting as the server side of the exchange.

---

## 2. CICS Resource Definitions (from CRDDEMOM.csd)

### Program Definition

| Attribute      | Value         |
|:---------------|:--------------|
| PROGRAM        | COACCT01      |
| GROUP          | CARDDEMO      |
| DESCRIPTION    | LIST CARDS    |
| RELOAD         | NO            |
| RESIDENT       | NO            |
| USAGE          | NORMAL        |
| STATUS         | ENABLED       |
| CEDF           | YES           |
| DATALOCATION   | ANY           |
| EXECKEY        | USER          |
| CONCURRENCY    | QUASIRENT     |
| API            | CICSAPI       |
| DYNAMIC        | NO            |
| TRANSID        | CDRA          |
| EXECUTIONSET   | FULLAPI       |
| JVM            | NO            |
| DEFINETIME     | 23/03/23 15:10:46 |

Source: CRDDEMOM.csd, lines 1–8.

### Transaction Definition

| Attribute     | Value        |
|:--------------|:-------------|
| TRANSACTION   | CDRA         |
| PROGRAM       | COACCT01     |
| TWASIZE       | 0            |
| PROFILE       | DFHCICST     |
| STATUS        | ENABLED      |
| TASKDATALOC   | ANY          |
| TASKDATAKEY   | USER         |
| STORAGECLEAR  | NO           |
| PRIORITY      | 1            |
| TRANCLASS     | DFHTCL00     |
| DTIMOUT       | NO           |
| RESTART       | NO           |
| SPURGE        | YES          |
| TPURGE        | YES          |
| DUMP          | YES          |
| TRACE         | YES          |
| ACTION        | BACKOUT      |
| WAIT          | YES          |
| RESSEC        | NO           |
| CMDSEC        | NO           |
| DEFINETIME    | 23/03/23 15:10:46 |

Source: CRDDEMOM.csd, lines 17–26.

Note: `ACTION(BACKOUT)` means that on abnormal termination, CICS will backout any syncpoint-protected resources (including MQ messages obtained under syncpoint).

---

## 3. Program Flow

### Paragraph Call Hierarchy

```
1000-CONTROL  (main entry)
    |
    +-- 2100-OPEN-ERROR-QUEUE
    |
    +-- [EXEC CICS RETRIEVE]  (get trigger message)
    |
    +-- 2300-OPEN-INPUT-QUEUE
    |
    +-- 2400-OPEN-OUTPUT-QUEUE
    |
    +-- 3000-GET-REQUEST  (first call, outside loop)
    |
    +-- PERFORM 4000-MAIN-PROCESS UNTIL NO-MORE-MSGS
    |       |
    |       +-- [EXEC CICS SYNCPOINT]
    |       +-- 3000-GET-REQUEST
    |               |
    |               +-- 4000-PROCESS-REQUEST-REPLY  (on successful GET)
    |                       |
    |                       +-- [EXEC CICS READ DATASET(ACCTDAT)]
    |                       +-- 4100-PUT-REPLY
    |                               |
    |                               +-- [CALL 'MQPUT' to OUTPUT-QUEUE-HANDLE]
    |                               +-- 9000-ERROR (on MQPUT failure)
    |                               +-- 8000-TERMINATION (on MQPUT failure)
    |
    +-- 8000-TERMINATION
            |
            +-- 5000-CLOSE-INPUT-QUEUE   (if REPLY-QUEUE-OPEN)
            +-- 5100-CLOSE-OUTPUT-QUEUE  (if RESP-QUEUE-OPEN)
            +-- 5200-CLOSE-ERROR-QUEUE   (if ERR-QUEUE-OPEN)
            +-- [EXEC CICS RETURN]
            +-- GOBACK
```

### Step-by-Step Logic

**Step 1 — Initialization (1000-CONTROL, lines 179–219)**

- MOVE SPACES to INPUT-QUEUE-NAME, QMGR-NAME, QUEUE-MESSAGE.
- INITIALIZE MQ-ERR-DISPLAY.
- PERFORM 2100-OPEN-ERROR-QUEUE (open error queue before anything else, so errors during startup can be reported).

**Step 2 — Retrieve trigger data (1000-CONTROL, lines 191–210)**

- EXEC CICS RETRIEVE INTO(MQTM): reads the trigger message that caused CICS to start this transaction. The MQTM copybook (CMQTML) contains the MQTM-QNAME field, which identifies which input queue this trigger originated from.
- If RESP = DFHRESP(NORMAL): MOVE MQTM-QNAME TO INPUT-QUEUE-NAME; MOVE 'CARD.DEMO.REPLY.ACCT' TO REPLY-QUEUE-NAME.
- If RESP is not NORMAL: populate MQ-ERR-DISPLAY with paragraph name 'CICS RETREIVE' [sic — source has a typo at line 200], RESP codes, then PERFORM 9000-ERROR and PERFORM 8000-TERMINATION (fatal, program exits).

**Step 3 — Open queues (1000-CONTROL, lines 212–213)**

- PERFORM 2300-OPEN-INPUT-QUEUE.
- PERFORM 2400-OPEN-OUTPUT-QUEUE.

**Step 4 — Initial GET (1000-CONTROL, line 214)**

- PERFORM 3000-GET-REQUEST: attempt to read the first message before entering the processing loop.

**Step 5 — Processing loop (1000-CONTROL, lines 215–218)**

- PERFORM 4000-MAIN-PROCESS UNTIL NO-MORE-MSGS.
- Loop terminates when WS-MQ-MSG-FLAG = 'Y' (set when MQRC-NO-MSG-AVAILABLE is returned).

**Step 6 — Normal termination (1000-CONTROL, line 218)**

- PERFORM 8000-TERMINATION.

---

### Paragraph: 2100-OPEN-ERROR-QUEUE (lines 289–322)

- Hardcode ERROR-QUEUE-NAME = 'CARD.DEMO.ERROR' (line 294).
- MOVE SPACES to MQOD-OBJECTQMGRNAME (use default queue manager).
- MOVE ERROR-QUEUE-NAME to MQOD-OBJECTNAME.
- COMPUTE MQ-OPTIONS = MQOO-OUTPUT + MQOO-PASS-ALL-CONTEXT + MQOO-FAIL-IF-QUIESCING.
- CALL 'MQOPEN' (arguments: QMGR-HANDLE-CONN, MQ-OBJECT-DESCRIPTOR, MQ-OPTIONS, MQ-HOBJ, MQ-CONDITION-CODE, MQ-REASON-CODE).
- On MQCC-OK: MOVE MQ-HOBJ TO ERROR-QUEUE-HANDLE; SET ERR-QUEUE-OPEN TO TRUE.
- On failure: DISPLAY MQ-ERR-DISPLAY; PERFORM 8000-TERMINATION (no 9000-ERROR here because error queue is not yet open).

---

### Paragraph: 2300-OPEN-INPUT-QUEUE (lines 222–253)

- MOVE SPACES to MQOD-OBJECTQMGRNAME.
- MOVE INPUT-QUEUE-NAME to MQOD-OBJECTNAME.
- COMPUTE MQ-OPTIONS = MQOO-INPUT-SHARED + MQOO-SAVE-ALL-CONTEXT + MQOO-FAIL-IF-QUIESCING.
- CALL 'MQOPEN'.
- On MQCC-OK: MOVE MQ-HOBJ TO INPUT-QUEUE-HANDLE; SET REPLY-QUEUE-OPEN TO TRUE.
  (Note: the status flag SET here is REPLY-QUEUE-OPEN, not INPUT-QUEUE-OPEN; this is the flag checked in 8000-TERMINATION to decide whether to call 5000-CLOSE-INPUT-QUEUE.)
- On failure: MOVE INPUT-QUEUE-NAME to MQ-APPL-QUEUE-NAME; MOVE 'INP MQOPEN ERR' to MQ-APPL-RETURN-MESSAGE; PERFORM 9000-ERROR; PERFORM 8000-TERMINATION (fatal).

---

### Paragraph: 2400-OPEN-OUTPUT-QUEUE (lines 255–287)

- MOVE SPACES to MQOD-OBJECTQMGRNAME.
- MOVE REPLY-QUEUE-NAME ('CARD.DEMO.REPLY.ACCT') to MQOD-OBJECTNAME.
- COMPUTE MQ-OPTIONS = MQOO-OUTPUT + MQOO-PASS-ALL-CONTEXT + MQOO-FAIL-IF-QUIESCING.
- CALL 'MQOPEN'.
- On MQCC-OK: MOVE MQ-HOBJ TO OUTPUT-QUEUE-HANDLE; SET RESP-QUEUE-OPEN TO TRUE.
- On failure: MOVE REPLY-QUEUE-NAME to MQ-APPL-QUEUE-NAME; MOVE 'OUT MQOPEN ERR' to MQ-APPL-RETURN-MESSAGE; PERFORM 9000-ERROR; PERFORM 8000-TERMINATION (fatal).

---

### Paragraph: 4000-MAIN-PROCESS (lines 325–331)

- EXEC CICS SYNCPOINT END-EXEC: commits the previous syncpoint unit of work (including the MQGET destructive read of the last message).
- PERFORM 3000-GET-REQUEST: fetch the next message.

---

### Paragraph: 3000-GET-REQUEST (lines 334–388)

- Set MQGMO-WAITINTERVAL = 5000 (5-second wait).
- MOVE SPACES to MQ-CORRELID and MQ-MSG-ID.
- MOVE INPUT-QUEUE-NAME to MQ-QUEUE; MOVE INPUT-QUEUE-HANDLE to MQ-HOBJ.
- MOVE 1000 to MQ-BUFFER-LENGTH.
- MOVE MQMI-NONE to MQMD-MSGID; MOVE MQCI-NONE to MQMD-CORRELID (receive any message, no filter).
- INITIALIZE REQUEST-MSG-COPY REPLACING NUMERIC BY ZEROES.
- COMPUTE MQGMO-OPTIONS = MQGMO-SYNCPOINT + MQGMO-FAIL-IF-QUIESCING + MQGMO-CONVERT + MQGMO-WAIT.
- CALL 'MQGET' (arguments: MQ-HCONN, MQ-HOBJ, MQ-MESSAGE-DESCRIPTOR, MQ-GET-MESSAGE-OPTIONS, MQ-BUFFER-LENGTH, MQ-BUFFER, MQ-DATA-LENGTH, MQ-CONDITION-CODE, MQ-REASON-CODE).
- On MQCC-OK:
  - MOVE MQMD-MSGID to MQ-MSG-ID.
  - MOVE MQMD-CORRELID to MQ-CORRELID.
  - MOVE MQMD-REPLYTOQ to MQ-QUEUE-REPLY.
  - MOVE MQ-BUFFER to REQUEST-MESSAGE.
  - MOVE MQ-CORRELID to SAVE-CORELID; MOVE MQ-QUEUE-REPLY to SAVE-REPLY2Q; MOVE MQ-MSG-ID to SAVE-MSGID.
  - MOVE REQUEST-MESSAGE to REQUEST-MSG-COPY (overlay parsed structure over raw buffer).
  - PERFORM 4000-PROCESS-REQUEST-REPLY.
  - ADD 1 TO MQ-MSG-COUNT.
- If MQRC-NO-MSG-AVAILABLE: SET NO-MORE-MSGS TO TRUE (terminates PERFORM loop in 1000-CONTROL).
- On other error: populate MQ-APPL-CONDITION-CODE, MQ-APPL-REASON-CODE, MQ-APPL-QUEUE-NAME; MOVE 'INP MQGET ERR:' to MQ-APPL-RETURN-MESSAGE; PERFORM 9000-ERROR; PERFORM 8000-TERMINATION (fatal).

---

### Paragraph: 4000-PROCESS-REQUEST-REPLY (lines 390–460)

This paragraph contains the core business logic.

- MOVE SPACES to REPLY-MESSAGE.
- INITIALIZE WS-DATE-TIME REPLACING NUMERIC BY ZEROES.
- Condition check: IF WS-FUNC = 'INQA' AND WS-KEY > ZEROES

  **Valid request path:**
  - MOVE WS-KEY TO WS-CARD-RID-ACCT-ID (convert numeric key from request message into the VSAM key field).
  - EXEC CICS READ:
    - DATASET(LIT-ACCTFILENAME) — literal 'ACCTDAT '.
    - RIDFLD(WS-CARD-RID-ACCT-ID-X) — character redefinition of the 11-digit account ID.
    - KEYLENGTH(LENGTH OF WS-CARD-RID-ACCT-ID-X) = 11.
    - INTO(ACCOUNT-RECORD) — CVACT01Y structure (300 bytes).
    - LENGTH(LENGTH OF ACCOUNT-RECORD) = 300.
    - RESP(WS-RESP-CD), RESP2(WS-REAS-CD).
  - EVALUATE WS-RESP-CD:
    - WHEN DFHRESP(NORMAL): Map account fields from ACCOUNT-RECORD to WS-ACCT-RESPONSE (see Data Structures section); MOVE WS-ACCT-RESPONSE TO REPLY-MESSAGE; PERFORM 4100-PUT-REPLY.
    - WHEN DFHRESP(NOTFND): STRING 'INVALID REQUEST PARAMETERS ACCT ID : ' WS-KEY DELIMITED BY SIZE INTO REPLY-MESSAGE; PERFORM 4100-PUT-REPLY.
    - WHEN OTHER: MOVE WS-RESP-CD to MQ-APPL-CONDITION-CODE; MOVE WS-REAS-CD to MQ-APPL-REASON-CODE; MOVE INPUT-QUEUE-NAME to MQ-APPL-QUEUE-NAME; MOVE 'ERROR WHILE READING ACCTFILE' to MQ-APPL-RETURN-MESSAGE; PERFORM 9000-ERROR; PERFORM 8000-TERMINATION (fatal).

  **Invalid request path (ELSE — WS-FUNC != 'INQA' or WS-KEY = 0):**
  - STRING 'INVALID REQUEST PARAMETERS ACCT ID : ' WS-KEY ' FUNCTION : ' WS-FUNC DELIMITED BY SIZE INTO REPLY-MESSAGE.
  - PERFORM 4100-PUT-REPLY.

---

### Paragraph: 4100-PUT-REPLY (lines 462–499)

- MOVE REPLY-MESSAGE to MQ-BUFFER.
- MOVE 1000 to MQ-BUFFER-LENGTH.
- MOVE SAVE-MSGID to MQMD-MSGID (echo back original message ID for correlation).
- MOVE SAVE-CORELID to MQMD-CORRELID.
- MOVE MQFMT-STRING to MQMD-FORMAT.
- COMPUTE MQMD-CODEDCHARSETID = MQCCSI-Q-MGR.
- COMPUTE MQPMO-OPTIONS = MQPMO-SYNCPOINT + MQPMO-DEFAULT-CONTEXT + MQPMO-FAIL-IF-QUIESCING.
- CALL 'MQPUT' (arguments: MQ-HCONN, OUTPUT-QUEUE-HANDLE, MQ-MESSAGE-DESCRIPTOR, MQ-PUT-MESSAGE-OPTIONS, MQ-BUFFER-LENGTH, MQ-BUFFER, MQ-CONDITION-CODE, MQ-REASON-CODE).
- On MQCC-OK: record codes in MQ-APPL fields.
- On failure: populate MQ-APPL-QUEUE-NAME = REPLY-QUEUE-NAME; MQ-APPL-RETURN-MESSAGE = 'MQPUT ERR'; PERFORM 9000-ERROR; PERFORM 8000-TERMINATION.

---

### Paragraph: 9000-ERROR (lines 501–537)

- MOVE MQ-ERR-DISPLAY to ERROR-MESSAGE.
- MOVE ERROR-MESSAGE to MQ-BUFFER.
- MOVE 1000 to MQ-BUFFER-LENGTH.
- MOVE MQFMT-STRING to MQMD-FORMAT.
- COMPUTE MQMD-CODEDCHARSETID = MQCCSI-Q-MGR.
- COMPUTE MQPMO-OPTIONS = MQPMO-SYNCPOINT + MQPMO-DEFAULT-CONTEXT + MQPMO-FAIL-IF-QUIESCING.
- CALL 'MQPUT' to ERROR-QUEUE-HANDLE (writes error details to 'CARD.DEMO.ERROR' queue).
- On MQPUT failure: DISPLAY MQ-ERR-DISPLAY (fallback to CICS log); PERFORM 8000-TERMINATION.

---

### Paragraph: 8000-TERMINATION (lines 538–550)

- IF REPLY-QUEUE-OPEN: PERFORM 5000-CLOSE-INPUT-QUEUE.
- IF RESP-QUEUE-OPEN: PERFORM 5100-CLOSE-OUTPUT-QUEUE.
- IF ERR-QUEUE-OPEN: PERFORM 5200-CLOSE-ERROR-QUEUE.
- EXEC CICS RETURN END-EXEC.
- GOBACK.

---

### Paragraphs: 5000, 5100, 5200 — Queue Close Routines (lines 552–620)

Each close paragraph follows the identical pattern:

- MOVE [queue name] to MQ-QUEUE; MOVE [queue handle] to MQ-HOBJ.
- COMPUTE MQ-OPTIONS = MQCO-NONE.
- CALL 'MQCLOSE' (arguments: MQ-HCONN, MQ-HOBJ, MQ-OPTIONS, MQ-CONDITION-CODE, MQ-REASON-CODE).
- On MQCC-OK: record codes.
- On failure: set MQ-APPL fields; PERFORM 9000-ERROR and/or PERFORM 8000-TERMINATION (5200 calls both; 5000 and 5100 call only 8000-TERMINATION).

| Paragraph             | Closes               | Handle               |
|:----------------------|:---------------------|:---------------------|
| 5000-CLOSE-INPUT-QUEUE  | INPUT-QUEUE-NAME   | INPUT-QUEUE-HANDLE   |
| 5100-CLOSE-OUTPUT-QUEUE | REPLY-QUEUE-NAME   | OUTPUT-QUEUE-HANDLE  |
| 5200-CLOSE-ERROR-QUEUE  | ERROR-QUEUE-NAME   | ERROR-QUEUE-HANDLE   |

---

## 4. Data Structures

### 4.1 Status Flags

| Variable              | PIC    | Initial | 88-Level Condition   | Usage                                      |
|:----------------------|:-------|:--------|:---------------------|:-------------------------------------------|
| WS-MQ-MSG-FLAG        | X(01)  | 'N'     | NO-MORE-MSGS = 'Y'   | Loop termination sentinel                  |
| WS-RESP-QUEUE-STS     | X(01)  | 'N'     | RESP-QUEUE-OPEN = 'Y'| Tracks whether output queue was opened     |
| WS-ERR-QUEUE-STS      | X(01)  | 'N'     | ERR-QUEUE-OPEN = 'Y' | Tracks whether error queue was opened      |
| WS-REPLY-QUEUE-STS    | X(01)  | 'N'     | REPLY-QUEUE-OPEN = 'Y'| Tracks whether input queue was opened     |

Source: COACCT01.cbl, lines 13–23.

Note on naming inconsistency: WS-REPLY-QUEUE-STS / REPLY-QUEUE-OPEN is SET TO TRUE inside 2300-OPEN-INPUT-QUEUE (line 245), not inside an "open reply queue" paragraph. Its check in 8000-TERMINATION at line 540 controls whether 5000-CLOSE-INPUT-QUEUE is called.

---

### 4.2 CICS Response Codes

| Variable            | PIC           | Usage                                |
|:--------------------|:--------------|:-------------------------------------|
| WS-CICS-RESP1-CD    | S9(08) COMP   | RESP parameter for CICS commands     |
| WS-CICS-RESP2-CD    | S9(08) COMP   | RESP2 parameter for CICS commands    |
| WS-CICS-RESP1-CD-D  | 9(08)         | Display-friendly copy of RESP1       |
| WS-CICS-RESP2-CD-D  | 9(08)         | Display-friendly copy of RESP2       |

Source: COACCT01.cbl, lines 26–30.

---

### 4.3 Date/Time Fields

| Variable       | PIC           | Usage                                  |
|:---------------|:--------------|:---------------------------------------|
| WS-ABS-TIME    | S9(15) COMP-3 | Absolute CICS time (not used in COACCT01's business path, but initialized) |
| WS-MMDDYYYY    | X(10)         | Formatted date                         |
| WS-TIME        | X(8)          | Formatted time                         |

Source: COACCT01.cbl, lines 35–38.

Note: WS-DATE-TIME is INITIALIZED in 4000-PROCESS-REQUEST-REPLY but ASKTIME/FORMATTIME are NOT called in COACCT01 (they are only used in CODATE01). The initialization here is defensive cleanup only.

---

### 4.4 Core MQ Communication Variables

| Variable              | PIC              | Usage                                                     |
|:----------------------|:-----------------|:----------------------------------------------------------|
| MQ-QUEUE              | X(48)            | Working queue name for current MQOPEN/MQCLOSE             |
| MQ-QUEUE-REPLY        | X(48)            | Reply-to queue name extracted from inbound MQMD           |
| MQ-HCONN              | S9(09) BINARY    | MQ connection handle (obtained externally by CICS bridge) |
| MQ-CONDITION-CODE     | S9(09) BINARY    | MQ completion code (MQCC-OK, MQCC-WARNING, MQCC-FAILED)   |
| MQ-REASON-CODE        | S9(09) BINARY    | MQ reason code                                            |
| MQ-HOBJ               | S9(09) BINARY    | Working object handle for current MQOPEN/MQCLOSE          |
| MQ-OPTIONS            | S9(09) BINARY    | Options bitmask for MQOPEN/MQCLOSE                        |
| MQ-BUFFER-LENGTH      | S9(09) BINARY    | Length of MQ-BUFFER passed to MQGET/MQPUT                 |
| MQ-BUFFER             | X(1000)          | Message data buffer                                       |
| MQ-DATA-LENGTH        | S9(09) BINARY    | Actual data length returned by MQGET                      |
| MQ-CORRELID           | X(24)            | Correlation ID from inbound message descriptor            |
| MQ-MSG-ID             | X(24)            | Message ID from inbound message descriptor                |
| MQ-MSG-COUNT          | 9(09)            | Count of messages processed in this invocation            |
| SAVE-CORELID          | X(24)            | Saved correlation ID for use in MQPUT reply               |
| SAVE-MSGID            | X(24)            | Saved message ID for use in MQPUT reply                   |
| SAVE-REPLY2Q          | X(48)            | Saved REPLYTOQ name (captured but not used for dynamic routing in this program) |

Source: COACCT01.cbl, lines 42–57.

---

### 4.5 MQ Error Display Record

| Sub-field                  | PIC    | Usage                              |
|:---------------------------|:-------|:-----------------------------------|
| MQ-ERROR-PARA              | X(25)  | Paragraph name where error occurred|
| FILLER                     | X(02)  | Spaces                             |
| MQ-APPL-RETURN-MESSAGE     | X(25)  | Application error description      |
| FILLER                     | X(02)  | Spaces                             |
| MQ-APPL-CONDITION-CODE     | 9(02)  | MQ condition code (display)        |
| FILLER                     | X(02)  | Spaces                             |
| MQ-APPL-REASON-CODE        | 9(05)  | MQ reason code (display)           |
| FILLER                     | X(02)  | Spaces                             |
| MQ-APPL-QUEUE-NAME         | X(48)  | Queue name involved in error       |

Total length: 25+2+25+2+2+2+5+2+48 = 113 bytes.
Source: COACCT01.cbl, lines 58–68.

---

### 4.6 MQ Copybook Members (External — IBM-supplied)

| COPY Member | 01-Level Group           | Contents                                               |
|:------------|:-------------------------|:-------------------------------------------------------|
| CMQGMOV     | MQ-GET-MESSAGE-OPTIONS   | MQGMO structure: get options, wait interval, etc.      |
| CMQPMOV     | MQ-PUT-MESSAGE-OPTIONS   | MQPMO structure: put options                           |
| CMQMDV      | MQ-MESSAGE-DESCRIPTOR    | MQMD structure: message descriptor (MsgId, CorrelId, Format, ReplyToQ, etc.) |
| CMQODV      | MQ-OBJECT-DESCRIPTOR     | MQOD structure: object descriptor (ObjectName, ObjectQMgrName, etc.) |
| CMQV        | MQ-CONSTANTS             | Named constants: MQCC-OK, MQOO-*, MQGMO-*, MQPMO-*, MQRC-*, etc. |
| CMQTML      | MQ-GET-QUEUE-MESSAGE     | MQTM trigger message structure: MQTM-QNAME, etc.       |

Source: COACCT01.cbl, lines 71–90. All six are IBM MQ for z/OS-supplied copybooks.
**[UNRESOLVED]** These copybooks are not present in the `app/cpy/` directory. Field-level layouts require the IBM MQ for z/OS copybook library (typically SCSQCOBC or equivalent).

---

### 4.7 Queue Handles and Names

| Variable              | PIC              | Initial | Usage                                           |
|:----------------------|:-----------------|:--------|:------------------------------------------------|
| QMGR-NAME             | X(48)            | SPACES  | Queue manager name (left blank = default QM)    |
| INPUT-QUEUE-NAME      | X(48)            | SPACES  | Populated from MQTM-QNAME via CICS RETRIEVE     |
| REPLY-QUEUE-NAME      | X(48)            | SPACES  | Hardcoded 'CARD.DEMO.REPLY.ACCT'                |
| ERROR-QUEUE-NAME      | X(48)            | SPACES  | Hardcoded 'CARD.DEMO.ERROR'                     |
| INPUT-QUEUE-HANDLE    | S9(09) BINARY    | 0       | Handle from MQOPEN of input queue               |
| OUTPUT-QUEUE-HANDLE   | S9(09) BINARY    | 0       | Handle from MQOPEN of reply queue               |
| ERROR-QUEUE-HANDLE    | S9(09) BINARY    | 0       | Handle from MQOPEN of error queue               |
| QMGR-HANDLE-CONN      | S9(09) BINARY    | 0       | Connection handle (set by CICS MQ bridge)       |

Source: COACCT01.cbl, lines 92–104.

---

### 4.8 Message Buffers

| Variable          | PIC      | Usage                                                              |
|:------------------|:---------|:-------------------------------------------------------------------|
| QUEUE-MESSAGE     | X(1000)  | General queue message work area                                    |
| REQUEST-MESSAGE   | X(1000)  | Raw inbound message from MQGET                                     |
| REPLY-MESSAGE     | X(1000)  | Outbound reply message to be sent via MQPUT                        |
| ERROR-MESSAGE     | X(1000)  | Error payload sent to CARD.DEMO.ERROR queue                        |

Source: COACCT01.cbl, lines 105–108.

---

### 4.9 Request Message Parsed Structure

```
01 REQUEST-MSG-COPY.
   10 WS-FUNC    PIC X(04)   -- Function code; 'INQA' = account inquiry
   10 WS-KEY     PIC 9(11)   -- Account number (numeric, 11 digits)
   10 WS-FILLER  PIC X(985)  -- Unused padding to total 1000 bytes
```

Source: COACCT01.cbl, lines 109–112.

The inbound MQ message must be exactly 1000 bytes with this layout. REQUEST-MESSAGE (raw buffer) is MOVED to REQUEST-MSG-COPY for field-level access to WS-FUNC and WS-KEY.

---

### 4.10 Working Variables

| Variable           | PIC          | Initial | Usage                                             |
|:-------------------|:-------------|:--------|:--------------------------------------------------|
| LIT-ACCTFILENAME   | X(8)         | 'ACCTDAT ' | CICS dataset name for account VSAM file        |
| WS-RESP-CD         | S9(09) COMP  | ZEROS   | CICS RESP from EXEC CICS READ                     |
| WS-REAS-CD         | S9(09) COMP  | ZEROS   | CICS RESP2 from EXEC CICS READ                    |
| WS-CARD-RID-CARDNUM| X(16)        | (none)  | Card number (part of WS-XREF-RID; not used here)  |
| WS-CARD-RID-CUST-ID| 9(09)        | (none)  | Customer ID (not used in this program)            |
| WS-CARD-RID-ACCT-ID| 9(11)        | (none)  | Account ID for VSAM READ key (numeric)            |
| WS-CARD-RID-ACCT-ID-X | X(11)    | (none)  | Character redefinition of above; passed as RIDFLD |

Source: COACCT01.cbl, lines 114–128.

---

### 4.11 Account Response Formatting Record

```
01 WS-ACCT-RESPONSE.
   05 WS-ACCT-LBL               PIC X(13)  VALUE 'ACCOUNT ID : '
   05 WS-ACCT-ID                PIC 9(11)
   05 WS-STATUS-LBL             PIC X(17)  VALUE 'ACCOUNT STATUS : '
   05 WS-ACCT-ACTIVE-STATUS     PIC X(01)
   05 WS-CURR-BAL-LBL           PIC X(10)  VALUE 'BALANCE : '
   05 WS-ACCT-CURR-BAL          PIC S9(10)V99
   05 WS-CRDT-LMT-LBL           PIC X(15)  VALUE 'CREDIT LIMIT : '
   05 WS-ACCT-CREDIT-LIMIT      PIC S9(10)V99
   05 WS-CASH-LIMIT-LBL         PIC X(13)  VALUE 'CASH LIMIT : '
   05 WS-ACCT-CASH-CREDIT-LIMIT PIC S9(10)V99
   05 WS-OPEN-DATE-LBL          PIC X(12)  VALUE 'OPEN DATE : '
   05 WS-ACCT-OPEN-DATE         PIC X(10)
   05 WS-EXPR-DATE-LBL          PIC X(12)  VALUE 'EXPR DATE : '
   05 WS-ACCT-EXPIRAION-DATE    PIC X(10)
   05 WS-REISSUE-DT-LBL         PIC X(12)  VALUE 'REIS DATE : '
   05 WS-ACCT-REISSUE-DATE      PIC X(10)
   05 WS-CURR-CYC-CREDIT-LBL    PIC X(13)  VALUE 'CREDIT BAL : '
   05 WS-ACCT-CURR-CYC-CREDIT   PIC S9(10)V99
   05 WS-CURR-CYC-DEBIT-LBL     PIC X(12)  VALUE 'DEBIT BAL : '
   05 WS-ACCT-CURR-CYC-DEBIT    PIC S9(10)V99
   05 WS-ACCT-GRP-LBL           PIC X(11)  VALUE 'GROUP ID : '
   05 WS-ACCT-GROUP-ID          PIC X(10)
```

Source: COACCT01.cbl, lines 130–169.

This record is the output template. Fixed-text labels are interleaved with data fields. The entire 01-level is MOVED to REPLY-MESSAGE (X(1000)) before MQPUT. Fields beyond the end of WS-ACCT-RESPONSE in REPLY-MESSAGE remain SPACES.

---

### 4.12 Account Record (from CVACT01Y copybook)

```
01 ACCOUNT-RECORD.
   05 ACCT-ID                 PIC 9(11)
   05 ACCT-ACTIVE-STATUS      PIC X(01)
   05 ACCT-CURR-BAL           PIC S9(10)V99
   05 ACCT-CREDIT-LIMIT       PIC S9(10)V99
   05 ACCT-CASH-CREDIT-LIMIT  PIC S9(10)V99
   05 ACCT-OPEN-DATE          PIC X(10)
   05 ACCT-EXPIRAION-DATE     PIC X(10)   [note: typo in original — "EXPIRAION"]
   05 ACCT-REISSUE-DATE       PIC X(10)
   05 ACCT-CURR-CYC-CREDIT    PIC S9(10)V99
   05 ACCT-CURR-CYC-DEBIT     PIC S9(10)V99
   05 ACCT-ADDR-ZIP           PIC X(10)
   05 ACCT-GROUP-ID           PIC X(10)
   05 FILLER                  PIC X(178)
```

Total record length: 300 bytes.
Source: app/cpy/CVACT01Y.cpy, COPY invoked at COACCT01.cbl line 171.

Note: ACCT-ADDR-ZIP is read into the record but is NOT propagated into WS-ACCT-RESPONSE. It is silently discarded in the reply message.

---

## 5. MQ Commands Summary

| Call        | Paragraph                  | Queue               | Handle                | Options                                                                  |
|:------------|:---------------------------|:--------------------|:----------------------|:-------------------------------------------------------------------------|
| MQOPEN      | 2100-OPEN-ERROR-QUEUE      | CARD.DEMO.ERROR     | ERROR-QUEUE-HANDLE    | MQOO-OUTPUT + MQOO-PASS-ALL-CONTEXT + MQOO-FAIL-IF-QUIESCING             |
| MQOPEN      | 2300-OPEN-INPUT-QUEUE      | (from MQTM-QNAME)   | INPUT-QUEUE-HANDLE    | MQOO-INPUT-SHARED + MQOO-SAVE-ALL-CONTEXT + MQOO-FAIL-IF-QUIESCING       |
| MQOPEN      | 2400-OPEN-OUTPUT-QUEUE     | CARD.DEMO.REPLY.ACCT| OUTPUT-QUEUE-HANDLE   | MQOO-OUTPUT + MQOO-PASS-ALL-CONTEXT + MQOO-FAIL-IF-QUIESCING             |
| MQGET       | 3000-GET-REQUEST           | INPUT-QUEUE-NAME    | INPUT-QUEUE-HANDLE    | MQGMO-SYNCPOINT + MQGMO-FAIL-IF-QUIESCING + MQGMO-CONVERT + MQGMO-WAIT (5000ms) |
| MQPUT       | 4100-PUT-REPLY             | CARD.DEMO.REPLY.ACCT| OUTPUT-QUEUE-HANDLE   | MQPMO-SYNCPOINT + MQPMO-DEFAULT-CONTEXT + MQPMO-FAIL-IF-QUIESCING        |
| MQPUT       | 9000-ERROR                 | CARD.DEMO.ERROR     | ERROR-QUEUE-HANDLE    | MQPMO-SYNCPOINT + MQPMO-DEFAULT-CONTEXT + MQPMO-FAIL-IF-QUIESCING        |
| MQCLOSE     | 5000-CLOSE-INPUT-QUEUE     | INPUT-QUEUE-NAME    | INPUT-QUEUE-HANDLE    | MQCO-NONE                                                                |
| MQCLOSE     | 5100-CLOSE-OUTPUT-QUEUE    | REPLY-QUEUE-NAME    | OUTPUT-QUEUE-HANDLE   | MQCO-NONE                                                                |
| MQCLOSE     | 5200-CLOSE-ERROR-QUEUE     | ERROR-QUEUE-NAME    | ERROR-QUEUE-HANDLE    | MQCO-NONE                                                                |

### Important MQ Design Notes

1. **Syncpoint scope**: Both MQGET (in 3000-GET-REQUEST) and MQPUT (in 4100-PUT-REPLY and 9000-ERROR) are performed under MQGMO-SYNCPOINT / MQPMO-SYNCPOINT. This means the destructive read of the input message and the write of the reply are both protected by CICS UOW. The EXEC CICS SYNCPOINT in 4000-MAIN-PROCESS commits the previous UOW before processing the next message.

2. **Message correlation**: SAVE-MSGID and SAVE-CORELID are copied from the MQGET response (MQMD-MSGID and MQMD-CORRELID) and placed back into MQMD-MSGID and MQMD-CORRELID on MQPUT. This preserves the correlation chain so the requesting client can match the reply to its original request.

3. **Reply queue hardcoded**: Despite capturing MQMD-REPLYTOQ into MQ-QUEUE-REPLY (and SAVE-REPLY2Q), the output queue for MQPUT is always OUTPUT-QUEUE-HANDLE, which was opened against the hardcoded 'CARD.DEMO.REPLY.ACCT' queue. The SAVE-REPLY2Q value is not used to route the reply dynamically.

4. **MQHCONN**: MQ-HCONN / QMGR-HANDLE-CONN are both declared as PIC S9(09) BINARY with VALUE 0. In the CICS-MQ bridge model, the connection handle is established by CICS itself before the transaction starts; the program does not call MQCONN. The 0 initial value works because CICS provides the handle implicitly.

---

## 6. VSAM File Access

| Attribute         | Value                            |
|:------------------|:---------------------------------|
| CICS Dataset Name | ACCTDAT (from LIT-ACCTFILENAME = 'ACCTDAT ') |
| Access Type       | EXEC CICS READ (random, by key)  |
| Access Mode       | Read-only                        |
| RIDFLD            | WS-CARD-RID-ACCT-ID-X (X(11))   |
| KEYLENGTH         | 11                               |
| INTO              | ACCOUNT-RECORD (300 bytes)       |
| Record Layout     | CVACT01Y.cpy                     |
| Paragraph         | 4000-PROCESS-REQUEST-REPLY       |

The dataset name 'ACCTDAT' is a CICS file definition name. The actual z/OS dataset name is resolved through the CICS File Control Table (FCT) or CICS resource definition. **[UNRESOLVED]** The FCT/CSD definition for ACCTDAT is not present in this codebase; the underlying z/OS dataset name and VSAM cluster details cannot be confirmed from available source.

### VSAM Read Conditions

| RESP Condition   | Action                                                         |
|:-----------------|:---------------------------------------------------------------|
| DFHRESP(NORMAL)  | Extract fields; format WS-ACCT-RESPONSE; PUT reply to MQ      |
| DFHRESP(NOTFND)  | Format 'INVALID REQUEST PARAMETERS ACCT ID : nnn' reply to MQ |
| All other        | Set error message 'ERROR WHILE READING ACCTFILE'; call 9000-ERROR; call 8000-TERMINATION (fatal) |

---

## 7. Called Programs and External Interfaces

| Type             | Target          | Paragraph             | Method               | Purpose                        |
|:-----------------|:----------------|:----------------------|:---------------------|:-------------------------------|
| MQ API           | MQOPEN          | 2100, 2300, 2400      | CALL 'MQOPEN'        | Open queues                    |
| MQ API           | MQGET           | 3000-GET-REQUEST      | CALL 'MQGET'         | Retrieve messages               |
| MQ API           | MQPUT           | 4100-PUT-REPLY        | CALL 'MQPUT'         | Send reply                     |
| MQ API           | MQPUT           | 9000-ERROR            | CALL 'MQPUT'         | Send error to error queue      |
| MQ API           | MQCLOSE         | 5000, 5100, 5200      | CALL 'MQCLOSE'       | Close queues                   |
| CICS command     | RETRIEVE        | 1000-CONTROL          | EXEC CICS RETRIEVE   | Get trigger message data       |
| CICS command     | READ            | 4000-PROCESS-REQUEST-REPLY | EXEC CICS READ  | VSAM account lookup            |
| CICS command     | SYNCPOINT       | 4000-MAIN-PROCESS     | EXEC CICS SYNCPOINT  | Commit current UOW             |
| CICS command     | RETURN          | 8000-TERMINATION      | EXEC CICS RETURN     | Return control to CICS         |

No static or dynamic CICS LINK, XCTL, or program-to-program CALL other than the MQ API calls listed above.

---

## 8. Error Handling

### Error Taxonomy

| Error Condition             | Detection Point          | Action                                           | Fatal? |
|:----------------------------|:-------------------------|:-------------------------------------------------|:-------|
| CICS RETRIEVE failure       | 1000-CONTROL             | Log to MQ-ERR-DISPLAY; 9000-ERROR; 8000-TERMINATION | Yes |
| MQOPEN failure (error queue)| 2100-OPEN-ERROR-QUEUE    | DISPLAY MQ-ERR-DISPLAY; 8000-TERMINATION         | Yes    |
| MQOPEN failure (input queue)| 2300-OPEN-INPUT-QUEUE    | 9000-ERROR; 8000-TERMINATION                     | Yes    |
| MQOPEN failure (output queue)| 2400-OPEN-OUTPUT-QUEUE  | 9000-ERROR; 8000-TERMINATION                     | Yes    |
| MQGET failure (no message)  | 3000-GET-REQUEST         | SET NO-MORE-MSGS TO TRUE; graceful termination   | No     |
| MQGET failure (other)       | 3000-GET-REQUEST         | 9000-ERROR; 8000-TERMINATION                     | Yes    |
| Invalid message (func/key)  | 4000-PROCESS-REQUEST-REPLY| Format error reply; PUT to reply queue; continue| No     |
| VSAM NOTFND                 | 4000-PROCESS-REQUEST-REPLY| Format NOTFND reply; PUT to reply queue; continue| No    |
| VSAM other failure          | 4000-PROCESS-REQUEST-REPLY| 9000-ERROR; 8000-TERMINATION                    | Yes    |
| MQPUT failure (reply)       | 4100-PUT-REPLY           | 9000-ERROR; 8000-TERMINATION                     | Yes    |
| MQPUT failure (error queue) | 9000-ERROR               | DISPLAY MQ-ERR-DISPLAY; 8000-TERMINATION         | Yes    |
| MQCLOSE failure (input)     | 5000-CLOSE-INPUT-QUEUE   | 8000-TERMINATION (recursive, exits via CICS RETURN) | Yes |
| MQCLOSE failure (output)    | 5100-CLOSE-OUTPUT-QUEUE  | 8000-TERMINATION                                 | Yes    |
| MQCLOSE failure (error)     | 5200-CLOSE-ERROR-QUEUE   | 9000-ERROR; 8000-TERMINATION                     | Yes    |

### Error Message Format

When 9000-ERROR is called, the full MQ-ERR-DISPLAY record (113 bytes) is written to 'CARD.DEMO.ERROR'. The record contains the originating paragraph name, a textual description, the MQ condition code, the MQ reason code, and the queue name involved.

### CICS Transaction Backout

The CSD defines ACTION(BACKOUT) for transaction CDRA. If the task abnormally terminates, any MQGET or MQPUT operations performed under syncpoint will be backed out, meaning the input message is requeued and any partial reply is removed.

---

## 9. Business Rules

1. **Function code validation**: Only requests where WS-FUNC = 'INQA' (account inquiry) AND WS-KEY > ZEROES (non-zero account number) are processed against VSAM. Any other combination results in an error reply message sent back to the caller without a VSAM read.

2. **Account data extraction**: All primary financial and status fields from the account record are included in the reply: account ID, active status, current balance, credit limit, cash credit limit, open date, expiration date, reissue date, current cycle credit, current cycle debit, and group ID.

3. **Excluded field**: ACCT-ADDR-ZIP is present in ACCOUNT-RECORD (CVACT01Y) but is not mapped into WS-ACCT-RESPONSE and does not appear in the reply message.

4. **Reply format**: The reply is a free-form human-readable string with embedded labels (e.g., 'ACCOUNT ID : ', 'BALANCE : '). It is not a structured data record; it is text suitable for display or logging by the consuming application.

5. **Not-found handling**: An account not found in VSAM results in an informational reply message (not an error queue message). The transaction continues to the next message.

6. **Message counting**: MQ-MSG-COUNT accumulates the number of successfully processed messages in each invocation but is not persisted or reported anywhere in the program.

7. **Queue name sourcing**: The input queue name is dynamically obtained at runtime from the MQ trigger message (MQTM-QNAME). The output queue is hardcoded ('CARD.DEMO.REPLY.ACCT'). The error queue is hardcoded ('CARD.DEMO.ERROR').

---

## 10. Inputs and Outputs

### Inputs

| Source               | Variable / Structure      | Description                                    |
|:---------------------|:--------------------------|:-----------------------------------------------|
| MQ trigger message   | MQTM (via CICS RETRIEVE)  | Contains MQTM-QNAME identifying input queue    |
| MQ input queue       | REQUEST-MESSAGE / REQUEST-MSG-COPY | Inbound account inquiry request message |
| VSAM ACCTDAT         | ACCOUNT-RECORD (CVACT01Y) | Account master record (300 bytes)              |

### Input Message Layout (REQUEST-MSG-COPY)

| Field      | PIC     | Offset | Value Expected |
|:-----------|:--------|:-------|:---------------|
| WS-FUNC    | X(04)   | 1      | 'INQA' for account inquiry |
| WS-KEY     | 9(11)   | 5      | 11-digit account number (> 0) |
| WS-FILLER  | X(985)  | 16     | Unused         |

### Outputs

| Destination          | Variable         | Description                                      |
|:---------------------|:-----------------|:-------------------------------------------------|
| MQ reply queue       | REPLY-MESSAGE    | Account data formatted as labeled text string    |
| MQ error queue       | ERROR-MESSAGE    | MQ-ERR-DISPLAY content on processing failure     |

### Reply Message Layout (on successful VSAM READ)

The reply is the content of WS-ACCT-RESPONSE (approximately 230 bytes of labels and data), zero-padded to 1000 bytes within REPLY-MESSAGE.

```
'ACCOUNT ID : ' + 11-digit-account-id
'ACCOUNT STATUS : ' + 1-char-status
'BALANCE : ' + signed-numeric-balance
'CREDIT LIMIT : ' + signed-numeric-limit
'CASH LIMIT : ' + signed-numeric-cash-limit
'OPEN DATE : ' + 10-char-date
'EXPR DATE : ' + 10-char-date
'REIS DATE : ' + 10-char-date
'CREDIT BAL : ' + signed-numeric-cycle-credit
'DEBIT BAL : ' + signed-numeric-cycle-debit
'GROUP ID : ' + 10-char-group-id
```

### Reply Message Layout (on NOTFND)

```
'INVALID REQUEST PARAMETERS ACCT ID : ' + WS-KEY (11 digits)
```

### Reply Message Layout (on invalid request)

```
'INVALID REQUEST PARAMETERS ACCT ID : ' + WS-KEY + ' FUNCTION : ' + WS-FUNC
```

---

## 11. Key Variables and Their Purpose

| Variable                  | Purpose                                                                          |
|:--------------------------|:---------------------------------------------------------------------------------|
| WS-FUNC                   | Function discriminator from inbound message; must be 'INQA' for VSAM lookup     |
| WS-KEY                    | Account number from inbound message; used as VSAM RIDFLD                         |
| INPUT-QUEUE-NAME          | MQ queue name for reading requests; sourced from MQTM trigger message at startup |
| REPLY-QUEUE-NAME          | Fixed output queue 'CARD.DEMO.REPLY.ACCT'; receives all reply messages           |
| ERROR-QUEUE-NAME          | Fixed error queue 'CARD.DEMO.ERROR'; receives error diagnostic messages           |
| WS-MQ-MSG-FLAG / NO-MORE-MSGS | Controls main processing loop; set when MQRC-NO-MSG-AVAILABLE received    |
| SAVE-MSGID / SAVE-CORELID | Preserve MQMD identifiers for echoing back in reply, enabling message correlation|
| ACCOUNT-RECORD            | VSAM record buffer overlaid by CVACT01Y structure; source of all reply data      |
| WS-ACCT-RESPONSE          | Pre-formatted reply template with embedded labels; moved directly to MQ buffer   |
| QMGR-HANDLE-CONN          | MQ connection handle; initialized to 0, used as-is (supplied by CICS MQ bridge) |
| MQ-ERR-DISPLAY            | Composite error record; content written to CARD.DEMO.ERROR on any fatal error    |
