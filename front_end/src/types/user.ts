/**
 * TypeScript types for User Administration module.
 *
 * Maps to COBOL CSUSR01Y.cpy SEC-USER-DATA record layout and
 * Pydantic schemas in the FastAPI backend.
 */

/**
 * User type values.
 * 'A' = Admin (SEC-USR-TYPE = 'A' in COBOL)
 * 'U' = Regular user (SEC-USR-TYPE = 'U' in COBOL)
 *
 * COBOL bug fix: COUSR01C only validated NOT SPACES; we enforce this enum.
 */
export type UserType = 'A' | 'U';

/**
 * Single row in the user list (COUSR00C BMS row fields).
 * Maps to: USRID, FNAME, LNAME, UTYPE columns from COUSR0A BMS map.
 */
export interface UserListItem {
  user_id: string;      // SEC-USR-ID PIC X(08)
  first_name: string;   // SEC-USR-FNAME PIC X(20)
  last_name: string;    // SEC-USR-LNAME PIC X(20)
  user_type: UserType;  // SEC-USR-TYPE PIC X(01)
}

/**
 * Full user record returned by GET /api/users/{user_id}.
 * Password is never included (COBOL stored plaintext; we hash and never return).
 */
export interface UserResponse {
  user_id: string;
  first_name: string;
  last_name: string;
  user_type: UserType;
  created_at: string;
  updated_at: string;
}

/**
 * Paginated user list response.
 * Maps to COUSR00C pagination state:
 *   page         → CDEMO-CU00-PAGE-NUM
 *   has_next_page → CDEMO-CU00-NEXT-PAGE-FLG = 'Y'
 *   has_prev_page → page > 1 (COUSR00C top-of-list guard)
 */
export interface UserListResponse {
  users: UserListItem[];
  page: number;
  page_size: number;
  total_count: number;
  has_next_page: boolean;
  has_prev_page: boolean;
}

/**
 * Request body for POST /api/users (COUSR01C).
 * All fields mandatory — mirrors COUSR01C PROCESS-ENTER-KEY validation.
 */
export interface UserCreateRequest {
  first_name: string;   // FNAMEI — max 20 chars (PIC X(20))
  last_name: string;    // LNAMEI — max 20 chars (PIC X(20))
  user_id: string;      // USERIDI — max 8 chars (PIC X(08))
  password: string;     // PASSWDI — DRK field on BMS map
  user_type: UserType;  // USRTYPEI — must be 'A' or 'U'
}

/**
 * Request body for PUT /api/users/{user_id} (COUSR02C).
 * user_id is the path param (immutable VSAM key, not in this body).
 */
export interface UserUpdateRequest {
  first_name: string;
  last_name: string;
  password: string;
  user_type: UserType;
}

/**
 * API error response shape.
 */
export interface ApiError {
  detail: string | { msg: string; type: string }[];
}

/**
 * Query params for GET /api/users.
 */
export interface UserListParams {
  page?: number;
  page_size?: number;
  search_user_id?: string;
}
