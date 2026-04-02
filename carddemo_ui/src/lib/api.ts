// ============================================================
// CardDemo API Client
// Axios instance with JWT interceptor and error normalization
// ============================================================

import axios, { AxiosError, AxiosInstance } from 'axios';
import { ApiError } from './types';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15_000,
});

/** Attach Bearer token from localStorage on every request */
apiClient.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('carddemo_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

/** Normalize error responses to a consistent shape */
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('carddemo_token');
      localStorage.removeItem('carddemo_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  },
);

/** Extract a human-readable message from an Axios error */
export function getErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const data = error.response?.data as ApiError | undefined;
    if (data?.message) return data.message;
    if (error.message) return error.message;
  }
  if (error instanceof Error) return error.message;
  return 'An unexpected error occurred';
}

// ---- Auth ----

export const authApi = {
  login: (user_id: string, password: string) =>
    apiClient.post('/auth/login', { user_id, password }),
};

// ---- Accounts ----

export const accountsApi = {
  get: (acctId: number | string) => apiClient.get(`/accounts/${acctId}`),
  update: (acctId: number | string, data: Record<string, unknown>) =>
    apiClient.put(`/accounts/${acctId}`, data),
};

// ---- Cards ----
// Backend uses keyset pagination: account_id, start_card_num, direction, page_size

export const cardsApi = {
  list: (params: {
    account_id?: number | string;
    start_card_num?: string;
    end_card_num?: string;
    direction?: string;
    page_size?: number;
  }) => apiClient.get('/cards', { params }),
  get: (cardNum: string) => apiClient.get(`/cards/${cardNum}`),
  update: (cardNum: string, data: Record<string, unknown>) =>
    apiClient.put(`/cards/${cardNum}`, data),
  create: (data: Record<string, unknown>) => apiClient.post('/cards', data),
};

// ---- Transactions ----
// Backend uses keyset pagination: start_tran_id, card_num, direction, page_size

export const transactionsApi = {
  list: (params: {
    start_tran_id?: string;
    end_tran_id?: string;
    card_num?: string;
    direction?: string;
    page_size?: number;
  }) => apiClient.get('/transactions', { params }),
  get: (tranId: string) => apiClient.get(`/transactions/${tranId}`),
  create: (data: Record<string, unknown>) =>
    apiClient.post('/transactions', data),
};

// ---- Billing ----

export const billingApi = {
  pay: (data: Record<string, unknown>) => apiClient.post('/billing/pay', data),
};

// ---- Reports ----

export const reportsApi = {
  generate: (data: Record<string, unknown>) =>
    apiClient.post('/reports/generate', data),
};

// ---- Users ----
// Backend uses keyset pagination: start_usr_id, direction, page_size

export const usersApi = {
  list: (params: {
    start_usr_id?: string;
    end_usr_id?: string;
    direction?: string;
    page_size?: number;
  }) => apiClient.get('/users', { params }),
  get: (usrId: string) => apiClient.get(`/users/${usrId}`),
  create: (data: Record<string, unknown>) => apiClient.post('/users', data),
  update: (usrId: string, data: Record<string, unknown>) =>
    apiClient.put(`/users/${usrId}`, data),
  delete: (usrId: string) =>
    apiClient.delete(`/users/${usrId}`, { data: { confirm: true } }),
};

// ---- Transaction Types ----
// Backend params: start_type_cd, type_cd_filter, desc_filter, page_size

export const transactionTypesApi = {
  list: (params: {
    start_type_cd?: string;
    type_cd_filter?: string;
    desc_filter?: string;
    page_size?: number;
  }) => apiClient.get('/transaction-types', { params }),
  get: (cd: string) => apiClient.get(`/transaction-types/${cd}`),
  create: (data: Record<string, unknown>) =>
    apiClient.post('/transaction-types', data),
  update: (cd: string, data: Record<string, unknown>) =>
    apiClient.put(`/transaction-types/${cd}`, data),
  delete: (cd: string) => apiClient.delete(`/transaction-types/${cd}`),
};

// ---- Authorizations ----

export const authorizationsApi = {
  summary: (params?: { account_id?: number | string }) =>
    apiClient.get('/authorizations', { params }),
  details: (acctId: number | string) =>
    apiClient.get(`/authorizations/${acctId}/details`),
  detail: (acctId: number | string, authDate: string, authTime: string) =>
    apiClient.get(
      `/authorizations/${acctId}/details/${authDate}/${authTime}`,
    ),
  flagFraud: (data: Record<string, unknown>) =>
    apiClient.post('/authorizations/fraud-flag', data),
  process: (data: Record<string, unknown>) =>
    apiClient.post('/authorizations/process', data),
};

