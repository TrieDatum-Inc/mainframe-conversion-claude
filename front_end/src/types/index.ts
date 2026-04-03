/**
 * TypeScript types for CardDemo Batch Processing Module.
 * Mirror the Pydantic schemas in the FastAPI backend.
 */

// ============================================================
// Common
// ============================================================

export interface BatchJobResponse {
  job_id: number
  job_type: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  started_at: string | null
  completed_at: string | null
  records_processed: number
  records_rejected: number
  result_summary: Record<string, unknown> | null
  created_at: string | null
}

// ============================================================
// CBTRN02C — Transaction Posting
// ============================================================

export interface DailyTransactionInput {
  tran_id: string
  tran_type_cd: string
  tran_cat_cd: string
  tran_source: string
  tran_desc: string
  tran_amt: string | number
  tran_merchant_id?: string
  tran_merchant_name?: string
  tran_merchant_city?: string
  tran_merchant_zip?: string
  tran_card_num: string
  tran_orig_ts: string
}

export interface RejectRecord {
  tran_id: string
  card_num: string
  reason_code: string
  reason_desc: string
  original_data: Record<string, unknown>
}

export interface TransactionPostingRequest {
  transactions: DailyTransactionInput[]
}

export interface TransactionPostingResponse {
  job_id: number
  status: string
  transactions_processed: number
  transactions_posted: number
  transactions_rejected: number
  has_rejects: boolean
  rejects: RejectRecord[]
  message: string
}

// ============================================================
// CBTRN03C — Transaction Report
// ============================================================

export interface TransactionReportRequest {
  start_date: string  // YYYY-MM-DD
  end_date: string    // YYYY-MM-DD
}

export interface TransactionReportLine {
  tran_id: string
  account_id: string
  tran_type_cd: string
  tran_type_desc: string
  tran_cat_cd: string
  tran_cat_desc: string
  tran_source: string
  tran_amt: string | number
  tran_proc_ts: string
  card_num: string
}

export interface ReportTotals {
  grand_total: string | number
  page_count: number
  transaction_count: number
}

export interface TransactionReportResponse {
  job_id: number
  status: string
  start_date: string
  end_date: string
  report_lines: TransactionReportLine[]
  totals: ReportTotals
  report_text: string
  message: string
}

// ============================================================
// CBACT04C — Interest Calculation
// ============================================================

export interface InterestCalculationRequest {
  run_date: string  // YYYY-MM-DD
}

export interface InterestTransactionResult {
  tran_id: string
  acct_id: string
  tran_type_cd: string
  tran_cat_cd: string
  balance: string | number
  interest_rate: string | number
  monthly_interest: string | number
  card_num: string
}

export interface AccountInterestSummary {
  acct_id: string
  total_interest: string | number
  category_count: number
  transactions_created: InterestTransactionResult[]
}

export interface InterestCalculationResponse {
  job_id: number
  status: string
  run_date: string
  accounts_processed: number
  interest_transactions_created: number
  account_summaries: AccountInterestSummary[]
  message: string
}

// ============================================================
// CBEXPORT — Data Export
// ============================================================

export interface CustomerExport {
  cust_id: string
  cust_first_name: string | null
  cust_middle_name: string | null
  cust_last_name: string | null
  cust_addr_line_1: string | null
  cust_addr_line_2: string | null
  cust_addr_line_3: string | null
  cust_addr_state_cd: string | null
  cust_addr_country_cd: string | null
  cust_addr_zip: string | null
  cust_phone_num_1: string | null
  cust_phone_num_2: string | null
  cust_ssn: string | null
  cust_govt_issued_id: string | null
  cust_dob: string | null
  cust_eft_account_id: string | null
  cust_pri_card_holder_ind: string | null
  cust_fico_credit_score: number | null
}

export interface AccountExport {
  acct_id: string
  acct_active_status: string
  acct_curr_bal: string | number
  acct_credit_limit: string | number
  acct_cash_credit_limit: string | number
  acct_open_date: string | null
  acct_expiration_date: string | null
  acct_reissue_date: string | null
  acct_curr_cyc_credit: string | number
  acct_curr_cyc_debit: string | number
  acct_addr_zip: string | null
  acct_group_id: string | null
}

export interface XrefExport {
  xref_card_num: string
  xref_cust_id: string | null
  xref_acct_id: string | null
}

export interface TransactionExport {
  tran_id: string
  tran_type_cd: string | null
  tran_cat_cd: string | null
  tran_source: string | null
  tran_desc: string | null
  tran_amt: string | number | null
  tran_merchant_id: string | null
  tran_merchant_name: string | null
  tran_merchant_city: string | null
  tran_merchant_zip: string | null
  tran_card_num: string | null
  tran_orig_ts: string | null
  tran_proc_ts: string | null
}

export interface CardExport {
  card_num: string
  card_acct_id: string | null
  card_cvv_cd: string | null
  card_embossed_name: string | null
  card_expiration_date: string | null
  card_active_status: string
}

export interface ExportPayload {
  export_timestamp: string
  branch_id: string
  region_code: string
  customers: CustomerExport[]
  accounts: AccountExport[]
  xrefs: XrefExport[]
  transactions: TransactionExport[]
  cards: CardExport[]
  total_records: number
}

export interface ExportResponse {
  job_id: number
  status: string
  customers_exported: number
  accounts_exported: number
  xrefs_exported: number
  transactions_exported: number
  cards_exported: number
  total_records_exported: number
  payload: ExportPayload
  message: string
}

// ============================================================
// CBIMPORT — Data Import
// ============================================================

export interface ImportValidationError {
  record_type: string
  record_id: string
  field: string
  error: string
}

export interface ImportRequest {
  payload: ExportPayload
}

export interface ImportResponse {
  job_id: number
  status: string
  total_records_read: number
  customers_imported: number
  accounts_imported: number
  xrefs_imported: number
  transactions_imported: number
  cards_imported: number
  validation_errors: ImportValidationError[]
  error_count: number
  message: string
}

// ============================================================
// UI State
// ============================================================

export type JobStatus = 'idle' | 'running' | 'success' | 'error'

export interface ApiError {
  detail: string
}
