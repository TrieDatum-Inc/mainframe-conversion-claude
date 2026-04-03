-- CardDemo Batch Processing Module: PostgreSQL Schema
-- Converted from VSAM KSDS and sequential file structures
-- Maps COBOL PIC types to PostgreSQL types per spec

-- Accounts table (CVACT01Y / ACCTFILE KSDS)
CREATE TABLE IF NOT EXISTS accounts (
    acct_id VARCHAR(11) PRIMARY KEY,
    acct_active_status CHAR(1) DEFAULT 'Y' CHECK (acct_active_status IN ('Y', 'N')),
    acct_curr_bal NUMERIC(12, 2) DEFAULT 0,
    acct_credit_limit NUMERIC(12, 2) DEFAULT 0,
    acct_cash_credit_limit NUMERIC(12, 2) DEFAULT 0,
    acct_open_date DATE,
    acct_expiration_date DATE,
    acct_reissue_date DATE,
    acct_curr_cyc_credit NUMERIC(12, 2) DEFAULT 0,
    acct_curr_cyc_debit NUMERIC(12, 2) DEFAULT 0,
    acct_addr_zip VARCHAR(10),
    acct_group_id VARCHAR(10),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Transactions table (CVTRA05Y / TRANSACT KSDS)
CREATE TABLE IF NOT EXISTS transactions (
    tran_id VARCHAR(16) PRIMARY KEY,
    tran_type_cd CHAR(2),
    tran_cat_cd VARCHAR(4),
    tran_source VARCHAR(10),
    tran_desc VARCHAR(100),
    tran_amt NUMERIC(11, 2),
    tran_merchant_id VARCHAR(9),
    tran_merchant_name VARCHAR(50),
    tran_merchant_city VARCHAR(50),
    tran_merchant_zip VARCHAR(10),
    tran_card_num VARCHAR(16),
    tran_orig_ts TIMESTAMP WITH TIME ZONE,
    tran_proc_ts TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Cards table (CVACT02Y / CARDFILE KSDS)
CREATE TABLE IF NOT EXISTS cards (
    card_num VARCHAR(16) PRIMARY KEY,
    card_acct_id VARCHAR(11),
    card_cvv_cd VARCHAR(3),
    card_embossed_name VARCHAR(50),
    card_expiration_date DATE,
    card_active_status CHAR(1) DEFAULT 'Y' CHECK (card_active_status IN ('Y', 'N')),
    FOREIGN KEY (card_acct_id) REFERENCES accounts(acct_id)
);

-- Card cross-references table (CVACT03Y / XREFFILE KSDS)
-- Primary key: card_num; alternate key: xref_acct_id (used by CBACT04C)
CREATE TABLE IF NOT EXISTS card_cross_references (
    xref_card_num VARCHAR(16) PRIMARY KEY,
    xref_cust_id VARCHAR(9),
    xref_acct_id VARCHAR(11),
    FOREIGN KEY (xref_acct_id) REFERENCES accounts(acct_id)
);

CREATE INDEX IF NOT EXISTS idx_card_xref_acct_id ON card_cross_references (xref_acct_id);

-- Customers table (CVCUS01Y / CUSTFILE KSDS)
CREATE TABLE IF NOT EXISTS customers (
    cust_id VARCHAR(9) PRIMARY KEY,
    cust_first_name VARCHAR(25),
    cust_middle_name VARCHAR(25),
    cust_last_name VARCHAR(25),
    cust_addr_line_1 VARCHAR(50),
    cust_addr_line_2 VARCHAR(50),
    cust_addr_line_3 VARCHAR(50),
    cust_addr_state_cd CHAR(2),
    cust_addr_country_cd CHAR(3),
    cust_addr_zip VARCHAR(10),
    cust_phone_num_1 VARCHAR(15),
    cust_phone_num_2 VARCHAR(15),
    cust_ssn VARCHAR(9),
    cust_govt_issued_id VARCHAR(20),
    cust_dob DATE,
    cust_eft_account_id VARCHAR(10),
    cust_pri_card_holder_ind CHAR(1),
    cust_fico_credit_score INTEGER
);

-- Transaction category balances (CVTRA01Y / TCATBALF KSDS)
-- Composite key: acct_id + tran_type_cd + tran_cat_cd
-- Used by CBTRN02C (update) and CBACT04C (sequential read)
CREATE TABLE IF NOT EXISTS transaction_category_balances (
    acct_id VARCHAR(11),
    tran_type_cd CHAR(2),
    tran_cat_cd VARCHAR(4),
    balance NUMERIC(12, 2) DEFAULT 0,
    PRIMARY KEY (acct_id, tran_type_cd, tran_cat_cd),
    FOREIGN KEY (acct_id) REFERENCES accounts(acct_id)
);

-- Disclosure groups / interest rates (CVTRA02Y / DISCGRP KSDS)
-- Composite key: group_id + tran_type_cd + tran_cat_cd
-- 'DEFAULT' group_id used as fallback by CBACT04C
CREATE TABLE IF NOT EXISTS disclosure_groups (
    group_id VARCHAR(10),
    tran_type_cd CHAR(2),
    tran_cat_cd VARCHAR(4),
    interest_rate NUMERIC(7, 4) DEFAULT 0,
    PRIMARY KEY (group_id, tran_type_cd, tran_cat_cd)
);

-- Transaction types reference (CVTRA03Y / TRANTYPE KSDS)
-- Used by CBTRN03C for report enrichment
CREATE TABLE IF NOT EXISTS transaction_types (
    tran_type CHAR(2) PRIMARY KEY,
    tran_type_desc VARCHAR(50)
);

-- Transaction categories reference (CVTRA04Y / TRANCATG KSDS)
-- Composite key: tran_type + tran_cat_cd
-- Used by CBTRN03C for report enrichment
CREATE TABLE IF NOT EXISTS transaction_categories (
    tran_type CHAR(2),
    tran_cat_cd VARCHAR(4),
    tran_cat_desc VARCHAR(50),
    PRIMARY KEY (tran_type, tran_cat_cd)
);

-- Batch job tracking
-- Maps JCL job execution metadata to a persistent audit table
CREATE TABLE IF NOT EXISTS batch_jobs (
    job_id SERIAL PRIMARY KEY,
    job_type VARCHAR(30) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    records_processed INTEGER DEFAULT 0,
    records_rejected INTEGER DEFAULT 0,
    result_summary JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Daily transaction rejects (DALYREJS GDG)
-- Maps COBOL reject record: 350-byte DALYTRAN + 80-byte validation trailer
CREATE TABLE IF NOT EXISTS daily_rejects (
    reject_id SERIAL PRIMARY KEY,
    batch_job_id INTEGER REFERENCES batch_jobs(job_id),
    tran_id VARCHAR(16),
    card_num VARCHAR(16),
    reason_code VARCHAR(3),
    reason_desc VARCHAR(100),
    original_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_daily_rejects_job ON daily_rejects (batch_job_id);
CREATE INDEX IF NOT EXISTS idx_daily_rejects_card ON daily_rejects (card_num);
CREATE INDEX IF NOT EXISTS idx_transactions_card ON transactions (tran_card_num);
CREATE INDEX IF NOT EXISTS idx_transactions_proc_ts ON transactions (tran_proc_ts);
CREATE INDEX IF NOT EXISTS idx_transactions_type_cat ON transactions (tran_type_cd, tran_cat_cd);
CREATE INDEX IF NOT EXISTS idx_tcatbal_acct ON transaction_category_balances (acct_id);
