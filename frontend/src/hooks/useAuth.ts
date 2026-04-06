/**
 * useAuth hook — convenience wrapper around the auth store.
 *
 * COBOL origin: Replaces CARDDEMO-COMMAREA access patterns in CICS programs.
 * Every COBOL program that needed user context had to:
 *   MOVE DFHCOMMAREA TO CARDDEMO-COMMAREA
 *   MOVE CDEMO-USER-ID TO WS-USER-ID
 *   IF CDEMO-USRTYP-ADMIN: ...
 *
 * This hook provides the same information from the Zustand auth store.
 */

'use client';

import { useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/auth-store';
import { authApi, ApiClientError } from '@/lib/api-client';
import type { LoginRequest } from '@/types';

export function useAuth() {
  const router = useRouter();
  const { token, user, isAuthenticated, login, logout: storeLogout } = useAuthStore();

  /**
   * Perform login API call and handle redirect.
   *
   * COBOL: COSGN00C PROCESS-ENTER-KEY → XCTL to appropriate menu.
   */
  const performLogin = useCallback(
    async (credentials: LoginRequest): Promise<{ success: boolean; error?: string }> => {
      try {
        const response = await authApi.login(credentials);
        login(response);

        // Set cookie for middleware protection
        if (typeof document !== 'undefined') {
          document.cookie = `carddemo_auth_token=${response.access_token}; path=/; max-age=3600; SameSite=Strict`;
        }

        router.push(response.redirect_to);
        return { success: true };
      } catch (error) {
        if (error instanceof ApiClientError) {
          return { success: false, error: error.message };
        }
        return { success: false, error: 'An unexpected error occurred' };
      }
    },
    [login, router]
  );

  /**
   * Perform logout — call API and clear local state.
   *
   * COBOL: COSGN00C RETURN-TO-PREV-SCREEN (PF3) → CCDA-MSG-THANK-YOU → bare RETURN.
   */
  const performLogout = useCallback(async () => {
    if (token) {
      try {
        await authApi.logout(token);
      } catch {
        // Ignore API errors on logout — clear state regardless
      }
    }

    storeLogout();

    if (typeof document !== 'undefined') {
      document.cookie = 'carddemo_auth_token=; path=/; max-age=0';
    }

    router.push('/login');
  }, [token, storeLogout, router]);

  return {
    user,
    token,
    isAuthenticated,
    isAdmin: user?.user_type === 'A',
    performLogin,
    performLogout,
  };
}
