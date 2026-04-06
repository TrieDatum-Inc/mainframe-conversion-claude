/**
 * Typed API client for the CardDemo Authorization module.
 * Wraps all backend endpoints with proper TypeScript types.
 * Handles authentication headers and error responses.
 *
 * Endpoints map to COBOL programs:
 *   getAuthorizationSummaries    → COPAUS0C (IMS GU PAUTSUM0 browse)
 *   getAuthorizationDetails      → COPAUS0C (IMS GNP PAUTDTL1, 5 per page)
 *   getAuthorizationDetail       → COPAUS1C (IMS GNP qualified)
 *   toggleFraudFlag              → COPAUS1C PF5 → COPAUS2C LINK
 *   getFraudLogs                 → DB2 CARDDEMO.AUTHFRDS read
 */

import type {
  ApiError,
  AuthDetailResponse,
  AuthFraudLogResponse,
  AuthListResponse,
  FraudToggleRequest,
  FraudToggleResponse,
  PaginatedResponse,
  AuthSummaryResponse,
} from '@/types/authorization';

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
const API_V1 = `${API_BASE_URL}/api/v1`;

/**
 * Get JWT token from localStorage.
 * Replaces: CARDDEMO-COMMAREA auth token passing between CICS screens.
 */
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
}

/**
 * Build request headers with Authorization Bearer token.
 * Replaces: CICS EIBCALEN check + RACF user identity.
 */
function buildHeaders(additionalHeaders?: Record<string, string>): Headers {
  const headers = new Headers({
    'Content-Type': 'application/json',
    ...additionalHeaders,
  });
  const token = getAuthToken();
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  return headers;
}

/**
 * Parse API response, throwing structured error on non-2xx status.
 */
async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorData: ApiError;
    try {
      errorData = await response.json();
    } catch {
      errorData = {
        error_code: `HTTP_${response.status}`,
        message: response.statusText,
        details: [],
      };
    }
    throw new ApiClientError(response.status, errorData);
  }
  return response.json() as Promise<T>;
}

/**
 * Structured API error with HTTP status and error_code.
 * Use error.status and error.apiError for conditional UI handling.
 */
export class ApiClientError extends Error {
  constructor(
    public readonly status: number,
    public readonly apiError: ApiError,
  ) {
    super(apiError.message);
    this.name = 'ApiClientError';
  }
}

// ---------------------------------------------------------------------------
// Authorization Summary — replaces COPAUS0C IMS GU PAUTSUM0 browse
// ---------------------------------------------------------------------------

/**
 * GET /api/v1/authorizations
 * Paginated list of authorization summaries.
 * Replaces: COPAUS0C GATHER-DETAILS + PROCESS-PAGE-FORWARD.
 */
export async function getAuthorizationSummaries(params: {
  page?: number;
  pageSize?: number;
}): Promise<PaginatedResponse<AuthSummaryResponse>> {
  const { page = 1, pageSize = 5 } = params;
  const url = new URL(`${API_V1}/authorizations`);
  url.searchParams.set('page', String(page));
  url.searchParams.set('page_size', String(pageSize));

  const response = await fetch(url.toString(), {
    method: 'GET',
    headers: buildHeaders(),
  });
  return parseResponse<PaginatedResponse<AuthSummaryResponse>>(response);
}

/**
 * GET /api/v1/authorizations/{accountId}/details
 * Paginated authorization detail list for a specific account.
 * Replaces: COPAUS0C IMS GNP PAUTDTL1 (5 rows per screen page).
 * PF7/PF8 maps to page-1/page+1.
 */
export async function getAuthorizationDetails(
  accountId: number,
  params: { page?: number; pageSize?: number },
): Promise<AuthListResponse> {
  const { page = 1, pageSize = 5 } = params;
  const url = new URL(`${API_V1}/authorizations/${accountId}/details`);
  url.searchParams.set('page', String(page));
  url.searchParams.set('page_size', String(pageSize));

  const response = await fetch(url.toString(), {
    method: 'GET',
    headers: buildHeaders(),
  });
  return parseResponse<AuthListResponse>(response);
}

// ---------------------------------------------------------------------------
// Authorization Detail — replaces COPAUS1C CPVD transaction
// ---------------------------------------------------------------------------

/**
 * GET /api/v1/authorizations/detail/{authId}
 * Full detail view of single authorization.
 * Replaces: COPAUS1C POPULATE-AUTH-DETAILS paragraph.
 * Returns decline_reason from inline table (WS-DECLINE-REASON-TABLE).
 * fraud_status_display: 'FRAUD'/'REMOVED'/'' (AUTHFRDO field, RED on COPAU01).
 */
export async function getAuthorizationDetail(
  authId: number,
): Promise<AuthDetailResponse> {
  const response = await fetch(`${API_V1}/authorizations/detail/${authId}`, {
    method: 'GET',
    headers: buildHeaders(),
  });
  return parseResponse<AuthDetailResponse>(response);
}

// ---------------------------------------------------------------------------
// Fraud Toggle — replaces COPAUS1C PF5 → COPAUS2C LINK
// ---------------------------------------------------------------------------

/**
 * PUT /api/v1/authorizations/detail/{authId}/fraud
 * Toggle fraud status on an authorization.
 * 3-state cycle: N→F (confirm), F→R (remove), R→F (re-confirm).
 * Replaces: COPAUS1C MARK-AUTH-FRAUD + EXEC CICS LINK COPAUS2C.
 * Atomic: authorization_detail + auth_fraud_log updated together.
 */
export async function toggleFraudFlag(
  authId: number,
  request: FraudToggleRequest,
): Promise<FraudToggleResponse> {
  const response = await fetch(`${API_V1}/authorizations/detail/${authId}/fraud`, {
    method: 'PUT',
    headers: buildHeaders(),
    body: JSON.stringify(request),
  });
  return parseResponse<FraudToggleResponse>(response);
}

/**
 * GET /api/v1/authorizations/detail/{authId}/fraud-logs
 * Fraud audit trail — immutable log of all flag toggle actions.
 * Maps to DB2 CARDDEMO.AUTHFRDS rows.
 */
export async function getFraudLogs(
  authId: number,
): Promise<AuthFraudLogResponse[]> {
  const response = await fetch(
    `${API_V1}/authorizations/detail/${authId}/fraud-logs`,
    {
      method: 'GET',
      headers: buildHeaders(),
    },
  );
  return parseResponse<AuthFraudLogResponse[]>(response);
}
