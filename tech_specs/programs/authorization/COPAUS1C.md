# Technical Specification: COPAUS1C
## Authorization Detail View Program

---

### 1. Program Overview

| Attribute       | Value                                              |
|-----------------|----------------------------------------------------|
| Program Name    | COPAUS1C                                           |
| Source File     | cbl/COPAUS1C.cbl                                   |
| Program Type    | CICS COBOL — IMS + BMS                            |
| Function        | Detail View and Fraud Marking of Authorization     |
| Transaction ID  | CPVD                                               |
| Author          | AWS                                                |
| PSB Used        | PSBPAUTB                                           |
| IMS PCB         | PAUT-PCB-NUM = 1 (DBPAUTP0, PROCOPT=AP)           |
| BMS Mapset      | COPAU01, Map COPAU1A                               |
| Called Program  | COPAUS2C (fraud DB2 update via EXEC CICS LINK)     |

**Purpose:** COPAUS1C displays the full detail of a single pending authorization record stored in IMS. It shows all transaction fields, merchant details, approval/decline status, and fraud indicators. The operator can use PF5 to toggle fraud status (mark or remove fraud flag) and PF8 to advance to the next authorization record for the account. Fraud marking triggers a CICS LINK to COPAUS2C which performs the DB2 INSERT/UPDATE.

---

### 2. Program Flow

```
MAIN-PARA
  |
  +-- Initialize: ERR-FLG-OFF, SEND-ERASE-YES
  |   Clear WS-MESSAGE and ERRMSGO
  |
  +-- [EIBCALEN = 0]
  |     Initialize CARDDEMO-COMMAREA
  |     MOVE WS-PGM-AUTH-SMRY to CDEMO-TO-PROGRAM
  |     RETURN-TO-PREV-SCREEN (XCTL to COPAUS0C)
  |
  +-- [EIBCALEN > 0]
  |     Move DFHCOMMAREA to CARDDEMO-COMMAREA
  |     Clear CDEMO-CPVD-FRAUD-DATA
  |     [NOT CDEMO-PGM-REENTER -- Initial entry from COPAUS0C]
  |       Set CDEMO-PGM-REENTER
  |       PROCESS-ENTER-KEY
  |       SEND-AUTHVIEW-SCREEN
  |     [CDEMO-PGM-REENTER -- Subsequent keys]
  |       RECEIVE-AUTHVIEW-SCREEN
  |       EVALUATE EIBAID:
  |         DFHENTER -> PROCESS-ENTER-KEY -> SEND-AUTHVIEW-SCREEN
  |         DFHPF3   -> RETURN-TO-PREV-SCREEN (XCTL to COPAUS0C)
  |         DFHPF5   -> MARK-AUTH-FRAUD    -> SEND-AUTHVIEW-SCREEN
  |         DFHPF8   -> PROCESS-PF8-KEY    -> SEND-AUTHVIEW-SCREEN
  |         OTHER    -> PROCESS-ENTER-KEY  -> 'Invalid key' -> SEND-AUTHVIEW-SCREEN
  |
  +-- EXEC CICS RETURN TRANSID(CPVD) COMMAREA(CARDDEMO-COMMAREA)
```

#### PROCESS-ENTER-KEY
```
  Clear COPAU1AO
  [CDEMO-ACCT-ID is numeric AND CDEMO-CPVD-PAU-SELECTED not spaces/low-values]
    Move CDEMO-ACCT-ID to WS-ACCT-ID
    Move CDEMO-CPVD-PAU-SELECTED to WS-AUTH-KEY
    READ-AUTH-RECORD
      SCHEDULE-PSB (EXEC DLI SCHD)
      EXEC DLI GU PAUTSUM0 WHERE(ACCNTID = PA-ACCT-ID)
      EXEC DLI GNP PAUTDTL1 WHERE(PAUT9CTS = PA-AUTHORIZATION-KEY)
    If IMS-PSB-SCHD: TAKE-SYNCPOINT; set IMS-PSB-NOT-SCHD
  Else: ERR-FLG-ON
  POPULATE-AUTH-DETAILS
```

#### MARK-AUTH-FRAUD
```
  Move CDEMO-ACCT-ID to WS-ACCT-ID
  Move CDEMO-CPVD-PAU-SELECTED to WS-AUTH-KEY
  READ-AUTH-RECORD (read existing record)
  [PA-FRAUD-CONFIRMED] -> set PA-FRAUD-REMOVED; set WS-REMOVE-FRAUD
  [else]               -> set PA-FRAUD-CONFIRMED; set WS-REPORT-FRAUD
  Move PENDING-AUTH-DETAILS to WS-FRAUD-AUTH-RECORD
  Move CDEMO-ACCT-ID to WS-FRD-ACCT-ID
  Move CDEMO-CUST-ID to WS-FRD-CUST-ID
  EXEC CICS LINK PROGRAM(COPAUS2C) COMMAREA(WS-FRAUD-DATA)
  [EIBRESP = NORMAL]
    [WS-FRD-UPDT-SUCCESS] -> UPDATE-AUTH-DETAILS (IMS REPL)
    [WS-FRD-UPDT-FAILED]  -> Move WS-FRD-ACT-MSG to WS-MESSAGE; ROLL-BACK
  [EIBRESP != NORMAL] -> ROLL-BACK
  Move PA-AUTHORIZATION-KEY to CDEMO-CPVD-PAU-SELECTED
  POPULATE-AUTH-DETAILS
```

#### PROCESS-PF8-KEY
```
  Move CDEMO-ACCT-ID to WS-ACCT-ID
  Move CDEMO-CPVD-PAU-SELECTED to WS-AUTH-KEY
  READ-AUTH-RECORD (position to current)
  READ-NEXT-AUTH-RECORD (GNP unqualified PAUTDTL1)
  If IMS-PSB-SCHD: TAKE-SYNCPOINT; set IMS-PSB-NOT-SCHD
  [AUTHS-EOF] -> SEND-ERASE-NO; WS-MESSAGE = 'Already at last Authorization...'
  [else] -> Move PA-AUTHORIZATION-KEY to CDEMO-CPVD-PAU-SELECTED
          -> POPULATE-AUTH-DETAILS
```

---

### 3. Data Structures

#### 3.1 Working Storage Key Fields (cbl/COPAUS1C.cbl, lines 32–54)

| Field                  | Picture               | Value       | Description                                |
|------------------------|-----------------------|-------------|--------------------------------------------|
| WS-PGM-AUTH-DTL        | PIC X(08)             | 'COPAUS1C'  | This program                               |
| WS-PGM-AUTH-SMRY       | PIC X(08)             | 'COPAUS0C'  | Summary program (PF3 target)               |
| WS-PGM-AUTH-FRAUD      | PIC X(08)             | 'COPAUS2C'  | Fraud update program (LINK target)         |
| WS-CICS-TRANID         | PIC X(04)             | 'CPVD'      | This transaction                           |
| WS-ERR-FLG             | PIC X(01)             | 'N'         | Error flag                                 |
| WS-AUTHS-EOF           | PIC X(01)             | 'N'         | End-of-IMS flag                            |
| WS-SEND-ERASE-FLG      | PIC X(01)             | 'Y'         | ERASE on send flag                         |
| WS-ACCT-ID             | PIC 9(11)             |             | Current account ID                         |
| WS-AUTH-KEY            | PIC X(08)             |             | Authorization key being displayed          |
| WS-AUTH-AMT            | PIC -zzzzzzz9.99      |             | Formatted approved amount                  |
| WS-AUTH-DATE           | PIC X(08)             | '00/00/00'  | Formatted date MM/DD/YY                    |
| WS-AUTH-TIME           | PIC X(08)             | '00:00:00'  | Formatted time HH:MM:SS                    |

#### 3.2 Decline Reason Table (lines 57–73)

An embedded 10-entry table in WS-DECLINE-REASON-TABLE, redefined as WS-DECLINE-REASON-TAB OCCURS 10 TIMES with ASCENDING KEY IS DECL-CODE INDEXED BY WS-DECL-RSN-IDX. Used with SEARCH ALL for binary search.

| Entry | DECL-CODE | DECL-DESC           |
|-------|-----------|---------------------|
| 1     | 0000      | APPROVED            |
| 2     | 3100      | INVALID CARD        |
| 3     | 4100      | INSUFFICNT FUND     |
| 4     | 4200      | CARD NOT ACTIVE     |
| 5     | 4300      | ACCOUNT CLOSED      |
| 6     | 4400      | EXCED DAILY LMT     |
| 7     | 5100      | CARD FRAUD          |
| 8     | 5200      | MERCHANT FRAUD      |
| 9     | 5300      | LOST CARD           |
| 10    | 9000      | UNKNOWN             |

#### 3.3 COMMAREA Extension (lines 109–120, after COPY COCOM01Y)

| Field                       | Picture              | Description                                     |
|-----------------------------|----------------------|-------------------------------------------------|
| CDEMO-CPVD-PAU-SEL-FLG      | PIC X(01)            | Selection flag from COPAUS0C                    |
| CDEMO-CPVD-PAU-SELECTED     | PIC X(08)            | Key of authorization being displayed            |
| CDEMO-CPVD-PAUKEY-PREV-PG   | PIC X(08) OCCURS 20  | Previous page keys (carried from COPAUS0C)      |
| CDEMO-CPVD-PAUKEY-LAST      | PIC X(08)            | Last authorization key displayed in list        |
| CDEMO-CPVD-PAGE-NUM         | PIC S9(04) COMP      | Current page number from COPAUS0C               |
| CDEMO-CPVD-NEXT-PAGE-FLG    | PIC X(01)            | Forward page indicator from COPAUS0C            |
| CDEMO-CPVD-AUTH-KEYS        | PIC X(08) OCCURS 5   | 5 keys from the summary screen page             |
| CDEMO-CPVD-FRAUD-DATA       | PIC X(100)           | Fraud communication (cleared on each entry)     |

#### 3.4 Fraud Communication Area (lines 93–104)

WS-FRAUD-DATA is the COMMAREA passed to COPAUS2C:

| Field                    | Picture  | Description                                         |
|--------------------------|----------|-----------------------------------------------------|
| WS-FRD-ACCT-ID           | PIC 9(11)| Account ID for the fraud record                     |
| WS-FRD-CUST-ID           | PIC 9(9) | Customer ID for the fraud record                    |
| WS-FRAUD-AUTH-RECORD     | PIC X(200)| Full PAUTDTL1 segment data (CIPAUDTY layout)       |
| WS-FRD-ACTION            | PIC X(01)| 'F'=report fraud, 'R'=remove fraud                 |
| WS-FRD-UPDATE-STATUS     | PIC X(01)| 'S'=success, 'F'=failed (returned by COPAUS2C)     |
| WS-FRD-ACT-MSG           | PIC X(50)| Status/error message (returned by COPAUS2C)         |

---

### 4. CICS, IMS, and MQ Commands

#### 4.1 CICS Commands

| Command                  | Location               | Parameters / Notes                                                     |
|--------------------------|------------------------|------------------------------------------------------------------------|
| EXEC CICS SEND MAP       | SEND-AUTHVIEW-SCREEN   | MAP('COPAU1A') MAPSET('COPAU01') FROM(COPAU1AO) ERASE CURSOR (or no ERASE) |
| EXEC CICS RECEIVE MAP    | RECEIVE-AUTHVIEW-SCREEN| MAP('COPAU1A') MAPSET('COPAU01') INTO(COPAU1AI) NOHANDLE               |
| EXEC CICS LINK           | MARK-AUTH-FRAUD        | PROGRAM(WS-PGM-AUTH-FRAUD='COPAUS2C') COMMAREA(WS-FRAUD-DATA) NOHANDLE |
| EXEC CICS XCTL           | RETURN-TO-PREV-SCREEN  | PROGRAM(CDEMO-TO-PROGRAM) COMMAREA(CARDDEMO-COMMAREA)                  |
| EXEC CICS SYNCPOINT      | TAKE-SYNCPOINT         | Commit IMS changes after detail INSERT or after PSB use                |
| EXEC CICS SYNCPOINT ROLLBACK | ROLL-BACK          | Rollback if fraud DB2 update fails or LINK fails                       |
| EXEC CICS RETURN         | MAIN-PARA              | TRANSID(CPVD) COMMAREA(CARDDEMO-COMMAREA)                              |

#### 4.2 IMS DLI Commands

| Command       | Paragraph          | Segment    | Qualifier                                    | Purpose                                      |
|---------------|--------------------|------------|----------------------------------------------|----------------------------------------------|
| EXEC DLI SCHD | SCHEDULE-PSB       | —          | PSB((PSB-NAME='PSBPAUTB')) NODHABEND         | Schedule PSB; handles TC by TERM + re-SCHD   |
| EXEC DLI TERM | SCHEDULE-PSB       | —          | — (only on TC condition)                     | Release existing PSB before re-scheduling    |
| EXEC DLI GU   | READ-AUTH-RECORD   | PAUTSUM0   | WHERE(ACCNTID = PA-ACCT-ID)                  | Read summary (parent) for account            |
| EXEC DLI GNP  | READ-AUTH-RECORD   | PAUTDTL1   | WHERE(PAUT9CTS = PA-AUTHORIZATION-KEY)       | Read specific detail record by key           |
| EXEC DLI GNP  | READ-NEXT-AUTH-RECORD | PAUTDTL1 | Unqualified                                 | Read next sibling detail record (PF8)        |
| EXEC DLI REPL | UPDATE-AUTH-DETAILS| PAUTDTL1   | —                                            | Replace detail record after fraud flag update|

---

### 5. Screen Interaction

Screen is COPAU1A within mapset COPAU01.

#### 5.1 Key Actions

| EIBAID   | Action                                                                          |
|----------|---------------------------------------------------------------------------------|
| DFHENTER | Re-read and re-display the currently selected authorization                     |
| DFHPF3   | XCTL back to COPAUS0C (summary screen)                                          |
| DFHPF5   | Toggle fraud status: mark as fraud (PA-FRAUD-CONFIRMED) or remove (PA-FRAUD-REMOVED) |
| DFHPF8   | Advance to next authorization detail record for same account                    |
| OTHER    | Display 'Invalid key' message, re-display current data                          |

#### 5.2 POPULATE-AUTH-DETAILS Field Mapping (lines 291–357)

| Map Field    | Source Field              | Format Notes                                       |
|--------------|---------------------------|----------------------------------------------------|
| CARDNUMO     | PA-CARD-NUM               | 16-char card number                                |
| AUTHDTO      | WS-AUTH-DATE              | Constructed as MM/DD/YY from PA-AUTH-ORIG-DATE     |
| AUTHTMO      | WS-AUTH-TIME              | Constructed as HH:MM:SS from PA-AUTH-ORIG-TIME     |
| AUTHAMTO     | WS-AUTH-AMT               | PIC -zzzzzzz9.99 of PA-APPROVED-AMT                |
| AUTHRSPO     | 'A' or 'D'                | Green if PA-AUTH-RESP-CODE='00', Red if not        |
| AUTHRSNO     | DECL-CODE + '-' + DECL-DESC| SEARCH ALL result: code 0000=APPROVED, etc.       |
| AUTHCDO      | PA-PROCESSING-CODE        | 6-digit processing code                            |
| POSEMDO      | PA-POS-ENTRY-MODE         | POS entry mode                                     |
| AUTHSRCO     | PA-MESSAGE-SOURCE         | Message source                                     |
| MCCCDO       | PA-MERCHANT-CATAGORY-CODE | Merchant category code                             |
| CRDEXPO      | PA-CARD-EXPIRY-DATE       | Formatted as MM/YY (slash inserted at position 3)  |
| AUTHTYPO     | PA-AUTH-TYPE              | Authorization type                                 |
| TRNIDO       | PA-TRANSACTION-ID         | Transaction ID                                     |
| AUTHMTCO     | PA-MATCH-STATUS           | Match status                                       |
| AUTHFRDO     | PA-AUTH-FRAUD + '-' + PA-FRAUD-RPT-DATE | 10 chars; '-' if no fraud    |
| MERNAMEO     | PA-MERCHANT-NAME          | Merchant name                                      |
| MERIDO       | PA-MERCHANT-ID            | Merchant ID                                        |
| MERCITYO     | PA-MERCHANT-CITY          | Merchant city                                      |
| MERSTO       | PA-MERCHANT-STATE         | Merchant state                                     |
| MERZIPO      | PA-MERCHANT-ZIP           | Merchant ZIP                                       |

**Color logic for AUTHRSPO:** DFHGREEN if PA-AUTH-RESP-CODE = '00' (approved); DFHRED otherwise (declined).

**Decline reason lookup:** SEARCH ALL WS-DECLINE-REASON-TAB on DECL-CODE = PA-AUTH-RESP-REASON. If no match found (AT END), code 9999 and 'ERROR' are displayed.

**Date construction (lines 297–303):**
- PA-AUTH-ORIG-DATE is YYMMDD (6 chars). Fields extracted: YY=positions 1:2, MM=positions 3:2, DD=positions 5:2
- Displayed as MM/DD/YY

**Fraud display (lines 344–350):**
- If PA-FRAUD-CONFIRMED or PA-FRAUD-REMOVED: AUTHFRDO = PA-AUTH-FRAUD + '-' + PA-FRAUD-RPT-DATE
- Otherwise: AUTHFRDO = '-'

---

### 6. Called Programs

| Program  | Call Method      | COMMAREA Structure   | Purpose                                        |
|----------|------------------|----------------------|------------------------------------------------|
| COPAUS2C | EXEC CICS LINK   | WS-FRAUD-DATA (263 bytes: 11+9+200+1+1+50) | Insert or update DB2 AUTHFRDS fraud record |
| COPAUS0C | EXEC CICS XCTL   | CARDDEMO-COMMAREA    | Return to summary screen (PF3)                 |

**Two-phase fraud commit sequence:**
1. COPAUS1C reads auth detail from IMS
2. COPAUS1C flags the detail record in memory (PA-FRAUD-CONFIRMED or PA-FRAUD-REMOVED)
3. COPAUS1C LINKs to COPAUS2C which performs DB2 INSERT/UPDATE on AUTHFRDS
4. COPAUS2C returns WS-FRD-UPDATE-STATUS = 'S' or 'F'
5. If success: COPAUS1C performs EXEC DLI REPL on PAUTDTL1 and EXEC CICS SYNCPOINT
6. If failure: COPAUS1C performs EXEC CICS SYNCPOINT ROLLBACK

---

### 7. Error Handling

| Condition                              | Response                                                          |
|----------------------------------------|-------------------------------------------------------------------|
| EIBCALEN = 0 (direct invocation)       | XCTL back to COPAUS0C immediately                                 |
| CDEMO-ACCT-ID not numeric or CPVD-PAU-SELECTED blank | ERR-FLG-ON; screen re-sent with no data         |
| IMS GU fails (non-GE/GB status)        | WS-ERR-FLG='Y'; error string into WS-MESSAGE; screen re-sent     |
| IMS GNP fails (non-GE/GB status)       | WS-ERR-FLG='Y'; error string into WS-MESSAGE; screen re-sent     |
| IMS REPL fails on fraud update         | ROLL-BACK; error string into WS-MESSAGE; screen re-sent          |
| PSB schedule fails                     | WS-ERR-FLG='Y'; error string into WS-MESSAGE; screen re-sent     |
| CICS LINK to COPAUS2C fails (EIBRESP != NORMAL) | ROLL-BACK; screen re-sent                          |
| COPAUS2C returns WS-FRD-UPDT-FAILED    | Move WS-FRD-ACT-MSG to WS-MESSAGE; ROLL-BACK                    |
| IMS REPL fails (fraud tag)             | ROLL-BACK; error string with IMS status into WS-MESSAGE          |
| PF8 at last authorization              | SEND-ERASE-NO; WS-MESSAGE = 'Already at the last Authorization...' |
| Decline reason code not in table       | AUTHRSNO = '9999-ERROR'                                          |

**Rollback scope:** EXEC CICS SYNCPOINT ROLLBACK undoes both the DB2 operation performed by COPAUS2C (via two-phase commit managed by CICS) and any pending IMS changes.

---

### 8. Business Rules

1. If the current authorization has PA-FRAUD-CONFIRMED ('F'), pressing PF5 changes it to PA-FRAUD-REMOVED ('R') and calls COPAUS2C with WS-REMOVE-FRAUD.
2. If the current authorization does not have PA-FRAUD-CONFIRMED, pressing PF5 sets PA-FRAUD-CONFIRMED ('F') and calls COPAUS2C with WS-REPORT-FRAUD.
3. The IMS PAUTDTL1 record is updated (REPL) only if the DB2 operation in COPAUS2C succeeds.
4. PA-FRAUD-RPT-DATE is set by COPAUS2C using CURRENT DATE at the time of the DB2 write.
5. PF8 navigation is limited to forward sequential reads (GNP); there is no backward navigation within the detail screen — PF3 returns to the summary list for backward navigation.

---

### 9. I/O Specification

| Direction | Resource      | Operation        | Data                                                  |
|-----------|---------------|------------------|-------------------------------------------------------|
| Input     | Map COPAU1A   | RECEIVE          | No input fields (all output only except AID key)      |
| Output    | Map COPAU1A   | SEND             | Card#, Auth date/time, response, reason, amount, POS mode, source, MCC, expiry, type, transaction ID, match status, fraud status, merchant details |
| Input     | IMS PAUTSUM0  | GU               | Summary segment for account (establishes parent)      |
| Input     | IMS PAUTDTL1  | GNP (qualified)  | Specific detail record by key                         |
| Input     | IMS PAUTDTL1  | GNP (unqualified)| Next detail record (PF8)                             |
| Output    | IMS PAUTDTL1  | REPL             | Updated detail record after fraud flag change         |
| Output    | COPAUS2C via LINK | COMMAREA    | Fraud data for DB2 insert/update                      |

---
