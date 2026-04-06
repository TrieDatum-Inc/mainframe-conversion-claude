# Technical Specification: CSUTLDTC — Date Validation Subroutine

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | CSUTLDTC |
| Source File | `app/cbl/CSUTLDTC.cbl` |
| Type | Callable Subroutine (Shared) |

## 2. Purpose

CSUTLDTC is a **callable date validation subroutine** that wraps the IBM Language Environment (LE) CEEDAYS API. It validates a date string against a format mask and returns a severity code and result message.

## 3. Interface

```
PROCEDURE DIVISION USING LS-DATE, LS-DATE-FORMAT, LS-RESULT
```

| Parameter | PIC | Direction | Description |
|-----------|-----|-----------|-------------|
| LS-DATE | X(10) | Input | Date to validate (e.g., '2022-07-19') |
| LS-DATE-FORMAT | X(10) | Input | Format mask (e.g., 'YYYY-MM-DD') |
| LS-RESULT | X(80) | Output | Result: first 4 bytes = severity code |

## 4. Return Values

| Severity | Meaning |
|----------|---------|
| '0000' | Date is valid |
| Non-zero | Date is invalid — message contains reason |

Special case: MSG-NO = '2513' is treated as an acceptable non-fatal condition by callers (Gregorian leap year boundary).

## 5. External Calls

| Target | Purpose |
|--------|---------|
| CEEDAYS | IBM LE date conversion API |

## 6. Callers

| Program | Usage |
|---------|-------|
| COTRN02C | Validate original and processing dates (YYYY-MM-DD) |
| CORPT00C | Validate custom date range for reports |
| COACTUPC | Date validation via CSUTLDPY paragraphs |

## 7. Implementation Notes

- Builds variable-length string structures (Vstring-length + Vstring-text) required by CEEDAYS.
- EVALUATE on FEEDBACK-CODE 88-levels (FC-INVALID-DATE, FC-BAD-DATE-VALUE, FC-INVALID-MONTH, etc.).
- RETURN-CODE is also set to the severity value.
