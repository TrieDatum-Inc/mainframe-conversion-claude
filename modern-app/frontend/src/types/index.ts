/**
 * TypeScript types for the CardDemo User Administration module.
 *
 * Mirrors the backend Pydantic schemas and COBOL data fields:
 *   user_id   → SEC-USR-ID   X(8)
 *   first_name → SEC-USR-FNAME X(20)
 *   last_name  → SEC-USR-LNAME X(20)
 *   user_type  → SEC-USR-TYPE  X(1) — 'A' | 'U'
 */

/** User type values (COBOL 88-level: A=Admin, U=Regular) */
export type UserType = "A" | "U";

/** A single user record as returned by the API (no password fields). */
export interface User {
  user_id: string;
  first_name: string;
  last_name: string;
  user_type: UserType;
  created_at: string;
  updated_at: string;
}

/** Paginated list response from GET /api/users */
export interface UserListResponse {
  users: User[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/** Request body for POST /api/users (COUSR01C — add user) */
export interface CreateUserPayload {
  user_id: string;
  first_name: string;
  last_name: string;
  password: string;
  user_type: UserType;
}

/** Request body for PUT /api/users/:id (COUSR02C — update user) */
export interface UpdateUserPayload {
  first_name: string;
  last_name: string;
  user_type: UserType;
  password?: string;
}

/** Response from DELETE /api/users/:id (COUSR03C — delete user) */
export interface DeleteUserResponse {
  message: string;
  user_id: string;
}

/** Generic API error shape */
export interface ApiError {
  detail: string | { msg: string; loc: string[] }[];
}

/** Pagination query parameters for user list */
export interface UserListParams {
  page?: number;
  page_size?: number;
  user_id?: string;
}
