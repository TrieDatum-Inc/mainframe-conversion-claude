/**
 * Authentication TypeScript types.
 *
 * COBOL origin: Maps fields from COSGN0A BMS map and CARDDEMO-COMMAREA.
 */

/**
 * Credentials submitted on the login form.
 * Maps BMS fields USRIDI (user_id) and PASSWDI (password) from COSGN0A.
 */
export interface LoginRequest {
  userId: string;
  password: string;
}

/**
 * Successful authentication response from POST /api/v1/auth/login.
 *
 * COBOL origin: Replaces the CARDDEMO-COMMAREA populated in COSGN00C
 * PROCESS-ENTER-KEY and passed to COADM01C or COMEN01C via CICS XCTL.
 * redirect_to replaces the XCTL target program decision.
 */
export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user_id: string;
  user_type: "A" | "U";
  first_name: string;
  last_name: string;
  redirect_to: string; // "/admin/menu" for type='A'; "/menu" for type='U'
}

/**
 * Decoded and stored user identity (stored in AuthContext / localStorage).
 *
 * COBOL origin: Subset of CARDDEMO-COMMAREA fields needed by the frontend:
 *   CDEMO-USER-ID, CDEMO-USER-TYPE, CDEMO-USER-FNAME, CDEMO-USER-LNAME.
 */
export interface AuthUser {
  userId: string;
  userType: "A" | "U";
  firstName: string;
  lastName: string;
}
