-- CardDemo PostgreSQL Schema
-- Converted from VSAM KSDS files, DB2 tables, and IMS databases
-- Source: CardDemo COBOL/CICS mainframe application by AWS
--
-- Table mapping:
--   accounts          <- ACCTDAT  VSAM KSDS (CVACT01Y, 300 bytes)
--   customers         <- CUSTDAT  VSAM KSDS (CVCUS01Y, 500 bytes)
--   cards             <- CARDDAT  VSAM KSDS (CVACT02Y, 150 bytes)
--   card_xref         <- CXACAIX  VSAM AIX  (CVACT03Y, 50 bytes)
--   transactions      <- TRANSACT VSAM KSDS (CVTRA05Y, 350 bytes)
--   users             <- USRSEC   VSAM KSDS (CSUSR01Y, 80 bytes)
--   tran_cat_bal      <- TRAN-CAT-BAL-FILE  (CVTRA01Y, 50 bytes)
--   disclosure_groups <- DIS-GROUP-FILE     (CVTRA02Y, 50 bytes)
--   transaction_types <- DB2 CARDDEMO.TRANSACTION_TYPE
--   transaction_categories <- DB2 CARDDEMO.TRANSACTION_CATEGORY
--   auth_summary      <- IMS PAUTSUM0 segment (CIPAUSMY)
--   auth_detail       <- IMS PAUTDTL1 segment (CIPAUDTY)
--   auth_fraud        <- DB2 CARDDEMO.AUTHFRDS

-- ============================================================
-- ACCOUNTS (ACCTDAT VSAM KSDS / CVACT01Y)
-- Primary key: ACCT-ID PIC 9(11)
-- Used by: COACTVWC, COACTUPC, COBIL00C, CBACT04C, CBTRN01C/02C
-- ============================================================
CREATE TABLE IF NOT EXISTS accounts (
    acct_id             BIGINT          NOT NULL,
    active_status       CHAR(1)         NOT NULL DEFAULT 'Y',
    curr_bal            NUMERIC(12,2)   NOT NULL DEFAULT 0.00,
    credit_limit        NUMERIC(12,2)   NOT NULL DEFAULT 0.00,
    cash_credit_limit   NUMERIC(12,2)   NOT NULL DEFAULT 0.00,
    open_date           DATE,
    expiration_date     DATE,           -- Note: original COBOL has typo 'EXPIRAION'
    reissue_date        DATE,
    curr_cycle_credit   NUMERIC(12,2)   NOT NULL DEFAULT 0.00,
    curr_cycle_debit    NUMERIC(12,2)   NOT NULL DEFAULT 0.00,
    addr_zip            VARCHAR(10),
    group_id            VARCHAR(10),    -- Used for DISCGRP-FILE lookup in CBACT04C

    CONSTRAINT pk_accounts PRIMARY KEY (acct_id),
    CONSTRAINT ck_account_active_status CHECK (active_status IN ('Y', 'N')),
    CONSTRAINT ck_account_id_positive CHECK (acct_id > 0)
);

CREATE INDEX IF NOT EXISTS ix_accounts_group_id ON accounts (group_id);

-- ============================================================
-- CUSTOMERS (CUSTDAT VSAM KSDS / CVCUS01Y)
-- Primary key: CUST-ID PIC 9(09)
-- Used by: COACTVWC, COACTUPC, CBTRN01C, CBCUS01C, CBSTM03A
-- ============================================================
CREATE TABLE IF NOT EXISTS customers (
    cust_id             INTEGER         NOT NULL,
    first_name          VARCHAR(25)     NOT NULL,
    middle_name         VARCHAR(25),
    last_name           VARCHAR(25)     NOT NULL,
    addr_line1          VARCHAR(50),
    addr_line2          VARCHAR(50),
    addr_line3          VARCHAR(50),    -- Used as city in COACTVWC display
    addr_state_cd       CHAR(2),        -- Validated via CSLKPCDY US state table
    addr_country_cd     CHAR(3),
    addr_zip            VARCHAR(10),
    phone_num1          VARCHAR(15),    -- Format: (999)999-9999 per CSLKPCDY
    phone_num2          VARCHAR(15),
    ssn                 INTEGER         NOT NULL,   -- CUST-SSN PIC 9(09)
    govt_issued_id      VARCHAR(20),
    dob                 DATE,           -- CUST-DOB-YYYY-MM-DD PIC X(10)
    eft_account_id      VARCHAR(10),
    pri_card_holder     CHAR(1)         DEFAULT 'Y',
    fico_score          SMALLINT,       -- CUST-FICO-CREDIT-SCORE PIC 9(03), 300-850

    CONSTRAINT pk_customers PRIMARY KEY (cust_id),
    CONSTRAINT ck_customer_id_positive CHECK (cust_id > 0),
    CONSTRAINT ck_customer_ssn_range CHECK (ssn >= 100000000 AND ssn <= 999999999),
    CONSTRAINT ck_customer_fico_range CHECK (fico_score IS NULL OR (fico_score >= 300 AND fico_score <= 850)),
    CONSTRAINT ck_customer_pri_card_holder CHECK (pri_card_holder IS NULL OR pri_card_holder IN ('Y', 'N'))
);

CREATE INDEX IF NOT EXISTS ix_customers_last_name ON customers (last_name);
CREATE INDEX IF NOT EXISTS ix_customers_ssn ON customers (ssn);

-- ============================================================
-- CARDS (CARDDAT VSAM KSDS / CVACT02Y)
-- Primary key: CARD-NUM PIC X(16)
-- Used by: COCRDLIC, COCRDSLC, COCRDUPC, CBTRN01C, CBACT02C
-- ============================================================
CREATE TABLE IF NOT EXISTS cards (
    card_num            VARCHAR(16)     NOT NULL,
    acct_id             BIGINT          NOT NULL,
    cvv_cd              SMALLINT        NOT NULL,
    embossed_name       VARCHAR(50),
    expiration_date     DATE,           -- CARD-EXPIRAION-DATE (original typo)
    active_status       CHAR(1)         NOT NULL DEFAULT 'Y',

    CONSTRAINT pk_cards PRIMARY KEY (card_num),
    CONSTRAINT fk_cards_accounts FOREIGN KEY (acct_id)
        REFERENCES accounts (acct_id) ON DELETE RESTRICT,
    CONSTRAINT ck_card_active_status CHECK (active_status IN ('Y', 'N')),
    CONSTRAINT ck_card_cvv_range CHECK (cvv_cd >= 0 AND cvv_cd <= 999)
);

CREATE INDEX IF NOT EXISTS ix_cards_acct_id ON cards (acct_id);
CREATE INDEX IF NOT EXISTS ix_cards_active_status ON cards (active_status);

-- ============================================================
-- CARD_XREF (CXACAIX VSAM AIX / CVACT03Y)
-- Primary key: XREF-CARD-NUM PIC X(16)
-- Alternate index on acct_id (replaces VSAM AIX behavior)
-- Used by: COACTUPC, COACTVWC, COBIL00C, COTRN02C, CBTRN01C
-- ============================================================
CREATE TABLE IF NOT EXISTS card_xref (
    card_num            VARCHAR(16)     NOT NULL,
    cust_id             INTEGER         NOT NULL,
    acct_id             BIGINT          NOT NULL,

    CONSTRAINT pk_card_xref PRIMARY KEY (card_num),
    CONSTRAINT fk_xref_cards FOREIGN KEY (card_num)
        REFERENCES cards (card_num) ON DELETE CASCADE,
    CONSTRAINT fk_xref_customers FOREIGN KEY (cust_id)
        REFERENCES customers (cust_id) ON DELETE RESTRICT,
    CONSTRAINT fk_xref_accounts FOREIGN KEY (acct_id)
        REFERENCES accounts (acct_id) ON DELETE RESTRICT
);

-- This index replicates the VSAM AIX (alternate index by account ID)
-- EXEC CICS READ DATASET('CXACAIX') RIDFLD(acct_id) -> uses this index
CREATE INDEX IF NOT EXISTS ix_card_xref_acct_id ON card_xref (acct_id);
CREATE INDEX IF NOT EXISTS ix_card_xref_cust_id ON card_xref (cust_id);

-- ============================================================
-- TRANSACTIONS (TRANSACT VSAM KSDS / CVTRA05Y)
-- Primary key: TRAN-ID PIC X(16)
-- Used by: COTRN00C, COTRN01C, COTRN02C, COBIL00C, CBTRN01C-03C, CBACT04C
-- ============================================================
CREATE TABLE IF NOT EXISTS transactions (
    tran_id             VARCHAR(16)     NOT NULL,
    tran_type_cd        CHAR(2)         NOT NULL,
    tran_cat_cd         INTEGER         NOT NULL,
    tran_source         VARCHAR(10),
    tran_desc           VARCHAR(100),
    tran_amt            NUMERIC(11,2)   NOT NULL,   -- TRAN-AMT PIC S9(09)V99
    merchant_id         INTEGER,
    merchant_name       VARCHAR(50),
    merchant_city       VARCHAR(50),
    merchant_zip        VARCHAR(10),
    card_num            VARCHAR(16)     NOT NULL,
    orig_ts             TIMESTAMP,
    proc_ts             TIMESTAMP,

    CONSTRAINT pk_transactions PRIMARY KEY (tran_id),
    CONSTRAINT fk_transactions_cards FOREIGN KEY (card_num)
        REFERENCES cards (card_num) ON DELETE RESTRICT,
    CONSTRAINT ck_transaction_type_not_empty CHECK (tran_type_cd != '')
);

CREATE INDEX IF NOT EXISTS ix_transactions_card_num ON transactions (card_num);
CREATE INDEX IF NOT EXISTS ix_transactions_tran_type_cd ON transactions (tran_type_cd);
CREATE INDEX IF NOT EXISTS ix_transactions_orig_ts ON transactions (orig_ts);

-- ============================================================
-- USERS (USRSEC VSAM KSDS / CSUSR01Y)
-- Primary key: SEC-USR-ID PIC X(08)
-- Used by: COSGN00C (auth), COUSR00C-03C (management)
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    usr_id              VARCHAR(8)      NOT NULL,   -- SEC-USR-ID PIC X(08)
    first_name          VARCHAR(20)     NOT NULL,   -- SEC-USR-FNAME PIC X(20)
    last_name           VARCHAR(20)     NOT NULL,   -- SEC-USR-LNAME PIC X(20)
    pwd_hash            VARCHAR(72)     NOT NULL,   -- SEC-USR-PWD (bcrypt hash)
    usr_type            CHAR(1)         NOT NULL DEFAULT 'U',  -- 'A'=Admin, 'U'=User

    CONSTRAINT pk_users PRIMARY KEY (usr_id),
    CONSTRAINT ck_user_type_valid CHECK (usr_type IN ('A', 'U')),
    CONSTRAINT ck_user_id_length CHECK (length(usr_id) >= 1 AND length(usr_id) <= 8)
);

CREATE INDEX IF NOT EXISTS ix_users_usr_type ON users (usr_type);

-- ============================================================
-- TRAN_CAT_BAL (TRAN-CAT-BAL-FILE VSAM KSDS / CVTRA01Y)
-- Composite key: acct_id + tran_type_cd + tran_cat_cd
-- Used by: CBACT04C (interest calc), CBTRN02C (posting)
-- ============================================================
CREATE TABLE IF NOT EXISTS tran_cat_bal (
    acct_id             BIGINT          NOT NULL,
    tran_type_cd        CHAR(2)         NOT NULL,
    tran_cat_cd         INTEGER         NOT NULL,
    tran_cat_bal        NUMERIC(11,2)   NOT NULL DEFAULT 0.00,

    CONSTRAINT pk_tran_cat_bal PRIMARY KEY (acct_id, tran_type_cd, tran_cat_cd),
    CONSTRAINT fk_tcatbal_accounts FOREIGN KEY (acct_id)
        REFERENCES accounts (acct_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_tran_cat_bal_acct_id ON tran_cat_bal (acct_id);

-- ============================================================
-- DISCLOSURE_GROUPS (DIS-GROUP-FILE VSAM KSDS / CVTRA02Y)
-- Composite key: acct_group_id + tran_type_cd + tran_cat_cd
-- Used by: CBACT04C for interest rate lookup
-- ============================================================
CREATE TABLE IF NOT EXISTS disclosure_groups (
    acct_group_id       VARCHAR(10)     NOT NULL,
    tran_type_cd        CHAR(2)         NOT NULL,
    tran_cat_cd         INTEGER         NOT NULL,
    int_rate            NUMERIC(6,2)    NOT NULL,   -- DIS-INT-RATE PIC S9(04)V99

    CONSTRAINT pk_disclosure_groups PRIMARY KEY (acct_group_id, tran_type_cd, tran_cat_cd)
);

-- ============================================================
-- TRANSACTION_TYPES (DB2 CARDDEMO.TRANSACTION_TYPE / CVTRA03Y)
-- Used by: COTRTLIC (list), COTRTUPC (add/update/delete), CBTRN03C
-- ============================================================
CREATE TABLE IF NOT EXISTS transaction_types (
    tran_type_cd        CHAR(2)         NOT NULL,
    tran_type_desc      VARCHAR(50)     NOT NULL,

    CONSTRAINT pk_transaction_types PRIMARY KEY (tran_type_cd)
);

-- ============================================================
-- TRANSACTION_CATEGORIES (DB2 CARDDEMO.TRANSACTION_CATEGORY / CVTRA04Y)
-- Composite key: tran_type_cd + tran_cat_cd
-- Used by: COTRTUPC (SELECT via EXEC SQL INCLUDE DCLTRCAT), CBTRN03C
-- ============================================================
CREATE TABLE IF NOT EXISTS transaction_categories (
    tran_type_cd        CHAR(2)         NOT NULL,
    tran_cat_cd         INTEGER         NOT NULL,
    tran_cat_desc       VARCHAR(50)     NOT NULL,

    CONSTRAINT pk_transaction_categories PRIMARY KEY (tran_type_cd, tran_cat_cd)
);

-- ============================================================
-- AUTH_SUMMARY (IMS PAUTSUM0 segment / CIPAUSMY copybook)
-- Used by: COPAUS0C (list), COPAUA0C (update running totals)
-- ============================================================
CREATE TABLE IF NOT EXISTS auth_summary (
    acct_id             BIGINT          NOT NULL,
    cust_id             INTEGER         NOT NULL,
    auth_status         CHAR(1),
    credit_limit        NUMERIC(11,2)   NOT NULL DEFAULT 0.00,
    cash_limit          NUMERIC(11,2)   NOT NULL DEFAULT 0.00,
    curr_bal            NUMERIC(11,2)   NOT NULL DEFAULT 0.00,
    cash_bal            NUMERIC(11,2)   NOT NULL DEFAULT 0.00,
    approved_count      INTEGER         NOT NULL DEFAULT 0,
    approved_amt        NUMERIC(11,2)   NOT NULL DEFAULT 0.00,
    declined_count      INTEGER         NOT NULL DEFAULT 0,
    declined_amt        NUMERIC(11,2)   NOT NULL DEFAULT 0.00,

    CONSTRAINT pk_auth_summary PRIMARY KEY (acct_id)
);

CREATE INDEX IF NOT EXISTS ix_auth_summary_cust_id ON auth_summary (cust_id);

-- ============================================================
-- AUTH_DETAIL (IMS PAUTDTL1 segment / CIPAUDTY copybook)
-- Composite key: auth_date + auth_time + acct_id (IMS segment key)
-- Used by: COPAUS1C (view), COPAUA0C (insert), COPAUS2C (fraud flag)
-- ============================================================
CREATE TABLE IF NOT EXISTS auth_detail (
    auth_date           DATE            NOT NULL,
    auth_time           TIME            NOT NULL,
    acct_id             BIGINT          NOT NULL,
    card_num            VARCHAR(16),
    tran_id             VARCHAR(16),
    auth_id_code        VARCHAR(10),
    response_code       CHAR(2),        -- '00'=approved, '51'=insufficient funds
    response_reason     VARCHAR(25),
    approved_amt        NUMERIC(11,2)   NOT NULL DEFAULT 0.00,
    auth_type           CHAR(1),
    match_status        CHAR(1),
    fraud_flag          CHAR(1)         NOT NULL DEFAULT 'N',

    CONSTRAINT pk_auth_detail PRIMARY KEY (auth_date, auth_time, acct_id),
    CONSTRAINT fk_auth_detail_summary FOREIGN KEY (acct_id)
        REFERENCES auth_summary (acct_id) ON DELETE CASCADE,
    CONSTRAINT ck_auth_detail_fraud_flag CHECK (fraud_flag IN ('Y', 'N'))
);

CREATE INDEX IF NOT EXISTS ix_auth_detail_card_num ON auth_detail (card_num);
CREATE INDEX IF NOT EXISTS ix_auth_detail_acct_id ON auth_detail (acct_id);

-- ============================================================
-- AUTH_FRAUD (DB2 CARDDEMO.AUTHFRDS)
-- Used by: COPAUS2C (INSERT/UPDATE fraud records)
-- ============================================================
CREATE TABLE IF NOT EXISTS auth_fraud (
    fraud_id            SERIAL          NOT NULL,
    card_num            VARCHAR(16)     NOT NULL,
    acct_id             BIGINT          NOT NULL,
    auth_date           DATE,
    auth_time           TIME,
    fraud_reason        VARCHAR(100),
    flagged_by          VARCHAR(8),
    flagged_ts          TIMESTAMP,
    fraud_status        CHAR(1)         DEFAULT 'P',  -- P=pending, C=confirmed, R=resolved

    CONSTRAINT pk_auth_fraud PRIMARY KEY (fraud_id)
);

CREATE INDEX IF NOT EXISTS ix_auth_fraud_card_num ON auth_fraud (card_num);
CREATE INDEX IF NOT EXISTS ix_auth_fraud_acct_id ON auth_fraud (acct_id);
