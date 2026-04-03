"use client";
import { useCallback, useEffect, useState } from "react";
import { fetchCardList } from "@/lib/api";
import type { CardListParams, CardListResponse } from "@/types/card";

interface UseCardListState { data: CardListResponse | null; isLoading: boolean; error: string | null; page: number; }
interface UseCardListReturn extends UseCardListState { goNextPage: () => void; goPrevPage: () => void; refresh: () => void; applyFilters: (acctId: string, cardNumFilter: string) => void; canGoBack: boolean; canGoForward: boolean; }

export function useCardList(pageSize: number = 7): UseCardListReturn {
  const [state, setState] = useState<UseCardListState>({ data: null, isLoading: false, error: null, page: 1 });
  const [cursorStack, setCursorStack] = useState<Array<string | undefined>>([undefined]);
  const [filters, setFilters] = useState<{ acctId?: string; cardNumFilter?: string }>({});

  const loadPage = useCallback(async (cursor: string | undefined, pageNum: number) => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }));
    try {
      const params: CardListParams = { page_size: pageSize, page: pageNum };
      if (cursor) params.cursor = cursor;
      if (filters.acctId) params.acct_id = filters.acctId;
      if (filters.cardNumFilter) params.card_num_filter = filters.cardNumFilter;
      const result = await fetchCardList(params);
      setState({ data: result, isLoading: false, error: null, page: pageNum });
    } catch (err) {
      setState((prev) => ({ ...prev, isLoading: false, error: err instanceof Error ? err.message : "Failed to load cards" }));
    }
  }, [pageSize, filters]);

  useEffect(() => { loadPage(undefined, 1); setCursorStack([undefined]); }, [filters]); // eslint-disable-line react-hooks/exhaustive-deps

  const goNextPage = useCallback(() => {
    if (!state.data?.has_next_page || !state.data.next_cursor) return;
    const nextCursor = state.data.next_cursor;
    setCursorStack((prev) => [...prev, nextCursor]);
    loadPage(nextCursor, state.page + 1);
  }, [state.data, state.page, loadPage]);

  const goPrevPage = useCallback(() => {
    if (cursorStack.length <= 1) return;
    const newStack = cursorStack.slice(0, -1);
    setCursorStack(newStack);
    loadPage(newStack[newStack.length - 1], state.page - 1);
  }, [cursorStack, state.page, loadPage]);

  const refresh = useCallback(() => loadPage(cursorStack[cursorStack.length - 1], state.page), [cursorStack, state.page, loadPage]);
  const applyFilters = useCallback((acctId: string, cardNumFilter: string) => setFilters({ acctId: acctId.trim() || undefined, cardNumFilter: cardNumFilter.trim() || undefined }), []);

  return { ...state, goNextPage, goPrevPage, refresh, applyFilters, canGoBack: cursorStack.length > 1, canGoForward: Boolean(state.data?.has_next_page) };
}
