# Technical Specification: CSUTLDTC — Date Validation Utility Program

## 1. Executive Summary

CSUTLDTC is a batch/called COBOL subprogram in the CardDemo application that validates a date string against a specified format mask. It acts as a thin wrapper around the IBM Language Environment (LE) API `CEEDAYS`, which converts a Gregorian date string in a caller-specified format to a Lilian date number (integer count of days since October 15, 1582). If CEEDAYS returns a non-zero feedback code, the date is invalid. The program returns a structured result record to its caller indicating the outcome severity, a message number, and a descriptive text message. It is invoked by CORPT00C via a static COBOL CALL statement during custom date range validation.

Source file: `app/cbl/CSUTLDTC.cbl`
Version stamp: `CardDemo_v1.0-15-g27d6c6f-68 Date: 2022-07-19 23:12:35 CDT`

---

## 2. Artifact Inventory

| Artifact | Type | Location | Role |
|---|---|---|---|
| CSUTLDTC.cbl | Batch/Called COBOL Subprogram | app/cbl/ | Date validation utility |
| CORPT00C.cbl | Caller (CICS Online) | app/cbl/ | Only known caller in the codebase |

No copybooks are referenced by CSUTLDTC. No COPY statements appear anywhere in the source.

---

## 3. Program Identity

| Attribute | Value | Source Reference |
|---|---|---|
| PROGRAM-ID | CSUTLDTC | CSUTLDTC.cbl line 20 |
| Type | Batch COBOL Subprogram (called via CALL) | CSUTLDTC.cbl line 88 (PROCEDURE DIVISION USING) |
| Called By | CORPT00C | CORPT00C.cbl lines 392, 412 |
| External API Used | CEEDAYS (IBM LE) | CSUTLDTC.cbl line 116 |

---

## 4. Data Division

### 4.1 Working-Storage Section (lines 24–80)

#### WS-DATE-TO-TEST (lines 25–31) — CEEDAYS Input: Date String

IBM Language Environment variable-length string structure:

| Sub-field | PIC | Purpose |
|---|---|---|
| Vstring-length | S9(4) BINARY | Length of the date string |
| Vstring-text / Vstring-char | PIC X OCCURS 0 TO 256 DEPENDING ON Vstring-length | Date string characters |

This is the LE varying-length string (varchar) format required by CEEDAYS as its first argument.

#### WS-DATE-FORMAT (lines 33–39) — CEEDAYS Input: Format Mask

Same LE varying-length string structure, used to hold the format picture string (e.g., 'YYYY-MM-DD').

| Sub-field | PIC | Purpose |
|---|---|---|
| Vstring-length | S9(4) BINARY | Length of format string |
| Vstring-text / Vstring-char | PIC X OCCURS 0 TO 256 DEPENDING ON Vstring-length | Format mask characters |

#### OUTPUT-LILLIAN (line 41) — CEEDAYS Output

| Field | PIC | Purpose |
|---|---|---|
| OUTPUT-LILLIAN | S9(9) BINARY | Lilian date value output; set to 0 before each CEEDAYS call |

#### WS-MESSAGE (lines 42–57) — Result Record (returned to caller)

This is the output record passed back to the caller as LS-RESULT.

| Sub-field | PIC | Purpose |
|---|---|---|
| WS-SEVERITY | X(04) | Severity code in character form |
| WS-SEVERITY-N REDEFINES WS-SEVERITY | PIC 9(4) | Severity as numeric (also placed in RETURN-CODE) |
| FILLER | X(11) | Literal 'Mesg Code:' |
| WS-MSG-NO | X(04) | Message number in character form |
| WS-MSG-NO-N REDEFINES WS-MSG-NO | PIC 9(4) | Message number as numeric |
| FILLER | X(01) | Space |
| WS-RESULT | X(15) | Descriptive result text (see EVALUATE below) |
| FILLER | X(01) | Space |
| FILLER | X(09) | Literal 'TstDate:' |
| WS-DATE | X(10) | Date string being tested (informational) |
| FILLER | X(01) | Space |
| FILLER | X(10) | Literal 'Mask used:' |
| WS-DATE-FMT | X(10) | Format mask used (informational) |
| FILLER | X(01) | Space |
| FILLER | X(03) | Spaces |

**Total WS-MESSAGE length**: 4 + 11 + 4 + 1 + 15 + 1 + 9 + 10 + 1 + 10 + 10 + 1 + 3 = 80 bytes.

**Caller's view** (from CORPT00C.cbl lines 129–137):

| Caller Field | Offset into LS-RESULT | PIC | Corresponds to WS-MESSAGE |
|---|---|---|---|
| CSUTLDTC-RESULT-SEV-CD | 1 | X(04) | WS-SEVERITY |
| FILLER | 5 | X(11) | 'Mesg Code:' |
| CSUTLDTC-RESULT-MSG-NUM | 16 | X(04) | WS-MSG-NO |
| CSUTLDTC-RESULT-MSG | 21 | X(61) | WS-RESULT through end |

#### FEEDBACK-CODE (lines 60–80) — CEEDAYS Feedback Token

A 12-byte IBM LE condition token structure:

| Sub-structure | Meaning |
|---|---|
| FEEDBACK-TOKEN-VALUE | 8-byte condition token (88-level conditions defined against it) |
| CASE-1-CONDITION-ID | Condition identification overlay |
| SEVERITY | S9(4) BINARY — CEEDAYS severity code |
| MSG-NO | S9(4) BINARY — CEEDAYS message number |
| CASE-2-CONDITION-ID REDEFINES CASE-1-CONDITION-ID | Alternative CLASS-CODE / CAUSE-CODE overlay |
| CASE-SEV-CTL | PIC X — severity control byte |
| FACILITY-ID | PIC XXX — 'CEE' for LE calls |
| I-S-INFO | S9(9) BINARY — Instance-specific info |

**88-level condition values on FEEDBACK-TOKEN-VALUE** (lines 62–70):

| 88 Level Name | Hex Value | Meaning |
|---|---|---|
| FC-INVALID-DATE | X'0000000000000000' | Date is valid (zero feedback = success) |
| FC-INSUFFICIENT-DATA | X'000309CB59C3C5C5' | Insufficient date data provided |
| FC-BAD-DATE-VALUE | X'000309CC59C3C5C5' | Bad date value |
| FC-INVALID-ERA | X'000309CD59C3C5C5' | Invalid era designation |
| FC-UNSUPP-RANGE | X'000309D159C3C5C5' | Date outside supported range |
| FC-INVALID-MONTH | X'000309D559C3C5C5' | Invalid month value |
| FC-BAD-PIC-STRING | X'000309D659C3C5C5' | Bad picture string (format mask error) |
| FC-NON-NUMERIC-DATA | X'000309D859C3C5C5' | Non-numeric data in date string |
| FC-YEAR-IN-ERA-ZERO | X'000309D959C3C5C5' | Year 0 in era |

**Note**: FC-INVALID-DATE (all zeros) is a misnomer in the variable name — it actually means the date IS valid (CEEDAYS returns zero feedback on success).

### 4.2 Linkage Section (lines 83–86)

```cobol
01 LS-DATE         PIC X(10).
01 LS-DATE-FORMAT  PIC X(10).
01 LS-RESULT       PIC X(80).
```

These are the three USING parameters:
- LS-DATE: 10-character date string (e.g., '2022-07-19')
- LS-DATE-FORMAT: 10-character format mask (e.g., 'YYYY-MM-DD')
- LS-RESULT: 80-character result record returned to caller

---

## 5. PROCEDURE DIVISION

Source: CSUTLDTC.cbl lines 88–153

### Entry and Exit (lines 88–101)

```
PROCEDURE DIVISION USING LS-DATE, LS-DATE-FORMAT, LS-RESULT.

    INITIALIZE WS-MESSAGE
    MOVE SPACES TO WS-DATE

    PERFORM A000-MAIN THRU A000-MAIN-EXIT

    MOVE WS-MESSAGE    TO LS-RESULT
    MOVE WS-SEVERITY-N TO RETURN-CODE

    EXIT PROGRAM.
```

Execution path:
1. Initializes WS-MESSAGE to defaults.
2. Clears WS-DATE.
3. Performs A000-MAIN to A000-MAIN-EXIT.
4. Copies WS-MESSAGE (80 bytes) to LS-RESULT.
5. Sets RETURN-CODE to WS-SEVERITY-N (numeric severity code).
6. Issues EXIT PROGRAM (returns to caller; does NOT GOBACK or STOP RUN).

### A000-MAIN (lines 103–151)

1. Copies LS-DATE into the varying-length string WS-DATE-TO-TEST:
   - Sets `Vstring-length OF WS-DATE-TO-TEST` = LENGTH OF LS-DATE (= 10).
   - Moves LS-DATE to `Vstring-text OF WS-DATE-TO-TEST` and to WS-DATE (for reporting).
2. Copies LS-DATE-FORMAT into WS-DATE-FORMAT:
   - Sets `Vstring-length OF WS-DATE-FORMAT` = LENGTH OF LS-DATE-FORMAT (= 10).
   - Moves LS-DATE-FORMAT to `Vstring-text OF WS-DATE-FORMAT` and to WS-DATE-FMT.
3. Sets OUTPUT-LILLIAN = 0.
4. Calls CEEDAYS:
   ```cobol
   CALL "CEEDAYS" USING
       WS-DATE-TO-TEST,
       WS-DATE-FORMAT,
       OUTPUT-LILLIAN,
       FEEDBACK-CODE
   ```
5. Moves SEVERITY OF FEEDBACK-CODE to WS-SEVERITY-N.
6. Moves MSG-NO OF FEEDBACK-CODE to WS-MSG-NO-N.
7. EVALUATE TRUE against 88-level conditions on FEEDBACK-TOKEN-VALUE:

| Condition | WS-RESULT Set To |
|---|---|
| FC-INVALID-DATE (zero = valid) | 'Date is valid     ' (15 chars) |
| FC-INSUFFICIENT-DATA | 'Insufficient   ' |
| FC-BAD-DATE-VALUE | 'Datevalue error' |
| FC-INVALID-ERA | 'Invalid Era    ' |
| FC-UNSUPP-RANGE | 'Unsupp. Range  ' |
| FC-INVALID-MONTH | 'Invalid month  ' |
| FC-BAD-PIC-STRING | 'Bad Pic String ' |
| FC-NON-NUMERIC-DATA | 'Nonnumeric data' |
| FC-YEAR-IN-ERA-ZERO | 'YearInEra is 0 ' |
| WHEN OTHER | 'Date is invalid' |

### A000-MAIN-EXIT (lines 152–153)

```cobol
A000-MAIN-EXIT.
    EXIT.
```

Plain EXIT paragraph serving as the THRU target for PERFORM A000-MAIN THRU A000-MAIN-EXIT.

---

## 6. Calling Interface

### Called From CORPT00C (lines 388–425 of CORPT00C.cbl)

CORPT00C defines a local CSUTLDTC-PARM structure and calls CSUTLDTC twice per custom date entry — once for the start date and once for the end date:

```cobol
01 CSUTLDTC-PARM.
   05 CSUTLDTC-DATE         PIC X(10).
   05 CSUTLDTC-DATE-FORMAT  PIC X(10).
   05 CSUTLDTC-RESULT.
      10 CSUTLDTC-RESULT-SEV-CD      PIC X(04).
      10 FILLER                      PIC X(11).
      10 CSUTLDTC-RESULT-MSG-NUM     PIC X(04).
      10 CSUTLDTC-RESULT-MSG         PIC X(61).

MOVE WS-START-DATE    TO CSUTLDTC-DATE
MOVE WS-DATE-FORMAT   TO CSUTLDTC-DATE-FORMAT    (='YYYY-MM-DD')
MOVE SPACES           TO CSUTLDTC-RESULT

CALL 'CSUTLDTC' USING CSUTLDTC-DATE
                      CSUTLDTC-DATE-FORMAT
                      CSUTLDTC-RESULT
```

Result evaluation in CORPT00C:
- `CSUTLDTC-RESULT-SEV-CD = '0000'` → date is valid, continue.
- `CSUTLDTC-RESULT-SEV-CD NOT = '0000'` AND `CSUTLDTC-RESULT-MSG-NUM NOT = '2513'` → date invalid, display error.
- `CSUTLDTC-RESULT-MSG-NUM = '2513'` → future date condition (CEEDAYS message 2513 indicates a date in the future), accepted as valid.

**Severity code mapping** between CSUTLDTC and CORPT00C:

The WS-SEVERITY-N in CSUTLDTC is derived from `SEVERITY OF FEEDBACK-CODE`, which is a BINARY S9(4) field from the CEEDAYS feedback token. For a valid date, CEEDAYS sets FEEDBACK-CODE to all zeros, so SEVERITY = 0 and WS-SEVERITY = '0000'. CORPT00C checks the character form CSUTLDTC-RESULT-SEV-CD, which maps to WS-SEVERITY (first 4 bytes of LS-RESULT).

---

## 7. Logic Flow Diagram

```
CALL 'CSUTLDTC' USING date, format, result
        |
        v
PROCEDURE DIVISION USING LS-DATE, LS-DATE-FORMAT, LS-RESULT
        |
        v
INITIALIZE WS-MESSAGE, clear WS-DATE
        |
        v
A000-MAIN:
  Build WS-DATE-TO-TEST (LE varying string) from LS-DATE (length=10)
  Build WS-DATE-FORMAT (LE varying string) from LS-DATE-FORMAT (length=10)
  Set OUTPUT-LILLIAN = 0
        |
        v
  CALL "CEEDAYS" USING WS-DATE-TO-TEST, WS-DATE-FORMAT,
                        OUTPUT-LILLIAN, FEEDBACK-CODE
        |
        v
  Extract SEVERITY and MSG-NO from FEEDBACK-CODE
        |
        v
  EVALUATE FEEDBACK-TOKEN-VALUE:
    All-zeros (FC-INVALID-DATE)  -> WS-RESULT = 'Date is valid'
    FC-INSUFFICIENT-DATA         -> WS-RESULT = 'Insufficient'
    FC-BAD-DATE-VALUE            -> WS-RESULT = 'Datevalue error'
    FC-INVALID-ERA               -> WS-RESULT = 'Invalid Era'
    FC-UNSUPP-RANGE              -> WS-RESULT = 'Unsupp. Range'
    FC-INVALID-MONTH             -> WS-RESULT = 'Invalid month'
    FC-BAD-PIC-STRING            -> WS-RESULT = 'Bad Pic String'
    FC-NON-NUMERIC-DATA          -> WS-RESULT = 'Nonnumeric data'
    FC-YEAR-IN-ERA-ZERO          -> WS-RESULT = 'YearInEra is 0'
    OTHER                        -> WS-RESULT = 'Date is invalid'
        |
        v
A000-MAIN-EXIT.
        |
        v
MOVE WS-MESSAGE TO LS-RESULT
MOVE WS-SEVERITY-N TO RETURN-CODE
EXIT PROGRAM
        |
        v
Control returns to caller (CORPT00C)
```

---

## 8. Dependencies

| Dependency | Type | Notes |
|---|---|---|
| CEEDAYS | IBM LE API | Must be available in the runtime LE library (SCEERUN or equivalent). Required for z/OS Language Environment. |
| CORPT00C | Caller | Only known caller in the codebase. Static link (CALL literal). |

No CICS interfaces are used. No file I/O. No copybooks. No DB2. The program is purely computational.

---

## 9. Return Codes

CSUTLDTC sets `RETURN-CODE` to WS-SEVERITY-N (the CEEDAYS severity code as a number). The RETURN-CODE special register in COBOL is the standard batch return code. Callers that invoke CSUTLDTC as a subprogram via CALL do not directly check RETURN-CODE; they instead inspect LS-RESULT.

| RETURN-CODE / WS-SEVERITY-N | Meaning |
|---|---|
| 0 | Date is valid |
| Non-zero | Date validation error; specific cause in MSG-NO and WS-RESULT |

---

## 10. Error Handling

CSUTLDTC does not perform any error handling. All outcomes — valid and invalid dates alike — are mapped to descriptive text in WS-RESULT and returned to the caller. There is no ABEND, no CICS ABEND, no file output. The EVALUATE in A000-MAIN covers all known CEEDAYS feedback conditions plus an OTHER catch-all.

---

## 11. Business Rules

| Rule | Implementation | Source Reference |
|---|---|---|
| Date validity is determined by CEEDAYS | CEEDAYS validates against the Gregorian calendar with leap-year awareness | Lines 116–120 |
| Format mask is always 'YYYY-MM-DD' when called from CORPT00C | CORPT00C.cbl line 389: `MOVE WS-DATE-FORMAT TO CSUTLDTC-DATE-FORMAT` where WS-DATE-FORMAT = 'YYYY-MM-DD' | CORPT00C.cbl lines 72, 389 |
| Future dates are not rejected | CORPT00C accepts CSUTLDTC-RESULT-MSG-NUM = '2513' as valid | CORPT00C.cbl line 399 |
| Date input is exactly 10 characters | LENGTH OF LS-DATE = 10 is used as Vstring-length | CSUTLDTC.cbl line 105 |

---

## 12. Open Questions and Gaps

1. **FC-INVALID-DATE naming**: The 88-level name FC-INVALID-DATE is set to value X'0000000000000000' (all zeros) — but this actually means the date IS valid (CEEDAYS returns zero feedback on success). The name is misleading. The EVALUATE WHEN clause for this condition correctly maps it to 'Date is valid', so the logic is correct despite the confusing name.
2. **LS-DATE fixed at 10 characters**: The LINKAGE SECTION declares LS-DATE as PIC X(10), meaning CSUTLDTC can only validate dates that fit in exactly 10 characters. The CEEDAYS API itself supports longer date strings, but CSUTLDTC does not expose this capability.
3. **No validation of LS-DATE-FORMAT**: CSUTLDTC blindly passes LS-DATE-FORMAT to CEEDAYS. If the format string is invalid, CEEDAYS returns FC-BAD-PIC-STRING (mapped to 'Bad Pic String' in WS-RESULT), which CORPT00C would treat as a date validation error — potentially confusing the user.
4. **Commented-out GOBACK**: Line 101 has `* GOBACK` commented out, with EXIT PROGRAM active at line 100. EXIT PROGRAM is correct for a subprogram called via COBOL CALL; GOBACK would also work but EXIT PROGRAM is the preferred construct.
5. **DISPLAY statement commented out**: Line 96 has `* DISPLAY WS-MESSAGE` commented out, indicating this was used during development/testing and removed.
6. **Thread safety for CICS callers**: Although CSUTLDTC uses only LOCAL (Working-Storage) data, in a CICS environment each CALL to CSUTLDTC obtains a new copy of Working-Storage via the CICS task memory model, so concurrent calls are safe.
