/**
 * Process authorization page — derived from COPAUA0C (CICS transaction CP00).
 * Replaces MQ-driven authorization engine with REST POST.
 */
'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { AppShell } from '@/components/layout/AppShell';
import { Button } from '@/components/ui/Button';
import { FormField, Input } from '@/components/ui/FormField';
import { Alert } from '@/components/ui/Alert';
import { AuthBadge } from '@/components/ui/StatusBadge';
import { authorizationService } from '@/services/authorizationService';
import { formatCurrency } from '@/lib/utils/format';
import { extractErrorMessage } from '@/services/apiClient';
import type { AuthorizationResponse } from '@/lib/types/api';

const schema = z.object({
  card_num: z.string().length(16, 'Card number must be 16 digits').regex(/^\d{16}$/),
  auth_date: z.string().length(6, 'Auth date must be YYMMDD (6 chars)'),
  auth_time: z.string().length(6, 'Auth time must be HHMMSS (6 chars)'),
  auth_type: z.string().min(1).max(4, 'Auth type max 4 chars'),
  card_expiry_date: z.string().length(4, 'Expiry must be MMYY (4 chars)'),
  transaction_amt: z
    .string()
    .regex(/^\d+(\.\d{1,2})?$/, 'Must be a valid amount')
    .refine((v) => parseFloat(v) >= 0, 'Amount must be non-negative'),
  transaction_id: z.string().min(1).max(15, 'Transaction ID max 15 chars'),
  merchant_name: z.string().max(22).optional(),
  merchant_city: z.string().max(13).optional(),
  merchant_state: z.string().max(2).optional(),
  merchant_zip: z.string().max(9).optional(),
  merchant_id: z.string().max(15).optional(),
  merchant_category_code: z.string().max(4).optional(),
});

type FormValues = z.infer<typeof schema>;

export default function NewAuthorizationPage() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [result, setResult] = useState<AuthorizationResponse | null>(null);

  const today = new Date();
  const defaultDate = `${String(today.getFullYear()).slice(2)}${String(today.getMonth() + 1).padStart(2, '0')}${String(today.getDate()).padStart(2, '0')}`;
  const defaultTime = `${String(today.getHours()).padStart(2, '0')}${String(today.getMinutes()).padStart(2, '0')}${String(today.getSeconds()).padStart(2, '0')}`;

  const { register, handleSubmit, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      auth_date: defaultDate,
      auth_time: defaultTime,
      auth_type: 'PURCH',
    },
  });

  const onSubmit = async (values: FormValues) => {
    setIsSubmitting(true);
    setSubmitError(null);
    setResult(null);
    try {
      const response = await authorizationService.processAuthorization({
        ...values,
        transaction_id: values.transaction_id.padEnd(15, ' ').slice(0, 15),
        merchant_id: (values.merchant_id ?? '').padEnd(15, ' ').slice(0, 15),
        merchant_name: (values.merchant_name ?? '').padEnd(22, ' ').slice(0, 22),
        merchant_city: (values.merchant_city ?? '').padEnd(13, ' ').slice(0, 13),
        merchant_state: (values.merchant_state ?? '').padEnd(2, ' ').slice(0, 2),
        merchant_zip: (values.merchant_zip ?? '').padEnd(9, ' ').slice(0, 9),
        merchant_category_code: (values.merchant_category_code ?? '').padEnd(4, ' ').slice(0, 4),
      });
      setResult(response);
    } catch (err) {
      setSubmitError(extractErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AppShell>
      <div className="max-w-2xl mx-auto">
        <div className="page-header">
          <div>
            <h1 className="page-title">Process Authorization</h1>
            <p className="page-subtitle">COPAUA0C — CP00</p>
          </div>
        </div>

        {submitError && <Alert variant="error" className="mb-4">{submitError}</Alert>}

        {result && (
          <div className={`card mb-4 ${result.is_approved ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
            <div className="flex items-center justify-between">
              <div>
                <AuthBadge isApproved={result.is_approved} />
                <p className="text-sm text-gray-600 mt-1">Auth Code: <span className="font-mono">{result.auth_id_code}</span></p>
                {result.decline_reason_description && (
                  <p className="text-sm text-red-700 mt-1">{result.decline_reason_description}</p>
                )}
              </div>
              <p className="text-2xl font-bold">{formatCurrency(result.approved_amt)}</p>
            </div>
          </div>
        )}

        <div className="card">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField label="Card Number" htmlFor="card_num" error={errors.card_num?.message} required>
                <Input id="card_num" inputMode="numeric" maxLength={16} placeholder="16 digits" {...register('card_num')} />
              </FormField>
              <FormField label="Amount" htmlFor="transaction_amt" error={errors.transaction_amt?.message} required>
                <Input id="transaction_amt" inputMode="decimal" placeholder="0.00" {...register('transaction_amt')} />
              </FormField>
              <FormField label="Auth Type" htmlFor="auth_type" error={errors.auth_type?.message} required>
                <Input id="auth_type" maxLength={4} placeholder="PURCH" {...register('auth_type')} />
              </FormField>
              <FormField label="Card Expiry (MMYY)" htmlFor="card_expiry_date" error={errors.card_expiry_date?.message} required>
                <Input id="card_expiry_date" maxLength={4} placeholder="1225" {...register('card_expiry_date')} />
              </FormField>
              <FormField label="Transaction ID" htmlFor="transaction_id" error={errors.transaction_id?.message} required>
                <Input id="transaction_id" maxLength={15} {...register('transaction_id')} />
              </FormField>
              <FormField label="Auth Date (YYMMDD)" htmlFor="auth_date" error={errors.auth_date?.message} required>
                <Input id="auth_date" maxLength={6} {...register('auth_date')} />
              </FormField>
              <FormField label="Auth Time (HHMMSS)" htmlFor="auth_time" error={errors.auth_time?.message} required>
                <Input id="auth_time" maxLength={6} {...register('auth_time')} />
              </FormField>
              <FormField label="Merchant Name" htmlFor="merchant_name" error={errors.merchant_name?.message}>
                <Input id="merchant_name" maxLength={22} {...register('merchant_name')} />
              </FormField>
              <FormField label="Merchant City" htmlFor="merchant_city" error={errors.merchant_city?.message}>
                <Input id="merchant_city" maxLength={13} {...register('merchant_city')} />
              </FormField>
              <FormField label="Merchant State" htmlFor="merchant_state" error={errors.merchant_state?.message}>
                <Input id="merchant_state" maxLength={2} {...register('merchant_state')} />
              </FormField>
            </div>

            <Button type="submit" variant="primary" isLoading={isSubmitting} className="w-full">
              Process Authorization
            </Button>
          </form>
        </div>
      </div>
    </AppShell>
  );
}
