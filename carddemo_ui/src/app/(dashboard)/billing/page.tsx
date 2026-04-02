'use client';

// ============================================================
// Bill Payment Page
// Mirrors COBIL00C program and COBIL00 BMS map.
// COBIL00C pays the FULL balance — no partial payments.
// Flow: Enter account ID -> show balance -> confirm Y/N -> pay full balance
// ============================================================

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { DollarSign, Search, CheckCircle } from 'lucide-react';
import { billingApi, accountsApi, getErrorMessage } from '@/lib/api';
import type { AccountWithCustomer, BillPaymentResponse } from '@/lib/types';
import { PageHeader } from '@/components/ui/PageHeader';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';

function formatCurrency(val: number | string | undefined | null): string {
  if (val == null) return '—';
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Number(val));
}

export default function BillingPage() {
  const queryClient = useQueryClient();
  const [acctIdInput, setAcctIdInput] = useState('');
  const [confirmedAcctId, setConfirmedAcctId] = useState('');
  const [showConfirm, setShowConfirm] = useState(false);
  const [lastPayment, setLastPayment] = useState<BillPaymentResponse | null>(null);

  const { data: account, isLoading: accountLoading, error: accountError } = useQuery({
    queryKey: ['account-billing', confirmedAcctId],
    queryFn: async () => {
      const response = await accountsApi.get(confirmedAcctId);
      return response.data as AccountWithCustomer;
    },
    enabled: Boolean(confirmedAcctId),
  });

  const mutation = useMutation({
    mutationFn: () =>
      billingApi.pay({ account_id: Number(confirmedAcctId) }),
    onSuccess: (resp) => {
      const result = resp.data as BillPaymentResponse;
      toast.success(result.message);
      setLastPayment(result);
      setShowConfirm(false);
      queryClient.invalidateQueries({ queryKey: ['account-billing', confirmedAcctId] });
    },
    onError: (err) => {
      toast.error(getErrorMessage(err));
      setShowConfirm(false);
    },
  });

  const handleAccountLookup = () => {
    const trimmed = acctIdInput.trim();
    if (!trimmed || isNaN(Number(trimmed))) {
      toast.error('Acct ID can NOT be empty. Please enter a valid Account ID.');
      return;
    }
    setConfirmedAcctId(trimmed);
    setLastPayment(null);
  };

  const balance = account?.account?.curr_bal;
  const hasDebt = balance != null && Number(balance) < 0;

  return (
    <div>
      <PageHeader
        title="Bill Payment"
        description="Pay account balance in full (COBIL00C)"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Bill Payment' },
        ]}
      />

      <div className="max-w-lg space-y-6">
        {/* Step 1: Account Lookup */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">1. Enter Account ID</h3>
          <div className="flex gap-2">
            <input
              type="text"
              value={acctIdInput}
              onChange={(e) => setAcctIdInput(e.target.value)}
              placeholder="Enter account ID (e.g. 10000000001)"
              inputMode="numeric"
              className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              onKeyDown={(e) => e.key === 'Enter' && handleAccountLookup()}
            />
            <button
              type="button"
              onClick={handleAccountLookup}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Search className="h-4 w-4" />
              Look Up
            </button>
          </div>

          {accountLoading && (
            <p className="mt-3 text-sm text-slate-500">Looking up account...</p>
          )}
          {accountError && (
            <p className="mt-3 text-sm text-red-600">{getErrorMessage(accountError)}</p>
          )}
        </div>

        {/* Step 2: Show Balance + Confirm */}
        {account && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
            <h3 className="text-sm font-semibold text-slate-700 mb-4">2. Account Balance</h3>
            <div className="rounded-lg bg-slate-50 border border-slate-200 p-4 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">Account Holder</span>
                <span className="font-medium text-slate-800">
                  {account.customer.first_name} {account.customer.last_name}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">Current Balance</span>
                <span className="font-bold text-lg text-slate-900">{formatCurrency(balance)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">Credit Limit</span>
                <span className="text-slate-700">{formatCurrency(account.account.credit_limit)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">Status</span>
                <span className={account.account.active_status === 'Y' ? 'text-emerald-600 font-medium' : 'text-red-600 font-medium'}>
                  {account.account.active_status === 'Y' ? 'Active' : 'Inactive'}
                </span>
              </div>
            </div>

            {hasDebt ? (
              <div className="mt-4">
                <p className="text-sm text-slate-600 mb-3">
                  Payment amount: <span className="font-bold text-slate-900">{formatCurrency(Math.abs(Number(balance)))}</span> (full balance)
                </p>
                <button
                  type="button"
                  onClick={() => setShowConfirm(true)}
                  disabled={mutation.isPending}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 transition-colors disabled:opacity-60"
                >
                  <DollarSign className="h-4 w-4" />
                  Confirm Bill Payment
                </button>
              </div>
            ) : (
              <div className="mt-4 rounded-lg bg-amber-50 border border-amber-200 p-3">
                <p className="text-sm text-amber-800 font-medium">You have nothing to pay.</p>
                <p className="text-xs text-amber-600 mt-1">Current balance is zero or credit.</p>
              </div>
            )}
          </div>
        )}

        {/* Confirm dialog — maps COBIL00C CONFIRMI Y/N */}
        <ConfirmDialog
          isOpen={showConfirm}
          title="Confirm Bill Payment"
          message={`Pay full balance of ${formatCurrency(balance ? Math.abs(Number(balance)) : 0)} for account ${confirmedAcctId}?`}
          confirmLabel="Pay Now"
          onConfirm={() => mutation.mutate()}
          onCancel={() => setShowConfirm(false)}
          isLoading={mutation.isPending}
        />

        {/* Step 3: Success */}
        {lastPayment && (
          <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-5">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle className="h-5 w-5 text-emerald-600" />
              <p className="text-sm font-semibold text-emerald-800">{lastPayment.message}</p>
            </div>
            <div className="space-y-1.5 text-sm">
              <div className="flex justify-between">
                <span className="text-emerald-700">Transaction ID</span>
                <span className="font-mono font-medium text-emerald-900">{lastPayment.transaction_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-emerald-700">Previous Balance</span>
                <span className="text-emerald-800">{formatCurrency(lastPayment.previous_balance)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-emerald-700">Payment Amount</span>
                <span className="font-medium text-emerald-900">{formatCurrency(lastPayment.payment_amount)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-emerald-700">New Balance</span>
                <span className="font-bold text-emerald-900">{formatCurrency(lastPayment.new_balance)}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
