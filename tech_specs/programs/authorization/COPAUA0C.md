# Technical Specification: COPAUA0C
## Card Authorization Decision Program

---

### 1. Program Overview

| Attribute       | Value                                      |
|-----------------|--------------------------------------------|
| Program Name    | COPAUA0C                                   |
| Source File     | cbl/COPAUA0C.cbl                           |
| Program Type    | CICS COBOL — IMS + MQ                     |
| Function        | Card Authorization Decision Program        |
| Transaction ID  | CP00                                       |
| Author          | SOUMA GHOSH                                |
| PSB Used        | PSBPAUTB                                   |
| IMS PCB         | PAUT-PCB-NUM = 1 (DBPAUTP0, PROCOPT=AP)   |
| MQ Request Queue | AWS.M2.CARDDEMO.PAUTH.REQUEST             |
| MQ Reply Queue  | Extracted from MQMD-REPLYTOQ at runtime    |

**Purpose:** COPAUA0C is the MQ trigger-driven authorization engine for the CardDemo system. It is invoked by the CICS MQ trigger mechanism when messages arrive on the request queue. It reads batches of authorization request messages (up to 500 per invocation), performs card and account lookups via VSAM, applies business rules to approve or decline each transaction, sends responses on the MQ reply queue, and persists authorization records to the IMS database.

---

### 2. Program Flow

```
MAIN-PARA
  |
  +-- 1000-INITIALIZE
  |     +-- EXEC CICS RETRIEVE (extract trigger data / queue name from MQTM)
  |     +-- 1100-OPEN-REQUEST-QUEUE  (CALL 'MQOPEN' MQOO-INPUT-SHARED)
  |     +-- 3100-READ-REQUEST-MQ     (first message read)
  |
  +-- 2000-MAIN-PROCESS  [UNTIL NO-MORE-MSG-AVAILABLE OR WS-LOOP-END]
  |     +-- 2100-EXTRACT-REQUEST-MSG  (UNSTRING CSV from MQ buffer)
  |     +-- 5000-PROCESS-AUTH
  |     |     +-- 1200-SCHEDULE-PSB   (EXEC DLI SCHD PSB(PSBPAUTB))
  |     |     +-- 5100-READ-XREF-RECORD   (CICS READ CCXREF  by card#)
  |     |     +-- 5200-READ-ACCT-RECORD   (CICS READ ACCTDAT by acct-id)
  |     |     +-- 5300-READ-CUST-RECORD   (CICS READ CUSTDAT by cust-id)
  |     |     +-- 5500-READ-AUTH-SUMMRY   (EXEC DLI GU PAUTSUM0)
  |     |     +-- 5600-READ-PROFILE-DATA  (CONTINUE -- placeholder)
  |     |     +-- 6000-MAKE-DECISION      (approve/decline logic)
  |     |     +-- 7100-SEND-RESPONSE      (CALL 'MQPUT1' reply)
  |     |     +-- 8000-WRITE-AUTH-TO-DB
  |     |           +-- 8400-UPDATE-SUMMARY  (IMS REPL or ISRT PAUTSUM0)
  |     |           +-- 8500-INSERT-AUTH     (IMS ISRT PAUTDTL1)
  |     +-- EXEC CICS SYNCPOINT
  |     +-- SET IMS-PSB-NOT-SCHD TO TRUE
  |     +-- ADD 1 TO WS-MSG-PROCESSED
  |     +-- [if < 500] 3100-READ-REQUEST-MQ (next message)
  |     +-- [if >= 500] SET WS-LOOP-END
  |
  +-- 9000-TERMINATE
  |     +-- EXEC DLI TERM  (if PSB still scheduled)
  |     +-- 9100-CLOSE-REQUEST-QUEUE  (CALL 'MQCLOSE')
  |
  +-- EXEC CICS RETURN
```

**Key Processing Limits:**
- `WS-REQSTS-PROCESS-LIMIT` is hardcoded to `500` (COPAUA0C.cbl, line 41). The program terminates the processing loop after 500 messages per CICS task invocation.
- MQ wait interval is `5000` milliseconds (line 242).

---

### 3. Data Structures

#### 3.1 Working Storage Key Fields (cbl/COPAUA0C.cbl, lines 32–210)

| Field                      | Picture              | Initial Value | Description                          |
|----------------------------|----------------------|---------------|--------------------------------------|
| WS-PGM-AUTH                | PIC X(08)            | 'COPAUA0C'    | This program name                    |
| WS-CICS-TRANID             | PIC X(04)            | 'CP00'        | CICS transaction ID                  |
| WS-ACCTFILENAME            | PIC X(8)             | 'ACCTDAT '    | VSAM account dataset name            |
| WS-CUSTFILENAME            | PIC X(8)             | 'CUSTDAT '    | VSAM customer dataset name           |
| WS-CARDFILENAME            | PIC X(8)             | 'CARDDAT '    | VSAM card dataset name               |
| WS-CARDFILENAME-ACCT-PATH  | PIC X(8)             | 'CARDAIX '    | Card alternate index dataset name    |
| WS-CCXREF-FILE             | PIC X(08)            | 'CCXREF  '    | Card cross-reference dataset name    |
| WS-REQSTS-PROCESS-LIMIT    | PIC S9(4) COMP       | 500           | Max messages per CICS task           |
| WS-MSG-PROCESSED           | PIC S9(4) COMP       | 0             | Count of messages processed          |
| WS-REQUEST-QNAME           | PIC X(48)            |               | MQ request queue name (from trigger) |
| WS-REPLY-QNAME             | PIC X(48)            |               | MQ reply queue name (from MQMD)      |
| WS-SAVE-CORRELID           | PIC X(24)            |               | Saved MQ correlation ID              |
| WS-WAIT-INTERVAL           | PIC S9(9) BINARY     | 5000          | MQ GET wait interval (ms)            |
| WS-AVAILABLE-AMT           | PIC S9(09)V99 COMP-3 |               | Computed available credit            |
| WS-TRANSACTION-AMT         | PIC S9(10)V99        |               | Parsed transaction amount            |
| WS-APPROVED-AMT            | PIC S9(10)V99        |               | Amount approved                      |

#### 3.2 MQ Data Structures (cbl/COPAUA0C.cbl, lines 148–171)

Four MQ structures are instantiated via IBM-provided copybooks:

| 01-Level Name          | Copybook   | Purpose                                    |
|------------------------|------------|--------------------------------------------|
| MQM-OD-REQUEST         | CMQODV     | Object descriptor for request queue MQOPEN |
| MQM-MD-REQUEST         | CMQMDV     | Message descriptor for MQGET               |
| MQM-OD-REPLY           | CMQODV     | Object descriptor for reply queue MQPUT1   |
| MQM-MD-REPLY           | CMQMDV     | Message descriptor for MQPUT1              |
| MQM-CONSTANTS          | CMQV       | MQ named constants                         |
| MQM-TRIGGER-DATA       | CMQTML     | Trigger message layout (MQTM)              |
| MQM-PUT-MESSAGE-OPTIONS| CMQPMOV    | MQPMO structure                            |
| MQM-GET-MESSAGE-OPTIONS| CMQGMOV    | MQGMO structure                            |

MQ handle variables:
- `W01-HCONN-REQUEST` / `W01-HOBJ-REQUEST` — request queue connection and object handles
- `W01-GET-BUFFER` PIC X(500) — receive buffer (500 bytes)
- `W02-HCONN-REPLY` / `W02-PUT-BUFFER` PIC X(200) — reply connection and buffer

#### 3.3 Switch / Flag Fields (lines 110–145)

| Field                     | Values                  | Meaning                                |
|---------------------------|-------------------------|----------------------------------------|
| WS-AUTH-RESP-FLG          | 'A' (APPROVED) / 'D' (DECLINED) | Final auth decision        |
| WS-MSG-LOOP-FLG           | 'E' (LOOP-END)          | Terminate message loop                 |
| WS-MSG-AVAILABLE-FLG      | 'M' (MORE) / 'N' (NONE) | More messages on queue                |
| WS-REQUEST-MQ-FLG         | 'O' (OPEN) / 'C' (CLOSED) | Request queue state                  |
| WS-REPLY-MQ-FLG           | 'O' (OPEN) / 'C' (CLOSED) | Reply queue state                    |
| WS-XREF-READ-FLG          | 'Y' (FOUND) / 'N' (NOT FOUND) | Card found in XREF              |
| WS-ACCT-MASTER-READ-FLG   | 'Y' / 'N'               | Account master found                   |
| WS-CUST-MASTER-READ-FLG   | 'Y' / 'N'               | Customer master found                  |
| WS-PAUT-SMRY-SEG-FLG      | 'Y' / 'N'               | IMS summary segment found              |
| WS-DECLINE-FLG            | 'A' (APPROVE) / 'D' (DECLINE) | Authorization decision          |
| WS-DECLINE-REASON-FLG     | 'I','A','C','F','M'     | Specific decline reason code           |

#### 3.4 IMS Segment Variables (lines 81–97)

| Field                  | Picture          | Value/Description                         |
|------------------------|------------------|-------------------------------------------|
| PSB-NAME               | PIC X(8)         | 'PSBPAUTB' — PSB to schedule              |
| PAUT-PCB-NUM           | PIC S9(4) COMP   | +1 — PCB ordinal position in PSBPAUTB    |
| IMS-RETURN-CODE        | PIC X(02)        | Copy of DIBSTAT after each DLI call       |

IMS status code 88-levels: STATUS-OK (' ','FW'), SEGMENT-NOT-FOUND ('GE'), DUPLICATE-SEGMENT-FOUND ('II'), WRONG-PARENTAGE ('GP'), END-OF-DB ('GB'), DATABASE-UNAVAILABLE ('BA'), PSB-SCHEDULED-MORE-THAN-ONCE ('TC'), COULD-NOT-SCHEDULE-PSB ('TE').

#### 3.5 Error Log Record (copybook CCPAUERY.cpy)

| Field              | Picture  | Description                    |
|--------------------|----------|--------------------------------|
| ERR-DATE           | X(06)    | YYMMDD of error                |
| ERR-TIME           | X(06)    | HHMMSS of error                |
| ERR-APPLICATION    | X(08)    | Populated with WS-CICS-TRANID  |
| ERR-PROGRAM        | X(08)    | Populated with WS-PGM-AUTH     |
| ERR-LOCATION       | X(04)    | Code point (e.g., 'M001')      |
| ERR-LEVEL          | X(01)    | 'L'=log, 'I'=info, 'W'=warning, 'C'=critical |
| ERR-SUBSYSTEM      | X(01)    | 'A'=app, 'C'=CICS, 'I'=IMS, 'D'=DB2, 'M'=MQ, 'F'=file |
| ERR-CODE-1         | X(09)    | Primary error code             |
| ERR-CODE-2         | X(09)    | Secondary error code           |
| ERR-MESSAGE        | X(50)    | Error description              |
| ERR-EVENT-KEY      | X(20)    | Usually card number            |

---

### 4. CICS, IMS, and MQ Commands

#### 4.1 CICS Commands

| Command             | Location                     | Parameters / Notes                                        |
|---------------------|------------------------------|-----------------------------------------------------------|
| EXEC CICS RETRIEVE  | 1000-INITIALIZE (line 233)   | INTO(MQTM) NOHANDLE — extracts MQ trigger data           |
| EXEC CICS RETURN    | MAIN-PARA (line 226)         | No TRANSID (program terminates task)                     |
| EXEC CICS SYNCPOINT | 2000-MAIN-PROCESS (line 335) | After each message; commits IMS and CICS resources       |
| EXEC CICS ASKTIME   | 8500-INSERT-AUTH (line 857)  | ABSTIME(WS-ABS-TIME) NOHANDLE                            |
| EXEC CICS FORMATTIME| 8500-INSERT-AUTH (line 861)  | ABSTIME YYDDD TIME MILLISECONDS                          |
| EXEC CICS ASKTIME   | 9500-LOG-ERROR (line 986)    | For error timestamp                                      |
| EXEC CICS FORMATTIME| 9500-LOG-ERROR (line 990)    | YYMMDD TIME                                              |

#### 4.2 IMS DLI Commands (EXEC DLI form, using PSB PSBPAUTB / PCB 1)

| Command          | Paragraph          | Segment      | Qualifier (SSA / WHERE)         | Purpose                                |
|------------------|--------------------|--------------|---------------------------------|----------------------------------------|
| EXEC DLI SCHD    | 1200-SCHEDULE-PSB  | —            | PSB((PSB-NAME))  NODHABEND      | Schedule PSB before each auth         |
| EXEC DLI GU      | 5500-READ-AUTH-SUMMRY | PAUTSUM0  | WHERE(ACCNTID = PA-ACCT-ID)     | Retrieve summary segment for account  |
| EXEC DLI REPL    | 8400-UPDATE-SUMMARY | PAUTSUM0   | —                               | Update existing summary segment       |
| EXEC DLI ISRT    | 8400-UPDATE-SUMMARY | PAUTSUM0   | —                               | Insert new summary segment            |
| EXEC DLI ISRT    | 8500-INSERT-AUTH   | PAUTSUM0 + PAUTDTL1 | WHERE(ACCNTID=PA-ACCT-ID) | Insert detail under parent        |
| EXEC DLI TERM    | 9000-TERMINATE     | —            | —                               | Release PSB                           |

**Note on PSB scheduling:** 1200-SCHEDULE-PSB handles the TC (already-scheduled) condition by issuing EXEC DLI TERM followed by a new EXEC DLI SCHD (lines 299–307). The PSB is re-scheduled per message and terminated at SYNCPOINT time. The flag IMS-PSB-NOT-SCHD is set to TRUE after each SYNCPOINT (line 337) so the next message call triggers a fresh schedule.

#### 4.3 MQ Calls (CALL statement form)

| Call           | Paragraph                  | Handle Used        | Options / Notes                                               |
|----------------|----------------------------|--------------------|---------------------------------------------------------------|
| CALL 'MQOPEN'  | 1100-OPEN-REQUEST-QUEUE    | W01-HCONN-REQUEST  | MQOO-INPUT-SHARED; queue name from MQTM trigger data         |
| CALL 'MQGET'   | 3100-READ-REQUEST-MQ       | W01-HOBJ-REQUEST   | MQGMO-NO-SYNCPOINT + MQGMO-WAIT + MQGMO-CONVERT + MQGMO-FAIL-IF-QUIESCING; wait 5000ms |
| CALL 'MQPUT1'  | 7100-SEND-RESPONSE         | W02-HCONN-REPLY    | One-shot open+put+close on reply queue; MQPMO-NO-SYNCPOINT + MQPMO-DEFAULT-CONTEXT; expiry 50 (5 seconds) |
| CALL 'MQCLOSE' | 9100-CLOSE-REQUEST-QUEUE   | W01-HOBJ-REQUEST   | MQCO-NONE                                                     |

**MQ GET options detail (3100-READ-REQUEST-MQ, line 389):**
- MQGMO-NO-SYNCPOINT: message is not under syncpoint (committed immediately on GET)
- MQGMO-WAIT: wait up to 5000ms for a message
- MQGMO-CONVERT: convert character set if needed
- MQGMO-FAIL-IF-QUIESCING: do not wait if queue manager is quiescing
- MQRC-NO-MSG-AVAILABLE triggers NO-MORE-MSG-AVAILABLE flag (clean loop exit)

**MQ PUT1 options detail (7100-SEND-RESPONSE, lines 741–766):**
- MQMT-REPLY message type
- Correlation ID from saved MQMD-CORRELID of request (WS-SAVE-CORRELID)
- MQPER-NOT-PERSISTENT: message is not persistent
- Expiry 50 = 5 seconds (MQ expiry units are tenths of seconds)
- MQFMT-STRING format

#### 4.4 VSAM File Access Commands

| Dataset Name  | Key Field               | Into Structure        | RESP Values Handled         |
|---------------|-------------------------|-----------------------|-----------------------------|
| CCXREF        | XREF-CARD-NUM (16 bytes)| CARD-XREF-RECORD      | NORMAL=found; NOTFND=not found; OTHER=critical |
| ACCTDAT       | WS-CARD-RID-ACCT-ID-X (11 bytes) | ACCOUNT-RECORD | NORMAL=found; NOTFND=not found; OTHER=critical |
| CUSTDAT       | WS-CARD-RID-CUST-ID-X (9 bytes)  | CUSTOMER-RECORD | NORMAL=found; NOTFND=not found; OTHER=critical |

All three are EXEC CICS READ with KEYLENGTH and LENGTH specified, using RESP/RESP2.

---

### 5. File Access

| File Reference | Access Method | Dataset DD Name | Key         | Struct Copybook | Operation |
|----------------|---------------|-----------------|-------------|-----------------|-----------|
| CCXREF         | CICS READ     | CCXREF          | Card number (16 bytes) | CVACT03Y | READ only |
| ACCTDAT        | CICS READ     | ACCTDAT         | Account ID (11 bytes)  | CVACT01Y | READ only |
| CUSTDAT        | CICS READ     | CUSTDAT         | Customer ID (9 bytes)  | CVCUS01Y | READ only |

---

### 6. Screen Interaction

COPAUA0C has **no screen interaction**. It is an MQ-triggered, non-interactive program. It uses EXEC CICS RETRIEVE to obtain the trigger message and EXEC CICS RETURN to terminate. No BMS maps are used.

---

### 7. Called Programs

| Program | Call Method     | COMMAREA / Data Passed      | Purpose                         |
|---------|-----------------|-----------------------------|---------------------------------|
| MQOPEN  | CALL statement  | W01-HCONN-REQUEST, MQM-OD-REQUEST, WS-OPTIONS, W01-HOBJ-REQUEST, WS-COMPCODE, WS-REASON | Open request queue |
| MQGET   | CALL statement  | W01-HCONN-REQUEST, W01-HOBJ-REQUEST, MQM-MD-REQUEST, MQM-GET-MESSAGE-OPTIONS, W01-BUFFLEN, W01-GET-BUFFER, W01-DATALEN, WS-COMPCODE, WS-REASON | Get message from queue |
| MQPUT1  | CALL statement  | W02-HCONN-REPLY, MQM-OD-REPLY, MQM-MD-REPLY, MQM-PUT-MESSAGE-OPTIONS, W02-BUFFLEN, W02-PUT-BUFFER, WS-COMPCODE, WS-REASON | Send response |
| MQCLOSE | CALL statement  | W01-HCONN-REQUEST, W01-HOBJ-REQUEST, MQCO-NONE, WS-COMPCODE, WS-REASON | Close request queue |

No EXEC CICS LINK or XCTL to other programs.

---

### 8. Error Handling

The program uses a structured error logging approach via the ERROR-LOG-RECORD copybook (CCPAUERY.cpy). Paragraph 9500-LOG-ERROR is called for all error conditions. After logging, processing continues unless an ERR-CRITICAL condition terminates further steps.

| Error Location | Subsystem | Level    | Condition                              |
|----------------|-----------|----------|----------------------------------------|
| M001           | MQ        | CRITICAL | MQOPEN failed on request queue         |
| M003           | CICS      | CRITICAL | MQGET failed (non-empty-queue reason)  |
| M004           | MQ        | CRITICAL | MQPUT1 failed on reply queue           |
| M005           | MQ        | WARNING  | MQCLOSE failed on request queue        |
| I001           | IMS       | CRITICAL | PSB schedule (SCHD) failed             |
| I002           | IMS       | CRITICAL | IMS GU on PAUTSUM0 failed              |
| I003           | IMS       | CRITICAL | IMS REPL/ISRT on PAUTSUM0 failed       |
| I004           | IMS       | CRITICAL | IMS ISRT on PAUTDTL1 failed            |
| A001           | APP       | WARNING  | Card not found in XREF (CCXREF)        |
| A002           | APP       | WARNING  | Account not found in ACCTDAT           |
| A003           | APP       | WARNING  | Customer not found in CUSTDAT          |
| C001           | CICS      | CRITICAL | CICS READ failed on CCXREF             |
| C002           | CICS      | CRITICAL | CICS READ failed on ACCTDAT            |
| C003           | CICS      | CRITICAL | CICS READ failed on CUSTDAT            |

**Non-critical (WARNING) conditions** result in a declined authorization with reason code 3100 (INVALID CARD) and processing continues.

**SYNCPOINT strategy:** EXEC CICS SYNCPOINT is issued after each successfully processed message (line 335). The IMS PSB flag is reset to NOT-SCHD immediately after syncpoint (line 337) so the next iteration re-schedules the PSB.

---

### 9. Business Rules

All business rules are applied in paragraph 6000-MAKE-DECISION (lines 657–732).

#### 9.1 Authorization Decision Logic

1. **Default:** Authorization is set to APPROVE at the start of 5000-PROCESS-AUTH (line 441).
2. **Card/Account not found:** If CARD-NFOUND-XREF, NFOUND-ACCT-IN-MSTR, or NFOUND-CUST-IN-MSTR, the authorization is declined.
3. **Credit limit check (with IMS summary):** If FOUND-PAUT-SMRY-SEG:
   - `WS-AVAILABLE-AMT = PA-CREDIT-LIMIT - PA-CREDIT-BALANCE`
   - If `WS-TRANSACTION-AMT > WS-AVAILABLE-AMT` → DECLINE with INSUFFICIENT-FUND
4. **Credit limit check (without IMS summary, using VSAM account):** If NFOUND-PAUT-SMRY-SEG and FOUND-ACCT-IN-MSTR:
   - `WS-AVAILABLE-AMT = ACCT-CREDIT-LIMIT - ACCT-CURR-BAL`
   - If `WS-TRANSACTION-AMT > WS-AVAILABLE-AMT` → DECLINE with INSUFFICIENT-FUND
5. **No account data at all:** DECLINE (no specific reason flag set).

**Note:** The program does NOT implement CARD-NOT-ACTIVE, ACCOUNT-CLOSED, CARD-FRAUD, or MERCHANT-FRAUD decline reasons in the current 6000-MAKE-DECISION code. Those 88-level conditions exist in WS-DECLINE-REASON-FLG but are set only by the XREF-lookup error path (reason 3100) and the credit-check path (reason 4100). The other reason codes (4200, 4300, 5100, 5200) appear in the response reason mapping (lines 700–717) but no code path sets those WS-DECLINE-REASON-FLG flags for this program.

#### 9.2 Response Code Assignment

| Condition          | AUTH-RESP-CODE | AUTH-RESP-REASON |
|--------------------|----------------|------------------|
| Approved           | '00'           | '0000'           |
| Card/acct not found| '05'           | '3100'           |
| Insufficient funds | '05'           | '4100'           |
| Card not active    | '05'           | '4200'           |
| Account closed     | '05'           | '4300'           |
| Card fraud         | '05'           | '5100'           |
| Merchant fraud     | '05'           | '5200'           |
| Unknown            | '05'           | '9000'           |

AUTH-ID-CODE is set to PA-RQ-AUTH-TIME (the request time field, 6 bytes) to serve as a unique authorization identifier.

#### 9.3 IMS Summary Update (8400-UPDATE-SUMMARY)

- If FOUND-PAUT-SMRY-SEG: use EXEC DLI REPL
- If NFOUND-PAUT-SMRY-SEG: initialize and EXEC DLI ISRT
- Approved authorization: ADD 1 to PA-APPROVED-AUTH-CNT; ADD WS-APPROVED-AMT to PA-APPROVED-AUTH-AMT; ADD WS-APPROVED-AMT to PA-CREDIT-BALANCE; SET PA-CASH-BALANCE = 0
- Declined authorization: ADD 1 to PA-DECLINED-AUTH-CNT; ADD PA-TRANSACTION-AMT to PA-DECLINED-AUTH-AMT

#### 9.4 Authorization Key Computation (8500-INSERT-AUTH)

The IMS detail segment key (PA-AUTHORIZATION-KEY) uses an inverted timestamp approach for descending sequence:
- `PA-AUTH-DATE-9C = 99999 - WS-YYDDD` (YYDDD format)
- `PA-AUTH-TIME-9C = 999999999 - WS-TIME-WITH-MS` (HHMMSSMMM)

This ensures newest authorizations sort first in IMS (ascending key = descending time).

---

### 10. I/O Specification

#### 10.1 Input

| Source           | Format               | Fields                                             |
|------------------|----------------------|----------------------------------------------------|
| MQ Request Queue | CSV, 500-byte buffer | AUTH-DATE, AUTH-TIME, CARD-NUM, AUTH-TYPE, CARD-EXPIRY-DATE, MESSAGE-TYPE, MESSAGE-SOURCE, PROCESSING-CODE, TRANSACTION-AMT, MERCHANT-CATAGORY-CODE, ACQR-COUNTRY-CODE, POS-ENTRY-MODE, MERCHANT-ID, MERCHANT-NAME, MERCHANT-CITY, MERCHANT-STATE, MERCHANT-ZIP, TRANSACTION-ID |

Amount field WS-TRANSACTION-AMT-AN is converted using FUNCTION NUMVAL (line 376).

#### 10.2 Output

| Target            | Format                | Fields                                                              |
|-------------------|-----------------------|---------------------------------------------------------------------|
| MQ Reply Queue    | CSV, up to 200 bytes  | CARD-NUM, TRANSACTION-ID, AUTH-ID-CODE, AUTH-RESP-CODE, AUTH-RESP-REASON, APPROVED-AMT |
| IMS DBPAUTP0      | PAUTSUM0 segment      | Summary aggregate data (counts, amounts, limits, balances)         |
| IMS DBPAUTP0      | PAUTDTL1 segment      | Full authorization detail record                                   |

---
