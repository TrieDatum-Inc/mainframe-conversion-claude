-- =============================================================================
-- CardDemo Batch Pipeline - Delta Table DDL
-- =============================================================================
-- Derived from COBOL copybooks:
--   CVTRA06Y.cpy  -> daily_transactions
--   CVTRA05Y.cpy  -> transactions
--   CVACT01Y.cpy  -> accounts
--   CVACT03Y.cpy  -> card_xref
--   CVTRA01Y.cpy  -> transaction_category_balance
--   CVTRA02Y.cpy  -> disclosure_groups
--   CVTRA03Y.cpy  -> transaction_types
--   CVTRA04Y.cpy  -> transaction_categories
--   CUSTREC.cpy   -> customers
--   COSTM01.cpy   -> transactions_by_card (TRNX-RECORD layout)
-- =============================================================================

-- ---------------------------------------------------------------------------
-- daily_transactions
-- Source: CVTRA06Y.cpy  DALYTRAN-RECORD  RECLN=350
-- Used by: CBTRN02C (input)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS carddemo.daily_transactions (
    tran_id               STRING        NOT NULL COMMENT 'DALYTRAN-ID PIC X(16)',
    tran_type_cd          STRING        NOT NULL COMMENT 'DALYTRAN-TYPE-CD PIC X(02)',
    tran_cat_cd           INT           NOT NULL COMMENT 'DALYTRAN-CAT-CD PIC 9(04)',
    tran_source           STRING        NOT NULL COMMENT 'DALYTRAN-SOURCE PIC X(10)',
    tran_desc             STRING        NOT NULL COMMENT 'DALYTRAN-DESC PIC X(100)',
    tran_amt              DECIMAL(11,2) NOT NULL COMMENT 'DALYTRAN-AMT PIC S9(09)V99',
    tran_merchant_id      BIGINT        NOT NULL COMMENT 'DALYTRAN-MERCHANT-ID PIC 9(09)',
    tran_merchant_name    STRING        NOT NULL COMMENT 'DALYTRAN-MERCHANT-NAME PIC X(50)',
    tran_merchant_city    STRING        NOT NULL COMMENT 'DALYTRAN-MERCHANT-CITY PIC X(50)',
    tran_merchant_zip     STRING        NOT NULL COMMENT 'DALYTRAN-MERCHANT-ZIP PIC X(10)',
    tran_card_num         STRING        NOT NULL COMMENT 'DALYTRAN-CARD-NUM PIC X(16)',
    tran_orig_ts          STRING        NOT NULL COMMENT 'DALYTRAN-ORIG-TS PIC X(26)',
    tran_proc_ts          STRING        NOT NULL COMMENT 'DALYTRAN-PROC-TS PIC X(26)'
)
USING DELTA
COMMENT 'Daily transaction input file - CVTRA06Y DALYTRAN-RECORD';

-- ---------------------------------------------------------------------------
-- transactions
-- Source: CVTRA05Y.cpy  TRAN-RECORD  RECLN=350
-- Used by: CBTRN02C (output/keyed), CBACT04C (output), CBTRN03C (input)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS carddemo.transactions (
    tran_id               STRING        NOT NULL COMMENT 'TRAN-ID PIC X(16)',
    tran_type_cd          STRING        NOT NULL COMMENT 'TRAN-TYPE-CD PIC X(02)',
    tran_cat_cd           INT           NOT NULL COMMENT 'TRAN-CAT-CD PIC 9(04)',
    tran_source           STRING        NOT NULL COMMENT 'TRAN-SOURCE PIC X(10)',
    tran_desc             STRING        NOT NULL COMMENT 'TRAN-DESC PIC X(100)',
    tran_amt              DECIMAL(11,2) NOT NULL COMMENT 'TRAN-AMT PIC S9(09)V99',
    tran_merchant_id      BIGINT        NOT NULL COMMENT 'TRAN-MERCHANT-ID PIC 9(09)',
    tran_merchant_name    STRING        NOT NULL COMMENT 'TRAN-MERCHANT-NAME PIC X(50)',
    tran_merchant_city    STRING        NOT NULL COMMENT 'TRAN-MERCHANT-CITY PIC X(50)',
    tran_merchant_zip     STRING        NOT NULL COMMENT 'TRAN-MERCHANT-ZIP PIC X(10)',
    tran_card_num         STRING        NOT NULL COMMENT 'TRAN-CARD-NUM PIC X(16)',
    tran_orig_ts          STRING        NOT NULL COMMENT 'TRAN-ORIG-TS PIC X(26)',
    tran_proc_ts          STRING        NOT NULL COMMENT 'TRAN-PROC-TS PIC X(26)'
)
USING DELTA
COMMENT 'Posted transaction master - CVTRA05Y TRAN-RECORD';

-- ---------------------------------------------------------------------------
-- accounts
-- Source: CVACT01Y.cpy  ACCOUNT-RECORD  RECLN=300
-- Used by: CBTRN02C (read/update), CBACT04C (read/update), CBSTM03A (read)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS carddemo.accounts (
    acct_id                STRING        NOT NULL COMMENT 'ACCT-ID PIC 9(11)',
    acct_active_status     STRING        NOT NULL COMMENT 'ACCT-ACTIVE-STATUS PIC X(01)',
    acct_curr_bal          DECIMAL(12,2) NOT NULL COMMENT 'ACCT-CURR-BAL PIC S9(10)V99',
    acct_credit_limit      DECIMAL(12,2) NOT NULL COMMENT 'ACCT-CREDIT-LIMIT PIC S9(10)V99',
    acct_cash_credit_limit DECIMAL(12,2) NOT NULL COMMENT 'ACCT-CASH-CREDIT-LIMIT PIC S9(10)V99',
    acct_open_date         STRING        NOT NULL COMMENT 'ACCT-OPEN-DATE PIC X(10)',
    acct_expiration_date   STRING        NOT NULL COMMENT 'ACCT-EXPIRAION-DATE PIC X(10)',
    acct_reissue_date      STRING        NOT NULL COMMENT 'ACCT-REISSUE-DATE PIC X(10)',
    acct_curr_cyc_credit   DECIMAL(12,2) NOT NULL COMMENT 'ACCT-CURR-CYC-CREDIT PIC S9(10)V99',
    acct_curr_cyc_debit    DECIMAL(12,2) NOT NULL COMMENT 'ACCT-CURR-CYC-DEBIT PIC S9(10)V99',
    acct_addr_zip          STRING        NOT NULL COMMENT 'ACCT-ADDR-ZIP PIC X(10)',
    acct_group_id          STRING        NOT NULL COMMENT 'ACCT-GROUP-ID PIC X(10)'
)
USING DELTA
COMMENT 'Account master - CVACT01Y ACCOUNT-RECORD'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');

-- ---------------------------------------------------------------------------
-- card_xref
-- Source: CVACT03Y.cpy  CARD-XREF-RECORD  RECLN=50
-- Used by: CBTRN02C (lookup), CBACT04C (lookup), CBTRN03C (lookup), CBSTM03A (drive)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS carddemo.card_xref (
    xref_card_num         STRING  NOT NULL COMMENT 'XREF-CARD-NUM PIC X(16)',
    xref_cust_id          BIGINT  NOT NULL COMMENT 'XREF-CUST-ID PIC 9(09)',
    xref_acct_id          BIGINT  NOT NULL COMMENT 'XREF-ACCT-ID PIC 9(11)'
)
USING DELTA
COMMENT 'Card-to-customer-to-account cross reference - CVACT03Y CARD-XREF-RECORD';

-- ---------------------------------------------------------------------------
-- transaction_category_balance
-- Source: CVTRA01Y.cpy  TRAN-CAT-BAL-RECORD  RECLN=50
-- Used by: CBTRN02C (read/write), CBACT04C (read sequentially)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS carddemo.transaction_category_balance (
    trancat_acct_id       BIGINT        NOT NULL COMMENT 'TRANCAT-ACCT-ID PIC 9(11)',
    trancat_type_cd       STRING        NOT NULL COMMENT 'TRANCAT-TYPE-CD PIC X(02)',
    trancat_cd            INT           NOT NULL COMMENT 'TRANCAT-CD PIC 9(04)',
    tran_cat_bal          DECIMAL(11,2) NOT NULL COMMENT 'TRAN-CAT-BAL PIC S9(09)V99'
)
USING DELTA
COMMENT 'Transaction category running balance - CVTRA01Y TRAN-CAT-BAL-RECORD'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');

-- ---------------------------------------------------------------------------
-- disclosure_groups
-- Source: CVTRA02Y.cpy  DIS-GROUP-RECORD  RECLN=50
-- Used by: CBACT04C (lookup interest rate)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS carddemo.disclosure_groups (
    dis_acct_group_id     STRING        NOT NULL COMMENT 'DIS-ACCT-GROUP-ID PIC X(10)',
    dis_tran_type_cd      STRING        NOT NULL COMMENT 'DIS-TRAN-TYPE-CD PIC X(02)',
    dis_tran_cat_cd       INT           NOT NULL COMMENT 'DIS-TRAN-CAT-CD PIC 9(04)',
    dis_int_rate          DECIMAL(6,2)  NOT NULL COMMENT 'DIS-INT-RATE PIC S9(04)V99'
)
USING DELTA
COMMENT 'Interest rate disclosure groups - CVTRA02Y DIS-GROUP-RECORD';

-- ---------------------------------------------------------------------------
-- transaction_types
-- Source: CVTRA03Y.cpy  TRAN-TYPE-RECORD  RECLN=60
-- Used by: CBTRN03C (lookup description)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS carddemo.transaction_types (
    tran_type             STRING  NOT NULL COMMENT 'TRAN-TYPE PIC X(02)',
    tran_type_desc        STRING  NOT NULL COMMENT 'TRAN-TYPE-DESC PIC X(50)'
)
USING DELTA
COMMENT 'Transaction type reference - CVTRA03Y TRAN-TYPE-RECORD';

-- ---------------------------------------------------------------------------
-- transaction_categories
-- Source: CVTRA04Y.cpy  TRAN-CAT-RECORD  RECLN=60
-- Used by: CBTRN03C (lookup description)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS carddemo.transaction_categories (
    tran_type_cd          STRING  NOT NULL COMMENT 'TRAN-TYPE-CD PIC X(02)',
    tran_cat_cd           INT     NOT NULL COMMENT 'TRAN-CAT-CD PIC 9(04)',
    tran_cat_type_desc    STRING  NOT NULL COMMENT 'TRAN-CAT-TYPE-DESC PIC X(50)'
)
USING DELTA
COMMENT 'Transaction category reference - CVTRA04Y TRAN-CAT-RECORD';

-- ---------------------------------------------------------------------------
-- customers
-- Source: CUSTREC.cpy  CUSTOMER-RECORD  RECLN=500
-- Used by: CBSTM03A (read for statement name/address)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS carddemo.customers (
    cust_id                BIGINT  NOT NULL COMMENT 'CUST-ID PIC 9(09)',
    cust_first_name        STRING  NOT NULL COMMENT 'CUST-FIRST-NAME PIC X(25)',
    cust_middle_name       STRING  NOT NULL COMMENT 'CUST-MIDDLE-NAME PIC X(25)',
    cust_last_name         STRING  NOT NULL COMMENT 'CUST-LAST-NAME PIC X(25)',
    cust_addr_line_1       STRING  NOT NULL COMMENT 'CUST-ADDR-LINE-1 PIC X(50)',
    cust_addr_line_2       STRING  NOT NULL COMMENT 'CUST-ADDR-LINE-2 PIC X(50)',
    cust_addr_line_3       STRING  NOT NULL COMMENT 'CUST-ADDR-LINE-3 PIC X(50)',
    cust_addr_state_cd     STRING  NOT NULL COMMENT 'CUST-ADDR-STATE-CD PIC X(02)',
    cust_addr_country_cd   STRING  NOT NULL COMMENT 'CUST-ADDR-COUNTRY-CD PIC X(03)',
    cust_addr_zip          STRING  NOT NULL COMMENT 'CUST-ADDR-ZIP PIC X(10)',
    cust_phone_num_1       STRING  NOT NULL COMMENT 'CUST-PHONE-NUM-1 PIC X(15)',
    cust_phone_num_2       STRING  NOT NULL COMMENT 'CUST-PHONE-NUM-2 PIC X(15)',
    cust_ssn               BIGINT  NOT NULL COMMENT 'CUST-SSN PIC 9(09)',
    cust_govt_issued_id    STRING  NOT NULL COMMENT 'CUST-GOVT-ISSUED-ID PIC X(20)',
    cust_dob_yyyymmdd      STRING  NOT NULL COMMENT 'CUST-DOB-YYYYMMDD PIC X(10)',
    cust_eft_account_id    STRING  NOT NULL COMMENT 'CUST-EFT-ACCOUNT-ID PIC X(10)',
    cust_pri_card_holder   STRING  NOT NULL COMMENT 'CUST-PRI-CARD-HOLDER-IND PIC X(01)',
    cust_fico_credit_score INT     NOT NULL COMMENT 'CUST-FICO-CREDIT-SCORE PIC 9(03)'
)
USING DELTA
COMMENT 'Customer master - CUSTREC.cpy CUSTOMER-RECORD';

-- ---------------------------------------------------------------------------
-- transactions_by_card
-- Source: COSTM01.cpy  TRNX-RECORD  RECLN=350
-- Used by: CBSTM03B (indexed file keyed on card+tran_id), CBSTM03A (read via B)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS carddemo.transactions_by_card (
    trnx_card_num         STRING        NOT NULL COMMENT 'TRNX-CARD-NUM PIC X(16) (part of TRNX-KEY)',
    trnx_id               STRING        NOT NULL COMMENT 'TRNX-ID PIC X(16) (part of TRNX-KEY)',
    trnx_type_cd          STRING        NOT NULL COMMENT 'TRNX-TYPE-CD PIC X(02)',
    trnx_cat_cd           INT           NOT NULL COMMENT 'TRNX-CAT-CD PIC 9(04)',
    trnx_source           STRING        NOT NULL COMMENT 'TRNX-SOURCE PIC X(10)',
    trnx_desc             STRING        NOT NULL COMMENT 'TRNX-DESC PIC X(100)',
    trnx_amt              DECIMAL(11,2) NOT NULL COMMENT 'TRNX-AMT PIC S9(09)V99',
    trnx_merchant_id      BIGINT        NOT NULL COMMENT 'TRNX-MERCHANT-ID PIC 9(09)',
    trnx_merchant_name    STRING        NOT NULL COMMENT 'TRNX-MERCHANT-NAME PIC X(50)',
    trnx_merchant_city    STRING        NOT NULL COMMENT 'TRNX-MERCHANT-CITY PIC X(50)',
    trnx_merchant_zip     STRING        NOT NULL COMMENT 'TRNX-MERCHANT-ZIP PIC X(10)',
    trnx_orig_ts          STRING        NOT NULL COMMENT 'TRNX-ORIG-TS PIC X(26)',
    trnx_proc_ts          STRING        NOT NULL COMMENT 'TRNX-PROC-TS PIC X(26)'
)
USING DELTA
COMMENT 'Transactions indexed by card number - COSTM01.cpy TRNX-RECORD';

-- ---------------------------------------------------------------------------
-- daily_reject_transactions
-- Source: Reject output of CBTRN02C (DALYREJS-FILE)
-- Contains original transaction record + validation trailer
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS carddemo.daily_reject_transactions (
    tran_id               STRING        NOT NULL COMMENT 'Original DALYTRAN-ID',
    tran_type_cd          STRING        NOT NULL COMMENT 'Original DALYTRAN-TYPE-CD',
    tran_cat_cd           INT           NOT NULL COMMENT 'Original DALYTRAN-CAT-CD',
    tran_source           STRING        NOT NULL COMMENT 'Original DALYTRAN-SOURCE',
    tran_desc             STRING        NOT NULL COMMENT 'Original DALYTRAN-DESC',
    tran_amt              DECIMAL(11,2) NOT NULL COMMENT 'Original DALYTRAN-AMT',
    tran_merchant_id      BIGINT        NOT NULL COMMENT 'Original DALYTRAN-MERCHANT-ID',
    tran_merchant_name    STRING        NOT NULL COMMENT 'Original DALYTRAN-MERCHANT-NAME',
    tran_merchant_city    STRING        NOT NULL COMMENT 'Original DALYTRAN-MERCHANT-CITY',
    tran_merchant_zip     STRING        NOT NULL COMMENT 'Original DALYTRAN-MERCHANT-ZIP',
    tran_card_num         STRING        NOT NULL COMMENT 'Original DALYTRAN-CARD-NUM',
    tran_orig_ts          STRING        NOT NULL COMMENT 'Original DALYTRAN-ORIG-TS',
    tran_proc_ts          STRING        NOT NULL COMMENT 'Original DALYTRAN-PROC-TS',
    validation_fail_reason     INT      NOT NULL COMMENT 'WS-VALIDATION-FAIL-REASON PIC 9(04)',
    validation_fail_reason_desc STRING  NOT NULL COMMENT 'WS-VALIDATION-FAIL-REASON-DESC PIC X(76)'
)
USING DELTA
COMMENT 'Daily rejected transactions with validation failure reason - DALYREJS-FILE';

-- ---------------------------------------------------------------------------
-- interest_transactions
-- Source: Output of CBACT04C (TRANSACT-FILE = new interest charge records)
-- These are synthetic transactions written for interest charges
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS carddemo.interest_transactions (
    tran_id               STRING        NOT NULL COMMENT 'TRAN-ID built from PARM-DATE + suffix',
    tran_type_cd          STRING        NOT NULL COMMENT 'TRAN-TYPE-CD hardcoded 01',
    tran_cat_cd           INT           NOT NULL COMMENT 'TRAN-CAT-CD hardcoded 05',
    tran_source           STRING        NOT NULL COMMENT 'TRAN-SOURCE hardcoded System',
    tran_desc             STRING        NOT NULL COMMENT 'TRAN-DESC Int. for a/c <acct_id>',
    tran_amt              DECIMAL(11,2) NOT NULL COMMENT 'TRAN-AMT = monthly interest amount',
    tran_merchant_id      BIGINT        NOT NULL COMMENT 'TRAN-MERCHANT-ID = 0',
    tran_merchant_name    STRING        NOT NULL COMMENT 'TRAN-MERCHANT-NAME spaces',
    tran_merchant_city    STRING        NOT NULL COMMENT 'TRAN-MERCHANT-CITY spaces',
    tran_merchant_zip     STRING        NOT NULL COMMENT 'TRAN-MERCHANT-ZIP spaces',
    tran_card_num         STRING        NOT NULL COMMENT 'TRAN-CARD-NUM from XREF lookup',
    tran_orig_ts          STRING        NOT NULL COMMENT 'TRAN-ORIG-TS current timestamp',
    tran_proc_ts          STRING        NOT NULL COMMENT 'TRAN-PROC-TS current timestamp'
)
USING DELTA
COMMENT 'Interest charge transactions generated by CBACT04C';

-- ---------------------------------------------------------------------------
-- transaction_report
-- Source: Output of CBTRN03C (CSV version of TRANREPT report)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS carddemo.transaction_report (
    report_date           STRING        NOT NULL COMMENT 'Processing date',
    tran_id               STRING        NOT NULL COMMENT 'TRAN-REPORT-TRANS-ID PIC X(16)',
    account_id            STRING        NOT NULL COMMENT 'TRAN-REPORT-ACCOUNT-ID PIC X(11)',
    tran_type_cd          STRING        NOT NULL COMMENT 'TRAN-REPORT-TYPE-CD PIC X(02)',
    tran_type_desc        STRING        NOT NULL COMMENT 'TRAN-REPORT-TYPE-DESC PIC X(15)',
    tran_cat_cd           INT           NOT NULL COMMENT 'TRAN-REPORT-CAT-CD PIC 9(04)',
    tran_cat_desc         STRING        NOT NULL COMMENT 'TRAN-REPORT-CAT-DESC PIC X(29)',
    tran_source           STRING        NOT NULL COMMENT 'TRAN-REPORT-SOURCE PIC X(10)',
    tran_amt              DECIMAL(11,2) NOT NULL COMMENT 'TRAN-REPORT-AMT',
    tran_proc_ts          STRING        NOT NULL COMMENT 'TRAN-PROC-TS PIC X(26)'
)
USING DELTA
COMMENT 'Transaction detail report - output of CBTRN03C';

-- ---------------------------------------------------------------------------
-- account_statements
-- Source: Output of CBSTM03A+CBSTM03B (CSV statement data)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS carddemo.account_statements (
    acct_id               STRING        NOT NULL COMMENT 'Account ID',
    cust_full_name        STRING        NOT NULL COMMENT 'Customer full name',
    cust_addr_line_1      STRING        NOT NULL COMMENT 'Address line 1',
    cust_addr_line_2      STRING        NOT NULL COMMENT 'Address line 2',
    cust_addr_full        STRING        NOT NULL COMMENT 'City/State/Country/ZIP combined',
    acct_curr_bal         DECIMAL(12,2) NOT NULL COMMENT 'Current balance',
    fico_score            INT           NOT NULL COMMENT 'FICO credit score',
    trnx_card_num         STRING        NOT NULL COMMENT 'Card number for this transaction',
    trnx_id               STRING        NOT NULL COMMENT 'Transaction ID',
    trnx_desc             STRING        NOT NULL COMMENT 'Transaction description',
    trnx_amt              DECIMAL(11,2) NOT NULL COMMENT 'Transaction amount',
    total_exp             DECIMAL(11,2) NOT NULL COMMENT 'Total expenditure for account'
)
USING DELTA
COMMENT 'Account statement detail rows - output of CBSTM03A/CBSTM03B pipeline';
