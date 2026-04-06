/**
 * Authentication Zustand store.
 *
 * COBOL origin: Replaces CARDDEMO-COMMAREA session state that CICS programs
 * passed between each other via EXEC CICS XCTL COMMAREA and RETURN COMMAREA.
 *
 * In COBOL, state was maintained in a 1024-byte COMMAREA structure including:
 *   CDEMO-USER-ID    (X(8))  → user.user_id
 *   CDEMO-USER-TYPE  (X(1))  → user.user_type
 *   CDEMO-USER-FNAME (X(20)) → user.first_name
 *   CDEMO-USER-LNAME (X(20)) → user.last_name
 *   CDEMO-SIGNED-ON-FLAG     → isAuthenticated
 *
 * The JWT token replaces the COMMAREA as the stateless authentication carrier.
 * localStorage persistence allows the session to survive page refreshes
 * (unlike CICS where the COMMAREA was lost on terminal disconnect).
 */

'use client';

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { AuthState, AuthUser, LoginResponse } from '@/types';

const AUTH_STORAGE_KEY = 'carddemo_auth';

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,

      /**
       * Store JWT token and user info after successful login.
       *
       * COBOL origin: Replaces COSGN00C PROCESS-ENTER-KEY paragraph that populated
       * CARDDEMO-COMMAREA with authenticated user data before CICS XCTL.
       *
       * Maps these COMMAREA fields:
       *   CDEMO-USER-ID    ← loginResponse.user_id
       *   CDEMO-USER-TYPE  ← loginResponse.user_type
       *   CDEMO-USER-FNAME ← loginResponse.first_name
       *   CDEMO-USER-LNAME ← loginResponse.last_name
       *   CDEMO-SIGNED-ON-FLAG = TRUE
       */
      login: (response: LoginResponse) => {
        const user: AuthUser = {
          user_id: response.user_id,
          user_type: response.user_type,
          first_name: response.first_name,
          last_name: response.last_name,
        };

        set({
          token: response.access_token,
          user,
          isAuthenticated: true,
        });
      },

      /**
       * Clear auth state on logout.
       *
       * COBOL origin: Replaces COSGN00C RETURN-TO-PREV-SCREEN paragraph (PF3):
       *   bare EXEC CICS RETURN (no TRANSID) → session ends, COMMAREA cleared.
       * Modern: token and user cleared from store and localStorage.
       */
      logout: () => {
        set({
          token: null,
          user: null,
          isAuthenticated: false,
        });
      },
    }),
    {
      name: AUTH_STORAGE_KEY,
      storage: createJSONStorage(() => localStorage),
      // Only persist the data fields; actions are not serializable
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

/**
 * Convenience hook to get the current auth token.
 * Used by the API client to inject the Authorization header.
 */
export function useAuthToken(): string | null {
  return useAuthStore((state) => state.token);
}

/**
 * Convenience hook to get the current user.
 */
export function useCurrentUser(): AuthUser | null {
  return useAuthStore((state) => state.user);
}

/**
 * Convenience hook to check if user is an admin.
 * COBOL origin: Replaces CDEMO-USRTYP-ADMIN 88-level condition check.
 */
export function useIsAdmin(): boolean {
  const user = useAuthStore((state) => state.user);
  return user?.user_type === 'A';
}
