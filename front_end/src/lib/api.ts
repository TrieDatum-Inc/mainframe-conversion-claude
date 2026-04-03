/**
 * API service layer — centralised HTTP client.
 * All calls go through here, keeping components decoupled from transport details.
 */

import axios, { AxiosError } from "axios";
import type {
  AccountDetailResponse,
  AccountUpdateRequest,
  AccountUpdateResponse,
  ApiError,
} from "@/types/account";

const apiClient = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

/** Normalise any axios error into a human-readable string. */
export function extractErrorMessage(err: unknown): string {
  if (err instanceof AxiosError) {
    const data = err.response?.data as ApiError | undefined;
    if (typeof data?.detail === "string") return data.detail;
    if (Array.isArray(data?.detail)) {
      return data.detail.map((d) => d.msg).join("; ");
    }
    if (err.response?.status === 409) {
      return "Record changed by some one else. Please review and try again.";
    }
    if (err.response?.status === 423) {
      return "Record is currently locked by another user. Please try again shortly.";
    }
  }
  if (err instanceof Error) return err.message;
  return "An unexpected error occurred.";
}

/**
 * GET /api/accounts/{acct_id}
 * Replicates COACTVWC 9000-READ-ACCT and screen population.
 */
export async function getAccount(acctId: string): Promise<AccountDetailResponse> {
  const { data } = await apiClient.get<AccountDetailResponse>(`/accounts/${acctId}`);
  return data;
}

/**
 * PUT /api/accounts/{acct_id}
 * Replicates COACTUPC 9600-WRITE-PROCESSING (F5=Save phase).
 * The updated_at field in the request body is the optimistic concurrency token
 * obtained from the previous GET response.
 */
export async function updateAccount(
  acctId: string,
  payload: AccountUpdateRequest
): Promise<AccountUpdateResponse> {
  const { data } = await apiClient.put<AccountUpdateResponse>(
    `/accounts/${acctId}`,
    payload
  );
  return data;
}
