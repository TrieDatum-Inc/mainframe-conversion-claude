/**
 * Client-side JWT helpers.
 *
 * COBOL origin: Replaces COMMAREA inspection for user type and session checks.
 * In COBOL, programs checked CDEMO-USRTYP-ADMIN to determine routing.
 * Here we decode the JWT claim `user_type` for the same purpose.
 */

import { AuthUser } from "@/types/auth";

const TOKEN_KEY = "carddemo_token";
const USER_KEY = "carddemo_user";

/**
 * Decode a JWT payload without verifying the signature.
 * Signature verification happens server-side; the frontend only needs the claims.
 */
export function decodeTokenPayload(token: string): Record<string, unknown> | null {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const payloadBase64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const decoded = atob(payloadBase64);
    return JSON.parse(decoded);
  } catch {
    return null;
  }
}

/**
 * Check whether a stored JWT is still within its expiry window.
 */
export function isTokenExpired(token: string): boolean {
  const payload = decodeTokenPayload(token);
  if (!payload || typeof payload.exp !== "number") return true;
  // Add a 30-second clock skew buffer
  return Date.now() / 1000 > payload.exp - 30;
}

/**
 * Persist the access token and user identity to localStorage.
 *
 * SECURITY NOTE — deliberate trade-off (security review finding #8):
 * Tokens are stored in localStorage for simplicity in this demo application.
 * localStorage is readable by any JavaScript on the page, which means an XSS
 * vulnerability could extract the token (stolen session).
 *
 * Production upgrade path: store the access token in an httpOnly, Secure,
 * SameSite=Strict cookie set by the API server on the login response. The
 * browser sends it automatically on every request — no JavaScript access to
 * the raw token at all, eliminating the XSS token-theft vector.
 * See security specification section 4.3 for the cookie configuration.
 *
 * XSS mitigations currently in place (reducing but not eliminating the risk):
 *   - React JSX auto-escapes all dynamic content (no dangerouslySetInnerHTML)
 *   - Content-Security-Policy header restricts script sources to 'self'
 *   - All user-supplied strings rendered as React text nodes (auto-escaped)
 */
export function storeAuthData(token: string, user: AuthUser): void {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

/**
 * Clear all auth data from localStorage.
 */
export function clearAuthData(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

/**
 * Retrieve the stored token, or null if absent or expired.
 */
export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  const token = localStorage.getItem(TOKEN_KEY);
  if (!token) return null;
  if (isTokenExpired(token)) {
    clearAuthData();
    return null;
  }
  return token;
}

/**
 * Retrieve the stored user identity, or null if absent.
 */
export function getStoredUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

/**
 * Check whether the current user has the Admin role.
 *
 * COBOL origin: Replaces CDEMO-USRTYP-ADMIN condition in downstream programs.
 */
export function isAdmin(user: AuthUser | null): boolean {
  return user?.userType === "A";
}
