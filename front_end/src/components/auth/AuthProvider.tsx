"use client";

/**
 * AuthProvider — React context for authentication state.
 *
 * COBOL origin: Replaces CARDDEMO-COMMAREA passed between CICS programs.
 * In the COBOL system, user identity and session state were carried in
 * COMMAREA fields (CDEMO-USER-ID, CDEMO-USRTYP-ADMIN, CDEMO-SIGNED-ON-FLAG).
 * This context provides the equivalent data to all React components.
 */

import React, {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useRouter } from "next/navigation";

import { api } from "@/lib/api";
import {
  clearAuthData,
  getStoredToken,
  getStoredUser,
  storeAuthData,
} from "@/lib/auth";
import { AuthUser, LoginResponse } from "@/types/auth";

interface AuthContextValue {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (response: LoginResponse) => void;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue>({
  user: null,
  token: null,
  isAuthenticated: false,
  login: () => {},
  logout: async () => {},
});

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);

  // Restore session from localStorage on mount (client-side hydration)
  useEffect(() => {
    const storedToken = getStoredToken();
    const storedUser = getStoredUser();
    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(storedUser);
    }
  }, []);

  /**
   * Store the login response and update context state.
   *
   * COBOL origin: Replaces COMMAREA population in PROCESS-ENTER-KEY:
   *   MOVE SEC-USR-ID TO CDEMO-USER-ID
   *   SET CDEMO-USRTYP-ADMIN TO TRUE/FALSE
   *   SET CDEMO-SIGNED-ON-FLAG TO TRUE
   */
  const login = useCallback((response: LoginResponse) => {
    const authUser: AuthUser = {
      userId: response.user_id,
      userType: response.user_type,
      firstName: response.first_name,
      lastName: response.last_name,
    };
    storeAuthData(response.access_token, authUser);
    setToken(response.access_token);
    setUser(authUser);
  }, []);

  /**
   * Clear session and call the logout endpoint.
   *
   * COBOL origin: Replaces COSGN00C RETURN-TO-PREV-SCREEN (PF3):
   *   bare EXEC CICS RETURN with no TRANSID — terminates the CICS task.
   * The API call is fire-and-forget; local state is cleared regardless.
   */
  const logout = useCallback(async () => {
    const currentToken = getStoredToken();
    clearAuthData();
    setToken(null);
    setUser(null);

    // Fire-and-forget the server-side token revocation
    if (currentToken) {
      try {
        await api.post("/api/v1/auth/logout", null, {
          headers: { Authorization: `Bearer ${currentToken}` },
        });
      } catch {
        // Swallow — local logout already complete
      }
    }

    router.push("/login");
  }, [router]);

  const value = useMemo(
    () => ({
      user,
      token,
      isAuthenticated: !!token && !!user,
      login,
      logout,
    }),
    [user, token, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
