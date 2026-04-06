# Technical Specification: CBEXPORT — Data Migration Export

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | CBEXPORT |
| Source File | `app/cbl/CBEXPORT.cbl` |
| Type | Batch COBOL |

## 2. Purpose

CBEXPORT reads all five master VSAM files sequentially and writes a **consolidated 500-byte multi-record-type export file** (EXPFILE KSDS) for branch migration. Each source record produces one export record, discriminated by EXPORT-REC-TYPE.

## 3. Files Accessed

### Input (all KSDS sequential)
| File DD | Layout | Description |
|---------|--------|-------------|
| CUSTFILE | CVCUS01Y (500 bytes) | Customer records |
| ACCTFILE | CVACT01Y (300 bytes) | Account records |
| XREFFILE | CVACT03Y (50 bytes) | Card cross-reference |
| TRANSACT | CVTRA05Y (350 bytes) | Transaction records |
| CARDFILE | CVACT02Y (150 bytes) | Card records |

### Output
| File DD | Format | Key | Description |
|---------|--------|-----|-------------|
| EXPFILE | KSDS fixed 500 bytes | EXPORT-SEQUENCE-NUM 9(9) COMP (position 28, length 4) | Multi-record export |

## 4. Export Record Layout (CVEXPORT.cpy)

| Offset | Field | Description |
|--------|-------|-------------|
| 1 | EXPORT-REC-TYPE X(1) | Record type discriminator |
| 2–27 | EXPORT-TIMESTAMP X(26) | Export timestamp |
| 28–31 | EXPORT-SEQUENCE-NUM 9(9) COMP | VSAM key (4 bytes) |
| 32–35 | EXPORT-BRANCH-ID X(4) | Branch identifier |
| 36–40 | EXPORT-REGION-CODE X(5) | Region code |
| 41–500 | EXPORT-RECORD-DATA X(460) | Record data (REDEFINES per type) |

### Record Types
| Type | REDEFINES | Source |
|------|-----------|--------|
| Customer | EXPORT-CUSTOMER-DATA | CUSTFILE — uses COMP/COMP-3 encoding |
| Account | EXPORT-ACCOUNT-DATA | ACCTFILE — balances as COMP-3 |
| Transaction | EXPORT-TRANSACTION-DATA | TRANSACT |
| Card Xref | EXPORT-CARD-XREF-DATA | XREFFILE |
| Card | EXPORT-CARD-DATA | CARDFILE |

## 5. Copybooks Used

CVEXPORT, CVCUS01Y, CVACT01Y, CVACT03Y, CVTRA05Y, CVACT02Y
