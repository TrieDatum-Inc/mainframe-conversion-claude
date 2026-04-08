/**
 * Transaction service — wraps all /api/v1/transactions/* endpoints.
 * Derived from COTRN00C, COTRN01C, COTRN02C, COBIL00C.
 */
import client from './apiClient';
import type {
  TransactionListResponse,
  TransactionResponse,
  TransactionCreateRequest,
  BillPaymentRequest,
} from '@/lib/types/api';

export interface ListTransactionsParams {
  cursor?: string;
  limit?: number;
  card_num?: string;
  acct_id?: number;
  direction?: 'forward' | 'backward';
}

export const transactionService = {
  /**
   * GET /api/v1/transactions
   * Derived from COTRN00C BROWSE-TRANSACTIONS (STARTBR TRANSACT).
   */
  async listTransactions(params: ListTransactionsParams = {}): Promise<TransactionListResponse> {
    const { data } = await client.get<TransactionListResponse>('/transactions', { params });
    return data;
  },

  /**
   * GET /api/v1/transactions/{tran_id}
   * Derived from COTRN01C READ-TRANSACTION paragraph.
   */
  async getTransaction(tranId: string): Promise<TransactionResponse> {
    const { data } = await client.get<TransactionResponse>(`/transactions/${tranId}`);
    return data;
  },

  /**
   * POST /api/v1/transactions
   * Derived from COTRN02C PROCESS-ENTER-KEY.
   */
  async createTransaction(request: TransactionCreateRequest): Promise<TransactionResponse> {
    const { data } = await client.post<TransactionResponse>('/transactions', request);
    return data;
  },

  /**
   * POST /api/v1/transactions/payment
   * Derived from COBIL00C PROCESS-PAYMENT paragraph.
   */
  async processPayment(request: BillPaymentRequest): Promise<TransactionResponse> {
    const { data } = await client.post<TransactionResponse>('/transactions/payment', request);
    return data;
  },
};
