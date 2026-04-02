// ============================================================
// CardDemo API Type Definitions
// Aligned with FastAPI backend Pydantic schemas
// ============================================================

// ---- Auth ----

export interface LoginRequest {
  user_id: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  user_type: 'A' | 'U';
  first_name: string;
  last_name: string;
}

export interface AuthUser {
  user_id: string;
  user_type: 'A' | 'U';
  first_name: string;
  last_name: string;
  token: string;
}

// ---- Accounts (AccountWithCustomerView) ----

export interface AccountView {
  acct_id: number;
  active_status: string;
  curr_bal: number;
  credit_limit: number;
  cash_credit_limit: number;
  open_date: string | null;
  expiration_date: string | null;
  reissue_date: string | null;
  curr_cycle_credit: number;
  curr_cycle_debit: number;
  addr_zip: string | null;
  group_id: string | null;
}

export interface CustomerView {
  cust_id: number;
  first_name: string;
  middle_name: string | null;
  last_name: string;
  addr_line1: string | null;
  addr_line2: string | null;
  addr_line3: string | null;
  addr_state_cd: string | null;
  addr_country_cd: string | null;
  addr_zip: string | null;
  phone_num1: string | null;
  phone_num2: string | null;
  ssn: number;
  govt_issued_id: string | null;
  dob: string | null;
  eft_account_id: string | null;
  pri_card_holder: string | null;
  fico_score: number | null;
}

export interface AccountWithCustomer {
  account: AccountView;
  customer: CustomerView;
  card_num: number | null;
}

export interface AccountUpdateRequest {
  account: {
    active_status?: string;
    credit_limit?: number;
    cash_credit_limit?: number;
    open_date?: string;
    expiration_date?: string;
    reissue_date?: string;
    group_id?: string;
    curr_cycle_credit?: number;
    curr_cycle_debit?: number;
    addr_zip?: string;
  };
  customer: {
    first_name: string;
    last_name: string;
    middle_name?: string;
    addr_line1?: string;
    addr_line2?: string;
    addr_line3?: string;
    addr_state_cd?: string;
    addr_country_cd?: string;
    addr_zip?: string;
    phone_num1?: string;
    phone_num2?: string;
    ssn: number;
    govt_issued_id?: string;
    dob?: string;
    eft_account_id?: string;
    pri_card_holder?: string;
    fico_score?: number;
  };
}

// ---- Cards (CardListResponse / CardView) ----

export interface Card {
  card_num: string;
  acct_id: number;
  embossed_name: string | null;
  expiration_date: string | null;
  active_status: string;
}

export interface CardListResponse {
  items: Card[];
  page: number;
  has_next_page: boolean;
  first_card_num: string | null;
  last_card_num: string | null;
  account_filter: number | null;
}

export interface CardUpdateRequest {
  active_status?: string;
  embossed_name?: string;
  expiration_date?: string;
}

export interface CardCreateRequest {
  card_num: string;
  acct_id: number;
  cvv_cd: number;
  embossed_name?: string;
  expiration_date?: string;
  active_status?: string;
  cust_id: number;
}

// ---- Transactions (TransactionListResponse / TransactionView) ----

export interface TransactionListItem {
  tran_id: string;
  tran_type_cd: string;
  tran_cat_cd: number;
  tran_amt: number;
  card_num: string;
  orig_ts: string | null;
}

export interface TransactionView {
  tran_id: string;
  tran_type_cd: string;
  tran_cat_cd: number;
  tran_source: string | null;
  tran_desc: string | null;
  tran_amt: number;
  merchant_id: number | null;
  merchant_name: string | null;
  merchant_city: string | null;
  merchant_zip: string | null;
  card_num: string;
  orig_ts: string | null;
  proc_ts: string | null;
}

export interface TransactionListResponse {
  items: TransactionListItem[];
  page: number;
  has_next_page: boolean;
  first_tran_id: string | null;
  last_tran_id: string | null;
  start_tran_id_filter: string | null;
}

export interface TransactionCreateRequest {
  tran_type_cd: string;
  tran_cat_cd: number;
  tran_amt: number;
  merchant_id?: number;
  merchant_name?: string;
  merchant_city?: string;
  merchant_zip?: string;
  tran_source?: string;
  tran_desc?: string;
  card_num?: string;
  acct_id?: number;
}

// ---- Billing ----

export interface BillPaymentRequest {
  account_id: number;
}

export interface BillPaymentResponse {
  account_id: number;
  previous_balance: number;
  payment_amount: number;
  new_balance: number;
  transaction_id: string;
  message: string;
}

// ---- Reports ----

export interface ReportGenerateRequest {
  start_date?: string;
  end_date?: string;
  account_id?: number;
  card_num?: string;
  confirm?: boolean;
}

export interface ReportGenerateResponse {
  report_id: string;
  status: string;
  message: string;
  total_transactions: number;
  total_amount: number;
}

// ---- Users (UserListResponse / UserView) ----

export interface User {
  usr_id: string;
  first_name: string;
  last_name: string;
  usr_type: 'A' | 'U';
}

export interface UserListResponse {
  items: User[];
  page: number;
  has_next_page: boolean;
  first_usr_id: string | null;
  last_usr_id: string | null;
}

export interface UserCreateRequest {
  usr_id: string;
  password: string;
  first_name: string;
  last_name: string;
  usr_type: 'A' | 'U';
}

export interface UserUpdateRequest {
  password?: string;
  first_name: string;
  last_name: string;
  usr_type: 'A' | 'U';
}

// ---- Transaction Types (TransactionTypeListResponse) ----

export interface TransactionType {
  tran_type_cd: string;
  tran_type_desc: string;
}

export interface TransactionTypeListResponse {
  items: TransactionType[];
  page: number;
  has_next_page: boolean;
  first_type_cd: string | null;
  last_type_cd: string | null;
  type_cd_filter: string | null;
  desc_filter: string | null;
}

export interface TransactionTypeCreateRequest {
  tran_type_cd: string;
  tran_type_desc: string;
}

export interface TransactionTypeUpdateRequest {
  tran_type_desc: string;
}

// ---- Authorizations (AuthSummaryListResponse / AuthDetailView) ----

export interface AuthorizationSummary {
  acct_id: number;
  cust_id: number;
  auth_status: string | null;
  credit_limit: number;
  cash_limit: number;
  curr_bal: number;
  cash_bal: number;
  approved_count: number;
  approved_amt: number;
  declined_count: number;
  declined_amt: number;
}

export interface AuthSummaryListResponse {
  items: AuthorizationSummary[];
  account_id_filter: number | null;
  total_count: number;
}

export interface AuthorizationDetail {
  auth_date: string;
  auth_time: string;
  acct_id: number;
  card_num: string | null;
  tran_id: string | null;
  auth_id_code: string | null;
  response_code: string | null;
  response_reason: string | null;
  approved_amt: number;
  auth_type: string | null;
  match_status: string | null;
  fraud_flag: string;
}

export interface FraudFlagRequest {
  acct_id: number;
  auth_date: string;
  auth_time: string;
  fraud_reason?: string;
  fraud_status?: string;
}

export interface AuthProcessRequest {
  card_num: string;
  requested_amt: number;
  merchant_id?: number;
  merchant_name?: string;
}

export interface AuthProcessResponse {
  response_code: string;
  approved: boolean;
  message: string;
}

// ---- API Error ----

export interface ApiError {
  error_code: string;
  message: string;
  field?: string;
}
