/**
 * Pagination hook for keyset-based pagination.
 * Maps to COBOL STARTBR/READNEXT/READPREV browse patterns.
 */
'use client';

import { useState, useCallback } from 'react';

interface PaginationState {
  cursor: string | undefined;
  direction: 'forward' | 'backward';
  page: number;
}

interface UsePaginationReturn {
  cursor: string | undefined;
  direction: 'forward' | 'backward';
  page: number;
  goNext: (nextCursor: string | null | undefined) => void;
  goPrev: (prevCursor: string | null | undefined) => void;
  reset: () => void;
}

export function usePagination(): UsePaginationReturn {
  const [state, setState] = useState<PaginationState>({
    cursor: undefined,
    direction: 'forward',
    page: 1,
  });

  // PF8 equivalent — READNEXT / next page
  const goNext = useCallback((nextCursor: string | null | undefined) => {
    if (!nextCursor) return;
    setState((prev) => ({
      cursor: nextCursor,
      direction: 'forward',
      page: prev.page + 1,
    }));
  }, []);

  // PF7 equivalent — READPREV / previous page
  const goPrev = useCallback((prevCursor: string | null | undefined) => {
    if (!prevCursor) return;
    setState((prev) => ({
      cursor: prevCursor,
      direction: 'backward',
      page: Math.max(1, prev.page - 1),
    }));
  }, []);

  const reset = useCallback(() => {
    setState({ cursor: undefined, direction: 'forward', page: 1 });
  }, []);

  return {
    cursor: state.cursor,
    direction: state.direction,
    page: state.page,
    goNext,
    goPrev,
    reset,
  };
}

/**
 * Numeric keyset pagination (used by authorizations).
 */
interface NumericPaginationState {
  cursor: number | undefined;
  page: number;
}

interface UseNumericPaginationReturn {
  cursor: number | undefined;
  page: number;
  goNext: (nextCursor: number | null | undefined) => void;
  goPrev: (prevCursor: number | null | undefined) => void;
  reset: () => void;
}

export function useNumericPagination(): UseNumericPaginationReturn {
  const [state, setState] = useState<NumericPaginationState>({
    cursor: undefined,
    page: 1,
  });

  const goNext = useCallback((nextCursor: number | null | undefined) => {
    if (nextCursor === null || nextCursor === undefined) return;
    setState((prev) => ({ cursor: nextCursor, page: prev.page + 1 }));
  }, []);

  const goPrev = useCallback((prevCursor: number | null | undefined) => {
    if (prevCursor === null || prevCursor === undefined) return;
    setState((prev) => ({ cursor: prevCursor, page: Math.max(1, prev.page - 1) }));
  }, []);

  const reset = useCallback(() => {
    setState({ cursor: undefined, page: 1 });
  }, []);

  return { cursor: state.cursor, page: state.page, goNext, goPrev, reset };
}
