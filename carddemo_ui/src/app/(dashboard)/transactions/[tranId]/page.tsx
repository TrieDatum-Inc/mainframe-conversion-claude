'use client';

// ============================================================
// Transaction Detail Page
// Mirrors COTRN01C program and COTRN01 BMS map.
// Read-only view of a single transaction record.
// ============================================================

import { use } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { transactionsApi, getErrorMessage } from '@/lib/api';
import type { TransactionView } from '@/lib/types';
import { PageHeader } from '@/components/ui/PageHeader';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

function formatCurrency(val: number | undefined | null): string {
  if (val == null) return '—';
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
}

function formatDateTime(ts: string): string {
  if (!ts) return '—';
  return new Date(ts).toLocaleString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

function SectionCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="border-b border-slate-100 bg-slate-50 px-5 py-3">
        <h3 className="text-sm font-semibold text-slate-700">{title}</h3>
      </div>
      <div className="p-5">{children}</div>
    </div>
  );
}

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-xs font-medium text-slate-500">{label}</span>
      <span className="text-sm text-slate-900">{value ?? '—'}</span>
    </div>
  );
}

export default function TransactionDetailPage({ params }: { params: Promise<{ tranId: string }> }) {
  const { tranId } = use(params);
  const router = useRouter();

  const { data: tran, isLoading, error } = useQuery({
    queryKey: ['transaction', tranId],
    queryFn: async () => {
      const response = await transactionsApi.get(tranId);
      return response.data as TransactionView;
    },
  });

  if (isLoading) {
    return (
      <div className="flex justify-center py-24">
        <LoadingSpinner size="lg" label="Loading transaction..." />
      </div>
    );
  }

  if (error || !tran) {
    return (
      <div className="rounded-xl bg-red-50 border border-red-200 p-6 text-center">
        <p className="text-sm text-red-700 font-medium">
          {error ? getErrorMessage(error) : 'Transaction not found'}
        </p>
        <button onClick={() => router.back()} className="mt-4 text-sm text-blue-600 hover:underline">Go back</button>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title={`Transaction ${tran.tran_id}`}
        description={tran.tran_desc ?? undefined}
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Transactions', href: '/transactions' },
          { label: tran.tran_id },
        ]}
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 max-w-4xl">
        <SectionCard title="Transaction Details">
          <div className="grid grid-cols-2 gap-5">
            <Field label="Transaction ID" value={<span className="font-mono text-xs">{tran.tran_id}</span>} />
            <Field label="Amount" value={<span className="text-lg font-bold text-slate-900">{formatCurrency(tran.tran_amt)}</span>} />
            <Field label="Type Code" value={tran.tran_type_cd} />
            <Field label="Category Code" value={tran.tran_cat_cd} />
            <Field label="Source" value={tran.tran_source} />
            <Field label="Date/Time" value={formatDateTime(tran.orig_ts ?? '')} />
            <Field label="Description" value={tran.tran_desc} />
          </div>
        </SectionCard>

        <SectionCard title="Card and Account">
          <div className="grid grid-cols-2 gap-5">
            <Field label="Card Number" value={
              <Link href={`/cards/${tran.card_num}`} className="font-mono text-xs text-blue-600 hover:underline">
                {tran.card_num}
              </Link>
            } />
          </div>
        </SectionCard>

        <SectionCard title="Merchant Information">
          <div className="grid grid-cols-2 gap-5">
            <Field label="Merchant ID" value={tran.merchant_id} />
            <Field label="Merchant Name" value={tran.merchant_name} />
            <Field label="City" value={tran.merchant_city} />
            <Field label="ZIP" value={tran.merchant_zip} />
          </div>
        </SectionCard>
      </div>
    </div>
  );
}
