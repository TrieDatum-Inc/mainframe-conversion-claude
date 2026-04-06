"use client";

/**
 * AccountTable — paginated, searchable account list.
 *
 * Modernizes COCRDLIC/COACTVWC browse pattern:
 *   - Search by account_id (replaces ACCTSID input field)
 *   - Paginated table (replaces F7/F8 paging)
 *   - Click row to view detail (replaces 'S' row selector)
 *
 * Columns mirror COACTVWC display fields: account_id, status,
 * current_balance, credit_limit, open_date.
 */

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { AccountListItem } from "@/types";

interface AccountTableProps {
  items: AccountListItem[];
  total: number;
  page: number;
  totalPages: number;
  searchValue: string;
  isLoading: boolean;
  onSearch: (value: string) => void;
  onPageChange: (page: number) => void;
}

function formatBalance(value: string): string {
  const num = parseFloat(value);
  return isNaN(num)
    ? value
    : num.toLocaleString("en-US", { style: "currency", currency: "USD" });
}

function formatDate(value: string | null): string {
  if (!value) return "--";
  return new Date(value).toLocaleDateString("en-US");
}

export function AccountTable({
  items,
  total,
  page,
  totalPages,
  searchValue,
  isLoading,
  onSearch,
  onPageChange,
}: AccountTableProps) {
  const router = useRouter();
  const [inputValue, setInputValue] = useState(searchValue);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(inputValue.trim());
  };

  return (
    <div className="space-y-4">
      {/* Search bar */}
      <form onSubmit={handleSearchSubmit} className="flex gap-2">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Search by account ID..."
          className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          maxLength={11}
        />
        <button
          type="submit"
          className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2"
        >
          Search
        </button>
        {searchValue && (
          <button
            type="button"
            onClick={() => {
              setInputValue("");
              onSearch("");
            }}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Clear
          </button>
        )}
      </form>

      {/* Table */}
      <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Account ID
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Status
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                Balance
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                Credit Limit
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Open Date
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {isLoading ? (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center text-sm text-gray-500">
                  Loading...
                </td>
              </tr>
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center text-sm text-gray-500">
                  No accounts found
                </td>
              </tr>
            ) : (
              items.map((account) => (
                <tr
                  key={account.account_id}
                  onClick={() => router.push(`/accounts/${account.account_id}`)}
                  className="cursor-pointer hover:bg-brand-50 transition-colors"
                >
                  <td className="whitespace-nowrap px-6 py-4 text-sm font-mono font-medium text-brand-700">
                    {account.account_id}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm">
                    <span
                      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                        account.active_status === "Y"
                          ? "bg-green-100 text-green-800"
                          : "bg-red-100 text-red-800"
                      }`}
                    >
                      {account.active_status === "Y" ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-right text-sm text-gray-900">
                    {formatBalance(account.current_balance)}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-right text-sm text-gray-900">
                    {formatBalance(account.credit_limit)}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                    {formatDate(account.open_date)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between text-sm text-gray-700">
        <span>
          {total > 0
            ? `Showing page ${page} of ${totalPages} (${total} total)`
            : "No results"}
        </span>
        <div className="flex gap-2">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1 || isLoading}
            className="rounded border border-gray-300 px-3 py-1 disabled:opacity-40 hover:bg-gray-50"
          >
            Previous
          </button>
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages || isLoading}
            className="rounded border border-gray-300 px-3 py-1 disabled:opacity-40 hover:bg-gray-50"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
