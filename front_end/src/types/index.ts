// =============================================================================
// TypeScript types matching backend Pydantic schemas
// CardDemo Credit Cards Module
// =============================================================================

// --- Auth ---

export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  username: string;
  role: string;
}

// --- Customer ---

export interface CustomerDetailResponse {
  customer_id: number;
  first_name: string;
  middle_name?: string;
  last_name: string;
  ssn_masked: string;
  date_of_birth?: string;
  address?: string;
  city?: string;
  state?: string;
  zip_code?: string;
  country?: string;
  phone_number?: string;
  email?: string;
  fico_credit_score?: number;
}

export interface CustomerUpdateRequest {
  first_name: string;
  middle_name?: string;
  last_name: string;
  ssn_part1?: string; // NNN
  ssn_part2?: string; // NN
  ssn_part3?: string; // NNNN
  date_of_birth?: string; // YYYY-MM-DD
  address?: string;
  city?: string;
  state?: string;
  zip_code?: string;
  country?: string;
  phone_number?: string;
  email?: string;
  fico_credit_score?: number;
}

// --- Account (COACTVWC / COACTUPC) ---

export interface AccountDetailResponse {
  account_id: number;
  active_status: "Y" | "N";
  credit_limit: number;
  cash_credit_limit: number;
  current_balance: number;
  current_cycle_credit: number;
  current_cycle_debit: number;
  open_date?: string;
  expiration_date?: string;
  reissue_date?: string;
  group_id?: string;
  customer: CustomerDetailResponse;
}

export interface AccountUpdateRequest {
  active_status?: "Y" | "N";
  credit_limit?: number;
  cash_credit_limit?: number;
  current_balance?: number;
  current_cycle_credit?: number;
  current_cycle_debit?: number;
  group_id?: string;
  customer: CustomerUpdateRequest;
}

// --- Credit Card (COCRDLIC / COCRDSLC / COCRDUPC) ---

export interface CardListItem {
  card_number: string;         // Full (for navigation)
  card_number_masked: string;  // Display (PCI-DSS)
  account_id: number;
  card_embossed_name: string;
  active_status: "Y" | "N";
  expiration_month?: number;
  expiration_year?: number;
}

export interface CardListResponse {
  items: CardListItem[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface CardDetailResponse {
  card_number: string;
  account_id: number;
  card_embossed_name: string;
  active_status: "Y" | "N";
  expiration_month?: number;
  expiration_year?: number;
  expiration_day?: number;     // DRK PROT FSET hidden BMS field
  updated_at: string;          // ISO timestamp — used as optimistic lock version
}

export interface CardUpdateRequest {
  card_embossed_name: string;
  active_status: "Y" | "N";
  expiration_month: number;
  expiration_year: number;
  optimistic_lock_version: string; // Must match updated_at from GET response
}

// --- Common ---

export interface ApiError {
  error_code: string;
  message: string;
  details?: string[];
}

export interface ApiErrorResponse {
  detail: ApiError;
}
