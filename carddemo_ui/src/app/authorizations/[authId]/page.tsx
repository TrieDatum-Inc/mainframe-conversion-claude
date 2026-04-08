/**
 * Authorization detail — derived from COPAUS1C (CICS transaction CPVD).
 * Includes fraud marking (PF5 → EXEC CICS LINK COPAUS2C).
 */
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { AppShell } from '@/components/layout/AppShell';
import { Button } from '@/components/ui/Button';
import { Alert } from '@/components/ui/Alert';
import { AuthBadge } from '@/components/ui/StatusBadge';
import { authorizationService } from '@/services/authorizationService';
import { formatCurrency } from '@/lib/utils/format';
import { extractErrorMessage } from '@/services/apiClient';
import { ROUTES } from '@/lib/constants/routes';
import type { AuthDetailResponse } from '@/lib/types/api';

interface PageProps {
  params: { authId: string };
}

export default function AuthorizationDetailPage({ params }: PageProps) {
  const authId = parseInt(params.authId, 10);
  const [auth, setAuth] = useState<AuthDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [fraudLoading, setFraudLoading] = useState(false);
  const [fraudMessage, setFraudMessage] = useState<string | null>(null);

  useEffect(() => {
    authorizationService
      .getAuthorizationDetail(authId)
      .then(setAuth)
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setIsLoading(false));
  }, [authId]);

  // PF5 equivalent — mark/unmark fraud (COPAUS1C → EXEC CICS LINK COPAUS2C)
  const handleFraudToggle = async () => {
    if (!auth) return;
    const isFraud = auth.auth_fraud === 'F';
    const action = isFraud ? 'R' : 'F'; // toggle

    setFraudLoading(true);
    setFraudMessage(null);
    try {
      const result = await authorizationService.markFraud(
        authId,
        auth.acct_id,
        0, // cust_id — would need to be passed from context in real app
        { action }
      );
      setFraudMessage(result.message);
      // Refresh detail
      const updated = await authorizationService.getAuthorizationDetail(authId);
      setAuth(updated);
    } catch (err) {
      setFraudMessage(extractErrorMessage(err));
    } finally {
      setFraudLoading(false);
    }
  };

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
            <h1 className="page-title">Authorization Detail</h1>
            <p className="page-subtitle">COPAUS1C — Auth #{authId}</p>
          </div>
          <div className="flex gap-2">
            {auth && (
              <Link href={ROUTES.AUTHORIZATION_BY_ACCOUNT(auth.acct_id)}>
                <Button variant="outline" size="sm">Back</Button>
              </Link>
            )}
          </div>
        </div>

        {error && <Alert variant="error" className="mb-4">{error}</Alert>}
        {fraudMessage && (
          <Alert variant="info" className="mb-4" onDismiss={() => setFraudMessage(null)}>
            {fraudMessage}
          </Alert>
        )}

        {auth && (
          <div className="space-y-4">
            {/* Decision banner */}
            <div
              className={`rounded-xl p-5 ${
                auth.is_approved
                  ? 'bg-green-50 border border-green-200'
                  : 'bg-red-50 border border-red-200'
              }`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <AuthBadge isApproved={auth.is_approved} />
                  {auth.decline_reason_description && (
                    <p className="text-sm text-red-700 mt-1">{auth.decline_reason_description}</p>
                  )}
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-gray-900">{formatCurrency(auth.transaction_amt)}</p>
                  <p className="text-sm text-gray-500">Approved: {formatCurrency(auth.approved_amt)}</p>
                </div>
              </div>
            </div>

            {/* Fraud marking — PF5 equivalent */}
            <div className="card flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">Fraud Flag</p>
                <p className="text-sm text-gray-500">
                  {auth.auth_fraud === 'F'
                    ? 'This authorization is marked as fraudulent'
                    : 'No fraud flag on this authorization'}
                </p>
              </div>
              <Button
                variant={auth.auth_fraud === 'F' ? 'secondary' : 'danger'}
                size="sm"
                isLoading={fraudLoading}
                onClick={handleFraudToggle}
              >
                {auth.auth_fraud === 'F' ? 'Remove Fraud Flag' : 'Mark as Fraud'}
              </Button>
            </div>

            {/* Transaction info */}
            <div className="card">
              <h2 className="text-base font-semibold text-gray-900 mb-4">Transaction Details</h2>
              <div className="grid grid-cols-2 gap-4">
                <Row label="Auth ID" value={auth.auth_id.toString()} mono />
                <Row label="Auth ID Code" value={auth.auth_id_code} mono />
                <Row label="Auth Type" value={auth.auth_type} />
                <Row label="Response Code" value={auth.auth_resp_code} mono />
                <Row label="Response Reason" value={auth.auth_resp_reason} />
                <Row label="Match Status" value={auth.match_status} />
                <Row label="Date" value={auth.auth_orig_date} />
                <Row label="Time" value={auth.auth_orig_time} />
              </div>
            </div>

            {/* Card info */}
            <div className="card">
              <h2 className="text-base font-semibold text-gray-900 mb-4">Card Details</h2>
              <div className="grid grid-cols-2 gap-4">
                <Row label="Card Number" value={auth.card_num} mono />
                <Row label="Expiry Date" value={auth.card_expiry_date} />
                <Row label="Account ID" value={auth.acct_id.toString()} />
                <Row label="POS Entry Mode" value={auth.pos_entry_mode?.toString()} />
              </div>
            </div>

            {/* Merchant info */}
            <div className="card">
              <h2 className="text-base font-semibold text-gray-900 mb-4">Merchant Details</h2>
              <div className="grid grid-cols-2 gap-4">
                <Row label="Merchant ID" value={auth.merchant_id} />
                <Row label="Merchant Name" value={auth.merchant_name} />
                <Row label="City" value={auth.merchant_city} />
                <Row label="State" value={auth.merchant_state} />
                <Row label="ZIP" value={auth.merchant_zip} />
                <Row label="Category Code" value={auth.merchant_category_code} />
                <Row label="Country Code" value={auth.acqr_country_code} />
                <Row label="Transaction ID" value={auth.transaction_id} mono />
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
