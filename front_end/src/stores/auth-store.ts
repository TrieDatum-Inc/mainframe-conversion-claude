/**
 * Zustand auth store.
 * Persists JWT token and user info in localStorage.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AuthState {
  accessToken: string | null;
  username: string | null;
  role: string | null;
  isAuthenticated: boolean;
  setAuth: (token: string, username: string, role: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      username: null,
      role: null,
      isAuthenticated: false,

      setAuth: (token: string, username: string, role: string) => {
        // Also write to localStorage so the axios interceptor can read it
        if (typeof window !== "undefined") {
          localStorage.setItem("access_token", token);
        }
        set({ accessToken: token, username, role, isAuthenticated: true });
      },

      clearAuth: () => {
        if (typeof window !== "undefined") {
          localStorage.removeItem("access_token");
        }
        set({ accessToken: null, username: null, role: null, isAuthenticated: false });
      },
    }),
    {
      name: "carddemo-auth",
      partialize: (state) => ({
        accessToken: state.accessToken,
        username: state.username,
        role: state.role,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
