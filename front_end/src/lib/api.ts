/**
 * Typed API client for the CardDemo backend.
 *
 * All HTTP calls to /api/v1/* are centralized here.
 * Error responses are normalized to ApiErrorResponse format.
 *
 * COBOL origin: Replaces CICS SEND MAP / RECEIVE MAP interactions.
 * Each function maps to one CICS transaction or program paragraph.
 */

import axios, { AxiosError } from 'axios';
import type {
  ApiErrorResponse,
  MessageResponse,
  PaginationParams,
  TransactionTypeCreateRequest,
  TransactionTypeListParams,
  TransactionTypeListResponse,
  TransactionTypeResponse,
  TransactionTypeUpdateRequest,
  UserCreateRequest,
  UserListResponse,
  UserResponse,
  UserUpdateRequest,
} from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/** Create an axios instance with base URL and JSON headers. */
const apiClient = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
});

/** Attach the JWT Bearer token from sessionStorage to every request. */
apiClient.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const stored = sessionStorage.getItem('carddemo-auth');
    if (stored) {
      const parsed = JSON.parse(stored);
      const token = parsed?.state?.token;
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
  }
  return config;
});

/** Normalize Axios errors to ApiErrorResponse. */
function extractError(err: unknown): ApiErrorResponse {
  if (err instanceof AxiosError && err.response?.data?.detail) {
    const detail = err.response.data.detail;
    if (typeof detail === 'object' && detail.error_code) {
      return detail as ApiErrorResponse;
    }
    return {
      error_code: 'API_ERROR',
      message: String(detail),
      details: [],
    };
  }
  return {
    error_code: 'NETWORK_ERROR',
    message: 'Network error — please check your connection',
    details: [],
  };
}

// =============================================================================
// User Management API — COUSR00C / COUSR01C / COUSR02C / COUSR03C
// =============================================================================

/**
 * GET /api/v1/users
 * COBOL origin: COUSR00C POPULATE-USER-DATA (STARTBR/READNEXT browse)
 */
export async function listUsers(params: PaginationParams): Promise<UserListResponse> {
  const { page, page_size, user_id_filter } = params;
  const query: Record<string, string | number> = { page, page_size };
  if (user_id_filter) query.user_id_filter = user_id_filter;

  const resp = await apiClient.get<UserListResponse>('/users', { params: query });
  return resp.data;
}

/**
 * GET /api/v1/users/{user_id}
 * COBOL origin: COUSR02C PROCESS-ENTER-KEY → READ-USER-SEC-FILE
 */
export async function getUser(userId: string): Promise<UserResponse> {
  const resp = await apiClient.get<UserResponse>(`/users/${encodeURIComponent(userId)}`);
  return resp.data;
}

/**
 * POST /api/v1/users
 * COBOL origin: COUSR01C PROCESS-ENTER-KEY → WRITE-USER-SEC-FILE
 */
export async function createUser(data: UserCreateRequest): Promise<UserResponse> {
  const resp = await apiClient.post<UserResponse>('/users', data);
  return resp.data;
}

/**
 * PUT /api/v1/users/{user_id}
 * COBOL origin: COUSR02C UPDATE-USER-INFO → UPDATE-USER-SEC-FILE
 */
export async function updateUser(
  userId: string,
  data: UserUpdateRequest
): Promise<UserResponse> {
  const resp = await apiClient.put<UserResponse>(
    `/users/${encodeURIComponent(userId)}`,
    data
  );
  return resp.data;
}

/**
 * DELETE /api/v1/users/{user_id}
 * COBOL origin: COUSR03C DELETE-USER-INFO → DELETE-USER-SEC-FILE
 * Bug fix: COUSR03C said 'Unable to Update User' on delete failure — corrected.
 */
export async function deleteUser(userId: string): Promise<MessageResponse> {
  const resp = await apiClient.delete<MessageResponse>(
    `/users/${encodeURIComponent(userId)}`
  );
  return resp.data;
}

// =============================================================================
// Transaction Type Management API — COTRTLIC (CTLI) + COTRTUPC (CTTU)
// All endpoints are admin-only (user_type='A' JWT claim required).
// =============================================================================

/**
 * GET /api/v1/transaction-types
 * COBOL origin: COTRTLIC 8000-READ-FORWARD / 8100-READ-BACKWARDS (cursor-based paging)
 * Replaced by standard page/page_size pagination.
 * Default page_size=7 matches COTRTLIC WS-MAX-SCREEN-LINES=7.
 */
export async function listTransactionTypes(
  params: TransactionTypeListParams = {}
): Promise<TransactionTypeListResponse> {
  const { page = 1, page_size = 7, type_code_filter, description_filter } = params;
  const query: Record<string, string | number> = { page, page_size };
  if (type_code_filter) query.type_code_filter = type_code_filter;
  if (description_filter) query.description_filter = description_filter;

  const resp = await apiClient.get<TransactionTypeListResponse>('/transaction-types', {
    params: query,
  });
  return resp.data;
}

/**
 * GET /api/v1/transaction-types/{type_code}
 * COBOL origin: COTRTUPC 9000-READ-TRANTYPE → 9100-GET-TRANSACTION-TYPE
 * Fetches a single transaction type for the detail/edit form (CTRTUPA).
 * Returns the updated_at timestamp needed for optimistic locking on PUT.
 */
export async function getTransactionType(typeCode: string): Promise<TransactionTypeResponse> {
  const resp = await apiClient.get<TransactionTypeResponse>(
    `/transaction-types/${encodeURIComponent(typeCode)}`
  );
  return resp.data;
}

/**
 * POST /api/v1/transaction-types
 * COBOL origin: COTRTUPC 9700-INSERT-RECORD
 * Creates a new transaction type (TTUP-CREATE-NEW-RECORD state → PF5).
 */
export async function createTransactionType(
  data: TransactionTypeCreateRequest
): Promise<TransactionTypeResponse> {
  const resp = await apiClient.post<TransactionTypeResponse>('/transaction-types', data);
  return resp.data;
}

/**
 * PUT /api/v1/transaction-types/{type_code}
 * COBOL origin: COTRTLIC 9200-UPDATE-RECORD (inline edit, 'U' + PF10)
 *              COTRTUPC 9600-WRITE-PROCESSING (UPDATE path, PF5)
 * Only description is editable. Requires optimistic_lock_version to detect concurrent edits.
 */
export async function updateTransactionType(
  typeCode: string,
  data: TransactionTypeUpdateRequest
): Promise<TransactionTypeResponse> {
  const resp = await apiClient.put<TransactionTypeResponse>(
    `/transaction-types/${encodeURIComponent(typeCode)}`,
    data
  );
  return resp.data;
}

/**
 * DELETE /api/v1/transaction-types/{type_code}
 * COBOL origin: COTRTLIC 9300-DELETE-RECORD (inline delete, 'D' + PF10)
 *              COTRTUPC 9800-DELETE-PROCESSING (PF4 confirm → PF4)
 * Returns 204 on success. Returns 409 if transactions reference this type (SQLCODE -532).
 */
export async function deleteTransactionType(typeCode: string): Promise<void> {
  await apiClient.delete(`/transaction-types/${encodeURIComponent(typeCode)}`);
}

export { extractError };
