"use client";

/**
 * Authorization List + Summary Page
 *
 * Maps to COPAU00 BMS screen (COPAUS0C).
 *
 * Layout:
 *   - Search by Account ID (replaces ACCTID input field on screen row 5)
 *   - When found: AuthSummary component (account context, rows 5-12)
 *   - Below: AuthTable component (5 records per page, rows 14-20)
 *   - F7/F8 pagination buttons
 *
 * Navigation:
 *   - Click row → /authorizations/[accountId]/details/[detailId]
 *   - "Process" link → /authorizations/process
 */

import { useCallback, useState } from "react";
import Link from "next/link";
import { getAccountAuthorizations } from "@/lib/api";
import type { PaginatedDetailResponse } from "@/types";
import { AuthSummary } from "@/components/Authorizations/AuthSummary";
import { AuthTable } from "@/components/Authorizations/AuthTable";

export default function AuthorizationsPage() {
  const [accountId, setAccountId] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [data, setData] = useState<PaginatedDetailResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);

  const fetchData = useCallback(async (id: string, pageNum: number) => {
    if (!id.trim()) return;
    setLoading(true);
    setError(null);

    try {
      const result = await getAccountAuthorizations(id.trim(), pageNum);
      setData(result);
      setAccountId(id.trim());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load authorizations");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchData(searchInput, 1);
  };

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
    fetchData(accountId, newPage);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header — mirrors COPAU00 rows 1-3 */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div>
            <p className="text-xs text-gray-400 font-mono">CPVS / COPAUS0C</p>
            <h1 className="text-lg font-semibold text-gray-900">View Authorizations</h1>
          </div>
          <Link
            href="/authorizations/process"
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Process New Authorization
          </Link>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-6 py-6 space-y-6">
        {/* Search Form — Account ID input (ACCTID field, row 5) */}
        <form onSubmit={handleSearch} className="flex gap-3">
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Enter Account ID (e.g. 00000000001)"
            className="flex-1 px-4 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
          />
          <button
            type="submit"
            disabled={loading || !searchInput.trim()}
            className="px-6 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? "Loading..." : "ENTER — Search"}
          </button>
        </form>

        {/* Error message (row 23 equivalent) */}
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Account Summary (rows 5-12) */}
        {data && <AuthSummary summary={data.summary} />}

        {/* Authorization records (rows 14-20) */}
        {data && (
          <>
            <p className="text-xs text-gray-500 -mb-4">
              Type &apos;S&apos; to View Authorization details from the list
            </p>
            <AuthTable
              accountId={accountId}
              details={data.details}
              page={page}
              totalPages={data.total_pages}
              totalCount={data.total_count}
              onPageChange={handlePageChange}
            />
          </>
        )}

        {/* Empty state */}
        {!data && !loading && !error && (
          <div className="text-center py-16 text-gray-400">
            <p className="text-sm">Enter an account ID to view authorizations</p>
            <p className="text-xs mt-1 font-mono">e.g. 00000000001, 00000000002</p>
          </div>
        )}
      </div>
    </div>
  );
}
