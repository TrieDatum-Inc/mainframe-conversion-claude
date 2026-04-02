'use client';

// ============================================================
// Transaction List Page
// Mirrors COTRN00C program and COTRN00 BMS map.
// Pageable: 10 rows per page. Filters: card_num, tran_type_cd.
// ============================================================

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Plus, Search, X } from 'lucide-react';
import { transactionsApi } from '@/lib/api';
import type { TransactionListItem, TransactionListResponse } from '@/lib/types';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { PageHeader } from '@/components/ui/PageHeader';

const PAGE_SIZE = 10;

function formatCurrency(val: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
}

function formatDate(ts: string | null): string {
  if (!ts) return '—';
  return new Date(ts).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
  });
}

const COLUMNS: Column<TransactionListItem>[] = [
  {
    key: 'tran_id',
    header: 'Tran ID',
    render: (row) => (
      <Link href={`/transactions/${row.tran_id}`} className="font-mono text-blue-600 hover:underline text-xs">
        {row.tran_id}
      </Link>
    ),
  },
  { key: 'tran_type_cd', header: 'Type', className: 'text-center' },
  { key: 'tran_cat_cd', header: 'Category', className: 'text-center' },
  {
    key: 'tran_amt',
    header: 'Amount',
    render: (row) => (
      <span className="font-medium">{formatCurrency(row.tran_amt)}</span>
    ),
    className: 'text-right',
  },
  {
    key: 'card_num',
    header: 'Card',
    render: (row) => (
      <span className="font-mono text-xs text-slate-500">
        ****{row.card_num?.slice(-4)}
      </span>
    ),
  },
  {
    key: 'orig_ts',
    header: 'Date',
    render: (row) => formatDate(row.orig_ts),
  },
];

export default function TransactionsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [page, setPage] = useState(1);
  const [cardFilter, setCardFilter] = useState(searchParams.get('card_num') ?? '');
  const [typeFilter, setTypeFilter] = useState('');

  const [applied, setApplied] = useState({
    card: searchParams.get('card_num') ?? '',
    type: '',
  });

  const [cursors, setCursors] = useState<Record<number, { start?: string }>>({});

  const { data, isLoading } = useQuery({
    queryKey: ['transactions', page, applied],
    queryFn: async () => {
      const params: Record<string, unknown> = { page_size: PAGE_SIZE };
      if (applied.card) params.card_num = applied.card;

      const cursor = cursors[page];
      if (cursor?.start) {
        params.start_tran_id = cursor.start;
        params.direction = 'forward';
      }

      const response = await transactionsApi.list(params);
      const result = response.data as TransactionListResponse;

      // Store cursor for next page
      if (result.items.length > 0 && result.has_next_page) {
        const lastItem = result.items[result.items.length - 1];
        setCursors((prev) => ({
          ...prev,
          [page + 1]: { start: lastItem.tran_id },
        }));
      }

      return result;
    },
  });

  const applyFilters = () => {
    setPage(1);
    setCursors({});
    setApplied({ card: cardFilter, type: typeFilter });
  };

  const clearFilters = () => {
    setCardFilter('');
    setTypeFilter('');
    setPage(1);
    setCursors({});
    setApplied({ card: '', type: '' });
  };

  const hasFilters = Boolean(applied.card || applied.type);

  return (
    <div>
      <PageHeader
        title="Transactions"
        description="Browse transaction records"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Transactions' },
        ]}
        actions={
          <Link
            href="/transactions/new"
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="h-4 w-4" />
            Add Transaction
          </Link>
        }
      />

      {/* Filters */}
      <div className="mb-5 bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
        <div className="flex flex-wrap gap-3 items-end">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-slate-600">Card Number</label>
            <input
              type="text"
              value={cardFilter}
              onChange={(e) => setCardFilter(e.target.value)}
              placeholder="Filter by card"
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 w-44"
              onKeyDown={(e) => e.key === 'Enter' && applyFilters()}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-slate-600">Type Code</label>
            <input
              type="text"
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value.toUpperCase())}
              maxLength={2}
              placeholder="e.g. PU"
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 w-24 uppercase"
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
        keyExtractor={(row) => row.tran_id}
        currentPage={page}
        pageSize={PAGE_SIZE}
        hasNextPage={data?.has_next_page ?? false}
        onPageChange={setPage}
        onRowClick={(row) => router.push(`/transactions/${row.tran_id}`)}
        isLoading={isLoading}
        emptyMessage="No transactions found"
      />
    </div>
  );
}
