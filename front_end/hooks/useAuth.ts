/**
 * useAuth hook — manages authentication state.
 *
 * Replaces CARDDEMO-COMMAREA persistence across CICS pseudo-conversational transactions.
 * JWT token stored in localStorage serves as the modern equivalent of COMMAREA.
 */
"use client";

import { useState, useEffect, useCallback } from "react";
import {
  login as apiLogin,
  logout as apiLogout,
  getStoredUser,
  getStoredToken,
  removeToken,
} from "@/lib/api";
import type { LoginFormData, UserInfo } from "@/types";

interface AuthState {
  user: UserInfo | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
}

interface UseAuthReturn extends AuthState {
  login: (data: LoginFormData) => Promise<string>;
  logout: () => Promise<void>;
  clearError: () => void;
}

export function useAuth(): UseAuthReturn {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: null,
    isLoading: true,
    error: null,
  });

  // Restore session from localStorage on mount
  // Equivalent to CICS COMMAREA being passed on re-entry (EIBCALEN > 0)
  useEffect(() => {
    const token = getStoredToken();
    const user = getStoredUser();

    setState({
      user: token ? user : null,
      token: token,
      isLoading: false,
      error: null,
    });
  }, []);

  /**
   * Login — maps COSGN00C PROCESS-ENTER-KEY + READ-USER-SEC-FILE.
   * Returns the redirect_to URL (BR-006 routing).
   */
  const login = useCallback(async (data: LoginFormData): Promise<string> => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await apiLogin(data);
      setState({
        user: response.user,
        token: response.access_token,
        isLoading: false,
        error: null,
      });
      return response.redirect_to;
    } catch (err) {
      const error = err as Record<string, unknown>;
      const message =
        typeof error.detail === "string"
          ? error.detail
          : "Login failed. Please try again.";
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: message,
      }));
      throw err;
    }
  }, []);

  /**
   * Logout — maps COSGN00C PF3 handler (CCDA-MSG-THANK-YOU + RETURN).
   * Clears token and user (equivalent to ending the CICS session).
   */
  const logout = useCallback(async (): Promise<void> => {
    setState((prev) => ({ ...prev, isLoading: true }));
    try {
      await apiLogout();
    } finally {
      setState({ user: null, token: null, isLoading: false, error: null });
    }
  }, []);

  const clearError = useCallback((): void => {
    setState((prev) => ({ ...prev, error: null }));
  }, []);

  return { ...state, login, logout, clearError };
}
