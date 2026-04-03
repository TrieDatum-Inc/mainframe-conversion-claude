/**
 * API service layer for User Administration module.
 *
 * Centralises all HTTP calls to the FastAPI backend.
 * Mirrors COBOL CICS command patterns:
 *   listUsers()          ← COUSR00C STARTBR/READNEXT (browse)
 *   getUser()            ← COUSR02C/03C READ (lookup phase)
 *   createUser()         ← COUSR01C WRITE
 *   updateUser()         ← COUSR02C REWRITE
 *   deleteUser()         ← COUSR03C DELETE
 *
 * Admin auth is passed via X-User-Type: A header.
 * In production, replace with JWT Bearer token from the auth module.
 */
import type {
  UserCreateRequest,
  UserListParams,
  UserListResponse,
  UserResponse,
  UserUpdateRequest,
} from '@/types/user';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

/**
 * Default headers.  X-User-Type: A satisfies the admin-only requirement
 * from the require_admin FastAPI dependency (maps to COADM01C admin-only access).
 *
 * TODO: Replace with real JWT auth token when auth module is integrated.
 */
function getHeaders(): HeadersInit {
  return {
    'Content-Type': 'application/json',
    'X-User-Type': 'A',
  };
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({ detail: response.statusText }));
    const message =
      typeof errorBody.detail === 'string'
        ? errorBody.detail
        : Array.isArray(errorBody.detail)
          ? errorBody.detail.map((e: { msg: string }) => e.msg).join('; ')
          : response.statusText;
    throw new ApiError(message, response.status);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * GET /api/users — COUSR00C User List
 *
 * Fetches one page of users ordered by user_id (VSAM KSDS key order).
 * Maps to COUSR00C PROCESS-PAGE-FORWARD with STARTBR/READNEXT.
 */
export async function listUsers(params: UserListParams = {}): Promise<UserListResponse> {
  const query = new URLSearchParams();
  if (params.page) query.set('page', params.page.toString());
  if (params.page_size) query.set('page_size', params.page_size.toString());
  if (params.search_user_id) query.set('search_user_id', params.search_user_id);

  const response = await fetch(`${API_BASE}/api/users?${query.toString()}`, {
    headers: getHeaders(),
  });
  return handleResponse<UserListResponse>(response);
}

/**
 * GET /api/users/{user_id} — COUSR02C/03C lookup phase
 *
 * Fetches user for display.  Used as:
 * - Phase 1 of update flow (COUSR02C PROCESS-ENTER-KEY)
 * - Phase 1 of delete confirmation (COUSR03C PROCESS-ENTER-KEY)
 *
 * Throws ApiError(404) when user not found (DFHRESP(NOTFND)).
 */
export async function getUser(userId: string): Promise<UserResponse> {
  const response = await fetch(`${API_BASE}/api/users/${encodeURIComponent(userId)}`, {
    headers: getHeaders(),
  });
  return handleResponse<UserResponse>(response);
}

/**
 * POST /api/users — COUSR01C Add User
 *
 * Creates a new user.  All fields mandatory.
 * Throws ApiError(409) on duplicate user_id (DFHRESP(DUPKEY)).
 * Throws ApiError(422) on validation error (Pydantic/COBOL validation).
 */
export async function createUser(data: UserCreateRequest): Promise<UserResponse> {
  const response = await fetch(`${API_BASE}/api/users`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(data),
  });
  return handleResponse<UserResponse>(response);
}

/**
 * PUT /api/users/{user_id} — COUSR02C Update User
 *
 * Updates an existing user.
 * Throws ApiError(404) when user not found.
 * Throws ApiError(422) when no fields changed
 *   ('Please modify to update ...' — COUSR02C no-change guard).
 */
export async function updateUser(
  userId: string,
  data: UserUpdateRequest,
): Promise<UserResponse> {
  const response = await fetch(`${API_BASE}/api/users/${encodeURIComponent(userId)}`, {
    method: 'PUT',
    headers: getHeaders(),
    body: JSON.stringify(data),
  });
  return handleResponse<UserResponse>(response);
}

/**
 * DELETE /api/users/{user_id} — COUSR03C Delete User (phase 2: PF5 confirm)
 *
 * Permanently deletes a user.
 * Two-phase pattern: UI must have shown confirmation before calling this.
 * Throws ApiError(404) when user not found.
 */
export async function deleteUser(userId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/users/${encodeURIComponent(userId)}`, {
    method: 'DELETE',
    headers: getHeaders(),
  });
  return handleResponse<void>(response);
}
