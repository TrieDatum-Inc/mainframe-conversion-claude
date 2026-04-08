/**
 * API client for CardDemo backend.
 * All calls go through Next.js rewrites → backend at /api/v1/...
 */

import axios, { AxiosError, AxiosInstance } from "axios";
import type {
  LoginRequest,
  TokenResponse,
  AccountDetailResponse,
  AccountUpdateRequest,
  CardListResponse,
  CardDetailResponse,
  CardUpdateRequest,
  ApiErrorResponse,
} from "@/types";

// ---------------------------------------------------------------------------
// Axios instance
// ---------------------------------------------------------------------------

const apiClient: AxiosInstance = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
});

// Attach JWT from localStorage on every request
apiClient.interceptors.request.use((config) => {
  if (typeof globalThis.window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// ---------------------------------------------------------------------------
// Error helper
// ---------------------------------------------------------------------------

export function extractErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const data = error.response?.data as ApiErrorResponse | undefined;
    if (data?.detail?.message) return data.detail.message;
    if (typeof data?.detail === "string") return data.detail;
    return error.message;
  }
  if (error instanceof Error) return error.message;
  return "An unexpected error occurred";
}

export function extractErrorCode(error: unknown): string | null {
  if (error instanceof AxiosError) {
    const data = error.response?.data as ApiErrorResponse | undefined;
    return data?.detail?.error_code ?? null;
  }
  return null;
}

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export async function login(credentials: LoginRequest): Promise<TokenResponse> {
  const resp = await apiClient.post<TokenResponse>("/auth/login", {
    user_id: credentials.username,
    password: credentials.password,
  });
  return resp.data;
}

// ---------------------------------------------------------------------------
// Accounts — COACTVWC / COACTUPC
// ---------------------------------------------------------------------------

export async function getAccount(accountId: number): Promise<AccountDetailResponse> {
  const resp = await apiClient.get<AccountDetailResponse>(`/accounts/${accountId}`);
  return resp.data;
}

export async function updateAccount(
  accountId: number,
  payload: AccountUpdateRequest
): Promise<AccountDetailResponse> {
  const resp = await apiClient.put<AccountDetailResponse>(`/accounts/${accountId}`, payload);
  return resp.data;
}

// ---------------------------------------------------------------------------
// Credit Cards — COCRDLIC / COCRDSLC / COCRDUPC
// ---------------------------------------------------------------------------

export async function listCards(params?: {
  account_id?: number;
  page?: number;
  page_size?: number;
}): Promise<CardListResponse> {
  const resp = await apiClient.get<CardListResponse>("/cards", { params });
  return resp.data;
}

export async function getCard(cardNumber: string): Promise<CardDetailResponse> {
  const resp = await apiClient.get<CardDetailResponse>(`/cards/${cardNumber}`);
  return resp.data;
}

export async function updateCard(
  cardNumber: string,
  payload: CardUpdateRequest
): Promise<CardDetailResponse> {
  const resp = await apiClient.put<CardDetailResponse>(`/cards/${cardNumber}`, payload);
  return resp.data;
}
