/**
 * useUsers hook — client-side data fetching for User Administration.
 *
 * Provides a convenient interface for the UserListTable component,
 * encapsulating pagination state management that mirrors COUSR00C's
 * CDEMO-CU00-PAGE-NUM and CDEMO-CU00-NEXT-PAGE-FLG COMMAREA fields.
 */
'use client';

import { useCallback, useEffect, useState } from 'react';

import { ApiError, listUsers } from '@/lib/api';
import type { UserListResponse } from '@/types/user';

interface UseUsersOptions {
  page?: number;
  pageSize?: number;
  searchUserId?: string;
}

interface UseUsersResult {
  data: UserListResponse | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useUsers({
  page = 1,
  pageSize = 10,
  searchUserId,
}: UseUsersOptions = {}): UseUsersResult {
  const [data, setData] = useState<UserListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await listUsers({
        page,
        page_size: pageSize,
        search_user_id: searchUserId,
      });
      setData(result);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Unable to lookup User...');
      }
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, searchUserId]);

  useEffect(() => {
    fetch();
  }, [fetch]);

  return { data, loading, error, refetch: fetch };
}
