'use client';

// ============================================================
// Authorization Details Page
// Mirrors COPAUS1C (detail view) + COPAUS2C (fraud update).
// Shows all pending auth details for an account with fraud flag toggle.
// ============================================================

import { use, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { AlertTriangle, ShieldCheck, ShieldAlert } from 'lucide-react';
import toast from 'react-hot-toast';
import Link from 'next/link';
import { authorizationsApi, getErrorMessage } from '@/lib/api';
import type { AuthorizationDetail } from '@/lib/types';
import { PageHeader } from '@/components/ui/PageHeader';
import { Badge } from '@/components/ui/Badge';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';

function formatCurrency(val: number | undefined | null): string {
  if (val == null) return '—';
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
}

function FraudBadge({ flag }: { flag: string }) {
  const isFraud = flag === 'Y' || flag === '1';
  return (
    <Badge
      variant={isFraud ? 'error' : 'approved'}
      label={isFraud ? 'Fraud' : 'Clear'}
    />
  );
}

interface FraudToggleProps {
  detail: AuthorizationDetail;
  acctId: string;
}

function FraudToggle({ detail, acctId }: FraudToggleProps) {
  const queryClient = useQueryClient();
  const [showConfirm, setShowConfirm] = useState(false);
  const isFraud = detail.fraud_flag === 'Y' || detail.fraud_flag === '1';
  const newFlag = isFraud ? 'N' : 'Y';
  const action = isFraud ? 'clear fraud flag' : 'mark as fraud';

  const mutation = useMutation({
    mutationFn: () =>
      authorizationsApi.flagFraud({
        acct_id: Number(acctId),
        auth_date: detail.auth_date,
        auth_time: detail.auth_time,
        fraud_reason: isFraud ? 'Cleared by operator' : 'Flagged by operator',
        fraud_status: isFraud ? 'R' : 'P',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['auth-details', acctId] });
      toast.success(`Authorization ${action === 'clear fraud flag' ? 'cleared' : 'flagged as fraud'}`);
      setShowConfirm(false);
    },
    onError: (err) => {
      toast.error(getErrorMessage(err));
      setShowConfirm(false);
    },
  });

  return (
    <>
      <button
        onClick={() => setShowConfirm(true)}
        className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
          isFraud
            ? 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100'
            : 'bg-red-50 text-red-700 hover:bg-red-100'
        }`}
        title={`Click to ${action}`}
      >
        {isFraud ? <ShieldCheck className="h-3.5 w-3.5" /> : <ShieldAlert className="h-3.5 w-3.5" />}
        {isFraud ? 'Clear' : 'Flag Fraud'}
      </button>

      <ConfirmDialog
        isOpen={showConfirm}
        title={isFraud ? 'Clear Fraud Flag' : 'Flag as Fraud'}
        message={`Are you sure you want to ${action} for this authorization (${detail.auth_date} ${detail.auth_time})?`}
        confirmLabel={isFraud ? 'Clear Flag' : 'Flag as Fraud'}
        onConfirm={() => mutation.mutate()}
        onCancel={() => setShowConfirm(false)}
        isLoading={mutation.isPending}
      />
    </>
  );
}

export default function AuthorizationDetailsPage({ params }: { params: Promise<{ acctId: string }> }) {
  const { acctId } = use(params);
  const router = useRouter();

  const { data: details, isLoading, error } = useQuery({
    queryKey: ['auth-details', acctId],
    queryFn: async () => {
      const response = await authorizationsApi.details(acctId);
      return response.data as AuthorizationDetail[];
    },
  });

  if (isLoading) {
    return (
      <div className="flex justify-center py-24">
        <LoadingSpinner size="lg" label="Loading authorizations..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl bg-red-50 border border-red-200 p-6 text-center">
        <p className="text-sm text-red-700 font-medium">{getErrorMessage(error)}</p>
        <button onClick={() => router.back()} className="mt-4 text-sm text-blue-600 hover:underline">Go back</button>
      </div>
    );
  }

  const items = details ?? [];
  const fraudCount = items.filter((d) => d.fraud_flag === 'Y' || d.fraud_flag === '1').length;

  return (
    <div>
      <PageHeader
        title={`Authorizations — Account ${acctId}`}
        description={`${items.length} pending authorization${items.length !== 1 ? 's' : ''}`}
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Authorizations', href: '/authorizations' },
          { label: `Account ${acctId}` },
        ]}
        actions={
          <Link
            href={`/accounts/${acctId}`}
            className="px-3 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
          >
            View Account
          </Link>
        }
      />

      {/* Summary badges */}
      {fraudCount > 0 && (
        <div className="mb-4 flex items-center gap-2 rounded-xl bg-red-50 border border-red-200 px-4 py-3">
          <AlertTriangle className="h-4 w-4 text-red-600 shrink-0" />
          <p className="text-sm text-red-700 font-medium">
            {fraudCount} authorization{fraudCount !== 1 ? 's' : ''} flagged as fraud
          </p>
        </div>
      )}

      {items.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
          <ShieldCheck className="h-10 w-10 text-slate-300 mx-auto mb-3" />
          <p className="text-sm text-slate-500">No pending authorizations for this account</p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50">
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Time</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Card</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Reason</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase tracking-wider">Amount</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-slate-600 uppercase tracking-wider">Response</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-slate-600 uppercase tracking-wider">Fraud</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-slate-600 uppercase tracking-wider">Action</th>
                </tr>
              </thead>
              <tbody>
                {items.map((detail, idx) => (
                  <tr key={idx} className="border-b border-slate-100 last:border-0 hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3 text-slate-700 font-mono text-xs">{detail.auth_date}</td>
                    <td className="px-4 py-3 text-slate-700 font-mono text-xs">{detail.auth_time}</td>
                    <td className="px-4 py-3">
                      <Link href={`/cards/${detail.card_num}`} className="font-mono text-xs text-blue-600 hover:underline">
                        ****{detail.card_num?.slice(-4)}
                      </Link>
                    </td>
                    <td className="px-4 py-3">
                      <div>
                        <p className="text-slate-700 font-medium text-xs">{detail.response_reason}</p>
                        <p className="text-slate-400 text-xs">{detail.auth_id_code}</p>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right font-medium text-slate-900">{formatCurrency(detail.approved_amt)}</td>
                    <td className="px-4 py-3 text-center">
                      <span className="font-mono text-xs text-slate-600">{detail.response_code}</span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <FraudBadge flag={detail.fraud_flag} />
                    </td>
                    <td className="px-4 py-3 text-center">
                      <FraudToggle detail={detail} acctId={acctId} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
