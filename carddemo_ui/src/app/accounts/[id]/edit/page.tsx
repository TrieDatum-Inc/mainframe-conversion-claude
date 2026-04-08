/**
 * Account edit page — derived from COACTUPC (CICS transaction CA0U).
 * BMS map: COACTUP
 *
 * COBOL validation rules preserved:
 *   - active_status must be 'Y' or 'N'
 *   - credit_limit >= 0
 *   - ZIP format: XXXXX or XXXXX-XXXX (CSLKPCDY)
 *   - group_id: admin only (403 if non-admin attempts change)
 */
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { AppShell } from '@/components/layout/AppShell';
import { Button } from '@/components/ui/Button';
import { FormField, Input, Select } from '@/components/ui/FormField';
import { Alert } from '@/components/ui/Alert';
import { accountService } from '@/services/accountService';
import { authService } from '@/services/authService';
import { accountUpdateSchema, type AccountUpdateFormValues } from '@/lib/validators/account';
import { extractErrorMessage } from '@/services/apiClient';
import { ROUTES } from '@/lib/constants/routes';
import type { AccountDetailResponse } from '@/lib/types/api';

interface PageProps {
  params: { id: string };
}

export default function AccountEditPage({ params }: PageProps) {
  const router = useRouter();
  const acctId = parseInt(params.id, 10);
  const [account, setAccount] = useState<AccountDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const isAdmin = authService.isAdmin();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<AccountUpdateFormValues>({
    resolver: zodResolver(accountUpdateSchema),
  });

  useEffect(() => {
    if (isNaN(acctId)) {
      setLoadError('Invalid account ID');
      setIsLoading(false);
      return;
    }

    accountService
      .getAccount(acctId)
      .then((data) => {
        setAccount(data);
        reset({
          active_status: (data.active_status as 'Y' | 'N') ?? undefined,
          curr_bal: data.curr_bal ?? undefined,
          credit_limit: data.credit_limit ?? undefined,
          cash_credit_limit: data.cash_credit_limit ?? undefined,
          open_date: data.open_date ?? undefined,
          expiration_date: data.expiration_date ?? undefined,
          reissue_date: data.reissue_date ?? undefined,
          curr_cycle_credit: data.curr_cycle_credit ?? undefined,
          curr_cycle_debit: data.curr_cycle_debit ?? undefined,
          addr_zip: data.addr_zip ?? undefined,
          group_id: isAdmin ? (data.group_id ?? undefined) : undefined,
        });
      })
      .catch((err) => setLoadError(extractErrorMessage(err)))
      .finally(() => setIsLoading(false));
  }, [acctId, reset, isAdmin]);

  const onSubmit = async (values: AccountUpdateFormValues) => {
    setIsSaving(true);
    setSaveError(null);
    setSaveSuccess(false);
    try {
      await accountService.updateAccount(acctId, values);
      setSaveSuccess(true);
      setTimeout(() => router.push(ROUTES.ACCOUNT_VIEW(acctId)), 1500);
    } catch (err) {
      setSaveError(extractErrorMessage(err));
    } finally {
      setIsSaving(false);
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
            <h1 className="page-title">Edit Account</h1>
            <p className="page-subtitle">Account #{acctId} — COACTUPC</p>
          </div>
          <Link href={ROUTES.ACCOUNT_VIEW(acctId)}>
            <Button variant="outline" size="sm">Cancel</Button>
          </Link>
        </div>

        {loadError && <Alert variant="error" className="mb-4">{loadError}</Alert>}
        {saveError && <Alert variant="error" className="mb-4">{saveError}</Alert>}
        {saveSuccess && (
          <Alert variant="success" className="mb-4">
            Account updated successfully. Redirecting...
          </Alert>
        )}

        {account && (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div className="card">
              <h2 className="text-base font-semibold text-gray-900 mb-4">Account Status</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <FormField label="Active Status" htmlFor="active_status" error={errors.active_status?.message}>
                  <Select id="active_status" hasError={!!errors.active_status} {...register('active_status')}>
                    <option value="">Select...</option>
                    <option value="Y">Y — Active</option>
                    <option value="N">N — Inactive</option>
                  </Select>
                </FormField>

                {isAdmin && (
                  <FormField
                    label="Group ID"
                    htmlFor="group_id"
                    error={errors.group_id?.message}
                    hint="Admin only (ACCT-GROUP-ID)"
                  >
                    <Input
                      id="group_id"
                      maxLength={10}
                      hasError={!!errors.group_id}
                      {...register('group_id')}
                    />
                  </FormField>
                )}
              </div>
            </div>

            <div className="card">
              <h2 className="text-base font-semibold text-gray-900 mb-4">Financial Fields</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <FormField label="Current Balance" htmlFor="curr_bal" error={errors.curr_bal?.message}>
                  <Input
                    id="curr_bal"
                    type="text"
                    inputMode="decimal"
                    placeholder="0.00"
                    hasError={!!errors.curr_bal}
                    {...register('curr_bal')}
                  />
                </FormField>
                <FormField label="Credit Limit" htmlFor="credit_limit" error={errors.credit_limit?.message}>
                  <Input
                    id="credit_limit"
                    type="text"
                    inputMode="decimal"
                    placeholder="0.00"
                    hasError={!!errors.credit_limit}
                    {...register('credit_limit')}
                  />
                </FormField>
                <FormField label="Cash Credit Limit" htmlFor="cash_credit_limit" error={errors.cash_credit_limit?.message}>
                  <Input
                    id="cash_credit_limit"
                    type="text"
                    inputMode="decimal"
                    placeholder="0.00"
                    hasError={!!errors.cash_credit_limit}
                    {...register('cash_credit_limit')}
                  />
                </FormField>
                <FormField label="Cycle Credit" htmlFor="curr_cycle_credit" error={errors.curr_cycle_credit?.message}>
                  <Input
                    id="curr_cycle_credit"
                    type="text"
                    inputMode="decimal"
                    placeholder="0.00"
                    hasError={!!errors.curr_cycle_credit}
                    {...register('curr_cycle_credit')}
                  />
                </FormField>
                <FormField label="Cycle Debit" htmlFor="curr_cycle_debit" error={errors.curr_cycle_debit?.message}>
                  <Input
                    id="curr_cycle_debit"
                    type="text"
                    inputMode="decimal"
                    placeholder="0.00"
                    hasError={!!errors.curr_cycle_debit}
                    {...register('curr_cycle_debit')}
                  />
                </FormField>
              </div>
            </div>

            <div className="card">
              <h2 className="text-base font-semibold text-gray-900 mb-4">Dates</h2>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <FormField label="Open Date" htmlFor="open_date" error={errors.open_date?.message} hint="YYYY-MM-DD">
                  <Input id="open_date" type="date" hasError={!!errors.open_date} {...register('open_date')} />
                </FormField>
                <FormField label="Expiration Date" htmlFor="expiration_date" error={errors.expiration_date?.message} hint="YYYY-MM-DD">
                  <Input id="expiration_date" type="date" hasError={!!errors.expiration_date} {...register('expiration_date')} />
                </FormField>
                <FormField label="Reissue Date" htmlFor="reissue_date" error={errors.reissue_date?.message} hint="YYYY-MM-DD">
                  <Input id="reissue_date" type="date" hasError={!!errors.reissue_date} {...register('reissue_date')} />
                </FormField>
              </div>
            </div>

            <div className="card">
              <h2 className="text-base font-semibold text-gray-900 mb-4">Address</h2>
              <div className="max-w-xs">
                <FormField
                  label="ZIP Code"
                  htmlFor="addr_zip"
                  error={errors.addr_zip?.message}
                  hint="XXXXX or XXXXX-XXXX (CSLKPCDY validation)"
                >
                  <Input
                    id="addr_zip"
                    type="text"
                    inputMode="numeric"
                    maxLength={10}
                    placeholder="12345 or 12345-6789"
                    hasError={!!errors.addr_zip}
                    {...register('addr_zip')}
                  />
                </FormField>
              </div>
            </div>

            <div className="flex justify-end gap-3">
              <Link href={ROUTES.ACCOUNT_VIEW(acctId)}>
                <Button variant="outline">Cancel</Button>
              </Link>
              <Button
                type="submit"
                variant="primary"
                isLoading={isSaving}
                disabled={!isDirty}
              >
                Save Changes
              </Button>
            </div>
          </form>
        )}
      </div>
    </AppShell>
  );
}
