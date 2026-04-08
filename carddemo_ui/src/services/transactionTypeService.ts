/**
 * Transaction type service — wraps /api/v1/transaction-types/* endpoints.
 * Derived from COTRTLIC, COTRTUPC.
 */
import client from './apiClient';
import type {
  TransactionTypeListResponse,
  TransactionTypeResponse,
  TransactionTypeUpdateRequest,
} from '@/lib/types/api';

export interface ListTransactionTypesParams {
  cursor?: string;
  direction?: 'forward' | 'backward';
  limit?: number;
  type_cd?: string;
  desc_filter?: string;
}

export const transactionTypeService = {
  /**
   * GET /api/v1/transaction-types
   * Derived from COTRTLIC C-TR-TYPE-FORWARD cursor browse.
   */
  async listTransactionTypes(
    params: ListTransactionTypesParams = {}
  ): Promise<TransactionTypeListResponse> {
    const { data } = await client.get<TransactionTypeListResponse>('/transaction-types', {
      params,
    });
    return data;
  },

  /**
   * GET /api/v1/transaction-types/{type_cd}
   * Derived from COTRTUPC 9000-READ-TRANTYPE paragraph.
   */
  async getTransactionType(typeCd: string): Promise<TransactionTypeResponse> {
    const { data } = await client.get<TransactionTypeResponse>(`/transaction-types/${typeCd}`);
    return data;
  },

  /**
   * PUT /api/v1/transaction-types/{type_cd}
   * Derived from COTRTUPC 9600-WRITE-PROCESSING (UPDATE).
   */
  async updateTransactionType(
    typeCd: string,
    request: TransactionTypeUpdateRequest
  ): Promise<TransactionTypeResponse> {
    const { data } = await client.put<TransactionTypeResponse>(
      `/transaction-types/${typeCd}`,
      request
    );
    return data;
  },

  /**
   * POST /api/v1/transaction-types
   * Derived from COTRTUPC TTUP-CREATE-NEW-RECORD (INSERT).
   */
  async createTransactionType(
    typeCd: string,
    request: TransactionTypeUpdateRequest
  ): Promise<TransactionTypeResponse> {
    const { data } = await client.post<TransactionTypeResponse>('/transaction-types', request, {
      params: { type_cd: typeCd },
    });
    return data;
  },

  /**
   * DELETE /api/v1/transaction-types/{type_cd}
   * Derived from COTRTLIC 9300-DELETE-RECORD (DELETE).
   */
  async deleteTransactionType(typeCd: string): Promise<void> {
    await client.delete(`/transaction-types/${typeCd}`);
  },
};
