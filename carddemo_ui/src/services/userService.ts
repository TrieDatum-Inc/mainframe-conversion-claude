/**
 * User management service — wraps /api/v1/admin/users/* endpoints.
 * Derived from COUSR00C, COUSR01C, COUSR02C, COUSR03C.
 * All endpoints require admin access.
 */
import client from './apiClient';
import type {
  UserListResponse,
  UserResponse,
  UserCreateRequest,
  UserUpdateRequest,
} from '@/lib/types/api';

export interface ListUsersParams {
  cursor?: string;
  limit?: number;
  direction?: 'forward' | 'backward';
}

export const userService = {
  /**
   * GET /api/v1/admin/users
   * Derived from COUSR00C BROWSE-USERS (STARTBR USRSEC).
   */
  async listUsers(params: ListUsersParams = {}): Promise<UserListResponse> {
    const { data } = await client.get<UserListResponse>('/admin/users', { params });
    return data;
  },

  /**
   * GET /api/v1/admin/users/{user_id}
   * EXEC CICS READ FILE('USRSEC') INTO(SEC-USER-DATA) RIDFLD(user_id).
   */
  async getUser(userId: string): Promise<UserResponse> {
    const { data } = await client.get<UserResponse>(`/admin/users/${userId}`);
    return data;
  },

  /**
   * POST /api/v1/admin/users
   * Derived from COUSR01C PROCESS-ENTER-KEY → EXEC CICS WRITE FILE('USRSEC').
   */
  async createUser(request: UserCreateRequest): Promise<UserResponse> {
    const { data } = await client.post<UserResponse>('/admin/users', request);
    return data;
  },

  /**
   * PUT /api/v1/admin/users/{user_id}
   * Derived from COUSR02C PROCESS-ENTER-KEY → EXEC CICS REWRITE FILE('USRSEC').
   */
  async updateUser(userId: string, request: UserUpdateRequest): Promise<UserResponse> {
    const { data } = await client.put<UserResponse>(`/admin/users/${userId}`, request);
    return data;
  },

  /**
   * DELETE /api/v1/admin/users/{user_id}
   * Derived from COUSR03C PROCESS-ENTER-KEY → EXEC CICS DELETE FILE('USRSEC').
   */
  async deleteUser(userId: string): Promise<void> {
    await client.delete(`/admin/users/${userId}`);
  },
};
