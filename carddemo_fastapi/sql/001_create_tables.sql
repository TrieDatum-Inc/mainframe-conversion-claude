-- ============================================================================
-- CardDemo FastAPI Migration - Table Creation Script
-- Source: AWS Mainframe Modernization CardDemo COBOL copybooks and DDL files
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. customers (CUSTREC.cpy - 500 bytes)
-- ============================================================================
CREATE TABLE IF NOT EXISTS customers (
    cust_id                 INTEGER         PRIMARY KEY,
    cust_first_name         VARCHAR(25)     NOT NULL,
    cust_middle_name        VARCHAR(25),
    cust_last_name          VARCHAR(25)     NOT NULL,
    cust_addr_line_1        VARCHAR(50),
    cust_addr_line_2        VARCHAR(50),
    cust_addr_line_3        VARCHAR(50),
    cust_addr_state_cd      CHAR(2),
    cust_addr_country_cd    CHAR(3),
    cust_addr_zip           VARCHAR(10),
    cust_phone_num_1        VARCHAR(15),
    cust_phone_num_2        VARCHAR(15),
    cust_ssn                INTEGER,
    cust_govt_issued_id     VARCHAR(20),
    cust_dob_yyyymmdd       VARCHAR(10),
    cust_eft_account_id     VARCHAR(10),
    cust_pri_card_holder_ind CHAR(1),
    cust_fico_credit_score  SMALLINT
);

-- ============================================================================
-- 2. accounts (CVACT01Y.cpy - 300 bytes)
-- ============================================================================
CREATE TABLE IF NOT EXISTS accounts (
    acct_id                 BIGINT          PRIMARY KEY,
    acct_active_status      CHAR(1)         NOT NULL DEFAULT 'Y',
    acct_curr_bal           NUMERIC(12,2)   DEFAULT 0,
    acct_credit_limit       NUMERIC(12,2)   DEFAULT 0,
    acct_cash_credit_limit  NUMERIC(12,2)   DEFAULT 0,
    acct_open_date          VARCHAR(10),
    acct_expiration_date    VARCHAR(10),
    acct_reissue_date       VARCHAR(10),
    acct_curr_cyc_credit    NUMERIC(12,2)   DEFAULT 0,
    acct_curr_cyc_debit     NUMERIC(12,2)   DEFAULT 0,
    acct_addr_zip           VARCHAR(10),
    acct_group_id           VARCHAR(10)
);

-- ============================================================================
-- 3. cards (CVACT02Y.cpy - 150 bytes)
-- ============================================================================
CREATE TABLE IF NOT EXISTS cards (
    card_num                CHAR(16)        NOT NULL,
    card_acct_id            BIGINT          NOT NULL,
    card_cvv_cd             SMALLINT        NOT NULL,
    card_embossed_name      VARCHAR(50),
    card_expiration_date    VARCHAR(10),
    card_active_status      CHAR(1)         DEFAULT 'Y',
    PRIMARY KEY (card_num, card_acct_id),
    CONSTRAINT fk_cards_acct
        FOREIGN KEY (card_acct_id)
        REFERENCES accounts (acct_id)
);

-- ============================================================================
-- 4. card_xref (CVACT03Y.cpy - 50 bytes)
-- ============================================================================
CREATE TABLE IF NOT EXISTS card_xref (
    xref_card_num           CHAR(16)        PRIMARY KEY,
    xref_cust_id            INTEGER         NOT NULL,
    xref_acct_id            BIGINT          NOT NULL,
    CONSTRAINT fk_xref_cust
        FOREIGN KEY (xref_cust_id)
        REFERENCES customers (cust_id),
    CONSTRAINT fk_xref_acct
        FOREIGN KEY (xref_acct_id)
        REFERENCES accounts (acct_id)
);

-- ============================================================================
-- 5. transactions (CVTRA05Y.cpy - 350 bytes)
-- ============================================================================
CREATE TABLE IF NOT EXISTS transactions (
    tran_id                 CHAR(16)        PRIMARY KEY,
    tran_type_cd            CHAR(2),
    tran_cat_cd             INTEGER,
    tran_source             VARCHAR(10),
    tran_desc               VARCHAR(100),
    tran_amt                NUMERIC(11,2),
    tran_merchant_id        INTEGER,
    tran_merchant_name      VARCHAR(50),
    tran_merchant_city      VARCHAR(50),
    tran_merchant_zip       VARCHAR(10),
    tran_card_num           CHAR(16),
    tran_orig_ts            VARCHAR(26),
    tran_proc_ts            VARCHAR(26)
);

-- ============================================================================
-- 6. users (CSUSR01Y.cpy - 80 bytes)
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    usr_id                  VARCHAR(8)      PRIMARY KEY,
    usr_fname               VARCHAR(20)     NOT NULL,
    usr_lname               VARCHAR(20)     NOT NULL,
    usr_pwd                 VARCHAR(8)      NOT NULL,
    usr_type                CHAR(1)         NOT NULL
);

-- ============================================================================
-- 7. tran_cat_balance (CVTRA01Y.cpy)
-- ============================================================================
CREATE TABLE IF NOT EXISTS tran_cat_balance (
    trancat_acct_id         BIGINT,
    trancat_type_cd         CHAR(2),
    trancat_cd              INTEGER,
    tran_cat_bal            NUMERIC(11,2)   DEFAULT 0,
    PRIMARY KEY (trancat_acct_id, trancat_type_cd, trancat_cd)
);

-- ============================================================================
-- 8. disclosure_groups (CVTRA02Y.cpy)
-- ============================================================================
CREATE TABLE IF NOT EXISTS disclosure_groups (
    dis_acct_group_id       VARCHAR(10),
    dis_tran_type_cd        CHAR(2),
    dis_tran_cat_cd         INTEGER,
    dis_int_rate            NUMERIC(6,2),
    PRIMARY KEY (dis_acct_group_id, dis_tran_type_cd, dis_tran_cat_cd)
);

-- ============================================================================
-- 9. transaction_types (CVTRA03Y.cpy / TRNTYPE.ddl)
-- ============================================================================
CREATE TABLE IF NOT EXISTS transaction_types (
    tran_type               CHAR(2)         PRIMARY KEY,
    tran_type_desc          VARCHAR(50)     NOT NULL
);

-- ============================================================================
-- 10. transaction_categories (CVTRA04Y.cpy / TRNTYCAT.ddl)
-- ============================================================================
CREATE TABLE IF NOT EXISTS transaction_categories (
    tran_type_cd            CHAR(2)         NOT NULL,
    tran_cat_cd             INTEGER         NOT NULL,
    tran_cat_type_desc      VARCHAR(50)     NOT NULL,
    PRIMARY KEY (tran_type_cd, tran_cat_cd),
    CONSTRAINT fk_trancat_type
        FOREIGN KEY (tran_type_cd)
        REFERENCES transaction_types (tran_type)
        ON DELETE RESTRICT
);

-- ============================================================================
-- 11. auth_fraud (AUTHFRDS.ddl)
-- ============================================================================
CREATE TABLE IF NOT EXISTS auth_fraud (
    card_num                CHAR(16),
    auth_ts                 TIMESTAMP,
    auth_type               CHAR(4),
    card_expiry_date        CHAR(4),
    message_type            CHAR(6),
    message_source          CHAR(6),
    auth_id_code            CHAR(6),
    auth_resp_code          CHAR(2),
    auth_resp_reason        CHAR(4),
    processing_code         CHAR(6),
    transaction_amt         NUMERIC(12,2),
    approved_amt            NUMERIC(12,2),
    merchant_category_code  CHAR(4),
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

-- ============================================================================
-- 12. pending_auth_summary (CIPAUSMY.cpy)
-- ============================================================================
CREATE TABLE IF NOT EXISTS pending_auth_summary (
    pa_acct_id              BIGINT          PRIMARY KEY,
    pa_cust_id              INTEGER         NOT NULL,
    pa_auth_status          CHAR(1),
    pa_account_status_1     CHAR(2),
    pa_account_status_2     CHAR(2),
    pa_account_status_3     CHAR(2),
    pa_account_status_4     CHAR(2),
    pa_account_status_5     CHAR(2),
    pa_credit_limit         NUMERIC(11,2),
    pa_cash_limit           NUMERIC(11,2),
    pa_credit_balance       NUMERIC(11,2),
    pa_cash_balance         NUMERIC(11,2),
    pa_approved_auth_cnt    INTEGER,
    pa_declined_auth_cnt    INTEGER,
    pa_approved_auth_amt    NUMERIC(11,2),
    pa_declined_auth_amt    NUMERIC(11,2)
);

-- ============================================================================
-- 13. pending_auth_details (CIPAUDTY.cpy)
-- ============================================================================
CREATE TABLE IF NOT EXISTS pending_auth_details (
    id                      SERIAL          PRIMARY KEY,
    pa_acct_id              BIGINT,
    pa_auth_date            VARCHAR(6),
    pa_auth_time            VARCHAR(6),
    pa_card_num             CHAR(16),
    pa_auth_type            CHAR(4),
    pa_card_expiry_date     CHAR(4),
    pa_message_type         CHAR(6),
    pa_message_source       CHAR(6),
    pa_auth_id_code         CHAR(6),
    pa_auth_resp_code       CHAR(2),
    pa_auth_resp_reason     CHAR(4),
    pa_processing_code      INTEGER,
    pa_transaction_amt      NUMERIC(12,2),
    pa_approved_amt         NUMERIC(12,2),
    pa_merchant_category_code CHAR(4),
    pa_acqr_country_code    CHAR(3),
    pa_pos_entry_mode       SMALLINT,
    pa_merchant_id          CHAR(15),
    pa_merchant_name        VARCHAR(22),
    pa_merchant_city        CHAR(13),
    pa_merchant_state       CHAR(2),
    pa_merchant_zip         CHAR(9),
    pa_transaction_id       CHAR(15),
    pa_match_status         CHAR(1),
    pa_auth_fraud           CHAR(1),
    pa_fraud_rpt_date       VARCHAR(8),
    CONSTRAINT fk_pa_detail_summary
        FOREIGN KEY (pa_acct_id)
        REFERENCES pending_auth_summary (pa_acct_id)
);

COMMIT;
