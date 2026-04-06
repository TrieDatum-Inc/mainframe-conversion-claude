"use client";

/**
 * /accounts — Account list page.
 *
 * Modernizes COACTVWC/COCRDLIC browse pattern:
 *   - Searchable, paginated account table
 *   - Clicking a row navigates to /accounts/[id]
 *
 * Authentication: uses JWT from AuthContext (maps to CICS COMMAREA check).
 */

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { apiClient } from "@/lib/api";
import { AccountTable } from "@/components/Accounts/AccountTable";
import type { AccountListItem } from "@/types";

const PAGE_SIZE = 20;

export default function AccountsPage() {
  const { token } = useAuth();
  const [items, setItems] = useState<AccountListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [searchValue, setSearchValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadAccounts = useCallback(
    async (search: string, p: number) => {
      if (!token) return;
      setIsLoading(true);
      setError(null);
      try {
        const result = await apiClient.listAccounts(token, {
          account_id: search || undefined,
          page: p,
          page_size: PAGE_SIZE,
        });
        setItems(result.items);
        setTotal(result.total);
        setPage(result.page);
        setTotalPages(result.total_pages);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load accounts");
      } finally {
        setIsLoading(false);
      }
    },
    [token]
  );

  useEffect(() => {
    loadAccounts(searchValue, 1);
  }, [loadAccounts]);

  const handleSearch = (value: string) => {
    setSearchValue(value);
    setPage(1);
    loadAccounts(value, 1);
  };

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
    loadAccounts(searchValue, newPage);
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Accounts</h1>
        <p className="mt-1 text-sm text-gray-500">
          View and manage credit card accounts
        </p>
      </div>

      {error && (
        <div className="mb-4 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <AccountTable
        items={items}
        total={total}
        page={page}
        totalPages={totalPages}
        searchValue={searchValue}
        isLoading={isLoading}
        onSearch={handleSearch}
        onPageChange={handlePageChange}
      />
    </div>
  );
}
