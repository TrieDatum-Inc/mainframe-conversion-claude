/**
 * Zustand auth store — persists JWT token and user context.
 *
 * COBOL origin: Replaces CARDDEMO-COMMAREA passed between CICS programs.
 * The COMMAREA carried CDEMO-USER-ID (X(08)) and CDEMO-USER-TYPE (X(01))
 * between screens; Zustand holds equivalent state on the client.
 *
 * CDEMO-USER-ID   X(08) → AuthUser.user_id
 * CDEMO-USER-TYPE X(01) → AuthUser.user_type ('A' or 'U')
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { AuthStore, AuthUser } from '@/types';

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      setAuth: (user: AuthUser, token: string) =>
        set({ user, token, isAuthenticated: true }),

      clearAuth: () =>
        set({ user: null, token: null, isAuthenticated: false }),
    }),
    {
      name: 'carddemo-auth',
      // Store in sessionStorage (cleared on tab close — better security than localStorage)
      storage: {
        getItem: (name) => {
          if (typeof window === 'undefined') return null;
          const item = sessionStorage.getItem(name);
          return item ? JSON.parse(item) : null;
        },
        setItem: (name, value) => {
          if (typeof window !== 'undefined') {
            sessionStorage.setItem(name, JSON.stringify(value));
          }
        },
        removeItem: (name) => {
          if (typeof window !== 'undefined') {
            sessionStorage.removeItem(name);
          }
        },
      },
    }
  )
);
