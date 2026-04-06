/**
 * Centralized API client for CardDemo backend.
 *
 * All HTTP calls are routed through Next.js rewrites (/api/* -> backend).
 * This prevents CORS issues in production and mirrors how CICS transactions
 * were isolated behind a single entry point (COSGN00C → CC00).
 */

import type {
  AccountDetail,
  AccountUpdateRequest,
  ApiError,
  CardDetail,
  CardUpdateRequest,
  CreateCategoryRequest,
  CreateTransactionTypeRequest,
  InlineSaveRequest,
  InlineSaveResponse,
  LoginRequest,
  LoginResponse,
  PaginatedAccounts,
  PaginatedCards,
  PaginatedTransactionTypes,
  TransactionTypeCategory,
  TransactionTypeDetail,
  TransactionType,
  UpdateCategoryRequest,
  UpdateTransactionTypeRequest,
  User,
} from "@/types";

const BASE_URL = "/api";

class ApiClient {
  private getAuthHeaders(token: string): Record<string, string> {
    return {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    };
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      let errorDetail = `HTTP ${response.status}`;
      try {
        const err: ApiError = await response.json();
        errorDetail = err.detail || errorDetail;
      } catch {
        // response body is not JSON
      }
      throw new Error(errorDetail);
    }
    return response.json() as Promise<T>;
  }

  /** POST /api/auth/login — maps to COSGN00C ENTER key action */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await fetch(`${BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: credentials.user_id.toUpperCase(),
        password: credentials.password.toUpperCase(),
      }),
    });
    return this.handleResponse<LoginResponse>(response);
  }

  /** POST /api/auth/logout — maps to COSGN00C PF3 action */
  async logout(token: string): Promise<void> {
    await fetch(`${BASE_URL}/auth/logout`, {
      method: "POST",
      headers: this.getAuthHeaders(token),
    });
    // Logout is best-effort; the client always clears local state regardless
  }

  /** GET /api/auth/me — get fresh user profile from JWT */
  async getMe(token: string): Promise<User> {
    const response = await fetch(`${BASE_URL}/auth/me`, {
      method: "GET",
      headers: this.getAuthHeaders(token),
    });
    return this.handleResponse<User>(response);
  }

  // -------------------------------------------------------------------------
  // Account endpoints (COACTVWC view, COACTUPC update)
  // -------------------------------------------------------------------------

  /** GET /api/accounts — paginated list with optional account_id filter */
  async listAccounts(
    token: string,
    params?: { account_id?: string; page?: number; page_size?: number }
  ): Promise<PaginatedAccounts> {
    const url = new URL(`${BASE_URL}/accounts`, window.location.origin);
    if (params?.account_id) url.searchParams.set("account_id", params.account_id);
    if (params?.page) url.searchParams.set("page", String(params.page));
    if (params?.page_size) url.searchParams.set("page_size", String(params.page_size));
    const response = await fetch(url.toString(), {
      headers: this.getAuthHeaders(token),
    });
    return this.handleResponse<PaginatedAccounts>(response);
  }

  /** GET /api/accounts/{account_id} — full detail with customer + cards */
  async getAccount(token: string, accountId: string): Promise<AccountDetail> {
    const response = await fetch(
      `${BASE_URL}/accounts/${encodeURIComponent(accountId)}`,
      { headers: this.getAuthHeaders(token) }
    );
    return this.handleResponse<AccountDetail>(response);
  }

  /** PUT /api/accounts/{account_id} — update account and customer fields */
  async updateAccount(
    token: string,
    accountId: string,
    body: AccountUpdateRequest
  ): Promise<AccountDetail> {
    const response = await fetch(
      `${BASE_URL}/accounts/${encodeURIComponent(accountId)}`,
      {
        method: "PUT",
        headers: this.getAuthHeaders(token),
        body: JSON.stringify(body),
      }
    );
    return this.handleResponse<AccountDetail>(response);
  }

  // -------------------------------------------------------------------------
  // Card endpoints (COCRDLIC list, COCRDSLC view, COCRDUPC update)
  // -------------------------------------------------------------------------

  /** GET /api/cards — paginated list (7 per page), optional account/card filters */
  async listCards(
    token: string,
    params?: {
      account_id?: string;
      card_number?: string;
      page?: number;
      page_size?: number;
    }
  ): Promise<PaginatedCards> {
    const url = new URL(`${BASE_URL}/cards`, window.location.origin);
    if (params?.account_id) url.searchParams.set("account_id", params.account_id);
    if (params?.card_number) url.searchParams.set("card_number", params.card_number);
    if (params?.page) url.searchParams.set("page", String(params.page));
    if (params?.page_size) url.searchParams.set("page_size", String(params.page_size));
    const response = await fetch(url.toString(), {
      headers: this.getAuthHeaders(token),
    });
    return this.handleResponse<PaginatedCards>(response);
  }

  /** GET /api/cards/{card_number} — full card detail (COCRDSLC READ CARDDAT) */
  async getCard(token: string, cardNumber: string): Promise<CardDetail> {
    const response = await fetch(
      `${BASE_URL}/cards/${encodeURIComponent(cardNumber)}`,
      { headers: this.getAuthHeaders(token) }
    );
    return this.handleResponse<CardDetail>(response);
  }

  /** PUT /api/cards/{card_number} — update editable fields (COCRDUPC REWRITE) */
  async updateCard(
    token: string,
    cardNumber: string,
    body: CardUpdateRequest
  ): Promise<CardDetail> {
    const response = await fetch(
      `${BASE_URL}/cards/${encodeURIComponent(cardNumber)}`,
      {
        method: "PUT",
        headers: this.getAuthHeaders(token),
        body: JSON.stringify(body),
      }
    );
    return this.handleResponse<CardDetail>(response);
  }

  // -------------------------------------------------------------------------
  // Transaction Type endpoints (admin-only, mirrors COTRTLIC / COTRTUPC)
  // -------------------------------------------------------------------------

  /** GET /api/transaction-types — paginated list with optional filters */
  async listTransactionTypes(
    token: string,
    params?: {
      type_code?: string;
      description?: string;
      page?: number;
      page_size?: number;
    }
  ): Promise<PaginatedTransactionTypes> {
    const url = new URL(`${BASE_URL}/transaction-types`, window.location.origin);
    if (params?.type_code) url.searchParams.set("type_code", params.type_code);
    if (params?.description) url.searchParams.set("description", params.description);
    if (params?.page) url.searchParams.set("page", String(params.page));
    if (params?.page_size) url.searchParams.set("page_size", String(params.page_size));
    const response = await fetch(url.toString(), {
      headers: this.getAuthHeaders(token),
    });
    return this.handleResponse<PaginatedTransactionTypes>(response);
  }

  /** GET /api/transaction-types/{type_code} — detail with categories */
  async getTransactionType(
    token: string,
    typeCode: string
  ): Promise<TransactionTypeDetail> {
    const response = await fetch(
      `${BASE_URL}/transaction-types/${encodeURIComponent(typeCode)}`,
      { headers: this.getAuthHeaders(token) }
    );
    return this.handleResponse<TransactionTypeDetail>(response);
  }

  /** POST /api/transaction-types — create (COTRTUPC F6=Add) */
  async createTransactionType(
    token: string,
    body: CreateTransactionTypeRequest
  ): Promise<TransactionType> {
    const response = await fetch(`${BASE_URL}/transaction-types`, {
      method: "POST",
      headers: this.getAuthHeaders(token),
      body: JSON.stringify(body),
    });
    return this.handleResponse<TransactionType>(response);
  }

  /** PUT /api/transaction-types/{type_code} — update description (COTRTUPC F5=Save) */
  async updateTransactionType(
    token: string,
    typeCode: string,
    body: UpdateTransactionTypeRequest
  ): Promise<TransactionType> {
    const response = await fetch(
      `${BASE_URL}/transaction-types/${encodeURIComponent(typeCode)}`,
      {
        method: "PUT",
        headers: this.getAuthHeaders(token),
        body: JSON.stringify(body),
      }
    );
    return this.handleResponse<TransactionType>(response);
  }

  /** DELETE /api/transaction-types/{type_code} — delete + cascade (COTRTLIC selector) */
  async deleteTransactionType(token: string, typeCode: string): Promise<void> {
    const response = await fetch(
      `${BASE_URL}/transaction-types/${encodeURIComponent(typeCode)}`,
      {
        method: "DELETE",
        headers: this.getAuthHeaders(token),
      }
    );
    if (!response.ok && response.status !== 204) {
      await this.handleResponse<void>(response);
    }
  }

  /** POST /api/transaction-types/inline-save — batch save (COTRTLIC F10=Save) */
  async inlineSaveTransactionTypes(
    token: string,
    body: InlineSaveRequest
  ): Promise<InlineSaveResponse> {
    const response = await fetch(`${BASE_URL}/transaction-types/inline-save`, {
      method: "POST",
      headers: this.getAuthHeaders(token),
      body: JSON.stringify(body),
    });
    return this.handleResponse<InlineSaveResponse>(response);
  }

  /** GET /api/transaction-types/{type_code}/categories */
  async listCategories(
    token: string,
    typeCode: string
  ): Promise<TransactionTypeCategory[]> {
    const response = await fetch(
      `${BASE_URL}/transaction-types/${encodeURIComponent(typeCode)}/categories`,
      { headers: this.getAuthHeaders(token) }
    );
    return this.handleResponse<TransactionTypeCategory[]>(response);
  }

  /** POST /api/transaction-types/{type_code}/categories */
  async createCategory(
    token: string,
    typeCode: string,
    body: CreateCategoryRequest
  ): Promise<TransactionTypeCategory> {
    const response = await fetch(
      `${BASE_URL}/transaction-types/${encodeURIComponent(typeCode)}/categories`,
      {
        method: "POST",
        headers: this.getAuthHeaders(token),
        body: JSON.stringify(body),
      }
    );
    return this.handleResponse<TransactionTypeCategory>(response);
  }

  /** PUT /api/transaction-types/{type_code}/categories/{category_code} */
  async updateCategory(
    token: string,
    typeCode: string,
    categoryCode: string,
    body: UpdateCategoryRequest
  ): Promise<TransactionTypeCategory> {
    const response = await fetch(
      `${BASE_URL}/transaction-types/${encodeURIComponent(typeCode)}/categories/${encodeURIComponent(categoryCode)}`,
      {
        method: "PUT",
        headers: this.getAuthHeaders(token),
        body: JSON.stringify(body),
      }
    );
    return this.handleResponse<TransactionTypeCategory>(response);
  }

  /** DELETE /api/transaction-types/{type_code}/categories/{category_code} */
  async deleteCategory(
    token: string,
    typeCode: string,
    categoryCode: string
  ): Promise<void> {
    const response = await fetch(
      `${BASE_URL}/transaction-types/${encodeURIComponent(typeCode)}/categories/${encodeURIComponent(categoryCode)}`,
      {
        method: "DELETE",
        headers: this.getAuthHeaders(token),
      }
    );
    if (!response.ok && response.status !== 204) {
      await this.handleResponse<void>(response);
    }
  }
}

export const apiClient = new ApiClient();
