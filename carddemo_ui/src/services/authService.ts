/**
 * Authentication service — wraps POST /api/v1/auth/login.
 * Derived from COSGN00C (CICS transaction CC00).
 */
import client, { TOKEN_KEY, USER_KEY } from './apiClient';
import type { LoginRequest, TokenResponse, AuthUser } from '@/lib/types/api';

export const authService = {
  /**
   * Authenticate user and store JWT token.
   * Maps to COSGN00C PROCESS-ENTER-KEY paragraph.
   */
  async login(request: LoginRequest): Promise<TokenResponse> {
    const { data } = await client.post<TokenResponse>('/auth/login', request);

    // Store token and user info
    if (typeof window !== 'undefined') {
      localStorage.setItem(TOKEN_KEY, data.access_token);
      const user: AuthUser = {
        user_id: data.user_id,
        user_type: data.user_type,
        first_name: data.first_name,
        last_name: data.last_name,
        is_admin: data.user_type === 'A',
      };
      localStorage.setItem(USER_KEY, JSON.stringify(user));
    }

    return data;
  },

  /**
   * Clear session data.
   */
  logout(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
    }
  },

  /**
   * Retrieve current user from localStorage.
   */
  getCurrentUser(): AuthUser | null {
    if (typeof window === 'undefined') return null;
    const stored = localStorage.getItem(USER_KEY);
    if (!stored) return null;
    try {
      return JSON.parse(stored) as AuthUser;
    } catch {
      return null;
    }
  },

  /**
   * Check if user is authenticated.
   */
  isAuthenticated(): boolean {
    if (typeof window === 'undefined') return false;
    return !!localStorage.getItem(TOKEN_KEY);
  },

  /**
   * Check if user has admin role.
   */
  isAdmin(): boolean {
    const user = this.getCurrentUser();
    return user?.user_type === 'A';
  },
};
