-- CardDemo Transaction Processing Module
-- PostgreSQL Schema
-- Converted from VSAM KSDS files: TRANSACT, CCXREF, CXACAIX, ACCTDAT

-- Transaction ID sequence for auto-increment (mirrors COBOL HIGH-VALUES + 1 pattern)
CREATE SEQUENCE IF NOT EXISTS transaction_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS transactions (
    tran_id         VARCHAR(16)  PRIMARY KEY,
    tran_type_cd    CHAR(2)      NOT NULL,
    tran_cat_cd     VARCHAR(4)   NOT NULL,
    tran_source     VARCHAR(10)  NOT NULL,
    tran_desc       VARCHAR(100) NOT NULL,
    tran_amt        NUMERIC(11, 2) NOT NULL,
    tran_merchant_id  VARCHAR(9)  NOT NULL,
    tran_merchant_name VARCHAR(50) NOT NULL,
    tran_merchant_city VARCHAR(50) NOT NULL,
    tran_merchant_zip  VARCHAR(10) NOT NULL,
    tran_card_num   VARCHAR(16)  NOT NULL,
    tran_orig_ts    TIMESTAMP WITH TIME ZONE NOT NULL,
    tran_proc_ts    TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transactions_tran_id     ON transactions (tran_id);
CREATE INDEX IF NOT EXISTS idx_transactions_tran_card_num ON transactions (tran_card_num);
CREATE INDEX IF NOT EXISTS idx_transactions_tran_orig_ts ON transactions (tran_orig_ts DESC);

-- Card cross-reference: primary key on card number (CCXREF)
-- Alternate index on account ID (CXACAIX) implemented via unique index
CREATE TABLE IF NOT EXISTS card_cross_references (
    xref_card_num  VARCHAR(16) PRIMARY KEY,
    xref_cust_id   VARCHAR(9)  NOT NULL,
    xref_acct_id   VARCHAR(11) NOT NULL,
    UNIQUE (xref_acct_id)   -- enforces AIX uniqueness (CXACAIX alternate index)
);

CREATE INDEX IF NOT EXISTS idx_xref_acct_id ON card_cross_references (xref_acct_id);

-- Account master (ACCTDAT)
CREATE TABLE IF NOT EXISTS accounts (
    acct_id              VARCHAR(11) PRIMARY KEY,
    acct_active_status   CHAR(1)     NOT NULL DEFAULT 'Y'
                             CHECK (acct_active_status IN ('Y', 'N')),
    acct_curr_bal        NUMERIC(12, 2) NOT NULL DEFAULT 0,
    acct_credit_limit    NUMERIC(12, 2) NOT NULL DEFAULT 0,
    acct_cash_credit_limit NUMERIC(12, 2) NOT NULL DEFAULT 0,
    acct_open_date       DATE,
    acct_expiration_date DATE,
    acct_reissue_date    DATE,
    acct_curr_cyc_credit NUMERIC(12, 2) NOT NULL DEFAULT 0,
    acct_curr_cyc_debit  NUMERIC(12, 2) NOT NULL DEFAULT 0,
    acct_addr_zip        VARCHAR(10),
    acct_group_id        VARCHAR(10),
    updated_at           TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Transaction types reference table (TRANTYPE)
CREATE TABLE IF NOT EXISTS transaction_types (
    tran_type      CHAR(2)     PRIMARY KEY,
    tran_type_desc VARCHAR(50) NOT NULL
);

-- Transaction categories reference table (TRANCATG)
-- Composite key: type + category code
CREATE TABLE IF NOT EXISTS transaction_categories (
    tran_type    CHAR(2)     NOT NULL REFERENCES transaction_types(tran_type),
    tran_cat_cd  VARCHAR(4)  NOT NULL,
    tran_cat_desc VARCHAR(50) NOT NULL,
    PRIMARY KEY (tran_type, tran_cat_cd)
);
