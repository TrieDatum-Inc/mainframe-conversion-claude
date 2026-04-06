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
