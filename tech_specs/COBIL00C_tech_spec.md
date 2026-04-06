# Technical Specification: COBIL00C — Bill Payment

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | COBIL00C |
| Source File | `app/cbl/COBIL00C.cbl` |
| Type | CICS Online |
| Transaction ID | CB00 |
| BMS Mapset | COBIL00 |
| BMS Map | COBIL0A |

## 2. Purpose

COBIL00C processes **online bill payments**. It looks up an account balance, requires Y/N confirmation, then creates a transaction record of type '02' (Payment) and reduces the account's current balance to zero.

## 3. Copybooks Used

| Copybook | Purpose |
|----------|---------|
| COCOM01Y | CARDDEMO-COMMAREA (extended with CDEMO-CB00-INFO) |
| COBIL00 | BMS symbolic map |
| COTTL01Y, CSDAT01Y, CSMSG01Y | Standard infrastructure |
| CVACT01Y | ACCOUNT-RECORD layout |
| CVACT03Y | CARD-XREF-RECORD layout |
| CVTRA05Y | TRAN-RECORD layout |
| DFHAID, DFHBMSCA | CICS constants |

## 4. VSAM Files Accessed

| File DD | Access Mode | Operations | Key |
|---------|-------------|------------|-----|
| ACCTDAT | Update | READ with UPDATE, REWRITE | ACCT-ID 9(11) |
| TRANSACT | Browse + Write | STARTBR HIGH-VALUES, READPREV, ENDBR, WRITE | TRAN-ID X(16) |
| CXACAIX | Read | READ by account ID | XREF-ACCT-ID 9(11) |

## 5. Screen Fields

### Input Fields
| Field | Length | Description |
|-------|--------|-------------|
| ACTIDIN | 11 | Account ID (cursor initial) |
| CONFIRM | 1 | Y/N confirmation |

### Output Fields
| Field | Length | Description |
|-------|--------|-------------|
| CURBAL | 14 | Current balance display |

### Function Keys
| Key | Action |
|-----|--------|
| ENTER | Process payment |
| PF3 | Back to menu |
| PF4 | Clear account input |

## 6. Program Flow

```
1. Enter with Account ID:
   a. READ ACCTDAT with UPDATE
   b. Display current balance
   c. If balance <= 0: "You have nothing to pay"

2. If CONFIRM = 'Y':
   a. READ CXACAIX to get card number for this account
   b. Find max TRAN-ID (STARTBR HIGH-VALUES, READPREV)
   c. Increment to get new TRAN-ID
   d. Build TRAN-RECORD:
      - TRAN-TYPE-CD = '02' (Payment)
      - TRAN-CAT-CD = 2
      - TRAN-SOURCE = 'POS TERM'
      - TRAN-DESC = 'BILL PAYMENT - ONLINE'
      - TRAN-AMT = ACCT-CURR-BAL (full balance)
      - TRAN-MERCHANT-ID = 999999999
      - TRAN-MERCHANT-NAME = 'BILL PAYMENT'
      - Timestamps via EXEC CICS ASKTIME / FORMATTIME
   e. WRITE to TRANSACT
   f. COMPUTE ACCT-CURR-BAL = ACCT-CURR-BAL - TRAN-AMT
   g. REWRITE ACCTDAT
```

## 7. Business Rules

1. **Payment is always for the full current balance** — no partial payment option.
2. Payment creates a type '02' transaction with category 2.
3. Merchant ID is hardcoded to 999999999 for bill payments.
4. If balance is zero or negative, no payment is processed.
5. Transaction ID generation uses the same max+1 pattern as COTRN02C.

## 8. Error Handling

| Condition | Message |
|-----------|---------|
| ACCTDAT READ NOTFND | "Account ID NOT found" |
| Other READ errors | "Unable to lookup Account" |
| TRANSACT WRITE failure | "Unable to Add Bill pay Transaction" |
| Balance <= 0 | "You have nothing to pay" |

## 9. Inter-Program Communication

| Target | Method | Condition |
|--------|--------|-----------|
| CDEMO-FROM-PROGRAM | XCTL | PF3 |
| COMEN01C | XCTL | PF3 default |
