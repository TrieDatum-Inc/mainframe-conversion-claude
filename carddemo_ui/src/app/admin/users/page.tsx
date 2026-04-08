/**
 * User management list — derived from COUSR00C (CICS transaction CU00).
 * BMS map: COUSR00
 *
 * Admin only. Keyset pagination (10 users per screen).
 */
'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { AppShell } from '@/components/layout/AppShell';
import { Button } from '@/components/ui/Button';
import { Alert } from '@/components/ui/Alert';
import { Pagination } from '@/components/ui/Pagination';
import { userService } from '@/services/userService';
import { authService } from '@/services/authService';
import { usePagination } from '@/hooks/usePagination';
import { extractErrorMessage } from '@/services/apiClient';
import { ROUTES } from '@/lib/constants/routes';
import type { UserListResponse } from '@/lib/types/api';

export default function UsersPage() {
  const router = useRouter();
  const { cursor, direction, page, goNext, goPrev } = usePagination();
  const [data, setData] = useState<UserListResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    if (!authService.isAdmin()) {
      router.replace(ROUTES.DASHBOARD);
    }
  }, [router]);

  const fetchUsers = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await userService.listUsers({ cursor, direction, limit: 10 });
      setData(result);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }, [cursor, direction]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleDelete = async (userId: string) => {
    if (!confirm(`Delete user "${userId}"? This action cannot be undone.`)) return;
    setDeletingId(userId);
    setDeleteError(null);
    try {
      await userService.deleteUser(userId);
      await fetchUsers();
    } catch (err) {
      setDeleteError(extractErrorMessage(err));
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <AppShell>
      <div className="max-w-4xl mx-auto">
        <div className="page-header">
          <div>
            <h1 className="page-title">User Management</h1>
            <p className="page-subtitle">COUSR00C — Admin Only</p>
          </div>
          <Link href={ROUTES.ADMIN_USER_NEW}>
            <Button variant="primary" size="sm">+ Add User</Button>
          </Link>
        </div>

        {error && <Alert variant="error" className="mb-4">{error}</Alert>}
        {deleteError && <Alert variant="error" className="mb-4">{deleteError}</Alert>}

        <div className="card">
          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin h-6 w-6 rounded-full border-4 border-blue-600 border-t-transparent" />
            </div>
          ) : data?.items.length === 0 ? (
            <p className="text-center text-gray-500 py-8">No users found.</p>
          ) : (
            <>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>User ID</th>
                    <th>Name</th>
                    <th>Type</th>
                    <th className="sr-only">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {data?.items.map((user) => (
                    <tr key={user.user_id} className="hover:bg-gray-50">
                      <td className="font-mono font-semibold">{user.user_id}</td>
                      <td>
                        {user.first_name || user.last_name
                          ? `${user.first_name ?? ''} ${user.last_name ?? ''}`.trim()
                          : '—'}
                      </td>
                      <td>
                        <span
                          className={`badge ${
                            user.is_admin
                              ? 'text-purple-700 bg-purple-50 ring-purple-600/20'
                              : 'text-gray-600 bg-gray-50 ring-gray-500/20'
                          }`}
                        >
                          {user.is_admin ? 'Admin' : 'Regular'}
                        </span>
                      </td>
                      <td className="text-right">
                        <div className="flex gap-1 justify-end">
                          <Link href={ROUTES.ADMIN_USER_EDIT(user.user_id.trim())}>
                            <Button variant="ghost" size="sm">Edit</Button>
                          </Link>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-red-600 hover:bg-red-50"
                            isLoading={deletingId === user.user_id}
                            onClick={() => handleDelete(user.user_id.trim())}
                          >
                            Delete
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <Pagination
                page={page}
                hasNext={!!data?.next_cursor}
                hasPrev={!!data?.prev_cursor}
                onNext={() => goNext(data?.next_cursor)}
                onPrev={() => goPrev(data?.prev_cursor)}
                total={data?.total}
              />
            </>
          )}
        </div>
      </div>
    </AppShell>
  );
}
