# Technical Specification: COPAUS2C
## Authorization Fraud Marking Program (DB2)

---

### 1. Program Overview

| Attribute       | Value                                              |
|-----------------|----------------------------------------------------|
| Program Name    | COPAUS2C                                           |
| Source File     | cbl/COPAUS2C.cbl                                   |
| Program Type    | CICS COBOL — DB2                                   |
| Function        | Mark or Remove Fraud Flag on Authorization; DB2 Write |
| Transaction ID  | CPVD (same as COPAUS1C; invoked via LINK only)    |
| Author          | AWS                                                |
| DB2 Table       | CARDDEMO.AUTHFRDS                                  |
| Called By       | COPAUS1C (EXEC CICS LINK)                          |
| DB2 Entry       | AWS01PLN (DEFINE DB2ENTRY in CRDDEMO2.csd)         |
| DB2 Transaction | CPVDTRAN (DEFINE DB2TRAN for CPVD)                |

**Purpose:** COPAUS2C is a CICS-linked subprogram responsible solely for writing fraud information to the DB2 AUTHFRDS table. It is not invoked by a terminal transaction directly. It receives all necessary data through its COMMAREA (passed from COPAUS1C). It converts the IMS-format timestamp to a DB2 TIMESTAMP string, populates all DCLAUTHFRDS host variables, and performs either an INSERT (new fraud record) or UPDATE (existing fraud record toggle).

---

### 2. Program Flow

```
MAIN-PARA
  |
  +-- EXEC CICS ASKTIME NOHANDLE -> WS-ABS-TIME
  +-- EXEC CICS FORMATTIME MMDDYY(WS-CUR-DATE) DATESEP NOHANDLE
  +-- Move WS-CUR-DATE to PA-FRAUD-RPT-DATE (sets date in commarea)
  |
  +-- Convert IMS timestamp to DB2 timestamp format:
  |     PA-AUTH-ORIG-DATE(1:2) -> WS-AUTH-YY
  |     PA-AUTH-ORIG-DATE(3:2) -> WS-AUTH-MM
  |     PA-AUTH-ORIG-DATE(5:2) -> WS-AUTH-DD
  |     WS-AUTH-TIME = 999999999 - PA-AUTH-TIME-9C
  |     WS-AUTH-HH = WS-AUTH-TIME-AN(1:2)
  |     WS-AUTH-MI = WS-AUTH-TIME-AN(3:2)
  |     WS-AUTH-SS = WS-AUTH-TIME-AN(5:2)
  |     WS-AUTH-SSS = WS-AUTH-TIME-AN(7:3)
  |     WS-AUTH-TS = "YY-MM-DD HH.MI.SSSSSNNN000"
  |
  +-- Populate DCLAUTHFRDS host variables from CIPAUDTY segment fields
  |
  +-- EXEC SQL INSERT INTO CARDDEMO.AUTHFRDS (all 26 columns) VALUES (host vars)
  |     [SQLCODE = 0]  -> WS-FRD-UPDT-SUCCESS; WS-FRD-ACT-MSG = 'ADD SUCCESS'
  |     [SQLCODE = -803] -> FRAUD-UPDATE (duplicate key -> UPDATE instead)
  |     [other SQLCODE] -> WS-FRD-UPDT-FAILED; format SQLCODE/SQLSTATE into msg
  |
  +-- EXEC CICS RETURN
  |
  FRAUD-UPDATE (only if SQLCODE = -803):
  +-- EXEC SQL UPDATE CARDDEMO.AUTHFRDS
  |       SET AUTH_FRAUD = :AUTH-FRAUD, FRAUD_RPT_DATE = CURRENT DATE
  |       WHERE CARD_NUM = :CARD-NUM AND AUTH_TS = TIMESTAMP_FORMAT(...)
  |     [SQLCODE = 0]  -> WS-FRD-UPDT-SUCCESS; WS-FRD-ACT-MSG = 'UPDT SUCCESS'
  |     [other SQLCODE] -> WS-FRD-UPDT-FAILED; format error message
```

---

### 3. Data Structures

#### 3.1 Working Storage (cbl/COPAUS2C.cbl, lines 32–60)

| Field             | Picture            | Description                                      |
|-------------------|--------------------|--------------------------------------------------|
| WS-PGMNAME        | PIC X(08)          | 'COPAUS2C'                                       |
| WS-LENGTH         | PIC S9(4) COMP     | Length work field                                |
| WS-AUTH-TIME      | PIC 9(09)          | Numeric work field for time inversion            |
| WS-AUTH-TIME-AN   | PIC X(09) (REDEFINES WS-AUTH-TIME) | Character view of time        |
| WS-AUTH-TS        | Composite 26-char  | DB2 TIMESTAMP formatted string                   |
| WS-ERR-FLG        | PIC X(01)          | Error flag                                       |
| WS-SQLCODE        | PIC +9(06)         | Formatted SQL return code for messages           |
| WS-SQLSTATE       | PIC +9(09)         | Formatted SQL state for messages                 |
| WS-ABS-TIME       | PIC S9(15) COMP-3  | CICS absolute time                               |
| WS-CUR-DATE       | PIC X(08)          | CICS-formatted current date MM/DD/YY             |

#### 3.2 WS-AUTH-TS Structure (lines 38–51)

The DB2 TIMESTAMP host variable is built character by character:

```
WS-AUTH-TS:
  WS-AUTH-YY   PIC X(02)    -- year (YY)
  FILLER       PIC X(01)    VALUE '-'
  WS-AUTH-MM   PIC X(02)    -- month (MM)
  FILLER       PIC X(01)    VALUE '-'
  WS-AUTH-DD   PIC X(02)    -- day (DD)
  FILLER       PIC X(01)    VALUE ' '
  WS-AUTH-HH   PIC X(02)    -- hour (HH)
  FILLER       PIC X(01)    VALUE '.'
  WS-AUTH-MI   PIC X(02)    -- minute (MI)
  FILLER       PIC X(01)    VALUE '.'
  WS-AUTH-SS   PIC X(02)    -- second (SS)
  WS-AUTH-SSS  PIC X(03)    -- milliseconds (SSS)
  FILLER       PIC X(03)    VALUE '000'
```

Total length: 2+1+2+1+2+1+2+1+2+1+2+3+3 = 23 characters. This is passed to DB2 via TIMESTAMP_FORMAT with pattern 'YY-MM-DD HH24.MI.SSNNNNNN'.

#### 3.3 LINKAGE SECTION / COMMAREA (lines 73–86)

The COMMAREA layout matches WS-FRAUD-DATA in COPAUS1C:

| Level/Field              | Picture  | Description                                        |
|--------------------------|----------|----------------------------------------------------|
| 02 WS-ACCT-ID            | PIC 9(11)| Account ID                                         |
| 02 WS-CUST-ID            | PIC 9(9) | Customer ID                                        |
| 02 WS-FRAUD-AUTH-RECORD  | COPY CIPAUDTY | Full 200-byte PAUTDTL1 segment (as PIC X(200) in caller) |
| 05 WS-FRD-ACTION         | PIC X(01)| 'F'=report fraud, 'R'=remove fraud (input)        |
| 05 WS-FRD-UPDATE-STATUS  | PIC X(01)| 'S'=success, 'F'=failed (output)                  |
| 05 WS-FRD-ACT-MSG        | PIC X(50)| Status/error message (output)                     |

**Note:** WS-FRAUD-AUTH-RECORD is typed as COPY CIPAUDTY in COPAUS2C's linkage section, so all PA- prefixed fields from the CIPAUDTY copybook are directly addressable within the received COMMAREA.

---

### 4. DB2 Commands

#### 4.1 SQL INCLUDE Statements (lines 65–70)

```cobol
EXEC SQL INCLUDE SQLCA END-EXEC.
EXEC SQL INCLUDE AUTHFRDS END-EXEC.
```

AUTHFRDS.dcl provides the DCLAUTHFRDS host variable structure and the EXEC SQL DECLARE TABLE statement for CARDDEMO.AUTHFRDS.

#### 4.2 INSERT Statement (lines 141–198)

Full INSERT of all 26 columns into CARDDEMO.AUTHFRDS. The AUTH_TS column uses the TIMESTAMP_FORMAT scalar function:

```sql
INSERT INTO CARDDEMO.AUTHFRDS
  (CARD_NUM, AUTH_TS, AUTH_TYPE, CARD_EXPIRY_DATE, MESSAGE_TYPE,
   MESSAGE_SOURCE, AUTH_ID_CODE, AUTH_RESP_CODE, AUTH_RESP_REASON,
   PROCESSING_CODE, TRANSACTION_AMT, APPROVED_AMT,
   MERCHANT_CATAGORY_CODE, ACQR_COUNTRY_CODE, POS_ENTRY_MODE,
   MERCHANT_ID, MERCHANT_NAME, MERCHANT_CITY, MERCHANT_STATE,
   MERCHANT_ZIP, TRANSACTION_ID, MATCH_STATUS, AUTH_FRAUD,
   FRAUD_RPT_DATE, ACCT_ID, CUST_ID)
VALUES
  (:CARD-NUM,
   TIMESTAMP_FORMAT(:AUTH-TS, 'YY-MM-DD HH24.MI.SSNNNNNN'),
   :AUTH-TYPE, :CARD-EXPIRY-DATE, :MESSAGE-TYPE, :MESSAGE-SOURCE,
   :AUTH-ID-CODE, :AUTH-RESP-CODE, :AUTH-RESP-REASON, :PROCESSING-CODE,
   :TRANSACTION-AMT, :APPROVED-AMT, :MERCHANT-CATAGORY-CODE,
   :ACQR-COUNTRY-CODE, :POS-ENTRY-MODE, :MERCHANT-ID, :MERCHANT-NAME,
   :MERCHANT-CITY, :MERCHANT-STATE, :MERCHANT-ZIP, :TRANSACTION-ID,
   :MATCH-STATUS, :AUTH-FRAUD, CURRENT DATE, :ACCT-ID, :CUST-ID)
```

**Note:** FRAUD_RPT_DATE uses DB2 CURRENT DATE (server-side date), not the host variable WS-CUR-DATE. However, PA-FRAUD-RPT-DATE in the IMS segment is set from WS-CUR-DATE (CICS FORMATTIME date) at the start of MAIN-PARA.

#### 4.3 UPDATE Statement — FRAUD-UPDATE Paragraph (lines 221–243)

```sql
UPDATE CARDDEMO.AUTHFRDS
  SET AUTH_FRAUD = :AUTH-FRAUD,
      FRAUD_RPT_DATE = CURRENT DATE
  WHERE CARD_NUM = :CARD-NUM
    AND AUTH_TS = TIMESTAMP_FORMAT(:AUTH-TS, 'YY-MM-DD HH24.MI.SSNNNNNN')
```

This is executed only when the INSERT fails with SQLCODE -803 (unique constraint violation, meaning the record already exists).

---

### 5. Timestamp Conversion Logic

The IMS key stores time in complement form. COPAUS2C reverses this to reconstruct the original time:

```
PA-AUTH-TIME-9C (IMS key, COMP-3 9-digit) stores: 999999999 - HHMMSSMMM
Therefore: original_time = 999999999 - PA-AUTH-TIME-9C
```

Line 107: `COMPUTE WS-AUTH-TIME = 999999999 - PA-AUTH-TIME-9C`

The result is then interpreted as a 9-digit string HHMMSSMMM via the REDEFINES WS-AUTH-TIME-AN.

---

### 6. Host Variable Mapping (lines 113–139)

All host variables for the INSERT are populated from the CIPAUDTY segment fields in the COMMAREA:

| DB2 Host Variable      | Source Field (CIPAUDTY)          |
|------------------------|----------------------------------|
| CARD-NUM               | PA-CARD-NUM                      |
| AUTH-TS                | WS-AUTH-TS (computed)            |
| AUTH-TYPE              | PA-AUTH-TYPE                     |
| CARD-EXPIRY-DATE       | PA-CARD-EXPIRY-DATE              |
| MESSAGE-TYPE           | PA-MESSAGE-TYPE                  |
| MESSAGE-SOURCE         | PA-MESSAGE-SOURCE                |
| AUTH-ID-CODE           | PA-AUTH-ID-CODE                  |
| AUTH-RESP-CODE         | PA-AUTH-RESP-CODE                |
| AUTH-RESP-REASON       | PA-AUTH-RESP-REASON              |
| PROCESSING-CODE        | PA-PROCESSING-CODE               |
| TRANSACTION-AMT        | PA-TRANSACTION-AMT               |
| APPROVED-AMT           | PA-APPROVED-AMT                  |
| MERCHANT-CATAGORY-CODE | PA-MERCHANT-CATAGORY-CODE        |
| ACQR-COUNTRY-CODE      | PA-ACQR-COUNTRY-CODE             |
| POS-ENTRY-MODE         | PA-POS-ENTRY-MODE                |
| MERCHANT-ID            | PA-MERCHANT-ID                   |
| MERCHANT-NAME          | PA-MERCHANT-NAME (VARCHAR(22))   |
| MERCHANT-CITY          | PA-MERCHANT-CITY                 |
| MERCHANT-STATE         | PA-MERCHANT-STATE                |
| MERCHANT-ZIP           | PA-MERCHANT-ZIP                  |
| TRANSACTION-ID         | PA-TRANSACTION-ID                |
| MATCH-STATUS           | PA-MATCH-STATUS                  |
| AUTH-FRAUD             | WS-FRD-ACTION ('F' or 'R')       |
| FRAUD_RPT_DATE         | CURRENT DATE (DB2 function)      |
| ACCT-ID                | WS-ACCT-ID (from commarea)       |
| CUST-ID                | WS-CUST-ID (from commarea)       |

**MERCHANT-NAME is VARCHAR:** DCLAUTHFRDS defines MERCHANT-NAME as a 49-level pair (MERCHANT-NAME-LEN + MERCHANT-NAME-TEXT). Line 130 sets MERCHANT-NAME-LEN = LENGTH OF PA-MERCHANT-NAME (22).

---

### 7. Error Handling

| Condition                | Handling                                                              |
|--------------------------|-----------------------------------------------------------------------|
| INSERT SQLCODE = 0       | WS-FRD-UPDT-SUCCESS; WS-FRD-ACT-MSG = 'ADD SUCCESS'                 |
| INSERT SQLCODE = -803    | Call FRAUD-UPDATE paragraph (duplicate key → update instead)         |
| INSERT other SQLCODE     | WS-FRD-UPDT-FAILED; WS-FRD-ACT-MSG = ' SYSTEM ERROR DB2: CODE:nnnnnn, STATE: nnnnnnnnn' |
| UPDATE SQLCODE = 0       | WS-FRD-UPDT-SUCCESS; WS-FRD-ACT-MSG = 'UPDT SUCCESS'                |
| UPDATE other SQLCODE     | WS-FRD-UPDT-FAILED; WS-FRD-ACT-MSG = ' UPDT ERROR DB2: CODE:nnnnnn, STATE: nnnnnnnnn' |

The program does not perform CICS ROLLBACK itself — it relies on the calling program (COPAUS1C) to issue EXEC CICS SYNCPOINT ROLLBACK if WS-FRD-UPDT-FAILED is returned.

**Two-phase commit:** COPAUS2C operates under the same CICS UOW as COPAUS1C because it is invoked via EXEC CICS LINK (not a new task). The DB2 operation in COPAUS2C and the subsequent IMS REPL in COPAUS1C are therefore both backed out by a single EXEC CICS SYNCPOINT ROLLBACK issued in COPAUS1C if either fails.

---

### 8. Business Rules

1. The primary key of AUTHFRDS is (CARD_NUM, AUTH_TS). The first time an authorization is flagged as fraud, an INSERT is attempted.
2. If the record already exists (SQLCODE -803), an UPDATE is performed to change only AUTH_FRAUD and FRAUD_RPT_DATE — all other columns retain their original values.
3. AUTH_FRAUD value comes from WS-FRD-ACTION: 'F' = fraud confirmed, 'R' = fraud removed.
4. PA-FRAUD-RPT-DATE in the IMS record and FRAUD_RPT_DATE in DB2 reflect the current date, but via different mechanisms: CICS FORMATTIME (MMDDYY with DATESEP) for IMS vs. DB2 CURRENT DATE for the DB2 column.

**[UNRESOLVED]** The DB2 schema shown in AUTHFRDS.ddl uses schema name CARDDEMO. The README (line 150) states: "Update the DB2 schema name in the program COPAUS2C.cbl to match your environment." The hardcoded schema 'CARDDEMO' at lines 142 and 223 must be changed at installation time to match the target DB2 schema.

---

### 9. Called Programs

None. COPAUS2C issues EXEC CICS RETURN to return to its caller (COPAUS1C) without invoking any other programs.

---

### 10. I/O Specification

| Direction | Resource            | Operation | Data                                          |
|-----------|---------------------|-----------|-----------------------------------------------|
| Input     | DFHCOMMAREA         | LINK      | WS-FRAUD-DATA (account ID, customer ID, full PAUTDTL1 segment, action flag) |
| Output    | DFHCOMMAREA         | LINK RETURN | WS-FRD-UPDATE-STATUS, WS-FRD-ACT-MSG, PA-FRAUD-RPT-DATE (set in the segment) |
| Output    | DB2 CARDDEMO.AUTHFRDS | INSERT  | Full fraud record (26 columns)                |
| Output    | DB2 CARDDEMO.AUTHFRDS | UPDATE  | AUTH_FRAUD + FRAUD_RPT_DATE only (on duplicate) |

---
