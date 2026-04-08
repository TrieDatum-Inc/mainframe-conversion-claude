/**
 * Authorization history for account — derived from COPAUS0C (CICS transaction CPVS).
 * BMS map: COPAU00
 *
 * Shows summary + paginated list of authorization details.
 * PF7/PF8 navigation via keyset pagination on auth_id.
 */
'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { AppShell } from '@/components/layout/AppShell';
import { Button } from '@/components/ui/Button';
import { Alert } from '@/components/ui/Alert';
import { AuthBadge } from '@/components/ui/StatusBadge';
import { Pagination } from '@/components/ui/Pagination';
import { authorizationService } from '@/services/authorizationService';
import { useNumericPagination } from '@/hooks/usePagination';
import { formatCurrency } from '@/lib/utils/format';
import { extractErrorMessage } from '@/services/apiClient';
import { ROUTES } from '@/lib/constants/routes';
import type { AuthDetailListResponse } from '@/lib/types/api';

interface PageProps {
  params: { acctId: string };
}

export default function AccountAuthorizationsPage({ params }: PageProps) {
  const acctId = parseInt(params.acctId, 10);
  const { cursor, page, goNext, goPrev } = useNumericPagination();
  const [data, setData] = useState<AuthDetailListResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAuths = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await authorizationService.listAuthorizations(acctId, {
        cursor,
        limit: 5,
      });
      setData(result);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }, [acctId, cursor]);

  useEffect(() => {
    if (!isNaN(acctId)) {
      fetchAuths();
    }
  }, [fetchAuths, acctId]);

  return (
    <AppShell>
      <div className="max-w-5xl mx-auto">
        <div className="page-header">
          <div>
            <h1 className="page-title">Authorization History</h1>
            <p className="page-subtitle">Account #{acctId} — COPAUS0C</p>
          </div>
          <div className="flex gap-2">
            <Link href={ROUTES.ACCOUNT_VIEW(acctId)}>
              <Button variant="outline" size="sm">Back to Account</Button>
            </Link>
            <Link href={ROUTES.AUTHORIZATIONS}>
              <Button variant="ghost" size="sm">All Accounts</Button>
            </Link>
          </div>
        </div>

        {error && <Alert variant="error" className="mb-4">{error}</Alert>}

        {/* Summary card */}
        {data?.summary && (
          <div className="card mb-4 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
            <h2 className="text-sm font-semibold text-blue-900 mb-3">Account Authorization Summary</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <SummaryItem label="Available Credit" value={formatCurrency(data.summary.available_credit)} />
              <SummaryItem label="Credit Limit" value={formatCurrency(data.summary.credit_limit)} />
              <SummaryItem
                label="Approved Count"
                value={data.summary.approved_auth_cnt.toString()}
              />
              <SummaryItem
                label="Declined Count"
                value={data.summary.declined_auth_cnt.toString()}
              />
              <SummaryItem
                label="Approved Amount"
                value={formatCurrency(data.summary.approved_auth_amt)}
              />
              <SummaryItem
                label="Declined Amount"
                value={formatCurrency(data.summary.declined_auth_amt)}
              />
            </div>
          </div>
        )}

        {/* Auth list */}
        <div className="card">
          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin h-6 w-6 rounded-full border-4 border-blue-600 border-t-transparent" />
            </div>
          ) : data?.items.length === 0 ? (
            <p className="text-center text-gray-500 py-8">No authorizations found.</p>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Auth ID</th>
                      <th>Decision</th>
                      <th>Amount</th>
                      <th>Merchant</th>
                      <th>Date</th>
                      <th>Fraud</th>
                      <th className="sr-only">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {data?.items.map((auth) => (
                      <tr key={auth.auth_id} className="hover:bg-gray-50">
                        <td className="font-mono text-xs">{auth.auth_id}</td>
                        <td>
                          <AuthBadge isApproved={auth.is_approved} />
                        </td>
                        <td className="font-semibold">{formatCurrency(auth.transaction_amt)}</td>
                        <td>{auth.merchant_name ?? '—'}</td>
                        <td className="text-gray-500 text-xs">
                          {auth.auth_orig_date ?? '—'}
                        </td>
                        <td>
                          {auth.auth_fraud === 'F' && (
                            <span className="badge text-red-700 bg-red-50 ring-red-600/20">Fraud</span>
                          )}
                        </td>
                        <td>
                          <Link href={ROUTES.AUTHORIZATION_DETAIL(auth.auth_id)}>
                            <Button variant="ghost" size="sm">View</Button>
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <Pagination
                page={page}
                hasNext={data?.next_cursor !== null && data?.next_cursor !== undefined}
                hasPrev={data?.prev_cursor !== null && data?.prev_cursor !== undefined}
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

function SummaryItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-medium text-blue-600 uppercase tracking-wide">{label}</p>
      <p className="text-sm font-semibold text-blue-900 mt-0.5">{value}</p>
    </div>
  );
}
