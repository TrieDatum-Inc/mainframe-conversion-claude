/**
 * HTTP client for the CardDemo FastAPI backend.
 *
 * Uses axios with:
 *   - Bearer token injection from localStorage
 *   - Automatic 401 → redirect to /login
 *   - Error normalization
 */
import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import type { ApiError } from '@/lib/types/api';

const API_BASE = process.env.NEXT_PUBLIC_API_URL
  ? `${process.env.NEXT_PUBLIC_API_URL}/api/v1`
  : '/api/v1';

export const TOKEN_KEY = 'carddemo_token';
export const USER_KEY = 'carddemo_user';

function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

const client: AxiosInstance = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30_000,
});

// Request interceptor — attach Bearer token
client.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor — handle 401 globally
client.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    if (error.response?.status === 401) {
      // Don't redirect for the login endpoint itself — let the page show the error.
      const url = error.config?.url ?? '';
      const isLoginRequest = url.includes('/auth/login');
      if (!isLoginRequest && typeof window !== 'undefined') {
        // Clear session and redirect to login
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
        window.location.href = '/login?session=expired';
      }
    }
    return Promise.reject(error);
  }
);

/**
 * Extract a human-readable error message from an API error response.
 */
export function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as ApiError | undefined;
    if (!data) return error.message || 'An unexpected error occurred';

    if (typeof data.detail === 'string') return data.detail;

    if (Array.isArray(data.detail)) {
      // FastAPI validation errors
      return data.detail.map((e) => `${e.loc.slice(-1)[0]}: ${e.msg}`).join('; ');
    }
  }
  if (error instanceof Error) return error.message;
  return 'An unexpected error occurred';
}

export default client;
