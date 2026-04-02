'use client';

// ============================================================
// Cards List Page
// Mirrors COCRDLIC (card list) program.
// Pageable: 7 rows per page (matches BMS map COCRDLI row count).
// ============================================================

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Plus, Search, X } from 'lucide-react';
import { cardsApi } from '@/lib/api';
import type { Card, CardListResponse } from '@/lib/types';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { PageHeader } from '@/components/ui/PageHeader';
import { Badge, statusBadge } from '@/components/ui/Badge';

const PAGE_SIZE = 7;

const COLUMNS: Column<Card>[] = [
  {
    key: 'card_num',
    header: 'Card Number',
    render: (row) => (
      <Link href={`/cards/${row.card_num}`} className="font-mono text-blue-600 hover:underline text-xs">
        {row.card_num}
      </Link>
    ),
  },
  { key: 'acct_id', header: 'Account ID' },
  { key: 'embossed_name', header: 'Embossed Name' },
  { key: 'expiration_date', header: 'Expiration' },
  {
    key: 'active_status',
    header: 'Status',
    render: (row) => (
      <Badge
        variant={statusBadge(row.active_status)}
        label={row.active_status === 'Y' ? 'Active' : 'Inactive'}
      />
    ),
  },
];

export default function CardsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [page, setPage] = useState(1);
  const [acctFilter, setAcctFilter] = useState(searchParams.get('account_id') ?? '');
  const [cardFilter, setCardFilter] = useState(searchParams.get('card_num') ?? '');
  const [appliedAcct, setAppliedAcct] = useState(acctFilter);
  const [appliedCard, setAppliedCard] = useState(cardFilter);

  // Track keyset cursors for pagination
  const [cursors, setCursors] = useState<Record<number, { start?: string; end?: string }>>({});

  const { data, isLoading } = useQuery({
    queryKey: ['cards', page, appliedAcct, appliedCard],
    queryFn: async () => {
      const params: Record<string, unknown> = { page_size: PAGE_SIZE };
      if (appliedAcct) params.account_id = Number(appliedAcct);

      // Use keyset cursor for pagination
      const cursor = cursors[page];
      if (cursor?.start) {
        params.start_card_num = cursor.start;
        params.direction = 'forward';
      }

      const response = await cardsApi.list(params);
      const result = response.data as CardListResponse;

      // Store cursors for next/prev pages
      if (result.items.length > 0) {
        const lastItem = result.items[result.items.length - 1];
        if (result.has_next_page) {
          setCursors((prev) => ({
            ...prev,
            [page + 1]: { start: lastItem.card_num },
          }));
        }
      }

      return result;
    },
  });

  const applyFilters = () => {
    setPage(1);
    setCursors({});
    setAppliedAcct(acctFilter);
    setAppliedCard(cardFilter);
  };

  const clearFilters = () => {
    setAcctFilter('');
    setCardFilter('');
    setPage(1);
    setCursors({});
    setAppliedAcct('');
    setAppliedCard('');
  };

  const hasFilters = Boolean(appliedAcct || appliedCard);

  return (
    <div>
      <PageHeader
        title="Credit Cards"
        description="Browse and manage credit cards"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Cards' },
        ]}
        actions={
          <Link
            href="/cards/new"
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="h-4 w-4" />
            Add Card
          </Link>
        }
      />

      {/* Search filters */}
      <div className="mb-5 bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
        <div className="flex flex-wrap gap-3 items-end">
          <div className="flex flex-col gap-1.5 min-w-[140px]">
            <label className="text-xs font-medium text-slate-600">Account ID</label>
            <input
              type="text"
              value={acctFilter}
              onChange={(e) => setAcctFilter(e.target.value)}
              placeholder="Filter by account"
              inputMode="numeric"
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              onKeyDown={(e) => e.key === 'Enter' && applyFilters()}
            />
          </div>
          <div className="flex flex-col gap-1.5 min-w-[180px]">
            <label className="text-xs font-medium text-slate-600">Card Number</label>
            <input
              type="text"
              value={cardFilter}
              onChange={(e) => setCardFilter(e.target.value)}
              placeholder="Filter by card number"
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
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
        keyExtractor={(row) => row.card_num}
        currentPage={page}
        pageSize={PAGE_SIZE}
        hasNextPage={data?.has_next_page ?? false}
        onPageChange={setPage}
        onRowClick={(row) => router.push(`/cards/${row.card_num}`)}
        isLoading={isLoading}
        emptyMessage="No cards found"
      />
    </div>
  );
}
