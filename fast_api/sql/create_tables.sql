-- Account Management Module: PostgreSQL Schema
-- Converted from COBOL VSAM files: ACCTDAT, CUSTDAT, CARDDAT, CXACAIX
-- Source copybooks: CVACT01Y, CVCUS01Y, CVACT02Y, CVACT03Y

-- Customers table (from CVCUS01Y copybook)
CREATE TABLE IF NOT EXISTS customers (
    cust_id             VARCHAR(9)   PRIMARY KEY,
    cust_first_name     VARCHAR(25),
    cust_middle_name    VARCHAR(25),
    cust_last_name      VARCHAR(25),
    cust_addr_line_1    VARCHAR(50),
    cust_addr_line_2    VARCHAR(50),
    cust_addr_line_3    VARCHAR(50),
    cust_addr_state_cd  CHAR(2),
    cust_addr_country_cd CHAR(3),
    cust_addr_zip       VARCHAR(10),
    cust_phone_num_1    VARCHAR(15),
    cust_phone_num_2    VARCHAR(15),
    cust_ssn            VARCHAR(9),
    cust_govt_issued_id VARCHAR(20),
    cust_dob            DATE,
    cust_eft_account_id VARCHAR(10),
    cust_pri_card_holder_ind CHAR(1) CHECK (cust_pri_card_holder_ind IN ('Y', 'N')),
    cust_fico_credit_score   INTEGER CHECK (cust_fico_credit_score BETWEEN 300 AND 850),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Accounts table (from CVACT01Y copybook)
-- ACCT-ID is 9(11) numeric in COBOL → VARCHAR(11) to preserve leading zeros if any
CREATE TABLE IF NOT EXISTS accounts (
    acct_id                 VARCHAR(11)     PRIMARY KEY,
    acct_active_status      CHAR(1)         NOT NULL DEFAULT 'Y'
                                CHECK (acct_active_status IN ('Y', 'N')),
    acct_curr_bal           NUMERIC(12, 2)  NOT NULL DEFAULT 0,
    acct_credit_limit       NUMERIC(12, 2)  NOT NULL DEFAULT 0,
    acct_cash_credit_limit  NUMERIC(12, 2)  NOT NULL DEFAULT 0,
    acct_open_date          DATE,
    acct_expiration_date    DATE,
    acct_reissue_date       DATE,
    acct_curr_cyc_credit    NUMERIC(12, 2)  NOT NULL DEFAULT 0,
    acct_curr_cyc_debit     NUMERIC(12, 2)  NOT NULL DEFAULT 0,
    acct_addr_zip           VARCHAR(10),
    acct_group_id           VARCHAR(10),
    updated_at              TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Cards table (from CVACT02Y copybook)
CREATE TABLE IF NOT EXISTS cards (
    card_num            VARCHAR(16)  PRIMARY KEY,
    card_acct_id        VARCHAR(11)  REFERENCES accounts(acct_id),
    card_cvv_cd         VARCHAR(3),
    card_embossed_name  VARCHAR(50),
    card_expiration_date DATE,
    card_active_status  CHAR(1)      DEFAULT 'Y' CHECK (card_active_status IN ('Y', 'N')),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Card cross-references table (from CVACT03Y copybook)
-- Replaces CXACAIX VSAM alternate index (keyed by XREF-ACCT-ID)
-- In PostgreSQL this is a regular table with a FK index on xref_acct_id
CREATE TABLE IF NOT EXISTS card_cross_references (
    xref_card_num   VARCHAR(16)  PRIMARY KEY,
    xref_cust_id    VARCHAR(9)   REFERENCES customers(cust_id),
    xref_acct_id    VARCHAR(11)  REFERENCES accounts(acct_id)
);

-- Index on xref_acct_id to replicate the CXACAIX alternate index lookup
CREATE INDEX IF NOT EXISTS idx_card_xref_acct_id
    ON card_cross_references (xref_acct_id);

-- Index on xref_cust_id for reverse lookups
CREATE INDEX IF NOT EXISTS idx_card_xref_cust_id
    ON card_cross_references (xref_cust_id);

-- Trigger function: automatically update updated_at on row changes
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach trigger to accounts
DROP TRIGGER IF EXISTS trg_accounts_updated_at ON accounts;
CREATE TRIGGER trg_accounts_updated_at
    BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Attach trigger to customers
DROP TRIGGER IF EXISTS trg_customers_updated_at ON customers;
CREATE TRIGGER trg_customers_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
