'use client';

/**
 * Authorization Summary Page — replaces BMS map COPAU0A (mapset COPAU00).
 * Route: /authorizations
 * COBOL program: COPAUS0C (transaction CPVS)
 *
 * Features (maps COPAUS0C behavior):
 *   - Account ID search input (ACCTIDI — UNPROT field, autoFocus)
 *   - Account/customer summary panel (rows 6-12 of COPAU00)
 *   - Authorization list table (5 rows, rows 16-20 of COPAU00)
 *   - Pagination: Previous/Next (maps PF7/PF8)
 *   - Row click → navigate to detail (maps 'S' selection + ENTER)
 *   - Error messages (ERRMSG field, row 23, RED)
 *   - Modern card layout, NOT green-screen replica
 */

import { useState, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { getAuthorizationDetails } from '@/lib/api';
import type { AuthListResponse, AuthListItem } from '@/types/authorization';
import { FraudStatusBadge } from '@/components/authorizations/FraudStatusBadge';
import {
  formatAuthDate,
  formatAuthTime,
  formatCurrency,
  getApprovalConfig,
} from '@/lib/utils';
import { ApiClientError } from '@/lib/api';

export default function AuthorizationSummaryPage() {
  const router = useRouter();

  // COPAUS0C: WS-ACCT-ID PIC X(11)
  const [accountIdInput, setAccountIdInput] = useState('');
  const [searchedAccountId, setSearchedAccountId] = useState<number | null>(null);
  const [listData, setListData] = useState<AuthListResponse | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  // COPAUS0C: WS-MESSAGE → ERRMSG field (row 23, RED)
  const [errorMessage, setErrorMessage] = useState('');

  /**
   * Handle search — maps COPAUS0C PROCESS-ENTER-KEY + GATHER-DETAILS.
   * Validates account ID (must be numeric, not blank).
   * COPAUS0C error: 'Please enter Acct Id...' | 'Acct Id must be Numeric...'
   */
  async function handleSearch(e: FormEvent, page: number = 1) {
    e.preventDefault();
    setErrorMessage('');

    // Replaces: COPAUS0C IF ACCTIDI = SPACES → WS-MESSAGE = 'Please enter Acct Id...'
    if (!accountIdInput.trim()) {
      setErrorMessage('Please enter an Account ID to search.');
      return;
    }

    // Replaces: COPAUS0C INSPECT numeric check → WS-MESSAGE = 'Acct Id must be Numeric...'
    if (!/^\d+$/.test(accountIdInput.trim())) {
      setErrorMessage('Account ID must be numeric.');
      return;
    }

    const accountId = parseInt(accountIdInput.trim(), 10);
    setIsLoading(true);
    setCurrentPage(page);

    try {
      const data = await getAuthorizationDetails(accountId, {
        page,
        pageSize: 5, // COPAUS0C: 5 rows per screen
      });
      setListData(data);
      setSearchedAccountId(accountId);
    } catch (err) {
      if (err instanceof ApiClientError) {
        if (err.status === 404) {
          // Replaces: IMS GU GE status — account not found
          setErrorMessage(
            `No authorization records found for account ${accountId}.`,
          );
          setListData(null);
        } else if (err.status === 401) {
          router.push('/login');
        } else {
          setErrorMessage(err.apiError.message);
        }
      } else {
        setErrorMessage('An unexpected error occurred. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  }

  /**
   * PF7 — scroll backward. Replaces COPAUS0C PROCESS-PF7-KEY.
   * Error if already at page 1: 'You are already at the top of the page...'
   */
  async function handlePreviousPage(e: FormEvent) {
    if (!listData?.has_previous) {
      setErrorMessage('You are already at the top of the page.');
      return;
    }
    await handleSearch(e, currentPage - 1);
  }

  /**
   * PF8 — scroll forward. Replaces COPAUS0C PROCESS-PF8-KEY.
   * Error if already at last page: 'You are already at the bottom of the page...'
   */
  async function handleNextPage(e: FormEvent) {
    if (!listData?.has_next) {
      setErrorMessage('You are already at the bottom of the page.');
      return;
    }
    await handleSearch(e, currentPage + 1);
  }

  /**
   * Row click — maps COPAUS0C 'S' selection → XCTL to COPAUS1C.
   * Original: SEL000n input field + ENTER → CDEMO-TO-PROGRAM = 'COPAUS1C'.
   */
  function handleRowClick(item: AuthListItem) {
    router.push(`/authorizations/detail/${item.auth_id}`);
  }

  const summary = listData?.summary;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Page header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-gray-900">
                Pending Authorizations
              </h1>
              <p className="text-sm text-gray-500 mt-1">
                COPAUS0C — Transaction CPVS
              </p>
            </div>
            <Link
              href="/menu"
              className="text-sm text-blue-600 hover:text-blue-800 font-medium"
            >
              Back to Menu
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        {/* Search panel — COPAU00 row 5: Account ID input (ACCTIDI, UNPROT, GREEN, autoFocus) */}
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
          <form onSubmit={(e) => handleSearch(e, 1)} className="flex gap-4 items-end">
            <div className="flex-1 max-w-xs">
              <label
                htmlFor="account-id"
                className="block text-sm font-medium text-cyan-700 mb-1"
              >
                Search Account ID
              </label>
              <input
                id="account-id"
                type="text"
                value={accountIdInput}
                onChange={(e) => setAccountIdInput(e.target.value)}
                placeholder="Enter 11-digit account ID"
                maxLength={11}
                autoFocus
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono underline decoration-green-500 underline-offset-2"
              />
            </div>
            <button
              type="submit"
              disabled={isLoading}
              className="px-6 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Searching...' : 'Search'}
            </button>
          </form>
        </div>

        {/* Error message — COPAU00 row 23 ERRMSG field (RED, BRT) */}
        {errorMessage && (
          <div className="bg-red-50 border border-red-300 rounded-md p-4">
            <p className="text-red-700 text-sm font-medium">{errorMessage}</p>
          </div>
        )}

        {/* Account/customer summary panel — COPAU00 rows 6-12 */}
        {summary && (
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
            <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-4">
              Account Summary — {summary.account_id}
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {/* Financial limits row */}
              <div>
                <label className="block text-xs text-cyan-600 uppercase tracking-wider mb-1">
                  Credit Limit
                </label>
                <div className="text-sm font-semibold text-blue-700">
                  {formatCurrency(summary.credit_limit)}
                </div>
              </div>
              <div>
                <label className="block text-xs text-cyan-600 uppercase tracking-wider mb-1">
                  Cash Limit
                </label>
                <div className="text-sm font-semibold text-blue-700">
                  {formatCurrency(summary.cash_limit)}
                </div>
              </div>
              <div>
                <label className="block text-xs text-cyan-600 uppercase tracking-wider mb-1">
                  Credit Balance
                </label>
                <div className="text-sm font-semibold text-blue-700">
                  {formatCurrency(summary.credit_balance)}
                </div>
              </div>
              <div>
                <label className="block text-xs text-cyan-600 uppercase tracking-wider mb-1">
                  Cash Balance
                </label>
                <div className="text-sm font-semibold text-blue-700">
                  {formatCurrency(summary.cash_balance)}
                </div>
              </div>
              {/* Auth counts row */}
              <div>
                <label className="block text-xs text-cyan-600 uppercase tracking-wider mb-1">
                  Approved Count
                </label>
                <div className="text-sm font-semibold text-green-700">
                  {summary.approved_auth_count}
                </div>
              </div>
              <div>
                <label className="block text-xs text-cyan-600 uppercase tracking-wider mb-1">
                  Declined Count
                </label>
                <div className="text-sm font-semibold text-red-600">
                  {summary.declined_auth_count}
                </div>
              </div>
              <div>
                <label className="block text-xs text-cyan-600 uppercase tracking-wider mb-1">
                  Approved Amount
                </label>
                <div className="text-sm font-semibold text-green-700">
                  {formatCurrency(summary.approved_auth_amount)}
                </div>
              </div>
              <div>
                <label className="block text-xs text-cyan-600 uppercase tracking-wider mb-1">
                  Declined Amount
                </label>
                <div className="text-sm font-semibold text-red-600">
                  {formatCurrency(summary.declined_auth_amount)}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Authorization list table — COPAU00 rows 14-20 */}
        {listData && (
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
            <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-gray-700">
                Authorizations
                <span className="ml-2 text-gray-500 font-normal">
                  ({listData.total_count} total — page {currentPage} of{' '}
                  {Math.ceil(listData.total_count / 5)})
                </span>
              </h2>
              <p className="text-xs text-gray-500">
                Click a row to view details
              </p>
            </div>

            {/* Table header — COPAU00 row 14 column labels */}
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Transaction ID
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Time
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      A/D
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Amount
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Fraud
                    </th>
                  </tr>
                </thead>

                {/* 5 authorization rows — COPAU00 rows 16-20 */}
                <tbody className="bg-white divide-y divide-gray-100">
                  {listData.items.length === 0 ? (
                    <tr>
                      <td
                        colSpan={8}
                        className="px-4 py-8 text-center text-sm text-gray-500"
                      >
                        No authorization records found for this account.
                      </td>
                    </tr>
                  ) : (
                    listData.items.map((item) => {
                      const approval = getApprovalConfig(item.approval_status);
                      return (
                        <tr
                          key={item.auth_id}
                          onClick={() => handleRowClick(item)}
                          className="hover:bg-blue-50 cursor-pointer transition-colors"
                          title="Click to view authorization details"
                        >
                          {/* TRNIDnn — BLUE */}
                          <td className="px-4 py-3 text-sm font-mono text-blue-700">
                            {item.transaction_id}
                          </td>
                          {/* PDATEnn */}
                          <td className="px-4 py-3 text-sm text-gray-700">
                            {formatAuthDate(item.auth_date)}
                          </td>
                          {/* PTIMEnn */}
                          <td className="px-4 py-3 text-sm text-gray-700">
                            {formatAuthTime(item.auth_time)}
                          </td>
                          {/* PTYPEnn */}
                          <td className="px-4 py-3 text-sm text-gray-700">
                            {item.auth_type ?? '—'}
                          </td>
                          {/* PAPRVnn — A=green, D=red */}
                          <td className={`px-4 py-3 text-sm font-semibold ${approval.className}`}>
                            {item.approval_status}
                          </td>
                          {/* PSTATnn */}
                          <td className="px-4 py-3 text-sm text-gray-700">
                            {item.match_status}
                          </td>
                          {/* PAMTnnn */}
                          <td className="px-4 py-3 text-sm text-right text-gray-800 font-medium">
                            {formatCurrency(item.amount)}
                          </td>
                          <td className="px-4 py-3">
                            <FraudStatusBadge
                              status={item.fraud_status as 'N' | 'F' | 'R'}
                              compact
                            />
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination — PF7=Previous, PF8=Next */}
            <div className="px-6 py-4 border-t border-gray-100 flex items-center justify-between">
              <p className="text-xs text-gray-500">
                Type S to view authorization details from the list
              </p>
              <div className="flex gap-3">
                {/* PF7=Backward */}
                <button
                  type="button"
                  onClick={(e) => handlePreviousPage(e as unknown as FormEvent)}
                  disabled={!listData.has_previous || isLoading}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  F7 — Previous
                </button>
                {/* PF8=Forward */}
                <button
                  type="button"
                  onClick={(e) => handleNextPage(e as unknown as FormEvent)}
                  disabled={!listData.has_next || isLoading}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  F8 — Next
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
