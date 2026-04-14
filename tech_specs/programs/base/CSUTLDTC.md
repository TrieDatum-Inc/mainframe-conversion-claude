# Technical Specification: CSUTLDTC

## 1. Program Overview

| Attribute        | Value                                                |
|------------------|------------------------------------------------------|
| Program ID       | CSUTLDTC                                             |
| Source File      | app/cbl/CSUTLDTC.cbl                                 |
| Application      | CardDemo                                             |
| Type             | Batch/CICS COBOL Subprogram (called utility)         |
| Transaction ID   | N/A (called subprogram, not an entry point)          |
| Function         | Date validation utility. Accepts a date string and format string from the caller, calls IBM Language Environment runtime API CEEDAYS to convert to a Lillian day number, and returns a severity code and result message. Used by COTRN02C and other programs to validate user-entered dates. Sets RETURN-CODE to WS-SEVERITY-N after execution. |

---

## 2. Program Flow

### High-Level Flow

```
ENTRY: PROCEDURE DIVISION USING LS-DATE, LS-DATE-FORMAT, LS-RESULT

MOVE LOW-VALUES / SPACES to working storage
MOVE LS-DATE to WS-DATE-TO-TEST
MOVE LS-DATE-FORMAT to WS-DATE-FORMAT

CALL 'CEEDAYS' USING WS-DATE-TO-TEST, WS-DATE-FORMAT,
                     WS-LILLIAN-DATE, FC-FEEDBACK-CODE

IF FC-INVALID-DATE (FC = X'0000000000000000'):
    MOVE WS-SEVERITY-G TO LS-RESULT (severity '0000' = good)
ELSE:
    MOVE WS-SEVERITY-N TO LS-RESULT (severity '1200' or message code)
    Populate WS-RESULT with error message text

MOVE WS-SEVERITY-N TO RETURN-CODE

STOP RUN
```

### Paragraph-Level Detail

| Paragraph       | Lines  | Description |
|-----------------|--------|-------------|
| PROCEDURE DIVISION USING ... | 80–158 | Single inline block: initialize; MOVE inputs; CALL CEEDAYS; evaluate FC; set LS-RESULT; set RETURN-CODE; STOP RUN |

No named paragraphs are defined. The entire PROCEDURE DIVISION is a single sequential block.

---

## 3. Data Structures

### Copybooks Referenced

None.

### Linkage Section (Parameters)

| Parameter      | PIC / Level | Purpose |
|----------------|-------------|---------|
| LS-DATE        | X(10)       | Input: date string to validate (e.g., '2024-01-15' or '01152024') |
| LS-DATE-FORMAT | X(30)       | Input: CEEDAYS picture string describing date format (e.g., 'YYYYMMDD' or 'MM/DD/YYYY') |
| LS-RESULT      | Group (15 bytes) | Output: SEV-CD X(04) severity code + result message text |

### LS-RESULT Layout

| Sub-field  | PIC     | Purpose |
|------------|---------|---------|
| SEV-CD     | X(04)   | Severity: '0000'=valid; non-zero = invalid/error |
| WS-RESULT  | X(11)   | Human-readable result description text |

### Key Working Storage Variables

| Variable           | PIC / Level | Purpose |
|--------------------|-------------|---------|
| WS-DATE-TO-TEST    | X(10)       | Copy of LS-DATE for CEEDAYS input |
| WS-DATE-FORMAT     | X(30)       | Copy of LS-DATE-FORMAT for CEEDAYS |
| WS-LILLIAN-DATE    | S9(09) COMP | Output from CEEDAYS: Lillian day number (days since Oct 14, 1582) |
| FC-FEEDBACK-CODE   | X(12)       | LE feedback code from CEEDAYS: X'000000000000000000000000' = success |
| FC-INVALID-DATE    | 88-level    | VALUE X'000000000000000000000000' — true when CEEDAYS found no error |
| WS-SEVERITY-G      | X(04) = '0000' | Good/valid severity code returned in SEV-CD |
| WS-SEVERITY-N      | X(04) = '1200' | Note/warning severity; also moved to RETURN-CODE |

**Note on FC-FEEDBACK-CODE**: The IBM LE CEEDAYS feedback code is a 12-byte structure. The 88-level FC-INVALID-DATE tests for all-zeros (no condition raised). A non-zero value means CEEDAYS detected an invalid date, unrecognized format, or out-of-range date.

**Note on RETURN-CODE**: MOVE WS-SEVERITY-N TO RETURN-CODE is executed unconditionally at the end of the program, regardless of whether the date was valid or not. Callers must use LS-RESULT SEV-CD, not RETURN-CODE, to determine validity.

---

## 4. CICS Commands Used

None. CSUTLDTC is a COBOL subprogram called with CALL. It may be called from CICS programs (e.g., COTRN02C) but contains no EXEC CICS statements.

---

## 5. File/Dataset Access

None.

---

## 6. Screen Interaction

None. Subprogram — no BMS interaction.

---

## 7. Called Programs / Transfers

| Called Program | Type        | Purpose |
|----------------|-------------|---------|
| CEEDAYS        | Static CALL | IBM Language Environment API: converts date string + format to Lillian day number; sets FC-FEEDBACK-CODE |

**CEEDAYS signature (IBM LE):**
```
CALL 'CEEDAYS' USING picture-string, date-value, lillian, feedback-code
```
- `picture-string`: format descriptor (same as LS-DATE-FORMAT)
- `date-value`: date string to convert (same as LS-DATE-TO-TEST)
- `lillian`: S9(09) COMP output — Lillian day number
- `feedback-code`: 12-byte feedback structure

**Callers of CSUTLDTC in CardDemo:**

| Caller    | Call Site              | Dates Validated |
|-----------|------------------------|-----------------|
| COTRN02C  | 9000-VALIDATE-FIELDS   | TRAN-ORIG-DATE, TRAN-PROC-DATE |

**[UNRESOLVED]** — Additional callers may exist in programs not fully inventoried (e.g., COBIL00C). Grep of app/cbl/ for 'CSUTLDTC' would confirm full caller list.

---

## 8. Error Handling

| Condition | Action |
|-----------|--------|
| CEEDAYS feedback code = all zeros (FC-INVALID-DATE) | SEV-CD='0000' (valid); WS-RESULT set to 'DATE IS VALID' or equivalent |
| CEEDAYS feedback code non-zero | SEV-CD='1200' (or CEEDAYS message code); WS-RESULT populated with error description text |
| Out-of-range Lillian date (e.g., year before 1582 in proleptic calendar) | CEEDAYS returns feedback; SEV-CD non-zero. Callers typically tolerate message '2513' (Gregorian proleptic range warning) as acceptable |

**Caller tolerance note**: COTRN02C checks `IF SEV-CD NOT = '0000'` to detect invalidity. Based on source analysis, COTRN02C also checks for specific message code '2513' and treats it as acceptable (date in Lillian proleptic range but valid for business purposes).

---

## 9. Business Rules

1. **Single responsibility**: CSUTLDTC solely validates whether a date string conforms to the given format and represents a calendar-valid date. No business date rules (e.g., not-in-future, not-in-past) are applied here.
2. **Format flexibility**: The date format is passed in by the caller, making CSUTLDTC reusable across different date formats used in CardDemo (e.g., YYYYMMDD for file dates, MM/DD/YYYY for screen dates).
3. **RETURN-CODE behavior**: RETURN-CODE is always set to WS-SEVERITY-N ('1200') at end, regardless of validation outcome. This is the z/OS batch program return code visible in JCL COND checking. Callers must use LS-RESULT.SEV-CD, not RETURN-CODE, for validity determination.
4. **Message '2513' tolerance**: CEEDAYS returns message token '2513' for dates that fall in the Lillian proleptic Gregorian calendar range (pre-1582 dates in Gregorian reckoning). CardDemo callers accept '2513' as a non-error condition.
5. **No CICS dependency**: CSUTLDTC can be called from both batch and online (CICS) programs without modification.

---

## 10. Inputs and Outputs

### Inputs

| Source       | Description |
|--------------|-------------|
| LS-DATE      | Date string to validate (up to 10 characters; format defined by LS-DATE-FORMAT) |
| LS-DATE-FORMAT | CEEDAYS picture string defining the format of LS-DATE |

### Outputs

| Destination  | Description |
|--------------|-------------|
| LS-RESULT.SEV-CD | '0000' = valid date; non-zero = invalid |
| LS-RESULT.WS-RESULT | Text description of validation result (11 characters) |
| RETURN-CODE  | Always set to WS-SEVERITY-N='1200' (not useful for validity checking by callers) |

---

## 11. Key Variables and Their Purpose

| Variable         | Purpose |
|------------------|---------|
| LS-DATE          | Input date string from caller |
| LS-DATE-FORMAT   | Input format picture string; passed directly to CEEDAYS |
| FC-FEEDBACK-CODE | 12-byte LE feedback code from CEEDAYS; FC-INVALID-DATE 88-level tests all-zeros for valid |
| WS-LILLIAN-DATE  | Lillian day number output from CEEDAYS (not returned to caller; used only to drive the CALL) |
| SEV-CD           | Primary output: '0000'=valid, non-zero=invalid; callers test this field |
| WS-SEVERITY-N    | Literal '1200' used for RETURN-CODE and for non-valid SEV-CD values |
