-- =============================================================================
-- CardDemo PostgreSQL DDL
-- Converted from AWS CardDemo COBOL/CICS/VSAM mainframe application
--
-- Source VSAM files → PostgreSQL tables:
--   ACCTDAT  (ACCTDATA.VSAM.KSDS,  300 bytes) → accounts
--   CARDDAT  (CARDDATA.VSAM.KSDS,  150 bytes) → cards
--   CCXREF   (CARDXREF.VSAM.KSDS,   50 bytes) → card_xref
--   CUSTDAT  (CUSTDATA.VSAM.KSDS,  500 bytes) → customers
--   TRANSACT (TRANSACT.VSAM.KSDS,  350 bytes) → transactions
--   USRSEC   (USRSEC.VSAM.KSDS,     80 bytes) → users
--   TRANTYPE (TRANTYPE.VSAM.KSDS,   60 bytes) → transaction_types
--   TRANCATG (TRANCATG.VSAM.KSDS,   60 bytes) → transaction_type_categories
--   TCATBALF (TCATBALF.VSAM.KSDS,   50 bytes) → tran_cat_balances
--   DISCGRP  (DISCGRP.VSAM.KSDS,    50 bytes) → disclosure_groups
--
-- DB2 tables → PostgreSQL tables:
--   CARDDEMO.TRANSACTION_TYPE          → transaction_types
--   CARDDEMO.TRANSACTION_TYPE_CATEGORY → transaction_type_categories
-- =============================================================================

-- Drop order respects foreign key constraints
DROP TABLE IF EXISTS tran_cat_balances CASCADE;
DROP TABLE IF EXISTS disclosure_groups CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS card_xref CASCADE;
DROP TABLE IF EXISTS cards CASCADE;
DROP TABLE IF EXISTS transaction_type_categories CASCADE;
DROP TABLE IF EXISTS transaction_types CASCADE;
DROP TABLE IF EXISTS accounts CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- =============================================================================
-- USERS table
-- Source: USRSEC VSAM KSDS (80 bytes)
-- Copybook: CSUSR01Y.cpy — SEC-USER-DATA
-- Primary key: SEC-USR-ID PIC X(08) → VARCHAR(8) (trimmed in queries)
-- =============================================================================
CREATE TABLE users (
    user_id      CHAR(8)     NOT NULL,  -- SEC-USR-ID PIC X(08) [uppercase, space-padded in COBOL]
    first_name   VARCHAR(20),           -- SEC-USR-FNAME PIC X(20)
    last_name    VARCHAR(20),           -- SEC-USR-LNAME PIC X(20)
    password_hash VARCHAR(60) NOT NULL, -- SEC-USR-PWD PIC X(08) [COBOL plaintext → bcrypt hash]
    user_type    CHAR(1)      NOT NULL DEFAULT 'U',  -- SEC-USR-TYPE PIC X(01): A=admin, U=regular

    CONSTRAINT pk_users PRIMARY KEY (user_id),
    CONSTRAINT ck_users_type CHECK (user_type IN ('A', 'U')),
    CONSTRAINT ck_users_id_len CHECK (length(trim(user_id)) BETWEEN 1 AND 8)
);

COMMENT ON TABLE users IS 'USRSEC VSAM KSDS — user security records (CSUSR01Y.cpy)';
COMMENT ON COLUMN users.user_id IS 'SEC-USR-ID PIC X(08): primary key, uppercase, COBOL space-padded';
COMMENT ON COLUMN users.password_hash IS 'SEC-USR-PWD PIC X(08) original; stored as bcrypt hash';
COMMENT ON COLUMN users.user_type IS 'SEC-USR-TYPE: A=admin (CDEMO-USRTYP-ADMIN), U=regular user';

-- =============================================================================
-- ACCOUNTS table
-- Source: ACCTDAT VSAM KSDS (300 bytes)
-- Copybook: CVACT01Y.cpy — ACCOUNT-RECORD
-- Primary key: ACCT-ID PIC 9(11) → BIGINT
-- =============================================================================
CREATE TABLE accounts (
    acct_id            BIGINT          NOT NULL,  -- ACCT-ID PIC 9(11)
    active_status      CHAR(1)         NOT NULL DEFAULT 'Y',  -- ACCT-ACTIVE-STATUS PIC X(01)
    curr_bal           NUMERIC(12,2)   NOT NULL DEFAULT 0.00, -- ACCT-CURR-BAL PIC S9(10)V99 COMP-3
    credit_limit       NUMERIC(12,2)   NOT NULL DEFAULT 0.00, -- ACCT-CREDIT-LIMIT PIC S9(10)V99 COMP-3
    cash_credit_limit  NUMERIC(12,2)   NOT NULL DEFAULT 0.00, -- ACCT-CASH-CREDIT-LIMIT PIC S9(10)V99 COMP-3
    open_date          VARCHAR(10),                            -- ACCT-OPEN-DATE PIC X(10) YYYY-MM-DD
    expiration_date    VARCHAR(10),                            -- ACCT-EXPIRAION-DATE PIC X(10) [typo in original]
    reissue_date       VARCHAR(10),                            -- ACCT-REISSUE-DATE PIC X(10)
    curr_cycle_credit  NUMERIC(12,2)   NOT NULL DEFAULT 0.00, -- ACCT-CURR-CYC-CREDIT PIC S9(10)V99 COMP-3
    curr_cycle_debit   NUMERIC(12,2)   NOT NULL DEFAULT 0.00, -- ACCT-CURR-CYC-DEBIT PIC S9(10)V99 COMP-3
    addr_zip           VARCHAR(10),                            -- ACCT-ADDR-ZIP PIC X(10)
    group_id           VARCHAR(10),                            -- ACCT-GROUP-ID PIC X(10)

    CONSTRAINT pk_accounts PRIMARY KEY (acct_id),
    CONSTRAINT ck_accounts_active CHECK (active_status IN ('Y', 'N')),
    CONSTRAINT ck_accounts_credit_limit CHECK (credit_limit >= 0),
    CONSTRAINT ck_accounts_cash_limit CHECK (cash_credit_limit >= 0)
);

CREATE INDEX ix_accounts_group_id ON accounts (group_id);

COMMENT ON TABLE accounts IS 'ACCTDAT VSAM KSDS — account records (CVACT01Y.cpy)';
COMMENT ON COLUMN accounts.acct_id IS 'ACCT-ID PIC 9(11): primary key';
COMMENT ON COLUMN accounts.curr_bal IS 'ACCT-CURR-BAL PIC S9(10)V99 COMP-3: current balance';
COMMENT ON COLUMN accounts.group_id IS 'ACCT-GROUP-ID PIC X(10): links to disclosure_groups for interest calc';
COMMENT ON COLUMN accounts.expiration_date IS 'ACCT-EXPIRAION-DATE [typo in original COBOL copybook retained]';

-- =============================================================================
-- CUSTOMERS table
-- Source: CUSTDAT VSAM KSDS (500 bytes)
-- Copybook: CVCUS01Y.cpy — CUSTOMER-RECORD
-- Primary key: CUST-ID PIC 9(09) → INTEGER
-- =============================================================================
CREATE TABLE customers (
    cust_id             INTEGER         NOT NULL,  -- CUST-ID PIC 9(09)
    first_name          VARCHAR(25),               -- CUST-FIRST-NAME PIC X(25)
    middle_name         VARCHAR(25),               -- CUST-MIDDLE-NAME PIC X(25)
    last_name           VARCHAR(25),               -- CUST-LAST-NAME PIC X(25)
    addr_line_1         VARCHAR(50),               -- CUST-ADDR-LINE-1 PIC X(50)
    addr_line_2         VARCHAR(50),               -- CUST-ADDR-LINE-2 PIC X(50)
    addr_line_3         VARCHAR(50),               -- CUST-ADDR-LINE-3 PIC X(50)
    addr_state_cd       CHAR(2),                   -- CUST-ADDR-STATE-CD PIC X(02)
    addr_country_cd     CHAR(3),                   -- CUST-ADDR-COUNTRY-CD PIC X(03)
    addr_zip            VARCHAR(10),               -- CUST-ADDR-ZIP PIC X(10)
    phone_num_1         VARCHAR(15),               -- CUST-PHONE-NUM-1 PIC X(15)
    phone_num_2         VARCHAR(15),               -- CUST-PHONE-NUM-2 PIC X(15)
    ssn                 INTEGER,                   -- CUST-SSN PIC 9(09) [SENSITIVE — encrypt at rest]
    govt_issued_id      VARCHAR(20),               -- CUST-GOVT-ISSUED-ID PIC X(20) [SENSITIVE]
    dob                 VARCHAR(10),               -- CUST-DOB-YYYY-MM-DD PIC X(10)
    eft_account_id      VARCHAR(10),               -- CUST-EFT-ACCOUNT-ID PIC X(10)
    pri_card_holder_ind CHAR(1) DEFAULT 'Y',       -- CUST-PRI-CARD-HOLDER-IND PIC X(01)
    fico_credit_score   SMALLINT,                  -- CUST-FICO-CREDIT-SCORE PIC 9(03) range 300-850

    CONSTRAINT pk_customers PRIMARY KEY (cust_id),
    CONSTRAINT ck_customers_pri_holder CHECK (pri_card_holder_ind IN ('Y', 'N')),
    CONSTRAINT ck_customers_fico CHECK (fico_credit_score BETWEEN 300 AND 850 OR fico_credit_score IS NULL)
);

CREATE INDEX ix_customers_last_name ON customers (last_name);
CREATE INDEX ix_customers_ssn ON customers (ssn);

COMMENT ON TABLE customers IS 'CUSTDAT VSAM KSDS — customer records (CVCUS01Y.cpy)';
COMMENT ON COLUMN customers.ssn IS 'CUST-SSN PIC 9(09): SENSITIVE — encrypt at rest in production';
COMMENT ON COLUMN customers.fico_credit_score IS 'CUST-FICO-CREDIT-SCORE PIC 9(03): range 300-850';

-- =============================================================================
-- CARDS table
-- Source: CARDDAT VSAM KSDS (150 bytes)
-- Copybook: CVACT02Y.cpy — CARD-RECORD
-- Primary key: CARD-NUM PIC X(16) → CHAR(16)
-- CARDAIX alt-index on CARD-ACCT-ID → ix_cards_acct_id
-- =============================================================================
CREATE TABLE cards (
    card_num        CHAR(16)    NOT NULL,  -- CARD-NUM PIC X(16): primary key
    acct_id         BIGINT      NOT NULL,  -- CARD-ACCT-ID PIC 9(11): FK to accounts
    cvv_cd          SMALLINT,              -- CARD-CVV-CD PIC 9(03)
    embossed_name   VARCHAR(50),           -- CARD-EMBOSSED-NAME PIC X(50)
    expiration_date VARCHAR(10),           -- CARD-EXPIRAION-DATE PIC X(10) [typo in original]
    active_status   CHAR(1)     NOT NULL DEFAULT 'Y',  -- CARD-ACTIVE-STATUS PIC X(01)

    CONSTRAINT pk_cards PRIMARY KEY (card_num),
    CONSTRAINT fk_cards_acct FOREIGN KEY (acct_id) REFERENCES accounts (acct_id) ON DELETE RESTRICT,
    CONSTRAINT ck_cards_active CHECK (active_status IN ('Y', 'N')),
    CONSTRAINT ck_cards_cvv CHECK (cvv_cd BETWEEN 0 AND 999 OR cvv_cd IS NULL)
);

-- CARDAIX: alternate index on CARD-ACCT-ID — used by COCRDLIC and COBIL00C
CREATE INDEX ix_cards_acct_id ON cards (acct_id);

COMMENT ON TABLE cards IS 'CARDDAT VSAM KSDS — card records (CVACT02Y.cpy)';
COMMENT ON COLUMN cards.card_num IS 'CARD-NUM PIC X(16): primary key, stored as string';
COMMENT ON COLUMN cards.acct_id IS 'CARD-ACCT-ID PIC 9(11): CARDAIX alternate index key';
COMMENT ON COLUMN cards.expiration_date IS 'CARD-EXPIRAION-DATE [typo in original COBOL copybook retained]';

-- =============================================================================
-- CARD_XREF table
-- Source: CCXREF VSAM KSDS (50 bytes)
-- Copybook: CVACT03Y.cpy — CARD-XREF-RECORD
-- Primary key: XREF-CARD-NUM PIC X(16)
-- CXACAIX alt-index on XREF-ACCT-ID → ix_card_xref_acct_id
-- =============================================================================
CREATE TABLE card_xref (
    card_num    CHAR(16)    NOT NULL,  -- XREF-CARD-NUM PIC X(16): primary key
    cust_id     INTEGER     NOT NULL,  -- XREF-CUST-ID PIC 9(09): FK to customers
    acct_id     BIGINT      NOT NULL,  -- XREF-ACCT-ID PIC 9(11): FK to accounts (CXACAIX key)

    CONSTRAINT pk_card_xref PRIMARY KEY (card_num),
    CONSTRAINT fk_xref_card FOREIGN KEY (card_num) REFERENCES cards (card_num) ON DELETE CASCADE,
    CONSTRAINT fk_xref_cust FOREIGN KEY (cust_id) REFERENCES customers (cust_id) ON DELETE RESTRICT,
    CONSTRAINT fk_xref_acct FOREIGN KEY (acct_id) REFERENCES accounts (acct_id) ON DELETE RESTRICT
);

-- CXACAIX: alternate index on XREF-ACCT-ID — used by COBIL00C
CREATE INDEX ix_card_xref_acct_id ON card_xref (acct_id);
CREATE INDEX ix_card_xref_cust_id ON card_xref (cust_id);

COMMENT ON TABLE card_xref IS 'CCXREF VSAM KSDS — card cross-reference (CVACT03Y.cpy)';
COMMENT ON COLUMN card_xref.acct_id IS 'XREF-ACCT-ID PIC 9(11): CXACAIX alternate index key';

-- =============================================================================
-- TRANSACTION_TYPES table
-- Source: DB2 CARDDEMO.TRANSACTION_TYPE + TRANTYPE VSAM
-- Copybook: trantype.txt format — TR_TYPE CHAR(2), TR_DESCRIPTION VARCHAR(50)
-- =============================================================================
CREATE TABLE transaction_types (
    type_cd     CHAR(2)     NOT NULL,  -- TR_TYPE CHAR(2) PK: '01'=Purchase, '02'=Payment, etc.
    description VARCHAR(50),           -- TR_DESCRIPTION VARCHAR(50)

    CONSTRAINT pk_transaction_types PRIMARY KEY (type_cd)
);

COMMENT ON TABLE transaction_types IS 'DB2 CARDDEMO.TRANSACTION_TYPE + TRANTYPE VSAM';
COMMENT ON COLUMN transaction_types.type_cd IS 'TR_TYPE CHAR(2): 01=Purchase, 02=Payment, 03=Credit, etc.';

-- =============================================================================
-- TRANSACTION_TYPE_CATEGORIES table
-- Source: DB2 CARDDEMO.TRANSACTION_TYPE_CATEGORY + TRANCATG VSAM
-- =============================================================================
CREATE TABLE transaction_type_categories (
    type_cd      CHAR(2)     NOT NULL,  -- TRC_TYPE_CODE CHAR(2) FK
    category_cd  SMALLINT    NOT NULL,  -- TRC_TYPE_CATEGORY
    description  VARCHAR(50),           -- TRC_TYPE_DESC

    CONSTRAINT pk_tran_type_cat PRIMARY KEY (type_cd, category_cd),
    CONSTRAINT fk_tran_cat_type FOREIGN KEY (type_cd) REFERENCES transaction_types (type_cd) ON DELETE CASCADE
);

COMMENT ON TABLE transaction_type_categories IS 'DB2 CARDDEMO.TRANSACTION_TYPE_CATEGORY + TRANCATG VSAM';

-- =============================================================================
-- TRANSACTIONS table
-- Source: TRANSACT VSAM KSDS (350 bytes)
-- Copybook: CVTRA05Y.cpy — TRAN-RECORD
-- Primary key: TRAN-ID PIC X(16) → CHAR(16)
-- Browse by TRAN-ID (sequential) → keyset pagination on tran_id
-- =============================================================================
CREATE TABLE transactions (
    tran_id         CHAR(16)        NOT NULL,  -- TRAN-ID PIC X(16): primary key
    type_cd         CHAR(2),                    -- TRAN-TYPE-CD PIC X(02): FK to transaction_types
    cat_cd          SMALLINT,                   -- TRAN-CAT-CD PIC 9(04)
    source          VARCHAR(10),                -- TRAN-SOURCE PIC X(10)
    description     VARCHAR(100),               -- TRAN-DESC PIC X(100)
    amount          NUMERIC(11,2)   NOT NULL DEFAULT 0.00,  -- TRAN-AMT PIC S9(09)V99 COMP-3
    merchant_id     INTEGER,                    -- TRAN-MERCHANT-ID PIC 9(09)
    merchant_name   VARCHAR(50),                -- TRAN-MERCHANT-NAME PIC X(50)
    merchant_city   VARCHAR(50),                -- TRAN-MERCHANT-CITY PIC X(50)
    merchant_zip    VARCHAR(10),                -- TRAN-MERCHANT-ZIP PIC X(10)
    card_num        CHAR(16),                   -- TRAN-CARD-NUM PIC X(16): FK to cards
    acct_id         BIGINT,                     -- Derived from XREF-ACCT-ID during posting
    orig_ts         VARCHAR(26),                -- TRAN-ORIG-TS PIC X(26): '2022-06-10 19:27:53.000000'
    proc_ts         VARCHAR(26),                -- TRAN-PROC-TS PIC X(26)

    CONSTRAINT pk_transactions PRIMARY KEY (tran_id),
    CONSTRAINT fk_tran_type FOREIGN KEY (type_cd) REFERENCES transaction_types (type_cd) ON DELETE RESTRICT,
    CONSTRAINT fk_tran_card FOREIGN KEY (card_num) REFERENCES cards (card_num) ON DELETE RESTRICT,
    CONSTRAINT fk_tran_acct FOREIGN KEY (acct_id) REFERENCES accounts (acct_id) ON DELETE RESTRICT
);

CREATE INDEX ix_transactions_card_num ON transactions (card_num);
CREATE INDEX ix_transactions_acct_id ON transactions (acct_id);
CREATE INDEX ix_transactions_orig_ts ON transactions (orig_ts);

COMMENT ON TABLE transactions IS 'TRANSACT VSAM KSDS — transaction records (CVTRA05Y.cpy)';
COMMENT ON COLUMN transactions.tran_id IS 'TRAN-ID PIC X(16): primary key, generated by COBIL00C/COTRN02C';
COMMENT ON COLUMN transactions.orig_ts IS 'TRAN-ORIG-TS PIC X(26): format YYYY-MM-DD HH:MM:SS.ffffff';
COMMENT ON COLUMN transactions.acct_id IS 'Denormalized from XREF-ACCT-ID — not in original COBOL record';

-- =============================================================================
-- TRAN_CAT_BALANCES table
-- Source: TCATBALF VSAM KSDS (50 bytes)
-- Copybook: CVTRA01Y.cpy — TRAN-CAT-BAL-RECORD
-- Composite primary key: (TRANCAT-ACCT-ID, TRANCAT-TYPE-CD, TRANCAT-CD)
-- =============================================================================
CREATE TABLE tran_cat_balances (
    acct_id     BIGINT          NOT NULL,  -- TRANCAT-ACCT-ID PIC 9(11): part of composite PK
    type_cd     CHAR(2)         NOT NULL,  -- TRANCAT-TYPE-CD PIC X(02): part of composite PK
    cat_cd      SMALLINT        NOT NULL,  -- TRANCAT-CD PIC 9(04): part of composite PK
    balance     NUMERIC(11,2)   NOT NULL DEFAULT 0.00,  -- TRAN-CAT-BAL PIC S9(09)V99 COMP-3

    CONSTRAINT pk_tran_cat_bal PRIMARY KEY (acct_id, type_cd, cat_cd),
    CONSTRAINT fk_tcb_acct FOREIGN KEY (acct_id) REFERENCES accounts (acct_id) ON DELETE CASCADE
);

COMMENT ON TABLE tran_cat_balances IS 'TCATBALF VSAM KSDS — transaction category balances (CVTRA01Y.cpy)';
COMMENT ON COLUMN tran_cat_balances.balance IS 'TRAN-CAT-BAL PIC S9(09)V99 COMP-3: used by CBACT04C interest calc';

-- =============================================================================
-- DISCLOSURE_GROUPS table
-- Source: DISCGRP VSAM KSDS (50 bytes)
-- Copybook: CVTRA02Y.cpy — DIS-GROUP-RECORD
-- Composite primary key: (DIS-ACCT-GROUP-ID, DIS-TRAN-TYPE-CD, DIS-TRAN-CAT-CD)
-- =============================================================================
CREATE TABLE disclosure_groups (
    group_id        VARCHAR(10)     NOT NULL,  -- DIS-ACCT-GROUP-ID PIC X(10)
    type_cd         CHAR(2)         NOT NULL,  -- DIS-TRAN-TYPE-CD PIC X(02)
    cat_cd          SMALLINT        NOT NULL,  -- DIS-TRAN-CAT-CD PIC 9(04)
    interest_rate   NUMERIC(6,2)    NOT NULL DEFAULT 0.00,  -- DIS-INT-RATE PIC S9(04)V99 [annual %]

    CONSTRAINT pk_disclosure_groups PRIMARY KEY (group_id, type_cd, cat_cd),
    CONSTRAINT ck_disc_rate CHECK (interest_rate >= 0)
);

COMMENT ON TABLE disclosure_groups IS 'DISCGRP VSAM KSDS — interest rate lookup (CVTRA02Y.cpy)';
COMMENT ON COLUMN disclosure_groups.interest_rate IS 'DIS-INT-RATE PIC S9(04)V99: annual interest rate % (e.g., 19.99)';

-- =============================================================================
-- Phase 3: Authorization Module Tables
-- Source programs: COPAUA0C.cbl, COPAUS0C.cbl, COPAUS1C.cbl, COPAUS2C.cbl
--
-- IMS hierarchical database replaced by PostgreSQL tables:
--   IMS PSB PSBPAUTB, segment PAUTSUM0 (CIPAUSMY.cpy) → auth_summaries
--   IMS PSB PSBPAUTB, segment PAUTDTL1 (CIPAUDTY.cpy) → auth_details
--   DB2 CARDDEMO.AUTHFRDS                              → auth_fraud_records
--
-- MQ request/reply (MQOPEN/MQGET/MQPUT1) replaced by synchronous REST POST.
-- =============================================================================

-- =============================================================================
-- AUTH_SUMMARIES table
-- Replaces IMS PAUTSUM0 root segment (CIPAUSMY.cpy)
-- One row per account — aggregate credit balance and authorization counters
-- =============================================================================
CREATE TABLE auth_summaries (
    acct_id             BIGINT          NOT NULL,   -- PA-ACCT-ID PIC S9(11) COMP-3
    cust_id             INTEGER,                    -- PA-CUST-ID PIC 9(09)
    auth_status         CHAR(1),                    -- PA-AUTH-STATUS PIC X(01)
    credit_limit        NUMERIC(11,2)   NOT NULL DEFAULT 0.00,  -- PA-CREDIT-LIMIT PIC S9(09)V99 COMP-3
    cash_limit          NUMERIC(11,2)   NOT NULL DEFAULT 0.00,  -- PA-CASH-LIMIT PIC S9(09)V99 COMP-3
    credit_balance      NUMERIC(11,2)   NOT NULL DEFAULT 0.00,  -- PA-CREDIT-BALANCE PIC S9(09)V99 COMP-3
    cash_balance        NUMERIC(11,2)   NOT NULL DEFAULT 0.00,  -- PA-CASH-BALANCE PIC S9(09)V99 COMP-3
    approved_auth_cnt   SMALLINT        NOT NULL DEFAULT 0,     -- PA-APPROVED-AUTH-CNT PIC S9(04) COMP
    declined_auth_cnt   SMALLINT        NOT NULL DEFAULT 0,     -- PA-DECLINED-AUTH-CNT PIC S9(04) COMP
    approved_auth_amt   NUMERIC(11,2)   NOT NULL DEFAULT 0.00,  -- PA-APPROVED-AUTH-AMT PIC S9(09)V99 COMP-3
    declined_auth_amt   NUMERIC(11,2)   NOT NULL DEFAULT 0.00,  -- PA-DECLINED-AUTH-AMT PIC S9(09)V99 COMP-3

    CONSTRAINT pk_auth_summaries PRIMARY KEY (acct_id),
    CONSTRAINT fk_auth_summaries_account FOREIGN KEY (acct_id)
        REFERENCES accounts(acct_id) ON DELETE CASCADE
);

COMMENT ON TABLE auth_summaries IS 'IMS PAUTSUM0 root segment (CIPAUSMY.cpy) — replaced by PostgreSQL';
COMMENT ON COLUMN auth_summaries.acct_id IS 'PA-ACCT-ID PIC S9(11) COMP-3 — IMS root segment key';
COMMENT ON COLUMN auth_summaries.credit_balance IS 'PA-CREDIT-BALANCE: running total of approved authorization amounts';


-- =============================================================================
-- AUTH_DETAILS table
-- Replaces IMS PAUTDTL1 child segment (CIPAUDTY.cpy)
-- One row per individual authorization request
-- Sorted by (auth_date_9c ASC, auth_time_9c ASC) — inverted COBOL timestamp order
-- =============================================================================
CREATE TABLE auth_details (
    auth_id             SERIAL          NOT NULL,   -- Surrogate PK (IMS used PA-AUTHORIZATION-KEY)
    acct_id             BIGINT          NOT NULL,   -- FK to auth_summaries
    auth_date_9c        INTEGER,                    -- PA-AUTH-DATE-9C PIC S9(05) COMP-3 (99999 - YYDDD)
    auth_time_9c        BIGINT,                     -- PA-AUTH-TIME-9C PIC S9(09) COMP-3 (999999999 - HHMMSSMMM)
    auth_orig_date      CHAR(6),                    -- PA-AUTH-ORIG-DATE PIC X(06) YYMMDD
    auth_orig_time      CHAR(6),                    -- PA-AUTH-ORIG-TIME PIC X(06) HHMMSS
    card_num            CHAR(16),                   -- PA-CARD-NUM PIC X(16)
    auth_type           CHAR(4),                    -- PA-AUTH-TYPE PIC X(04)
    card_expiry_date    CHAR(4),                    -- PA-CARD-EXPIRY-DATE PIC X(04) MMYY
    message_type        CHAR(6),                    -- PA-MESSAGE-TYPE PIC X(06)
    message_source      CHAR(6),                    -- PA-MESSAGE-SOURCE PIC X(06)
    auth_id_code        CHAR(6),                    -- PA-AUTH-ID-CODE PIC X(06)
    auth_resp_code      CHAR(2),                    -- PA-AUTH-RESP-CODE PIC X(02) ('00'=approved,'05'=declined)
    auth_resp_reason    CHAR(4),                    -- PA-AUTH-RESP-REASON PIC X(04) (see COPAUS1C table)
    processing_code     INTEGER,                    -- PA-PROCESSING-CODE PIC 9(06)
    transaction_amt     NUMERIC(12,2)   NOT NULL DEFAULT 0.00,  -- PA-TRANSACTION-AMT PIC S9(10)V99 COMP-3
    approved_amt        NUMERIC(12,2)   NOT NULL DEFAULT 0.00,  -- PA-APPROVED-AMT PIC S9(10)V99 COMP-3
    merchant_category_code CHAR(4),                -- PA-MERCHANT-CATAGORY-CODE PIC X(04) [sic]
    acqr_country_code   CHAR(3),                    -- PA-ACQR-COUNTRY-CODE PIC X(03)
    pos_entry_mode      SMALLINT,                   -- PA-POS-ENTRY-MODE PIC 9(02)
    merchant_id         CHAR(15),                   -- PA-MERCHANT-ID PIC X(15)
    merchant_name       VARCHAR(22),                -- PA-MERCHANT-NAME PIC X(22)
    merchant_city       CHAR(13),                   -- PA-MERCHANT-CITY PIC X(13)
    merchant_state      CHAR(2),                    -- PA-MERCHANT-STATE PIC X(02)
    merchant_zip        CHAR(9),                    -- PA-MERCHANT-ZIP PIC X(09)
    transaction_id      CHAR(15),                   -- PA-TRANSACTION-ID PIC X(15)
    match_status        CHAR(1)         NOT NULL DEFAULT 'P',  -- PA-MATCH-STATUS: P/D/E/M
    auth_fraud          CHAR(1),                    -- PA-AUTH-FRAUD: F=Confirmed R=Removed
    fraud_rpt_date      CHAR(8),                    -- PA-FRAUD-RPT-DATE PIC X(08) MM/DD/YY

    CONSTRAINT pk_auth_details PRIMARY KEY (auth_id),
    CONSTRAINT fk_auth_details_summary FOREIGN KEY (acct_id)
        REFERENCES auth_summaries(acct_id) ON DELETE CASCADE,
    CONSTRAINT ck_auth_details_match_status
        CHECK (match_status IN ('P','D','E','M')),
    CONSTRAINT ck_auth_details_fraud
        CHECK (auth_fraud IN ('F','R') OR auth_fraud IS NULL)
);

CREATE INDEX ix_auth_details_card_num ON auth_details(card_num);
CREATE INDEX ix_auth_details_acct_id_match_status ON auth_details(acct_id, match_status);
CREATE INDEX ix_auth_details_sort_key ON auth_details(acct_id, auth_date_9c, auth_time_9c);

COMMENT ON TABLE auth_details IS 'IMS PAUTDTL1 child segment (CIPAUDTY.cpy) — replaced by PostgreSQL';
COMMENT ON COLUMN auth_details.auth_date_9c IS 'PA-AUTH-DATE-9C: inverted YYDDD (99999-YYDDD) for most-recent-first sort';
COMMENT ON COLUMN auth_details.auth_time_9c IS 'PA-AUTH-TIME-9C: inverted time (999999999-HHMMSSMMM) for most-recent-first sort';
COMMENT ON COLUMN auth_details.match_status IS 'P=Pending, D=Declined, E=Expired, M=Matched with transaction';
COMMENT ON COLUMN auth_details.auth_resp_reason IS '0000=Approved,3100=InvalidCard,4100=InsufficientFund,4200=NotActive,4300=Closed,5100=Fraud,5200=MerchantFraud';


-- =============================================================================
-- AUTH_FRAUD_RECORDS table
-- Replaces DB2 table CARDDEMO.AUTHFRDS (COPAUS2C EXEC SQL INSERT/UPDATE)
-- Created/updated when user marks an authorization as fraud (COPAUS1C PF5)
-- Composite PK: (card_num, auth_ts) — mirrors DB2 schema
-- =============================================================================
CREATE TABLE auth_fraud_records (
    card_num            CHAR(16)        NOT NULL,   -- CARD_NUM CHAR(16) — PK part 1
    auth_ts             VARCHAR(26)     NOT NULL,   -- AUTH_TS TIMESTAMP 'YY-MM-DD HH24.MI.SSNNNNNN' — PK part 2
    auth_type           CHAR(4),                    -- AUTH_TYPE
    card_expiry_date    CHAR(4),                    -- CARD_EXPIRY_DATE
    message_type        CHAR(6),                    -- MESSAGE_TYPE
    message_source      CHAR(6),                    -- MESSAGE_SOURCE
    auth_id_code        CHAR(6),                    -- AUTH_ID_CODE
    auth_resp_code      CHAR(2),                    -- AUTH_RESP_CODE
    auth_resp_reason    CHAR(4),                    -- AUTH_RESP_REASON
    processing_code     INTEGER,                    -- PROCESSING_CODE
    transaction_amt     NUMERIC(12,2)   NOT NULL DEFAULT 0.00,  -- TRANSACTION_AMT
    approved_amt        NUMERIC(12,2)   NOT NULL DEFAULT 0.00,  -- APPROVED_AMT
    merchant_category_code CHAR(4),                -- MERCHANT_CATAGORY_CODE [sic]
    acqr_country_code   CHAR(3),                    -- ACQR_COUNTRY_CODE
    pos_entry_mode      SMALLINT,                   -- POS_ENTRY_MODE
    merchant_id         CHAR(15),                   -- MERCHANT_ID
    merchant_name       VARCHAR(22),                -- MERCHANT_NAME
    merchant_city       CHAR(13),                   -- MERCHANT_CITY
    merchant_state      CHAR(2),                    -- MERCHANT_STATE
    merchant_zip        CHAR(9),                    -- MERCHANT_ZIP
    transaction_id      CHAR(15),                   -- TRANSACTION_ID
    match_status        CHAR(1),                    -- MATCH_STATUS
    auth_fraud          CHAR(1),                    -- AUTH_FRAUD: F=Confirmed R=Removed
    fraud_rpt_date      DATE,                       -- FRAUD_RPT_DATE (CURRENT DATE in COPAUS2C)
    acct_id             BIGINT,                     -- ACCT_ID BIGINT
    cust_id             INTEGER,                    -- CUST_ID INTEGER

    CONSTRAINT pk_auth_fraud_records PRIMARY KEY (card_num, auth_ts)
);

CREATE INDEX ix_auth_fraud_acct_id ON auth_fraud_records(acct_id);
CREATE INDEX ix_auth_fraud_card_num ON auth_fraud_records(card_num);

COMMENT ON TABLE auth_fraud_records IS 'DB2 CARDDEMO.AUTHFRDS — fraud-flagged authorizations (COPAUS2C)';
COMMENT ON COLUMN auth_fraud_records.auth_ts IS 'YY-MM-DD HH.MI.SSNNNNNN — reconstructed from PA-AUTH-ORIG-DATE + inverted PA-AUTH-TIME-9C';
COMMENT ON COLUMN auth_fraud_records.auth_fraud IS 'F=Fraud Confirmed (COPAUS1C PF5 first press), R=Fraud Removed (PF5 second press)';

-- End of DDL
