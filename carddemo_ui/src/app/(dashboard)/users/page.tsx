'use client';

// ============================================================
// User List Page (Admin Only)
// Mirrors COUSR00C program and COUSR00 BMS map.
// Pageable: 10 rows per page. Admin-only — redirects user type 'U'.
// ============================================================

import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Plus, Search, X } from 'lucide-react';
import { usersApi } from '@/lib/api';
import type { User, UserListResponse } from '@/lib/types';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { PageHeader } from '@/components/ui/PageHeader';
import { Badge, userTypeBadge } from '@/components/ui/Badge';
import { useAuth } from '@/contexts/AuthContext';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

const PAGE_SIZE = 10;

const COLUMNS: Column<User>[] = [
  {
    key: 'usr_id',
    header: 'User ID',
    render: (row) => (
      <Link href={`/users/${row.usr_id}`} className="font-medium text-blue-600 hover:underline">
        {row.usr_id}
      </Link>
    ),
  },
  { key: 'first_name', header: 'First Name' },
  { key: 'last_name', header: 'Last Name' },
  {
    key: 'usr_type',
    header: 'Type',
    render: (row) => (
      <Badge variant={userTypeBadge(row.usr_type)} label={row.usr_type === 'A' ? 'Admin' : 'User'} />
    ),
    className: 'text-center',
  },
];

export default function UsersPage() {
  const { isAdmin, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const [page, setPage] = useState(1);
  const [usrFilter, setUsrFilter] = useState('');
  const [appliedFilter, setAppliedFilter] = useState('');
  const [cursors, setCursors] = useState<Record<number, { start?: string }>>({});

  useEffect(() => {
    if (!authLoading && !isAdmin) {
      router.replace('/dashboard');
    }
  }, [isAdmin, authLoading, router]);

  const { data, isLoading } = useQuery({
    queryKey: ['users', page, appliedFilter],
    queryFn: async () => {
      const params: Record<string, unknown> = { page_size: PAGE_SIZE };

      // If filtering, use as start key
      if (appliedFilter) {
        params.start_usr_id = appliedFilter;
      } else {
        const cursor = cursors[page];
        if (cursor?.start) {
          params.start_usr_id = cursor.start;
          params.direction = 'forward';
        }
      }

      const response = await usersApi.list(params);
      const result = response.data as UserListResponse;

      // Store cursor for next page
      if (result.items.length > 0 && result.has_next_page) {
        const lastItem = result.items[result.items.length - 1];
        setCursors((prev) => ({
          ...prev,
          [page + 1]: { start: lastItem.usr_id },
        }));
      }

      return result;
    },
    enabled: isAdmin,
  });

  if (authLoading) {
    return (
      <div className="flex justify-center py-24">
        <LoadingSpinner size="lg" label="Checking permissions..." />
      </div>
    );
  }

  if (!isAdmin) return null;

  const applyFilter = () => {
    setPage(1);
    setCursors({});
    setAppliedFilter(usrFilter.toUpperCase());
  };

  const clearFilter = () => {
    setUsrFilter('');
    setAppliedFilter('');
    setPage(1);
    setCursors({});
  };

  return (
    <div>
      <PageHeader
        title="User Management"
        description="Create and manage system users"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Users' },
        ]}
        actions={
          <Link
            href="/users/new"
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="h-4 w-4" />
            Add User
          </Link>
        }
      />

      {/* Filter */}
      <div className="mb-5 bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
        <div className="flex gap-3 items-end">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-slate-600">User ID</label>
            <input
              type="text"
              value={usrFilter}
              onChange={(e) => setUsrFilter(e.target.value.toUpperCase())}
              placeholder="Filter by user ID"
              maxLength={8}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 w-40 uppercase"
              onKeyDown={(e) => e.key === 'Enter' && applyFilter()}
            />
          </div>
          <button
            onClick={applyFilter}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Search className="h-4 w-4" />
            Search
          </button>
          {appliedFilter && (
            <button
              onClick={clearFilter}
              className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-slate-600 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
            >
              <X className="h-4 w-4" />
              Clear
            </button>
          )}
        </div>
      </div>

      <DataTable
        columns={COLUMNS}
        data={data?.items ?? []}
        keyExtractor={(row) => row.usr_id}
        currentPage={page}
        pageSize={PAGE_SIZE}
        hasNextPage={data?.has_next_page ?? false}
        onPageChange={setPage}
        onRowClick={(row) => router.push(`/users/${row.usr_id}`)}
        isLoading={isLoading}
        emptyMessage="No users found"
      />
    </div>
  );
}
