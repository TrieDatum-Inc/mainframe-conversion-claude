# Technical Specification: COPAUS2C

## Program Name and Purpose

**Program ID:** COPAUS2C  
**Source File:** `/app/app-authorization-ims-db2-mq/cbl/COPAUS2C.cbl`  
**Type:** CICS COBOL IMS DB2 Program (called sub-program)  
**Application:** CardDemo - Authorization Module  
**Function:** Mark Authorization Message as Fraud (or Remove Fraud Flag) in DB2

COPAUS2C is invoked exclusively via CICS LINK from COPAUS1C. It receives the full authorization detail record (a copy of PAUTDTL1 segment data) plus account/customer IDs and an action flag ('F'=report fraud, 'R'=remove fraud). It then either inserts a new row into the DB2 table CARDDEMO.AUTHFRDS, or if a duplicate key is detected (SQLCODE -803), updates the existing row.

This program does NOT interact directly with IMS — it operates on the DB2 fraud reporting table only.

---

## Artifact Inventory

| Artifact | Type | Role |
|----------|------|------|
| COPAUS2C.cbl | COBOL Source | Main program |
| CIPAUDTY.cpy | Copybook | IMS PAUTDTL1 layout — defines PA-* fields used as DB2 source data |
| AUTHFRDS DCLGEN | DB2 DCLGEN | EXEC SQL INCLUDE AUTHFRDS; defines host variables for CARDDEMO.AUTHFRDS |

**Note:** The AUTHFRDS DCLGEN is referenced as `EXEC SQL INCLUDE AUTHFRDS END-EXEC` at line 69. The actual DCLGEN file is not present in the `/cpy/` directory as inspected. [ARTIFACT NOT AVAILABLE FOR INSPECTION: AUTHFRDS DCLGEN]. Field names referenced in source: CARD-NUM, AUTH-TS, AUTH-TYPE, CARD-EXPIRY-DATE, MESSAGE-TYPE, MESSAGE-SOURCE, AUTH-ID-CODE, AUTH-RESP-CODE, AUTH-RESP-REASON, PROCESSING-CODE, TRANSACTION-AMT, APPROVED-AMT, MERCHANT-CATAGORY-CODE, ACQR-COUNTRY-CODE, POS-ENTRY-MODE, MERCHANT-ID, MERCHANT-NAME (with MERCHANT-NAME-LEN and MERCHANT-NAME-TEXT implied by VARCHAR), MERCHANT-CITY, MERCHANT-STATE, MERCHANT-ZIP, TRANSACTION-ID, MATCH-STATUS, AUTH-FRAUD, FRAUD-RPT-DATE (from CURRENT DATE), ACCT-ID, CUST-ID.

---

## IDENTIFICATION DIVISION Metadata

- **PROGRAM-ID:** COPAUS2C  
- **AUTHOR:** AWS  
- Source lines 22–24

---

## DATA DIVISION

### Working-Storage Variables (lines 32–60)

| Field | PIC | Purpose |
|-------|-----|---------|
| WS-PGMNAME | X(08) | 'COPAUS2C' |
| WS-LENGTH | S9(4) COMP | Length variable |
| WS-AUTH-TIME | 9(09) | Auth time (numeric) |
| WS-AUTH-TIME-AN | X(09) REDEFINES | Auth time (alphanumeric for parsing) |
| WS-AUTH-TS | — | Timestamp for DB2 formatted as 'YY-MM-DD HH.MI.SSNNNNNN' |
| WS-AUTH-YY | X(02) | Year portion |
| WS-AUTH-MM | X(02) | Month portion |
| WS-AUTH-DD | X(02) | Day portion |
| WS-AUTH-HH | X(02) | Hour portion |
| WS-AUTH-MI | X(02) | Minute portion |
| WS-AUTH-SS | X(02) | Seconds portion |
| WS-AUTH-SSS | X(03) | Milliseconds portion |
| WS-ERR-FLG | X(01) | Error flag |
| WS-SQLCODE | +9(06) | SQLCODE display |
| WS-SQLSTATE | +9(09) | SQLSTATE display |
| WS-ABS-TIME | S9(15) COMP-3 | CICS absolute time |
| WS-CUR-DATE | X(08) | Current date MMDDYY |

### SQL Includes (lines 64–70)

```cobol
EXEC SQL INCLUDE SQLCA END-EXEC.
EXEC SQL INCLUDE AUTHFRDS END-EXEC.
```

---

## LINKAGE SECTION (lines 73–86)

The DFHCOMMAREA structure passed from COPAUS1C via CICS LINK:

```
01 DFHCOMMAREA.
  02 WS-ACCT-ID              PIC 9(11)     -- Account ID
  02 WS-CUST-ID              PIC 9(9)      -- Customer ID
  02 WS-FRAUD-AUTH-RECORD                  -- Full auth detail (CIPAUDTY layout)
     COPY CIPAUDTY.
  02 WS-FRAUD-STATUS-RECORD                -- Action and result
     05 WS-FRD-ACTION        PIC X(01)     -- F=Report Fraud, R=Remove Fraud
     05 WS-FRD-UPDATE-STATUS PIC X(01)     -- S=Success, F=Failed (set by this pgm)
     05 WS-FRD-ACT-MSG       PIC X(50)     -- Result message (set by this pgm)
```

All PA-* field references in the PROCEDURE DIVISION (e.g., PA-CARD-NUM, PA-AUTH-TYPE, etc.) resolve to the CIPAUDTY fields within WS-FRAUD-AUTH-RECORD.

---

## DB2 SQL Operations

### DB2 Table: CARDDEMO.AUTHFRDS

This table stores fraud-flagged authorization records. Column correspondence to source fields (from SQL at lines 141–198):

| DB2 Column | Source Field | Notes |
|------------|-------------|-------|
| CARD_NUM | :CARD-NUM | From PA-CARD-NUM |
| AUTH_TS | TIMESTAMP_FORMAT(:AUTH-TS, 'YY-MM-DD HH24.MI.SSNNNNNN') | Built from auth date/time complement decode |
| AUTH_TYPE | :AUTH-TYPE | From PA-AUTH-TYPE |
| CARD_EXPIRY_DATE | :CARD-EXPIRY-DATE | From PA-CARD-EXPIRY-DATE |
| MESSAGE_TYPE | :MESSAGE-TYPE | From PA-MESSAGE-TYPE |
| MESSAGE_SOURCE | :MESSAGE-SOURCE | From PA-MESSAGE-SOURCE |
| AUTH_ID_CODE | :AUTH-ID-CODE | From PA-AUTH-ID-CODE |
| AUTH_RESP_CODE | :AUTH-RESP-CODE | From PA-AUTH-RESP-CODE |
| AUTH_RESP_REASON | :AUTH-RESP-REASON | From PA-AUTH-RESP-REASON |
| PROCESSING_CODE | :PROCESSING-CODE | From PA-PROCESSING-CODE |
| TRANSACTION_AMT | :TRANSACTION-AMT | From PA-TRANSACTION-AMT |
| APPROVED_AMT | :APPROVED-AMT | From PA-APPROVED-AMT |
| MERCHANT_CATAGORY_CODE | :MERCHANT-CATAGORY-CODE | From PA-MERCHANT-CATAGORY-CODE |
| ACQR_COUNTRY_CODE | :ACQR-COUNTRY-CODE | From PA-ACQR-COUNTRY-CODE |
| POS_ENTRY_MODE | :POS-ENTRY-MODE | From PA-POS-ENTRY-MODE |
| MERCHANT_ID | :MERCHANT-ID | From PA-MERCHANT-ID |
| MERCHANT_NAME | :MERCHANT-NAME | From PA-MERCHANT-NAME (VARCHAR) |
| MERCHANT_CITY | :MERCHANT-CITY | From PA-MERCHANT-CITY |
| MERCHANT_STATE | :MERCHANT-STATE | From PA-MERCHANT-STATE |
| MERCHANT_ZIP | :MERCHANT-ZIP | From PA-MERCHANT-ZIP |
| TRANSACTION_ID | :TRANSACTION-ID | From PA-TRANSACTION-ID |
| MATCH_STATUS | :MATCH-STATUS | From PA-MATCH-STATUS |
| AUTH_FRAUD | :AUTH-FRAUD | From WS-FRD-ACTION ('F' or 'R') |
| FRAUD_RPT_DATE | CURRENT DATE | DB2 special register |
| ACCT_ID | :ACCT-ID | From WS-ACCT-ID |
| CUST_ID | :CUST-ID | From WS-CUST-ID |

### INSERT Statement (lines 141–198)

```sql
INSERT INTO CARDDEMO.AUTHFRDS
    (CARD_NUM, AUTH_TS, AUTH_TYPE, CARD_EXPIRY_DATE, MESSAGE_TYPE,
     MESSAGE_SOURCE, AUTH_ID_CODE, AUTH_RESP_CODE, AUTH_RESP_REASON,
     PROCESSING_CODE, TRANSACTION_AMT, APPROVED_AMT, MERCHANT_CATAGORY_CODE,
     ACQR_COUNTRY_CODE, POS_ENTRY_MODE, MERCHANT_ID, MERCHANT_NAME,
     MERCHANT_CITY, MERCHANT_STATE, MERCHANT_ZIP, TRANSACTION_ID,
     MATCH_STATUS, AUTH_FRAUD, FRAUD_RPT_DATE, ACCT_ID, CUST_ID)
VALUES (
    :CARD-NUM,
    TIMESTAMP_FORMAT(:AUTH-TS, 'YY-MM-DD HH24.MI.SSNNNNNN'),
    :AUTH-TYPE, :CARD-EXPIRY-DATE, :MESSAGE-TYPE, :MESSAGE-SOURCE,
    :AUTH-ID-CODE, :AUTH-RESP-CODE, :AUTH-RESP-REASON, :PROCESSING-CODE,
    :TRANSACTION-AMT, :APPROVED-AMT, :MERCHANT-CATAGORY-CODE,
    :ACQR-COUNTRY-CODE, :POS-ENTRY-MODE, :MERCHANT-ID, :MERCHANT-NAME,
    :MERCHANT-CITY, :MERCHANT-STATE, :MERCHANT-ZIP, :TRANSACTION-ID,
    :MATCH-STATUS, :AUTH-FRAUD, CURRENT DATE, :ACCT-ID, :CUST-ID
)
```

### UPDATE Statement — FRAUD-UPDATE paragraph (lines 222–244)

Invoked when INSERT returns SQLCODE -803 (duplicate key):

```sql
UPDATE CARDDEMO.AUTHFRDS
   SET AUTH_FRAUD     = :AUTH-FRAUD,
       FRAUD_RPT_DATE = CURRENT DATE
 WHERE CARD_NUM = :CARD-NUM
   AND AUTH_TS  = TIMESTAMP_FORMAT(:AUTH-TS, 'YY-MM-DD HH24.MI.SSNNNNNN')
```

---

## CICS Commands

| Command | Location | Purpose |
|---------|----------|---------|
| EXEC CICS ASKTIME ABSTIME | MAIN-PARA (line 91) | Get current timestamp |
| EXEC CICS FORMATTIME MMDDYY DATESEP | MAIN-PARA (line 95) | Format current date as MM/DD/YY |
| EXEC CICS RETURN | MAIN-PARA (line 218) | Return to caller (COPAUS1C) |

---

## Program Flow — PROCEDURE DIVISION

### MAIN-PARA (line 88) — Linear execution, no paragraphs called except FRAUD-UPDATE

```
1. EXEC CICS ASKTIME; EXEC CICS FORMATTIME
   -> WS-CUR-DATE = current date in MMDDYY format
   -> MOVE WS-CUR-DATE to PA-FRAUD-RPT-DATE

2. Build WS-AUTH-TS from PA-AUTH-ORIG-DATE fields:
   MOVE PA-AUTH-ORIG-DATE(1:2) to WS-AUTH-YY
   MOVE PA-AUTH-ORIG-DATE(3:2) to WS-AUTH-MM
   MOVE PA-AUTH-ORIG-DATE(5:2) to WS-AUTH-DD

3. Decode auth time from complement:
   COMPUTE WS-AUTH-TIME = 999999999 - PA-AUTH-TIME-9C
   MOVE WS-AUTH-TIME-AN(1:2) to WS-AUTH-HH
   MOVE WS-AUTH-TIME-AN(3:2) to WS-AUTH-MI
   MOVE WS-AUTH-TIME-AN(5:2) to WS-AUTH-SS
   MOVE WS-AUTH-TIME-AN(7:3) to WS-AUTH-SSS
   -> WS-AUTH-TS now = "YY-MM-DD HH.MI.SSSSSNNN000"

4. Map all PA-* fields and WS-ACCT-ID/WS-CUST-ID to DB2 host variables

5. EXEC SQL INSERT INTO CARDDEMO.AUTHFRDS ...

6. IF SQLCODE = 0:
       SET WS-FRD-UPDT-SUCCESS
       MOVE 'ADD SUCCESS' to WS-FRD-ACT-MSG
   ELSE IF SQLCODE = -803:
       PERFORM FRAUD-UPDATE
   ELSE:
       SET WS-FRD-UPDT-FAILED
       Build error message from SQLCODE + SQLSTATE into WS-FRD-ACT-MSG

7. EXEC CICS RETURN
```

### FRAUD-UPDATE (line 221)

```
EXEC SQL UPDATE CARDDEMO.AUTHFRDS
   SET AUTH_FRAUD = :AUTH-FRAUD, FRAUD_RPT_DATE = CURRENT DATE
 WHERE CARD_NUM = :CARD-NUM AND AUTH_TS = TIMESTAMP_FORMAT(...)

IF SQLCODE = 0:
    SET WS-FRD-UPDT-SUCCESS; MOVE 'UPDT SUCCESS' to WS-FRD-ACT-MSG
ELSE:
    SET WS-FRD-UPDT-FAILED
    Build error message from SQLCODE + SQLSTATE into WS-FRD-ACT-MSG
```

---

## Timestamp Construction

PA-AUTH-ORIG-DATE is stored in IMS as YYMMDD (6 chars). PA-AUTH-TIME-9C is the complement encoding: `999999999 - time-with-milliseconds`. Decoding steps:

```
WS-AUTH-TIME (numeric) = 999999999 - PA-AUTH-TIME-9C
WS-AUTH-TIME-AN (redefines, PIC X(09)) is then parsed as:
  positions 1-2: HH
  positions 3-4: MI
  positions 5-6: SS
  positions 7-9: SSS (milliseconds)

WS-AUTH-TS assembles to: "YY-MM-DD HH.MI.SSSSSNNN000"
  (the '000' FILLER at WS-AUTH-SSS+3 pads to 6 fractional digits for DB2 TIMESTAMP)
```

The DB2 TIMESTAMP_FORMAT mask `'YY-MM-DD HH24.MI.SSNNNNNN'` matches this format.

---

## Error Handling

| Condition | WS-FRD-UPDATE-STATUS | WS-FRD-ACT-MSG |
|-----------|----------------------|----------------|
| INSERT SQLCODE = 0 | S (SUCCESS) | 'ADD SUCCESS' |
| INSERT SQLCODE = -803 (duplicate) | Calls FRAUD-UPDATE | 'UPDT SUCCESS' or error message |
| FRAUD-UPDATE SQLCODE = 0 | S (SUCCESS) | 'UPDT SUCCESS' |
| Any other SQLCODE | F (FAILED) | ' SYSTEM ERROR DB2: CODE:nnnnnn, STATE: nnnnnnnnn' |

The caller (COPAUS1C) checks WS-FRD-UPDATE-STATUS on return. If FAILED, COPAUS1C performs a SYNCPOINT ROLLBACK to undo the IMS REPL update.

---

## Transaction Flow Participation

COPAUS2C does not have its own CICS transaction. It is a LINKed sub-program within COPAUS1C's CPVD transaction context. It inherits the UOW of the calling task.

```
COPAUS1C (CPVD) --[CICS LINK]--> COPAUS2C
                                      |-- DB2 INSERT/UPDATE CARDDEMO.AUTHFRDS
                <--[CICS RETURN]------
```

After return, COPAUS1C either:
- Performs IMS REPL on PAUTDTL1 (if success)
- Performs CICS SYNCPOINT ROLLBACK (if failure)

---

## Inter-Program Interactions

| Program | Relationship | Method |
|---------|-------------|--------|
| COPAUS1C | Caller | CICS LINK |
| CARDDEMO.AUTHFRDS | DB2 table | INSERT/UPDATE |
