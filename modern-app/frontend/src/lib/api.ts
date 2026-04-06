/**
 * Centralized API client for the Authorization module.
 *
 * All requests include the JWT Bearer token from localStorage.
 * Base URL points to the FastAPI backend.
 */

import type {
  AuthorizationDetail,
  AuthorizationListResponse,
  AuthorizationProcessRequest,
  AuthorizationProcessResponse,
  FraudActionRequest,
  FraudActionResponse,
  PaginatedDetailResponse,
  PurgeRequest,
  PurgeResponse,
} from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

// ---------------------------------------------------------------------------
// HTTP helpers
// ---------------------------------------------------------------------------

function getAuthHeaders(): HeadersInit {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    const message =
      errorBody.detail ?? `HTTP ${response.status}: ${response.statusText}`;
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Authorization Processing (COPAUA0C)
// ---------------------------------------------------------------------------

export async function processAuthorization(
  request: AuthorizationProcessRequest
): Promise<AuthorizationProcessResponse> {
  const response = await fetch(`${BASE_URL}/authorizations/process`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  });
  return handleResponse<AuthorizationProcessResponse>(response);
}

// ---------------------------------------------------------------------------
// Authorization Viewing (COPAUS0C + COPAUS1C)
// ---------------------------------------------------------------------------

export async function listAuthorizations(
  page = 1,
  pageSize = 20,
  accountId?: string
): Promise<AuthorizationListResponse> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  if (accountId) {
    params.set("account_id", accountId);
  }

  const response = await fetch(
    `${BASE_URL}/authorizations?${params.toString()}`,
    { headers: getAuthHeaders() }
  );
  return handleResponse<AuthorizationListResponse>(response);
}

export async function getAccountAuthorizations(
  accountId: string,
  page = 1
): Promise<PaginatedDetailResponse> {
  const response = await fetch(
    `${BASE_URL}/authorizations/${accountId}?page=${page}`,
    { headers: getAuthHeaders() }
  );
  return handleResponse<PaginatedDetailResponse>(response);
}

export async function getAuthorizationDetail(
  accountId: string,
  detailId: number
): Promise<AuthorizationDetail> {
  const response = await fetch(
    `${BASE_URL}/authorizations/${accountId}/details/${detailId}`,
    { headers: getAuthHeaders() }
  );
  return handleResponse<AuthorizationDetail>(response);
}

// ---------------------------------------------------------------------------
// Fraud Management (COPAUS2C)
// ---------------------------------------------------------------------------

export async function toggleFraud(
  detailId: number,
  request: FraudActionRequest
): Promise<FraudActionResponse> {
  const response = await fetch(
    `${BASE_URL}/authorizations/details/${detailId}/fraud`,
    {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(request),
    }
  );
  return handleResponse<FraudActionResponse>(response);
}

// ---------------------------------------------------------------------------
// Purge (CBPAUP0C — admin only)
// ---------------------------------------------------------------------------

export async function purgeAuthorizations(
  request: PurgeRequest
): Promise<PurgeResponse> {
  const response = await fetch(`${BASE_URL}/authorizations/purge`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  });
  return handleResponse<PurgeResponse>(response);
}
