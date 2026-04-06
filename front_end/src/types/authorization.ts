/**
 * TypeScript types for the Authorization module.
 * Maps Pydantic schemas from the backend to TypeScript interfaces.
 * Sources: COPAU00 (COPAU0A map) and COPAU01 (COPAU1A map) BMS fields.
 */

/**
 * Authorization summary — maps IMS PAUTSUM0 root segment.
 * Displayed in rows 6-12 of COPAU00 screen.
 * Fields: PA-CREDIT-LIMIT, PA-CASH-LIMIT, PA-CREDIT-BALANCE, PA-CASH-BALANCE,
 *         PA-APPROVED-AUTH-CNT, PA-DECLINED-AUTH-CNT, PA-APPROVED-AUTH-AMT, PA-DECLINED-AUTH-AMT
 */
export interface AuthSummaryResponse {
  account_id: number;
  credit_limit: number;
  cash_limit: number;
  credit_balance: number;
  cash_balance: number;
  approved_auth_count: number;   // PA-APPROVED-AUTH-CNT — APPRCNTO
  declined_auth_count: number;   // PA-DECLINED-AUTH-CNT — DECLCNTO
  approved_auth_amount: number;  // PA-APPROVED-AUTH-AMT — APPRAMTO
  declined_auth_amount: number;  // PA-DECLINED-AUTH-AMT — DECLAMTO
}

/**
 * Single authorization list row — maps 5 rows of COPAU00 screen.
 * Fields: TRNIDnn, PDATEnn, PTIMEnn, PTYPEnn, PAPRVnn, PSTATnn, PAMTnnn
 * COPAUS0C POPULATE-AUTH-LIST paragraph.
 */
export interface AuthListItem {
  auth_id: number;
  transaction_id: string;       // PA-TRANSACTION-ID — TRNIDnn (BLUE)
  card_number_masked: string;
  auth_date: string;            // PA-AUTH-ORIG-DATE MM/DD/YY — PDATEnn
  auth_time: string;            // PA-AUTH-ORIG-TIME HH:MM:SS — PTIMEnn
  auth_type: string | null;     // PA-AUTH-TYPE — PTYPEnn
  approval_status: 'A' | 'D';  // 'A'=Approved, 'D'=Declined — PAPRVnn
  match_status: 'P' | 'D' | 'E' | 'M';  // PA-MATCH-STATUS — PSTATnn
  amount: number;               // PA-TRANSACTION-AMT — PAMTnnn
  fraud_status: 'N' | 'F' | 'R';
  fraud_status_display: string; // 'FRAUD' | 'REMOVED' | ''
}

/**
 * Paginated authorization list response — maps COPAUS0C screen.
 * summary: PAUTSUM0 header section (rows 6-12)
 * items: up to 5 PAUTDTL1 detail rows (rows 16-20)
 * has_next: CDEMO-CPVS-NEXT-PAGE-FLG 'Y'/'N' (PF8 availability)
 * has_previous: PF7 availability
 */
export interface AuthListResponse {
  summary: AuthSummaryResponse;
  items: AuthListItem[];
  page: number;
  page_size: number;
  total_count: number;
  has_next: boolean;   // CDEMO-CPVS-NEXT-PAGE-FLG
  has_previous: boolean;
}

/**
 * Full authorization detail — maps all COPAU01 (COPAU1A map) fields.
 * All fields are ASKIP (read-only) on COPAU01.
 * AUTHMTCO and AUTHFRDO displayed in RED.
 * COPAUS1C POPULATE-AUTH-DETAILS paragraph (lines 291-357).
 */
export interface AuthDetailResponse {
  auth_id: number;
  account_id: number;

  // CARDNUMO — PA-CARD-NUM (PINK text on COPAU01)
  card_number: string;
  card_number_masked: string;

  // AUTHDTO — PA-AUTH-ORIG-DATE (PINK text)
  auth_date: string;
  // AUTHTMO — PA-AUTH-ORIG-TIME (PINK text)
  auth_time: string;

  // AUTHRSPO — PA-AUTH-RESP-CODE ('A'=Approved, 'D'=Declined)
  // GREEN if '00', RED otherwise (DFHGREEN/DFHRED in COPAUS1C)
  auth_response_code: string;
  approval_status: 'A' | 'D';

  // AUTHRSNO — DECL-CODE + '-' + DECL-DESC (from SEARCH ALL table)
  // e.g., '4100-INSUFFICNT FUND', '00-APPROVED'
  decline_reason: string;

  // AUTHCDO — PA-PROCESSING-CODE (auth approval code)
  auth_code: string | null;

  // AUTHAMTO — PA-TRANSACTION-AMT
  amount: number;

  // POSEMDO — PA-POS-ENTRY-MODE
  pos_entry_mode: string | null;

  // AUTHSRCO — PA-MESSAGE-SOURCE
  auth_source: string | null;

  // MCCCDO — PA-MERCHANT-CATAGORY-CODE
  mcc_code: string | null;

  // CRDEXPO — PA-CARD-EXPIRY-DATE
  card_expiry: string | null;

  // AUTHTYPO — PA-AUTH-TYPE
  auth_type: string | null;

  // TRNIDO — PA-TRANSACTION-ID
  transaction_id: string;

  // AUTHMTCO — PA-MATCH-STATUS (RED text on COPAU01)
  match_status: 'P' | 'D' | 'E' | 'M';

  // AUTHFRDO — fraud status (RED text on COPAU01)
  fraud_status: 'N' | 'F' | 'R';
  fraud_status_display: 'FRAUD' | 'REMOVED' | '';

  // Merchant details section (below row 17 separator in COPAU01)
  merchant_name: string | null;  // MERNAMEO (row 19)
  merchant_id: string | null;    // MERIDO (row 19)
  merchant_city: string | null;  // MERCITYO (row 21)
  merchant_state: string | null; // MERSTO (row 21)
  merchant_zip: string | null;   // MERZIPO (row 21)

  processed_at: string | null;
  updated_at: string | null;
}

/**
 * Fraud toggle request — maps COPAUS1C PF5 action body.
 * current_fraud_status: client-side current value to prevent double-toggle.
 */
export interface FraudToggleRequest {
  current_fraud_status: 'N' | 'F' | 'R';
}

/**
 * Fraud toggle response — maps COPAUS2C result + COPAUS1C POPULATE-AUTH-DETAILS.
 * Returned after successful toggle for immediate UI update.
 */
export interface FraudToggleResponse {
  auth_id: number;
  previous_fraud_status: 'N' | 'F' | 'R';
  new_fraud_status: 'N' | 'F' | 'R';
  fraud_status_display: 'FRAUD' | 'REMOVED' | '';
  fraud_report_date: string | null;
  message: string;  // 'ADD SUCCESS' | 'UPDT SUCCESS' (WS-FRD-ACT-MSG)
}

/**
 * Fraud audit log entry — maps DB2 CARDDEMO.AUTHFRDS row.
 */
export interface AuthFraudLogResponse {
  log_id: number;
  auth_id: number;
  transaction_id: string;
  card_number_masked: string;
  account_id: number;
  fraud_flag: 'F' | 'R';
  fraud_flag_display: string;
  fraud_report_date: string;
  auth_response_code: string | null;
  auth_amount: number | null;
  merchant_name: string | null;
  merchant_id: string | null;
  logged_at: string;
}

/**
 * Paginated response envelope (generic).
 */
export interface PaginatedResponse<T> {
  items: T[];
  page: number;
  page_size: number;
  total_count: number;
  has_next: boolean;
  has_previous: boolean;
}

/**
 * API error response — standard error envelope.
 */
export interface ApiError {
  error_code: string;
  message: string;
  details: string[];
}

/**
 * Match status labels (COPAUS1C: P=Pending, D=Declined, E=Expired, M=Matched)
 */
export const MATCH_STATUS_LABELS: Record<string, string> = {
  P: 'Pending',
  D: 'Declined',
  E: 'Expired',
  M: 'Matched',
};

/**
 * Fraud status metadata for color coding and labels.
 * Maps BMS display: AUTHFRDO='FRAUD'(RED)/'REMOVED'(YELLOW)/''(GREEN=no fraud)
 */
export const FRAUD_STATUS_CONFIG: Record<
  'N' | 'F' | 'R',
  { label: string; badgeClass: string; toggleLabel: string }
> = {
  N: {
    label: 'No Fraud',
    badgeClass: 'bg-green-100 text-green-800 border border-green-300',
    toggleLabel: 'Mark as Fraud',
  },
  F: {
    label: 'Fraud Confirmed',
    badgeClass: 'bg-red-100 text-red-800 border border-red-300',
    toggleLabel: 'Remove Fraud Flag',
  },
  R: {
    label: 'Fraud Removed',
    badgeClass: 'bg-yellow-100 text-yellow-800 border border-yellow-300',
    toggleLabel: 'Re-confirm Fraud',
  },
};
