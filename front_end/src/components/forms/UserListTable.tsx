/**
 * UserListTable — COUSR00C (CU00) User List screen conversion.
 *
 * BMS Map: COUSR0A (COUSR00 mapset), 24x80
 *
 * BMS column layout (10 rows × 5 cols):
 *   Col Sel  (col 6,  len 1)  → edit/delete action buttons
 *   Col User ID (col 12, len 8)
 *   Col First Name (col 24, len 20)
 *   Col Last Name (col 48, len 20)
 *   Col Type (col 73, len 1)
 *
 * Row selection mapping (COUSR00C PROCESS-ENTER-KEY):
 *   'U' → Edit button → navigate to /users/{id}/edit
 *   'D' → Delete button → navigate to /users/{id}/delete
 *
 * Pagination (COUSR00C PF7/PF8):
 *   F7=Backward → prev page
 *   F8=Forward  → next page
 *   Top-of-list guard: 'You are already at the top of the page...'
 *   Bottom-of-list guard: 'You are already at the bottom of the page...'
 */
'use client';

import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';

import { Button } from '@/components/ui/Button';
import { StatusMessage } from '@/components/ui/StatusMessage';
import { ApiError, listUsers } from '@/lib/api';
import { formatUserType, getErrorMessage } from '@/lib/utils';
import type { UserListItem, UserListResponse } from '@/types/user';

const PAGE_SIZE = 10; // COUSR00C: 10 rows per BMS screen

export function UserListTable() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const currentPage = Number(searchParams.get('page') || '1');
  const searchUserId = searchParams.get('search') || '';

  const [data, setData] = useState<UserListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusMessage, setStatusMessage] = useState<{
    text: string;
    type: 'success' | 'error' | 'info';
  } | null>(null);
  const [searchInput, setSearchInput] = useState(searchUserId);

  const fetchPage = useCallback(
    async (page: number, search: string) => {
      setLoading(true);
      setStatusMessage(null);
      try {
        const result = await listUsers({
          page,
          page_size: PAGE_SIZE,
          search_user_id: search || undefined,
        });
        setData(result);

        if (result.users.length === 0 && page === 1) {
          setStatusMessage({
            text: 'You are at the top of the page...',
            type: 'info',
          });
        }
      } catch (err) {
        if (err instanceof ApiError) {
          setStatusMessage({ text: err.message, type: 'error' });
        } else {
          setStatusMessage({ text: getErrorMessage(err), type: 'error' });
        }
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    fetchPage(currentPage, searchUserId);
  }, [currentPage, searchUserId, fetchPage]);

  const navigatePage = (page: number) => {
    const params = new URLSearchParams();
    params.set('page', page.toString());
    if (searchInput) params.set('search', searchInput);
    router.push(`/users?${params.toString()}`);
  };

  // PF7 = Backward — COUSR00C PROCESS-PF7-KEY
  const handlePrevPage = () => {
    if (!data?.has_prev_page) {
      // COUSR00C: 'You are already at the top of the page...'
      setStatusMessage({
        text: 'You are already at the top of the page...',
        type: 'info',
      });
      return;
    }
    navigatePage(currentPage - 1);
  };

  // PF8 = Forward — COUSR00C PROCESS-PF8-KEY
  const handleNextPage = () => {
    if (!data?.has_next_page) {
      // COUSR00C: 'You are already at the bottom of the page...'
      setStatusMessage({
        text: 'You are already at the bottom of the page...',
        type: 'info',
      });
      return;
    }
    navigatePage(currentPage + 1);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const params = new URLSearchParams();
    params.set('page', '1');
    if (searchInput) params.set('search', searchInput);
    router.push(`/users?${params.toString()}`);
  };

  return (
    <div className="space-y-4">
      {/* Search field — Row 6 USRIDIN (COUSR00C) */}
      <form onSubmit={handleSearch} className="flex gap-2 items-end">
        <div>
          <label
            htmlFor="search-user-id"
            className="block text-sm font-medium text-cyan-700 mb-1"
          >
            Search User ID:
          </label>
          <input
            id="search-user-id"
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            maxLength={8}
            placeholder="User ID"
            className="rounded-md border border-gray-300 px-3 py-2 text-sm w-32 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <Button type="submit" size="sm">
          Search (Enter)
        </Button>
        {searchInput && (
          <Button
            type="button"
            size="sm"
            variant="ghost"
            onClick={() => {
              setSearchInput('');
              router.push('/users');
            }}
          >
            Clear
          </Button>
        )}
      </form>

      {/* Page number — Row 4 PAGENUM field */}
      {data && (
        <div className="flex items-center justify-between text-sm text-gray-500">
          <span>
            Page: <strong className="text-blue-700">{currentPage}</strong>
            {' — '}
            {data.total_count} total user{data.total_count !== 1 ? 's' : ''}
          </span>
          <span className="text-xs italic text-neutral-500">
            Type U to Update or D to Delete a User from the list
          </span>
        </div>
      )}

      {/* Status message — ERRMSG field */}
      {statusMessage && (
        <StatusMessage message={statusMessage.text} type={statusMessage.type} />
      )}

      {loading ? (
        <div className="text-center py-8 text-gray-500 text-sm">Loading users...</div>
      ) : (
        <>
          {/* User list table — 10 rows (COUSR00C WS-IDX 1-10) */}
          <div className="overflow-x-auto rounded-md border border-gray-200">
            <table className="w-full text-sm">
              <thead>
                {/* Column headings — Row 8 from BMS map */}
                <tr className="bg-gray-100 border-b border-gray-200">
                  <th className="px-3 py-2 text-left font-medium text-gray-600 w-8">Sel</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-600 w-24">User ID</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-600">First Name</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-600">Last Name</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-600 w-16">Type</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-600">Actions</th>
                </tr>
              </thead>
              <tbody>
                {data?.users.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-8 text-gray-500 italic">
                      No users found.
                    </td>
                  </tr>
                ) : (
                  data?.users.map((user: UserListItem, idx: number) => (
                    <tr
                      key={user.user_id}
                      className={`border-b border-gray-100 hover:bg-blue-50 transition-colors ${
                        idx % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'
                      }`}
                    >
                      {/* Sel column — maps to SEL000x fields (FSET,NORM,UNPROT) */}
                      <td className="px-3 py-2 text-gray-400 text-xs">{idx + 1}</td>
                      {/* USRID column — ASKIP (output only) */}
                      <td className="px-3 py-2 font-mono text-blue-700 font-medium">
                        {user.user_id}
                      </td>
                      <td className="px-3 py-2 text-gray-800">{user.first_name}</td>
                      <td className="px-3 py-2 text-gray-800">{user.last_name}</td>
                      {/* UTYPE column */}
                      <td className="px-3 py-2">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                            user.user_type === 'A'
                              ? 'bg-amber-100 text-amber-800'
                              : 'bg-blue-100 text-blue-800'
                          }`}
                        >
                          {user.user_type} — {formatUserType(user.user_type)}
                        </span>
                      </td>
                      {/* Actions — maps to row selection 'U' (update) and 'D' (delete) */}
                      <td className="px-3 py-2">
                        <div className="flex gap-2">
                          {/* 'U' selection → COUSR02C */}
                          <Link
                            href={`/users/${user.user_id}/edit`}
                            className="text-xs text-blue-600 hover:text-blue-800 hover:underline font-medium"
                            aria-label={`Update user ${user.user_id}`}
                          >
                            U - Update
                          </Link>
                          {/* 'D' selection → COUSR03C */}
                          <Link
                            href={`/users/${user.user_id}/delete`}
                            className="text-xs text-red-600 hover:text-red-800 hover:underline font-medium"
                            aria-label={`Delete user ${user.user_id}`}
                          >
                            D - Delete
                          </Link>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Function key legend — Row 24 from BMS */}
          {/* ENTER=Continue  F3=Back  F7=Backward  F8=Forward */}
          <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-gray-200">
            {/* F7 = Backward */}
            <Button
              size="sm"
              variant="secondary"
              onClick={handlePrevPage}
              disabled={!data?.has_prev_page}
              aria-label="Previous page (F7)"
            >
              F7 - Backward
            </Button>
            {/* F8 = Forward */}
            <Button
              size="sm"
              variant="secondary"
              onClick={handleNextPage}
              disabled={!data?.has_next_page}
              aria-label="Next page (F8)"
            >
              F8 - Forward
            </Button>
            {/* Add new user — COADM01C menu option for COUSR01C */}
            <Link href="/users/new">
              <Button size="sm">Add User</Button>
            </Link>
          </div>
        </>
      )}
    </div>
  );
}
