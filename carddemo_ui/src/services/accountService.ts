/**
 * Account service — wraps all /api/v1/accounts/* endpoints.
 * Derived from COACTVWC, COACTUPC, COBIL00C.
 */
import client from './apiClient';
import type {
  AccountDetailResponse,
  AccountResponse,
  AccountUpdateRequest,
  AccountPaymentRequest,
  TransactionResponse,
} from '@/lib/types/api';

export const accountService = {
  /**
   * GET /api/v1/accounts/{acct_id}
   * Derived from COACTVWC READ-PROCESSING paragraph.
   */
  async getAccount(acctId: number): Promise<AccountDetailResponse> {
    const { data } = await client.get<AccountDetailResponse>(`/accounts/${acctId}`);
    return data;
  },

  /**
   * PUT /api/v1/accounts/{acct_id}
   * Derived from COACTUPC PROCESS-ENTER-KEY → VALIDATE-INPUT-FIELDS.
   */
  async updateAccount(acctId: number, request: AccountUpdateRequest): Promise<AccountResponse> {
    const { data } = await client.put<AccountResponse>(`/accounts/${acctId}`, request);
    return data;
  },

  /**
   * POST /api/v1/accounts/{acct_id}/payments
   * Derived from COBIL00C PROCESS-PAYMENT paragraph.
   */
  async processPayment(
    acctId: number,
    request: AccountPaymentRequest
  ): Promise<TransactionResponse> {
    const { data } = await client.post<TransactionResponse>(
      `/accounts/${acctId}/payments`,
      request
    );
    return data;
  },
};
