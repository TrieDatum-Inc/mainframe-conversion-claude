-- CardDemo PostgreSQL Schema
-- Converted from COBOL VSAM/DB2 data structures
-- Source: CSUSR01Y, CVACT01Y, CVACT02Y, CVACT03Y, CVCUS01Y, CVTRA01Y-05Y, AUTHFRDS DB2 table
-- Migration: Auth & Navigation Module (COSGN00C / COMEN01C / COADM01C)

-- ============================================================
-- USERS TABLE (from USRSEC VSAM KSDS — CSUSR01Y copybook)
-- COBOL key: SEC-USR-ID PIC X(08)
-- NOTE: Password is bcrypt-hashed; COBOL stored plaintext PIC X(08)
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    user_id        VARCHAR(8)   PRIMARY KEY,
    first_name     VARCHAR(20)  NOT NULL,
    last_name      VARCHAR(20)  NOT NULL,
    password       VARCHAR(255) NOT NULL,  -- bcrypt hash (COBOL was plaintext PIC X(08))
    user_type      CHAR(1)      NOT NULL CHECK (user_type IN ('A', 'U')),  -- A=Admin, U=Regular
    created_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- CUSTOMERS TABLE (from CUSTDAT VSAM KSDS — CVCUS01Y copybook)
-- COBOL key: CUST-ID PIC 9(09)
-- ============================================================
CREATE TABLE IF NOT EXISTS customers (
    cust_id                  NUMERIC(9)   PRIMARY KEY,
    first_name               VARCHAR(25)  NOT NULL,
    middle_name              VARCHAR(25),
    last_name                VARCHAR(25)  NOT NULL,
    addr_line_1              VARCHAR(50),
    addr_line_2              VARCHAR(50),
    addr_line_3              VARCHAR(50),
    addr_state_cd            CHAR(2),
    addr_country_cd          CHAR(3),
    addr_zip                 VARCHAR(10),
    phone_num_1              VARCHAR(15),
    phone_num_2              VARCHAR(15),
    ssn                      NUMERIC(9),   -- COBOL: CUST-SSN PIC 9(09) — sensitive PII
    govt_issued_id           VARCHAR(20),
    dob                      DATE,         -- COBOL: CUST-DOB-YYYY-MM-DD X(10)
    eft_account_id           VARCHAR(10),
    primary_card_holder_ind  CHAR(1),
    fico_credit_score        SMALLINT CHECK (fico_credit_score BETWEEN 300 AND 850),
    created_at               TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at               TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- ACCOUNTS TABLE (from ACCTDAT VSAM KSDS — CVACT01Y copybook)
-- COBOL key: ACCT-ID PIC 9(11)
-- ============================================================
CREATE TABLE IF NOT EXISTS accounts (
    acct_id               NUMERIC(11)     PRIMARY KEY,
    active_status         CHAR(1)         NOT NULL DEFAULT 'Y' CHECK (active_status IN ('Y', 'N')),
    curr_bal              NUMERIC(12, 2)  NOT NULL DEFAULT 0,   -- COBOL: S9(10)V99
    credit_limit          NUMERIC(12, 2)  NOT NULL DEFAULT 0,   -- COBOL: S9(10)V99
    cash_credit_limit     NUMERIC(12, 2)  NOT NULL DEFAULT 0,   -- COBOL: S9(10)V99
    open_date             DATE,           -- COBOL: ACCT-OPEN-DATE X(10) YYYY-MM-DD
    expiration_date       DATE,           -- COBOL: ACCT-EXPIRAION-DATE X(10) [typo preserved from source]
    reissue_date          DATE,
    curr_cycle_credit     NUMERIC(12, 2)  NOT NULL DEFAULT 0,
    curr_cycle_debit      NUMERIC(12, 2)  NOT NULL DEFAULT 0,
    addr_zip              VARCHAR(10),
    group_id              VARCHAR(10),    -- Links to disclosure_groups
    created_at            TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at            TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- CARDS TABLE (from CARDDAT VSAM KSDS — CVACT02Y copybook)
-- COBOL key: CARD-NUM PIC X(16)
-- ============================================================
CREATE TABLE IF NOT EXISTS cards (
    card_num           VARCHAR(16)   PRIMARY KEY,
    acct_id            NUMERIC(11)   NOT NULL REFERENCES accounts(acct_id),
    cvv_cd             NUMERIC(3),   -- COBOL: CARD-CVV-CD PIC 9(03)
    embossed_name      VARCHAR(50),
    expiration_date    DATE,         -- COBOL: CARD-EXPIRAION-DATE X(10) [typo preserved]
    active_status      CHAR(1)       NOT NULL DEFAULT 'Y' CHECK (active_status IN ('Y', 'N')),
    created_at         TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at         TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- CARD CROSS-REFERENCES TABLE (from XREFFILE VSAM KSDS — CVACT03Y copybook)
-- COBOL key: XREF-CARD-NUM PIC X(16)
-- ============================================================
CREATE TABLE IF NOT EXISTS card_cross_references (
    card_num   VARCHAR(16)  PRIMARY KEY REFERENCES cards(card_num),
    cust_id    NUMERIC(9)   NOT NULL REFERENCES customers(cust_id),
    acct_id    NUMERIC(11)  NOT NULL REFERENCES accounts(acct_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_card_xref_acct_id ON card_cross_references(acct_id);
CREATE INDEX IF NOT EXISTS idx_card_xref_cust_id ON card_cross_references(cust_id);

-- ============================================================
-- TRANSACTION TYPES TABLE (from TRANTYPE VSAM KSDS + DB2 TRANSACTION_TYPE)
-- COBOL key: TRAN-TYPE PIC X(02)
-- ============================================================
CREATE TABLE IF NOT EXISTS transaction_types (
    tran_type_cd   CHAR(2)      PRIMARY KEY,   -- COBOL: TRAN-TYPE PIC X(02)
    description    VARCHAR(50)  NOT NULL        -- COBOL: TRAN-TYPE-DESC PIC X(50)
);

-- ============================================================
-- TRANSACTION CATEGORIES TABLE (from TRANCATG VSAM KSDS + DB2 TRANSACTION_TYPE_CATEGORY)
-- COBOL composite key: type_code + category_code
-- ============================================================
CREATE TABLE IF NOT EXISTS transaction_categories (
    tran_type_cd   CHAR(2)      NOT NULL REFERENCES transaction_types(tran_type_cd),
    tran_cat_cd    NUMERIC(4)   NOT NULL,   -- COBOL: TRAN-CAT-CD PIC 9(04)
    description    VARCHAR(50)  NOT NULL,
    PRIMARY KEY (tran_type_cd, tran_cat_cd)
);

-- ============================================================
-- TRANSACTIONS TABLE (from TRANSACT VSAM KSDS — CVTRA05Y copybook)
-- COBOL key: TRAN-ID PIC X(16)
-- ============================================================
CREATE TABLE IF NOT EXISTS transactions (
    tran_id           VARCHAR(16)   PRIMARY KEY,
    tran_type_cd      CHAR(2)       REFERENCES transaction_types(tran_type_cd),
    tran_cat_cd       NUMERIC(4),
    source            VARCHAR(10),   -- COBOL: TRAN-SOURCE PIC X(10)
    description       VARCHAR(100),  -- COBOL: TRAN-DESC PIC X(100)
    amount            NUMERIC(11, 2) NOT NULL,  -- COBOL: TRAN-AMT S9(09)V99
    merchant_id       NUMERIC(9),
    merchant_name     VARCHAR(50),
    merchant_city     VARCHAR(50),
    merchant_zip      VARCHAR(10),
    card_num          VARCHAR(16)    REFERENCES cards(card_num),
    orig_timestamp    TIMESTAMP WITH TIME ZONE,  -- COBOL: TRAN-ORIG-TS X(26)
    proc_timestamp    TIMESTAMP WITH TIME ZONE,  -- COBOL: TRAN-PROC-TS X(26)
    created_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transactions_card_num  ON transactions(card_num);
CREATE INDEX IF NOT EXISTS idx_transactions_orig_ts   ON transactions(orig_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_type_cat  ON transactions(tran_type_cd, tran_cat_cd);

-- ============================================================
-- TRANSACTION CATEGORY BALANCES TABLE (from TCATBALF VSAM KSDS — CVTRA01Y copybook)
-- COBOL composite key: TRANCAT-ACCT-ID + TRANCAT-TYPE-CD + TRANCAT-CD
-- ============================================================
CREATE TABLE IF NOT EXISTS transaction_category_balances (
    acct_id       NUMERIC(11)   NOT NULL REFERENCES accounts(acct_id),
    tran_type_cd  CHAR(2)       NOT NULL,
    tran_cat_cd   NUMERIC(4)    NOT NULL,
    balance       NUMERIC(12, 2) NOT NULL DEFAULT 0,
    updated_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (acct_id, tran_type_cd, tran_cat_cd)
);

-- ============================================================
-- DISCLOSURE GROUPS TABLE (from DISCGRP VSAM KSDS — CVTRA02Y copybook)
-- COBOL composite key: DIS-ACCT-GROUP-ID + DIS-TRAN-TYPE-CD + DIS-TRAN-CAT-CD
-- ============================================================
CREATE TABLE IF NOT EXISTS disclosure_groups (
    acct_group_id  VARCHAR(10)   NOT NULL,
    tran_type_cd   CHAR(2)       NOT NULL,
    tran_cat_cd    NUMERIC(4)    NOT NULL,
    interest_rate  NUMERIC(5, 2) NOT NULL DEFAULT 0,  -- inferred from context
    fee_amount     NUMERIC(9, 2) NOT NULL DEFAULT 0,  -- inferred from context
    PRIMARY KEY (acct_group_id, tran_type_cd, tran_cat_cd)
);

-- ============================================================
-- DAILY REJECTS TABLE (from DALYREJS GDG — for batch rejected transactions)
-- ============================================================
CREATE TABLE IF NOT EXISTS daily_rejects (
    id             BIGSERIAL    PRIMARY KEY,
    tran_id        VARCHAR(16),
    reject_code    VARCHAR(10)  NOT NULL,
    reject_reason  VARCHAR(100),
    raw_data       TEXT,
    rejected_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- AUTHORIZATION FRAUD TABLE (from AUTHFRDS DB2 table — Authorization Extension)
-- DB2 unique index XAUTHFRD on (CARD_NUM ASC, AUTH_TS DESC)
-- ============================================================
CREATE TABLE IF NOT EXISTS authorization_fraud (
    card_num                VARCHAR(16)    NOT NULL,
    auth_ts                 TIMESTAMP WITH TIME ZONE NOT NULL,
    auth_type               CHAR(4),
    card_expiry_date        CHAR(4),
    message_type            CHAR(6),
    message_source          CHAR(6),
    auth_id_code            CHAR(6),
    auth_resp_code          CHAR(2),
    auth_resp_reason        CHAR(4),
    processing_code         CHAR(6),
    transaction_amt         NUMERIC(12, 2),
    approved_amt            NUMERIC(12, 2),
    merchant_category_code  CHAR(4),       -- Note: DB2 source has typo "CATAGORY"
    acqr_country_code       CHAR(3),
    pos_entry_mode          SMALLINT,
    merchant_id             CHAR(15),
    merchant_name           VARCHAR(22),
    merchant_city           CHAR(13),
    merchant_state          CHAR(2),
    merchant_zip            CHAR(9),
    transaction_id          CHAR(15),
    match_status            CHAR(1),
    auth_fraud              CHAR(1),
    fraud_rpt_date          DATE,
    acct_id                 NUMERIC(11),
    cust_id                 NUMERIC(9),
    PRIMARY KEY (card_num, auth_ts)
);

CREATE UNIQUE INDEX IF NOT EXISTS xauthfrd ON authorization_fraud(card_num ASC, auth_ts DESC);

-- ============================================================
-- REPORT JOBS TABLE (new — replaces CORPT00C TDQ JOBS submission)
-- COBOL equivalent: EXEC CICS WRITEQ TD QUEUE('JOBS') writes JCL to internal reader
-- Modern: INSERT a report_jobs row; background processing handles execution
-- PROC TRANREPT → background task reading transactions filtered by date range
-- ============================================================
CREATE TABLE IF NOT EXISTS report_jobs (
    job_id         SERIAL          PRIMARY KEY,
    report_type    VARCHAR(20)     NOT NULL,   -- 'monthly', 'yearly', 'custom' (WS-REPORT-NAME)
    start_date     DATE            NOT NULL,   -- PARM-START-DATE in JCL inline data
    end_date       DATE            NOT NULL,   -- PARM-END-DATE in JCL inline data
    status         VARCHAR(20)     NOT NULL DEFAULT 'pending',  -- pending/running/completed/failed
    submitted_by   VARCHAR(8),                -- CDEMO-USERID from COMMAREA
    submitted_at   TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at   TIMESTAMP WITH TIME ZONE,
    result_path    VARCHAR(255)               -- path to generated report (replaces GDG TRANREPT)
);

CREATE INDEX IF NOT EXISTS idx_report_jobs_submitted_at ON report_jobs(submitted_at DESC);
CREATE INDEX IF NOT EXISTS idx_report_jobs_status ON report_jobs(status);
