/**
 * Shared TypeScript types for the CardDemo frontend.
 *
 * These mirror the Pydantic schemas in the backend, which in turn
 * map to COBOL data structures (CSUSR01Y copybook, COMMAREA fields).
 */

/** Maps to CDEMO-USER-TYPE: 'A' = Admin, 'U' = Regular User */
export type UserType = "A" | "U";

/** Maps to CSUSR01Y user record fields */
export interface User {
  user_id: string;
  first_name: string;
  last_name: string;
  user_type: UserType;
}

/** Response from POST /api/auth/login */
export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

/** Request body for POST /api/auth/login */
export interface LoginRequest {
  user_id: string;
  password: string;
}

/** Shape of the auth context provided to all components */
export interface AuthContextValue {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
}

/** A single navigation menu item (maps to COMEN02Y / COADM02Y array entries) */
export interface MenuItem {
  id: string;
  label: string;
  description: string;
  icon: string;
  href: string;
  adminOnly: boolean;
}

/** API error response shape */
export interface ApiError {
  detail: string;
}

// ---------------------------------------------------------------------------
// Transaction Type types
// Maps to COBOL DB2: CARDDEMO.TRANSACTION_TYPE, CARDDEMO.TRANSACTION_TYPE_CATEGORY
// ---------------------------------------------------------------------------

/** Maps to TR_TYPE CHAR(2) + TR_DESCRIPTION VARCHAR(50) */
export interface TransactionType {
  id: number;
  type_code: string;
  description: string;
  created_at: string;
  updated_at: string;
}

/** TransactionType with its sub-categories (COTRTUPC detail view) */
export interface TransactionTypeDetail extends TransactionType {
  categories: TransactionTypeCategory[];
}

/** Maps to CARDDEMO.TRANSACTION_TYPE_CATEGORY */
export interface TransactionTypeCategory {
  id: number;
  type_code: string;
  category_code: string;
  description: string;
  created_at: string;
  updated_at: string;
}

/** Paginated list response from GET /api/transaction-types */
export interface PaginatedTransactionTypes {
  items: TransactionType[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

/** Request body for POST /api/transaction-types */
export interface CreateTransactionTypeRequest {
  type_code: string;
  description: string;
}

/** Request body for PUT /api/transaction-types/{type_code} */
export interface UpdateTransactionTypeRequest {
  description: string;
}

/** Request body for POST /api/transaction-types/inline-save (COTRTLIC F10=Save) */
export interface InlineSaveRequest {
  updates: Array<{ type_code: string; description: string }>;
}

/** Response from POST /api/transaction-types/inline-save */
export interface InlineSaveResponse {
  saved: number;
  errors: string[];
}

/** Request body for POST /api/transaction-types/{type_code}/categories */
export interface CreateCategoryRequest {
  category_code: string;
  description: string;
}

/** Request body for PUT /api/transaction-types/{type_code}/categories/{category_code} */
export interface UpdateCategoryRequest {
  description: string;
}

// ---------------------------------------------------------------------------
// Account types
// Maps to COBOL ACCTDATA VSAM (CVACT01Y) + CUSTDATA VSAM (CVCUS01Y)
// Programs: COACTVWC (view), COACTUPC (update)
// ---------------------------------------------------------------------------

/** Brief customer info embedded in account detail (from CXACAIX lookup) */
export interface CustomerInfo {
  id: number;
  customer_id: string;
  first_name: string;
  middle_name: string;
  last_name: string;
  address_line_1: string;
  address_line_2: string;
  address_line_3: string;
  state_code: string;
  country_code: string;
  zip_code: string;
  phone_1: string;
  phone_2: string;
  ssn: string;
  govt_issued_id: string;
  date_of_birth: string | null;
  eft_account_id: string;
  primary_card_holder: string;
  fico_score: number | null;
  created_at: string;
  updated_at: string;
}

/** Card summary row inside account detail (CARDAIX browse result) */
export interface CardSummary {
  card_number: string;
  active_status: string;
  expiration_date: string | null;
  embossed_name: string;
}

/** Single account row for list view (COACTVWC/COCRDLIC browse) */
export interface AccountListItem {
  account_id: string;
  active_status: string;
  current_balance: string;
  credit_limit: string;
  open_date: string | null;
}

/** Full account detail with customer + cards (COACTVWC output) */
export interface AccountDetail {
  id: number;
  account_id: string;
  active_status: string;
  current_balance: string;
  credit_limit: string;
  cash_credit_limit: string;
  open_date: string | null;
  expiration_date: string | null;
  reissue_date: string | null;
  current_cycle_credit: string;
  current_cycle_debit: string;
  address_zip: string | null;
  group_id: string | null;
  customer: CustomerInfo | null;
  cards: CardSummary[];
  created_at: string;
  updated_at: string;
}

/** Paginated list response for GET /api/accounts */
export interface PaginatedAccounts {
  items: AccountListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/** Request body for PUT /api/accounts/{account_id} (COACTUPC editable fields) */
export interface AccountUpdateRequest {
  // Account fields
  active_status?: string;
  credit_limit?: number;
  cash_credit_limit?: number;
  open_date?: string | null;
  expiration_date?: string | null;
  reissue_date?: string | null;
  current_cycle_credit?: number;
  current_cycle_debit?: number;
  group_id?: string | null;
  // Customer fields
  first_name?: string;
  middle_name?: string;
  last_name?: string;
  address_line_1?: string;
  address_line_2?: string;
  address_line_3?: string;
  state_code?: string;
  country_code?: string;
  zip_code?: string;
  phone_1?: string;
  phone_2?: string;
  ssn?: string;
  govt_issued_id?: string;
  date_of_birth?: string | null;
  eft_account_id?: string;
  primary_card_holder?: string;
  fico_score?: number | null;
}

// ---------------------------------------------------------------------------
// Card types
// Maps to COBOL CARDDATA VSAM (CVACT02Y)
// Programs: COCRDLIC (list), COCRDSLC (view), COCRDUPC (update)
// ---------------------------------------------------------------------------

/** Card row for list view (COCRDLIC 7-per-page) */
export interface CardListItem {
  card_number: string;
  account_id: string;
  embossed_name: string;
  active_status: string;
  expiration_date: string | null;
}

/** Full card record (COCRDSLC view) */
export interface CardDetail {
  id: number;
  card_number: string;
  account_id: string;
  cvv_code: string;
  embossed_name: string;
  active_status: string;
  expiration_date: string | null;
  created_at: string;
  updated_at: string;
}

/** Paginated list response for GET /api/cards (COCRDLIC 7 per page) */
export interface PaginatedCards {
  items: CardListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/** Request body for PUT /api/cards/{card_number} (COCRDUPC editable fields) */
export interface CardUpdateRequest {
  embossed_name?: string;
  active_status?: string;     // 'Y' or 'N' only
  expiry_month?: number;      // 1-12
  expiry_year?: number;       // 1950-2099
  // NOTE: account_id is NEVER included — it is PROTECTED (ACCTSID PROT in BMS)
}
