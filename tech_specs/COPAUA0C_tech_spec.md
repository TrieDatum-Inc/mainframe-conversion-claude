# Technical Specification: COPAUA0C — Authorization Decision Engine

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | COPAUA0C |
| Source File | `app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl` |
| Type | CICS Online (IMS + MQ) |
| Transaction ID | CP00 |
| Sub-Application | app-authorization-ims-db2-mq |

## 2. Purpose

COPAUA0C is the **card authorization decision engine**. It processes incoming authorization request messages from an MQ queue, evaluates the card and account state against VSAM master files, records the authorization decision in IMS, and sends a reply message back to the MQ reply queue.

## 3. Technology Stack

- **CICS** for transaction management
- **IBM MQ** for message queuing (request/reply pattern)
- **IMS DL/I** for hierarchical database storage (via CICS-IMS interface)
- **VSAM** for master data reads

## 4. Copybooks Used

| Copybook | Purpose |
|----------|---------|
| CCPAURQY | MQ authorization request message layout |
| CCPAURLY | MQ authorization response message layout |
| CCPAUERY | Error log record layout |
| CIPAUSMY | IMS summary segment layout (PAUTSUM0) |
| CIPAUDTY | IMS detail segment layout (PAUTDTL1) |
| COCOM01Y | CARDDEMO-COMMAREA |
| CMQODV, CMQMDV, CMQPMOV, CMQGMOV, CMQV, CMQTML | IBM MQ API structures |

## 5. Data Access

### MQ Queues
| Queue | Direction | Purpose |
|-------|-----------|---------|
| Request Queue | GET | Incoming authorization requests (up to 500 per invocation) |
| Reply Queue | PUT | Authorization response messages |
| Error Queue | PUT | Error records |

### IMS Database (DBPAUTP0 via PSB PSBPAUTB, PCB +1)
| Segment | Operation | Description |
|---------|-----------|-------------|
| PAUTSUM0 (root) | ISRT | Account-level authorization summary (one per account) |
| PAUTDTL1 (child) | ISRT | Individual authorization detail (one per request) |

### VSAM Files (CICS READ)
| File DD | Purpose |
|---------|---------|
| ACCTDAT | Account validation |
| CUSTDAT | Customer lookup |
| CARDDAT | Card validation |
| CARDAIX | Card alternate index (by account) |
| CCXREF | Card-to-account cross reference |

## 6. Authorization Business Logic

### Decline Reason Flags
| Flag | Code | Meaning |
|------|------|---------|
| I | INSUFFICIENT-FUND | Available credit < requested amount |
| A | CARD-NOT-ACTIVE | Card status is not 'Y' |
| C | ACCOUNT-CLOSED | Account status is not active |
| F | CARD-FRAUD | Card flagged for fraud |
| M | MERCHANT-FRAUD | Merchant flagged for fraud |

### Available Amount Calculation
```
WS-AVAILABLE-AMT = credit-limit - current-balance - pending-approved-amount
```

### Response Codes
| Response | Code | Description |
|----------|------|-------------|
| Approved | 'A' | All validations passed, sufficient funds |
| Declined | 'D' | One or more decline reasons triggered |

## 7. Processing Flow

```
1. MQOPEN request queue, reply queue
2. Loop (up to 500 messages):
   a. MQGET next message from request queue
   b. Parse CCPAURQY request record
   c. READ VSAM files to validate card/account/customer
   d. Check decline conditions (funds, active, fraud, etc.)
   e. Build IMS segments:
      - ISRT PAUTSUM0 (summary — insert or update)
      - ISRT PAUTDTL1 (detail — new record per authorization)
   f. Build CCPAURLY reply message with auth code, response, amount
   g. MQPUT reply to reply queue
3. MQCLOSE all queues
4. MQDISC from queue manager
```

## 8. IMS Database Structure

```
DBPAUTP0 (HIDAM/VSAM)
└── PAUTSUM0 (Root Segment, 100 bytes)
    Key: ACCNTID (PA-ACCT-ID, packed decimal 6 bytes)
    Fields: credit limits, balances, approved/declined counts and amounts
    │
    └── PAUTDTL1 (Child Segment, 200 bytes)
        Key: PAUT9CTS (PA-AUTH-DATE-9C + PA-AUTH-TIME-9C, COMP-3 timestamp)
        Fields: card number, auth type, amounts, merchant, response, fraud status
```

## 9. Error Handling

Errors are logged to the MQ error queue using the CCPAUERY layout with severity levels:
- L = Log, I = Info, W = Warning, C = Critical
- Subsystem codes: A=App, C=CICS, I=IMS, D=DB2, M=MQ, F=File
