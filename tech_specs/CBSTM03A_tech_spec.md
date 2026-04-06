# Technical Specification: CBSTM03A — Account Statement Generator

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | CBSTM03A |
| Source File | `app/cbl/CBSTM03A.CBL` |
| Type | Batch COBOL |
| JCL | CREASTMT job, STEP040 |

## 2. Purpose

CBSTM03A generates **account statements in two formats**: plain text (STMTFILE, 80-byte) and HTML (HTMLFILE, 100-byte). It reads transaction data via the CBSTM03B subroutine, along with cross-reference, customer, and account data. Intentionally uses complex COBOL features (ALTER/GO TO, 2D arrays, COMP/COMP-3) for modernization tooling testing.

## 3. Files Accessed

| File DD | Direction | Format |
|---------|-----------|--------|
| STMTFILE | Output | Sequential, 80-byte (plain text statement) |
| HTMLFILE | Output | Sequential, 100-byte (HTML statement) |

All other file I/O is delegated to CBSTM03B:
- TRNXFILE (transactions indexed by card+tran-id)
- XREFFILE (card cross-reference)
- CUSTFILE (customer data)
- ACCTFILE (account data)

## 4. Inter-Program Calls

| Target | Method | Interface |
|--------|--------|-----------|
| CBSTM03B | CALL USING WS-M03B-AREA | DD name (8), operation code (1), return code (2), key (25), key length (S9(4)), data buffer (1000) |

### Operation Codes
| Code | Operation |
|------|-----------|
| O | Open file |
| C | Close file |
| R | Read next (sequential) |
| K | Read by key (random) |
| W | Write |
| Z | Rewrite |

## 5. Statement Content

Statement lines (ST-LINE0 through ST-LINE14) include:
- Account ID
- Current balance
- FICO score
- Credit limit
- Customer name and address
- Transaction detail lines with amounts

## 6. Copybooks Used

COSTM01 (statement working storage), CVACT03Y, CUSTREC, CVACT01Y
