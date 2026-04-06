/**
 * Centralized API client for the CardDemo Transaction Module.
 * All backend calls go through this module.
 */

import axios, { AxiosInstance } from "axios";
import type {
  BillPaymentPreview,
  BillPaymentRequest,
  BillPaymentResult,
  ReportRequest,
  ReportResult,
  TransactionCreateRequest,
  TransactionDetail,
  TransactionPage,
} from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function createApiClient(): AxiosInstance {
  const client = axios.create({ baseURL: BASE_URL });

  // Attach JWT token from localStorage on every request
  client.interceptors.request.use((config) => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("access_token");
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  });

  return client;
}

const api = createApiClient();

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export async function login(username: string, password: string): Promise<string> {
  const form = new URLSearchParams();
  form.append("username", username);
  form.append("password", password);
  const resp = await api.post<{ access_token: string }>("/api/auth/token", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return resp.data.access_token;
}

// ---------------------------------------------------------------------------
// Transactions — CT00, CT01, CT02
// ---------------------------------------------------------------------------

export interface ListTransactionsParams {
  page?: number;
  page_size?: number;
  transaction_id?: string;
  card_number?: string;
  account_id?: string;
  start_date?: string;
  end_date?: string;
}

export async function listTransactions(
  params: ListTransactionsParams = {}
): Promise<TransactionPage> {
  const resp = await api.get<TransactionPage>("/api/transactions", { params });
  return resp.data;
}

export async function getTransaction(transactionId: string): Promise<TransactionDetail> {
  const resp = await api.get<TransactionDetail>(`/api/transactions/${transactionId}`);
  return resp.data;
}

export async function createTransaction(
  payload: TransactionCreateRequest
): Promise<TransactionDetail> {
  const resp = await api.post<TransactionDetail>("/api/transactions", payload);
  return resp.data;
}

export async function getLastTransaction(cardNumber: string): Promise<TransactionDetail | null> {
  try {
    const page = await listTransactions({ card_number: cardNumber, page_size: 1 });
    if (page.items.length === 0) return null;
    return getTransaction(page.items[0].transaction_id);
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Bill Payment — CB00
// ---------------------------------------------------------------------------

export async function previewBillPayment(accountId: string): Promise<BillPaymentPreview> {
  const resp = await api.get<BillPaymentPreview>(`/api/bill-payment/preview/${accountId}`);
  return resp.data;
}

export async function processBillPayment(
  payload: BillPaymentRequest
): Promise<BillPaymentResult> {
  const resp = await api.post<BillPaymentResult>("/api/bill-payment", payload);
  return resp.data;
}

// ---------------------------------------------------------------------------
// Reports — CR00
// ---------------------------------------------------------------------------

export async function generateReport(payload: ReportRequest): Promise<ReportResult> {
  const resp = await api.post<ReportResult>("/api/reports/transactions", payload);
  return resp.data;
}
