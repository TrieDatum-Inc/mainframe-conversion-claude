// ---------------------------------------------------------------------------
// Shared response types (mirrors app/schemas/common.py)
// ---------------------------------------------------------------------------

export interface PaginatedResponse<T> {
  items: T[];
  page: number;
  page_size: number;
  total_count: number;
  has_next_page: boolean;
}

export interface MessageResponse {
  message: string;
  message_type?: string; // 'info' | 'success' | 'error'
}

export interface ErrorResponse {
  error_message: string;
  field?: string;
}

// ---------------------------------------------------------------------------
// Auth (mirrors app/schemas/auth.py — COSGN00C)
// ---------------------------------------------------------------------------

export interface LoginRequest {
  user_id: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  user_id: string;
  user_type: string; // 'A' (admin) or 'U' (regular)
}

// ---------------------------------------------------------------------------
// Accounts (mirrors app/schemas/account.py — COACTVWC / COACTUPC)
// ---------------------------------------------------------------------------

export interface AccountView {
  acct_id: number;
  acct_active_status: string;
  acct_curr_bal: number;
  acct_credit_limit: number;
  acct_cash_credit_limit: number;
  acct_open_date: string;
  acct_expiration_date: string;
  acct_reissue_date: string;
  acct_curr_cyc_credit: number;
  acct_curr_cyc_debit: number;
  acct_addr_zip: string;
  acct_group_id: string;
  // Customer fields (joined)
  cust_id?: number;
  cust_first_name?: string;
  cust_middle_name?: string;
  cust_last_name?: string;
  cust_addr_line_1?: string;
  cust_addr_line_2?: string;
  cust_addr_line_3?: string;
  cust_addr_state_cd?: string;
  cust_addr_country_cd?: string;
  cust_addr_zip?: string;
  cust_phone_num_1?: string;
  cust_phone_num_2?: string;
  cust_ssn?: number;
  cust_govt_issued_id?: string;
  cust_dob_yyyymmdd?: string;
  cust_eft_account_id?: string;
  cust_pri_card_holder_ind?: string;
  cust_fico_credit_score?: number;
}

export interface AccountUpdate {
  acct_active_status?: string;
  acct_credit_limit?: number;
  acct_cash_credit_limit?: number;
  acct_open_date?: string;
  acct_expiration_date?: string;
  acct_reissue_date?: string;
  cust_first_name?: string;
  cust_middle_name?: string;
  cust_last_name?: string;
  cust_addr_line_1?: string;
  cust_addr_line_2?: string;
  cust_addr_line_3?: string;
  cust_addr_state_cd?: string;
  cust_addr_country_cd?: string;
  cust_addr_zip?: string;
  cust_phone_num_1?: string;
  cust_phone_num_2?: string;
  cust_ssn?: number;
  cust_govt_issued_id?: string;
  cust_dob_yyyymmdd?: string;
  cust_eft_account_id?: string;
  cust_pri_card_holder_ind?: string;
  cust_fico_credit_score?: number;
}

// ---------------------------------------------------------------------------
// Cards (mirrors app/schemas/card.py — COCRDLIC / COCRDSLC / COCRDUPC)
// ---------------------------------------------------------------------------

export interface CardListItem {
  card_num: string;
  card_acct_id: number;
  card_active_status: string;
  card_expiration_date: string;
}

export interface CardDetail {
  card_num: string;
  card_acct_id: number;
  card_cvv_cd: number;
  card_embossed_name: string;
  card_expiration_date: string;
  card_active_status: string;
}

export interface CardUpdate {
  card_embossed_name?: string;
  card_active_status?: string;
  card_expiration_date?: string;
}

// ---------------------------------------------------------------------------
// Transactions (mirrors app/schemas/transaction.py — COTRN00C-02C)
// ---------------------------------------------------------------------------

export interface TransactionListItem {
  tran_id: string;
  tran_card_num: string;
  tran_amt: number;
  tran_orig_ts: string;
  tran_type_cd: string;
}

export interface TransactionDetail {
  tran_id: string;
  tran_type_cd: string;
  tran_cat_cd: number;
  tran_source: string;
  tran_desc: string;
  tran_amt: number;
  tran_merchant_id: number;
  tran_merchant_name: string;
  tran_merchant_city: string;
  tran_merchant_zip: string;
  tran_card_num: string;
  tran_orig_ts: string;
  tran_proc_ts: string;
}

export interface TransactionCreate {
  card_num?: string;
  acct_id?: number;
  tran_type_cd: string;
  tran_cat_cd: number;
  tran_source: string;
  tran_desc: string;
  tran_amt: number;
  tran_merchant_id: number;
  tran_merchant_name: string;
  tran_merchant_city: string;
  tran_merchant_zip: string;
  confirm: string; // 'N' preview, 'Y' submit
}

// ---------------------------------------------------------------------------
// Users (mirrors app/schemas/user.py — COUSR00C-03C)
// ---------------------------------------------------------------------------

export interface UserListItem {
  usr_id: string;
  usr_fname: string;
  usr_lname: string;
  usr_type: string;
}

export interface UserRead {
  usr_id: string;
  usr_fname: string;
  usr_lname: string;
  usr_type: string;
}

export interface UserCreate {
  usr_id: string;
  usr_fname: string;
  usr_lname: string;
  usr_pwd: string;
  usr_type: string;
}

export interface UserUpdate {
  usr_fname?: string;
  usr_lname?: string;
  usr_pwd?: string;
  usr_type?: string;
}

// ---------------------------------------------------------------------------
// Authorizations (mirrors app/schemas/authorization.py — COPAUS0C-2C, COPAUA0C)
// ---------------------------------------------------------------------------

export interface AuthSummaryItem {
  pa_acct_id: number;
  pa_cust_id: number;
  pa_auth_status: string;
  pa_credit_limit: number;
  pa_cash_limit: number;
  pa_credit_balance: number;
  pa_cash_balance: number;
  pa_account_status_1?: string;
  pa_account_status_2?: string;
  pa_account_status_3?: string;
  pa_account_status_4?: string;
  pa_account_status_5?: string;
  pa_approved_auth_cnt: number;
  pa_declined_auth_cnt: number;
  pa_approved_auth_amt?: number;
  pa_declined_auth_amt?: number;
}

export interface AuthDetailRecord {
  id: number;
  pa_acct_id: number;
  pa_auth_date: string;
  pa_auth_time: string;
  pa_card_num: string;
  pa_auth_type: string;
  pa_card_expiry_date: string;
  pa_message_type: string;
  pa_message_source: string;
  pa_auth_id_code: string;
  pa_auth_resp_code: string;
  pa_auth_resp_reason: string;
  pa_processing_code: string;
  pa_transaction_amt: number;
  pa_approved_amt: number;
  pa_merchant_category_code: string;
  pa_acqr_country_code: string;
  pa_pos_entry_mode: string;
  pa_merchant_id: string;
  pa_merchant_name: string;
  pa_merchant_city: string;
  pa_merchant_state: string;
  pa_merchant_zip: string;
  pa_transaction_id: string;
  pa_match_status: string;
  pa_auth_fraud: string;
  pa_fraud_rpt_date: string;
  auth_status: string;
}

export interface AuthDetailResponse {
  summary: AuthSummaryItem;
  details: AuthDetailRecord[];
}

export interface AuthDecisionRequest {
  card_num: string;
  auth_type: string;
  card_expiry_date: string;
  transaction_amt: number;
  merchant_category_code?: string;
  acqr_country_code?: string;
  pos_entry_mode?: number;
  merchant_id?: string;
  merchant_name?: string;
  merchant_city?: string;
  merchant_state?: string;
  merchant_zip?: string;
}

export interface AuthDecisionResponse {
  card_num: string;
  transaction_id: string;
  auth_id_code: string;
  auth_resp_code: string;
  auth_resp_reason: string;
  approved_amt: number;
}

export interface MarkFraudRequest {
  card_num: string;
  auth_ts: string;
  acct_id: number;
  cust_id: number;
  action: string; // 'F' or 'R'
}

export interface MarkFraudResponse {
  message: string;
  status: string;
}

// ---------------------------------------------------------------------------
// Bill Payment (mirrors app/schemas/bill_payment.py — COBIL00C)
// ---------------------------------------------------------------------------

export interface BillPaymentRequest {
  acct_id: number;
  confirm: string; // 'N' preview, 'Y' submit
}

export interface BillPaymentResponse {
  message: string;
  tran_id?: string;
  previous_balance?: number;
  new_balance?: number;
  acct_id?: number;
}

// ---------------------------------------------------------------------------
// Reports (mirrors app/schemas/report.py — CORPT00C)
// ---------------------------------------------------------------------------

export interface ReportRequest {
  report_type: string; // 'monthly' | 'yearly' | 'custom'
  start_month?: number;
  start_day?: number;
  start_year?: number;
  end_month?: number;
  end_day?: number;
  end_year?: number;
  confirm: string;
}

export interface ReportResponse {
  message: string;
  report_type?: string;
  start_date?: { month?: number; day?: number; year?: number };
  end_date?: { month?: number; day?: number; year?: number };
}

// ---------------------------------------------------------------------------
// Transaction Types (mirrors app/schemas/transaction_type.py — COTRTLIC / COTRTUPC)
// ---------------------------------------------------------------------------

export interface TransactionTypeItem {
  tran_type: string;
  tran_type_desc: string;
}

export interface TransactionTypeCreate {
  tran_type: string;
  tran_type_desc: string;
}

export interface TransactionTypeUpdate {
  tran_type_desc: string;
}
