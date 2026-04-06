/**
 * TypeScript types for the CardDemo Transaction Module frontend.
 * All field lengths and types mirror the COBOL record layouts (CVTRA05Y etc.)
 */

// ---------------------------------------------------------------------------
// Transactions
// ---------------------------------------------------------------------------

/** Matches TransactionListItem schema — COTRN00C 4-column display row. */
export interface TransactionListItem {
  transaction_id: string; // X(16)
  card_number: string;    // X(16)
  description: string;    // X(100)
  amount: number;
  original_date: string;  // MM/DD/YY display format
}

/** Paginated list response — matches TransactionPage schema. */
export interface TransactionPage {
  items: TransactionListItem[];
  page: number;
  page_size: number;
  total: number;
  has_next: boolean;
  has_prev: boolean;
}

/** Full transaction detail — matches COTRN01C 13 output fields. */
export interface TransactionDetail {
  transaction_id: string;
  card_number: string;
  type_code: string;
  category_code: string;
  source: string;
  description: string;
  amount: number;
  original_timestamp: string;
  processing_timestamp: string;
  merchant_id: string;
  merchant_name: string;
  merchant_city: string;
  merchant_zip: string;
  created_at: string;
  updated_at: string;
}

/** Request body for POST /api/transactions — COTRN02C fields. */
export interface TransactionCreateRequest {
  account_id?: string;
  card_number?: string;
  type_code: string;
  category_code: string;
  source?: string;
  description?: string;
  amount: number;
  original_date: string;   // YYYY-MM-DD
  processing_date: string; // YYYY-MM-DD
  merchant_id?: string;
  merchant_name?: string;
  merchant_city?: string;
  merchant_zip?: string;
  confirmed: boolean;
}

// ---------------------------------------------------------------------------
// Bill Payment
// ---------------------------------------------------------------------------

/** GET /api/bill-payment/preview/{account_id} response. */
export interface BillPaymentPreview {
  account_id: string;
  current_balance: number;
  can_pay: boolean;
  message: string;
}

/** POST /api/bill-payment request body. */
export interface BillPaymentRequest {
  account_id: string;
  confirmed: boolean;
}

/** POST /api/bill-payment response. */
export interface BillPaymentResult {
  account_id: string;
  card_number: string;
  transaction_id: string;
  amount_paid: number;
  new_balance: number;
  message: string;
}

// ---------------------------------------------------------------------------
// Reports
// ---------------------------------------------------------------------------

export type ReportType = "monthly" | "yearly" | "custom";

/** POST /api/reports/transactions request body. */
export interface ReportRequest {
  report_type: ReportType;
  start_date?: string;  // YYYY-MM-DD
  end_date?: string;    // YYYY-MM-DD
  confirmed: boolean;
}

/** Single row in report output — mirrors CBTRN03C report fields. */
export interface ReportTransactionRow {
  transaction_id: string;
  card_number: string;
  type_code: string;
  category_code: string;
  description: string;
  amount: number;
  original_date: string;
  processing_date: string;
  merchant_name: string;
  merchant_city: string;
}

/** POST /api/reports/transactions response. */
export interface ReportResult {
  report_type: ReportType;
  start_date: string;
  end_date: string;
  total_transactions: number;
  total_amount: number;
  transactions: ReportTransactionRow[];
  generated_at: string;
}

// ---------------------------------------------------------------------------
// API error shape
// ---------------------------------------------------------------------------

export interface ApiError {
  detail: string | { message: string; [key: string]: unknown };
}
