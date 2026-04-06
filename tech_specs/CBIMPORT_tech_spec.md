# Technical Specification: CBIMPORT — Data Migration Import

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | CBIMPORT |
| Source File | `app/cbl/CBIMPORT.cbl` |
| Type | Batch COBOL |

## 2. Purpose

CBIMPORT is the **inverse of CBEXPORT**. It reads the 500-byte multi-record EXPFILE, validates data integrity, and splits records into separate normalized output files based on EXPORT-REC-TYPE.

## 3. Files Accessed

### Input
| File DD | Format | Description |
|---------|--------|-------------|
| EXPFILE | KSDS fixed 500 bytes | Multi-record export file |

### Output (all sequential)
| File DD | Layout | Description |
|---------|--------|-------------|
| CUSTOUT | CVCUS01Y (500 bytes) | Customer records |
| ACCTOUT | CVACT01Y (300 bytes) | Account records |
| XREFOUT | CVACT03Y (50 bytes) | Card cross-reference |
| TRNXOUT | CVTRA05Y (350 bytes) | Transaction records |
| CARDOUT | CVACT02Y (150 bytes) | Card records |
| ERROUT | 132 bytes | Validation error records |

## 4. Processing Logic

```
For each EXPFILE record:
  1. Read EXPORT-REC-TYPE
  2. Based on type, extract data from EXPORT-RECORD-DATA
  3. Validate checksums/data integrity
  4. Write to appropriate output file
  5. If validation fails → write to ERROUT
```

## 5. Copybooks Used

CVEXPORT, CVCUS01Y, CVACT01Y, CVACT03Y, CVTRA05Y, CVACT02Y
