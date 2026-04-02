'use client';

// ============================================================
// Auth Context
// Manages login/logout state, JWT token storage, and user session.
// Mirrors the COSGN00C sign-on program logic.
// ============================================================

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { useRouter } from 'next/navigation';
import { authApi, getErrorMessage } from '@/lib/api';
import type { AuthUser, LoginResponse } from '@/lib/types';

interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  isAdmin: boolean;
  login: (userId: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const TOKEN_KEY = 'carddemo_token';
const USER_KEY = 'carddemo_user';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  /** Rehydrate session from localStorage on mount */
  useEffect(() => {
    const storedUser = localStorage.getItem(USER_KEY);
    const storedToken = localStorage.getItem(TOKEN_KEY);
    if (storedUser && storedToken) {
      try {
        const parsed: AuthUser = JSON.parse(storedUser);
        setUser(parsed);
      } catch {
        localStorage.removeItem(USER_KEY);
        localStorage.removeItem(TOKEN_KEY);
      }
    }
    setIsLoading(false);
  }, []);

  const login = useCallback(
    async (userId: string, password: string) => {
      const response = await authApi.login(userId, password);
      const data: LoginResponse = response.data;

      const authUser: AuthUser = {
        user_id: data.user_id,
        user_type: data.user_type,
        first_name: data.first_name,
        last_name: data.last_name,
        token: data.access_token,
      };

      localStorage.setItem(TOKEN_KEY, data.access_token);
      localStorage.setItem(USER_KEY, JSON.stringify(authUser));
      setUser(authUser);
      router.push('/dashboard');
    },
    [router],
  );

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setUser(null);
    router.push('/login');
  }, [router]);

  const isAdmin = user?.user_type === 'A';

  const value = useMemo(
    () => ({ user, isLoading, isAdmin, login, logout }),
    [user, isLoading, isAdmin, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}

/** Convenience export for error message utility */
export { getErrorMessage };
