-- ============================================================================
-- CardDemo COBOL-to-Databricks Migration: Delta Table DDL
-- Replicates COBOL VSAM/Sequential file layouts as Delta tables
-- ============================================================================
-- Run this notebook in a Databricks SQL or Python notebook to create the
-- schema and all required Delta tables.
-- ============================================================================

-- Create a dedicated schema (database) for the CardDemo application
CREATE SCHEMA IF NOT EXISTS carddemo;
USE carddemo;

-- ============================================================================
-- 1. DAILY_TRANSACTIONS  (CVTRA06Y / DALYTRAN-RECORD)
--    Input sequential file for CBTRN02C batch posting.
--    350-byte COBOL record.
-- ============================================================================
CREATE TABLE IF NOT EXISTS daily_transactions (
    dalytran_id               STRING        NOT NULL   COMMENT 'Transaction ID - PIC X(16)',
    dalytran_type_cd          STRING        NOT NULL   COMMENT 'Transaction type code - PIC X(02)',
    dalytran_cat_cd           INT           NOT NULL   COMMENT 'Transaction category code - PIC 9(04)',
    dalytran_source           STRING                   COMMENT 'Transaction source - PIC X(10)',
    dalytran_desc             STRING                   COMMENT 'Description - PIC X(100)',
    dalytran_amt              DECIMAL(11,2) NOT NULL   COMMENT 'Amount - PIC S9(09)V99',
    dalytran_merchant_id      BIGINT                   COMMENT 'Merchant ID - PIC 9(09)',
    dalytran_merchant_name    STRING                   COMMENT 'Merchant name - PIC X(50)',
    dalytran_merchant_city    STRING                   COMMENT 'Merchant city - PIC X(50)',
    dalytran_merchant_zip     STRING                   COMMENT 'Merchant zip - PIC X(10)',
    dalytran_card_num         STRING        NOT NULL   COMMENT 'Card number - PIC X(16)',
    dalytran_orig_ts          STRING                   COMMENT 'Original timestamp - PIC X(26)',
    dalytran_proc_ts          STRING                   COMMENT 'Processing timestamp - PIC X(26)'
)
USING DELTA
COMMENT 'Daily transaction input file - Source: DALYTRAN DD (sequential)'
TBLPROPERTIES ('cobol.copybook' = 'CVTRA06Y', 'cobol.program' = 'CBTRN02C');

-- ============================================================================
-- 2. TRANSACTIONS  (CVTRA05Y / TRAN-RECORD)
--    Posted transactions VSAM KSDS file.
--    Written by CBTRN02C, read by CBTRN03C and CBSTM03A.
--    350-byte COBOL record.
-- ============================================================================
CREATE TABLE IF NOT EXISTS transactions (
    tran_id                   STRING        NOT NULL   COMMENT 'Transaction ID - PIC X(16)',
    tran_type_cd              STRING        NOT NULL   COMMENT 'Transaction type code - PIC X(02)',
    tran_cat_cd               INT           NOT NULL   COMMENT 'Transaction category code - PIC 9(04)',
    tran_source               STRING                   COMMENT 'Transaction source - PIC X(10)',
    tran_desc                 STRING                   COMMENT 'Description - PIC X(100)',
    tran_amt                  DECIMAL(11,2) NOT NULL   COMMENT 'Amount - PIC S9(09)V99',
    tran_merchant_id          BIGINT                   COMMENT 'Merchant ID - PIC 9(09)',
    tran_merchant_name        STRING                   COMMENT 'Merchant name - PIC X(50)',
    tran_merchant_city        STRING                   COMMENT 'Merchant city - PIC X(50)',
    tran_merchant_zip         STRING                   COMMENT 'Merchant zip - PIC X(10)',
    tran_card_num             STRING        NOT NULL   COMMENT 'Card number - PIC X(16)',
    tran_orig_ts              STRING                   COMMENT 'Original timestamp - PIC X(26)',
    tran_proc_ts              STRING                   COMMENT 'Processing timestamp - PIC X(26)',
    CONSTRAINT pk_transactions PRIMARY KEY (tran_id)
)
USING DELTA
COMMENT 'Posted transactions VSAM KSDS - Source: TRANFILE DD'
TBLPROPERTIES ('cobol.copybook' = 'CVTRA05Y', 'cobol.program' = 'CBTRN02C,CBACT04C,CBTRN03C,CBSTM03A');

-- ============================================================================
-- 3. CARD_XREF  (CVACT03Y / CARD-XREF-RECORD)
--    Card-to-Account cross-reference VSAM KSDS.
--    50-byte COBOL record. Primary key: card_num. Alt key: acct_id.
-- ============================================================================
CREATE TABLE IF NOT EXISTS card_xref (
    xref_card_num             STRING        NOT NULL   COMMENT 'Card number (primary key) - PIC X(16)',
    xref_cust_id              BIGINT        NOT NULL   COMMENT 'Customer ID - PIC 9(09)',
    xref_acct_id              BIGINT        NOT NULL   COMMENT 'Account ID - PIC 9(11)',
    CONSTRAINT pk_card_xref PRIMARY KEY (xref_card_num)
)
USING DELTA
COMMENT 'Card cross-reference VSAM KSDS - Source: XREFFILE/CARDXREF DD'
TBLPROPERTIES ('cobol.copybook' = 'CVACT03Y');

-- ============================================================================
-- 4. CUSTOMERS  (CUSTREC / CUSTOMER-RECORD)
--    Customer master VSAM KSDS.
--    500-byte COBOL record. Key: cust_id.
-- ============================================================================
CREATE TABLE IF NOT EXISTS customers (
    cust_id                   BIGINT        NOT NULL   COMMENT 'Customer ID - PIC 9(09)',
    cust_first_name           STRING                   COMMENT 'First name - PIC X(25)',
    cust_middle_name          STRING                   COMMENT 'Middle name - PIC X(25)',
    cust_last_name            STRING                   COMMENT 'Last name - PIC X(25)',
    cust_addr_line_1          STRING                   COMMENT 'Address line 1 - PIC X(50)',
    cust_addr_line_2          STRING                   COMMENT 'Address line 2 - PIC X(50)',
    cust_addr_line_3          STRING                   COMMENT 'Address line 3 - PIC X(50)',
    cust_addr_state_cd        STRING                   COMMENT 'State code - PIC X(02)',
    cust_addr_country_cd      STRING                   COMMENT 'Country code - PIC X(03)',
    cust_addr_zip             STRING                   COMMENT 'Zip code - PIC X(10)',
    cust_phone_num_1          STRING                   COMMENT 'Phone 1 - PIC X(15)',
    cust_phone_num_2          STRING                   COMMENT 'Phone 2 - PIC X(15)',
    cust_ssn                  BIGINT                   COMMENT 'SSN - PIC 9(09)',
    cust_govt_issued_id       STRING                   COMMENT 'Govt issued ID - PIC X(20)',
    cust_dob_yyyymmdd         STRING                   COMMENT 'DOB - PIC X(10)',
    cust_eft_account_id       STRING                   COMMENT 'EFT account - PIC X(10)',
    cust_pri_card_holder_ind  STRING                   COMMENT 'Primary cardholder - PIC X(01)',
    cust_fico_credit_score    INT                      COMMENT 'FICO score - PIC 9(03)',
    CONSTRAINT pk_customers PRIMARY KEY (cust_id)
)
USING DELTA
COMMENT 'Customer master VSAM KSDS - Source: CUSTFILE DD'
TBLPROPERTIES ('cobol.copybook' = 'CUSTREC');

-- ============================================================================
-- 5. ACCOUNTS  (CVACT01Y / ACCOUNT-RECORD)
--    Account master VSAM KSDS. Updated by CBTRN02C and CBACT04C.
--    300-byte COBOL record. Key: acct_id.
-- ============================================================================
CREATE TABLE IF NOT EXISTS accounts (
    acct_id                   BIGINT        NOT NULL   COMMENT 'Account ID - PIC 9(11)',
    acct_active_status        STRING                   COMMENT 'Active status - PIC X(01)',
    acct_curr_bal             DECIMAL(12,2) NOT NULL   COMMENT 'Current balance - PIC S9(10)V99',
    acct_credit_limit         DECIMAL(12,2)            COMMENT 'Credit limit - PIC S9(10)V99',
    acct_cash_credit_limit    DECIMAL(12,2)            COMMENT 'Cash credit limit - PIC S9(10)V99',
    acct_open_date            STRING                   COMMENT 'Open date - PIC X(10)',
    acct_expiraion_date       STRING                   COMMENT 'Expiration date - PIC X(10) (sic)',
    acct_reissue_date         STRING                   COMMENT 'Reissue date - PIC X(10)',
    acct_curr_cyc_credit      DECIMAL(12,2) NOT NULL DEFAULT 0  COMMENT 'Current cycle credit - PIC S9(10)V99',
    acct_curr_cyc_debit       DECIMAL(12,2) NOT NULL DEFAULT 0  COMMENT 'Current cycle debit - PIC S9(10)V99',
    acct_addr_zip             STRING                   COMMENT 'Zip code - PIC X(10)',
    acct_group_id             STRING                   COMMENT 'Group ID - PIC X(10)',
    CONSTRAINT pk_accounts PRIMARY KEY (acct_id)
)
USING DELTA
COMMENT 'Account master VSAM KSDS - Source: ACCTFILE DD'
TBLPROPERTIES ('cobol.copybook' = 'CVACT01Y', 'delta.feature.allowColumnDefaults' = 'supported');

-- ============================================================================
-- 6. TRANSACTION_CATEGORY_BALANCES  (CVTRA01Y / TRAN-CAT-BAL-RECORD)
--    Category balance VSAM KSDS.
--    Written/updated by CBTRN02C, read by CBACT04C.
--    50-byte COBOL record. Composite key: acct_id + type_cd + cat_cd.
-- ============================================================================
CREATE TABLE IF NOT EXISTS transaction_category_balances (
    trancat_acct_id           BIGINT        NOT NULL   COMMENT 'Account ID - PIC 9(11)',
    trancat_type_cd           STRING        NOT NULL   COMMENT 'Transaction type code - PIC X(02)',
    trancat_cd                INT           NOT NULL   COMMENT 'Transaction category code - PIC 9(04)',
    tran_cat_bal              DECIMAL(11,2) NOT NULL DEFAULT 0  COMMENT 'Category balance - PIC S9(09)V99',
    CONSTRAINT pk_tran_cat_bal PRIMARY KEY (trancat_acct_id, trancat_type_cd, trancat_cd)
)
USING DELTA
COMMENT 'Transaction category balance VSAM KSDS - Source: TCATBALF DD'
TBLPROPERTIES ('cobol.copybook' = 'CVTRA01Y', 'delta.feature.allowColumnDefaults' = 'supported');

-- ============================================================================
-- 7. DISCLOSURE_GROUPS  (CVTRA02Y / DIS-GROUP-RECORD)
--    Interest rate lookup VSAM KSDS.
--    Read by CBACT04C. 50-byte COBOL record.
--    Composite key: group_id + type_cd + cat_cd.
-- ============================================================================
CREATE TABLE IF NOT EXISTS disclosure_groups (
    dis_acct_group_id         STRING        NOT NULL   COMMENT 'Account group ID - PIC X(10)',
    dis_tran_type_cd          STRING        NOT NULL   COMMENT 'Transaction type code - PIC X(02)',
    dis_tran_cat_cd           INT           NOT NULL   COMMENT 'Transaction category code - PIC 9(04)',
    dis_int_rate              DECIMAL(6,2)  NOT NULL   COMMENT 'Interest rate (APR) - PIC S9(04)V99',
    CONSTRAINT pk_disclosure_groups PRIMARY KEY (dis_acct_group_id, dis_tran_type_cd, dis_tran_cat_cd)
)
USING DELTA
COMMENT 'Disclosure group / interest rate VSAM KSDS - Source: DISCGRP DD'
TBLPROPERTIES ('cobol.copybook' = 'CVTRA02Y');

-- ============================================================================
-- 8. TRANSACTION_TYPES  (CVTRA03Y / TRAN-TYPE-RECORD)
--    Transaction type reference VSAM KSDS.
--    Read by CBTRN03C. 60-byte COBOL record.
-- ============================================================================
CREATE TABLE IF NOT EXISTS transaction_types (
    tran_type                 STRING        NOT NULL   COMMENT 'Transaction type code - PIC X(02)',
    tran_type_desc            STRING                   COMMENT 'Description - PIC X(50)',
    CONSTRAINT pk_tran_types PRIMARY KEY (tran_type)
)
USING DELTA
COMMENT 'Transaction type reference VSAM KSDS - Source: TRANTYPE DD'
TBLPROPERTIES ('cobol.copybook' = 'CVTRA03Y');

-- ============================================================================
-- 9. TRANSACTION_CATEGORIES  (CVTRA04Y / TRAN-CAT-RECORD)
--    Transaction category reference VSAM KSDS.
--    Read by CBTRN03C. 60-byte COBOL record.
--    Composite key: type_cd + cat_cd.
-- ============================================================================
CREATE TABLE IF NOT EXISTS transaction_categories (
    tran_type_cd              STRING        NOT NULL   COMMENT 'Transaction type code - PIC X(02)',
    tran_cat_cd               INT           NOT NULL   COMMENT 'Category code - PIC 9(04)',
    tran_cat_type_desc        STRING                   COMMENT 'Description - PIC X(50)',
    CONSTRAINT pk_tran_categories PRIMARY KEY (tran_type_cd, tran_cat_cd)
)
USING DELTA
COMMENT 'Transaction category reference VSAM KSDS - Source: TRANCATG DD'
TBLPROPERTIES ('cobol.copybook' = 'CVTRA04Y');

-- ============================================================================
-- 10. DAILY_TRANSACTION_REJECTS  (Output from CBTRN02C)
--     430-byte COBOL record = 350-byte transaction + 80-byte trailer.
-- ============================================================================
CREATE TABLE IF NOT EXISTS daily_transaction_rejects (
    dalytran_id               STRING        NOT NULL   COMMENT 'Transaction ID',
    dalytran_type_cd          STRING                   COMMENT 'Transaction type code',
    dalytran_cat_cd           INT                      COMMENT 'Transaction category code',
    dalytran_source           STRING                   COMMENT 'Transaction source',
    dalytran_desc             STRING                   COMMENT 'Description',
    dalytran_amt              DECIMAL(11,2)            COMMENT 'Amount',
    dalytran_merchant_id      BIGINT                   COMMENT 'Merchant ID',
    dalytran_merchant_name    STRING                   COMMENT 'Merchant name',
    dalytran_merchant_city    STRING                   COMMENT 'Merchant city',
    dalytran_merchant_zip     STRING                   COMMENT 'Merchant zip',
    dalytran_card_num         STRING                   COMMENT 'Card number',
    dalytran_orig_ts          STRING                   COMMENT 'Original timestamp',
    dalytran_proc_ts          STRING                   COMMENT 'Processing timestamp',
    reject_reason_code        INT           NOT NULL   COMMENT 'Validation fail reason code - PIC 9(04)',
    reject_reason_desc        STRING        NOT NULL   COMMENT 'Validation fail description - PIC X(76)'
)
USING DELTA
COMMENT 'Rejected daily transactions - Output: DALYREJS DD'
TBLPROPERTIES ('cobol.program' = 'CBTRN02C');
