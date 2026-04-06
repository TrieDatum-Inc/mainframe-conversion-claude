"use client";

/**
 * UserTable component — paginated data table for COUSR00C (List Users).
 *
 * Preserves COUSR00C behaviour:
 *   - 10 rows per page default (matches BMS 10-row display)
 *   - Forward/backward pagination (PF8/PF7 → Next/Prev buttons)
 *   - User ID filter (USRIDIN search field)
 *   - Per-row Edit/Delete actions (replaces 'U'/'D' selection codes)
 *   - Top/bottom guard messages when at boundaries
 */
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { getErrorMessage, listUsers } from "@/lib/api";
import { userTypeLabel } from "@/lib/utils";
import type { User, UserListResponse } from "@/types";
import DeleteUserDialog from "./DeleteUserDialog";

const DEFAULT_PAGE_SIZE = 10;

interface TableState {
  data: UserListResponse | null;
  loading: boolean;
  error: string | null;
  page: number;
  userIdFilter: string;
}

export default function UserTable() {
  const [state, setState] = useState<TableState>({
    data: null,
    loading: true,
    error: null,
    page: 1,
    userIdFilter: "",
  });
  const [deleteTarget, setDeleteTarget] = useState<User | null>(null);
  const [filterInput, setFilterInput] = useState("");

  const fetchUsers = useCallback(async (page: number, userIdFilter: string) => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const result = await listUsers({
        page,
        page_size: DEFAULT_PAGE_SIZE,
        user_id: userIdFilter || undefined,
      });
      setState((prev) => ({ ...prev, data: result, loading: false }));
    } catch (err) {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: getErrorMessage(err),
      }));
    }
  }, []);

  useEffect(() => {
    fetchUsers(state.page, state.userIdFilter);
  }, [fetchUsers, state.page, state.userIdFilter]);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    setState((prev) => ({ ...prev, page: 1, userIdFilter: filterInput }));
  }

  function handlePageChange(newPage: number) {
    setState((prev) => ({ ...prev, page: newPage }));
  }

  function handleDeleteSuccess() {
    setDeleteTarget(null);
    fetchUsers(state.page, state.userIdFilter);
  }

  const { data, loading, error } = state;
  const isFirstPage = state.page === 1;
  const isLastPage = data ? state.page >= data.total_pages : true;

  return (
    <div className="space-y-4">
      {/* Search bar — mirrors USRIDIN field on COUSR00C row 6 */}
      <form onSubmit={handleSearch} className="flex gap-2 items-end">
        <div>
          <label
            htmlFor="userIdSearch"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Search User ID
          </label>
          <input
            id="userIdSearch"
            type="text"
            maxLength={8}
            value={filterInput}
            onChange={(e) => setFilterInput(e.target.value.toUpperCase())}
            placeholder="e.g. ADMIN"
            className="border border-gray-300 rounded px-3 py-2 text-sm w-40 font-mono uppercase focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Search
        </button>
        {state.userIdFilter && (
          <button
            type="button"
            onClick={() => {
              setFilterInput("");
              setState((prev) => ({ ...prev, page: 1, userIdFilter: "" }));
            }}
            className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
          >
            Clear
          </button>
        )}
      </form>

      {/* Status messages — mirrors COUSR00C ERRMSG row 23 */}
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
          {error}
        </div>
      )}
      {!loading && isFirstPage && data?.total === 0 && (
        <div className="p-3 bg-blue-50 border border-blue-200 rounded text-blue-700 text-sm">
          No users found.
        </div>
      )}

      {/* Data table */}
      <div className="overflow-x-auto border border-gray-200 rounded-lg shadow-sm">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left font-semibold text-gray-600 tracking-wide">
                User ID
              </th>
              <th className="px-4 py-3 text-left font-semibold text-gray-600 tracking-wide">
                First Name
              </th>
              <th className="px-4 py-3 text-left font-semibold text-gray-600 tracking-wide">
                Last Name
              </th>
              <th className="px-4 py-3 text-left font-semibold text-gray-600 tracking-wide">
                Type
              </th>
              <th className="px-4 py-3 text-right font-semibold text-gray-600 tracking-wide">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-100">
            {loading ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-400">
                  Loading...
                </td>
              </tr>
            ) : (
              data?.users.map((user) => (
                <tr key={user.user_id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 font-mono font-medium text-gray-900">
                    {user.user_id}
                  </td>
                  <td className="px-4 py-3 text-gray-700">{user.first_name}</td>
                  <td className="px-4 py-3 text-gray-700">{user.last_name}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        user.user_type === "A"
                          ? "bg-purple-100 text-purple-800"
                          : "bg-green-100 text-green-800"
                      }`}
                    >
                      {userTypeLabel(user.user_type)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right space-x-2">
                    {/* Edit — mirrors 'U' selection in COUSR00C */}
                    <Link
                      href={`/admin/users/${user.user_id}/edit`}
                      className="inline-flex items-center px-3 py-1 text-xs font-medium text-blue-700 bg-blue-50 rounded hover:bg-blue-100 transition-colors"
                    >
                      Edit
                    </Link>
                    {/* Delete — mirrors 'D' selection in COUSR00C */}
                    <button
                      onClick={() => setDeleteTarget(user)}
                      className="inline-flex items-center px-3 py-1 text-xs font-medium text-red-700 bg-red-50 rounded hover:bg-red-100 transition-colors"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination — mirrors PF7 (backward) / PF8 (forward) keys */}
      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>
            Page {data.page} of {data.total_pages} &mdash; {data.total} total users
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => handlePageChange(state.page - 1)}
              disabled={isFirstPage}
              className="px-3 py-1 border border-gray-300 rounded disabled:opacity-40 hover:bg-gray-50 disabled:cursor-not-allowed"
            >
              Previous (F7)
            </button>
            <button
              onClick={() => handlePageChange(state.page + 1)}
              disabled={isLastPage}
              className="px-3 py-1 border border-gray-300 rounded disabled:opacity-40 hover:bg-gray-50 disabled:cursor-not-allowed"
            >
              Next (F8)
            </button>
          </div>
        </div>
      )}

      {/* Delete confirmation dialog — mirrors COUSR03C two-phase delete */}
      {deleteTarget && (
        <DeleteUserDialog
          user={deleteTarget}
          onSuccess={handleDeleteSuccess}
          onCancel={() => setDeleteTarget(null)}
        />
      )}
    </div>
  );
}
