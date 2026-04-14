# Database Specification: PostgreSQL Schema

## Document Purpose

Defines the complete PostgreSQL schema mapping all VSAM KSDS files, VSAM AIX (alternate index) files, DB2 tables, and IMS database segments from the CardDemo mainframe application into a unified relational database.

---

## 1. COBOL-to-PostgreSQL Data Type Mapping

| COBOL Picture | COBOL Usage | PostgreSQL Type | Notes |
|--------------|-------------|-----------------|-------|
| PIC X(n) | DISPLAY | VARCHAR(n) | Trim trailing spaces on read/write |
| PIC 9(n) | DISPLAY | INTEGER or BIGINT | Use BIGINT when n > 9 |
| PIC 9(n)V9(m) | DISPLAY | NUMERIC(n+m, m) | Preserve exact decimal precision |
| PIC S9(n)V9(m) | COMP-3 | NUMERIC(n+m, m) | Signed packed decimal → signed numeric |
| PIC S9(n) | COMP | INTEGER or BIGINT | Binary integer |
| PIC S9(9) | COMP | INTEGER | Standard 4-byte binary |
| PIC 9(8) (date CCYYMMDD) | DISPLAY | DATE | Convert on insert/read |
| PIC X(10) (date YYYY-MM-DD) | DISPLAY | DATE | ISO format stored as DATE |
| PIC 9(11) (account ID) | DISPLAY | BIGINT | 11-digit numeric key |
| PIC X(16) (card number) | DISPLAY | CHAR(16) | Fixed 16-char; PCI-DSS: store masked or tokenized |
| PIC X(8) (user ID) | DISPLAY | VARCHAR(8) | Right-pad to 8 for VSAM key compatibility |
| PIC X(1) (flag Y/N) | DISPLAY | CHAR(1) with CHECK | CHECK (col IN ('Y','N')) |
| PIC X(1) (type A/U) | DISPLAY | VARCHAR(1) with CHECK | CHECK (col IN ('A','U')) |
| OCCURS n TIMES | — | Child table or JSONB array | Prefer separate table for relational integrity |
| Level 88 conditions | — | ENUM type or CHECK constraint | Map 88-level values to allowed values |

---

## 2. Table Definitions

### 2.1 `users` Table
**Source**: USRSEC VSAM KSDS (CSUSR01Y copybook)
**Key**: SEC-USR-ID X(8) → `user_id VARCHAR(8) PRIMARY KEY`

```sql
CREATE TABLE users (
    user_id         VARCHAR(8)   NOT NULL,
    first_name      VARCHAR(20)  NOT NULL,
    last_name       VARCHAR(20)  NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,    -- bcrypt hash; replaces SEC-USR-PWD X(8) plain text
    user_type       CHAR(1)      NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_users PRIMARY KEY (user_id),
    CONSTRAINT chk_users_type CHECK (user_type IN ('A', 'U'))
);

CREATE INDEX idx_users_last_name ON users(last_name);
CREATE INDEX idx_users_user_type ON users(user_type);
```

**Migration Note**: SEC-USR-FILLER X(23) is not migrated (unused padding). SEC-USR-PWD X(8) is hashed with bcrypt before storage; the original plain-text passwords must be re-set or migrated with a temporary forced-reset flag.

---

### 2.2 `accounts` Table
**Source**: ACCTDAT VSAM KSDS (CVACT01Y copybook)
**Key**: ACCT-ID 9(11) → `account_id BIGINT PRIMARY KEY`
**Record length**: 300 bytes

```sql
CREATE TABLE accounts (
    account_id              BIGINT          NOT NULL,
    active_status           CHAR(1)         NOT NULL DEFAULT 'Y',
    current_balance         NUMERIC(12, 2)  NOT NULL DEFAULT 0.00,
    credit_limit            NUMERIC(12, 2)  NOT NULL DEFAULT 0.00,
    cash_credit_limit       NUMERIC(12, 2)  NOT NULL DEFAULT 0.00,
    open_date               DATE,
    expiration_date         DATE,
    reissue_date            DATE,
    curr_cycle_credit       NUMERIC(12, 2)  NOT NULL DEFAULT 0.00,
    curr_cycle_debit        NUMERIC(12, 2)  NOT NULL DEFAULT 0.00,
    zip_code                VARCHAR(10),
    group_id                VARCHAR(10),
    created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_accounts PRIMARY KEY (account_id),
    CONSTRAINT chk_accounts_active CHECK (active_status IN ('Y', 'N')),
    CONSTRAINT chk_accounts_credit_limit CHECK (credit_limit >= 0),
    CONSTRAINT chk_accounts_cash_limit CHECK (cash_credit_limit >= 0),
    CONSTRAINT chk_accounts_cash_lte_credit CHECK (cash_credit_limit <= credit_limit)
);

CREATE INDEX idx_accounts_active_status ON accounts(active_status);
CREATE INDEX idx_accounts_group_id ON accounts(group_id);
```

**Field Mapping**:
| COBOL Field | PIC | PostgreSQL Column | Notes |
|------------|-----|------------------|-------|
| ACCT-ID | 9(11) | account_id BIGINT | Primary key |
| ACCT-ACTIVE-STATUS | X(1) | active_status CHAR(1) | Y/N |
| ACCT-CURR-BAL | S9(10)V99 COMP-3 | current_balance NUMERIC(12,2) | |
| ACCT-CREDIT-LIMIT | S9(10)V99 COMP-3 | credit_limit NUMERIC(12,2) | |
| ACCT-CASH-CREDIT-LIMIT | S9(10)V99 COMP-3 | cash_credit_limit NUMERIC(12,2) | |
| ACCT-OPEN-DATE | X(10) | open_date DATE | YYYY-MM-DD format |
| ACCT-EXPIRAION-DATE | X(10) | expiration_date DATE | Note: typo in source preserved as comment |
| ACCT-REISSUE-DATE | X(10) | reissue_date DATE | |
| ACCT-CURR-CYC-CREDIT | S9(10)V99 COMP-3 | curr_cycle_credit NUMERIC(12,2) | |
| ACCT-CURR-CYC-DEBIT | S9(10)V99 COMP-3 | curr_cycle_debit NUMERIC(12,2) | |
| ACCT-ADDR-ZIP | X(10) | zip_code VARCHAR(10) | |
| ACCT-GROUP-ID | X(10) | group_id VARCHAR(10) | |
| FILLER X(178) | — | (not stored) | Padding bytes discarded |

---

### 2.3 `customers` Table
**Source**: CUSTDAT VSAM KSDS (CVCUS01Y copybook)
**Key**: CUST-ID 9(9) → `customer_id INTEGER PRIMARY KEY`
**Record length**: 500 bytes

```sql
CREATE TABLE customers (
    customer_id             INTEGER         NOT NULL,
    first_name              VARCHAR(25)     NOT NULL,
    middle_name             VARCHAR(25),
    last_name               VARCHAR(25)     NOT NULL,
    street_address_1        VARCHAR(50),
    street_address_2        VARCHAR(50),
    city                    VARCHAR(50),
    state_code              CHAR(2),
    zip_code                VARCHAR(10),
    country_code            CHAR(3),
    phone_number_1          VARCHAR(15),
    phone_number_2          VARCHAR(15),
    ssn                     VARCHAR(11),    -- format: NNN-NN-NNNN; encrypted at rest recommended
    date_of_birth           DATE,
    fico_score              SMALLINT,
    government_id_ref       VARCHAR(20),
    eft_account_id          VARCHAR(10),
    primary_card_holder_flag CHAR(1)        NOT NULL DEFAULT 'Y',
    created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_customers PRIMARY KEY (customer_id),
    CONSTRAINT chk_customers_primary_flag CHECK (primary_card_holder_flag IN ('Y', 'N')),
    CONSTRAINT chk_customers_fico CHECK (fico_score IS NULL OR (fico_score >= 300 AND fico_score <= 850))
);

CREATE INDEX idx_customers_last_name ON customers(last_name);
CREATE INDEX idx_customers_ssn ON customers(ssn);  -- for lookup; consider encryption
```

**Field Mapping (CVCUS01Y)**:
| COBOL Field | PIC | PostgreSQL Column |
|------------|-----|------------------|
| CUST-ID | 9(9) | customer_id INTEGER |
| CUST-FIRST-NAME | X(25) | first_name |
| CUST-MIDDLE-NAME | X(25) | middle_name |
| CUST-LAST-NAME | X(25) | last_name |
| CUST-ADDR-LINE-1 | X(50) | street_address_1 |
| CUST-ADDR-LINE-2 | X(50) | street_address_2 |
| CUST-ADDR-CITY | X(50) | city |
| CUST-ADDR-STATE-CD | X(2) | state_code |
| CUST-ADDR-COUNTRY-CD | X(3) | country_code |
| CUST-ADDR-ZIP | X(10) | zip_code |
| CUST-PHONE-NUM-1 | X(15) | phone_number_1 |
| CUST-PHONE-NUM-2 | X(15) | phone_number_2 |
| CUST-SSN | 9(9) (parts: 3+2+4) | ssn VARCHAR(11) formatted |
| CUST-DOB-YYYY-MM-DD | X(10) | date_of_birth DATE |
| CUST-EFT-ACCOUNT-ID | X(10) | eft_account_id |
| CUST-PRI-CARD-HOLDER-IND | X(1) | primary_card_holder_flag |
| CUST-FICO-CREDIT-SCORE | 9(3) | fico_score SMALLINT |
| CUST-GOVT-ISSUED-ID | X(20) | government_id_ref |

---

### 2.4 `account_customer_xref` Table
**Source**: Derived from ACCTDAT/CUSTDAT relationship (CVACT04Y or equivalent join key)
**Purpose**: Links accounts to customers (COACTUPC reads both via account ID → customer ID)

```sql
CREATE TABLE account_customer_xref (
    account_id      BIGINT      NOT NULL,
    customer_id     INTEGER     NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_acct_cust_xref PRIMARY KEY (account_id, customer_id),
    CONSTRAINT fk_acctcust_account FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    CONSTRAINT fk_acctcust_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE INDEX idx_acctcust_customer ON account_customer_xref(customer_id);
```

---

### 2.5 `credit_cards` Table
**Source**: CARDDAT VSAM KSDS (CVACT02Y copybook)
**Key**: CARD-NUM X(16) → `card_number CHAR(16) PRIMARY KEY`
**Record length**: 150 bytes

```sql
CREATE TABLE credit_cards (
    card_number             CHAR(16)        NOT NULL,
    account_id              BIGINT          NOT NULL,
    customer_id             INTEGER         NOT NULL,
    card_embossed_name      VARCHAR(50),
    active_status           CHAR(1)         NOT NULL DEFAULT 'Y',
    expiration_date         DATE,
    expiration_day          SMALLINT,       -- hidden EXPDAY field from COCRDUP map
    cvv                     VARCHAR(4),     -- not shown in any update screen; stored encrypted
    created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_cards PRIMARY KEY (card_number),
    CONSTRAINT fk_cards_account FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    CONSTRAINT fk_cards_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    CONSTRAINT chk_cards_active CHECK (active_status IN ('Y', 'N')),
    CONSTRAINT chk_cards_exp_month CHECK (EXTRACT(MONTH FROM expiration_date) BETWEEN 1 AND 12),
    CONSTRAINT chk_cards_exp_year CHECK (EXTRACT(YEAR FROM expiration_date) BETWEEN 1950 AND 2099)
);

CREATE INDEX idx_cards_account_id ON credit_cards(account_id);
CREATE INDEX idx_cards_customer_id ON credit_cards(customer_id);
CREATE INDEX idx_cards_active_status ON credit_cards(active_status);
```

---

### 2.6 `card_account_xref` Table
**Source**: CARDXREF VSAM KSDS with AIX (CVACT03Y copybook: CARD-XREF-RECORD 50 bytes)
**Keys**: Primary = XREF-CARD-NUM X(16); AIX = XREF-ACCT-ID 9(11)
**Note**: COACTVWC reads this via AIX (account → cards). COTRN02C reads this by card → account.

```sql
CREATE TABLE card_account_xref (
    card_number     CHAR(16)    NOT NULL,
    customer_id     INTEGER     NOT NULL,
    account_id      BIGINT      NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_card_xref PRIMARY KEY (card_number),
    CONSTRAINT fk_cardxref_account FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    CONSTRAINT fk_cardxref_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Replaces VSAM AIX on XREF-ACCT-ID: allows lookup by account_id to find all cards
CREATE INDEX idx_cardxref_account ON card_account_xref(account_id);
CREATE INDEX idx_cardxref_customer ON card_account_xref(customer_id);
```

---

### 2.7 `transactions` Table
**Source**: TRANSACT VSAM KSDS (CVTRA05Y copybook)
**Key**: TRAN-ID X(16) → `transaction_id VARCHAR(16) PRIMARY KEY`

```sql
CREATE TABLE transactions (
    transaction_id          VARCHAR(16)     NOT NULL,
    card_number             CHAR(16)        NOT NULL,
    transaction_type_code   VARCHAR(2)      NOT NULL,
    transaction_category_code VARCHAR(4),
    transaction_source      VARCHAR(10),
    description             VARCHAR(60),
    amount                  NUMERIC(10, 2)  NOT NULL,
    original_date           DATE,
    processed_date          DATE,
    merchant_id             VARCHAR(9),
    merchant_name           VARCHAR(30),
    merchant_city           VARCHAR(25),
    merchant_zip            VARCHAR(10),
    created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_transactions PRIMARY KEY (transaction_id),
    CONSTRAINT fk_transactions_card FOREIGN KEY (card_number) REFERENCES credit_cards(card_number),
    CONSTRAINT fk_transactions_type FOREIGN KEY (transaction_type_code) REFERENCES transaction_types(type_code)
);

-- Replaces VSAM sequential browse starting at HIGH-VALUES for max ID
CREATE SEQUENCE transaction_id_seq START 1;

CREATE INDEX idx_transactions_card_number ON transactions(card_number);
CREATE INDEX idx_transactions_type_code ON transactions(transaction_type_code);
CREATE INDEX idx_transactions_original_date ON transactions(original_date);
CREATE INDEX idx_transactions_processed_date ON transactions(processed_date);
CREATE INDEX idx_transactions_merchant_id ON transactions(merchant_id);
```

**COTRN02C Special Fields**:
| COBOL Field | PostgreSQL Column | Notes |
|------------|------------------|-------|
| TRAN-ID X(16) | transaction_id | Was generated via READPREV+ADD1; now uses sequence |
| TRAN-TYPE-CD X(2) | transaction_type_code | FK to transaction_types |
| TRAN-CAT-CD 9(4) | transaction_category_code | 4-digit numeric category |
| TRAN-SOURCE X(10) | transaction_source | 'POS TERM' for bill payment |
| TRAN-DESC X(60) | description | |
| TRAN-AMT S9(7)V99 | amount | Signed |
| TRAN-ORIG-TS X(10) | original_date | YYYY-MM-DD |
| TRAN-PROC-TS X(10) | processed_date | YYYY-MM-DD |
| TRAN-MERCHANT-ID 9(9) | merchant_id | 9-digit numeric stored as string |

---

### 2.8 `transaction_types` Table
**Source**: DB2 table CARDDEMO.TRANSACTION_TYPE (COTRTLIC, COTRTUPC)

```sql
CREATE TABLE transaction_types (
    type_code       VARCHAR(2)      NOT NULL,
    description     VARCHAR(50)     NOT NULL,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_transaction_types PRIMARY KEY (type_code),
    CONSTRAINT chk_tt_type_code_numeric CHECK (type_code ~ '^[0-9]{1,2}$'),
    CONSTRAINT chk_tt_type_code_nonzero CHECK (type_code::INTEGER > 0),
    CONSTRAINT chk_tt_description_alphanum CHECK (description ~ '^[A-Za-z0-9 ]+$')
);
```

**COTRTLIC / COTRTUPC Business Rules**:
- type_code must be numeric 01–99 (original COBOL: NUMERIC test + not zero check)
- description must be alphanumeric only (no special characters — from COTRTUPC validation)
- DELETE is blocked if FK constraint exists (SQLCODE -532 in original → FK violation in PostgreSQL)

---

### 2.9 `authorization_summary` Table
**Source**: IMS PAUTSUM0 root segment (CIPAUSMY copybook)
**Replaces**: HISAM root segment under DBPAUTP0 database

```sql
CREATE TABLE authorization_summary (
    account_id              BIGINT          NOT NULL,
    credit_limit            NUMERIC(12, 2)  NOT NULL DEFAULT 0.00,
    cash_limit              NUMERIC(12, 2)  NOT NULL DEFAULT 0.00,
    credit_balance          NUMERIC(12, 2)  NOT NULL DEFAULT 0.00,
    cash_balance            NUMERIC(12, 2)  NOT NULL DEFAULT 0.00,
    approved_auth_count     INTEGER         NOT NULL DEFAULT 0,
    declined_auth_count     INTEGER         NOT NULL DEFAULT 0,
    approved_auth_amount    NUMERIC(12, 2)  NOT NULL DEFAULT 0.00,
    declined_auth_amount    NUMERIC(12, 2)  NOT NULL DEFAULT 0.00,
    created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_auth_summary PRIMARY KEY (account_id),
    CONSTRAINT fk_authsum_account FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);
```

---

### 2.10 `authorization_detail` Table
**Source**: IMS PAUTDTL1 child segment (CIPAUDTY copybook; 200 bytes)
**Replaces**: HISAM child segments under PAUTSUM0

**IMS Key Note**: IMS uses inverted timestamp key (999999999 - AUTH-TIME-9C) for descending order. PostgreSQL uses `processed_at DESC` ordering instead.

```sql
CREATE TABLE authorization_detail (
    auth_id                 BIGSERIAL       NOT NULL,
    account_id              BIGINT          NOT NULL,
    transaction_id          VARCHAR(16)     NOT NULL,
    card_number             CHAR(16)        NOT NULL,
    auth_date               DATE            NOT NULL,
    auth_time               TIME            NOT NULL,
    auth_response_code      CHAR(2)         NOT NULL,  -- '00'=approved, other=declined
    auth_code               VARCHAR(6),
    transaction_amount      NUMERIC(10, 2)  NOT NULL,
    pos_entry_mode          VARCHAR(4),
    auth_source             VARCHAR(10),
    mcc_code                VARCHAR(4),
    card_expiry_date        VARCHAR(5),
    auth_type               VARCHAR(14),
    match_status            CHAR(1)         NOT NULL DEFAULT 'P',  -- P/D/E/M
    fraud_status            CHAR(1)         NOT NULL DEFAULT 'N',  -- N/F/R (N=none, F=confirmed, R=removed)
    merchant_name           VARCHAR(25),
    merchant_id             VARCHAR(15),
    merchant_city           VARCHAR(25),
    merchant_state          CHAR(2),
    merchant_zip            VARCHAR(10),
    processed_at            TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_auth_detail PRIMARY KEY (auth_id),
    CONSTRAINT fk_authdet_summary FOREIGN KEY (account_id) REFERENCES authorization_summary(account_id),
    CONSTRAINT chk_authdet_match CHECK (match_status IN ('P', 'D', 'E', 'M')),
    CONSTRAINT chk_authdet_fraud CHECK (fraud_status IN ('N', 'F', 'R'))
);

CREATE INDEX idx_authdet_account_id ON authorization_detail(account_id);
CREATE INDEX idx_authdet_card_number ON authorization_detail(card_number);
CREATE INDEX idx_authdet_processed_at ON authorization_detail(processed_at DESC);  -- replaces inverted IMS key
CREATE INDEX idx_authdet_transaction_id ON authorization_detail(transaction_id);
CREATE INDEX idx_authdet_fraud_status ON authorization_detail(fraud_status);
```

**COPAUS2C DB2 Integration**: The original CARDDEMO.AUTHFRDS DB2 table had 26 columns storing fraud flag data. This is merged into `authorization_detail` via the `fraud_status` column and a separate `auth_fraud_log` table below.

---

### 2.11 `auth_fraud_log` Table
**Source**: DB2 CARDDEMO.AUTHFRDS table (COPAUS2C)
**Purpose**: Immutable audit log of fraud flag toggles (COPAUS2C inserts on fraud set; updates only AUTH_FRAUD and FRAUD_RPT_DATE on duplicate)

```sql
CREATE TABLE auth_fraud_log (
    log_id              BIGSERIAL       NOT NULL,
    auth_id             BIGINT          NOT NULL,
    transaction_id      VARCHAR(16)     NOT NULL,
    card_number         CHAR(16)        NOT NULL,
    account_id          BIGINT          NOT NULL,
    fraud_flag          CHAR(1)         NOT NULL,   -- 'F'=confirmed, 'R'=removed
    fraud_report_date   TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    auth_response_code  CHAR(2),
    auth_amount         NUMERIC(10, 2),
    merchant_name       VARCHAR(22),    -- DB2 AUTHFRDS MERCHANT_NAME VARCHAR(22)
    merchant_id         VARCHAR(9),
    logged_at           TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_fraud_log PRIMARY KEY (log_id),
    CONSTRAINT fk_fraudlog_auth FOREIGN KEY (auth_id) REFERENCES authorization_detail(auth_id)
);

CREATE INDEX idx_fraudlog_transaction ON auth_fraud_log(transaction_id);
CREATE INDEX idx_fraudlog_account ON auth_fraud_log(account_id);
CREATE UNIQUE INDEX idx_fraudlog_unique_auth ON auth_fraud_log(auth_id, fraud_flag) WHERE fraud_flag = 'F';  -- replaces SQLCODE -803 duplicate key handling
```

---

### 2.12 `report_requests` Table
**Source**: CORPT00C TDQ-based batch job submission
**Purpose**: Replace JCL submission via TDQ QUEUE='JOBS'; store request state for background processing

```sql
CREATE TABLE report_requests (
    request_id      BIGSERIAL   NOT NULL,
    report_type     CHAR(1)     NOT NULL,       -- 'M'=monthly, 'Y'=yearly, 'C'=custom
    start_date      DATE,
    end_date        DATE,
    requested_by    VARCHAR(8)  NOT NULL,        -- user_id
    status          VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    result_path     VARCHAR(500),
    error_message   VARCHAR(500),
    requested_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,
    CONSTRAINT pk_report_requests PRIMARY KEY (request_id),
    CONSTRAINT fk_rptreq_user FOREIGN KEY (requested_by) REFERENCES users(user_id),
    CONSTRAINT chk_rptreq_type CHECK (report_type IN ('M', 'Y', 'C')),
    CONSTRAINT chk_rptreq_status CHECK (status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED')),
    CONSTRAINT chk_rptreq_custom_dates CHECK (
        report_type != 'C' OR (start_date IS NOT NULL AND end_date IS NOT NULL AND end_date >= start_date)
    )
);
```

---

## 3. Entity-Relationship Summary

```
users (user_id PK)
    └── report_requests (requested_by FK)

accounts (account_id PK)
    ├── account_customer_xref (account_id FK)
    ├── credit_cards (account_id FK)
    ├── card_account_xref (account_id FK)
    ├── authorization_summary (account_id PK/FK)
    └── auth_fraud_log (account_id FK)

customers (customer_id PK)
    ├── account_customer_xref (customer_id FK)
    ├── credit_cards (customer_id FK)
    └── card_account_xref (customer_id FK)

credit_cards (card_number PK)
    ├── card_account_xref (card_number FK)
    ├── transactions (card_number FK)
    └── authorization_detail (card_number FK)

transaction_types (type_code PK)
    └── transactions (transaction_type_code FK)

authorization_summary (account_id PK)
    └── authorization_detail (account_id FK)

authorization_detail (auth_id PK)
    └── auth_fraud_log (auth_id FK)
```

---

## 4. Audit Column Strategy

All mutable tables include `created_at` and `updated_at` columns. The `updated_at` column is updated by a trigger on every row modification, replacing the manual WS-DATACHANGED-FLAG pattern in COACTUPC and the CCUP-OLD-DETAILS snapshot in COCRDUPC.

```sql
-- Trigger function for automatic updated_at management
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all mutable tables
CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_accounts_updated_at
    BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_customers_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_cards_updated_at
    BEFORE UPDATE ON credit_cards
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_transactions_updated_at
    BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_tt_updated_at
    BEFORE UPDATE ON transaction_types
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_authdet_updated_at
    BEFORE UPDATE ON authorization_detail
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

## 5. Index Strategy

### Access Pattern Analysis from COBOL Programs

| Program | Access Pattern | Index Required |
|---------|---------------|----------------|
| COSGN00C | READ USRSEC by SEC-USR-ID | PK on users.user_id |
| COUSR00C | STARTBR USRSEC from LOW-VALUES/filter | users.user_id (PK, already btree) |
| COACTVWC | READ ACCTDAT by ACCT-ID | PK on accounts.account_id |
| COACTVWC | READ CARDAIX by ACCT-ID | idx_cardxref_account |
| COCRDLIC | STARTBR CARDDAT with optional account/card filter | idx_cards_account_id; PK on card_number |
| COTRN00C | STARTBR TRANSACT from filter/anchor | idx_transactions_original_date; PK |
| COTRN02C | STARTBR CCXREF by card → account lookup | PK on card_account_xref.card_number |
| COPAUS0C | GU PAUTSUM0 by account ID | PK on authorization_summary.account_id |
| COTRTLIC | DB2 cursor >= start_key DESC filter | PK on transaction_types.type_code |

---

## 6. Seed Data Requirements

Each table requires a minimum of 10 realistic seed rows. Seed data files are located in `backend/sql/seed_data.sql`.

### Key Seed Constraints

- `users`: Include at least 2 Admin users (user_type='A') and 8 Regular users (user_type='U'). Passwords are bcrypt hashes of test passwords.
- `accounts`: 10 accounts with varied balances, credit limits, active statuses.
- `customers`: 10 customers, some shared across multiple accounts.
- `credit_cards`: 10–15 cards linked to the seeded accounts.
- `transactions`: At least 50 transactions across the seeded cards (to exercise pagination).
- `transaction_types`: 10 types including type code '01' (standard) and '02' (bill payment per COBIL00C).
- `authorization_summary`: 10 summaries corresponding to seeded accounts.
- `authorization_detail`: 25+ authorization records to exercise COPAUS0C pagination (5 per page).

---

## 7. Database Constraints Replacing COBOL Validation

| COBOL Validation | PostgreSQL Constraint |
|-----------------|----------------------|
| COUSR01C: DUPKEY/DUPREC on WRITE | UNIQUE constraint on users.user_id (PK) |
| COACTUPC: SSN part 1 not 0/666/900-999 | CHECK constraint on customers.ssn |
| COACTUPC: FICO score valid range | CHECK (fico_score BETWEEN 300 AND 850) |
| COACTUPC: Y/N flags | CHECK (col IN ('Y', 'N')) |
| COCRDUPC: expiry month 1-12 | CHECK via DATE type validation |
| COCRDUPC: expiry year 1950-2099 | CHECK via DATE type validation |
| COTRTUPC: type_code numeric nonzero | CHECK (type_code ~ '^[0-9]+$' AND type_code::INT > 0) |
| COTRTUPC: description alphanumeric | CHECK (description ~ '^[A-Za-z0-9 ]+$') |
| COTRTUPC: FK violation on delete | FK transactions.transaction_type_code REFERENCES transaction_types |
| COBIL00C: ACCT-CURR-BAL set to 0 on payment | Application-level UPDATE (not constraint) |

---

## 8. Security Considerations

- **PCI-DSS**: `credit_cards.card_number` should be tokenized or masked in application layer. Store only last 4 digits for display; use token for processing.
- **SSN**: Encrypt `customers.ssn` at the application layer using pgcrypto or application-level AES-256. Never return raw SSN in API responses.
- **Passwords**: Never store, log, or return password values. Only bcrypt hashes stored.
- **Row-level security**: Consider PostgreSQL RLS policies to enforce that regular users cannot query `users` table rows.
