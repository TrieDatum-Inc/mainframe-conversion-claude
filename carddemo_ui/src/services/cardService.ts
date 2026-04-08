/**
 * Card service — wraps all /api/v1/cards/* endpoints.
 * Derived from COCRDLIC, COCRDSLC, COCRDUPC.
 */
import client from './apiClient';
import type {
  CardListResponse,
  CardResponse,
  CardUpdateRequest,
} from '@/lib/types/api';

export interface ListCardsParams {
  account_id?: number;
  cursor?: string;
  limit?: number;
  direction?: 'forward' | 'backward';
}

export const cardService = {
  /**
   * GET /api/v1/cards
   * Derived from COCRDLIC BROWSE-CARDS paragraph (STARTBR CARDAIX).
   */
  async listCards(params: ListCardsParams = {}): Promise<CardListResponse> {
    const { data } = await client.get<CardListResponse>('/cards', { params });
    return data;
  },

  /**
   * GET /api/v1/cards/{card_num}
   * Derived from COCRDSLC READ-CARD-DATA paragraph.
   */
  async getCard(cardNum: string): Promise<CardResponse> {
    const { data } = await client.get<CardResponse>(`/cards/${cardNum}`);
    return data;
  },

  /**
   * PUT /api/v1/cards/{card_num}
   * Derived from COCRDUPC PROCESS-ENTER-KEY → EXEC CICS REWRITE FILE('CARDDAT').
   * Only embossed_name and active_status are updatable.
   */
  async updateCard(cardNum: string, request: CardUpdateRequest): Promise<CardResponse> {
    const { data } = await client.put<CardResponse>(`/cards/${cardNum}`, request);
    return data;
  },
};
