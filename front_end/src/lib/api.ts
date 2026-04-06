/**
 * Typed API client for the CardDemo backend.
 *
 * All HTTP calls to /api/v1/* are centralized here.
 * Error responses are normalized to ApiErrorResponse format.
 *
 * COBOL origin: Replaces CICS SEND MAP / RECEIVE MAP interactions.
 * Each function maps to one CICS transaction or program paragraph.
 */

import axios, { AxiosError } from 'axios';
import type {
  AccountUpdateRequest,
  AccountViewResponse,
  ApiErrorResponse,
  BillPaymentRequest,
  BillPaymentResponse,
  BillingBalanceResponse,
  CardDetailResponse,
  CardListParams,
  CardListResponse,
  CardUpdateRequest,
  MessageResponse,
  PaginationParams,
  ReportRequestCreate,
  ReportRequestResponse,
  ReportStatusResponse,
  TransactionCreateRequest,
  TransactionDetailResponse,
  TransactionListParams,
  TransactionListResponse,
  TransactionTypeCreateRequest,
  TransactionTypeListParams,
  TransactionTypeListResponse,
  TransactionTypeResponse,
  TransactionTypeUpdateRequest,
  UserCreateRequest,
  UserListResponse,
  UserResponse,
  UserUpdateRequest,
} from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/** Create an axios instance with base URL and JSON headers. */
const apiClient = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
});

/** Attach the JWT Bearer token from sessionStorage to every request. */
apiClient.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const stored = sessionStorage.getItem('carddemo-auth');
    if (stored) {
      const parsed = JSON.parse(stored);
      const token = parsed?.state?.token;
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
  }
  return config;
});

/** Normalize Axios errors to ApiErrorResponse. */
function extractError(err: unknown): ApiErrorResponse {
  if (err instanceof AxiosError && err.response?.data?.detail) {
    const detail = err.response.data.detail;
    if (typeof detail === 'object' && detail.error_code) {
      return detail as ApiErrorResponse;
    }
    return {
      error_code: 'API_ERROR',
      message: String(detail),
      details: [],
    };
  }
  return {
    error_code: 'NETWORK_ERROR',
    message: 'Network error — please check your connection',
    details: [],
  };
}

// =============================================================================
// User Management API — COUSR00C / COUSR01C / COUSR02C / COUSR03C
// =============================================================================

/**
 * GET /api/v1/users
 * COBOL origin: COUSR00C POPULATE-USER-DATA (STARTBR/READNEXT browse)
 */
export async function listUsers(params: PaginationParams): Promise<UserListResponse> {
  const { page, page_size, user_id_filter } = params;
  const query: Record<string, string | number> = { page, page_size };
  if (user_id_filter) query.user_id_filter = user_id_filter;

  const resp = await apiClient.get<UserListResponse>('/users', { params: query });
  return resp.data;
}

/**
 * GET /api/v1/users/{user_id}
 * COBOL origin: COUSR02C PROCESS-ENTER-KEY → READ-USER-SEC-FILE
 */
export async function getUser(userId: string): Promise<UserResponse> {
  const resp = await apiClient.get<UserResponse>(`/users/${encodeURIComponent(userId)}`);
  return resp.data;
}

/**
 * POST /api/v1/users
 * COBOL origin: COUSR01C PROCESS-ENTER-KEY → WRITE-USER-SEC-FILE
 */
export async function createUser(data: UserCreateRequest): Promise<UserResponse> {
  const resp = await apiClient.post<UserResponse>('/users', data);
  return resp.data;
}

/**
 * PUT /api/v1/users/{user_id}
 * COBOL origin: COUSR02C UPDATE-USER-INFO → UPDATE-USER-SEC-FILE
 */
export async function updateUser(
  userId: string,
  data: UserUpdateRequest
): Promise<UserResponse> {
  const resp = await apiClient.put<UserResponse>(
    `/users/${encodeURIComponent(userId)}`,
    data
  );
  return resp.data;
}

/**
 * DELETE /api/v1/users/{user_id}
 * COBOL origin: COUSR03C DELETE-USER-INFO → DELETE-USER-SEC-FILE
 * Bug fix: COUSR03C said 'Unable to Update User' on delete failure — corrected.
 */
export async function deleteUser(userId: string): Promise<MessageResponse> {
  const resp = await apiClient.delete<MessageResponse>(
    `/users/${encodeURIComponent(userId)}`
  );
  return resp.data;
}

// =============================================================================
// Transaction Type Management API — COTRTLIC (CTLI) + COTRTUPC (CTTU)
// All endpoints are admin-only (user_type='A' JWT claim required).
// =============================================================================

/**
 * GET /api/v1/transaction-types
 * COBOL origin: COTRTLIC 8000-READ-FORWARD / 8100-READ-BACKWARDS (cursor-based paging)
 * Replaced by standard page/page_size pagination.
 * Default page_size=7 matches COTRTLIC WS-MAX-SCREEN-LINES=7.
 */
export async function listTransactionTypes(
  params: TransactionTypeListParams = {}
): Promise<TransactionTypeListResponse> {
  const { page = 1, page_size = 7, type_code_filter, description_filter } = params;
  const query: Record<string, string | number> = { page, page_size };
  if (type_code_filter) query.type_code_filter = type_code_filter;
  if (description_filter) query.description_filter = description_filter;

  const resp = await apiClient.get<TransactionTypeListResponse>('/transaction-types', {
    params: query,
  });
  return resp.data;
}

/**
 * GET /api/v1/transaction-types/{type_code}
 * COBOL origin: COTRTUPC 9000-READ-TRANTYPE → 9100-GET-TRANSACTION-TYPE
 * Fetches a single transaction type for the detail/edit form (CTRTUPA).
 * Returns the updated_at timestamp needed for optimistic locking on PUT.
 */
export async function getTransactionType(typeCode: string): Promise<TransactionTypeResponse> {
  const resp = await apiClient.get<TransactionTypeResponse>(
    `/transaction-types/${encodeURIComponent(typeCode)}`
  );
  return resp.data;
}

/**
 * POST /api/v1/transaction-types
 * COBOL origin: COTRTUPC 9700-INSERT-RECORD
 * Creates a new transaction type (TTUP-CREATE-NEW-RECORD state → PF5).
 */
export async function createTransactionType(
  data: TransactionTypeCreateRequest
): Promise<TransactionTypeResponse> {
  const resp = await apiClient.post<TransactionTypeResponse>('/transaction-types', data);
  return resp.data;
}

/**
 * PUT /api/v1/transaction-types/{type_code}
 * COBOL origin: COTRTLIC 9200-UPDATE-RECORD (inline edit, 'U' + PF10)
 *              COTRTUPC 9600-WRITE-PROCESSING (UPDATE path, PF5)
 * Only description is editable. Requires optimistic_lock_version to detect concurrent edits.
 */
export async function updateTransactionType(
  typeCode: string,
  data: TransactionTypeUpdateRequest
): Promise<TransactionTypeResponse> {
  const resp = await apiClient.put<TransactionTypeResponse>(
    `/transaction-types/${encodeURIComponent(typeCode)}`,
    data
  );
  return resp.data;
}

/**
 * DELETE /api/v1/transaction-types/{type_code}
 * COBOL origin: COTRTLIC 9300-DELETE-RECORD (inline delete, 'D' + PF10)
 *              COTRTUPC 9800-DELETE-PROCESSING (PF4 confirm → PF4)
 * Returns 204 on success. Returns 409 if transactions reference this type (SQLCODE -532).
 */
export async function deleteTransactionType(typeCode: string): Promise<void> {
  await apiClient.delete(`/transaction-types/${encodeURIComponent(typeCode)}`);
}

// =============================================================================
// Account Management API — COACTVWC (view) + COACTUPC (update)
// =============================================================================

/**
 * GET /api/v1/accounts/{account_id}
 * COBOL origin: COACTVWC READ-ACCT-BY-ACCT-ID → READ-CUST-BY-CUST-ID → READ-CARD-BY-ACCT-AIX
 * Joins three data sources: ACCTDAT + CUSTDAT + CARDAIX.
 */
export async function getAccount(accountId: number): Promise<AccountViewResponse> {
  const resp = await apiClient.get<AccountViewResponse>(`/accounts/${accountId}`);
  return resp.data;
}

/**
 * PUT /api/v1/accounts/{account_id}
 * COBOL origin: COACTUPC UPDATE-ACCOUNT-INFO (15+ validation rules)
 * Updates both account and customer fields in a single transaction.
 */
export async function updateAccount(
  accountId: number,
  data: AccountUpdateRequest
): Promise<AccountViewResponse> {
  const resp = await apiClient.put<AccountViewResponse>(`/accounts/${accountId}`, data);
  return resp.data;
}

// =============================================================================
// Credit Card Management API — COCRDLIC (list) + COCRDSLC (view) + COCRDUPC (update)
// =============================================================================

/**
 * GET /api/v1/cards
 * COBOL origin: COCRDLIC POPULATE-USER-DATA (7-row STARTBR/READNEXT/READPREV browse)
 * Default page_size=7 matches COCRDLIC original display.
 * Card numbers masked (last 4 digits only) per PCI-DSS.
 */
export async function listCards(params: CardListParams = {}): Promise<CardListResponse> {
  const { account_id, card_number, page = 1, page_size = 7 } = params;
  const query: Record<string, string | number> = { page, page_size };
  if (account_id) query.account_id = account_id;
  if (card_number) query.card_number = card_number;

  const resp = await apiClient.get<CardListResponse>('/cards', { params: query });
  return resp.data;
}

/**
 * GET /api/v1/cards/{card_number}
 * COBOL origin: COCRDSLC PROCESS-ENTER-KEY → READ DATASET(CARDDAT) RIDFLD(WS-CARD-NUM)
 * Returns updated_at as optimistic_lock_version for use in PUT request.
 */
export async function getCard(cardNumber: string): Promise<CardDetailResponse> {
  const resp = await apiClient.get<CardDetailResponse>(`/cards/${encodeURIComponent(cardNumber)}`);
  return resp.data;
}

/**
 * PUT /api/v1/cards/{card_number}
 * COBOL origin: COCRDUPC UPDATE-CARD (7-state machine):
 *   - Validates embossed name alpha-only (INSPECT CONVERTING)
 *   - Validates expiry month 1-12, year 1950-2099
 *   - Checks optimistic lock (CCUP-OLD-DETAILS snapshot)
 *   - account_id is PROT (NOT updated — cannot be changed)
 * Returns 409 Conflict if record was modified since last fetch.
 */
export async function updateCard(
  cardNumber: string,
  data: CardUpdateRequest
): Promise<CardDetailResponse> {
  const resp = await apiClient.put<CardDetailResponse>(
    `/cards/${encodeURIComponent(cardNumber)}`,
    data
  );
  return resp.data;
}

// =============================================================================
// Transaction API — COTRN00C (list) + COTRN01C (view) + COTRN02C (add)
// =============================================================================

/**
 * GET /api/v1/transactions
 * COBOL origin: COTRN00C POPULATE-TRAN-DATA (STARTBR/READNEXT browse, 10 rows/page)
 */
export async function listTransactions(
  params: TransactionListParams = {}
): Promise<TransactionListResponse> {
  const { page = 1, page_size = 10, tran_id_filter, account_id } = params;
  const query: Record<string, string | number> = { page, page_size };
  if (tran_id_filter) query.tran_id_filter = tran_id_filter;
  if (account_id) query.account_id = account_id;

  const resp = await apiClient.get<TransactionListResponse>('/transactions', {
    params: query,
  });
  return resp.data;
}

/**
 * GET /api/v1/transactions/{transaction_id}
 * COBOL origin: COTRN01C PROCESS-ENTER-KEY → READ TRANSACT by TRNIDINI
 * Bug fix: original used READ UPDATE (exclusive lock) — modern uses plain SELECT.
 */
export async function getTransaction(
  transactionId: string
): Promise<TransactionDetailResponse> {
  const resp = await apiClient.get<TransactionDetailResponse>(
    `/transactions/${encodeURIComponent(transactionId)}`
  );
  return resp.data;
}

/**
 * GET /api/v1/transactions/last
 * COBOL origin: COTRN02C PF5 COPY-LAST-TRAN-DATA — pre-fills form with last transaction.
 */
export async function getLastTransaction(): Promise<TransactionDetailResponse | null> {
  try {
    const resp = await apiClient.get<TransactionDetailResponse>('/transactions/last');
    return resp.data;
  } catch {
    return null;
  }
}

/**
 * POST /api/v1/transactions
 * COBOL origin: COTRN02C ADD-TRANSACTION (after CONFIRMI='Y' gate)
 * Race condition fix: ID generated via PostgreSQL sequence, not STARTBR/READPREV/ADD-1.
 */
export async function createTransaction(
  data: TransactionCreateRequest
): Promise<TransactionDetailResponse> {
  const resp = await apiClient.post<TransactionDetailResponse>('/transactions', data);
  return resp.data;
}

// =============================================================================
// Billing API — COBIL00C (CBIL0A BMS map)
// Two-phase: Phase 1 = GET balance (read-only), Phase 2 = POST payment
// =============================================================================

/**
 * GET /api/v1/billing/{account_id}/balance
 * COBOL origin: COBIL00C Phase 1 — READ-ACCTDAT-FILE → display ACCT-CURR-BAL.
 * Plain SELECT — no lock (COBIL00C only acquired lock before payment).
 */
export async function getBillingBalance(
  accountId: number
): Promise<BillingBalanceResponse> {
  const resp = await apiClient.get<BillingBalanceResponse>(
    `/billing/${accountId}/balance`
  );
  return resp.data;
}

/**
 * POST /api/v1/billing/{account_id}/payment
 * COBOL origin: COBIL00C CONF-PAY-YES:
 *   SELECT FOR UPDATE → WRITE TRANSACT → COMPUTE ACCT-CURR-BAL = 0 → REWRITE ACCTDAT
 * confirm='Y' required (CONFIRMI gate).
 */
export async function processPayment(
  accountId: number,
  data: BillPaymentRequest
): Promise<BillPaymentResponse> {
  const resp = await apiClient.post<BillPaymentResponse>(
    `/billing/${accountId}/payment`,
    data
  );
  return resp.data;
}

// =============================================================================
// Reports API — CORPT00C (CRPT0A BMS map)
// COBOL origin: CORPT00C WRITEQ TD QUEUE='JOBS' → DB record + background task
// =============================================================================

/**
 * POST /api/v1/reports/request
 * COBOL origin: CORPT00C PROCESS-ENTER-KEY → WIRTE-JOBSUB-TDQ
 * Returns 202 Accepted — report generated asynchronously.
 */
export async function requestReport(
  data: ReportRequestCreate
): Promise<ReportRequestResponse> {
  const resp = await apiClient.post<ReportRequestResponse>('/reports/request', data);
  return resp.data;
}

/**
 * GET /api/v1/reports/{report_id}
 * No COBOL equivalent — new status polling capability.
 * Replaces the lack of status visibility in original TDQ-based submission.
 */
export async function getReportStatus(reportId: number): Promise<ReportStatusResponse> {
  const resp = await apiClient.get<ReportStatusResponse>(`/reports/${reportId}`);
  return resp.data;
}

export { extractError };
