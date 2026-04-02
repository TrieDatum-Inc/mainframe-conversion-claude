'use client';

// ============================================================
// Transaction Types List Page
// Mirrors COTRTLIC program and COTRTLI BMS map.
// Pageable: 7 rows per page. Filters: type code, description.
// ============================================================

import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Plus, Search, X } from 'lucide-react';
import { transactionTypesApi } from '@/lib/api';
import type { TransactionType, TransactionTypeListResponse } from '@/lib/types';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { PageHeader } from '@/components/ui/PageHeader';
import { useAuth } from '@/contexts/AuthContext';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

const PAGE_SIZE = 7;

const COLUMNS: Column<TransactionType>[] = [
  {
    key: 'tran_type_cd',
    header: 'Type Code',
    render: (row) => (
      <span className="font-mono font-bold text-slate-800">{row.tran_type_cd}</span>
    ),
    className: 'w-28',
  },
  { key: 'tran_type_desc', header: 'Description' },
];

export default function TransactionTypesPage() {
  const { isAdmin, isLoading: authLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && !isAdmin) {
      router.replace('/dashboard');
    }
  }, [isAdmin, authLoading, router]);

  if (authLoading) {
    return (
      <div className="flex justify-center py-24">
        <LoadingSpinner size="lg" label="Checking permissions..." />
      </div>
    );
  }

  if (!isAdmin) return null;
  const [page, setPage] = useState(1);
  const [codeFilter, setCodeFilter] = useState('');
  const [descFilter, setDescFilter] = useState('');
  const [applied, setApplied] = useState({ code: '', desc: '' });
  const [cursors, setCursors] = useState<Record<number, { start?: string }>>({});

  const { data, isLoading } = useQuery({
    queryKey: ['transaction-types', page, applied],
    enabled: isAdmin,
    queryFn: async () => {
      const params: Record<string, unknown> = { page_size: PAGE_SIZE };
      if (applied.code) params.type_cd_filter = applied.code.toUpperCase();
      if (applied.desc) params.desc_filter = applied.desc;

      const cursor = cursors[page];
      if (cursor?.start) {
        params.start_type_cd = cursor.start;
      }

      const response = await transactionTypesApi.list(params);
      const result = response.data as TransactionTypeListResponse;

      if (result.items.length > 0 && result.has_next_page) {
        const lastItem = result.items[result.items.length - 1];
        setCursors((prev) => ({
          ...prev,
          [page + 1]: { start: lastItem.tran_type_cd },
        }));
      }

      return result;
    },
  });

  const applyFilters = () => {
    setPage(1);
    setCursors({});
    setApplied({ code: codeFilter, desc: descFilter });
  };

  const clearFilters = () => {
    setCodeFilter('');
    setDescFilter('');
    setPage(1);
    setCursors({});
    setApplied({ code: '', desc: '' });
  };

  const hasFilters = Boolean(applied.code || applied.desc);

  return (
    <div>
      <PageHeader
        title="Transaction Types"
        description="View and manage transaction type codes"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Transaction Types' },
        ]}
        actions={
          <Link
            href="/transaction-types/new"
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="h-4 w-4" />
            Add Type
          </Link>
        }
      />

      {/* Filters */}
      <div className="mb-5 bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
        <div className="flex flex-wrap gap-3 items-end">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-slate-600">Type Code</label>
            <input
              type="text"
              value={codeFilter}
              onChange={(e) => setCodeFilter(e.target.value.toUpperCase())}
              maxLength={2}
              placeholder="e.g. PU"
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 w-24 uppercase"
              onKeyDown={(e) => e.key === 'Enter' && applyFilters()}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-slate-600">Description</label>
            <input
              type="text"
              value={descFilter}
              onChange={(e) => setDescFilter(e.target.value)}
              placeholder="Search description"
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 w-56"
              onKeyDown={(e) => e.key === 'Enter' && applyFilters()}
            />
          </div>
          <button
            onClick={applyFilters}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Search className="h-4 w-4" />
            Search
          </button>
          {hasFilters && (
            <button
              onClick={clearFilters}
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
        keyExtractor={(row) => row.tran_type_cd}
        currentPage={page}
        pageSize={PAGE_SIZE}
        hasNextPage={data?.has_next_page ?? false}
        onPageChange={setPage}
        onRowClick={(row) => router.push(`/transaction-types/${row.tran_type_cd}`)}
        isLoading={isLoading}
        emptyMessage="No transaction types found"
      />
    </div>
  );
}
