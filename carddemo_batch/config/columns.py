"""
CardDemo Batch - Column Name Constants

Single source of truth for all column names used in PySpark transformations
and pipeline MERGE statements. Organized by COBOL copybook / entity.

Naming convention: COL_<ENTITY>_<FIELD> for table columns,
                   COL_<NAME> for derived/computed columns.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Transaction (CVTRA05Y / CVTRA06Y copybooks — TRAN-RECORD / DALYTRAN-RECORD)
# ---------------------------------------------------------------------------
COL_TRAN_ID = "tran_id"
COL_TRAN_TYPE_CD = "tran_type_cd"
COL_TRAN_CAT_CD = "tran_cat_cd"
COL_TRAN_SOURCE = "tran_source"
COL_TRAN_DESC = "tran_desc"
COL_TRAN_AMT = "tran_amt"
COL_TRAN_MERCHANT_ID = "tran_merchant_id"
COL_TRAN_MERCHANT_NAME = "tran_merchant_name"
COL_TRAN_MERCHANT_CITY = "tran_merchant_city"
COL_TRAN_MERCHANT_ZIP = "tran_merchant_zip"
COL_TRAN_CARD_NUM = "tran_card_num"
COL_TRAN_ORIG_TS = "tran_orig_ts"
COL_TRAN_PROC_TS = "tran_proc_ts"

# ---------------------------------------------------------------------------
# Account (CVACT01Y copybook — ACCOUNT-RECORD)
# ---------------------------------------------------------------------------
COL_ACCT_ID = "acct_id"
COL_ACCT_CURR_BAL = "acct_curr_bal"
COL_ACCT_CREDIT_LIMIT = "acct_credit_limit"
COL_ACCT_EXPIRATION_DATE = "acct_expiration_date"
COL_ACCT_CURR_CYC_CREDIT = "acct_curr_cyc_credit"
COL_ACCT_CURR_CYC_DEBIT = "acct_curr_cyc_debit"
COL_ACCT_GROUP_ID = "acct_group_id"

# ---------------------------------------------------------------------------
# Card Cross-Reference (CVACT03Y copybook — CARD-XREF-RECORD)
# ---------------------------------------------------------------------------
COL_XREF_CARD_NUM = "xref_card_num"
COL_XREF_CUST_ID = "xref_cust_id"
COL_XREF_ACCT_ID = "xref_acct_id"

# ---------------------------------------------------------------------------
# Transaction Category Balance (CVTRA01Y copybook — TRAN-CAT-BAL-RECORD)
# ---------------------------------------------------------------------------
COL_TRANCAT_ACCT_ID = "trancat_acct_id"
COL_TRANCAT_TYPE_CD = "trancat_type_cd"
COL_TRANCAT_CD = "trancat_cd"
COL_TRAN_CAT_BAL = "tran_cat_bal"

# ---------------------------------------------------------------------------
# Disclosure Group (interest rate lookup)
# ---------------------------------------------------------------------------
COL_DIS_ACCT_GROUP_ID = "dis_acct_group_id"
COL_DIS_TRAN_TYPE_CD = "dis_tran_type_cd"
COL_DIS_TRAN_CAT_CD = "dis_tran_cat_cd"
COL_DIS_INT_RATE = "dis_int_rate"

# ---------------------------------------------------------------------------
# Customer (CUSTREC copybook)
# ---------------------------------------------------------------------------
COL_CUST_ID = "cust_id"
COL_CUST_FIRST_NAME = "cust_first_name"
COL_CUST_MIDDLE_NAME = "cust_middle_name"
COL_CUST_LAST_NAME = "cust_last_name"
COL_CUST_ADDR_LINE_1 = "cust_addr_line_1"
COL_CUST_ADDR_LINE_2 = "cust_addr_line_2"
COL_CUST_ADDR_LINE_3 = "cust_addr_line_3"
COL_CUST_ADDR_STATE_CD = "cust_addr_state_cd"
COL_CUST_ADDR_COUNTRY_CD = "cust_addr_country_cd"
COL_CUST_ADDR_ZIP = "cust_addr_zip"
COL_CUST_FICO_CREDIT_SCORE = "cust_fico_credit_score"

# ---------------------------------------------------------------------------
# Transaction by Card (TRNX — used by CBSTM03)
# ---------------------------------------------------------------------------
COL_TRNX_CARD_NUM = "trnx_card_num"
COL_TRNX_ID = "trnx_id"
COL_TRNX_DESC = "trnx_desc"
COL_TRNX_AMT = "trnx_amt"

# ---------------------------------------------------------------------------
# Transaction Type / Category Lookups
# ---------------------------------------------------------------------------
COL_TRAN_TYPE = "tran_type"
COL_TRAN_TYPE_DESC = "tran_type_desc"
COL_TRAN_CAT_TYPE_DESC = "tran_cat_type_desc"

# Join aliases to avoid ambiguity
COL_TT_TRAN_TYPE = "tt_tran_type"
COL_TC_TYPE_CD = "tc_type_cd"
COL_TC_CAT_CD = "tc_cat_cd"
COL_DEF_TYPE_CD = "def_type_cd"
COL_DEF_CAT_CD = "def_cat_cd"

# ---------------------------------------------------------------------------
# Validation (computed by CBTRN02C)
# ---------------------------------------------------------------------------
COL_VALIDATION_FAIL_REASON = "validation_fail_reason"
COL_VALIDATION_FAIL_REASON_DESC = "validation_fail_reason_desc"

# ---------------------------------------------------------------------------
# Derived / Computed Columns
# ---------------------------------------------------------------------------
# CBTRN02C balance deltas
COL_BALANCE_DELTA = "balance_delta"
COL_CURR_BAL_DELTA = "curr_bal_delta"
COL_CYC_CREDIT_DELTA = "cyc_credit_delta"
COL_CYC_DEBIT_DELTA = "cyc_debit_delta"

# CBACT04C interest
COL_SPECIFIC_INT_RATE = "specific_int_rate"
COL_DEFAULT_INT_RATE = "default_int_rate"
COL_MONTHLY_INTEREST = "monthly_interest"
COL_TOTAL_INTEREST = "total_interest"
COL_RESET_CYCLE_BALANCES = "reset_cycle_balances"

# CBSTM03 statement
COL_CUST_FULL_NAME = "cust_full_name"
COL_CUST_ADDR_FULL = "cust_addr_full"
COL_TOTAL_EXP = "total_exp"
COL_FICO_SCORE = "fico_score"

# CBTRN03C report
COL_REPORT_DATE = "report_date"
COL_ACCOUNT_ID = "account_id"
COL_TRAN_CAT_DESC = "tran_cat_desc"
COL_PAGE_NUM = "page_num"
COL_ACCOUNT_TOTAL = "account_total"
COL_PAGE_TOTAL = "page_total"
COL_GRAND_TOTAL = "grand_total"
