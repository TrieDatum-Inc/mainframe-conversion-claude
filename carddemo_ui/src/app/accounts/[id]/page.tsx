/**
 * Account detail view — derived from COACTVWC (CICS transaction CA0V).
 * BMS map: COACTVW
 *
 * Displays all ACCT-* fields plus customer join from CUSTDAT/CCXREF.
 */
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { AppShell } from '@/components/layout/AppShell';
import { Button } from '@/components/ui/Button';
import { Alert } from '@/components/ui/Alert';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { accountService } from '@/services/accountService';
import { formatCurrency, formatDate } from '@/lib/utils/format';
import { extractErrorMessage } from '@/services/apiClient';
import { ROUTES } from '@/lib/constants/routes';
import type { AccountDetailResponse } from '@/lib/types/api';

interface PageProps {
  params: { id: string };
}

export default function AccountDetailPage({ params }: PageProps) {
  const acctId = parseInt(params.id, 10);
  const [account, setAccount] = useState<AccountDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isNaN(acctId)) {
      setError('Invalid account ID');
      setIsLoading(false);
      return;
    }

    accountService
      .getAccount(acctId)
      .then(setAccount)
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setIsLoading(false));
  }, [acctId]);

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
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="page-header">
          <div>
            <h1 className="page-title">Account Details</h1>
            <p className="page-subtitle">Account #{acctId} — COACTVWC</p>
          </div>
          <div className="flex gap-2">
            <Link href={ROUTES.ACCOUNTS}>
              <Button variant="outline" size="sm">Back</Button>
            </Link>
            {account && (
              <>
                <Link href={ROUTES.ACCOUNT_EDIT(acctId)}>
                  <Button variant="secondary" size="sm">Edit Account</Button>
                </Link>
              </>
            )}
          </div>
        </div>

        {error && <Alert variant="error" className="mb-4">{error}</Alert>}

        {account && (
          <div className="space-y-6">
            {/* Customer Info */}
            {(account.customer_id || account.customer_name) && (
              <div className="card">
                <h2 className="text-base font-semibold text-gray-900 mb-4">Customer Information</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <DetailRow label="Customer ID" value={account.customer_id?.toString()} />
                  <DetailRow label="Customer Name" value={account.customer_name} />
                </div>
              </div>
            )}

            {/* Account Overview */}
            <div className="card">
              <h2 className="text-base font-semibold text-gray-900 mb-4">Account Overview</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                <DetailRow
                  label="Account ID"
                  value={account.acct_id.toString()}
                  mono
                />
                <div className="flex flex-col gap-1">
                  <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Status</span>
                  <StatusBadge status={account.active_status} />
                </div>
                <DetailRow label="Group ID" value={account.group_id} />
              </div>
            </div>

            {/* Financial Summary */}
            <div className="card">
              <h2 className="text-base font-semibold text-gray-900 mb-4">Financial Summary</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                <AmountRow label="Current Balance" value={account.curr_bal} />
                <AmountRow label="Credit Limit" value={account.credit_limit} />
                <AmountRow label="Cash Credit Limit" value={account.cash_credit_limit} />
                <AmountRow label="Cycle Credit" value={account.curr_cycle_credit} />
                <AmountRow label="Cycle Debit" value={account.curr_cycle_debit} />
              </div>
            </div>

            {/* Dates */}
            <div className="card">
              <h2 className="text-base font-semibold text-gray-900 mb-4">Key Dates</h2>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <DetailRow label="Open Date" value={formatDate(account.open_date)} />
                <DetailRow label="Expiration Date" value={formatDate(account.expiration_date)} />
                <DetailRow label="Reissue Date" value={formatDate(account.reissue_date)} />
              </div>
            </div>

            {/* Address */}
            {account.addr_zip && (
              <div className="card">
                <h2 className="text-base font-semibold text-gray-900 mb-4">Address</h2>
                <DetailRow label="ZIP Code" value={account.addr_zip} />
              </div>
            )}

            {/* Cards link */}
            <div className="card bg-blue-50 border-blue-200">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-blue-900">Credit Cards</h3>
                  <p className="text-sm text-blue-700 mt-0.5">View all cards associated with this account</p>
                </div>
                <Link href={`${ROUTES.CARDS}?account_id=${acctId}`}>
                  <Button variant="outline" size="sm">View Cards</Button>
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}

function DetailRow({
  label,
  value,
  mono,
}: {
  label: string;
  value?: string | null;
  mono?: boolean;
}) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">{label}</span>
      <span className={`text-sm text-gray-900 ${mono ? 'font-mono' : ''}`}>
        {value ?? '—'}
      </span>
    </div>
  );
}

function AmountRow({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">{label}</span>
      <span className="text-sm font-semibold text-gray-900">{formatCurrency(value)}</span>
    </div>
  );
}
