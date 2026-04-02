'use client';

// ============================================================
// Authorizations Summary Page
// Mirrors COPAUS0C program — pending authorization list screen.
// Shows account-level summaries of pending authorizations.
// ============================================================

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { Search, X } from 'lucide-react';
import { authorizationsApi } from '@/lib/api';
import type { AuthorizationSummary, AuthSummaryListResponse } from '@/lib/types';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { PageHeader } from '@/components/ui/PageHeader';

function formatCurrency(val: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
}

const COLUMNS: Column<AuthorizationSummary>[] = [
  { key: 'acct_id', header: 'Account ID' },
  { key: 'approved_count', header: 'Approved', className: 'text-center' },
  {
    key: 'approved_amt',
    header: 'Approved Amount',
    render: (row) => <span className="font-medium">{formatCurrency(row.approved_amt)}</span>,
    className: 'text-right',
  },
  { key: 'declined_count', header: 'Declined', className: 'text-center' },
  {
    key: 'declined_amt',
    header: 'Declined Amount',
    render: (row) => <span className="font-medium">{formatCurrency(row.declined_amt)}</span>,
    className: 'text-right',
  },
  {
    key: 'credit_limit',
    header: 'Credit Limit',
    render: (row) => formatCurrency(row.credit_limit),
    className: 'text-right',
  },
  {
    key: 'curr_bal',
    header: 'Balance',
    render: (row) => formatCurrency(row.curr_bal),
    className: 'text-right',
  },
];

export default function AuthorizationsPage() {
  const router = useRouter();
  const [acctFilter, setAcctFilter] = useState('');
  const [appliedFilter, setAppliedFilter] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['authorizations', appliedFilter],
    queryFn: async () => {
      const params: Record<string, unknown> = {};
      if (appliedFilter) params.account_id = Number(appliedFilter);
      const response = await authorizationsApi.summary(params);
      return response.data as AuthSummaryListResponse;
    },
  });

  const applyFilter = () => setAppliedFilter(acctFilter);
  const clearFilter = () => {
    setAcctFilter('');
    setAppliedFilter('');
  };

  return (
    <div>
      <PageHeader
        title="Pending Authorizations"
        description="Account-level pending authorization summary"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Authorizations' },
        ]}
      />

      {/* Filter */}
      <div className="mb-5 bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
        <div className="flex gap-3 items-end">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-slate-600">Account ID Filter</label>
            <input
              type="text"
              value={acctFilter}
              onChange={(e) => setAcctFilter(e.target.value)}
              placeholder="Filter by account ID"
              inputMode="numeric"
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 w-44"
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
        keyExtractor={(row) => row.acct_id}
        currentPage={1}
        pageSize={data?.items?.length ?? 10}
        hasNextPage={false}
        onPageChange={() => {}}
        onRowClick={(row) => router.push(`/authorizations/${row.acct_id}`)}
        isLoading={isLoading}
        emptyMessage="No pending authorizations found"
      />
    </div>
  );
}
