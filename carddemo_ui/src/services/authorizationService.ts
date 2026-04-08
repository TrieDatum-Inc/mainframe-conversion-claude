/**
 * Authorization service — wraps /api/v1/authorizations/* endpoints.
 * Derived from COPAUA0C, COPAUS0C, COPAUS1C, COPAUS2C.
 */
import client from './apiClient';
import type {
  AuthorizationRequest,
  AuthorizationResponse,
  AuthDetailListResponse,
  AuthDetailResponse,
  FraudMarkRequest,
  FraudMarkResponse,
} from '@/lib/types/api';

export interface ListAuthorizationsParams {
  cursor?: number;
  limit?: number;
}

export const authorizationService = {
  /**
   * POST /api/v1/authorizations
   * Derived from COPAUA0C (CICS transaction CP00) — MQ-driven authorization engine.
   */
  async processAuthorization(request: AuthorizationRequest): Promise<AuthorizationResponse> {
    const { data } = await client.post<AuthorizationResponse>('/authorizations', request);
    return data;
  },

  /**
   * GET /api/v1/authorizations/accounts/{acct_id}
   * Derived from COPAUS0C (CICS transaction CPVS) GATHER-DETAILS.
   */
  async listAuthorizations(
    acctId: number,
    params: ListAuthorizationsParams = {}
  ): Promise<AuthDetailListResponse> {
    const { data } = await client.get<AuthDetailListResponse>(
      `/authorizations/accounts/${acctId}`,
      { params }
    );
    return data;
  },

  /**
   * GET /api/v1/authorizations/details/{auth_id}
   * Derived from COPAUS1C (CICS transaction CPVD) READ-AUTH-RECORD.
   */
  async getAuthorizationDetail(authId: number): Promise<AuthDetailResponse> {
    const { data } = await client.get<AuthDetailResponse>(`/authorizations/details/${authId}`);
    return data;
  },

  /**
   * GET /api/v1/authorizations/accounts/{acct_id}/next
   * Derived from COPAUS1C PROCESS-PF8-KEY → READ-NEXT-AUTH-RECORD (IMS get-next).
   */
  async getNextAuthorization(
    acctId: number,
    currentAuthId: number
  ): Promise<AuthDetailResponse> {
    const { data } = await client.get<AuthDetailResponse>(
      `/authorizations/accounts/${acctId}/next`,
      { params: { current_auth_id: currentAuthId } }
    );
    return data;
  },

  /**
   * POST /api/v1/authorizations/details/{auth_id}/fraud
   * Derived from COPAUS1C MARK-AUTH-FRAUD paragraph (PF5) → EXEC CICS LINK COPAUS2C.
   */
  async markFraud(
    authId: number,
    acctId: number,
    custId: number,
    request: FraudMarkRequest
  ): Promise<FraudMarkResponse> {
    const { data } = await client.post<FraudMarkResponse>(
      `/authorizations/details/${authId}/fraud`,
      request,
      { params: { acct_id: acctId, cust_id: custId } }
    );
    return data;
  },
};
