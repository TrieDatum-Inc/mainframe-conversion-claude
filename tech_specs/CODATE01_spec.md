# Technical Specification: CODATE01

## 1. Executive Summary

CODATE01 is a **CICS MQ-triggered COBOL program** in the VSAM-MQ subsystem of the CardDemo application. It acts as a **date and time lookup service**: it listens on an IBM MQ input queue for any request message, retrieves the current system date and time via `EXEC CICS ASKTIME` / `EXEC CICS FORMATTIME`, and returns a formatted date-and-time string to a reply queue. Unlike COACCT01 (which has specific input parameters), CODATE01 returns the same system date/time for any request received — the request content is irrelevant. The program shares the same MQ infrastructure pattern as COACCT01: CICS RETRIEVE to obtain queue name, MQOPEN/MQGET/MQPUT/MQCLOSE for queue operations, and a message processing loop. The reply queue name is hardcoded as `CARD.DEMO.REPLY.DATE`.

---

## 2. Artifact Inventory

| Artifact | Type | Location |
|---|---|---|
| CODATE01.cbl | CICS online COBOL program (MQ-triggered) | `app/app-vsam-mq/cbl/CODATE01.cbl` |
| CMQGMOV | IBM MQ GET message options structure | IBM MQ-supplied |
| CMQPMOV | IBM MQ PUT message options structure | IBM MQ-supplied |
| CMQMDV | IBM MQ message descriptor structure | IBM MQ-supplied |
| CMQODV | IBM MQ object descriptor structure | IBM MQ-supplied |
| CMQV | IBM MQ constants | IBM MQ-supplied |
| CMQTML | IBM MQ trigger message layout | IBM MQ-supplied |

> CODATE01 does not include CVACT01Y or any VSAM record layout. It has no VSAM file access.

---

## 3. Program Identity

| Attribute | Value | Source |
|---|---|---|
| Program-ID | CODATE01 IS INITIAL | Line 2 |
| Author | AWS | Line 3 |
| Date Written | 03/21 | Line 4 |
| Invocation | CICS MQ-triggered (EXEC CICS RETRIEVE) | Lines 140-159 |
| Reply queue | CARD.DEMO.REPLY.DATE | Line 147 (hardcoded) |
| Error queue | CARD.DEMO.ERROR | Line 243 (hardcoded) |

---

## 4. Differences from COACCT01

CODATE01 is structurally near-identical to COACCT01. The key differences are:

| Aspect | COACCT01 | CODATE01 |
|---|---|---|
| Reply queue | CARD.DEMO.REPLY.ACCT | CARD.DEMO.REPLY.DATE |
| Processing | VSAM READ from ACCTDAT, key-based | CICS ASKTIME / FORMATTIME — no VSAM |
| Input validation | WS-FUNC = 'INQA' AND WS-KEY > 0 | None — any message triggers date/time response |
| CVACT01Y copybook | Included | Not included |
| Response content | Account record fields | Formatted system date and time string |
| WS-VARIABLES | Includes LIT-ACCTFILENAME, WS-CARD-RID-* | Does not include these fields |

---

## 5. MQ Infrastructure (Identical to COACCT01)

### 5.1 Queue Names

| Queue Name | Role | Set At |
|---|---|---|
| (from RETRIEVE MQTM-QNAME) | Input queue | Line 146 |
| CARD.DEMO.REPLY.DATE | Reply queue | Line 147 (hardcoded) |
| CARD.DEMO.ERROR | Error queue | Line 243 (hardcoded) |

### 5.2 MQ Working Storage Fields

Identical to COACCT01 (same MQ-HCONN, MQ-HOBJ, MQ-BUFFER, MQ-CONDITION-CODE, MQ-REASON-CODE, etc.). See COACCT01 spec section 4.2 for the complete field inventory.

### 5.3 MQ Copybooks

Identical to COACCT01 (CMQGMOV, CMQPMOV, CMQMDV, CMQODV, CMQV, CMQTML).

---

## 6. Request Message Format

CODATE01 does not parse the request message content. Any message arriving on the input queue triggers a date/time response. The REQUEST-MSG-COPY structure (lines 109-112) is defined identically to COACCT01 but its fields (WS-FUNC, WS-KEY, WS-FILLER) are not read in `4000-PROCESS-REQUEST-REPLY`.

---

## 7. Response Message Format

The reply message is constructed in paragraph `4000-PROCESS-REQUEST-REPLY` (lines 339-364) using a STRING statement:

```cobol
STRING 'SYSTEM DATE : ' WS-MMDDYYYY
       'SYSTEM TIME : ' WS-TIME
       DELIMITED BY SIZE
       INTO REPLY-MESSAGE
END-STRING
```

| Component | Format | Source |
|---|---|---|
| 'SYSTEM DATE : ' | Literal (14 chars) | Hardcoded |
| WS-MMDDYYYY | PIC X(10), format MM-DD-YYYY | From EXEC CICS FORMATTIME with DATESEP('-') |
| 'SYSTEM TIME : ' | Literal (14 chars) | Hardcoded |
| WS-TIME | PIC X(8), format HH:MM:SS | From EXEC CICS FORMATTIME with TIMESEP |

Example response: `SYSTEM DATE : 04-02-2026SYSTEM TIME : 14:35:22`

Total placed in REPLY-MESSAGE (PIC X(1000)), then into MQ-BUFFER.

---

## 8. CICS Commands

| Command | Paragraph | Purpose |
|---|---|---|
| `EXEC CICS RETRIEVE INTO(MQTM) RESP(...) RESP2(...)` | `1000-CONTROL` (lines 140-159) | Retrieve MQ trigger message; obtain input queue name |
| `EXEC CICS ASKTIME ABSTIME(WS-ABS-TIME)` | `4000-PROCESS-REQUEST-REPLY` (line 343) | Obtain current absolute time |
| `EXEC CICS FORMATTIME ABSTIME(WS-ABS-TIME) MMDDYYYY(WS-MMDDYYYY) DATESEP('-') TIME(WS-TIME) TIMESEP` | `4000-PROCESS-REQUEST-REPLY` (lines 347-353) | Format absolute time into readable date and time strings |
| `EXEC CICS SYNCPOINT` | `4000-MAIN-PROCESS` (lines 275-277) | Commit after each message cycle |
| `EXEC CICS RETURN` | `8000-TERMINATION` (line 453) | Return to CICS after queue is drained |

---

## 9. MQ Operations

Identical in structure to COACCT01. All MQ API calls use the same parameters:

| Operation | Paragraph | MQ API Call |
|---|---|---|
| Open error queue | `2100-OPEN-ERROR-QUEUE` | `CALL 'MQOPEN'` with MQOO-OUTPUT |
| Open input queue | `2300-OPEN-INPUT-QUEUE` | `CALL 'MQOPEN'` with MQOO-INPUT-SHARED + MQOO-SAVE-ALL-CONTEXT |
| Open reply queue | `2400-OPEN-OUTPUT-QUEUE` | `CALL 'MQOPEN'` with MQOO-OUTPUT + MQOO-PASS-ALL-CONTEXT |
| Get message | `3000-GET-REQUEST` | `CALL 'MQGET'` with MQGMO-SYNCPOINT + MQGMO-WAIT (5000ms) |
| Put reply | `4100-PUT-REPLY` | `CALL 'MQPUT'` with MQPMO-SYNCPOINT |
| Put error | `9000-ERROR` | `CALL 'MQPUT'` to ERROR-QUEUE-HANDLE |
| Close input queue | `5000-CLOSE-INPUT-QUEUE` | `CALL 'MQCLOSE'` with MQCO-NONE |
| Close reply queue | `5100-CLOSE-OUTPUT-QUEUE` | `CALL 'MQCLOSE'` with MQCO-NONE |
| Close error queue | `5200-CLOSE-ERROR-QUEUE` | `CALL 'MQCLOSE'` with MQCO-NONE |

---

## 10. VSAM File Operations

None. CODATE01 does not access any VSAM files.

---

## 11. DB2 SQL Statements

None.

---

## 12. BMS Screen / CICS Map Operations

None. This is a headless service program.

---

## 13. PROCEDURE DIVISION — Paragraph-by-Paragraph Logic

### Control Flow

```
1000-CONTROL (entry point)
     |
     +---> PERFORM 2100-OPEN-ERROR-QUEUE
     |
     +---> EXEC CICS RETRIEVE INTO(MQTM)
     |         If OK: INPUT-QUEUE-NAME = MQTM-QNAME
     |                REPLY-QUEUE-NAME = 'CARD.DEMO.REPLY.DATE'
     |         Else:  PERFORM 9000-ERROR, PERFORM 8000-TERMINATION
     |
     +---> PERFORM 2300-OPEN-INPUT-QUEUE
     +---> PERFORM 2400-OPEN-OUTPUT-QUEUE
     |
     +---> PERFORM 3000-GET-REQUEST  (prime read)
     |
     +---> PERFORM 4000-MAIN-PROCESS UNTIL NO-MORE-MSGS
     |           |
     |           +---> EXEC CICS SYNCPOINT
     |           +---> PERFORM 3000-GET-REQUEST
     |                     |
     |                     +---> MQGET with 5-second wait
     |                     +---> If OK: PERFORM 4000-PROCESS-REQUEST-REPLY
     |                     +---> If MQRC-NO-MSG-AVAILABLE: SET NO-MORE-MSGS
     |                     +---> If other error: 9000-ERROR, 8000-TERMINATION
     |
     +---> PERFORM 8000-TERMINATION
```

**4000-PROCESS-REQUEST-REPLY** (lines 339-364):
1. MOVE SPACES TO REPLY-MESSAGE
2. INITIALIZE WS-DATE-TIME REPLACING NUMERIC BY ZEROES
3. `EXEC CICS ASKTIME ABSTIME(WS-ABS-TIME)` — get absolute time
4. `EXEC CICS FORMATTIME ABSTIME(WS-ABS-TIME) MMDDYYYY(WS-MMDDYYYY) DATESEP('-') TIME(WS-TIME) TIMESEP`
5. STRING 'SYSTEM DATE : ' WS-MMDDYYYY 'SYSTEM TIME : ' WS-TIME DELIMITED BY SIZE INTO REPLY-MESSAGE
6. PERFORM 4100-PUT-REPLY

> Note: No validation of the incoming request message. Every message received results in a date/time reply regardless of content.

---

## 14. Date and Time Variables

| Field | PIC | Description |
|---|---|---|
| WS-ABS-TIME | PIC S9(15) COMP-3 | Absolute time in microseconds (CICS internal format) |
| WS-MMDDYYYY | PIC X(10) | Formatted date — MM-DD-YYYY (DATESEP='-') |
| WS-TIME | PIC X(8) | Formatted time — HH:MM:SS (TIMESEP=default colon) |

---

## 15. Error Handling

| Condition | Action |
|---|---|
| CICS RETRIEVE fails | PERFORM 9000-ERROR (put to error queue), PERFORM 8000-TERMINATION |
| MQOPEN (input) fails | PERFORM 9000-ERROR, PERFORM 8000-TERMINATION |
| MQOPEN (output) fails | PERFORM 9000-ERROR, PERFORM 8000-TERMINATION |
| MQOPEN (error queue) fails | DISPLAY MQ-ERR-DISPLAY, PERFORM 8000-TERMINATION |
| MQGET fails (non-empty-queue) | PERFORM 9000-ERROR, PERFORM 8000-TERMINATION |
| MQPUT (reply) fails | PERFORM 9000-ERROR, PERFORM 8000-TERMINATION |
| MQPUT (error queue) fails | DISPLAY MQ-ERR-DISPLAY, PERFORM 8000-TERMINATION |
| MQCLOSE fails | PERFORM 8000-TERMINATION |

CICS ASKTIME and FORMATTIME do not have explicit error handling; CICS RESP codes are not checked for these commands. This is low risk as these commands rarely fail in a healthy CICS environment.

---

## 16. Queue-Opened Status Flags

Same as COACCT01. See COACCT01 spec section 14. The same naming inconsistency exists: `REPLY-QUEUE-OPEN` is SET in `2300-OPEN-INPUT-QUEUE` but the flag name suggests it tracks the reply/output queue.

---

## 17. Inter-Program Interactions

| Component | Mechanism | Purpose |
|---|---|---|
| CICS MQ Bridge | EXEC CICS RETRIEVE | Provides triggering queue name (MQTM-QNAME) |
| IBM MQ (MQOPEN/MQGET/MQPUT/MQCLOSE) | Native MQ API CALL | Queue management and message exchange |
| CARD.DEMO.REPLY.DATE queue | MQPUT | Sends date/time replies |
| CARD.DEMO.ERROR queue | MQPUT | Sends error details |

No VSAM file access. No DB2 access. No calls to other application programs.

---

## 18. Copybooks Referenced

| Copybook | Location | Purpose |
|---|---|---|
| CMQGMOV | Line 71 | MQ GET message options |
| CMQPMOV | Line 75 | MQ PUT message options |
| CMQMDV | Line 79 | MQ message descriptor |
| CMQODV | Line 83 | MQ object descriptor |
| CMQV | Line 87 | MQ constants |
| CMQTML | Line 90 | MQ trigger message layout (MQTM-QNAME) |

---

## 19. Comparison to COACCT01 — Structural Similarities

The table below captures the identical paragraphs shared between CODATE01 and COACCT01:

| Paragraph | Both Programs |
|---|---|
| 1000-CONTROL | Identical except REPLY-QUEUE-NAME literal |
| 2100-OPEN-ERROR-QUEUE | Identical |
| 2300-OPEN-INPUT-QUEUE | Identical |
| 2400-OPEN-OUTPUT-QUEUE | Identical |
| 3000-GET-REQUEST | Identical |
| 4000-MAIN-PROCESS | Identical |
| 4100-PUT-REPLY | Identical |
| 9000-ERROR | Identical |
| 8000-TERMINATION | Identical |
| 5000-CLOSE-INPUT-QUEUE | Identical |
| 5100-CLOSE-OUTPUT-QUEUE | Identical |
| 5200-CLOSE-ERROR-QUEUE | Identical |

Only `4000-PROCESS-REQUEST-REPLY` differs: COACCT01 does VSAM READ; CODATE01 does CICS ASKTIME/FORMATTIME.

This pattern strongly suggests the two programs were created from a common template. In a modernization context, they could share a common service framework with pluggable processing logic.

---

## 20. Open Questions and Gaps

1. **Request message ignored**: CODATE01 does not validate or inspect the request message in any way. Any 1000-byte message (including empty ones) triggers a date/time response. This may be intentional (the service is a pure "what time is it?" service) or may be an oversight.

2. **No CICS transaction defined in provided artifacts**: The CICS transaction ID that triggers CODATE01 is not available in the analyzed source artifacts. It would be in CICS CSD definitions.

3. **Date format uses separator '-'**: `DATESEP('-')` produces MM-DD-YYYY format. Consumers of this service must handle the hyphen separator explicitly.

4. **No error reply for FORMATTIME failure**: If CICS FORMATTIME were to fail (non-standard condition), the program would put a spaces-filled REPLY-MESSAGE to the reply queue rather than an error indicator. This is a minor gap in error coverage.
