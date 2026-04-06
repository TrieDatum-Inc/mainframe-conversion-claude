"use client";

/**
 * Authentication context and provider.
 *
 * Replicates the CICS COMMAREA propagation model:
 *   - COSGN00C stores CDEMO-USER-ID + CDEMO-USER-TYPE in COMMAREA
 *   - Every subsequent program reads from COMMAREA
 *
 * Here, auth state (user + JWT) is stored in React context + localStorage,
 * and every component/route that needs identity reads from this context.
 */

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { AuthContextValue, LoginRequest, User } from "@/types";
import { apiClient } from "@/lib/api";

const TOKEN_KEY = "carddemo_token";

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Restore session from localStorage on mount
  useEffect(() => {
    const restoreSession = async () => {
      const storedToken = localStorage.getItem(TOKEN_KEY);
      if (!storedToken) {
        setIsLoading(false);
        return;
      }
      try {
        const freshUser = await apiClient.getMe(storedToken);
        setToken(storedToken);
        setUser(freshUser);
      } catch {
        // Token expired or invalid — clear it
        localStorage.removeItem(TOKEN_KEY);
      } finally {
        setIsLoading(false);
      }
    };

    restoreSession();
  }, []);

  const login = useCallback(async (credentials: LoginRequest): Promise<void> => {
    const response = await apiClient.login(credentials);
    localStorage.setItem(TOKEN_KEY, response.access_token);
    setToken(response.access_token);
    setUser(response.user);
  }, []);

  const logout = useCallback(async (): Promise<void> => {
    if (token) {
      // Best-effort — ignore errors (maps to CICS RETURN without TRANSID)
      try {
        await apiClient.logout(token);
      } catch {
        // silent
      }
    }
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }, [token]);

  const value: AuthContextValue = {
    user,
    token,
    isLoading,
    isAuthenticated: !!user && !!token,
    // Maps to CDEMO-USER-TYPE = 'A' check in COADM01C
    isAdmin: user?.user_type === "A",
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/** Hook to consume auth context. Throws if used outside AuthProvider. */
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
