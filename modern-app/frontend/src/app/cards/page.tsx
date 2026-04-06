"use client";

/**
 * /cards — Card list page.
 *
 * Modernizes COCRDLIC (Credit Card List Browse):
 *   - Paginated 7 per page (F7/F8 navigation)
 *   - Filter by account number (ACCTSID input)
 *   - Filter by card number (CARDSID input)
 *   - Row actions: View (CCDL) and Edit (CCUP) — replaces 'S'/'U' selectors
 */

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { apiClient } from "@/lib/api";
import { CardTable } from "@/components/Cards/CardTable";
import type { CardListItem } from "@/types";

const PAGE_SIZE = 7; // COCRDLIC: exactly 7 rows per page

export default function CardsPage() {
  const { token } = useAuth();
  const [items, setItems] = useState<CardListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [accountFilter, setAccountFilter] = useState("");
  const [cardFilter, setCardFilter] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadCards = useCallback(
    async (acctId: string, cardNum: string, p: number) => {
      if (!token) return;
      setIsLoading(true);
      setError(null);
      try {
        const result = await apiClient.listCards(token, {
          account_id: acctId || undefined,
          card_number: cardNum || undefined,
          page: p,
          page_size: PAGE_SIZE,
        });
        setItems(result.items);
        setTotal(result.total);
        setPage(result.page);
        setTotalPages(result.total_pages);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load cards");
      } finally {
        setIsLoading(false);
      }
    },
    [token]
  );

  useEffect(() => {
    loadCards("", "", 1);
  }, [loadCards]);

  const handleFilter = (acctId: string, cardNum: string) => {
    setAccountFilter(acctId);
    setCardFilter(cardNum);
    setPage(1);
    loadCards(acctId, cardNum, 1);
  };

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
    loadCards(accountFilter, cardFilter, newPage);
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Credit Cards</h1>
        <p className="mt-1 text-sm text-gray-500">
          View and manage credit cards
        </p>
      </div>

      {error && (
        <div className="mb-4 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <CardTable
        items={items}
        total={total}
        page={page}
        totalPages={totalPages}
        accountFilter={accountFilter}
        cardFilter={cardFilter}
        isLoading={isLoading}
        onFilter={handleFilter}
        onPageChange={handlePageChange}
      />
    </div>
  );
}
