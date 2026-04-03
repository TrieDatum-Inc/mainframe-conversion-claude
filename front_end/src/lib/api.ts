/**
 * Centralized API service layer.
 * All calls to the FastAPI backend go through this module.
 */

import type {
  TransactionDetail,
  TransactionFormData,
  TransactionListResponse,
  TransactionValidateResponse,
} from "@/types/transaction";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });

  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(errorBody.detail ?? res.statusText, res.status);
  }

  return res.json() as Promise<T>;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// ---------------------------------------------------------------------------
// CT00: Transaction List
// ---------------------------------------------------------------------------

export interface ListTransactionsParams {
  page?: number;
  page_size?: number;
  start_tran_id?: string;
  direction?: "forward" | "backward";
  anchor_tran_id?: string;
}

export async function listTransactions(
  params: ListTransactionsParams = {}
): Promise<TransactionListResponse> {
  const qs = new URLSearchParams();
  if (params.page) qs.set("page", String(params.page));
  if (params.page_size) qs.set("page_size", String(params.page_size));
  if (params.start_tran_id) qs.set("start_tran_id", params.start_tran_id);
  if (params.direction) qs.set("direction", params.direction);
  if (params.anchor_tran_id) qs.set("anchor_tran_id", params.anchor_tran_id);
  const query = qs.toString() ? `?${qs.toString()}` : "";
  return request<TransactionListResponse>(`/api/transactions${query}`);
}

// ---------------------------------------------------------------------------
// CT01: Transaction Detail
// ---------------------------------------------------------------------------

export async function getTransaction(tranId: string): Promise<TransactionDetail> {
  return request<TransactionDetail>(`/api/transactions/${tranId}`);
}

// ---------------------------------------------------------------------------
// CT02: Add Transaction — Step 1 (validate)
// ---------------------------------------------------------------------------

export async function validateTransaction(
  data: Omit<TransactionFormData, "confirm">
): Promise<TransactionValidateResponse> {
  return request<TransactionValidateResponse>("/api/transactions/validate", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ---------------------------------------------------------------------------
// CT02: Add Transaction — Step 2 (confirmed create)
// ---------------------------------------------------------------------------

export async function createTransaction(
  data: TransactionFormData & { confirm: string }
): Promise<TransactionDetail> {
  return request<TransactionDetail>("/api/transactions", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ---------------------------------------------------------------------------
// CT02: Copy last transaction (PF5 equivalent)
// ---------------------------------------------------------------------------

export async function copyLastTransaction(params: {
  card_num?: string;
  acct_id?: string;
}): Promise<TransactionDetail> {
  const qs = new URLSearchParams();
  if (params.card_num) qs.set("card_num", params.card_num);
  if (params.acct_id) qs.set("acct_id", params.acct_id);
  return request<TransactionDetail>(`/api/transactions/copy-last?${qs.toString()}`);
}
