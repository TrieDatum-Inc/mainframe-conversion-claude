"use client";

/**
 * AuthTable Component
 *
 * Paginated table of authorization records (5 per page).
 * Maps to COPAU00 BMS rows 14-20:
 *   - Column headers: Sel | Tran ID | Date | Time | Type | A/D | Status | Amount
 *   - 5 rows per page (PAGE_SIZE = 5 in COPAUS0C)
 *   - F7 (prev) / F8 (next) → Previous/Next buttons
 *
 * Clicking a row navigates to the detail view (COPAUS1C).
 */

import { useRouter } from "next/navigation";
import type { AuthorizationDetail } from "@/types";
import {
  formatCurrency,
  formatDate,
  formatTime,
  getMatchStatusClasses,
  getResponseBadgeClasses,
} from "@/lib/utils";

interface AuthTableProps {
  accountId: string;
  details: AuthorizationDetail[];
  page: number;
  totalPages: number;
  totalCount: number;
  onPageChange: (page: number) => void;
}

export function AuthTable({
  accountId,
  details,
  page,
  totalPages,
  totalCount,
  onPageChange,
}: AuthTableProps) {
  const router = useRouter();

  const handleRowClick = (detail: AuthorizationDetail) => {
    router.push(`/authorizations/${accountId}/details/${detail.id}`);
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
          Authorization Records
        </h3>
        <span className="text-xs text-gray-500">
          {totalCount} total &mdash; page {page} of {totalPages}
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Transaction ID
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Date
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Time
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Type
              </th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                A/D
              </th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                Status
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                Amount
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {details.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-gray-400 text-sm">
                  No authorization records found
                </td>
              </tr>
            ) : (
              details.map((detail) => (
                <tr
                  key={detail.id}
                  onClick={() => handleRowClick(detail)}
                  className="hover:bg-blue-50 cursor-pointer transition-colors"
                >
                  <td className="px-4 py-3 font-mono text-xs text-gray-700">
                    {detail.transaction_id}
                  </td>
                  <td className="px-4 py-3 text-gray-700">
                    {formatDate(detail.auth_date)}
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {formatTime(detail.auth_time)}
                  </td>
                  <td className="px-4 py-3 text-gray-700">{detail.auth_type}</td>
                  <td className="px-4 py-3 text-center">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-xs font-bold ${getResponseBadgeClasses(
                        detail.auth_response_code === "00" ? "A" : "D"
                      )}`}
                    >
                      {detail.auth_response_code === "00" ? "A" : "D"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-xs ${getMatchStatusClasses(
                        detail.match_status
                      )}`}
                    >
                      {detail.match_status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-medium text-gray-900">
                    {formatCurrency(detail.transaction_amount)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination (F7/F8 equivalent) */}
      <div className="px-6 py-3 border-t border-gray-100 flex items-center justify-between">
        <p className="text-xs text-gray-500">
          Type &apos;S&apos; to select — click any row to view authorization details
        </p>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="px-3 py-1 text-xs rounded border border-gray-300 text-gray-600 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            &larr; F7 Backward
          </button>
          <span className="text-xs text-gray-500">
            {page} / {totalPages}
          </span>
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            className="px-3 py-1 text-xs rounded border border-gray-300 text-gray-600 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            F8 Forward &rarr;
          </button>
        </div>
      </div>
    </div>
  );
}
