/**
 * TypeScript interfaces matching the FastAPI Pydantic schemas.
 *
 * COBOL origin: Maps USRSEC VSAM KSDS fields (CSUSR01Y copybook)
 * and COUSR BMS map field types to TypeScript.
 *
 * Security: password_hash is NEVER included in any response type.
 */

// ---------------------------------------------------------------------------
// User types — maps CSUSR01Y copybook fields
// ---------------------------------------------------------------------------

/**
 * User type values.
 * COBOL origin: SEC-USR-TYPE X(01) — 'A'=Admin, 'U'=Regular
 */
export type UserType = 'A' | 'U';

/**
 * User response from GET /api/v1/users and GET /api/v1/users/{user_id}.
 * Password is NEVER included.
 *
 * COBOL origin: COUSR0AO output map fields: USRID1O, FNAME1O, LNAME1O, UTYPE1O
 */
export interface UserResponse {
  user_id: string;        // SEC-USR-ID X(08)
  first_name: string;     // SEC-USR-FNAME X(20)
  last_name: string;      // SEC-USR-LNAME X(20)
  user_type: UserType;    // SEC-USR-TYPE X(01)
  created_at: string;     // ISO datetime (not in original VSAM)
  updated_at: string;     // ISO datetime (not in original VSAM)
}

/**
 * Paginated user list response from GET /api/v1/users.
 *
 * COBOL origin: COUSR00C POPULATE-USER-DATA output state:
 *   items           → rows displayed (USRID1O–USRID10O, FNAME1O–FNAME10O, etc.)
 *   has_next        → CDEMO-CU00-NEXT-PAGE-FLG
 *   first_item_key  → CDEMO-CU00-USRID-FIRST
 *   last_item_key   → CDEMO-CU00-USRID-LAST
 */
export interface UserListResponse {
  items: UserResponse[];
  page: number;
  page_size: number;
  total_count: number;
  has_next: boolean;
  has_previous: boolean;
  first_item_key: string | null;
  last_item_key: string | null;
}

/**
 * Request body for POST /api/v1/users.
 *
 * COBOL origin: COUSR01C COUSR1AI input map fields:
 *   FNAMEI, LNAMEI, USERIDI, PASSWDI, USRTYPEI — all required
 */
export interface UserCreateRequest {
  user_id: string;      // USERIDI (max 8 chars, alphanumeric)
  first_name: string;   // FNAMEI (max 20 chars, non-blank)
  last_name: string;    // LNAMEI (max 20 chars, non-blank)
  password: string;     // PASSWDI (required on create)
  user_type: UserType;  // USRTYPEI ('A' or 'U')
}

/**
 * Request body for PUT /api/v1/users/{user_id}.
 *
 * COBOL origin: COUSR02C COUSR2AI editable fields (user_id not editable):
 *   FNAMEI, LNAMEI, PASSWDI (optional), USRTYPEI
 */
export interface UserUpdateRequest {
  first_name: string;
  last_name: string;
  password?: string;    // Optional — blank means no password change
  user_type: UserType;
}

// ---------------------------------------------------------------------------
// Common API types
// ---------------------------------------------------------------------------

export interface ApiErrorResponse {
  error_code: string;
  message: string;
  details: Array<{ field?: string; message: string }>;
}

export interface MessageResponse {
  message: string;
}

export interface PaginationParams {
  page: number;
  page_size: number;
  user_id_filter?: string;
}

// ---------------------------------------------------------------------------
// Transaction Type types — maps CARDDEMO.TRANSACTION_TYPE DB2 table
// COBOL origin: COTRTLIC (list/update/delete) + COTRTUPC (add/update/delete)
// ---------------------------------------------------------------------------

/**
 * Transaction type response from GET /api/v1/transaction-types and related endpoints.
 *
 * COBOL origin: DCLTRTYP DCLGEN fields:
 *   DCL-TR-TYPE         CHAR(2)     → type_code
 *   DCL-TR-DESCRIPTION  VARCHAR(50) → description
 *   updated_at is added for optimistic locking (replaces COTRTLIC WS-DATACHANGED-FLAG)
 */
export interface TransactionTypeResponse {
  type_code: string;    // TR_TYPE CHAR(2) — 2-digit numeric, e.g. '01'
  description: string;  // TR_DESCRIPTION VARCHAR(50) — alphanumeric only
  created_at: string;   // ISO datetime (not in original DB2 table)
  updated_at: string;   // ISO datetime — used as optimistic lock version on PUT
}

/**
 * Paginated transaction type list response from GET /api/v1/transaction-types.
 *
 * COBOL origin: COTRTLIC WS-CA-ALL-ROWS-OUT (7 rows per page, WS-MAX-SCREEN-LINES=7).
 *   has_next        → CA-NEXT-PAGE-EXISTS
 *   first_item_key  → WS-CA-FIRST-TR-CODE (backward cursor anchor)
 *   last_item_key   → WS-CA-LAST-TR-CODE (forward cursor anchor)
 */
export interface TransactionTypeListResponse {
  items: TransactionTypeResponse[];
  page: number;
  page_size: number;
  total_count: number;
  has_next: boolean;
  has_previous: boolean;
  first_item_key: string | null;
  last_item_key: string | null;
}

/**
 * Request body for POST /api/v1/transaction-types.
 *
 * COBOL origin: COTRTUPC TTUP-CREATE-NEW-RECORD state.
 *   TRTYPCD → type_code (numeric 01-99, non-zero per 1210-EDIT-TRANTYPE)
 *   TRTYDSC → description (alphanumeric per 1230-EDIT-ALPHANUM-REQD)
 */
export interface TransactionTypeCreateRequest {
  type_code: string;    // 1-2 digit numeric string, e.g. '01', '15'
  description: string;  // Alphanumeric + spaces, max 50 chars
}

/**
 * Request body for PUT /api/v1/transaction-types/{type_code}.
 *
 * COBOL origin: COTRTUPC 9600-WRITE-PROCESSING (UPDATE path).
 * Only description is editable — type_code is protected on both screens.
 * optimistic_lock_version replaces COTRTLIC WS-DATACHANGED-FLAG.
 */
export interface TransactionTypeUpdateRequest {
  description: string;                // New description
  optimistic_lock_version: string;   // updated_at from GET — ISO datetime string
}

/**
 * Query parameters for GET /api/v1/transaction-types.
 *
 * COBOL origin: COTRTLIC filter fields TRTYPE (type code filter) and TRDESC (description filter).
 */
export interface TransactionTypeListParams {
  page?: number;
  page_size?: number;
  type_code_filter?: string;
  description_filter?: string;
}

// ---------------------------------------------------------------------------
// Auth store types
// ---------------------------------------------------------------------------

export interface AuthUser {
  user_id: string;
  user_type: UserType;
  first_name?: string;
  last_name?: string;
}

export interface AuthStore {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  setAuth: (user: AuthUser, token: string) => void;
  clearAuth: () => void;
}
