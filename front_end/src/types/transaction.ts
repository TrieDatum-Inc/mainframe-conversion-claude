/**
 * TypeScript types mirroring the FastAPI response schemas.
 * Field names match COBOL CVTRA05Y copybook layout.
 */

export interface TransactionListItem {
  tran_id: string;
  tran_orig_ts: string;
  tran_desc: string;
  tran_amt: number;
}

export interface PaginationMeta {
  page: number;
  page_size: number;
  has_next_page: boolean;
  has_prev_page: boolean;
  first_tran_id: string | null;
  last_tran_id: string | null;
}

export interface TransactionListResponse {
  items: TransactionListItem[];
  pagination: PaginationMeta;
}

export interface TransactionDetail {
  tran_id: string;
  tran_type_cd: string;
  tran_cat_cd: string;
  tran_source: string;
  tran_desc: string;
  tran_amt: number;
  tran_merchant_id: string;
  tran_merchant_name: string;
  tran_merchant_city: string;
  tran_merchant_zip: string;
  tran_card_num: string;
  tran_orig_ts: string;
  tran_proc_ts: string;
}

/**
 * Form data for COTRN02C Add Transaction screen.
 * Maps directly to TransactionCreate Pydantic schema.
 */
export interface TransactionFormData {
  acct_id?: string;
  card_num?: string;
  tran_type_cd: string;
  tran_cat_cd: string;
  tran_source: string;
  tran_desc: string;
  tran_amt: string;        // string to preserve ±99999999.99 format
  tran_orig_dt: string;    // YYYY-MM-DD
  tran_proc_dt: string;    // YYYY-MM-DD
  tran_merchant_id: string;
  tran_merchant_name: string;
  tran_merchant_city: string;
  tran_merchant_zip: string;
  confirm?: string;
}

export interface TransactionValidateResponse {
  resolved_card_num: string;
  resolved_acct_id: string;
  acct_active: boolean;
  normalized_amt: string;
}

export interface ApiError {
  detail: string;
  field?: string;
}
