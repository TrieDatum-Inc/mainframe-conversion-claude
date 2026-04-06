-- =============================================================================
-- CardDemo PostgreSQL Schema
-- Source: USRSEC VSAM KSDS (CSUSR01Y copybook)
-- =============================================================================

-- Trigger function for automatic updated_at management
-- COBOL origin: Replaces the manual WS-DATACHANGED-FLAG pattern in COACTUPC
--               and the CCUP-OLD-DETAILS snapshot in COCRDUPC.
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- users table
-- COBOL origin: USRSEC VSAM KSDS — SEC-USER-DATA record (CSUSR01Y)
--   SEC-USR-ID     X(08) → user_id VARCHAR(8) PRIMARY KEY
--   SEC-USR-PWD    X(08) → password_hash VARCHAR(255) [bcrypt; never plain text]
--   SEC-USR-FNAME  X(20) → first_name VARCHAR(20)
--   SEC-USR-LNAME  X(20) → last_name VARCHAR(20)
--   SEC-USR-TYPE   X(01) → user_type CHAR(1) CHECK IN ('A','U')
--   SEC-USR-FILLER X(23) → (not migrated; unused padding)
-- =============================================================================
CREATE TABLE IF NOT EXISTS users (
    user_id         VARCHAR(8)   NOT NULL,
    first_name      VARCHAR(20)  NOT NULL,
    last_name       VARCHAR(20)  NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,    -- bcrypt hash; plain-text SEC-USR-PWD never stored
    user_type       CHAR(1)      NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_users PRIMARY KEY (user_id),
    CONSTRAINT chk_users_type CHECK (user_type IN ('A', 'U'))
);

CREATE INDEX IF NOT EXISTS idx_users_last_name ON users(last_name);
CREATE INDEX IF NOT EXISTS idx_users_user_type ON users(user_type);

-- Trigger: auto-update updated_at on every REWRITE (COUSR02C equivalent)
DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- transaction_types table
-- COBOL origin: DB2 table CARDDEMO.TRANSACTION_TYPE (DCLTRTYP DCLGEN copybook)
--   TR_TYPE        CHAR(2)     → type_code VARCHAR(2) PRIMARY KEY
--   TR_DESCRIPTION VARCHAR(50) → description VARCHAR(50) NOT NULL
--
-- Programs: COTRTLIC (list/update/delete, Transaction CTLI)
--           COTRTUPC (add/update/delete, Transaction CTTU)
--
-- Constraints replace COBOL validation paragraphs:
--   chk_tt_type_code_numeric → COTRTUPC 1245-EDIT-NUM-REQD (NUMERIC test)
--   chk_tt_type_code_nonzero → COTRTUPC 1210-EDIT-TRANTYPE (non-zero check)
--   chk_tt_description_alphanum → COTRTUPC 1230-EDIT-ALPHANUM-REQD
-- FK from transactions.transaction_type_code replaces SQLCODE -532 delete guard.
-- =============================================================================
CREATE TABLE IF NOT EXISTS transaction_types (
    type_code       VARCHAR(2)   NOT NULL,
    description     VARCHAR(50)  NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_transaction_types PRIMARY KEY (type_code),
    CONSTRAINT chk_tt_type_code_numeric CHECK (type_code ~ '^[0-9]{1,2}$'),
    CONSTRAINT chk_tt_type_code_nonzero CHECK (type_code::INTEGER > 0),
    CONSTRAINT chk_tt_description_alphanum CHECK (description ~ '^[A-Za-z0-9 ]+$')
);

-- Trigger: auto-update updated_at (replaces COTRTLIC WS-DATACHANGED-FLAG pattern)
DROP TRIGGER IF EXISTS trg_tt_updated_at ON transaction_types;
CREATE TRIGGER trg_tt_updated_at
    BEFORE UPDATE ON transaction_types
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- accounts table
-- COBOL origin: ACCTDAT VSAM KSDS (CVACT01Y copybook) — 300-byte record
--   ACCT-ID               9(11)            → account_id BIGINT PRIMARY KEY
--   ACCT-ACTIVE-STATUS    X(1)             → active_status CHAR(1)
--   ACCT-CURR-BAL         S9(10)V99 COMP-3 → current_balance NUMERIC(12,2)
--   ACCT-CREDIT-LIMIT     S9(10)V99 COMP-3 → credit_limit NUMERIC(12,2)
--   ACCT-CASH-CREDIT-LIMIT S9(10)V99 COMP-3 → cash_credit_limit NUMERIC(12,2)
--   ACCT-OPEN-DATE        X(10)            → open_date DATE (YYYY-MM-DD)
--   ACCT-EXPIRAION-DATE   X(10)            → expiration_date DATE
--   ACCT-REISSUE-DATE     X(10)            → reissue_date DATE
--   ACCT-CURR-CYC-CREDIT  S9(10)V99 COMP-3 → curr_cycle_credit NUMERIC(12,2)
--   ACCT-CURR-CYC-DEBIT   S9(10)V99 COMP-3 → curr_cycle_debit NUMERIC(12,2)
--   ACCT-ADDR-ZIP         X(10)            → zip_code VARCHAR(10)
--   ACCT-GROUP-ID         X(10)            → group_id VARCHAR(10)
--   FILLER X(178)                          → (discarded)
--
-- Programs: COACTVWC (read-only view), COACTUPC (update with 15+ validations)
-- =============================================================================
CREATE TABLE IF NOT EXISTS accounts (
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

CREATE INDEX IF NOT EXISTS idx_accounts_active_status ON accounts(active_status);
CREATE INDEX IF NOT EXISTS idx_accounts_group_id ON accounts(group_id);

DROP TRIGGER IF EXISTS trg_accounts_updated_at ON accounts;
CREATE TRIGGER trg_accounts_updated_at
    BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- customers table
-- COBOL origin: CUSTDAT VSAM KSDS (CVCUS01Y copybook) — 500-byte record
--   CUST-ID               9(9)   → customer_id INTEGER PRIMARY KEY
--   CUST-FIRST-NAME       X(25)  → first_name VARCHAR(25)
--   CUST-MIDDLE-NAME      X(25)  → middle_name VARCHAR(25)
--   CUST-LAST-NAME        X(25)  → last_name VARCHAR(25)
--   CUST-ADDR-LINE-1      X(50)  → street_address_1 VARCHAR(50)
--   CUST-ADDR-LINE-2      X(50)  → street_address_2 VARCHAR(50)
--   CUST-ADDR-CITY        X(50)  → city VARCHAR(50)
--   CUST-ADDR-STATE-CD    X(2)   → state_code CHAR(2)
--   CUST-ADDR-ZIP         X(10)  → zip_code VARCHAR(10)
--   CUST-ADDR-COUNTRY-CD  X(3)   → country_code CHAR(3)
--   CUST-PHONE-NUM-1      X(15)  → phone_number_1 VARCHAR(15)
--   CUST-PHONE-NUM-2      X(15)  → phone_number_2 VARCHAR(15)
--   CUST-SSN parts 3+2+4         → ssn VARCHAR(11) as NNN-NN-NNNN
--   CUST-DOB-YYYY-MM-DD   X(10)  → date_of_birth DATE
--   CUST-EFT-ACCOUNT-ID   X(10)  → eft_account_id VARCHAR(10)
--   CUST-PRI-CARD-HOLDER-IND X(1) → primary_card_holder_flag CHAR(1)
--   CUST-FICO-CREDIT-SCORE 9(3)  → fico_score SMALLINT CHECK 300-850
--   CUST-GOVT-ISSUED-ID   X(20)  → government_id_ref VARCHAR(20)
--
-- Programs: COACTVWC (read), COACTUPC (update — alpha-only name validation, SSN validation)
-- =============================================================================
CREATE TABLE IF NOT EXISTS customers (
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
    ssn                     VARCHAR(11),    -- NNN-NN-NNNN; encrypt at rest recommended
    date_of_birth           DATE,
    fico_score              SMALLINT,
    government_id_ref       VARCHAR(20),
    eft_account_id          VARCHAR(10),
    primary_card_holder_flag CHAR(1)        NOT NULL DEFAULT 'Y',
    created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_customers PRIMARY KEY (customer_id),
    CONSTRAINT chk_customers_primary_flag CHECK (primary_card_holder_flag IN ('Y', 'N')),
    CONSTRAINT chk_customers_fico CHECK (
        fico_score IS NULL OR (fico_score >= 300 AND fico_score <= 850)
    )
);

CREATE INDEX IF NOT EXISTS idx_customers_last_name ON customers(last_name);
CREATE INDEX IF NOT EXISTS idx_customers_ssn ON customers(ssn);

DROP TRIGGER IF EXISTS trg_customers_updated_at ON customers;
CREATE TRIGGER trg_customers_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- account_customer_xref table
-- COBOL origin: Derived from ACCTDAT/CUSTDAT relationship (CVACT04Y)
-- Purpose: Links accounts to customers for COACTVWC READ-CUST-BY-CUST-ID
-- =============================================================================
CREATE TABLE IF NOT EXISTS account_customer_xref (
    account_id      BIGINT      NOT NULL,
    customer_id     INTEGER     NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_acct_cust_xref PRIMARY KEY (account_id, customer_id),
    CONSTRAINT fk_acctcust_account FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    CONSTRAINT fk_acctcust_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE INDEX IF NOT EXISTS idx_acctcust_customer ON account_customer_xref(customer_id);

-- =============================================================================
-- credit_cards table
-- COBOL origin: CARDDAT VSAM KSDS (CVACT02Y copybook) — 150-byte record
--   CARD-NUM          X(16)  → card_number CHAR(16) PRIMARY KEY
--   CARD-ACCT-ID      9(11)  → account_id BIGINT FK
--   CARD-CUST-ID      9(9)   → customer_id INTEGER FK
--   CARD-EMBOSSED-NAME X(50) → card_embossed_name VARCHAR(50)
--   CARD-ACTIVE-STATUS X(1)  → active_status CHAR(1)
--   CARD-EXPIRY-DATE  (derived) → expiration_date DATE
--   EXPDAY (COCRDUP hidden field) → expiration_day SMALLINT
--
-- Programs: COCRDLIC (browse), COCRDSLC (view), COCRDUPC (update)
-- COCRDUPC: account_id is PROT (cannot be changed); optimistic lock via updated_at
-- =============================================================================
CREATE TABLE IF NOT EXISTS credit_cards (
    card_number             CHAR(16)        NOT NULL,
    account_id              BIGINT          NOT NULL,
    customer_id             INTEGER         NOT NULL,
    card_embossed_name      VARCHAR(50),
    active_status           CHAR(1)         NOT NULL DEFAULT 'Y',
    expiration_date         DATE,
    expiration_day          SMALLINT,
    cvv                     VARCHAR(4),     -- never shown in update screen; store encrypted
    created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_cards PRIMARY KEY (card_number),
    CONSTRAINT fk_cards_account FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    CONSTRAINT fk_cards_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    CONSTRAINT chk_cards_active CHECK (active_status IN ('Y', 'N')),
    CONSTRAINT chk_cards_exp_month CHECK (
        expiration_date IS NULL OR
        EXTRACT(MONTH FROM expiration_date) BETWEEN 1 AND 12
    ),
    CONSTRAINT chk_cards_exp_year CHECK (
        expiration_date IS NULL OR
        EXTRACT(YEAR FROM expiration_date) BETWEEN 1950 AND 2099
    )
);

CREATE INDEX IF NOT EXISTS idx_cards_account_id ON credit_cards(account_id);
CREATE INDEX IF NOT EXISTS idx_cards_customer_id ON credit_cards(customer_id);
CREATE INDEX IF NOT EXISTS idx_cards_active_status ON credit_cards(active_status);

DROP TRIGGER IF EXISTS trg_cards_updated_at ON credit_cards;
CREATE TRIGGER trg_cards_updated_at
    BEFORE UPDATE ON credit_cards
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- card_account_xref table
-- COBOL origin: CARDXREF VSAM KSDS + AIX on XREF-ACCT-ID (CVACT03Y copybook)
--   XREF-CARD-NUM   X(16) → card_number CHAR(16) PRIMARY KEY
--   XREF-CUST-ID    9(9)  → customer_id INTEGER
--   XREF-ACCT-ID    9(11) → account_id BIGINT [was VSAM AIX; now PostgreSQL index]
--
-- COACTVWC uses CARDAIX (AIX on XREF-ACCT-ID) to find cards for an account.
-- idx_cardxref_account replaces the VSAM AIX.
-- COTRN02C: READ CCXREF by card_number → account_id lookup.
-- =============================================================================
CREATE TABLE IF NOT EXISTS card_account_xref (
    card_number     CHAR(16)    NOT NULL,
    customer_id     INTEGER     NOT NULL,
    account_id      BIGINT      NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_card_xref PRIMARY KEY (card_number),
    CONSTRAINT fk_cardxref_card FOREIGN KEY (card_number)
        REFERENCES credit_cards(card_number),
    CONSTRAINT fk_cardxref_account FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    CONSTRAINT fk_cardxref_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Replaces VSAM AIX on XREF-ACCT-ID
CREATE INDEX IF NOT EXISTS idx_cardxref_account ON card_account_xref(account_id);
CREATE INDEX IF NOT EXISTS idx_cardxref_customer ON card_account_xref(customer_id);

-- =============================================================================
-- transaction_id_seq
-- Replaces COTRN02C/COBIL00C STARTBR(HIGH-VALUES)+READPREV+ADD-1 race condition.
-- COTRN02C: two concurrent tasks could both read the same last TRAN-ID and
--           generate the same new ID. NEXTVAL is atomic under concurrency.
-- =============================================================================
CREATE SEQUENCE IF NOT EXISTS transaction_id_seq START 1;

-- =============================================================================
-- transactions table
-- COBOL origin: TRANSACT VSAM KSDS (CVTRA05Y / COTRN02Y copybook)
-- Programs: COTRN00C (list), COTRN01C (view), COTRN02C (add), COBIL00C (payment)
-- =============================================================================
CREATE TABLE IF NOT EXISTS transactions (
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
    CONSTRAINT fk_transactions_card FOREIGN KEY (card_number)
        REFERENCES credit_cards(card_number),
    CONSTRAINT fk_transactions_type FOREIGN KEY (transaction_type_code)
        REFERENCES transaction_types(type_code),
    CONSTRAINT chk_transactions_nonzero_amount CHECK (amount != 0)
);

-- Replaces VSAM browse indexes used by COTRN00C STARTBR/READNEXT
CREATE INDEX IF NOT EXISTS idx_transactions_card_number ON transactions(card_number);
CREATE INDEX IF NOT EXISTS idx_transactions_type_code ON transactions(transaction_type_code);
CREATE INDEX IF NOT EXISTS idx_transactions_original_date ON transactions(original_date);
CREATE INDEX IF NOT EXISTS idx_transactions_processed_date ON transactions(processed_date);
CREATE INDEX IF NOT EXISTS idx_transactions_merchant_id ON transactions(merchant_id);

CREATE TRIGGER trg_transactions_updated_at
    BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- report_requests table
-- COBOL origin: CORPT00C WIRTE-JOBSUB-TDQ (TDQ QUEUE='JOBS' batch submission)
-- Replaces JCL submission with persistent request + background processing.
-- Adds status tracking that the original JCL submission lacked.
-- =============================================================================
CREATE TABLE IF NOT EXISTS report_requests (
    request_id      BIGSERIAL   NOT NULL,
    report_type     CHAR(1)     NOT NULL,
    start_date      DATE,
    end_date        DATE,
    requested_by    VARCHAR(8)  NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    result_path     VARCHAR(500),
    error_message   VARCHAR(500),
    requested_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,
    CONSTRAINT pk_report_requests PRIMARY KEY (request_id),
    CONSTRAINT fk_rptreq_user FOREIGN KEY (requested_by)
        REFERENCES users(user_id),
    CONSTRAINT chk_rptreq_type CHECK (report_type IN ('M', 'Y', 'C')),
    CONSTRAINT chk_rptreq_status CHECK (
        status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED')
    ),
    CONSTRAINT chk_rptreq_custom_dates CHECK (
        report_type != 'C' OR (
            start_date IS NOT NULL AND
            end_date IS NOT NULL AND
            end_date >= start_date
        )
    )
);
