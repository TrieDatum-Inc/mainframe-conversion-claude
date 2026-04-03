import type { CardDetail, CardListParams, CardListResponse, CardUpdateRequest, CardUpdateResponse } from "@/types/card";
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

export class ApiClientError extends Error {
  constructor(public readonly status: number, public readonly detail: string) {
    super(detail);
    this.name = "ApiClientError";
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${path}`;
  const resp = await fetch(url, { headers: { "Content-Type": "application/json", ...options.headers }, ...options });
  if (!resp.ok) {
    let detail = `HTTP ${resp.status}`;
    try {
      const body = await resp.json();
      if (typeof body.detail === "string") detail = body.detail;
      else if (Array.isArray(body.detail)) detail = body.detail.map((e: { msg: string }) => e.msg).join("; ");
    } catch { /* ignore */ }
    throw new ApiClientError(resp.status, detail);
  }
  return resp.json() as Promise<T>;
}

export async function fetchCardList(params: CardListParams = {}): Promise<CardListResponse> {
  const qs = new URLSearchParams();
  if (params.cursor) qs.set("cursor", params.cursor);
  if (params.acct_id) qs.set("acct_id", params.acct_id);
  if (params.card_num_filter) qs.set("card_num_filter", params.card_num_filter);
  if (params.page_size) qs.set("page_size", String(params.page_size));
  if (params.page) qs.set("page", String(params.page));
  const query = qs.toString() ? `?${qs.toString()}` : "";
  return request<CardListResponse>(`/cards${query}`);
}

export async function fetchCardDetail(cardNum: string): Promise<CardDetail> {
  return request<CardDetail>(`/cards/${encodeURIComponent(cardNum)}`);
}

export async function updateCard(cardNum: string, data: CardUpdateRequest): Promise<CardUpdateResponse> {
  return request<CardUpdateResponse>(`/cards/${encodeURIComponent(cardNum)}`, { method: "PUT", body: JSON.stringify(data) });
}
