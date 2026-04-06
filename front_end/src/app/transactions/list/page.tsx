/**
 * Transaction List page — COTRN00 (BMS map CTRN0A)
 *
 * Route: /transactions/list
 * API: GET /api/v1/transactions
 * COBOL program: COTRN00C
 *
 * COTRN00C behavior replicated:
 *   - 10 rows per page (POPULATE-TRAN-DATA loop limit)
 *   - TRNIDINI filter → WHERE transaction_id >= filter (STARTBR key)
 *   - PF7/PF8 navigation → has_previous/has_next pagination
 *   - CDEMO-CT00-NEXT-PAGE-FLG / CDEMO-CT00-TRNID-FIRST / LAST
 *
 * Modern additions:
 *   - Account ID filter (allows filtering by account's cards)
 *   - Clickable row → /transactions/view?id={transaction_id}
 *   - Amount color-coded: negative=red, positive=green
 */

'use client';

import { useState, useCallback } from 'react';
import Link from 'next/link';
import { listTransactions, extractError } from '@/lib/api';
import type { TransactionListItem, TransactionListResponse } from '@/types';
import { formatCurrency } from '@/components/ui/CurrencyDisplay';

const PAGE_SIZE = 10; // COTRN00C: 10 rows per page

export default function TransactionListPage() {
  const [tranIdFilter, setTranIdFilter] = useState('');
  const [accountIdFilter, setAccountIdFilter] = useState('');
  const [data, setData] = useState<TransactionListResponse | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchPage = useCallback(
    async (page: number, tranFilter?: string, acctFilter?: string) => {
      setLoading(true);
      setError('');
      try {
        const params: Record<string, string | number> = {
          page,
          page_size: PAGE_SIZE,
        };
        const tf = tranFilter ?? tranIdFilter;
        const af = acctFilter ?? accountIdFilter;
        if (tf.trim()) params.tran_id_filter = tf.trim();
        if (af.trim()) params.account_id = parseInt(af.trim(), 10);

        const result = await listTransactions(params);
        setData(result);
        setCurrentPage(page);
      } catch (err) {
        const apiErr = extractError(err);
        setError(apiErr.message);
        setData(null);
      } finally {
        setLoading(false);
      }
    },
    [tranIdFilter, accountIdFilter]
  );

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    fetchPage(1, tranIdFilter, accountIdFilter);
  }

  function handleClear() {
    setTranIdFilter('');
    setAccountIdFilter('');
    setData(null);
    setError('');
    setCurrentPage(1);
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Transaction List</h1>
            <p className="text-sm text-gray-500 mt-1">
              COTRN00C — browse transactions (10 per page)
            </p>
          </div>
          <div className="flex gap-3">
            <Link
              href="/transactions/add"
              className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700"
            >
              Add Transaction
            </Link>
            <Link
              href="/transactions/view"
              className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md text-sm font-medium hover:bg-gray-300"
            >
              View by ID
            </Link>
          </div>
        </div>

        {/* Search / Filter form */}
        <form
          onSubmit={handleSearch}
          className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6"
        >
          <div className="flex flex-wrap gap-4 items-end">
            <div>
              <label
                htmlFor="tranIdFilter"
                className="block text-xs font-medium text-gray-600 mb-1"
              >
                Transaction ID Filter
                <span className="ml-1 text-gray-400">(TRNIDINI — browse from)</span>
              </label>
              <input
                id="tranIdFilter"
                type="text"
                value={tranIdFilter}
                onChange={(e) => setTranIdFilter(e.target.value)}
                maxLength={16}
                placeholder="0000000000000001"
                className="w-48 px-3 py-2 border border-gray-300 rounded-md text-sm font-mono"
              />
            </div>
            <div>
              <label
                htmlFor="accountIdFilter"
                className="block text-xs font-medium text-gray-600 mb-1"
              >
                Account ID
              </label>
              <input
                id="accountIdFilter"
                type="text"
                value={accountIdFilter}
                onChange={(e) => setAccountIdFilter(e.target.value)}
                maxLength={11}
                placeholder="10000000001"
                className="w-40 px-3 py-2 border border-gray-300 rounded-md text-sm font-mono"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Searching...' : 'Search'}
            </button>
            <button
              type="button"
              onClick={handleClear}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md text-sm font-medium hover:bg-gray-300"
            >
              Clear
            </button>
          </div>
        </form>

        {/* Error */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* Results table */}
        {data && (
          <>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden mb-4">
              <div className="px-4 py-3 border-b border-gray-200 flex justify-between items-center">
                <span className="text-sm text-gray-600">
                  Page {data.page} of {Math.ceil(data.total_count / PAGE_SIZE) || 1}
                  &nbsp;&mdash;&nbsp;{data.total_count} total
                </span>
                <span className="text-xs text-gray-400 font-mono">
                  {data.first_item_key && `First: ${data.first_item_key}`}
                  {data.last_item_key && `  Last: ${data.last_item_key}`}
                </span>
              </div>

              {data.items.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  No transactions found. Try a different filter.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200 text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left font-medium text-gray-600">
                          Transaction ID
                        </th>
                        <th className="px-4 py-3 text-left font-medium text-gray-600">
                          Card
                        </th>
                        <th className="px-4 py-3 text-left font-medium text-gray-600">
                          Type
                        </th>
                        <th className="px-4 py-3 text-left font-medium text-gray-600">
                          Description
                        </th>
                        <th className="px-4 py-3 text-right font-medium text-gray-600">
                          Amount
                        </th>
                        <th className="px-4 py-3 text-left font-medium text-gray-600">
                          Date
                        </th>
                        <th className="px-4 py-3 text-left font-medium text-gray-600">
                          Source
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {data.items.map((t: TransactionListItem) => (
                        <TransactionRow key={t.transaction_id} transaction={t} />
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Pagination — PF7 (previous) / PF8 (next) */}
            <div className="flex justify-between items-center">
              <button
                onClick={() => fetchPage(currentPage - 1)}
                disabled={!data.has_previous || loading}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md text-sm font-medium hover:bg-gray-300 disabled:opacity-40"
              >
                PF7 &larr; Previous
              </button>
              <span className="text-sm text-gray-500">Page {currentPage}</span>
              <button
                onClick={() => fetchPage(currentPage + 1)}
                disabled={!data.has_next || loading}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md text-sm font-medium hover:bg-gray-300 disabled:opacity-40"
              >
                Next &rarr; PF8
              </button>
            </div>
          </>
        )}

        {/* Quick nav footer */}
        <div className="mt-8 pt-4 border-t border-gray-200 flex gap-4 text-sm">
          <Link href="/" className="text-blue-600 hover:underline">
            Main Menu
          </Link>
          <Link href="/billing/payment" className="text-blue-600 hover:underline">
            Bill Payment
          </Link>
          <Link href="/reports/transactions" className="text-blue-600 hover:underline">
            Transaction Reports
          </Link>
        </div>
      </div>
    </div>
  );
}

function TransactionRow({ transaction }: { transaction: TransactionListItem }) {
  const amount = parseFloat(transaction.amount);
  const isNeg = !isNaN(amount) && amount < 0;

  return (
    <tr className="hover:bg-blue-50 cursor-pointer">
      <td className="px-4 py-3 font-mono text-xs">
        <Link
          href={`/transactions/view?id=${encodeURIComponent(transaction.transaction_id)}`}
          className="text-blue-600 hover:underline"
        >
          {transaction.transaction_id}
        </Link>
      </td>
      <td className="px-4 py-3 font-mono text-xs text-gray-500">
        ****{transaction.card_number.slice(-4)}
      </td>
      <td className="px-4 py-3 text-center">
        <span className="px-2 py-0.5 bg-gray-100 rounded text-xs font-medium">
          {transaction.transaction_type_code}
        </span>
      </td>
      <td className="px-4 py-3 text-gray-700 max-w-xs truncate">
        {transaction.description || '-'}
      </td>
      <td
        className={`px-4 py-3 text-right font-mono font-semibold ${
          isNeg ? 'text-red-600' : 'text-green-700'
        }`}
      >
        {formatCurrency(transaction.amount)}
      </td>
      <td className="px-4 py-3 text-xs text-gray-500">
        {transaction.original_date || '-'}
      </td>
      <td className="px-4 py-3 text-xs text-gray-400">
        {transaction.transaction_source || '-'}
      </td>
    </tr>
  );
}
