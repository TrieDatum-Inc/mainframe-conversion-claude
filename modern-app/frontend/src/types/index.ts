/**
 * TypeScript types for the Authorization module.
 *
 * Mirrors Pydantic schemas from the FastAPI backend.
 * Field names map to COBOL IMS segment fields.
 */

// ---------------------------------------------------------------------------
// Decline Reason Codes (COPAUS1C 10-entry lookup table)
// ---------------------------------------------------------------------------

export const DECLINE_REASON_CODES: Record<string, string> = {
  "00": "APPROVED",
  "31": "INVALID CARD",
  "41": "INSUFFICIENT FUND",
  "42": "CARD NOT ACTIVE",
  "43": "ACCOUNT CLOSED",
  "44": "EXCEED DAILY LIMIT",
  "51": "CARD FRAUD",
  "52": "MERCHANT FRAUD",
  "53": "LOST CARD",
  "90": "UNKNOWN",
};

// ---------------------------------------------------------------------------
// Authorization Summary (IMS PAUTSUM0 root segment)
// Maps to COPAU00 BMS screen account context section
// ---------------------------------------------------------------------------

export interface AuthorizationSummary {
  id: number;
  account_id: string;
  customer_id: string;
  auth_status: "A" | "C" | "I";
  credit_limit: string;
  cash_limit: string;
  credit_balance: string;
  cash_balance: string;
  approved_count: number;
  declined_count: number;
  approved_amount: string;
  declined_amount: string;
}

export interface AuthorizationSummaryListItem {
  id: number;
  account_id: string;
  customer_id: string;
  auth_status: "A" | "C" | "I";
  approved_count: number;
  declined_count: number;
  approved_amount: string;
  declined_amount: string;
}

// ---------------------------------------------------------------------------
// Authorization Detail (IMS PAUTDTL1 child segment)
// Maps to COPAU01 BMS screen fields
// ---------------------------------------------------------------------------

export interface AuthorizationDetail {
  id: number;
  summary_id: number;
  card_number: string;
  auth_date: string; // ISO date string YYYY-MM-DD
  auth_time: string; // HH:MM:SS
  auth_type: string;
  card_expiry: string;
  message_type: string;
  auth_response_code: string;
  auth_response_reason: string;
  auth_code: string;
  transaction_amount: string;
  approved_amount: string;
  pos_entry_mode: string;
  auth_source: string;
  mcc_code: string;
  merchant_name: string;
  merchant_id: string;
  merchant_city: string;
  merchant_state: string;
  merchant_zip: string;
  transaction_id: string;
  match_status: "P" | "D" | "E" | "M";
  fraud_status: "F" | "R" | null;
  fraud_report_date: string | null;
  processing_code: string;
  decline_reason_description: string | null;
}

// ---------------------------------------------------------------------------
// Paginated Detail Response (COPAUS0C 5-per-page view)
// ---------------------------------------------------------------------------

export interface PaginatedDetailResponse {
  summary: AuthorizationSummary;
  details: AuthorizationDetail[];
  page: number;
  page_size: number;
  total_count: number;
  total_pages: number;
}

export interface AuthorizationListResponse {
  items: AuthorizationSummaryListItem[];
  page: number;
  page_size: number;
  total_count: number;
  total_pages: number;
}

// ---------------------------------------------------------------------------
// Authorization Processing (COPAUA0C MQ request → POST /process)
// ---------------------------------------------------------------------------

export interface AuthorizationProcessRequest {
  card_number: string;
  card_expiry: string;
  amount: string;
  auth_type?: string;
  message_type?: string;
  pos_entry_mode?: string;
  processing_code?: string;
  mcc_code?: string;
  merchant_name?: string;
  merchant_id?: string;
  merchant_city?: string;
  merchant_state?: string;
  merchant_zip?: string;
}

export interface AuthorizationProcessResponse {
  transaction_id: string;
  auth_response: "A" | "D"; // A=Approved, D=Declined
  auth_response_code: string;
  auth_response_reason: string;
  auth_code: string;
  transaction_amount: string;
  approved_amount: string;
  card_number: string;
  decline_reason: string | null;
}

// ---------------------------------------------------------------------------
// Fraud Management (COPAUS2C mark/remove)
// ---------------------------------------------------------------------------

export interface FraudActionRequest {
  action: "mark" | "remove";
}

export interface FraudActionResponse {
  success: boolean;
  action: string;
  fraud_flag: "F" | "R" | null;
  fraud_report_date: string | null;
  message: string;
}

// ---------------------------------------------------------------------------
// Purge (CBPAUP0C batch equivalent — admin only)
// ---------------------------------------------------------------------------

export interface PurgeRequest {
  expiry_days?: number;
}

export interface PurgeResponse {
  details_purged: number;
  summaries_purged: number;
  expiry_days: number;
  message: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

export function getAuthStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    A: "Active",
    C: "Closed",
    I: "Inactive",
  };
  return labels[status] ?? status;
}

export function getMatchStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    P: "Pending",
    D: "Declined",
    E: "Expired",
    M: "Matched",
  };
  return labels[status] ?? status;
}

export function getFraudStatusLabel(status: string | null): string {
  if (!status) return "None";
  return status === "F" ? "Fraud Confirmed" : "Fraud Removed";
}
