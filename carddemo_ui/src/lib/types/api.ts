/**
 * Core API types derived from FastAPI schemas.
 * Maps to Pydantic models in fast_api/app/schemas/
 */

// ─── Auth ──────────────────────────────────────────────────────────────────

export interface LoginRequest {
  user_id: string; // SEC-USR-ID PIC X(08) — max 8 chars, uppercased
  password: string; // SEC-USR-PWD PIC X(08) — max 8 chars
}

export interface TokenResponse {
  access_token: string;
  token_type: 'bearer';
  user_id: string; // CDEMO-USER-ID
  user_type: 'A' | 'U'; // 'A'=admin, 'U'=regular
  first_name: string | null;
  last_name: string | null;
}

export interface AuthUser {
  user_id: string;
  user_type: 'A' | 'U';
  first_name: string | null;
  last_name: string | null;
  is_admin: boolean;
}

// ─── Accounts ───────────────────────────────────────────────────────────────

export interface AccountResponse {
  acct_id: number; // ACCT-ID PIC 9(11)
  active_status: 'Y' | 'N' | null; // ACCT-ACTIVE-STATUS
  curr_bal: string | null; // Decimal as string
  credit_limit: string | null;
  cash_credit_limit: string | null;
  open_date: string | null; // YYYY-MM-DD
  expiration_date: string | null;
  reissue_date: string | null;
  curr_cycle_credit: string | null;
  curr_cycle_debit: string | null;
  addr_zip: string | null;
  group_id: string | null;
}

export interface AccountDetailResponse extends AccountResponse {
  customer_id: number | null;
  customer_name: string | null;
}

export interface AccountUpdateRequest {
  active_status?: 'Y' | 'N';
  curr_bal?: string;
  credit_limit?: string;
  cash_credit_limit?: string;
  open_date?: string;
  expiration_date?: string;
  reissue_date?: string;
  curr_cycle_credit?: string;
  curr_cycle_debit?: string;
  addr_zip?: string;
  group_id?: string;
}

export interface AccountPaymentRequest {
  payment_amount: string; // Decimal as string
  description?: string;
}

// ─── Cards ──────────────────────────────────────────────────────────────────

export interface CardResponse {
  card_num: string; // CARD-NUM PIC X(16)
  acct_id: number | null;
  cvv_cd: number | null;
  embossed_name: string | null;
  expiration_date: string | null;
  active_status: 'Y' | 'N' | null;
}

export interface CardListResponse {
  items: CardResponse[];
  total: number;
  next_cursor: string | null;
  prev_cursor: string | null;
}

export interface CardUpdateRequest {
  embossed_name?: string;
  active_status?: 'Y' | 'N';
}

// ─── Transactions ────────────────────────────────────────────────────────────

export interface TransactionResponse {
  tran_id: string; // TRAN-ID PIC X(16)
  acct_id: number | null;
  type_cd: string | null; // TRAN-TYPE-CD PIC X(02)
  cat_cd: number | null;
  source: string | null;
  description: string | null;
  amount: string; // Decimal
  merchant_id: number | null;
  merchant_name: string | null;
  merchant_city: string | null;
  merchant_zip: string | null;
  card_num: string | null;
  orig_ts: string | null;
  proc_ts: string | null;
}

export interface TransactionListResponse {
  items: TransactionResponse[];
  total: number;
  next_cursor: string | null;
  prev_cursor: string | null;
}

export interface TransactionCreateRequest {
  amount: string; // Decimal — must not be zero
  card_num: string; // 16 chars exact
  type_cd: string; // 1-2 chars
  cat_cd?: number;
  source?: string;
  description?: string;
  merchant_id?: number;
  merchant_name?: string;
  merchant_city?: string;
  merchant_zip?: string;
  orig_ts?: string;
  proc_ts?: string;
}

export interface BillPaymentRequest {
  account_id: number;
  payment_amount: string; // Decimal — positive
  description?: string;
}

// ─── Users ───────────────────────────────────────────────────────────────────

export interface UserResponse {
  user_id: string; // SEC-USR-ID PIC X(08)
  first_name: string | null;
  last_name: string | null;
  user_type: 'A' | 'U' | null;
  is_admin: boolean;
}

export interface UserListResponse {
  items: UserResponse[];
  total: number;
  next_cursor: string | null;
  prev_cursor: string | null;
}

export interface UserCreateRequest {
  user_id: string; // max 8 chars, uppercased
  password: string; // max 8 chars
  first_name?: string;
  last_name?: string;
  user_type?: 'A' | 'U';
}

export interface UserUpdateRequest {
  first_name?: string;
  last_name?: string;
  user_type?: 'A' | 'U';
  password?: string; // optional new password
}

// ─── Admin ────────────────────────────────────────────────────────────────────

export interface AdminMenuItem {
  option_number: number;
  name: string;
  display_text: string;
  program_name: string;
  transaction_id: string;
  rest_endpoint: string;
  is_installed: boolean;
}

export interface AdminMenuResponse {
  transaction_id: string;
  program_name: string;
  menu_title: string;
  option_count: number;
  menu_items: AdminMenuItem[];
}

// ─── Reports ─────────────────────────────────────────────────────────────────

export type ReportType = 'monthly' | 'yearly' | 'custom';
export type ReportStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface ReportSubmitRequest {
  report_type: ReportType;
  start_date?: string; // YYYY-MM-DD — required for 'custom'
  end_date?: string; // YYYY-MM-DD — required for 'custom'
}

export interface ReportJob {
  job_id: string;
  report_type: ReportType;
  start_date: string;
  end_date: string;
  status: ReportStatus;
  submitted_at: string;
  submitted_by: string;
  message: string;
}

// ─── Authorizations ──────────────────────────────────────────────────────────

export type AuthDecision = '00' | '05'; // '00'=approved, '05'=declined
export type FraudAction = 'F' | 'R'; // 'F'=confirmed, 'R'=removed

export interface AuthorizationRequest {
  auth_date: string; // YYMMDD
  auth_time: string; // HHMMSS
  card_num: string; // 16 chars
  auth_type: string; // max 4 chars
  card_expiry_date: string; // MMYY
  message_type?: string;
  message_source?: string;
  processing_code?: number;
  transaction_amt: string; // Decimal
  merchant_category_code?: string;
  acqr_country_code?: string;
  pos_entry_mode?: number;
  merchant_id?: string;
  merchant_name?: string;
  merchant_city?: string;
  merchant_state?: string;
  merchant_zip?: string;
  transaction_id: string; // max 15 chars
}

export interface AuthorizationResponse {
  card_num: string;
  transaction_id: string;
  auth_id_code: string;
  auth_resp_code: AuthDecision;
  auth_resp_reason: string;
  approved_amt: string;
  is_approved: boolean;
  decline_reason_description: string | null;
  auth_detail_id: number | null;
}

export interface AuthDetailResponse {
  auth_id: number;
  acct_id: number;
  auth_date_9c: number | null;
  auth_time_9c: number | null;
  auth_orig_date: string | null;
  auth_orig_time: string | null;
  card_num: string | null;
  auth_type: string | null;
  card_expiry_date: string | null;
  message_type: string | null;
  message_source: string | null;
  auth_id_code: string | null;
  auth_resp_code: string | null;
  auth_resp_reason: string | null;
  processing_code: number | null;
  transaction_amt: string;
  approved_amt: string;
  merchant_category_code: string | null;
  acqr_country_code: string | null;
  pos_entry_mode: number | null;
  merchant_id: string | null;
  merchant_name: string | null;
  merchant_city: string | null;
  merchant_state: string | null;
  merchant_zip: string | null;
  transaction_id: string | null;
  match_status: string;
  auth_fraud: string | null;
  fraud_rpt_date: string | null;
  is_approved: boolean;
  decline_reason_description: string | null;
}

export interface AuthSummaryResponse {
  acct_id: number;
  cust_id: number | null;
  auth_status: string | null;
  credit_limit: string;
  cash_limit: string;
  credit_balance: string;
  cash_balance: string;
  available_credit: string;
  approved_auth_cnt: number;
  declined_auth_cnt: number;
  approved_auth_amt: string;
  declined_auth_amt: string;
}

export interface AuthDetailListResponse {
  items: AuthDetailResponse[];
  total: number;
  next_cursor: number | null;
  prev_cursor: number | null;
  summary: AuthSummaryResponse | null;
}

export interface FraudMarkRequest {
  action: FraudAction;
}

export interface FraudMarkResponse {
  success: boolean;
  message: string;
  auth_fraud: string | null;
  fraud_rpt_date: string | null;
}

// ─── Transaction Types ────────────────────────────────────────────────────────

export interface TransactionTypeResponse {
  type_cd: string; // TR_TYPE CHAR(2)
  description: string; // TR_DESCRIPTION CHAR(50)
}

export interface TransactionTypeListResponse {
  items: TransactionTypeResponse[];
  total: number;
  next_cursor: string | null;
  prev_cursor: string | null;
}

export interface TransactionTypeUpdateRequest {
  description: string;
}

// ─── API Error ────────────────────────────────────────────────────────────────

export interface ApiError {
  detail: string | ValidationError[];
  status?: number;
}

export interface ValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
}

// ─── Pagination helpers ───────────────────────────────────────────────────────

export interface PaginationParams {
  cursor?: string;
  limit?: number;
  direction?: 'forward' | 'backward';
}
