/**
 * TypeScript type definitions for the CardDemo frontend.
 *
 * These types mirror the Pydantic schemas in the backend and the COBOL
 * data structures from the original VSAM/BMS specifications.
 */

// =============================================================================
// Authentication Types
// Maps COSGN0A BMS map fields and CARDDEMO-COMMAREA
// =============================================================================

/**
 * Login form values — maps COSGN0A BMS map input fields:
 *   USERIDI (USERID field, 8 chars, UNPROT) → userId
 *   PASSWDI (PASSWD field, 8 chars, DRK UNPROT) → password
 */
export interface LoginFormValues {
  userId: string;    // COBOL: USERIDI PIC X(8); max 8 chars
  password: string;  // COBOL: PASSWDI PIC X(8); DRK = type="password"
}

/**
 * Login API request body — matches backend LoginRequest schema.
 */
export interface LoginRequest {
  user_id: string;
  password: string;
}

/**
 * Login API response — matches backend LoginResponse schema.
 * Maps CARDDEMO-COMMAREA fields populated by COSGN00C PROCESS-ENTER-KEY.
 */
export interface LoginResponse {
  access_token: string;
  token_type: 'bearer';
  expires_in: number;        // seconds; default 3600
  user_id: string;           // CDEMO-USER-ID X(8)
  user_type: 'A' | 'U';     // CDEMO-USER-TYPE; 'A'=Admin, 'U'=User
  first_name: string;        // CDEMO-USER-FNAME
  last_name: string;         // CDEMO-USER-LNAME
  redirect_to: string;       // '/admin/menu' for A, '/menu' for U
}

// =============================================================================
// User Types
// Maps CSUSR01Y copybook fields and COUSR00-03C BMS map fields
// =============================================================================

/**
 * User type discriminator — maps SEC-USR-TYPE PIC X(01):
 *   'A' = Administrator (CDEMO-USRTYP-ADMIN 88-level)
 *   'U' = Regular User
 */
export type UserType = 'A' | 'U';

/**
 * User record — matches backend UserResponse schema.
 * password_hash is intentionally excluded (never returned by API).
 */
export interface User {
  user_id: string;           // SEC-USR-ID PIC X(08)
  first_name: string;        // SEC-USR-FNAME PIC X(20)
  last_name: string;         // SEC-USR-LNAME PIC X(20)
  user_type: UserType;       // SEC-USR-TYPE PIC X(01)
  created_at: string;        // ISO 8601 timestamp
  updated_at: string;        // ISO 8601 timestamp
}

// =============================================================================
// API Error Types
// Maps COBOL WS-MESSAGE and CICS RESP codes to structured errors
// =============================================================================

/**
 * Standard API error response — matches backend ErrorResponse schema.
 * Maps WS-MESSAGE display in COBOL programs.
 */
export interface ApiError {
  error_code: string;   // e.g. "INVALID_CREDENTIALS", "USER_NOT_FOUND"
  message: string;      // Human-readable message (maps WS-MESSAGE content)
  details: Array<{
    field?: string;
    message: string;
  }>;
}

/**
 * Standard API success message — matches backend MessageResponse schema.
 */
export interface MessageResponse {
  message: string;
}

// =============================================================================
// Auth Store Types
// Replaces CARDDEMO-COMMAREA session state
// =============================================================================

/**
 * Authenticated user context stored in Zustand auth store.
 * Replaces CARDDEMO-COMMAREA fields passed between CICS programs.
 */
export interface AuthUser {
  user_id: string;
  user_type: UserType;
  first_name: string;
  last_name: string;
}

/**
 * Auth store state shape.
 */
export interface AuthState {
  token: string | null;
  user: AuthUser | null;
  isAuthenticated: boolean;
  login: (response: LoginResponse) => void;
  logout: () => void;
}
