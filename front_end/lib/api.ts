/**
 * Centralized API service layer for CardDemo.
 *
 * Maps CICS EXEC commands to HTTP calls:
 *   EXEC CICS READ DATASET('USRSEC')  → login()
 *   EXEC CICS RETURN (no TRANSID)     → logout()
 *   EXEC CICS SEND MAP('COMEN1A')     → getMainMenu()
 *   EXEC CICS SEND MAP('COADM1A')     → getAdminMenu()
 *   EXEC CICS XCTL                    → navigateMainMenu() / navigateAdminMenu()
 */
import type {
  LoginFormData,
  LoginResponse,
  MenuResponse,
  NavigateResponse,
  UserInfo,
} from "@/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ============================================================
// Token management — replaces CARDDEMO-COMMAREA persistence
// ============================================================

const TOKEN_KEY = "carddemo_token";
const USER_KEY = "carddemo_user";

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function storeToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function removeToken(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getStoredUser(): UserInfo | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as UserInfo;
  } catch {
    return null;
  }
}

export function storeUser(user: UserInfo): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

// ============================================================
// HTTP helper
// ============================================================

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getStoredToken();
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({
      detail: "Network error",
    }));
    throw { status: response.status, ...errorData };
  }

  return response.json() as Promise<T>;
}

// ============================================================
// Auth API — COSGN00C equivalents
// ============================================================

/**
 * Login — maps COSGN00C PROCESS-ENTER-KEY + READ-USER-SEC-FILE.
 *
 * BR-003: user_id and password are uppercased before sending
 *         (mirrors FUNCTION UPPER-CASE in COBOL).
 * BR-006: response.redirect_to determines which dashboard to show.
 */
export async function login(data: LoginFormData): Promise<LoginResponse> {
  const response = await request<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({
      user_id: data.user_id.toUpperCase().trim(),
      password: data.password.toUpperCase().trim(),
    }),
  });

  // Persist token and user info (replaces COMMAREA state)
  storeToken(response.access_token);
  storeUser(response.user);

  return response;
}

/**
 * Logout — maps COSGN00C PF3 handler (SEND-PLAIN-TEXT + RETURN no TRANSID).
 * Client discards the JWT token.
 */
export async function logout(): Promise<void> {
  try {
    await request("/auth/logout", { method: "POST" });
  } finally {
    removeToken();
  }
}

/**
 * Get current user info from JWT claims (COMMAREA equivalent).
 */
export async function getCurrentUser(): Promise<UserInfo> {
  return request<UserInfo>("/auth/me");
}

// ============================================================
// Menu API — COMEN01C / COADM01C equivalents
// ============================================================

/**
 * Get main menu — maps COMEN01C SEND-MENU-SCREEN + BUILD-MENU-OPTIONS.
 * Returns the 11 menu options from COMEN02Y table.
 */
export async function getMainMenu(): Promise<MenuResponse> {
  return request<MenuResponse>("/menu/main");
}

/**
 * Navigate main menu — maps COMEN01C PROCESS-ENTER-KEY + XCTL.
 * Returns the target route for the selected option.
 */
export async function navigateMainMenu(
  option: number
): Promise<NavigateResponse> {
  return request<NavigateResponse>("/menu/main/navigate", {
    method: "POST",
    body: JSON.stringify({ option }),
  });
}

/**
 * Get admin menu — maps COADM01C SEND-MENU-SCREEN + BUILD-MENU-OPTIONS.
 * Returns the 6 admin options from COADM02Y table.
 */
export async function getAdminMenu(): Promise<MenuResponse> {
  return request<MenuResponse>("/menu/admin");
}

/**
 * Navigate admin menu — maps COADM01C PROCESS-ENTER-KEY + XCTL.
 */
export async function navigateAdminMenu(
  option: number
): Promise<NavigateResponse> {
  return request<NavigateResponse>("/menu/admin/navigate", {
    method: "POST",
    body: JSON.stringify({ option }),
  });
}
