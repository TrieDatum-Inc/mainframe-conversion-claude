/**
 * Authentication hook — provides auth state and actions.
 * Reads from localStorage (token + user object set by authService).
 */
'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/services/authService';
import type { AuthUser, LoginRequest } from '@/lib/types/api';
import { extractErrorMessage } from '@/services/apiClient';

interface UseAuthReturn {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isLoading: boolean;
  login: (request: LoginRequest) => Promise<void>;
  logout: () => void;
  error: string | null;
}

export function useAuth(): UseAuthReturn {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Hydrate user from localStorage on mount
  useEffect(() => {
    const currentUser = authService.getCurrentUser();
    setUser(currentUser);
  }, []);

  const login = useCallback(
    async (request: LoginRequest) => {
      setIsLoading(true);
      setError(null);
      try {
        const tokenResponse = await authService.login(request);
        const authUser: AuthUser = {
          user_id: tokenResponse.user_id,
          user_type: tokenResponse.user_type,
          first_name: tokenResponse.first_name,
          last_name: tokenResponse.last_name,
          is_admin: tokenResponse.user_type === 'A',
        };
        setUser(authUser);
        // Navigate based on role (admin menu vs regular dashboard)
        router.push('/dashboard');
      } catch (err) {
        const msg = extractErrorMessage(err);
        setError(msg);
        // Auto-clear after 2 seconds
        setTimeout(() => setError(null), 2000);
      } finally {
        setIsLoading(false);
      }
    },
    [router]
  );

  const logout = useCallback(() => {
    authService.logout();
    setUser(null);
    router.push('/login');
  }, [router]);

  return {
    user,
    isAuthenticated: !!user,
    isAdmin: user?.user_type === 'A',
    isLoading,
    login,
    logout,
    error,
  };
}
