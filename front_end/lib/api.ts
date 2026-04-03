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
  AccountBalanceResponse,
  LoginFormData,
  LoginResponse,
  MenuResponse,
  NavigateResponse,
  PaymentResponse,
  ReportJobListResponse,
  ReportJobResponse,
  ReportSubmitRequest,
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

// ============================================================
// Reports API — CORPT00C equivalents
// ============================================================

/**
 * Submit a report job — maps CORPT00C SUBMIT-JOB-TO-INTRDR.
 * CONFIRM=Y is implicit: this function is called only after user confirms.
 *
 * Report types:
 *   monthly → MONTHLYI field selected (auto-calculates current month range)
 *   yearly  → YEARLYI field selected (auto-calculates current year range)
 *   custom  → CUSTOMI field selected + SDTMM/SDTDD/SDTYYYY + EDTMM/EDTDD/EDTYYYY
 */
export async function submitReport(
  data: ReportSubmitRequest
): Promise<ReportJobResponse> {
  return request<ReportJobResponse>("/reports", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * List recent report jobs — displays history of submitted reports.
 */
export async function listReports(
  limit = 20
): Promise<ReportJobListResponse> {
  return request<ReportJobListResponse>(`/reports?limit=${limit}`);
}

/**
 * Get a single report job by ID.
 */
export async function getReport(jobId: number): Promise<ReportJobResponse> {
  return request<ReportJobResponse>(`/reports/${jobId}`);
}

// ============================================================
// Payments API — COBIL00C equivalents
// ============================================================

/**
 * Phase 1: Look up account balance.
 * Maps COBIL00C READ-ACCTDAT-FILE + CURBALI display (lines 184-196).
 * User sees balance before confirming payment.
 *
 * BR-003: Returns info message if balance <= 0 ('You have nothing to pay...')
 */
export async function getAccountBalance(
  acctId: string
): Promise<AccountBalanceResponse> {
  return request<AccountBalanceResponse>(`/payments/balance/${acctId}`);
}

/**
 * Phase 2: Process bill payment — maps COBIL00C CONF-PAY-YES path.
 * CONFIRM=Y is implicit: caller only invokes this when user has confirmed.
 *
 * Atomic operation:
 *   1. Reads account (validates positive balance)
 *   2. Gets card number from cross-reference
 *   3. Generates next transaction ID (MAX+1)
 *   4. Creates type-02 payment transaction
 *   5. Zeros account balance
 *
 * BR-004: Always pays full balance (no partial payment).
 */
export async function processPayment(
  acctId: string
): Promise<PaymentResponse> {
  return request<PaymentResponse>(`/payments/${acctId}`, {
    method: "POST",
  });
}
