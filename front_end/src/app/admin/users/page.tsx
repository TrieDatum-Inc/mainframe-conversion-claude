'use client';

/**
 * User List page — /admin/users
 *
 * COBOL origin: COUSR00C (Transaction CU00), BMS map COUSR0A
 *
 * Replaces:
 *   - STARTBR/READNEXT/READPREV browse on USRSEC VSAM
 *   - 10-row table: USRID1O–USRID10O, FNAME1O–FNAME10O, LNAME1O–LNAME10O, UTYPE1O–UTYPE10O
 *   - USRIDINI filter input
 *   - SEL0001I–SEL0010I row selectors ('U'=update, 'D'=delete) → per-row buttons
 *   - PF7 (previous page) / PF8 (next page) → Previous/Next buttons
 *   - PF3 → Back to Admin Menu
 *   - PF2 → Add New User (COUSR01C)
 *
 * Admin only: guarded by middleware.ts checking user_type='A'.
 */

import React, { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { listUsers } from '@/lib/api';
import { extractError } from '@/lib/api';
import { UserTable } from '@/components/lists/UserTable';
import { MessageBar } from '@/components/ui/MessageBar';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import type { UserListResponse } from '@/types';

const PAGE_SIZE = 10; // COUSR00C: fixed 10 rows per page

export default function UserListPage() {
  const router = useRouter();
  const [data, setData] = useState<UserListResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [page, setPage] = useState(1);
  const [filterInput, setFilterInput] = useState('');
  const [activeFilter, setActiveFilter] = useState('');

  const fetchUsers = useCallback(
    async (currentPage: number, filter: string) => {
      setLoading(true);
      setError('');
      try {
        const result = await listUsers({
          page: currentPage,
          page_size: PAGE_SIZE,
          user_id_filter: filter || undefined,
        });
        setData(result);
      } catch (err) {
        const apiError = extractError(err);
        setError(apiError.message);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    fetchUsers(page, activeFilter);
  }, [fetchUsers, page, activeFilter]);

  /** ENTER key: apply filter and reset to page 1 (COUSR00C USRIDINI filter) */
  const handleFilterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    setActiveFilter(filterInput.trim().toUpperCase());
  };

  /** PF7 — previous page (COUSR00C READPREV direction) */
  const handlePreviousPage = () => {
    if (page > 1) setPage((p) => p - 1);
  };

  /** PF8 — next page (COUSR00C READNEXT direction) */
  const handleNextPage = () => {
    if (data?.has_next) setPage((p) => p + 1);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Page header — maps COUSR00C standard header (title, program name, date/time) */}
      <header className="bg-blue-900 text-white py-3 px-6">
        <div className="flex justify-between items-center">
          <div>
            <p className="text-xs text-blue-300">COUSR00C | CU00</p>
            <h1 className="text-lg font-bold">User List / Management</h1>
          </div>
          <div className="text-xs text-blue-300 text-right">
            <p>CardDemo Administration</p>
            <p>Admin Only</p>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-6 space-y-4">
        {/* Message bars — ERRMSGO row 23 equivalent */}
        {error && <MessageBar message={error} variant="error" />}
        {success && <MessageBar message={success} variant="success" />}

        {/* Filter and Add controls */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-end">
            {/* USRIDINI filter — COUSR00C STARTBR at entered key */}
            <form onSubmit={handleFilterSubmit} className="flex gap-2 flex-1">
              <div className="flex-1">
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Filter by User ID (browse from this point)
                </label>
                <input
                  type="text"
                  maxLength={8}
                  value={filterInput}
                  onChange={(e) => setFilterInput(e.target.value.toUpperCase())}
                  placeholder="e.g. USER0005"
                  className="w-full border border-gray-300 rounded px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <button
                type="submit"
                className="self-end px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 transition-colors"
              >
                Search
              </button>
              {activeFilter && (
                <button
                  type="button"
                  onClick={() => { setFilterInput(''); setActiveFilter(''); setPage(1); }}
                  className="self-end px-3 py-2 bg-gray-100 text-gray-700 text-sm rounded hover:bg-gray-200 transition-colors"
                >
                  Clear
                </button>
              )}
            </form>

            {/* PF2 — Add New User → COUSR01C */}
            <Link
              href="/admin/users/add"
              className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded hover:bg-green-700 transition-colors whitespace-nowrap"
            >
              + Add New User
            </Link>
          </div>
        </div>

        {/* User table */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          {loading ? (
            <LoadingSpinner label="Loading users..." />
          ) : (
            <>
              <div className="flex justify-between items-center mb-3">
                <p className="text-sm text-gray-600">
                  {data ? (
                    <>
                      Showing page {data.page} of{' '}
                      {Math.ceil(data.total_count / PAGE_SIZE)} (
                      {data.total_count} total users)
                      {activeFilter && (
                        <span className="ml-2 text-blue-600">
                          filtered from: <code className="font-mono">{activeFilter}</code>
                        </span>
                      )}
                    </>
                  ) : (
                    'No data loaded'
                  )}
                </p>
              </div>

              <UserTable users={data?.items ?? []} />

              {/* PF7/PF8 pagination buttons */}
              <div className="flex justify-between items-center mt-4">
                <button
                  type="button"
                  onClick={handlePreviousPage}
                  disabled={!data?.has_previous}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  Previous Page (PF7)
                </button>
                <span className="text-sm text-gray-500">Page {page}</span>
                <button
                  type="button"
                  onClick={handleNextPage}
                  disabled={!data?.has_next}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  Next Page (PF8)
                </button>
              </div>
            </>
          )}
        </div>

        {/* PF3 — Back to Admin Menu */}
        <div className="flex justify-start">
          <Link
            href="/admin/menu"
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded transition-colors"
          >
            Back to Admin Menu (PF3)
          </Link>
        </div>
      </main>
    </div>
  );
}
