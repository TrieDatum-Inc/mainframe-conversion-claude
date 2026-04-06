/**
 * Typed API client for all CardDemo REST API calls.
 *
 * COBOL origin: Replaces all CICS FILE CONTROL commands, EXEC SQL statements,
 * and CICS SEND/RECEIVE MAP interactions with typed HTTP calls.
 *
 * The Authorization header with the JWT token replaces the COMMAREA
 * that CICS programs passed to identify the authenticated user.
 *
 * Error handling: API errors are unwrapped from the standard
 * {"error_code": ..., "message": ..., "details": [...]} envelope
 * and re-thrown as ApiClientError instances with structured data.
 */

import type { ApiError, LoginRequest, LoginResponse, MessageResponse, User } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_PREFIX = '/api/v1';

/**
 * Structured API error — provides error_code for programmatic handling
 * and message for display in the ERRMSG bar (row 23 equivalent).
 */
export class ApiClientError extends Error {
  constructor(
    public readonly error_code: string,
    message: string,
    public readonly details: ApiError['details'] = [],
    public readonly status: number = 0
  ) {
    super(message);
    this.name = 'ApiClientError';
  }
}

/**
 * Get the stored JWT token for request authorization.
 * Reads from localStorage where the Zustand store persists it.
 * Returns null in SSR context (localStorage is not available server-side).
 */
function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null;
  try {
    const stored = localStorage.getItem('carddemo_auth');
    if (!stored) return null;
    const parsed = JSON.parse(stored);
    return parsed?.state?.token ?? null;
  } catch {
    return null;
  }
}

/**
 * Core fetch wrapper with auth injection and error normalization.
 */
async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null
): Promise<T> {
  const authToken = token ?? getStoredToken();

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  if (authToken) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${authToken}`;
  }

  const url = `${API_BASE_URL}${API_PREFIX}${path}`;
  const response = await fetch(url, { ...options, headers });

  // Parse response body (always JSON from our API)
  let body: unknown;
  try {
    body = await response.json();
  } catch {
    body = { error_code: 'PARSE_ERROR', message: 'Failed to parse API response', details: [] };
  }

  if (!response.ok) {
    const error = body as Partial<ApiError>;
    throw new ApiClientError(
      error.error_code ?? `HTTP_${response.status}`,
      error.message ?? `HTTP error ${response.status}`,
      error.details ?? [],
      response.status
    );
  }

  return body as T;
}

// =============================================================================
// Authentication API
// Maps COSGN00C (Transaction: CC00) → /api/v1/auth/*
// =============================================================================

export const authApi = {
  /**
   * POST /api/v1/auth/login
   *
   * COBOL origin: COSGN00C PROCESS-ENTER-KEY paragraph.
   * Replaces EXEC CICS READ DATASET(USRSEC) + plain-text password comparison.
   * Returns JWT token and redirect_to URL (replaces CICS XCTL routing).
   */
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    return apiFetch<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  },

  /**
   * POST /api/v1/auth/logout
   *
   * COBOL origin: COSGN00C RETURN-TO-PREV-SCREEN (PF3 path).
   * Replaces bare EXEC CICS RETURN (no TRANSID — session ends).
   */
  logout: async (token: string): Promise<MessageResponse> => {
    return apiFetch<MessageResponse>(
      '/auth/logout',
      { method: 'POST' },
      token
    );
  },

  /**
   * GET /api/v1/auth/me
   *
   * No COBOL equivalent — new capability.
   * Returns profile of the currently authenticated user.
   */
  me: async (token: string): Promise<User> => {
    return apiFetch<User>('/auth/me', { method: 'GET' }, token);
  },
};
