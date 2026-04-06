/**
 * Card List page — COCRDLI (BMS map CCRDLIA)
 *
 * Route: /cards/list
 * API: GET /api/v1/cards
 * COBOL program: COCRDLIC
 *
 * COCRDLIC browsed CARDDAT VSAM using STARTBR/READNEXT/READPREV with a
 * 7-row display page. This modern equivalent:
 *   - Filters by optional account_id or card_number prefix
 *   - Default page_size=7 matches WS-MAX-SCREEN-LINES=7 from COCRDLIC
 *   - Card numbers shown masked (last 4 digits) per PCI-DSS
 *   - Clicking a row navigates to /cards/view?cardNumber={full_number}
 *
 * PF key equivalents:
 *   PF7 (prev page) → "Previous" button
 *   PF8 (next page) → "Next" button
 *   PF3 (exit)      → "Back" button
 *   Enter (select)  → row click → /cards/view
 *
 * Note: CardListResponse uses `items` field (not `cards`).
 *       CardListItem does not include embossed_name — list view shows number, account, status only.
 */

'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { listCards, extractError } from '@/lib/api';
import type { CardListItem, CardListResponse } from '@/types';
import { MessageBar } from '@/components/ui/MessageBar';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import StatusBadge from '@/components/ui/StatusBadge';

const PAGE_SIZE = 7; // matches COCRDLIC WS-MAX-SCREEN-LINES=7

export default function CardListPage() {
  const router = useRouter();

  // Filter inputs (ACCT00SI, CRDNUM field on CCRDLIA map)
  const [accountIdFilter, setAccountIdFilter] = useState('');
  const [cardNumberFilter, setCardNumberFilter] = useState('');

  // State
  const [result, setResult] = useState<CardListResponse | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [hasSearched, setHasSearched] = useState(false);

  const fetchCards = useCallback(
    async (page: number, acctId: string, cardNum: string) => {
      setLoading(true);
      setError('');
      try {
        const data = await listCards({
          page,
          page_size: PAGE_SIZE,
          account_id: acctId ? parseInt(acctId, 10) : undefined,
          card_number: cardNum.trim() || undefined,
        });
        setResult(data);
        setCurrentPage(page);
        setHasSearched(true);
      } catch (err) {
        const apiErr = extractError(err);
        setError(apiErr.message);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (accountIdFilter && !/^\d{1,11}$/.test(accountIdFilter.trim())) {
      setError('Account ID must be numeric (up to 11 digits)');
      return;
    }
    fetchCards(1, accountIdFilter.trim(), cardNumberFilter.trim());
  }

  function handleClear() {
    setAccountIdFilter('');
    setCardNumberFilter('');
    setResult(null);
    setError('');
    setHasSearched(false);
    setCurrentPage(1);
  }

  function handlePrev() {
    if (currentPage > 1) {
      fetchCards(currentPage - 1, accountIdFilter.trim(), cardNumberFilter.trim());
    }
  }

  function handleNext() {
    if (result?.has_next) {
      fetchCards(currentPage + 1, accountIdFilter.trim(), cardNumberFilter.trim());
    }
  }

  function handleRowClick(card: CardListItem) {
    router.push(`/cards/view?cardNumber=${encodeURIComponent(card.card_number)}`);
  }

  const totalPages = result ? Math.ceil(result.total_count / PAGE_SIZE) : 0;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Page header */}
      <div className="bg-blue-900 text-white px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-yellow-300">CardDemo</h1>
            <p className="text-sm text-blue-200">Credit Card Demo Application</p>
          </div>
          <div className="text-sm text-blue-200">
            <span className="font-medium text-white">COCRDLI</span> — Credit Card List
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-6">
        {/* Filter form */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Search Credit Cards</h2>
          <form onSubmit={handleSearch} className="flex flex-wrap gap-4 items-end">
            <div className="flex-1 min-w-[180px]">
              <label htmlFor="acctFilter" className="block text-sm font-medium text-gray-700 mb-1">
                Account ID
              </label>
              <input
                id="acctFilter"
                type="text"
                value={accountIdFilter}
                onChange={(e) => setAccountIdFilter(e.target.value)}
                maxLength={11}
                placeholder="Filter by account ID"
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm
                           focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                           font-mono"
              />
            </div>
            <div className="flex-1 min-w-[200px]">
              <label htmlFor="cardFilter" className="block text-sm font-medium text-gray-700 mb-1">
                Card Number
              </label>
              <input
                id="cardFilter"
                type="text"
                value={cardNumberFilter}
                onChange={(e) => setCardNumberFilter(e.target.value)}
                maxLength={16}
                placeholder="Filter by card number"
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm
                           focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                           font-mono"
              />
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={loading}
                className="px-5 py-2 bg-blue-600 text-white rounded-md text-sm font-medium
                           hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Loading...' : 'Search'}
              </button>
              <button
                type="button"
                onClick={handleClear}
                className="px-5 py-2 bg-gray-100 text-gray-700 rounded-md text-sm font-medium
                           hover:bg-gray-200 border border-gray-300"
              >
                Clear
              </button>
              <button
                type="button"
                onClick={() => router.back()}
                className="px-5 py-2 bg-gray-100 text-gray-700 rounded-md text-sm font-medium
                           hover:bg-gray-200 border border-gray-300"
              >
                Back
              </button>
            </div>
          </form>
        </div>

        {error && <MessageBar message={error} color="red" className="mb-4" />}

        {loading && (
          <div className="flex justify-center py-12">
            <LoadingSpinner />
          </div>
        )}

        {/* Results table */}
        {hasSearched && !loading && result && (
          <div className="bg-white rounded-lg shadow">
            {/* Table header with count */}
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h3 className="text-base font-semibold text-gray-900">
                Cards
                {result.total_count > 0 && (
                  <span className="ml-2 text-sm font-normal text-gray-500">
                    ({result.total_count} total)
                  </span>
                )}
              </h3>
              <span className="text-sm text-gray-500">
                Page {currentPage} of {totalPages || 1}
              </span>
            </div>

            {result.items.length === 0 ? (
              <div className="px-6 py-10 text-center text-gray-500 text-sm">
                No cards found matching your search criteria.
              </div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Card Number
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Account ID
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {result.items.map((card) => (
                        <tr
                          key={card.card_number}
                          onClick={() => handleRowClick(card)}
                          className="hover:bg-blue-50 cursor-pointer transition-colors"
                        >
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="font-mono text-sm text-gray-900">
                              {card.card_number_masked}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                            {card.account_id}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <StatusBadge
                              status={card.active_status}
                              activeLabel="Active"
                              inactiveLabel="Inactive"
                            />
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-600 hover:text-blue-800">
                            View Details
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Pagination — PF7 / PF8 equivalent */}
                <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
                  <button
                    onClick={handlePrev}
                    disabled={!result.has_previous || loading}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300
                               rounded-md hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    PF7 — Previous
                  </button>
                  <span className="text-sm text-gray-600">
                    Showing {(currentPage - 1) * PAGE_SIZE + 1}–
                    {Math.min(currentPage * PAGE_SIZE, result.total_count)} of {result.total_count}
                  </span>
                  <button
                    onClick={handleNext}
                    disabled={!result.has_next || loading}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300
                               rounded-md hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    PF8 — Next
                  </button>
                </div>
              </>
            )}
          </div>
        )}

        {hasSearched && !loading && result && result.items.length > 0 && (
          <p className="mt-3 text-xs text-gray-400 text-center">
            Click any row to view card details. Card numbers are masked per PCI-DSS (last 4 digits only).
          </p>
        )}
      </div>
    </div>
  );
}
