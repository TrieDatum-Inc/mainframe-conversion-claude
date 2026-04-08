/**
 * Bill payment page — derived from COBIL00C (CICS transaction CB00).
 * BMS map: COBIL00
 *
 * COBOL business rules preserved:
 *   - payment_amount must be positive
 *   - payment_amount <= ACCT-CURR-BAL (enforced by API)
 *   - Creates TRANSACT record (TRAN-TYPE-CD='02', TRAN-SOURCE='POS TERM')
 *   - Reduces ACCT-CURR-BAL by payment_amount
 */
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { AppShell } from '@/components/layout/AppShell';
import { Button } from '@/components/ui/Button';
import { FormField, Input } from '@/components/ui/FormField';
import { Alert } from '@/components/ui/Alert';
import { accountService } from '@/services/accountService';
import { billPaymentSchema, type BillPaymentFormValues } from '@/lib/validators/account';
import { formatCurrency } from '@/lib/utils/format';
import { extractErrorMessage } from '@/services/apiClient';
import { ROUTES } from '@/lib/constants/routes';
import type { AccountDetailResponse } from '@/lib/types/api';

interface PageProps {
  params: { id: string };
}

export default function AccountPaymentPage({ params }: PageProps) {
  const router = useRouter();
  const acctId = parseInt(params.id, 10);
  const [account, setAccount] = useState<AccountDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [confirmed, setConfirmed] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<BillPaymentFormValues>({
    resolver: zodResolver(billPaymentSchema),
    defaultValues: { description: 'Bill Payment' },
  });

  const paymentAmount = watch('payment_amount');

  useEffect(() => {
    if (isNaN(acctId)) {
      setLoadError('Invalid account ID');
      setIsLoading(false);
      return;
    }
    accountService
      .getAccount(acctId)
      .then(setAccount)
      .catch((err) => setLoadError(extractErrorMessage(err)))
      .finally(() => setIsLoading(false));
  }, [acctId]);

  const onSubmit = async (values: BillPaymentFormValues) => {
    if (!confirmed) {
      setSubmitError('Please confirm the payment before submitting');
      return;
    }
    setIsSubmitting(true);
    setSubmitError(null);
    setSubmitSuccess(false);
    try {
      await accountService.processPayment(acctId, {
        payment_amount: values.payment_amount,
        description: values.description,
      });
      setSubmitSuccess(true);
      setTimeout(() => router.push(ROUTES.BILL_PAYMENT), 2000);
    } catch (err) {
      setSubmitError(extractErrorMessage(err));
      setIsSubmitting(false);
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
      <div className="max-w-xl mx-auto">
        <div className="page-header">
          <div>
            <h1 className="page-title">Bill Payment</h1>
            <p className="page-subtitle">Account #{acctId} — COBIL00C</p>
          </div>
          <Link href={ROUTES.BILL_PAYMENT}>
            <Button variant="outline" size="sm">Cancel</Button>
          </Link>
        </div>

        {loadError && <Alert variant="error" className="mb-4">{loadError}</Alert>}

        {account && (() => {
          const hasNoBalance = Number(account.curr_bal) <= 0;
          return (
          <div className="space-y-4">
            {hasNoBalance && (
              <Alert variant="info">
                There is no outstanding balance on this account. No payment is required.
              </Alert>
            )}
            {/* Account summary */}
            <div className="card bg-blue-50 border-blue-200">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-blue-600 font-medium uppercase tracking-wide">Current Balance</p>
                  <p className="text-2xl font-bold text-blue-900">{formatCurrency(account.curr_bal)}</p>
                </div>
                <div>
                  <p className="text-xs text-blue-600 font-medium uppercase tracking-wide">Credit Limit</p>
                  <p className="text-xl font-semibold text-blue-800">{formatCurrency(account.credit_limit)}</p>
                </div>
              </div>
            </div>

            {/* Payment form */}
            <div className="card">
              {submitError && <Alert variant="error" className="mb-4">{submitError}</Alert>}
              {submitSuccess && (
                <Alert variant="success" className="mb-4">
                  Bill payment successful. Redirecting...
                </Alert>
              )}

              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                <FormField
                  label="Payment Amount"
                  htmlFor="payment_amount"
                  error={errors.payment_amount?.message}
                  hint="Must be positive and within current balance (COBIL00C validation)"
                  required
                >
                  <div className="relative">
                    <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-500 text-sm">$</span>
                    <Input
                      id="payment_amount"
                      type="text"
                      inputMode="decimal"
                      autoFocus
                      placeholder="0.00"
                      hasError={!!errors.payment_amount}
                      className="pl-7"
                      {...register('payment_amount')}
                    />
                  </div>
                </FormField>

                <FormField label="Description" htmlFor="description" error={errors.description?.message}>
                  <Input
                    id="description"
                    maxLength={100}
                    {...register('description')}
                  />
                </FormField>

                {/* Confirmation checkbox — mirrors COBIL00C CONFIRMI = 'Y' */}
                <div className="flex items-start gap-3 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <input
                    id="confirm"
                    type="checkbox"
                    checked={confirmed}
                    onChange={(e) => setConfirmed(e.target.checked)}
                    className="mt-0.5 h-4 w-4 rounded border-yellow-400 text-yellow-600 focus:ring-yellow-500"
                  />
                  <label htmlFor="confirm" className="text-sm text-yellow-800">
                    I confirm this payment of{' '}
                    <strong>
                      {paymentAmount ? `$${paymentAmount}` : 'the entered amount'}
                    </strong>{' '}
                    for account #{acctId} (COBIL00C: CONFIRMI = &apos;Y&apos;)
                  </label>
                </div>

                <div className="flex justify-end gap-3">
                  <Link href={ROUTES.BILL_PAYMENT}>
                    <Button variant="outline">Cancel</Button>
                  </Link>
                  <Button
                    type="submit"
                    variant="primary"
                    isLoading={isSubmitting}
                    disabled={!confirmed || hasNoBalance}
                  >
                    Submit Payment
                  </Button>
                </div>
              </form>
            </div>
          </div>
          );
        })()}
      </div>
    </AppShell>
  );
}
