/**
 * Typed API client for the CardDemo backend.
 *
 * Wraps fetch with:
 *   - Base URL from NEXT_PUBLIC_API_URL env var
 *   - Automatic Authorization: Bearer header injection from localStorage
 *   - Structured error parsing matching the backend's ErrorResponse envelope
 */

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * Structured API error matching the backend ErrorResponse schema.
 */
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly errorCode: string,
    message: string,
    public readonly details: unknown[] = []
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * Retrieve the stored access token from localStorage (client-side only).
 */
function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("carddemo_token");
}

/**
 * Build request headers, injecting Authorization if a token is present.
 */
function buildHeaders(extra?: Record<string, string>): HeadersInit {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...extra,
  };
  const token = getStoredToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

/**
 * Parse and throw an ApiError from a non-OK response.
 */
async function handleErrorResponse(response: Response): Promise<never> {
  let errorCode = "HTTP_ERROR";
  let message = `HTTP ${response.status}`;
  let details: unknown[] = [];

  try {
    const body = await response.json();
    errorCode = body.error_code ?? errorCode;
    message = body.message ?? message;
    details = body.details ?? details;
  } catch {
    // Non-JSON error body — use defaults
  }

  throw new ApiError(response.status, errorCode, message, details);
}

/**
 * POST request to the API.
 *
 * Usage:
 *   const response = await api.post<LoginResponse>("/api/v1/auth/login", { user_id, password })
 */
async function post<T>(
  path: string,
  body: unknown,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: buildHeaders(
      options?.headers as Record<string, string> | undefined
    ),
    body: JSON.stringify(body),
    ...options,
  });

  if (!response.ok) {
    await handleErrorResponse(response);
  }

  // 204 No Content has no body
  if (response.status === 204) {
    return undefined as unknown as T;
  }

  return response.json() as Promise<T>;
}

/**
 * GET request to the API.
 */
async function get<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "GET",
    headers: buildHeaders(
      options?.headers as Record<string, string> | undefined
    ),
    ...options,
  });

  if (!response.ok) {
    await handleErrorResponse(response);
  }

  return response.json() as Promise<T>;
}

export const api = { post, get };
