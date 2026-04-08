/**
 * Transaction detail view — derived from COTRN01C (CICS transaction CT01).
 * BMS map: COTRN01
 */
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { AppShell } from '@/components/layout/AppShell';
import { Button } from '@/components/ui/Button';
import { Alert } from '@/components/ui/Alert';
import { transactionService } from '@/services/transactionService';
import { formatCurrency, formatTimestamp } from '@/lib/utils/format';
import { extractErrorMessage } from '@/services/apiClient';
import { ROUTES } from '@/lib/constants/routes';
import type { TransactionResponse } from '@/lib/types/api';

interface PageProps {
  params: { id: string };
}

export default function TransactionDetailPage({ params }: PageProps) {
  const { id } = params;
  const [transaction, setTransaction] = useState<TransactionResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    transactionService
      .getTransaction(id)
      .then(setTransaction)
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setIsLoading(false));
  }, [id]);

  if (isLoading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin h-8 w-8 rounded-full border-4 border-blue-600 border-t-transparent" />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="max-w-3xl mx-auto">
        <div className="page-header">
          <div>
            <h1 className="page-title">Transaction Details</h1>
            <p className="page-subtitle">COTRN01C</p>
          </div>
          <Link href={ROUTES.TRANSACTIONS}>
            <Button variant="outline" size="sm">Back</Button>
          </Link>
        </div>

        {error && <Alert variant="error" className="mb-4">{error}</Alert>}

        {transaction && (
          <div className="space-y-4">
            <div className="card">
              <h2 className="text-base font-semibold text-gray-900 mb-4">Transaction Overview</h2>
              <div className="grid grid-cols-2 gap-4">
                <Row label="Transaction ID" value={transaction.tran_id} mono />
                <Row label="Amount" value={formatCurrency(transaction.amount)} />
                <Row label="Type Code" value={transaction.type_cd} />
                <Row label="Category Code" value={transaction.cat_cd?.toString()} />
                <Row label="Source" value={transaction.source} />
                <Row label="Description" value={transaction.description} />
              </div>
            </div>

            <div className="card">
              <h2 className="text-base font-semibold text-gray-900 mb-4">Merchant</h2>
              <div className="grid grid-cols-2 gap-4">
                <Row label="Merchant ID" value={transaction.merchant_id?.toString()} />
                <Row label="Merchant Name" value={transaction.merchant_name} />
                <Row label="City" value={transaction.merchant_city} />
                <Row label="ZIP" value={transaction.merchant_zip} />
              </div>
            </div>

            <div className="card">
              <h2 className="text-base font-semibold text-gray-900 mb-4">Card & Account</h2>
              <div className="grid grid-cols-2 gap-4">
                <Row label="Card Number" value={transaction.card_num} mono />
                {transaction.acct_id && (
                  <div>
                    <p className="text-xs font-medium text-gray-500 uppercase">Account</p>
                    <Link
                      href={ROUTES.ACCOUNT_VIEW(transaction.acct_id)}
                      className="text-sm text-blue-600 hover:underline mt-1 block"
                    >
                      #{transaction.acct_id}
                    </Link>
                  </div>
                )}
              </div>
            </div>

            <div className="card">
              <h2 className="text-base font-semibold text-gray-900 mb-4">Timestamps</h2>
              <div className="grid grid-cols-2 gap-4">
                <Row label="Originated" value={formatTimestamp(transaction.orig_ts)} />
                <Row label="Processed" value={formatTimestamp(transaction.proc_ts)} />
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}

function Row({ label, value, mono }: { label: string; value?: string | null; mono?: boolean }) {
  return (
    <div>
      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">{label}</p>
      <p className={`text-sm text-gray-900 mt-1 ${mono ? 'font-mono' : ''}`}>{value ?? '—'}</p>
    </div>
  );
}
