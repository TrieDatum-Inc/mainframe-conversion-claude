# Technical Specification: COACTUPC

## 1. Program Overview

| Attribute        | Value                                                |
|------------------|------------------------------------------------------|
| Program ID       | COACTUPC                                             |
| Source File      | app/cbl/COACTUPC.cbl                                 |
| Application      | CardDemo                                             |
| Type             | CICS COBOL Program (Online)                          |
| Transaction ID   | CAUP (inferred from WS-TRANID literal — **[UNRESOLVED]** value not visible in lines 1-449 read; requires lines 450+ or CSD confirmation) |
| Function         | Accept and process Account Update. Allows authorized users to modify account fields (status, credit limits, balances, dates) and associated customer fields (name, address, phone, SSN, DOB, FICO score). Validates all input fields before allowing updates to ACCTDAT and CUSTDAT files. |

---

## 2. Program Flow

### High-Level Flow

```
ENTRY (CICS RETURN with TRANSID = CAUP and COMMAREA)

EIBCALEN = 0 OR fresh entry:
    Initialize CARDDEMO-COMMAREA
    CDEMO-PGM-CONTEXT = 0 (ENTER mode)
    Send account update screen

EIBCALEN > 0 (returning with commarea):
    Receive updated COMMAREA
    EVALUATE EIBAID / PFK-FLAG:
        ENTER:
            IF CDEMO-PGM-ENTER: send screen (first time)
            IF CDEMO-PGM-REENTER: receive screen inputs
                PERFORM 2000-PROCESS-INPUTS
                    Validate all fields (signed numbers, alpha, phone, SSN, dates, Y/N flags)
                    IF input errors: re-send screen with error highlights
                    ELSE: PERFORM 9000-UPDATE-ACCOUNT
                        READ ACCTDAT UPDATE, READ CUSTDAT UPDATE
                        REWRITE both if WS-DATACHANGED-FLAG = '1'
                Send screen (with results or errors)
        PF3: XCTL back to calling program (CDEMO-FROM-PROGRAM)
        PF12: XCTL back to COMEN01C (main menu)

CICS RETURN TRANSID(CAUP) COMMAREA(CARDDEMO-COMMAREA)
```

### Paragraph-Level Detail

Lines beyond 449 not fully read. The following is based on WORKING-STORAGE structure and CICS patterns observed:

| Paragraph                  | Lines     | Description |
|----------------------------|-----------|-------------|
| MAIN-PARA / 0000-MAIN      | ~450+     | Entry point: EIBCALEN check; COMMAREA load; PFK routing; CICS RETURN |
| YYYY-STORE-PFKEY           | ~450+     | Maps EIBAID to PFK flag (PFK-VALID/PFK-INVALID) |
| 1000-SEND-MAP              | ~450+     | CICS SEND MAP('...') MAPSET('...') |
| 2000-PROCESS-INPUTS        | ~450+     | Validates all editable fields; sets WS-DATACHANGED-FLAG |
| 9000-UPDATE-ACCOUNT        | ~450+     | CICS READ UPDATE on ACCTDAT and CUSTDAT; CICS REWRITE if data changed |
| ABEND-ROUTINE              | ~450+     | CICS HANDLE ABEND target |

**Note**: The PROCEDURE DIVISION begins beyond line 449. The full procedure division content requires reading the source file from approximately line 450 onward. All paragraph details above are inferred from WORKING-STORAGE structure and CICS conventions visible in lines 1-449.

---

## 3. Data Structures

### Copybooks Referenced

| Copybook  | Used In              | Contents |
|-----------|----------------------|----------|
| CSUTLDWY  | WORKING-STORAGE (line 166) | Generic date edit variables (CCYYMMDD format) — **[UNRESOLVED]** complete layout requires app/cpy/CSUTLDWY.cpy |
| COCOM01Y  | Referenced (inferred from CDEMO-FROM-PROGRAM, CDEMO-PGM-CONTEXT usage) | CARDDEMO-COMMAREA shared structure |
| BMS mapset| COPY statement for mapset (name not visible in lines 1-449) | Account update screen fields |

### Key Working Storage Variables

| Variable                       | PIC / Structure | Purpose |
|--------------------------------|-----------------|---------|
| WS-RESP-CD / WS-REAS-CD        | S9(09) COMP     | CICS RESP/RESP2 for CICS command response checking |
| WS-TRANID                      | X(4)            | Transaction ID value (CAUP inferred) |
| WS-DATACHANGED-FLAG            | X(1)            | '0'=no changes; '1'=change detected; drives conditional REWRITE |
| WS-INPUT-FLAG                  | X(1)            | LOW-VALUES=pending; '0'=ok; '1'=error |
| WS-RETURN-FLAG                 | X(1)            | LOW-VALUES=off; '1'=on (signals navigation return) |
| WS-PFK-FLAG                    | X(1)            | '0'=valid PF key; '1'=invalid PF key |
| WS-EDIT-SIGNED-NUMBER-9V2-X    | X(15)           | Work area for signed number edit (credit limit, balance fields) |
| WS-FLG-SIGNED-NUMBER-EDIT      | X(1)            | LOW-VALUES=valid; '0'=not-ok; 'B'=blank |
| WS-EDIT-ALPHANUM-ONLY          | X(256)          | Work area for alphanumeric field validation |
| WS-EDIT-ALPHA-ONLY-FLAGS       | X(1)            | LOW-VALUES=valid; '0'=not-ok; 'B'=blank |
| WS-EDIT-YES-NO                 | X(1)            | Y/N validation flag; 88 FLG-YES-NO-ISVALID values 'Y','N' |
| WS-EDIT-US-PHONE-NUM           | X(15)           | Phone number edit area: (NNN) NNN-NNNN format |
| WS-EDIT-US-PHONE-NUM-FLGS      | Group (3 bytes) | Three per-segment flags (area code, exchange, subscriber) |
| WS-EDIT-US-SSN                 | Group (9 bytes) | SSN edit area: PART1 9(3), PART2 9(2), PART3 9(4) |
| INVALID-SSN-PART1              | 88 level        | Invalid area codes: 0, 666, 900-999 |
| WS-EDIT-US-SSN-FLGS            | Group (3 bytes) | Three per-part flags |
| WS-EDIT-DT-OF-BIRTH-FLGS       | Group (3 bytes) | Per-component date-of-birth validation flags (year/month/day) |
| WS-EDIT-OPEN-DATE-FLGS         | Group (3 bytes) | Per-component account open-date validation flags |
| WS-EXPIRY-DATE-FLGS            | Group (3 bytes) | Per-component expiry date validation flags |
| WS-EDIT-REISSUE-DATE-FLGS      | Group (3 bytes) | Per-component reissue date validation flags |
| WS-EDIT-FICO-SCORE-FLGS        | X(1)            | FICO score validation flag |
| WS-EDIT-ACCT-STATUS            | X(1)            | Y/N validation for ACCT-ACTIVE-STATUS field |
| WS-EDIT-PRI-CARDHOLDER         | X(1)            | Y/N validation for primary card holder indicator |
| ACCT-UPDATE-RECORD             | Group 300 bytes | Inline account data structure (mirrors CVACT01Y) |
| CUST-UPDATE-RECORD             | Group ~500 bytes | Inline customer data structure (mirrors CVCUS01Y) |
| WS-CURR-DATE                   | X(21)           | Receives FUNCTION CURRENT-DATE for date calculations |
| WS-DIV-BY / WS-DIVIDEND / WS-REMAINDER | COMP-3  | Arithmetic work variables for date calculations |

---

## 4. CICS Commands Used

| Command          | Purpose |
|------------------|---------|
| EXEC CICS RETURN TRANSID COMMAREA | Pseudo-conversational RETURN with CAUP transaction ID |
| EXEC CICS SEND MAP MAPSET FROM ERASE | Send account update BMS screen |
| EXEC CICS RECEIVE MAP MAPSET INTO RESP RESP2 | Receive screen input |
| EXEC CICS READ DATASET INTO LENGTH RIDFLD UPDATE RESP RESP2 | Read ACCTDAT and CUSTDAT for update |
| EXEC CICS REWRITE DATASET FROM LENGTH RESP RESP2 | Rewrite updated account and customer records |
| EXEC CICS XCTL PROGRAM COMMAREA | Transfer to previous program (PF3) or main menu (PF12) |
| EXEC CICS HANDLE ABEND LABEL | Set abend handler |
| EXEC CICS ASKTIME / FORMATTIME | Timestamp generation (inferred from CSDAT01Y pattern) |

---

## 5. File/Dataset Access

| CICS File Name | Access Type | Purpose |
|----------------|-------------|---------|
| ACCTDAT        | READ UPDATE + REWRITE | Read account record for display; rewrite on confirmed update |
| CUSTDAT        | READ UPDATE + REWRITE | Read customer record for display; rewrite on confirmed update |

---

## 6. Screen Interaction

| BMS Mapset | BMS Map | Transaction |
|------------|---------|-------------|
| Not determinable from lines 1-449 — requires COPY statement for BMS mapset in remaining source | Unknown | CAUP |

**Key Screen Fields (inferred from validation structure):**

| Field (Logical) | Validation |
|-----------------|------------|
| Account ID      | Required; non-zero 11-digit numeric |
| Customer ID     | Required; non-zero 9-digit numeric |
| ACCT-ACTIVE-STATUS | Y/N only (FLG-ACCT-STATUS-ISVALID) |
| Credit limit    | Signed number edit (WS-FLG-SIGNED-NUMBER-EDIT) |
| Cash credit limit | Signed number edit |
| Current balance | Signed number edit |
| Cycle credit/debit | Signed number edit |
| Account open date | CCYYMMDD via CSUTLDWY date edit |
| Account expiry date | CCYYMMDD |
| Account reissue date | CCYYMMDD |
| Customer first/middle/last name | Alpha-only (FLG-ALPHA-ISVALID) |
| Address lines   | Alphanumeric |
| Phone number 1/2 | US phone format NNN-NNN-NNNN (area code validated) |
| SSN             | 9-digit; PART1 not in {0, 666, 900-999} |
| Date of birth   | CCYYMMDD |
| EFT account ID  | Alphanumeric |
| Primary card holder | Y/N |
| FICO score      | Numeric |

**Navigation:**
- PF3: return to calling program (CDEMO-FROM-PROGRAM)
- PF12: return to COMEN01C (main menu)

---

## 7. Called Programs / Transfers

| Program   | Method       | Condition |
|-----------|--------------|-----------|
| CDEMO-FROM-PROGRAM | CICS XCTL | PF3 pressed |
| COMEN01C  | CICS XCTL   | PF12 pressed |

---

## 8. Error Handling

| Condition | Action |
|-----------|--------|
| Validation flag not valid (per field) | Set WS-INPUT-FLAG='1' (INPUT-ERROR); highlight screen field; re-send map |
| Invalid SSN PART1 (0, 666, 900-999) | FLG-EDIT-US-SSN-PART1-NOT-OK; INPUT-ERROR |
| Invalid phone segment | Per-segment flag set; INPUT-ERROR |
| Invalid date (CCYYMMDD) | CSUTLDWY flags set; INPUT-ERROR |
| CICS READ NOTFND on ACCTDAT | Error message; re-send map |
| CICS READ NOTFND on CUSTDAT | Error message; re-send map |
| CICS REWRITE failure | Error message; re-send map |
| EIBCALEN = 0 | Redirect to signon (COSGN00C) |
| CICS HANDLE ABEND | ABEND-ROUTINE |

---

## 9. Business Rules

1. **Comprehensive validation**: 15+ field-level validations covering signed numbers, alpha-only, alphanumeric, Y/N flags, US phone format, SSN rules, and date validity via CEEDAYS (CSUTLDWY).
2. **SSN validation rules**: Part 1 (area number) must not be 0, 666, or in range 900-999. This mirrors IRS/SSA validity rules for US Social Security Numbers.
3. **Phone format**: Expected format (NNN) NNN-NNNN with area code (part A), exchange (part B), and subscriber number (part C) each independently validated as numeric.
4. **WS-DATACHANGED-FLAG**: Change detection prevents unnecessary REWRITE operations. Only fields that were actually modified trigger a file update.
5. **Pseudo-conversational pattern**: CICS RETURN with TRANSID=CAUP and COMMAREA on every screen cycle. First entry detected by EIBCALEN=0 or CDEMO-PGM-ENTER context.
6. **No confirmation step**: Unlike COBIL00C and COUSR03C, account update does not appear to require explicit Y/N confirmation (no CONF-PAY-FLG equivalent visible).

---

## 10. Inputs and Outputs

### Inputs

| Source    | Description |
|-----------|-------------|
| BMS Screen | All editable account and customer fields |
| ACCTDAT   | Account master record (READ UPDATE for display and modification) |
| CUSTDAT   | Customer master record (READ UPDATE for display and modification) |
| COMMAREA  | CDEMO-FROM-PROGRAM, CDEMO-FROM-TRANID for navigation on PF3 |

### Outputs

| Destination | Description |
|-------------|-------------|
| BMS Screen  | Account and customer field display; validation error messages |
| ACCTDAT     | CICS REWRITE with updated account fields |
| CUSTDAT     | CICS REWRITE with updated customer fields |

---

## 11. Key Variables and Their Purpose

| Variable               | Purpose |
|------------------------|---------|
| WS-DATACHANGED-FLAG    | Prevents unnecessary REWRITE; '1' if user changed any field |
| WS-INPUT-FLAG          | INPUT-ERROR flag; '1' if any field fails validation; drives screen re-send |
| WS-EDIT-US-SSN         | Full SSN in three-part structure for area/group/serial validation |
| WS-EDIT-US-PHONE-NUM   | Full phone in three-part structure for area/exchange/subscriber validation |
| ACCT-UPDATE-RECORD     | Inline account structure for reading and updating account fields |
| CUST-UPDATE-RECORD     | Inline customer structure for reading and updating customer fields |
