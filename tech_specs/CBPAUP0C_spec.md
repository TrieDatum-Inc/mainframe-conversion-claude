# Technical Specification: CBPAUP0C

## Program Name and Purpose

**Program ID:** CBPAUP0C  
**Source File:** `/app/app-authorization-ims-db2-mq/cbl/CBPAUP0C.cbl`  
**Type:** Batch COBOL IMS Program  
**Application:** CardDemo - Authorization Module  
**Function:** Delete Expired Pending Authorization Messages from the IMS database

This program performs housekeeping on the IMS pending authorization database. It scans all PAUTSUM0 (summary) segments and their child PAUTDTL1 (detail) segments. Any detail segment whose authorization date is older than a configurable expiry threshold (in days) is deleted. When all detail segments under a summary are removed, the summary segment itself is also deleted. The program uses IMS checkpoint/restart support for recoverability.

---

## Artifact Inventory

| Artifact | Type | Role |
|----------|------|------|
| CBPAUP0C.cbl | COBOL Source | Main program |
| CIPAUSMY.cpy | Copybook | IMS PAUTSUM0 segment layout |
| CIPAUDTY.cpy | Copybook | IMS PAUTDTL1 segment layout |
| PSBPAUTB | PSB (not available for inspection) | IMS Program Specification Block |

---

## IDENTIFICATION DIVISION Metadata

- **PROGRAM-ID:** CBPAUP0C  
- **AUTHOR:** AWS  
- Source line 22–24

---

## ENVIRONMENT DIVISION

No FILE-CONTROL entries are defined (lines 30–31). The program has no sequential or VSAM files. All data access is through IMS DL/I calls.

Input parameters are received from SYSIN via `ACCEPT PRM-INFO FROM SYSIN` at line 189.

---

## DATA DIVISION

### WORKING-STORAGE SECTION

**01 WS-VARIABLES** (lines 41–73)

| Field | PIC | Initial | Purpose |
|-------|-----|---------|---------|
| WS-PGMNAME | X(08) | 'CBPAUP0C' | Program identification |
| CURRENT-DATE | 9(06) | — | System date (YYMMDD from DATE) |
| CURRENT-YYDDD | 9(05) | — | Julian date from DAY (used for expiry computation) |
| WS-AUTH-DATE | 9(05) | — | Decoded authorization date (Julian, derived from PA-AUTH-DATE-9C) |
| WS-EXPIRY-DAYS | S9(4) COMP | — | Threshold days for expiry (from parm or default 5) |
| WS-DAY-DIFF | S9(4) COMP | — | Computed age of authorization in days |
| IDX | S9(4) COMP | — | Loop index |
| WS-CURR-APP-ID | 9(11) | — | Current account ID being processed |
| WS-NO-CHKP | 9(8) | 0 | Checkpoint counter |
| WS-AUTH-SMRY-PROC-CNT | 9(8) | 0 | Summary records processed since last checkpoint |
| WS-TOT-REC-WRITTEN | S9(8) COMP | 0 | (Unused in current logic) |
| WS-NO-SUMRY-READ | S9(8) COMP | 0 | Running count of summary segments read |
| WS-NO-SUMRY-DELETED | S9(8) COMP | 0 | Running count of summary segments deleted |
| WS-NO-DTL-READ | S9(8) COMP | 0 | Running count of detail segments read |
| WS-NO-DTL-DELETED | S9(8) COMP | 0 | Running count of detail segments deleted |
| WS-ERR-FLG | X(01) | 'N' | Error flag; 88-Y=ERR-FLG-ON, N=ERR-FLG-OFF |
| WS-END-OF-AUTHDB-FLAG | X(01) | 'N' | IMS end-of-database flag; 88-Y=END-OF-AUTHDB |
| WS-MORE-AUTHS-FLAG | X(01) | 'N' | More child detail segments available; 88-Y=MORE-AUTHS |
| WS-QUALIFY-DELETE-FLAG | X(01) | 'N' | Expiry qualification; 88-Y=QUALIFIED-FOR-DELETE |
| WS-INFILE-STATUS | X(02) | SPACES | Unused file status variable |
| WS-CUSTID-STATUS | X(02) | SPACES | File status; 88-10=END-OF-FILE |

**Checkpoint ID** (lines 75–78):

```
WK-CHKPT-ID
  10 FILLER          'RMAD'
  10 WK-CHKPT-ID-CTR 9(04)
```

**01 WS-IMS-VARIABLES** (lines 79–95)

| Field | PIC | Value | Purpose |
|-------|-----|-------|---------|
| PSB-NAME | X(8) | 'PSBPAUTB' | Name of PSB to schedule |
| PAUT-PCB-NUM | S9(4) COMP | +2 | PCB offset — NOTE: this program uses PCB #2; COPAUA0C uses PCB #1 |
| IMS-RETURN-CODE | X(02) | — | Receives DIBSTAT after each DL/I call |

88-level conditions on IMS-RETURN-CODE:
- `STATUS-OK`: spaces or 'FW'
- `SEGMENT-NOT-FOUND`: 'GE'
- `DUPLICATE-SEGMENT-FOUND`: 'II'
- `WRONG-PARENTAGE`: 'GP'
- `END-OF-DB`: 'GB'
- `DATABASE-UNAVAILABLE`: 'BA'
- `PSB-SCHEDULED-MORE-THAN-ONCE`: 'TC'
- `COULD-NOT-SCHEDULE-PSB`: 'TE'
- `RETRY-CONDITION`: 'BA', 'FH', 'TE'

**01 PRM-INFO** (lines 98–108) — SYSIN parameter layout

| Field | PIC | Position | Purpose |
|-------|-----|----------|---------|
| P-EXPIRY-DAYS | 9(02) | 1–2 | Days after which auth is considered expired; default 5 |
| FILLER | X(01) | 3 | Delimiter |
| P-CHKP-FREQ | X(05) | 4–8 | How often to take a checkpoint (count of summaries); default 5 |
| FILLER | X(01) | 9 | Delimiter |
| P-CHKP-DIS-FREQ | X(05) | 10–14 | How often to display a checkpoint message; default 10 |
| FILLER | X(01) | 15 | Delimiter |
| P-DEBUG-FLAG | X(01) | 16 | 'Y' enables debug DISPLAY statements |
| FILLER | X(01) | 17 | Padding |

### LINKAGE SECTION

```
01 IO-PCB-MASK    PIC X.
01 PGM-PCB-MASK   PIC X.
```

The PROCEDURE DIVISION USING clause declares `IO-PCB-MASK` and `PGM-PCB-MASK` at lines 132–133, which is the standard IMS batch entry convention. The actual PCB used for database access is PCB(2) as specified in `PAUT-PCB-NUM`.

---

## Copybooks Referenced

| Copybook | Used In | Purpose |
|----------|---------|---------|
| CIPAUSMY.cpy | Line 117 | IMS PAUTSUM0 (pending auth summary) segment field layout |
| CIPAUDTY.cpy | Line 121 | IMS PAUTDTL1 (pending auth detail) segment field layout |

### CIPAUSMY.cpy — PENDING-AUTH-SUMMARY Fields

| Field | PIC | Description |
|-------|-----|-------------|
| PA-ACCT-ID | S9(11) COMP-3 | Account ID (root segment key) |
| PA-CUST-ID | 9(09) | Customer ID |
| PA-AUTH-STATUS | X(01) | Authorization overall status |
| PA-ACCOUNT-STATUS | X(02) OCCURS 5 | Account status codes (up to 5) |
| PA-CREDIT-LIMIT | S9(09)V99 COMP-3 | Credit limit |
| PA-CASH-LIMIT | S9(09)V99 COMP-3 | Cash limit |
| PA-CREDIT-BALANCE | S9(09)V99 COMP-3 | Current credit balance of pending auths |
| PA-CASH-BALANCE | S9(09)V99 COMP-3 | Current cash balance of pending auths |
| PA-APPROVED-AUTH-CNT | S9(04) COMP | Count of approved authorizations |
| PA-DECLINED-AUTH-CNT | S9(04) COMP | Count of declined authorizations |
| PA-APPROVED-AUTH-AMT | S9(09)V99 COMP-3 | Total approved authorization amount |
| PA-DECLINED-AUTH-AMT | S9(09)V99 COMP-3 | Total declined authorization amount |
| FILLER | X(34) | Padding |

### CIPAUDTY.cpy — PENDING-AUTH-DETAILS Fields

| Field | PIC | Description |
|-------|-----|-------------|
| PA-AUTHORIZATION-KEY | — | Composite key (date + time) |
| PA-AUTH-DATE-9C | S9(05) COMP-3 | Complement-encoded date (99999 - YYDDD) |
| PA-AUTH-TIME-9C | S9(09) COMP-3 | Complement-encoded time |
| PA-AUTH-ORIG-DATE | X(06) | Original date YYMMDD |
| PA-AUTH-ORIG-TIME | X(06) | Original time HHMMSS |
| PA-CARD-NUM | X(16) | Card number |
| PA-AUTH-TYPE | X(04) | Authorization type |
| PA-CARD-EXPIRY-DATE | X(04) | Card expiry MMYY |
| PA-MESSAGE-TYPE | X(06) | ISO message type |
| PA-MESSAGE-SOURCE | X(06) | Message source system |
| PA-AUTH-ID-CODE | X(06) | Authorization ID code |
| PA-AUTH-RESP-CODE | X(02) | Response code; 88 PA-AUTH-APPROVED='00' |
| PA-AUTH-RESP-REASON | X(04) | Decline reason code |
| PA-PROCESSING-CODE | 9(06) | ISO processing code |
| PA-TRANSACTION-AMT | S9(10)V99 COMP-3 | Transaction amount |
| PA-APPROVED-AMT | S9(10)V99 COMP-3 | Approved amount |
| PA-MERCHANT-CATAGORY-CODE | X(04) | MCC |
| PA-ACQR-COUNTRY-CODE | X(03) | Acquirer country |
| PA-POS-ENTRY-MODE | 9(02) | POS entry mode |
| PA-MERCHANT-ID | X(15) | Merchant identifier |
| PA-MERCHANT-NAME | X(22) | Merchant name |
| PA-MERCHANT-CITY | X(13) | Merchant city |
| PA-MERCHANT-STATE | X(02) | Merchant state |
| PA-MERCHANT-ZIP | X(09) | Merchant ZIP |
| PA-TRANSACTION-ID | X(15) | Transaction identifier |
| PA-MATCH-STATUS | X(01) | Match status: P=Pending, D=Declined, E=Expired, M=Matched |
| PA-AUTH-FRAUD | X(01) | Fraud flag: F=Confirmed, R=Removed |
| PA-FRAUD-RPT-DATE | X(08) | Fraud report date |
| FILLER | X(17) | Padding |

---

## IMS DL/I Calls

All calls use EXEC DLI syntax. The PSB is **PSBPAUTB**, PCB number **2** (PAUT-PCB-NUM = +2).

### 2000-FIND-NEXT-AUTH-SUMMARY (line 216)

```cobol
EXEC DLI GN USING PCB(PAUT-PCB-NUM)
     SEGMENT (PAUTSUM0)
     INTO (PENDING-AUTH-SUMMARY)
END-EXEC
```
- **Function:** GN (Get Next) — sequential scan of all PAUTSUM0 root segments
- **Status handling:** spaces=success; 'GB'=end-of-database; other=ABEND

### 3000-FIND-NEXT-AUTH-DTL (line 248)

```cobol
EXEC DLI GNP USING PCB(PAUT-PCB-NUM)
     SEGMENT (PAUTDTL1)
     INTO (PENDING-AUTH-DETAILS)
END-EXEC
```
- **Function:** GNP (Get Next within Parent) — reads child detail segments under the current summary
- **Status handling:** spaces=success; 'GE' or 'GB'=no more children; other=ABEND

### 5000-DELETE-AUTH-DTL (line 302)

```cobol
EXEC DLI DLET USING PCB(PAUT-PCB-NUM)
     SEGMENT (PAUTDTL1)
     FROM (PENDING-AUTH-DETAILS)
END-EXEC
```
- **Function:** DLET — deletes the most recently fetched PAUTDTL1 segment
- **Status handling:** spaces=success; other=ABEND

### 6000-DELETE-AUTH-SUMMARY (line 327)

```cobol
EXEC DLI DLET USING PCB(PAUT-PCB-NUM)
     SEGMENT (PAUTSUM0)
     FROM (PENDING-AUTH-SUMMARY)
END-EXEC
```
- **Function:** DLET — deletes the PAUTSUM0 segment after all children are removed
- **Status handling:** spaces=success; other=ABEND

### 9000-TAKE-CHECKPOINT (line 352)

```cobol
EXEC DLI CHKP ID(WK-CHKPT-ID)
END-EXEC
```
- **Function:** CHKP — IMS checkpoint for restart/recovery
- **Status handling:** spaces=success; other=ABEND

---

## Program Flow — Paragraph-by-Paragraph Logic

### MAIN-PARA (line 136)

```
1. PERFORM 1000-INITIALIZE
2. PERFORM 2000-FIND-NEXT-AUTH-SUMMARY     (prime the loop)
3. PERFORM UNTIL ERR-FLG-ON OR END-OF-AUTHDB
     a. PERFORM 3000-FIND-NEXT-AUTH-DTL    (prime inner loop)
     b. PERFORM UNTIL NO-MORE-AUTHS
          i.  PERFORM 4000-CHECK-IF-EXPIRED
          ii. IF QUALIFIED-FOR-DELETE THEN PERFORM 5000-DELETE-AUTH-DTL
          iii.PERFORM 3000-FIND-NEXT-AUTH-DTL   (advance inner loop)
     c. IF PA-APPROVED-AUTH-CNT <= 0 AND PA-DECLINED-AUTH-CNT <= 0
             PERFORM 6000-DELETE-AUTH-SUMMARY
     d. IF WS-AUTH-SMRY-PROC-CNT > P-CHKP-FREQ
             PERFORM 9000-TAKE-CHECKPOINT; reset counter
     e. PERFORM 2000-FIND-NEXT-AUTH-SUMMARY
4. PERFORM 9000-TAKE-CHECKPOINT            (final checkpoint)
5. DISPLAY summary statistics
6. GOBACK
```

**Note — Bug observation:** At line 156, the condition reads `IF PA-APPROVED-AUTH-CNT <= 0 AND PA-APPROVED-AUTH-CNT <= 0` — the second condition repeats PA-APPROVED-AUTH-CNT instead of referencing PA-DECLINED-AUTH-CNT. This is likely a coding error that causes the summary to be deleted only when the approved count is zero, regardless of the declined count.

### 1000-INITIALIZE (line 183)

- Accepts current date and Julian date from the system.
- Reads parameter string from SYSIN into PRM-INFO.
- Validates and defaults parameters: P-EXPIRY-DAYS defaults to 5, P-CHKP-FREQ to 5, P-CHKP-DIS-FREQ to 10, P-DEBUG-FLAG to 'N'.

### 4000-CHECK-IF-EXPIRED (line 277)

```
COMPUTE WS-AUTH-DATE = 99999 - PA-AUTH-DATE-9C
COMPUTE WS-DAY-DIFF  = CURRENT-YYDDD - WS-AUTH-DATE
IF WS-DAY-DIFF >= WS-EXPIRY-DAYS
   SET QUALIFIED-FOR-DELETE TO TRUE
   Update PA-APPROVED-AUTH-CNT or PA-DECLINED-AUTH-CNT
ELSE
   SET NOT-QUALIFIED-FOR-DELETE TO TRUE
```

The authorization date is stored as a complement (99999 - YYDDD) for descending sort in IMS. The decode reverses this to obtain the original Julian day. The difference from today determines age.

When qualified for deletion:
- If response code = '00' (approved): decrements PA-APPROVED-AUTH-CNT and subtracts PA-APPROVED-AMT from PA-APPROVED-AUTH-AMT.
- Otherwise (declined): decrements PA-DECLINED-AUTH-CNT and subtracts PA-TRANSACTION-AMT from PA-DECLINED-AUTH-AMT.

### 9999-ABEND (line 377)

Sets RETURN-CODE to 16 and issues GOBACK. No IMS TERM is issued — the IMS region will handle cleanup on abnormal termination.

---

## Error Handling

| Condition | Action |
|-----------|--------|
| GN returns non-spaces, non-GB | DISPLAY error, PERFORM 9999-ABEND |
| GNP returns non-spaces, non-GE, non-GB | DISPLAY error, PERFORM 9999-ABEND |
| DLET (detail) returns non-spaces | DISPLAY error, PERFORM 9999-ABEND |
| DLET (summary) returns non-spaces | DISPLAY error, PERFORM 9999-ABEND |
| CHKP returns non-spaces | DISPLAY error, PERFORM 9999-ABEND |
| 9999-ABEND | MOVE 16 TO RETURN-CODE; GOBACK |

---

## Transaction Flow Participation

This is a standalone batch program. It does not participate in any CICS transaction flow. It is typically invoked via a JCL job step in a batch housekeeping job chain.

**Typical invocation context:**
- JCL EXEC PGM=CBPAUP0C
- PSB PSBPAUTB must be available in the IMS catalog
- SYSIN DD provides the parameter string: `05 00005 00010 N`

---

## Inter-Program Interactions

| Interaction | Target | Method |
|-------------|--------|--------|
| IMS PSB | PSBPAUTB | Implicit — assigned by IMS region at program schedule |

No CALL statements to other programs. No CICS interactions.

---

## Output Summary (DISPLAY statements)

At program end (lines 171–177), the following statistics are displayed to SYSOUT:

```
# TOTAL SUMMARY READ  : nnnnnnnn
# SUMMARY REC DELETED : nnnnnnnn
# TOTAL DETAILS READ  : nnnnnnnn
# DETAILS REC DELETED : nnnnnnnn
```
