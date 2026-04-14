# Technical Specification: CODATE01
## System Date Inquiry via MQ — VSAM/MQ Extension

---

## 1. Program Overview

| Attribute         | Value                                     |
|:------------------|:------------------------------------------|
| Program ID        | CODATE01                                  |
| Transaction ID    | CDRD                                      |
| Type              | Online (CICS)                             |
| Author            | AWS                                       |
| Date Written      | 03/21                                     |
| Compilation Mode  | IS INITIAL (fresh storage on every invocation) |
| CICS Group        | CARDDEMO                                  |
| Concurrency       | QUASIRENT                                 |
| EXECKEY           | USER                                      |
| Source File       | app/app-vsam-mq/cbl/CODATE01.cbl          |
| CSD Definition    | app/app-vsam-mq/csd/CRDDEMOM.csd          |

### Purpose

CODATE01 is a CICS-hosted MQ listener program that implements the server side of a date inquiry request/response pattern. It is started by the CICS-MQ bridge when a message arrives on an IBM MQ input queue. The program:

1. Opens an error queue, an input queue, and an output (reply) queue.
2. Reads request messages one at a time from the input queue using MQGET.
3. For each request received, queries the CICS system for the current date and time using EXEC CICS ASKTIME / FORMATTIME.
4. Formats the system date and time into a human-readable reply string.
5. Writes the reply string back to the reply queue using MQPUT.
6. Continues until no more messages are available (MQRC-NO-MSG-AVAILABLE), then closes all queues and returns to CICS.

CODATE01 performs no VSAM file I/O. It is a pure MQ-to-CICS-time-service bridge. The program structure is architecturally identical to COACCT01, differing only in the business logic within 4000-PROCESS-REQUEST-REPLY.

---

## 2. CICS Resource Definitions (from CRDDEMOM.csd)

### Program Definition

| Attribute      | Value         |
|:---------------|:--------------|
| PROGRAM        | CODATE01      |
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
| TRANSID        | CDRD          |
| EXECUTIONSET   | FULLAPI       |
| JVM            | NO            |
| DEFINETIME     | 23/03/23 15:10:46 |

Source: CRDDEMOM.csd, lines 9–16.

### Transaction Definition

| Attribute     | Value        |
|:--------------|:-------------|
| TRANSACTION   | CDRD         |
| PROGRAM       | CODATE01     |
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

Source: CRDDEMOM.csd, lines 27–36.

Note: `ACTION(BACKOUT)` means that on abnormal termination, CICS will backout syncpoint-protected MQ messages (MQGET and MQPUT performed under syncpoint).

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
    |                       +-- [EXEC CICS ASKTIME]
    |                       +-- [EXEC CICS FORMATTIME]
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

**Step 1 — Initialization (1000-CONTROL, lines 129–134)**

- MOVE SPACES to INPUT-QUEUE-NAME, QMGR-NAME, QUEUE-MESSAGE.
- INITIALIZE MQ-ERR-DISPLAY.
- PERFORM 2100-OPEN-ERROR-QUEUE. Opening the error queue first ensures that any subsequent errors during startup can be reported via MQ.

**Step 2 — Retrieve trigger data (1000-CONTROL, lines 140–158)**

- EXEC CICS RETRIEVE INTO(MQTM) RESP(WS-CICS-RESP1-CD) RESP2(WS-CICS-RESP2-CD): reads the MQ trigger message that caused CICS to start this transaction. MQTM is the structure defined by the CMQTML copybook.
- If RESP = DFHRESP(NORMAL): MOVE MQTM-QNAME TO INPUT-QUEUE-NAME; MOVE 'CARD.DEMO.REPLY.DATE' TO REPLY-QUEUE-NAME.
- If RESP is not NORMAL: MOVE 'CICS RETRIEVE' to MQ-ERROR-PARA; format RESP codes via STRING into MQ-APPL-RETURN-MESSAGE; PERFORM 9000-ERROR; PERFORM 8000-TERMINATION (fatal, program exits).

**Step 3 — Open queues (1000-CONTROL, lines 161–162)**

- PERFORM 2300-OPEN-INPUT-QUEUE.
- PERFORM 2400-OPEN-OUTPUT-QUEUE.

**Step 4 — Initial GET (1000-CONTROL, line 163)**

- PERFORM 3000-GET-REQUEST: attempt to read the first message before entering the loop.

**Step 5 — Processing loop (1000-CONTROL, lines 164–166)**

- PERFORM 4000-MAIN-PROCESS UNTIL NO-MORE-MSGS.
- Loop terminates when WS-MQ-MSG-FLAG = 'Y'.

**Step 6 — Normal termination (1000-CONTROL, line 167)**

- PERFORM 8000-TERMINATION.

---

### Paragraph: 2100-OPEN-ERROR-QUEUE (lines 238–271)

- Hardcode ERROR-QUEUE-NAME = 'CARD.DEMO.ERROR' (line 243).
- MOVE SPACES to MQOD-OBJECTQMGRNAME (use default queue manager).
- MOVE ERROR-QUEUE-NAME to MQOD-OBJECTNAME.
- COMPUTE MQ-OPTIONS = MQOO-OUTPUT + MQOO-PASS-ALL-CONTEXT + MQOO-FAIL-IF-QUIESCING.
- CALL 'MQOPEN' (arguments: QMGR-HANDLE-CONN, MQ-OBJECT-DESCRIPTOR, MQ-OPTIONS, MQ-HOBJ, MQ-CONDITION-CODE, MQ-REASON-CODE).
- On MQCC-OK: MOVE MQ-HOBJ TO ERROR-QUEUE-HANDLE; SET ERR-QUEUE-OPEN TO TRUE.
- On failure: DISPLAY MQ-ERR-DISPLAY; PERFORM 8000-TERMINATION (no 9000-ERROR here since the error queue is not yet open).

---

### Paragraph: 2300-OPEN-INPUT-QUEUE (lines 171–202)

- MOVE SPACES to MQOD-OBJECTQMGRNAME.
- MOVE INPUT-QUEUE-NAME to MQOD-OBJECTNAME.
- COMPUTE MQ-OPTIONS = MQOO-INPUT-SHARED + MQOO-SAVE-ALL-CONTEXT + MQOO-FAIL-IF-QUIESCING.
- CALL 'MQOPEN'.
- On MQCC-OK: MOVE MQ-HOBJ TO INPUT-QUEUE-HANDLE; SET REPLY-QUEUE-OPEN TO TRUE.
  (Note: the status flag set is REPLY-QUEUE-OPEN, checked in 8000-TERMINATION to decide whether to call 5000-CLOSE-INPUT-QUEUE. Naming is counter-intuitive but consistent with COACCT01.)
- On failure: MOVE INPUT-QUEUE-NAME to MQ-APPL-QUEUE-NAME; MOVE 'INP MQOPEN ERR' to MQ-APPL-RETURN-MESSAGE; PERFORM 9000-ERROR; PERFORM 8000-TERMINATION (fatal).

---

### Paragraph: 2400-OPEN-OUTPUT-QUEUE (lines 204–236)

- MOVE SPACES to MQOD-OBJECTQMGRNAME.
- MOVE REPLY-QUEUE-NAME ('CARD.DEMO.REPLY.DATE') to MQOD-OBJECTNAME.
- COMPUTE MQ-OPTIONS = MQOO-OUTPUT + MQOO-PASS-ALL-CONTEXT + MQOO-FAIL-IF-QUIESCING.
- CALL 'MQOPEN'.
- On MQCC-OK: MOVE MQ-HOBJ TO OUTPUT-QUEUE-HANDLE; SET RESP-QUEUE-OPEN TO TRUE.
- On failure: MOVE REPLY-QUEUE-NAME to MQ-APPL-QUEUE-NAME; MOVE 'OUT MQOPEN ERR' to MQ-APPL-RETURN-MESSAGE; PERFORM 9000-ERROR; PERFORM 8000-TERMINATION (fatal).

---

### Paragraph: 4000-MAIN-PROCESS (lines 274–280)

- EXEC CICS SYNCPOINT END-EXEC: commits the previous unit of work (the MQGET destructive read of the last message and its reply MQPUT).
- PERFORM 3000-GET-REQUEST.

---

### Paragraph: 3000-GET-REQUEST (lines 283–337)

- Set MQGMO-WAITINTERVAL = 5000 (5-second wait timeout).
- MOVE SPACES to MQ-CORRELID, MQ-MSG-ID.
- MOVE INPUT-QUEUE-NAME to MQ-QUEUE; MOVE INPUT-QUEUE-HANDLE to MQ-HOBJ.
- MOVE 1000 to MQ-BUFFER-LENGTH.
- MOVE MQMI-NONE to MQMD-MSGID; MOVE MQCI-NONE to MQMD-CORRELID (accept any message, no filter applied).
- INITIALIZE REQUEST-MSG-COPY REPLACING NUMERIC BY ZEROES.
- COMPUTE MQGMO-OPTIONS = MQGMO-SYNCPOINT + MQGMO-FAIL-IF-QUIESCING + MQGMO-CONVERT + MQGMO-WAIT.
- CALL 'MQGET' (arguments: MQ-HCONN, MQ-HOBJ, MQ-MESSAGE-DESCRIPTOR, MQ-GET-MESSAGE-OPTIONS, MQ-BUFFER-LENGTH, MQ-BUFFER, MQ-DATA-LENGTH, MQ-CONDITION-CODE, MQ-REASON-CODE).
- On MQCC-OK:
  - MOVE MQMD-MSGID to MQ-MSG-ID.
  - MOVE MQMD-CORRELID to MQ-CORRELID.
  - MOVE MQMD-REPLYTOQ to MQ-QUEUE-REPLY.
  - MOVE MQ-BUFFER to REQUEST-MESSAGE.
  - MOVE MQ-CORRELID to SAVE-CORELID; MOVE MQ-QUEUE-REPLY to SAVE-REPLY2Q; MOVE MQ-MSG-ID to SAVE-MSGID.
  - MOVE REQUEST-MESSAGE to REQUEST-MSG-COPY.
  - PERFORM 4000-PROCESS-REQUEST-REPLY.
  - ADD 1 TO MQ-MSG-COUNT.
- If MQRC-NO-MSG-AVAILABLE: SET NO-MORE-MSGS TO TRUE (terminates PERFORM loop in 1000-CONTROL).
- On other error: populate MQ-APPL fields; MOVE 'INP MQGET ERR:' to MQ-APPL-RETURN-MESSAGE; PERFORM 9000-ERROR; PERFORM 8000-TERMINATION (fatal).

---

### Paragraph: 4000-PROCESS-REQUEST-REPLY (lines 339–364)

This paragraph contains the core business logic specific to CODATE01.

- MOVE SPACES to REPLY-MESSAGE.
- INITIALIZE WS-DATE-TIME REPLACING NUMERIC BY ZEROES (clears WS-ABS-TIME, WS-MMDDYYYY, WS-TIME).
- EXEC CICS ASKTIME ABSTIME(WS-ABS-TIME) END-EXEC: retrieves the current CICS absolute time as a packed-decimal value (COMP-3, S9(15)).
- EXEC CICS FORMATTIME:
  - ABSTIME(WS-ABS-TIME): input from ASKTIME.
  - MMDDYYYY(WS-MMDDYYYY): format date as MM-DD-YYYY (10 chars).
  - DATESEP('-'): use hyphen as date separator.
  - TIME(WS-TIME): format time as HH:MM:SS (8 chars).
  - TIMESEP: use default time separator (colon).
- STRING 'SYSTEM DATE : ' WS-MMDDYYYY 'SYSTEM TIME : ' WS-TIME DELIMITED BY SIZE INTO REPLY-MESSAGE END-STRING.
- PERFORM 4100-PUT-REPLY.

There is no request content validation in CODATE01. Any valid inbound MQ message triggers a date/time response, regardless of the content of WS-FUNC or WS-KEY in REQUEST-MSG-COPY. The request message content is parsed into REQUEST-MSG-COPY (same structure as COACCT01) but those fields are never tested in 4000-PROCESS-REQUEST-REPLY.

---

### Paragraph: 4100-PUT-REPLY (lines 366–403)

- MOVE REPLY-MESSAGE to MQ-BUFFER.
- MOVE 1000 to MQ-BUFFER-LENGTH.
- MOVE SAVE-MSGID to MQMD-MSGID (echo back original message ID).
- MOVE SAVE-CORELID to MQMD-CORRELID.
- MOVE MQFMT-STRING to MQMD-FORMAT.
- COMPUTE MQMD-CODEDCHARSETID = MQCCSI-Q-MGR.
- COMPUTE MQPMO-OPTIONS = MQPMO-SYNCPOINT + MQPMO-DEFAULT-CONTEXT + MQPMO-FAIL-IF-QUIESCING.
- CALL 'MQPUT' (arguments: MQ-HCONN, OUTPUT-QUEUE-HANDLE, MQ-MESSAGE-DESCRIPTOR, MQ-PUT-MESSAGE-OPTIONS, MQ-BUFFER-LENGTH, MQ-BUFFER, MQ-CONDITION-CODE, MQ-REASON-CODE).
- On MQCC-OK: record codes in MQ-APPL fields.
- On failure: MOVE REPLY-QUEUE-NAME to MQ-APPL-QUEUE-NAME; MOVE 'MQPUT ERR' to MQ-APPL-RETURN-MESSAGE; PERFORM 9000-ERROR; PERFORM 8000-TERMINATION.

---

### Paragraph: 9000-ERROR (lines 405–441)

- MOVE MQ-ERR-DISPLAY to ERROR-MESSAGE.
- MOVE ERROR-MESSAGE to MQ-BUFFER.
- MOVE 1000 to MQ-BUFFER-LENGTH.
- MOVE MQFMT-STRING to MQMD-FORMAT.
- COMPUTE MQMD-CODEDCHARSETID = MQCCSI-Q-MGR.
- COMPUTE MQPMO-OPTIONS = MQPMO-SYNCPOINT + MQPMO-DEFAULT-CONTEXT + MQPMO-FAIL-IF-QUIESCING.
- CALL 'MQPUT' to ERROR-QUEUE-HANDLE (writes error details to 'CARD.DEMO.ERROR').
- On MQPUT failure: DISPLAY MQ-ERR-DISPLAY; PERFORM 8000-TERMINATION.

---

### Paragraph: 8000-TERMINATION (lines 442–454)

- IF REPLY-QUEUE-OPEN: PERFORM 5000-CLOSE-INPUT-QUEUE.
- IF RESP-QUEUE-OPEN: PERFORM 5100-CLOSE-OUTPUT-QUEUE.
- IF ERR-QUEUE-OPEN: PERFORM 5200-CLOSE-ERROR-QUEUE.
- EXEC CICS RETURN END-EXEC.
- GOBACK.

---

### Paragraphs: 5000, 5100, 5200 — Queue Close Routines (lines 456–524)

Each close paragraph follows the identical pattern:

- MOVE [queue name] to MQ-QUEUE; MOVE [queue handle] to MQ-HOBJ.
- COMPUTE MQ-OPTIONS = MQCO-NONE.
- CALL 'MQCLOSE' (arguments: MQ-HCONN, MQ-HOBJ, MQ-OPTIONS, MQ-CONDITION-CODE, MQ-REASON-CODE).
- On MQCC-OK: record codes.
- On failure: populate MQ-APPL fields; 5200-CLOSE-ERROR-QUEUE calls 9000-ERROR then 8000-TERMINATION; 5000 and 5100 call only 8000-TERMINATION.

| Paragraph             | Closes               | Handle               |
|:----------------------|:---------------------|:---------------------|
| 5000-CLOSE-INPUT-QUEUE  | INPUT-QUEUE-NAME   | INPUT-QUEUE-HANDLE   |
| 5100-CLOSE-OUTPUT-QUEUE | REPLY-QUEUE-NAME   | OUTPUT-QUEUE-HANDLE  |
| 5200-CLOSE-ERROR-QUEUE  | ERROR-QUEUE-NAME   | ERROR-QUEUE-HANDLE   |

---

## 4. Data Structures

### 4.1 Status Flags

| Variable              | PIC    | Initial | 88-Level Condition   | Usage                                       |
|:----------------------|:-------|:--------|:---------------------|:--------------------------------------------|
| WS-MQ-MSG-FLAG        | X(01)  | 'N'     | NO-MORE-MSGS = 'Y'   | Loop termination sentinel                   |
| WS-RESP-QUEUE-STS     | X(01)  | 'N'     | RESP-QUEUE-OPEN = 'Y'| Tracks whether output queue was opened      |
| WS-ERR-QUEUE-STS      | X(01)  | 'N'     | ERR-QUEUE-OPEN = 'Y' | Tracks whether error queue was opened       |
| WS-REPLY-QUEUE-STS    | X(01)  | 'N'     | REPLY-QUEUE-OPEN = 'Y'| Tracks whether input queue was opened      |

Source: CODATE01.cbl, lines 13–23.

---

### 4.2 CICS Response Codes

| Variable            | PIC           | Usage                                |
|:--------------------|:--------------|:-------------------------------------|
| WS-CICS-RESP1-CD    | S9(08) COMP   | RESP parameter for CICS commands     |
| WS-CICS-RESP2-CD    | S9(08) COMP   | RESP2 parameter for CICS commands    |
| WS-CICS-RESP1-CD-D  | 9(08)         | Display-friendly copy of RESP1       |
| WS-CICS-RESP2-CD-D  | 9(08)         | Display-friendly copy of RESP2       |

Source: CODATE01.cbl, lines 26–30.

---

### 4.3 Date/Time Fields (actively used in this program)

| Variable       | PIC           | Usage                                             |
|:---------------|:--------------|:--------------------------------------------------|
| WS-ABS-TIME    | S9(15) COMP-3 | Packed-decimal absolute time from EXEC CICS ASKTIME |
| WS-MMDDYYYY    | X(10)         | Formatted date MM-DD-YYYY from EXEC CICS FORMATTIME |
| WS-TIME        | X(8)          | Formatted time HH:MM:SS from EXEC CICS FORMATTIME   |

Source: CODATE01.cbl, lines 35–38.

These fields are INITIALIZED at the start of 4000-PROCESS-REQUEST-REPLY and then populated by ASKTIME and FORMATTIME before being serialized into the reply.

---

### 4.4 Core MQ Communication Variables

| Variable              | PIC              | Usage                                                      |
|:----------------------|:-----------------|:-----------------------------------------------------------|
| MQ-QUEUE              | X(48)            | Working queue name for current MQOPEN/MQCLOSE              |
| MQ-QUEUE-REPLY        | X(48)            | Reply-to queue name extracted from inbound MQMD            |
| MQ-HCONN              | S9(09) BINARY    | MQ connection handle (set by CICS MQ bridge; initial 0)    |
| MQ-CONDITION-CODE     | S9(09) BINARY    | MQ completion code (MQCC-OK, MQCC-WARNING, MQCC-FAILED)    |
| MQ-REASON-CODE        | S9(09) BINARY    | MQ reason code                                             |
| MQ-HOBJ               | S9(09) BINARY    | Working object handle for current MQOPEN/MQCLOSE           |
| MQ-OPTIONS            | S9(09) BINARY    | Options bitmask for MQOPEN/MQCLOSE                         |
| MQ-BUFFER-LENGTH      | S9(09) BINARY    | Length of MQ-BUFFER passed to MQGET/MQPUT                  |
| MQ-BUFFER             | X(1000)          | Message data buffer                                        |
| MQ-DATA-LENGTH        | S9(09) BINARY    | Actual data length returned by MQGET                       |
| MQ-CORRELID           | X(24)            | Correlation ID from inbound message descriptor             |
| MQ-MSG-ID             | X(24)            | Message ID from inbound message descriptor                 |
| MQ-MSG-COUNT          | 9(09)            | Count of messages processed in this invocation             |
| SAVE-CORELID          | X(24)            | Saved correlation ID for use in MQPUT reply                |
| SAVE-MSGID            | X(24)            | Saved message ID for use in MQPUT reply                    |
| SAVE-REPLY2Q          | X(48)            | Saved REPLYTOQ name (captured but not used for routing)    |

Source: CODATE01.cbl, lines 42–57.

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

Total length: 113 bytes.
Source: CODATE01.cbl, lines 58–68.

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

Source: CODATE01.cbl, lines 71–90. All six are IBM MQ for z/OS-supplied copybooks.
**[UNRESOLVED]** These copybooks are not present in the `app/cpy/` directory. Field-level layouts require the IBM MQ for z/OS copybook library (typically SCSQCOBC or equivalent).

---

### 4.7 Queue Handles and Names

| Variable              | PIC              | Initial | Usage                                             |
|:----------------------|:-----------------|:--------|:--------------------------------------------------|
| QMGR-NAME             | X(48)            | SPACES  | Queue manager name (left blank = default QM)      |
| INPUT-QUEUE-NAME      | X(48)            | SPACES  | Populated from MQTM-QNAME via CICS RETRIEVE       |
| REPLY-QUEUE-NAME      | X(48)            | SPACES  | Hardcoded 'CARD.DEMO.REPLY.DATE'                  |
| ERROR-QUEUE-NAME      | X(48)            | SPACES  | Hardcoded 'CARD.DEMO.ERROR'                       |
| INPUT-QUEUE-HANDLE    | S9(09) BINARY    | 0       | Handle from MQOPEN of input queue                 |
| OUTPUT-QUEUE-HANDLE   | S9(09) BINARY    | 0       | Handle from MQOPEN of reply queue                 |
| ERROR-QUEUE-HANDLE    | S9(09) BINARY    | 0       | Handle from MQOPEN of error queue                 |
| QMGR-HANDLE-CONN      | S9(09) BINARY    | 0       | Connection handle (set by CICS MQ bridge)         |

Source: CODATE01.cbl, lines 92–104.

---

### 4.8 Message Buffers

| Variable          | PIC      | Usage                                                              |
|:------------------|:---------|:-------------------------------------------------------------------|
| QUEUE-MESSAGE     | X(1000)  | General queue message work area                                    |
| REQUEST-MESSAGE   | X(1000)  | Raw inbound message from MQGET                                     |
| REPLY-MESSAGE     | X(1000)  | Outbound reply message sent via MQPUT                              |
| ERROR-MESSAGE     | X(1000)  | Error payload sent to CARD.DEMO.ERROR queue                        |

Source: CODATE01.cbl, lines 105–108.

---

### 4.9 Request Message Parsed Structure

```
01 REQUEST-MSG-COPY.
   10 WS-FUNC    PIC X(04)   -- Function code (parsed but not used in CODATE01)
   10 WS-KEY     PIC 9(11)   -- Key field (parsed but not used in CODATE01)
   10 WS-FILLER  PIC X(985)  -- Unused padding to total 1000 bytes
```

Source: CODATE01.cbl, lines 109–112.

The request message content is received and overlaid into REQUEST-MSG-COPY but neither WS-FUNC nor WS-KEY is evaluated in the business logic. Any message on the input queue triggers a date/time reply unconditionally.

---

### 4.10 Working Variables

| Variable           | PIC          | Initial | Usage                                               |
|:-------------------|:-------------|:--------|:----------------------------------------------------|
| LIT-ACCTFILENAME   | X(8)         | 'ACCTDAT ' | Declared but never used (no VSAM READ in CODATE01)|
| WS-RESP-CD         | S9(09) COMP  | ZEROS   | Declared but never used (no CICS READ in CODATE01) |
| WS-REAS-CD         | S9(09) COMP  | ZEROS   | Declared but never used (no CICS READ in CODATE01) |

Source: CODATE01.cbl, lines 114–120.

These variables are present in the WORKING-STORAGE section of CODATE01 but are entirely unused, indicating that CODATE01 was developed by copying the COACCT01 structure and retaining these declarations. They represent dead storage.

---

## 5. MQ Commands Summary

| Call        | Paragraph                  | Queue               | Handle                | Options                                                                  |
|:------------|:---------------------------|:--------------------|:----------------------|:-------------------------------------------------------------------------|
| MQOPEN      | 2100-OPEN-ERROR-QUEUE      | CARD.DEMO.ERROR     | ERROR-QUEUE-HANDLE    | MQOO-OUTPUT + MQOO-PASS-ALL-CONTEXT + MQOO-FAIL-IF-QUIESCING             |
| MQOPEN      | 2300-OPEN-INPUT-QUEUE      | (from MQTM-QNAME)   | INPUT-QUEUE-HANDLE    | MQOO-INPUT-SHARED + MQOO-SAVE-ALL-CONTEXT + MQOO-FAIL-IF-QUIESCING       |
| MQOPEN      | 2400-OPEN-OUTPUT-QUEUE     | CARD.DEMO.REPLY.DATE| OUTPUT-QUEUE-HANDLE   | MQOO-OUTPUT + MQOO-PASS-ALL-CONTEXT + MQOO-FAIL-IF-QUIESCING             |
| MQGET       | 3000-GET-REQUEST           | INPUT-QUEUE-NAME    | INPUT-QUEUE-HANDLE    | MQGMO-SYNCPOINT + MQGMO-FAIL-IF-QUIESCING + MQGMO-CONVERT + MQGMO-WAIT (5000ms) |
| MQPUT       | 4100-PUT-REPLY             | CARD.DEMO.REPLY.DATE| OUTPUT-QUEUE-HANDLE   | MQPMO-SYNCPOINT + MQPMO-DEFAULT-CONTEXT + MQPMO-FAIL-IF-QUIESCING        |
| MQPUT       | 9000-ERROR                 | CARD.DEMO.ERROR     | ERROR-QUEUE-HANDLE    | MQPMO-SYNCPOINT + MQPMO-DEFAULT-CONTEXT + MQPMO-FAIL-IF-QUIESCING        |
| MQCLOSE     | 5000-CLOSE-INPUT-QUEUE     | INPUT-QUEUE-NAME    | INPUT-QUEUE-HANDLE    | MQCO-NONE                                                                |
| MQCLOSE     | 5100-CLOSE-OUTPUT-QUEUE    | REPLY-QUEUE-NAME    | OUTPUT-QUEUE-HANDLE   | MQCO-NONE                                                                |
| MQCLOSE     | 5200-CLOSE-ERROR-QUEUE     | ERROR-QUEUE-NAME    | ERROR-QUEUE-HANDLE    | MQCO-NONE                                                                |

### Important MQ Design Notes

1. **Syncpoint scope**: Both MQGET and MQPUT execute under MQGMO-SYNCPOINT / MQPMO-SYNCPOINT. The EXEC CICS SYNCPOINT in 4000-MAIN-PROCESS commits the previous unit of work before each new message is fetched.

2. **Message correlation**: SAVE-MSGID and SAVE-CORELID are copied from MQMD at MQGET time and placed back into MQMD at MQPUT time. The requesting application uses these identifiers to match the date/time reply to its original request.

3. **Reply queue hardcoded**: Despite capturing MQMD-REPLYTOQ into SAVE-REPLY2Q, the MQPUT always targets OUTPUT-QUEUE-HANDLE, which was opened against the hardcoded 'CARD.DEMO.REPLY.DATE' queue.

4. **No content-based routing**: Unlike COACCT01, CODATE01 does not inspect WS-FUNC or WS-KEY. Every successfully received MQ message results in a date/time reply unconditionally.

5. **MQHCONN**: QMGR-HANDLE-CONN is declared with VALUE 0. In the CICS-MQ bridge model, the CICS transaction is started with an established MQ connection; the program uses this implicit handle without calling MQCONN.

---

## 6. VSAM File Access

CODATE01 performs **no VSAM file access**. The LIT-ACCTFILENAME variable (VALUE 'ACCTDAT ') and WS-RESP-CD/WS-REAS-CD are present in WORKING-STORAGE (inherited from COACCT01's structure) but are never referenced in the PROCEDURE DIVISION of CODATE01.

---

## 7. CICS Commands

| Command         | Paragraph                     | Purpose                                             |
|:----------------|:------------------------------|:----------------------------------------------------|
| EXEC CICS RETRIEVE | 1000-CONTROL               | Read MQ trigger message (MQTM structure)            |
| EXEC CICS SYNCPOINT | 4000-MAIN-PROCESS          | Commit current unit of work between messages        |
| EXEC CICS ASKTIME  | 4000-PROCESS-REQUEST-REPLY  | Obtain current system absolute time                 |
| EXEC CICS FORMATTIME | 4000-PROCESS-REQUEST-REPLY| Format absolute time into date (MMDDYYYY) and time  |
| EXEC CICS RETURN   | 8000-TERMINATION            | Return control to CICS                              |

### ASKTIME / FORMATTIME Detail

```
EXEC CICS ASKTIME
     ABSTIME(WS-ABS-TIME)         -- PIC S9(15) COMP-3
END-EXEC

EXEC CICS FORMATTIME
     ABSTIME(WS-ABS-TIME)
     MMDDYYYY(WS-MMDDYYYY)        -- produces MM-DD-YYYY (10 chars)
     DATESEP('-')                  -- hyphen separator
     TIME(WS-TIME)                 -- produces HH:MM:SS (8 chars)
     TIMESEP                       -- default separator (colon)
END-EXEC
```

Source: CODATE01.cbl, lines 343–353.

---

## 8. Called Programs and External Interfaces

| Type             | Target          | Paragraph             | Method               | Purpose                        |
|:-----------------|:----------------|:----------------------|:---------------------|:-------------------------------|
| MQ API           | MQOPEN          | 2100, 2300, 2400      | CALL 'MQOPEN'        | Open queues                    |
| MQ API           | MQGET           | 3000-GET-REQUEST      | CALL 'MQGET'         | Retrieve messages               |
| MQ API           | MQPUT           | 4100-PUT-REPLY        | CALL 'MQPUT'         | Send date/time reply            |
| MQ API           | MQPUT           | 9000-ERROR            | CALL 'MQPUT'         | Send error to error queue      |
| MQ API           | MQCLOSE         | 5000, 5100, 5200      | CALL 'MQCLOSE'       | Close queues                   |
| CICS command     | RETRIEVE        | 1000-CONTROL          | EXEC CICS RETRIEVE   | Get trigger message data       |
| CICS command     | SYNCPOINT       | 4000-MAIN-PROCESS     | EXEC CICS SYNCPOINT  | Commit current UOW             |
| CICS command     | ASKTIME         | 4000-PROCESS-REQUEST-REPLY | EXEC CICS ASKTIME | Get system absolute time     |
| CICS command     | FORMATTIME      | 4000-PROCESS-REQUEST-REPLY | EXEC CICS FORMATTIME | Format date and time        |
| CICS command     | RETURN          | 8000-TERMINATION      | EXEC CICS RETURN     | Return control to CICS         |

No static or dynamic CICS LINK, XCTL, or program-to-program CALL other than the MQ API calls listed above. No VSAM file I/O.

---

## 9. Error Handling

### Error Taxonomy

| Error Condition             | Detection Point          | Action                                           | Fatal? |
|:----------------------------|:-------------------------|:-------------------------------------------------|:-------|
| CICS RETRIEVE failure       | 1000-CONTROL             | Log to MQ-ERR-DISPLAY; 9000-ERROR; 8000-TERMINATION | Yes |
| MQOPEN failure (error queue)| 2100-OPEN-ERROR-QUEUE    | DISPLAY MQ-ERR-DISPLAY; 8000-TERMINATION         | Yes    |
| MQOPEN failure (input queue)| 2300-OPEN-INPUT-QUEUE    | 9000-ERROR; 8000-TERMINATION                     | Yes    |
| MQOPEN failure (output queue)| 2400-OPEN-OUTPUT-QUEUE  | 9000-ERROR; 8000-TERMINATION                     | Yes    |
| MQGET failure (no message)  | 3000-GET-REQUEST         | SET NO-MORE-MSGS TO TRUE; graceful termination   | No     |
| MQGET failure (other)       | 3000-GET-REQUEST         | 9000-ERROR; 8000-TERMINATION                     | Yes    |
| MQPUT failure (reply)       | 4100-PUT-REPLY           | 9000-ERROR; 8000-TERMINATION                     | Yes    |
| MQPUT failure (error queue) | 9000-ERROR               | DISPLAY MQ-ERR-DISPLAY; 8000-TERMINATION         | Yes    |
| MQCLOSE failure (input)     | 5000-CLOSE-INPUT-QUEUE   | 8000-TERMINATION                                 | Yes    |
| MQCLOSE failure (output)    | 5100-CLOSE-OUTPUT-QUEUE  | 8000-TERMINATION                                 | Yes    |
| MQCLOSE failure (error)     | 5200-CLOSE-ERROR-QUEUE   | 9000-ERROR; 8000-TERMINATION                     | Yes    |

Note: CODATE01 has fewer error conditions than COACCT01 because there is no VSAM I/O and no request validation. CICS ASKTIME and FORMATTIME do not have application-level error handling in this program (no RESP/RESP2 checked for those commands).

### Error Message Format

When 9000-ERROR is called, the full MQ-ERR-DISPLAY record (113 bytes) is written to 'CARD.DEMO.ERROR'. The record contains: paragraph name, error description text, MQ condition code, MQ reason code, and queue name.

### CICS Transaction Backout

The CSD defines ACTION(BACKOUT) for transaction CDRD. On abnormal termination, CICS backs out syncpoint-protected MQ operations: the input message is requeued and any partial reply is removed from the output queue.

---

## 10. Business Rules

1. **No request validation**: CODATE01 does not inspect WS-FUNC or WS-KEY from the request message. Any message arriving on the input queue generates a date/time reply. This contrasts with COACCT01, which validates WS-FUNC = 'INQA' and WS-KEY > ZEROES.

2. **Date format**: The date is formatted as MM-DD-YYYY (MMDDYYYY option with DATESEP('-')), yielding a 10-character string. The time is formatted as HH:MM:SS (TIME with TIMESEP), yielding an 8-character string.

3. **System time source**: The date and time reflect the CICS region's system clock at the moment 4000-PROCESS-REQUEST-REPLY executes for each message. Each message in the same invocation of the program may receive a slightly different timestamp.

4. **Reply always succeeds unless MQ fails**: Because there is no VSAM read and no request content validation, the only conditions that prevent a reply from being placed on the reply queue are MQ infrastructure failures.

5. **Dead storage in WORKING-STORAGE**: LIT-ACCTFILENAME, WS-RESP-CD, and WS-REAS-CD are declared but serve no function in this program. They are residual artifacts from the COACCT01 template.

6. **Message counting**: MQ-MSG-COUNT accumulates the count of messages processed but is not persisted or reported.

7. **Queue name sourcing**: Input queue dynamically sourced from MQTM-QNAME. Output queue hardcoded to 'CARD.DEMO.REPLY.DATE'. Error queue hardcoded to 'CARD.DEMO.ERROR'.

---

## 11. Inputs and Outputs

### Inputs

| Source               | Variable / Structure      | Description                                    |
|:---------------------|:--------------------------|:-----------------------------------------------|
| MQ trigger message   | MQTM (via CICS RETRIEVE)  | Contains MQTM-QNAME identifying input queue    |
| MQ input queue       | REQUEST-MESSAGE / REQUEST-MSG-COPY | Inbound date request message (content not validated) |
| CICS clock           | WS-ABS-TIME               | System absolute time from EXEC CICS ASKTIME    |

### Input Message Layout (REQUEST-MSG-COPY)

| Field      | PIC     | Offset | Notes                                   |
|:-----------|:--------|:-------|:----------------------------------------|
| WS-FUNC    | X(04)   | 1      | Not inspected; any value accepted       |
| WS-KEY     | 9(11)   | 5      | Not inspected; any value accepted       |
| WS-FILLER  | X(985)  | 16     | Unused                                  |

### Outputs

| Destination          | Variable         | Description                                         |
|:---------------------|:-----------------|:----------------------------------------------------|
| MQ reply queue       | REPLY-MESSAGE    | System date and time formatted as labeled text string|
| MQ error queue       | ERROR-MESSAGE    | MQ-ERR-DISPLAY content on processing failure        |

### Reply Message Content

The reply is a STRING-assembled character value placed into REPLY-MESSAGE (X(1000)):

```
'SYSTEM DATE : MM-DD-YYYY SYSTEM TIME : HH:MM:SS'
```

Exactly: the literal 'SYSTEM DATE : ' (14 chars) + WS-MMDDYYYY (10 chars) + 'SYSTEM TIME : ' (14 chars) + WS-TIME (8 chars) = 46 chars of significant content; remainder of the 1000-byte buffer is SPACES.

Source: CODATE01.cbl, lines 355–360.

---

## 12. Key Variables and Their Purpose

| Variable                  | Purpose                                                                          |
|:--------------------------|:---------------------------------------------------------------------------------|
| WS-ABS-TIME               | Receives packed-decimal absolute time from EXEC CICS ASKTIME; input to FORMATTIME|
| WS-MMDDYYYY               | Date formatted as MM-DD-YYYY by EXEC CICS FORMATTIME; included in reply message  |
| WS-TIME                   | Time formatted as HH:MM:SS by EXEC CICS FORMATTIME; included in reply message    |
| INPUT-QUEUE-NAME          | MQ queue name for reading requests; dynamically sourced from MQTM-QNAME          |
| REPLY-QUEUE-NAME          | Fixed output queue 'CARD.DEMO.REPLY.DATE'; receives all date/time reply messages  |
| ERROR-QUEUE-NAME          | Fixed error queue 'CARD.DEMO.ERROR'; receives error diagnostic messages           |
| WS-MQ-MSG-FLAG / NO-MORE-MSGS | Controls main processing loop; set when MQRC-NO-MSG-AVAILABLE received        |
| SAVE-MSGID / SAVE-CORELID | Preserve MQMD identifiers for echoing back in reply, enabling message correlation |
| QMGR-HANDLE-CONN          | MQ connection handle; initialized to 0, used as-is (supplied by CICS MQ bridge)  |
| MQ-ERR-DISPLAY            | Composite error record; written to CARD.DEMO.ERROR on any fatal error             |
| LIT-ACCTFILENAME          | Declared but unused (dead storage; artifact of COACCT01 template)                |
| WS-RESP-CD / WS-REAS-CD   | Declared but unused (dead storage; artifact of COACCT01 template)                |

---

## 13. Comparison with COACCT01

| Aspect                    | COACCT01                                    | CODATE01                                      |
|:--------------------------|:--------------------------------------------|:----------------------------------------------|
| Transaction ID            | CDRA                                        | CDRD                                          |
| Reply queue               | CARD.DEMO.REPLY.ACCT                        | CARD.DEMO.REPLY.DATE                          |
| Request validation        | Validates WS-FUNC='INQA' and WS-KEY>0       | None — any message triggers a reply           |
| VSAM access               | EXEC CICS READ DATASET(ACCTDAT)             | None                                          |
| CICS time commands        | Not used (INITIALIZE only)                  | ASKTIME + FORMATTIME                          |
| Reply content             | Account fields with labels                  | System date + time with labels                |
| Dead storage              | None                                        | LIT-ACCTFILENAME, WS-RESP-CD, WS-REAS-CD      |
| WS-ACCT-RESPONSE          | Defined and used                            | Not present                                   |
| CVACT01Y COPY             | Yes (line 171)                              | No                                            |
| Shared structure          | 1000-CONTROL through 5200 paragraphs identical in structure to CODATE01 | Same |
| Error handling depth      | 3-tier (NOTFND reply, 9000-ERROR, 8000-TERMINATION) | 2-tier (9000-ERROR, 8000-TERMINATION)   |
